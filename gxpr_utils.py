"""Util functions for gxpr scripts."""
import glob
import os
import re
import subprocess


MAJOR_TOM = '/home/ironsnail/major-tom-versions/major-tom-release-avionics-32.1'

def get_serial(serial_location):
  cmd = [os.path.join(MAJOR_TOM,'tools/console/console'),
         '--serial', serial_location, '--node', 'kGxpr', 'mfginfo', 'get',
         'kGxpr']
  print cmd
  try:
    ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    print ret
  except subprocess.CalledProcessError as e:
    print e
    return None
  SN_LINE = 'serial_number: "'
  for line in ret.splitlines():
    line = line.strip()
    if line.startswith(SN_LINE):
      return line[len(SN_LINE):-1]
  return None


# Used for searching for specific serial devices
def serial_glob(manu, model, intf=0, port=0):
  globstr = '/dev/serial/by-id/usb-%s_%s_*-if%02d-port%d' \
      % (manu, model, intf, port)
  regstr = '^/dev/serial/by-id/usb-%s_%s_(.*)-if%02d-port%d$' \
      % (manu, model, intf, port)
  return [(dev, re.search(regstr, dev).group(1), get_serial(dev)) for dev in glob.glob(globstr)]

if __name__ == "__main__":
  import pprint  
  pprint.pprint(serial_glob('loon', 'gxprbridge', 3))
