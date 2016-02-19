#!/usr/bin/env python
import altitude
import ppc4
import sys
from aardvark_py import *
from datetime import datetime
from glob import glob
from time import sleep

# Throw errors on Aardvark API failure
def check_result(result):
  try:
    code = result[0]
  except TypeError:
    code = result
  if code < 0:
    raise Exception, 'Aardvark access failure code %d' % result[0]
  return result

# Find an Aardvark for GPIO
(num, ports, unique_ids) = aa_find_devices_ext(16, 16)
for port in ports:
  if not (port & AA_PORT_NOT_FREE):
    aardvark = check_result(aa_open(port))
    check_result(aa_configure(aardvark, AA_CONFIG_GPIO_ONLY))
    check_result(aa_target_power(aardvark, AA_TARGET_POWER_BOTH))
    break
else:
  raise Exception, 'Could not find Aardvark USB device'

# Aardvark GPIO configuration
GPIO_NC = 0x20 # Bitmask for normally closed switch position
GPIO_NO = 0x08 # Bitmask for normally open switch position

# Locate the PPC
print "Searching for PPC4"
for dev in glob('/dev/serial/by-id/*'):
  # FTDI and loon belong to a gxpr_bridge
  if dev.startswith('/dev/serial/by-id/usb-loon_'):
    continue
  if dev.startswith('/dev/serial/by-id/usb-FTDI_TTL232RG-VSW3V3'):
    continue
  # Assume it's a PPC and try talking to it in order to confirm
  try:
    ppc = ppc4.PPC4(dev)
    print "  %s: PPC4" % dev
    break
  except:
    print "  %s: Unknown" % dev
else:
  raise Exception, "FATAL: Could not locate PPC4"

# Open log file
out = open(sys.argv[1], 'wt')
out.write('"TIMESTAMP"')
out.write(',"RDY","PRES","RATE","ATM","STATUS","UNCERT"')
out.write(',"NC","NO"')
out.write('\n')
out.flush()

# Perform an individual test
def run_tests(fl):
  # Set the pressure
  meters = fl * 1E2 * altitude.meter_per_foot
  pres = altitude.altitude_to_pressure(meters) / 1E3
  print "  Setting pressure to %.3f kPa (FL%03.0f)" % (pres, fl)
  ppc.wait_pressure(pres)
  sleep(10.0)
  # Mesure a data point
  pres = ppc.status()
  gpio = aa_gpio_get(aardvark)
  out.write(datetime.now().isoformat())
  for v in pres:
      out.write(',%e' % v)
  out.write(',%d' % bool(~gpio & GPIO_NC))
  out.write(',%d' % bool(~gpio & GPIO_NO))
  out.write('\n')
  out.flush()

# Perform the sweep
print "Beginning test"
while True:
  for i in range(100):
    run_tests(i * 7 + 50)
  for i in range(100):
    run_tests(750 - i * 7)
