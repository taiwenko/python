##!/usr/bin/env python

import argparse
import aeroflex
import errno
import math
import re
import serial
import sys
import os
import time

from datetime import datetime
from os import makedirs
from time import sleep
from tools import shell

class UnitUnderTest(object):
  
  # change the sbvars will affect the gxpr_temp matlab script
  """Utility class to track the data associated with a specific bridge board"""
  sbvars = []
  sbvars.append('version_hash_gxpr_bridge')
  sbvars.append('version_hash_gxpr')
  sbvars.append('gxpr_system_state')
  sbvars.append('gxpr_system_error')
  sbvars.append('gxpr_target_power')
  sbvars.append('gxpr_has_power')
  #sbvars.append('gxpr_serial_number')
  sbvars.append('version_hash_gxpr_bridge')
  sbvars.append('version_hash_gxpr_fpga')
  sbvars.append('gxpr_fpga_core_rail_voltage')
  sbvars.append('gxpr_fpga_logic_rail_voltage')
  sbvars.append('gxpr_driver_rail_voltage')
  sbvars.append('gxpr_pa_rail_voltage')
  sbvars.append('gxpr_vin_rail_voltage')
  sbvars.append('gxpr_tx_temperature')
  sbvars.append('gxpr_mode_a_interrogation_count')
  sbvars.append('gxpr_mode_a_transmission_count')
  sbvars.append('gxpr_mode_c_interrogation_count')
  sbvars.append('gxpr_mode_c_transmission_count')
  sbvars.append('gxpr_barometer_target_heater_setpoint')
  sbvars.append('gxpr_barometer_heater_setpoint')
  sbvars.append('gxpr_barometer_heater_on')
  sbvars.append('transponder_squawk_code')
  sbvars.append('transponder_mode')

  sbchecks = 'gxpr_mode_a_interrogation_count'

  def __init__(self, dev, logdir='.', serial=None, aero_path='.'):
    """Create a new instance of UnitUnderTest"""
    # Create control structures

    aero = aeroflex.Aeroflex(aero_path)
    aerovars = aeroflex.fields()
    
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
    # Open logfile and check if file exists before write
    logfile = '%s-temptest-%s.csv' % (logdir, self._serial)
    if os.path.exists(logfile):
      message = raw_input('File path: %s already exists. Wish to overwrite? [y/N] ' % (logfile))
      if message != 'y':
        logfile = raw_input('What is the new file path? ' )
        while True:
          if os.path.exists(logfile):
            logfile = raw_input('New file path also exists. Got another one? ' )       
          else:
            break;
    print("Write measurements into " + logfile)
    self._log = open(logfile, 'wt')
    self._writeheader(aerovars)
  
  def _init(self):
    self._tom = shell.Shell(self._dev, log=self.shell_log)
    self._sb = shell.Scoreboard(self._tom, 'gxpr_bridge')
  
  def _reinit(self):
    print 'ALERT: Lost communication with S/N %s, resetting' % self._serial
    sleep(5)
    self._tom.reset()

  def shell_log(self, logstr, *args, **kwargs):
    pass

  def gxpr_power(self, switch):

    if switch == 'off':
      for i in range(3):
        try:
          # Take the measurements
          self._tom.sendline('test power off')
          print 'Disable power to the GXPR'
          break
        except:
          self._reinit()
      else:
        raise Exception, 'Unable to resynchronize with Major Tom'
    elif switch == 'on':
      for i in range(3):
        try:
          # Take the measurements
          self._tom.sendline('test power on')
          print 'Enable power to the GXPR!'
          break
        except:
          self._reinit()
      else:
        raise Exception, 'Unable to resynchronize with Major Tom'

  def access_aero(self, aero_path):
    # Create control structures
    print "Accessing the Aeroflex"
    aero = aeroflex.Aeroflex(aero_path)
    aeromap = aero.measure()

  def check_inter_count(self):
    
    for i in range(3):
      try:
        sbmap = self._sb.query()
        break
      except:
        self._reinit()
    else:
      raise Exception, 'Unable to resynchronize with Major Tom'

    check_col = UnitUnderTest.sbchecks
    inter_count = sbmap[check_col][1]
    if inter_count == '0':
      return ['0', '0']
    else:
      # gxpr_sn = sbmap['gxpr_serial_number']
      gxpr_sn = inter_count
      return [inter_count, gxpr_sn]

  def measure(self, channel, aero_path):

    # Create control structures
    print "Accessing the Aeroflex"
    aero = aeroflex.Aeroflex(aero_path)
    aerovars = aeroflex.fields()
    
    for i in range(3):
      try:
        # Take the measurements
        ts1 = datetime.now().isoformat()
        sbmap = self._sb.query()
        break
      except:
        self._reinit()
    else:
      raise Exception, 'Unable to resynchronize with Major Tom'

    # Take the measurements
    ts2 = datetime.now().isoformat()
    aeromap = aero.measure()
    ts3 = datetime.now().isoformat()
    if aeromap['overall'] == 'NREP':
    	print "  GXPR Status: No Reply"
    elif aeromap['overall'] == 'FAIL':
        print "  GXPR Status: Replied"
  
    # Commit to logfile
    self._log.write(ts1)
    for sbvar in UnitUnderTest.sbvars:
      try:
        self._log.write(',%e' % sbmap[sbvar][1])
      except TypeError:
        self._log.write(',%s' % sbmap[sbvar][1])

    self._log.write(',%s' % ts2)
    self._log.write(',%s' % channel)
    for var in aerovars:
        try:
            self._log.write(',%e' % aeromap[var])
        except TypeError:
            self._log.write(',%s' % aeromap[var])
    self._log.write(',%s\n' % ts3)
    self._log.flush()

  def _writeheader(self, aerovars):
    # Write file header
    self._log.write('TIMESTAMP')
    # Major Tom Variables
    for sbvar in UnitUnderTest.sbvars:
        self._log.write(',%s' % sbvar)
    # Aeroflex Variales
    self._log.write(',TIMESTAMP')
    self._log.write(',OUTCHANNEL')
    for var in aerovars:
        self._log.write(',%s' % var)
    self._log.write(',TIMESTAMP\n')
    self._log.flush()
