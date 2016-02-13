#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the rffe_temp_test
# Author: TaiWen Ko
# Date: 2014-11-20
#
# Change Log: 
# 2014-12-09: Added bk8500 driver to control and read the bk8500 eload.

import xpf6020
import chroma6312
import bk8500
import watlowf4
import argparse
import math
import os

from datetime import datetime
from time import sleep

parser = argparse.ArgumentParser(description='RFFE Temperature Test Script')
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
vin = 48
iin = 7
# Outputs A (Chroma6312)
ch1_v = 5.5
ch1_i = 3.0

ch2_v = 5
ch2_i = 1.5

ch3_v = 48
ch3_i = 1.0

ch4_v = 12
ch4_i = 4.25
# Outputs B (BK8500)
ch5_v = 5.5
ch5_i = 1.5 # can't be greater than ch5_i_max
ch5_i_max = 5 

print "Accessing the Power Supply"
ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1,vin)
ps.set_currentlimit(1,iin)

print "Accessing the Chroma Electronic Loads"
eloads = chroma6312.Chroma6312(chroma_path)
eloads.reset()
eloads.set_mode('1','CCH')  # 0-20A @ 5mA resolution
eloads.config_static_current('1',ch1_i)
eloads.set_mode('2','CCH')
eloads.config_static_current('2',ch2_i)
eloads.set_mode('3','CCH')
eloads.config_static_current('3',ch3_i)
eloads.set_mode('4','CCH')
eloads.config_static_current('4',ch4_i)
sleep(1)

print "Accessing the BK Electronic Load"
bkload = bk8500.Bk8500()
bkload.remote_switch('on')
bkload.config_cc_mode(ch5_i, ch5_i_max)

print "Accessing the Temperature Chamber"
chamber = watlowf4.WatlowF4(chamber_path)

# Write headers
dt = datetime.now()
dt = dt.replace(microsecond=0)
logdir = '%srffe_temp_test-%s.csv' % (args.logfile, dt)
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP,')
    logfile.write('CHANNEL,')
    logfile.write('CURRENT(A),')
    logfile.write('VOLTAGE(V),')
    logfile.write('TEMPERATURE(C),')
    logfile.write('RESULT\n')
    logfile.flush()

def measure_all_cold_load():

  ps.all_output('on')
  eloads_measure_check('3',ch3_i,ch3_v,1)
  eloads_measure_check('4',ch4_i,ch4_v,1)
  eloads_measure_check('1',ch1_i,ch1_v,1)
  eloads_measure_check('2',ch2_i,ch2_v,1)
  bkload_measure_check(ch5_i,ch5_v)

def measure_all_cold_noload():

  ps.all_output('on')
  eloads_measure_check('3',0,ch3_v,1)
  eloads_measure_check('4',0,ch4_v,1)
  eloads_measure_check('1',0,ch1_v,1)
  eloads_measure_check('2',0,ch2_v,1)
  bkload_measure_check(0,ch5_v)

def measure_all_hot():
  
  eloads_measure_check('3',ch3_i,ch3_v,1)
  eloads_measure_check('4',ch4_i,ch4_v,1)
  eloads_measure_check('1',ch1_i,ch1_v,1)
  eloads_measure_check('2',ch2_i,ch2_v,1)
  bkload_measure_check(ch5_i,ch5_v)

def eloads_measure_check(channel,current,voltage,cycle):
  eloads.set_channel(channel)
  r_channel = str(eloads.query_channel())
  if channel != r_channel:
    print 'Failed to config the correct load channel.'

  temperature = chamber.get_temp()

  ts = [] 
  r_current = []
  r_voltage = []

  for x in xrange(cycle):
    ts.append(datetime.now().isoformat())
    r_current.append(eloads.measure('current'))
    r_voltage.append(eloads.measure('voltage'))

  tolerance = 0.05
  current_max = current * (1 + tolerance)
  current_min = current * (1 - tolerance)
  voltage_max = voltage * (1 + tolerance)
  voltage_min = voltage * (1 - tolerance)
  
  for x in xrange(cycle):
    if r_current[x] > current_max:
      result = 'FAILED'
    elif r_current[x] < current_min:
      result = 'FAILED'
    elif r_voltage[x] > voltage_max:
      result = 'FAILED'
    elif r_voltage[x] < voltage_min:
      result = 'FAILED'
    else:
      result = 'PASSED'

    if x != (cycle-1):
      result = 'InProgress'

    print ('Ch' + r_channel + ' ' + result + ' @ ' + str(r_voltage[x]) + 'V, ' + str(r_current[x]) + 'A')
    logfile.write('%s,' % ts[x])
    logfile.write('%s,' % r_channel)
    logfile.write('%s,' % r_current[x])
    logfile.write('%s,' % r_voltage[x])
    logfile.write('%s,' % temperature)
    logfile.write('%s\n' % result)

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
  logfile.write('5,')
  logfile.write('%s,' % r_ch5_i)
  logfile.write('%s,' % r_ch5_v)
  logfile.write('%s,' % temperature)
  logfile.write('%s\n' % result)

# Temperature Cycling
# 1. Rise temperature to hot_temp to burn off excess moisture in chamber
# 2. Drop temperature to cold_start to test cold start
# 3. Turn on UUT power and measure
# 4. Rise temperature to hot_temp
# 5. Measure

# Temperature Profile
cold_start = -60
ambient_temp = 20
hot_temp = 50
coldsoaktime = 10
hotsoaktime = 20
soaktime = 20

print "RFFE temperature test started"

max_cycle = args.cycle
cycle = 0

chamber.conditioning_on(True)

while cycle != int(max_cycle):

  cycle = cycle + 1

  chamber.ramp_down(cold_start)
  chamber.soak_time(coldsoaktime)
  ps.all_output('on')
  chamber.soak_time(coldsoaktime)
  measure_all_cold_noload()
  eloads.load_switch('1','on') 
  eloads.load_switch('2','on')
  eloads.load_switch('3','on')
  eloads.load_switch('4','on')
  bkload.load_switch('on')
  chamber.soak_time(coldsoaktime)
  measure_all_cold_load()
  eloads.load_switch('1','off')
  eloads.load_switch('2','off')
  eloads.load_switch('3','off')
  eloads.load_switch('4','off')
  bkload.load_switch('off')
  ps.all_output('off')
  

  chamber.ramp_up(hot_temp)
  ps.all_output('on')
  eloads.load_switch('1','on') 
  eloads.load_switch('2','on')
  eloads.load_switch('3','on')
  eloads.load_switch('4','on')
  bkload.load_switch('on')
  chamber.soak_time(hotsoaktime)
  measure_all_hot()
  eloads.load_switch('1','off')
  eloads.load_switch('2','off')
  eloads.load_switch('3','off')
  eloads.load_switch('4','off')
  bkload.load_switch('off')
  ps.all_output('off')

  print 'Cycle %s completed.' % cycle
  sleep(1)

#clean up
eloads.disconnect()
bkload.remote_switch('off')
chamber.ramp_down(ambient_temp)
chamber.soak_time(soaktime)
chamber.conditioning_on(False)
print 'RFFE temperature test completed.'
