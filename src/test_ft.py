#!/usr/bin/env python3

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
from ft import *
import unittest

class TestEpoch(unittest.TestCase):
  def test_new(self):
    ep = Epoch(4, '0')

  def test_new_fail(self):
    try:
      ep = Epoch('a', '0')
    except AssertionError:
      return
    assert(0)

  def test_eq(self):
    ep1 = Epoch(4, '0')
    assert(ep1 == Epoch(4, '0')) # Equal even though different instances
    assert(ep1 != Epoch(5, '0'))
    assert(ep1 != Epoch(4, '1'))

  def test_le_self(self):
    ep = Epoch(0, 'a')
    assert(ep <= ep)

  def test_le_instance(self):
    assert(Epoch(0, 'a') <= Epoch(0, 'a')) # Comparable even though different instances

  def test_le_not_comperable(self):
    epA = Epoch(0, 'a')
    epB = Epoch(0, 'b')
    assert(not epA <= epB)
    assert(not epB <= epA)

  def test_le(self):
    ep = Epoch(0, 'a')
    assert(ep <= Epoch(0, 'a'))
    assert(Epoch(0, 'a') <= ep)
    assert(ep <= Epoch(1, 'a'))
    assert(not Epoch(1, 'a') <= ep)


class TestVC(unittest.TestCase):
  def test_empty(self):
    vc = VC()
    assert(list(vc.vc.keys()) == [])
    assert(vc['a'] == 0)
    assert(vc[1] == 0)

  def test_from_epochs(self):
    vc = VC(Epoch(4, 'a'), Epoch(1, 'b'))
    assert(len(list(vc.vc.keys())) == 2)
    assert(vc['z'] == 0)
    assert(vc[1] == 0)
    assert(vc['a'] == 4)
    assert(vc['b'] == 1)


  def test_inc(self):
    vc = VC()
    assert(vc['a'] == 0)
    vc.inc('a')
    assert(vc['a'] == 1)
    vc.inc('b')
    assert(vc['b'] == 1)
    vc.inc('a')
    assert(vc['a'] == 2)
    assert(vc['b'] == 1)
    assert(vc['c'] == 0)

  def test_le_fail(self):
    vc = VC()
    try:
      vc <= 10
    except AssertionError:
      return
    assert(0)

  def test_le(self):
    vc = VC()
    assert(vc <= vc)
    vc2 = VC()
    assert(vc <= vc2)
    assert(vc2 <= vc)
    vc2.inc('a')
    assert(vc <= vc2)
    assert(not vc2 <= vc)
    vc.inc('a')
    assert(vc <= vc2)
    assert(vc2 <= vc)
    vc.inc('a')
    vc2.inc('b')
    assert(not vc <= vc2)
    assert(not vc2 <= vc)

  def test_lub_trivial(self):
    vc1 = VC()
    vc2 = VC() 
    lub = VC.lub(vc1, vc2)
    assert(vc1 <= lub)
    assert(vc2 <= lub)

  def test_lub_self(self):
    vc1 = VC()
    vc2 = VC() 
    vc1.inc('a')
    vc2.inc('a')
    vc2.inc('a')
    assert(vc1 <= vc2)
    lub = VC.lub(vc1, vc2)
    assert(vc1 <= lub)
    assert(vc2 <= lub)
    assert(lub <= vc2)

  def test_lub(self):
    vc1 = VC()
    vc2 = VC() 
    vc1.inc('a')
    vc2.inc('b')
    vc2.inc('b')
    assert(not vc1 <= vc2)
    assert(not vc2 <= vc1)
    lub = VC.lub(vc1, vc2)
    assert(vc1 <= lub)
    assert(vc2 <= lub)


  def test_new(self):
    vc1 = VC()
    vc1.inc('a')
    vc1.inc('b')
    vc1.inc('b')
    vc2 = VC.new(vc1)
    assert(vc1 <= vc2)
    assert(vc2 <= vc1)



class TestProc(unittest.TestCase):
  def test_new(self):
    pid = '0'
    p = Proc(pid)
    assert(p.vc[pid] == 1)

  def test_inc(self):
    pid = '0'
    p = Proc(pid)
    assert(p.vc[pid] == 1)
    p.inc()
    assert(p.vc[pid] == 2)
    assert(p.vc['o'] == 0)

  def test_epoch(self):
    pid = '0'
    p = Proc(pid)
    assert(p.epoch() == Epoch(1, '0'))
    p.inc()
    assert(p.epoch() == Epoch(2, '0'))


class TestLock(unittest.TestCase):
  def test_acq(self):
    l = Lock('l')
    pass # TODO

  def test_rel(self):
    l = Lock('l')
    pass # TODO


class TestFT(unittest.TestCase):
 
  def test_fork(self):
    ft = FT(verbose=False)
    assert(0 in ft.procs)
    assert(ft.procs[0].vc[0] == 1)  # Every process starts with its VC at 1
    assert(ft.procs[0].vc[1] == 0)
    assert(ft.procs[0].vc[42] == 0)
    ft.fork(0,1)
    assert(ft.procs[0].vc[0] == 2) # Advanced proc[0]'s VC by 1
    assert(ft.procs[0].vc[1] == 0)
    assert(ft.procs[0].vc[42] == 0)
    assert(ft.procs[1].vc[0] == 1) # proc[1] inherits knowledge of parent's vc
    assert(ft.procs[1].vc[1] == 1) # Every process starts with its VC at 1
    assert(ft.procs[1].vc[42] == 0)
    ft.fork(0,2)
    assert(ft.procs[0].vc[0] == 3) # Advanced proc[0]'s VC by 1
    assert(ft.procs[0].vc[1] == 0)
    assert(ft.procs[0].vc[42] == 0)
    assert(ft.procs[1].vc[0] == 1)
    assert(ft.procs[1].vc[1] == 1)
    assert(ft.procs[1].vc[42] == 0)
    assert(ft.procs[2].vc[0] == 2)
    assert(ft.procs[2].vc[1] == 0)
    assert(ft.procs[2].vc[2] == 1) # Every process starts with its VC at 1
    assert(ft.procs[2].vc[42] == 0)

  def test_fork2(self):
    ft = FT(verbose=False)
    assert(1 not in ft.procs.keys())
    assert(1 not in ft.deleted_pids)
    ft.fork(0,1)
    assert(1 in ft.procs.keys())
    assert(1 not in ft.deleted_pids)
    ft.end(1)
    assert(1 not in ft.procs.keys())
    assert(1 in ft.deleted_pids)
    try:
      ft.fork(0,1)
    except AssertionError:
      return
    assert(False)
    
  def test_range(self):
    rd = FT(verbose=False)
    base = 0x0
    size = 0x100
    step = 8
    rd.range(0, base, size, 0)
    vs = [hex(i) for i in range(base, base+size, step)]
    #print(list(rd.vars.keys()))
    #print(vs)
    assert(list(rd.vars.keys()) == vs)

    base = 0x180
    size = 0x20
    rd.range(0, base, size, 1)
    vs += [hex(i) for i in range(base, base+size, step)] 
    #print(list(rd.vars.keys()))
    #print(vs)
    assert(list(rd.vars.keys()) == vs)
    

class TestStats(unittest.TestCase):

  def test_num_vc_entries(self):
    ft = FT(verbose=False)
    ft.fork(0,1)
    ft.fork(0,2)

    ft.acq(0,'l')
    ft.write(0, 'z')
    ft.rel(0,'l')

    ft.write(1, 'x')

    ft.acq(2,'l')
    ft.write(2, 'z')
    ft.rel(2,'l')

    ft.acq(0,'l')
    ft.read(0, 'z')
    ft.rel(0,'l')

    ft.read(2, 'z')

    #mv = Stats.min_vars(ft)
    #print(mv)
    #ft.printReport()
    #print(Stats.getNumVcEntries(ft, 'locks'))
    #print(Stats.getNumVcEntries(ft, 'procs'))
    assert(Stats.getNumVcEntries(ft, 'locks') == 2)
    assert(Stats.getNumVcEntries(ft, 'procs') == 6)


  def est_stats(self):
    ft = FT(verbose=False, stats_interval=1)
    ft.fork(0,1)
    ft.fork(0,2)

    ft.acq(0,'l')
    ft.write(0, 'z')
    ft.rel(0,'l')

    ft.write(1, 'x')
    ft.fork(1,3)

    ft.acq(2,'l')
    ft.write(2, 'z')
    ft.rel(2,'l')

    ft.acq(0,'l')
    ft.read(0, 'z')

    #mv = Stats.min_vars(ft)
    #print(mv)
    #ft.printReport()
   

def main(argv):
  unittest.main()

if __name__ == "__main__":
  sys.exit(main(sys.argv))
