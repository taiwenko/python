#!/usr/bin/env python
import altitude
import argparse
import glob
import errno
import math
import ppc4
import re
import serial
import sys

from datetime import datetime
from os import makedirs
from time import sleep
from tools import shell

class UnitUnderTest(object):
  """Utility class to track the data associated with a specific bridge board"""
  sbvars = []
  sbvars.append('gxpr_bridge_barometric_pressure_raw')
  sbvars.append('gxpr_bridge_barometric_pressure')
  sbvars.append('gxpr_bridge_barometer_temperature')
  def __init__(self, dev, logdir='.', serial=None):
    """Create a new instance of UnitUnderTest"""
    # Create control structures
    self._dev = dev
    self._init()
    # Request serial number from unit
    if serial is None:
      serial_pattern = 'S/N: (\d+)\r'
      self._tom.sendline('test serial_number get')
      while self._tom.expect([shell.SHELL_PROMPT, serial_pattern]):
        serial = int(self._tom.match.group(1))
      if not serial:
        raise Exception, "Unknown serial number"
    self._serial = serial
    # Open the logfile
    # TODO: Check for preexisting log file
    logfile = '%s/bmp280cal-%s.csv' % (logdir, self._serial)
    self._log = open(logfile, 'wt')
    self._writeheader()
    print "  %s: S/N %s" % (dev, serial)
  def _init(self):
    self._tom = shell.Shell(self._dev, log=self.shell_log)
    self._sb = shell.Scoreboard(self._tom, 'gxpr_bridge')
  def _reinit(self):
    print 'ALERT: Lost communication with S/N %s, resetting' % self._serial
    sleep(5)
    self._tom.reset()
  def shell_log(self, logstr, *args, **kwargs):
    pass
  def measure(self, *args):
    for i in range(3):
      try:
        # Take the measurements
        ts = datetime.now().isoformat()
        sbmap = self._sb.query()
        break
      except:
        self._reinit()
    else:
      raise Exception, 'Unable to resynchronize with Major Tom'
    # Commit to logfile
    self._log.write(ts)
    for arg in args:
      try:
        self._log.write(',%e' % arg)
      except TypeError:
        self._log.write(',%s' % arg)
    for sbvar in UnitUnderTest.sbvars:
      try:
        self._log.write(',%e' % sbmap[sbvar][1])
      except TypeError:
        self._log.write(',%s' % sbmap[sbvar][1])
    self._log.write('\n')
    self._log.flush()
  def temp(self, kelvin):
    for i in range(3):
      try:
        # Use the barometer's heater to sample different temperatures
        self._tom.send_command('test set_baro_thermostat %f' % kelvin)
        break
      except:
        self._reinit()
    else:
      raise Exception, 'Unable to resynchronize with Major Tom'
  def _writeheader(self):
    # Write file header
    self._log.write('"TIMESTAMP"')
    # Fluke Measurements
    self._log.write(',"RDY","PRES","RATE","ATM","STATUS","UNCERT"')
    # Major Tom Variables
    for sbvar in UnitUnderTest.sbvars:
        self._log.write(',"%s"' % sbvar)
    self._log.write('\n')
    self._log.flush()

# Base serial numbers from the time when testing started
default_serial = int((datetime.utcnow() - datetime(2014, 1, 1)).total_seconds())
parser = argparse.ArgumentParser(description='Mass Calibration Script')
parser.add_argument('--min-altitude',
    metavar='flight-level', type=float, default=10.0,
    help='Lowest altitude to include in altitude sweep')
parser.add_argument('--max-altitude',
    metavar='flight-level', type=float, default=700.0,
    help='Highest altitude to include in altitude sweep')
parser.add_argument('--count-altitude',
    metavar='count', type=int, default=30,
    help='Number of points to test when sweeping the altitude')
parser.add_argument('--settle-altitude',
    metavar='seconds', type=float, default=30.0,
    help='Desired system settling time after pressure changes')
parser.add_argument('--settle-timeout',
    metavar='seconds', type=float, default=1800.0,
    help='Maximum time to wait for pressure stabilization before resetting')
parser.add_argument('--hold-limit',
    metavar='kPa', type=float, default=0.02,
    help='Required precision for the PPC4')
parser.add_argument('--passes',
    metavar='count', type=int, default=2,
    help='Number of up-down pressure passes per test temperature')
parser.add_argument('--min-temperature',
    metavar='kelvin', type=float, default=293.15,
    help='Lowest temperature to use for the temperature sweep')
parser.add_argument('--max-temperature',
    metavar='kelvin', type=float, default=313.15,
    help='Highest temeprature to use for the temperature sweep')
parser.add_argument('--count-temperature',
    metavar='count', type=int, default=4,
    help='Number of points to test when sweeping the temperature')
parser.add_argument('--settle-temperature',
    metavar='seconds', type=float, default=30.0,
    help='Desired system settling time after temperature changes')
parser.add_argument('--logs',
    metavar='directory', type=str, default='.',
    help='Directory to store per-unit calibration logs')
parser.add_argument('--volume',
    metavar='cc', type=float, default=None,
    help='Optional test volume hint for the PPC4')
parser.add_argument('--soak',
    metavar='seconds', type=float, default=None,
    help='Optional low pressure soak prior to test')
parser.add_argument('--soak-pressure',
    metavar='kPa', type=float, default=5.0,
    help='Target pressure for the low pressure soak')
parser.add_argument('--soak-temperature',
    metavar='kelvin', type=float, default=340.0,
    help='Target temperature for the low pressure soak')
args = parser.parse_args()

# Locating the serial devices
ppc = None
units = []
error = False

# Used for searching for specific serial devices
def serial_glob(manu, model, intf=0, port=0):
  globstr = '/dev/serial/by-id/usb-%s_%s_*-if%02d-port%d' \
      % (manu, model, intf, port)
  regstr = '^/dev/serial/by-id/usb-%s_%s_(.*)-if%02d-port%d$' \
      % (manu, model, intf, port)
  return [(dev, re.search(regstr, dev).group(1)) for dev in glob.glob(globstr)]

# Get the list of v1 bridges
print "Locating Version 1.1 Bridges"
for (dev, serial) in serial_glob('FTDI', 'TTL232RG-VSW3V3'):
  # This serial applies to the cable so we can't use it
  try:
    units.append(UnitUnderTest(dev, logdir=args.logs))
  except Exception, e:
    print "  %s: %s" % (dev, str(e).split('\n')[0])
    error = True

# Get the list of v2 bridges
print "Locating Version 2.1 Bridges"
for (dev, serial) in serial_glob('loon', 'gxprbridge', 3):
  try:
    units.append(UnitUnderTest(dev, logdir=args.logs, serial=serial))
  except Exception, e:
    print "  %s: %s" % (dev, str(e).split('\n')[0])
    error = True

# Look for the PPC on the remaining serial ports
print "Searching for PPC4"
for dev in glob.glob('/dev/serial/by-id/*'):
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
  print "FATAL: Could not locate PPC4"
  sys.exit(1)

# Verify we located all the bridges
if len(units) == 0:
  print "FATAL: Could not locate any units for calibration"
  sys.exit(1)
if error:
  print "WARNING: One or more units could not be confirmed"
  s = raw_input('Continue? [y/N]')
  if not s.lower().startswith('y'):
    sys.exit(1)

# Initialize the PPC4 access object
print "Accessing PPC4"
print "  Venting PPC4"
ppc.vent()
while not ppc.vented():
  pass
print "  Configuring PPC4"
ppc.autorange(102, 'kPa')
ppc.mode(ppc4.DYNAMIC_CONTROL)
ppc.hold_limit(args.hold_limit)

# Begin a soak if requested
if args.soak is not None:
  print "Beginning low pressure soak"
  print "  Setting soak temperature"
  for unit in units:
    unit.temp(args.soak_temperature)
  print "  Setting pressure"
  ppc.wait_pressure(args.soak_pressure, volume=args.volume)
  print "  Soaking"
  sleep(args.soak)
  print "  Resetting temperature"
  for unit in units:
    unit.temp(args.min_temperature)

# Compute stepping parameters
# For temperature, N points gives us N-1 regions
if args.count_temperature > 1:
  temp_step = (args.max_temperature - args.min_temperature) \
          / (args.count_temperature - 1)
else:
  temp_step = 0
# For pressure, the ramp means that the max/min points are used half as many
# times as the others.  Having N points per slope means we still end up with
# N regions.
pres_step = (args.max_altitude - args.min_altitude) / args.count_altitude
print "Sweeping from FL%03.0f to FL%03.0f in %d steps." \
    % (args.min_altitude, args.max_altitude, pres_step)

# Helper function to sweep temperature at a specific pressure
def run_tests(fl):
  # Set the pressure
  meters = fl * 1E2 * altitude.meter_per_foot
  pres = altitude.altitude_to_pressure(meters) / 1E3
  print "    Setting pressure to %.3f kPa (FL%03.0f)" % (pres, fl)
  ppc.wait_pressure(pres, stable=args.settle_altitude, \
    timeout=args.settle_timeout, volume=args.volume)
  # Sweep Temperature
  for temp_idx in range(args.count_temperature):
    # Set temperature on device
    temp = temp_idx * temp_step + args.min_temperature
    print "      Setting Temperature to %g" % temp
    for unit in units:
      unit.temp(temp)
    # Wait for stabilization
    sleep(args.settle_temperature)
    # Make the measurements
    print "        Taking measurements"
    for unit in units:
      pres = ppc.status()
      unit.measure(*pres)
  # Return temperature to minimum so it can cool during pressure change
  if args.count_temperature > 1:
    print "      Resetting Temperature to %g" % args.min_temperature
    for unit in units:
      unit.temp(args.min_temperature)

# Schedule sweeps
for pass_idx in range(args.passes):
  print "  Beginning sweep number %d of %d" % (pass_idx+1, args.passes)
  # Down sweep
  for sweep_idx in range(args.count_altitude):
    run_tests(args.min_altitude + pres_step * sweep_idx)
  # Up sweep
  for sweep_idx in range(args.count_altitude):
    run_tests(args.max_altitude - pres_step * sweep_idx)

# Clean up after ourselves
print "Tests Completed"
print "  Resetting Temperature to %g" % args.min_temperature
for unit in units:
  unit.temp(args.min_temperature)
print "  Venting PPC4"
ppc.vent()
