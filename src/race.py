#!/usr/bin/env python3

'''
@author:    Daniel S. Fava
@email:     danielsf@ifi.uio.no
@contact:   www.danielfava.com
@copyright: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
@date:      April 2020

See https://github.com/dfava/paper.go.mm.drd
'''

from abc import abstractmethod

class DataRace():
  def __init__(self, message, drType=None):
    assert(drType == None or drType in ['rw', 'ww', 'wr'])
    self.drType = drType
    self.message = message

  def isRW(self):
    assert(self.drType in ['rw', 'ww', 'wr'])
    return self.drType == 'rw'

  def isWW(self):
    assert(self.drType in ['rw', 'ww', 'wr'])
    return self.drType == 'ww'

  def isWR(self):
    assert(self.drType in ['rw', 'ww', 'wr'])
    return self.drType == 'wr'


class RaceDetector():

  @abstractmethod
  def read(self, pid, var):
    pass

  @abstractmethod
  def write(self, pid, var):
    pass

  @abstractmethod
  def acq(self, pid, lock):
    pass

  @abstractmethod
  def rel(self, pid, lock):
    pass

  @abstractmethod
  def fork(self, pid, oid):
    pass

  def range(self, pid, addr, length, access_type):
    if self.verbose:
      print("%s: %s %s %s %s %s" % (self.__class__.__name__, 'rg ', pid, hex(addr), hex(length), 'w' if access_type else 'r'))
    step = 0x8
    assert(access_type in [0,1])
    for v in range(addr, addr+length, step):
      if access_type == 0:
        self.read(pid, v)
      else:
        self.write(pid, v)
