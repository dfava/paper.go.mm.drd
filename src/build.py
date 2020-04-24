#!/usr/bin/env python3.7
#
# Script that builds a Go application for data-race checking
# when the Go race checher has been instrumented with calls
# to Python.
#
# Some of the hacks below were necessary to get around the
# following Go compiler bug:
#
# https://github.com/golang/go/issues/37012

'''
@author:    Daniel S. Fava
@email:     danielsf@ifi.uio.no
@contact:   www.danielfava.com
@copyright: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
@date:      April 2020

See https://github.com/dfava/paper.go.mm.drd
'''

import os
import re
import sys
import uuid
import shutil
import subprocess


def build(fname, work, go='go'):
  ret = subprocess.run('python3-config --ldflags'.split(' '), capture_output=True, text=True)
  pyLdFlags = ret.stdout.strip()
  
  cmd = '%s build -race -n %s' % (go, fname)
  print(cmd)
  ret = subprocess.run(cmd.split(' '), capture_output=True, text=True)
  lines = ret.stderr.split('\n')
  cd = None
  cat_file = None
  cat_content = ''
  startnum = 5
  for (lnum, line) in enumerate(lines[startnum:]):
    #print(line)
    cmd = line.replace('$WORK', work)
    print('%d: %s' % (lnum+startnum, cmd))
    m = re.match('cd (.*)', cmd)
    if m:
      cd = m.group(1)
      print('  recording cd')
      continue
    m = re.search('\|\|', cmd)
    if m:
      print('  skipping')
      continue
    m = re.search(os.sep + work, cmd)
    if m:
      cmd = re.sub('\S*' + work, work, cmd)
      print('  turning command into: %s' % cmd)
    m = re.search('(clang|gcc).*race\S*\.syso', cmd)
    if m:
      cmd += ' ' + pyLdFlags
      print('  adding Py to load flags: %s' % cmd)
    m = re.match('cat (.*) << (.*)', cmd)
    if m:
      cat_file = m.group(1)[1:]
      print(' catting to file: %s' % cat_file)
      cat_content = m.group(2)[6:] + '\n'
      continue
    if cat_file != None:
      if cmd == 'EOF':
        fhandle = open(cat_file, 'w')
        fhandle.write(cat_content)
        fhandle.close()
        cat_content = ''
        cat_file = None
        continue
      cat_content += cmd + '\n'
      print(cat_content)
      continue
    p = subprocess.Popen(cmd, shell=True, cwd=cd)
    ret = p.wait()
    assert(ret==0)
    print('  %d' % ret)


def main(argv):
  if len(argv) < 2:
    print("ERR: What to build?  Missing 'filename.go' argument.")
    return 1
  if len(argv) > 3:
    print("ERR: Too many args")
    return 1

  fname = argv[1]
  go = argv[2] if len(argv) == 3 else 'go'
  work = os.getcwd() + os.sep + str(uuid.uuid4().hex)
  try:
    build(fname, work, go)
  except Exception as e:
    shutil.rmtree(work, ignore_errors=True)
    raise e
  shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
  sys.exit(main(sys.argv))
