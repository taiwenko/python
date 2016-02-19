#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the mppt_temp_test
# Author: TaiWen Ko
# Date: 2014-12-22

import xpf6020
import chroma62020H
import bk8500
import watlowf4
import argparse
import math
import os

from datetime import datetime
from time import sleep

parser = argparse.ArgumentParser(description='MPPT Temperature Test Script')
parser.add_argument('cycle',
        help='Number of temperature cycle')
parser.add_argument('logfile',
        help='CSV file to append new measurements')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

# Make sure to use the correct serial-to-usb cable
ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A602FGGN-if00-port0'
chroma_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A603QW14-if00-port0'
# Mr. Freeze
chamber_path = '/dev/serial/by-id/usb-FTDI_UC232R_FTVTALKY-if00-port0'
# Easy Bake Oven
# chamber_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A603R0MG-if00-port0'

# Input
vin = 43
iin = 1.5

# Output (BK8500)
ch5_v = 46
ch5_i = 1.5 # can't be greater than ch5_i_max
ch5_i_max = 5 

print "Accessing the Power Supply"
ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1,vin)
ps.set_currentlimit(1,iin)

print "Accessing the BK Electronic Load"
bkload = bk8500.Bk8500()
bkload.remote_switch('on')
bkload.config_cc_mode(ch5_i, ch5_i_max)

print " Accessing the Chroma62020H"
chroma = chroma62020H.Chroma62020H()

print "Accessing the Temperature Chamber"
chamber = watlowf4.WatlowF4(chamber_path)

# Write headers
dt = datetime.now()
dt = dt.replace(microsecond=0)
logdir = '%smppt_temp_test-%s.csv' % (args.logfile, dt)
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP,')
    logfile.write('CURRENT(A),')
    logfile.write('VOLTAGE(V),')
    logfile.write('TEMPERATURE(C),')
    logfile.write('RESULT\n')
    logfile.flush()


def bkload_measure_check(current,voltage):
  
  ts = datetime.now().isoformat()
  temperature = chamber.get_temp()

  [r_ch5_v, r_ch5_i] = bkload.read()

  tolerance = 0.05
  current_max = current * (1 + tolerance)
  current_min = current * (1 - tolerance)
  voltage_max = voltage * (1 + tolerance)
  voltage_min = voltage * (1 - tolerance)

  if float(r_ch5_i) > float(current_max):
    result = 'FAILED'
  elif float(r_ch5_i) < float(current_min):
    result = 'FAILED'
  elif float(r_ch5_v) > float(voltage_max):
    result = 'FAILED'
  elif float(r_ch5_v) < float(voltage_min):
    result = 'FAILED'
  else:
    result = 'PASSED'
  print ('Ch5 ' + result + ' @ ' + str(r_ch5_v) + 'V, ' + str(r_ch5_i) + 'A')
  logfile.write('%s,' % ts)
  logfile.write('%s,' % r_ch5_i)
  logfile.write('%s,' % r_ch5_v)
  logfile.write('%s,' % temperature)
  logfile.write('%s\n' % result)

# Temperature Profile
cold_start = -60
ambient_temp = 20
hot_temp = 50
coldsoaktime = 10
hotsoaktime = 20
soaktime = 20

print "MPPT temperature test started"

max_cycle = args.cycle
cycle = 0

chamber.conditioning_on(True)

while cycle != int(max_cycle):

  cycle = cycle + 1

  chamber.ramp_down(cold_start)
  chamber.soak_time(coldsoaktime)
  bkload.load_switch('on')
  ps.all_output('on')
  # turn on chroma62020H and measure
  bkload_measure_check(ch5_i,ch5_v)

  chamber.ramp_up(hot_temp)
  chamber.soak_time(hotsoaktime)
  # turn on chroma62020H and measure
  bkload_measure_check(ch5_i,ch5_v)
  
  ps.all_output('off')
  bkload.load_switch('off')

  print 'Cycle %s completed.' % cycle
  sleep(1)

#clean up
bkload.remote_switch('off')
chamber.ramp_down(ambient_temp)
chamber.soak_time(soaktime)
chamber.conditioning_on(False)
print 'MPPT temperature test completed.'
