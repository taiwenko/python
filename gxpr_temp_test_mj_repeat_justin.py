#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the gxpr_temp_test with Major Tom
# Author: TaiWen Ko

import aeroflex
import xpf6020
import watlowf4
import instrument
import multitest_justin as multitest
import argparse
import glob
import re
import sys
import twk_utils
import gxpr_utils

from datetime import datetime
from time import sleep
from tools import newshell as shell

utils = twk_utils.Twk_utils()

parser = argparse.ArgumentParser(description='Transponder Temperature Test Script')
parser.add_argument('cycle',
        help='Number of temperature cycle')
parser.add_argument('max_uut',
        help='Number of UUTs')
parser.add_argument('logfile',
        help='CSV file to append new measurements')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

sorensen_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A703PO3I-if00-port0'
aero_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AJ03ALVY-if00-port0'
tchamber_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A603R0MG-if00-port0'

print "Accessing the RF Switch"
mini = instrument.InstLabBrickSwitch()
mini.connect()
mini._outchannel(1) #initialze 

print "Accessing the Power Supply"
sore = xpf6020.Xpf6020(sorensen_path)
# Reset and check connection
sore.reset_ps()
sore.set_voltage(1,24)
sore.set_currentlimit(1,2)
sleep(1)
sore.ind_output(1,'on')
sleep(10)

print "Accessing the Temperature Chamber"
chamber = watlowf4.WatlowF4(tchamber_path)
# Reset and check connection
chamber.conditioning_on(False)

def cleanup():
  chamber.conditioning_on(False)
  sore.all_output('off')


# Locating the serial devices
units = []
error = False

# Get the list of v2 bridges
print "Locating Version 2.1 Bridges"
for (dev, serial, gxprserial) in gxpr_utils.serial_glob('loon', 'gxprbridge', 3):
  try:
    print 'gxprserial', gxprserial
    units.append(multitest.UnitUnderTest(dev, logdir=args.logfile, serial=serial, aero_path=aero_path, gxprserial=gxprserial))
  except Exception, e:
    print "  %s: %s" % (dev, str(e).split('\n')[0])
    error = True

# Verify we located all the bridges
if len(units) == 0:
  print "FATAL: Could not locate any units for calibration. Make sure there are no logs with the same name."
  cleanup()
  sys.exit(1)
if error:
  print "WARNING: One or more units could not be confirmed"
  s = raw_input('Continue? [y/N]')
  if not s.lower().startswith('y'):
    cleanup()
    sys.exit(1)

# Match Bridge Unit to RF Channel
def gxpr2switch():

  channel = 0
  ch_array = []

  while channel != int(args.max_uut):

    match = []
    count = 1
    channel = channel + 1

    mini._outchannel(channel)
    sleep(1)  # wait for switch to settle
    
    for unit in units:
      unit.access_aero(aero_path)
      break
    
    for unit in units:
      match = unit.check_inter_count()
      if match[0] == '0':
         count = count + 1
      else:
         print match
         #gxpr_sn = match[1][1]
	 gxpr_sn = unit._gxprserial
	 
         print "RF switch channel " + str(channel) + " is connected to GXPR S/N " + gxpr_sn + " and Bridge Unit " + str(count) + " SN " + unit._serial
         ch_array.append(count)
         unit.gxpr_power('off')
         sleep(2)
         unit.gxpr_power('on')
         sleep(8)
         break
    
  return ch_array


def aeromeasure(ch_array):

  channel = 0

  while channel != int(args.max_uut):

    channel = channel + 1
    count = 1

    mini._outchannel(channel)
    sleep(2)  # wait for switch to settle

    print "Measuring output channel " + str(channel) + " ..."

    # Take measurements
    for unit in units:
      if ch_array[channel-1] == count:
      	unit.measure(channel, aero_path)
      	break
      else:
        count = count + 1

# Get GXPR to RF switch relationship
ch_array = gxpr2switch()
print ch_array
print len(ch_array)
if len(ch_array) != int(args.max_uut):
  print "FATAL: Could not locate all units for testing. Please check USB connection"
  cleanup()
  sys.exit(1)

# Turn off power supply.
#sore.all_output('off')
for unit in units:
  unit.gxpr_power('off')
sleep(1)

# Temperature Cycling
# 1. Rise temperature to hot_temp to burn off excess moister in chamber
# 2. Drop temperature to ambient_temp 
# 3. Drop temperature to cold_start to test cold start
# 4. Turn on GXPR power and measure IFR6000 and SB
# 5. Rise temperature to cold_temp
# 6. Measure IFR6000 and SB
# 7. Rise temperature to ambient_temp
# 8. Measure IFR6000 and SB
# 9. Rise temperature to hot_temp
# 10. Measure IFR6000 and SB

# Temperature Profile
cold_start = -35
cold_temp = -20
ambient_temp = 20
hot_temp = 50
soaktime = 20

print "GXPR temperature test started"

max_cycle = args.cycle
cycle = 0

chamber.conditioning_on(True)

# Burn off excessive moisture
chamber.ramp_up(hot_temp) 
chamber.soak_time(soaktime) 

while cycle != int(max_cycle):

  cycle = cycle + 1

  chamber.ramp_down(cold_start)
  chamber.soak_time(soaktime)

  #sore.all_output('on') # power on the GXPRs
  for unit in units:
    unit.gxpr_power('on')
  sleep(60)  # wait for the GXPRs to turn on
  aeromeasure(ch_array)  # measure @ cold start

  chamber.ramp_up(cold_temp)
  chamber.soak_time(soaktime)
  aeromeasure(ch_array)  # measure @ cold temp 

  chamber.ramp_up(ambient_temp)
  chamber.soak_time(soaktime)
  aeromeasure(ch_array)  # measure @ ambient temp

  chamber.ramp_up(hot_temp)
  chamber.soak_time(soaktime)
  aeromeasure(ch_array)  # measure @ hot temp

  print 'Cycle %s completed.' % cycle
  #sore.all_output('off') # no power until cold start
  for unit in units:
    unit.gxpr_power('off')
  sleep(1)
  mini._outchannel(1)    # reset switch

#clean up
chamber.ramp_down(ambient_temp)
chamber.soak_time(soaktime)
chamber.conditioning_on(False)
sore.all_output('off')

ts = utils.get_timestamp()
print '*** GXPR temperature test completed @ %s***' % ts
utils.send_email('GXPR Temperature Test', 'GXPR temperature test is done!!')

