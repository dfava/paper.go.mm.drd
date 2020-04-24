#!/usr/bin/env python3
#
# A Python implementation of the FastTrack data-race detector
# https://dl.acm.org/doi/abs/10.1145/1543135.1542490
#
# The implementation has been instrumented for data collection.

'''
@author:    Daniel S. Fava
@email:     danielsf@ifi.uio.no
@contact:   www.danielfava.com
@copyright: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
@date:      April 2020

See https://github.com/dfava/paper.go.mm.drd
'''

import os
import sys
import inspect

from race import *


class Epoch():
  def __init__(self, c, pid):
    assert(type(c) == int)
    self.c = c
    self.pid = pid

  def __eq__(self, rhs):
    return isinstance(rhs, Epoch) and self.c == rhs.c and self.pid == rhs.pid

  def __le__(self, rhs):
    assert(type(rhs) in [Epoch, VC])
    if type(rhs) == Epoch:
      return self.pid == rhs.pid and self.c <= rhs.c
    return self.c <= rhs[self.pid]

  def __str__(self):
    return "%s@%s" % (self.c.__str__(), self.pid.__str__())

  def __repr__(self):
    return "%s@%s" % (self.c.__str__(), self.pid.__str__())


class VC():
  def __init__(self, *epochs):
    self.vc = {}
    for epoch in epochs:
      assert(type(epoch) == Epoch)
    for epoch in epochs:
      assert(epoch.pid not in self.vc.keys())
      self.vc[epoch.pid] = epoch.c

  def __getitem__(self, key):
    try:
      return self.vc[key]
    except KeyError:
      return 0

  def inc(self, pid):
    try:
      self.vc[pid] += 1
    except KeyError:
      self.vc[pid] = 1

  def __le__(self, rhs):
    assert(type(rhs)==VC)
    for pid in self.vc.keys():
      if self[pid] > rhs[pid]:
        return False
    return True

  def __str__(self):
    return self.vc.__str__()

  def __repr__(self):
    return self.vc.__repr__()

  @classmethod
  def new(cls, other):
    assert(type(other) == VC)
    ret = VC()
    ret.vc = dict(other.vc)
    return ret

  @classmethod
  def lub(cls, vc1, vc2):
    assert(type(vc1) == VC)
    assert(type(vc2) == VC)
    ret = VC()
    keys = set().union(vc1.vc.keys(), vc2.vc.keys())
    for item in keys:
      ret.vc[item] = vc1[item] if vc1[item] > vc2[item] else vc2[item]
    return ret
      

class Proc():
  def __init__(self, pid):
    self.id = pid
    self.vc = VC()
    self.inc()  # See FT's "initial analysis state"

  def inc(self):
    self.vc.inc(self.id)

  def epoch(self):
    return Epoch(self.vc[self.id], self.id)

  def __str__(self):
    return "proc[%s]: %s" % (self.id, self.vc)


class Lock():
  def __init__(self, lid):
    self.id = lid
    self.vc = VC()

  def __str__(self):
    return "lock[%s]: %s" % (self.id, self.vc)


class Var():
  # Assume proc 0 is always present and is the initial process
  def __init__(self, var):
    self.var = var
    self.w = Epoch(0,0)
    self.r = Epoch(0,0)

  def __str__(self):
    return "var[%s]: %s %s" % (self.var, self.w, self.r)


class FT(RaceDetector):

  def __init__(self,verbose=False, stats_interval=10000):
    assert(type(verbose)==bool)
    assert(stats_interval==None or type(stats_interval)==int)
    self.procs = {}
    self.locks = {}
    self.vars = {}
    self.deleted_pids = set()
    self.procs[0] = Proc(0) # Proc 0 is always present
    self.verbose = verbose
    self.info = False
    self.race = True
    self.numOps = {'read'  : 0,
                   'write' : 0,
                   'acq'   : 0,
                   'rel'   : 0,
                   'rem'   : 0,
                   'rea'   : 0,
                  }
    self.stats_interval = stats_interval


  def getTotalOps(self):
    return sum([self.numOps[i] for i in self.numOps.keys()])


  def isTimeToPrintStats(self):
    return type(self.stats_interval) == int and \
              self.getTotalOps() % self.stats_interval == 0


  def stats(self):
    if self.isTimeToPrintStats():
      num_ops = self.getTotalOps()

      data = {'procs' : {'all' : None},
              'locks' : {'all' : None},
             }
      for where in data.keys():
        data[where]['all'] = Stats.getVcEntries(self, where)

      nprocs = len(self.procs.keys())
      print("%s, ops=%d, procs=%d/%d, locks=%d, VC procs=%d, VC locks=%d" % (\
          self.__class__.__name__,\
          num_ops,\
          nprocs,\
          nprocs + len(self.deleted_pids),\
          len(self.locks.keys()),\
          Stats.countVcEntries(data['procs']['stale']),\
          Stats.countVcEntries(data['procs']['all']),\
          Stats.countVcEntries(data['locks']['stale']),\
          Stats.countVcEntries(data['locks']['all']),\
          ))

  def printProcs(self, fmt=None):
    assert(fmt==None)
    for pid in self.procs.keys():
      print(self.procs[pid])

  def printVars(self):
    for v in self.vars.keys():
      print(self.vars[v])
  
  def printLocks(self):
    for l in self.locks.keys():
      print(self.locks[l])

  def printReport(self, print_procs=True,print_vars=True,print_locks=True, fmt=None):
    if print_procs:
      self.printProcs(fmt=fmt)
      #print()
    if print_vars:
      self.printVars()
      #print()
    if print_locks:
      self.printLocks()
    #print()

  def initVar(self, var):
    assert(var not in self.vars.keys())
    self.vars[var] = Var(var)

  def mklock(self, lid):
    assert(lid not in self.locks.keys())
    self.locks[lid] = Lock(lid)


  def read(self, pid, var):
    self.numOps[inspect.currentframe().f_code.co_name] += 1
    var = hex(var) if type(var) == int else var
    if self.verbose:
      print("%s: %s %s %s" % (self.__class__.__name__, 'rd ', pid, var))

    assert(pid in self.procs.keys())
    if var not in self.vars.keys():
      self.initVar(var)
    
    # Read same epoch
    if self.vars[var].r == self.procs[pid].epoch():
      self.stats(); return

    # Read shared
    if type(self.vars[var].r) == VC and \
          self.vars[var].w <= self.procs[pid].vc:
      self.vars[var].r.vc[pid] = self.procs[pid].vc[pid]
      self.stats(); return

    if type(self.vars[var].r) == Epoch and \
          self.vars[var].w <= self.procs[pid].vc:

      # Read exclusive
      if self.vars[var].r <= self.procs[pid].vc:
        self.vars[var].r = self.procs[pid].epoch()
        self.stats(); return
      
      # Read share
      self.vars[var].r = VC(self.procs[pid].epoch(), self.vars[var].r)
      self.stats(); return
    
    # Data race
    message = "%s: (ERR) Data race on read %s %s\n" % (self.__class__.__name__, pid, var)
    message += "  %s\n" % self.procs[pid]
    message += "  %s" % self.vars[var]
    if self.verbose or self.race:
      print(message)
    self.stats(); return DataRace(message)


  def write(self, pid, var):
    self.numOps[inspect.currentframe().f_code.co_name] += 1
    var = hex(var) if type(var) == int else var
    if self.verbose:
      print("%s: %s %s %s" % (self.__class__.__name__, 'wr ', pid, var))

    assert(pid in self.procs.keys())
    if var not in self.vars.keys():
      self.initVar(var)

    # Write same epoch
    if self.vars[var].w == self.procs[pid].epoch():
      self.stats(); return

    # Write exclusive
    if type(self.vars[var].r) == Epoch and \
          self.vars[var].r <= self.procs[pid].vc and \
          self.vars[var].w <= self.procs[pid].vc:
      self.vars[var].w = self.procs[pid].epoch()
      self.stats(); return

    # Write shared
    if type(self.vars[var].r) == VC and \
          self.vars[var].r <= self.procs[pid].vc and \
          self.vars[var].w <= self.procs[pid].vc:
      self.vars[var].w = self.procs[pid].epoch()
      self.vars[var].r = VC()
      self.stats(); return

    # Data race
    message = "%s: (ERR) Data race on write %s %s\n" % (self.__class__.__name__, pid, var)
    message += "  %s\n" % self.procs[pid]
    message += "  %s" % self.vars[var]
    if self.verbose or self.race:
      print(message)
    self.stats(); return DataRace(message)


  def acq(self, pid, lock):
    self.numOps[inspect.currentframe().f_code.co_name] += 1
    lock = hex(lock) if type(lock) == int else lock
    if self.verbose:
      print("%s: %s %s %s" % (self.__class__.__name__, 'acq', pid, lock))

    assert(pid in self.procs.keys())
    if lock not in self.locks.keys():
      self.mklock(lock)
    self.procs[pid].vc = VC.lub(self.procs[pid].vc, self.locks[lock].vc)
    self.stats(); return


  def release(self, pid, lock, f='rel'):
    assert(f in ['rel', 'rem', 'rea'])
    self.numOps[f] += 1
    lock = hex(lock) if type(lock) == int else lock
    if self.verbose:
      print("%s: %s %s %s" % (self.__class__.__name__, f, pid, lock))

    assert(pid in self.procs.keys())
    if lock not in self.locks.keys():
      self.mklock(lock)
      if self.info:
        print("%s: (INFO) Release w/o prior acq: %s %s %s" % (self.__class__.__name__, f, pid, lock))
    if f == 'rel':
      self.locks[lock].vc = VC.new(self.procs[pid].vc)
    elif f == 'rem':
      self.locks[lock].vc = VC.lub(self.procs[pid].vc, self.locks[lock].vc) 
    elif f == 'rea':
      tmp = VC.new(self.procs[pid].vc)
      self.procs[pid].vc = VC.lub(self.procs[pid].vc, self.locks[lock].vc)
      self.locks[lock].vc = tmp
    else:
      assert(0)
    self.procs[pid].inc()
    self.stats(); return
    

  def rel(self, pid, lock):
    '''release: (T,L) => (T, TL)'''
    self.release(pid, lock)


  def rem(self, pid, lock):
    '''release merge: (T,L) => (T, T \cup L)'''
    self.release(pid, lock, f='rem')


  def rea(self, pid, lock):
    '''release-acquire: (T,L) => (T \cup L, T)'''
    self.release(pid, lock, f='rea')


  def fork(self, pid, oid):
    if self.verbose:
      print("%s: %s %s %s" % (self.__class__.__name__, 'frk', pid, oid))

    assert(pid in self.procs.keys())
    assert(oid not in self.procs.keys())
    assert(oid not in self.deleted_pids) # Enforces uniqueness of pids
    self.procs[oid] = Proc(oid)
    self.procs[oid].vc = VC.lub(self.procs[oid].vc, self.procs[pid].vc)
    self.procs[pid].inc()

  def join(self, pid, oid):
    assert(pid in self.procs.keys())
    assert(oid in self.procs.keys())
    assert(0)

  def end(self, pid):
    if self.verbose:
      print("%s: %s %s" % (self.__class__.__name__, 'end', pid))

    assert(pid in self.procs.keys())
    del(self.procs[pid])
    self.deleted_pids.add(pid)


  def free(self, addr, size):
    if self.verbose:
      print("%s: %s %s" % (self.__class__.__name__, 'free', addr, size))

    # Go over self.locks and remove them if addr <= self.locks <= addr+size
    print("ERR: Implement free")
    assert(0)


class Stats():

  @classmethod
  def getVcEntries(cls, ft, where):
    assert(where in ['locks', 'procs'])
    ret = {}
    dct = ft.procs if where == 'procs' else ft.locks    
    for item in dct.keys():
      ret[item] = dct[item].vc
    return ret

  @classmethod
  def countVcEntries(cls, dct):
    ret = 0
    for item in dct.keys():
      ret += len(dct[item].vc)
    return ret

  @classmethod
  def getNumVcEntries(cls, ft, where):
    dct = cls.getVcEntries(ft, where)
    return cls.countVcEntries(dct)
