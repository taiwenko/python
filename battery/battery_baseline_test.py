#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the battery_baseline_temp_test
# Author: TaiWen Ko
# Date: 2015-02-03

import twk_utils
import bk8500
import xpf6020
import math
import os
import sys

from time import sleep

import tools.utils as tools
from tools import shell

# Accessing emails
utils = twk_utils.Twk_utils()

pfc_path = '/dev/serial/by-id/usb-FTDI_Dual_RS232-HS-if01-port0'
ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5029ID1-if00-port0'

# Charge battery
print "Accessing the XPF6020 Power Supply"

batt_vin = 49.8
batt_iin = 2

ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1,batt_vin) 
ps.set_currentlimit(1,batt_iin)

print "Accessing the BK8500 Electronic Load"
bkload = bk8500.Bk8500()
bkload.remote_switch('on')

print "Accessing the Payload"
tom = shell.Shell(pfc_path)
sb = shell.Scoreboard(tom,'battery')

def batt_discharging(current, wait_time, monitor_freq, cycle):
  
  ts = utils.get_timestamp()
  print 'Discharging the battery @ %s A...[%s]' % (current, ts)
  
  max_current = current * 1.5
  bkload.config_cc_mode(current, max_current)
  sleep(1)
  bkload.load_switch('on')
  sleep(2)
  tom.sendline('power on acs')
  sleep(2)

  check_batt_discharge(current, wait_time, monitor_freq, cycle)
  
def check_batt_discharge(current, wait_time, monitor_freq, cycle):

  current_time = 0
  while float(current_time) < float(wait_time):

    soc = safe_blocking_query('battery0_soc_percent')
    current_soc = soc.split("'")[3]
    ts = utils.get_timestamp()
    print 'Battery0_soc_percent is %s...[%s]' % (current_soc, ts)

    volt = safe_blocking_query('battery0_voltage')
    current_volt = volt.split("'")[3]
    ts = utils.get_timestamp()
    print 'Battery0_voltage is %s...[%s]' % (current_volt, ts)

    avg_i = safe_blocking_query('battery0_average_current')
    current_avg_i = avg_i.split("'")[3]
    ts = utils.get_timestamp()
    print 'Battery0_average_current is %s...[%s]' % (current_avg_i, ts)

    [r_load_v, r_load_i] = bkload.read()
    logfile.write('%s,' % ts)
    logfile.write('%s,' % cycle)
    logfile.write('%s,' % current)
    logfile.write('%s,' % r_load_i)
    logfile.write('%s,' % current_soc)
    logfile.write('%s,' % current_volt)
    logfile.write('%s\n' % current_avg_i)  
    sleep(monitor_freq)
    current_time = current_time + monitor_freq

def shutdown():
  message = 'Received shutdown signal.  Shutting off.'
  print message
  ts = utils.get_timestamp()
  utils.send_email('Battery Baseline Test Update', message + ts)
  bkload.load_switch('off')
  sys.exit(0)

def safe_blocking_query(field):
  value = None
  num_tries = 1
  max_tries = 5
  while value is None and num_tries <= max_tries:
    try:
      value = str(sb.query(field))
    except:
      sleep(10)
      #sleep(60)
      num_tries += 1
  
  if num_tries > max_tries:
    print 'Querying field %s failed after %d tries.' % (field, max_tries)
    shutdown()
  elif:
    # re-setting the heater setpoint to 273
    tom.sendline('power heater 273')
  return value

def check_batt_temp(target_temp, tolerance):

  temp0 = str(sb.query('battery0_temperature0'))
  temp1 = str(sb.query('battery0_temperature1'))
  current_temp0 = temp0.split("'")[3]
  current_temp1 = temp1.split("'")[3]

  temp_max = target_temp * (1 + tolerance)
  temp_min = target_temp * (1 - tolerance)

  if float(temp_min) < float(current_temp0) < float(temp_max):
    if float(temp_min) < float(current_temp1) < float(temp_max):
      print 'Temp Check PASSED. All battery temperature are between ' + str(temp_min) + 'k to ' + str(temp_max) + 'k.'
    else:
      print 'Temp Check FAILED! Not all battery temperature are between ' + str(temp_min) + 'k to ' + str(temp_max) + 'k.'
  else:
    print 'Temp Check FAILED! Not all battery temperature are between ' + str(temp_min) + 'k to ' + str(temp_max) + 'k.'
  
  print 'Battery0_temperature0 is ' + current_temp0 + 'k and Battery0_temperature1 is ' + current_temp1 + 'k.'

# Write headers
ts = utils.get_timestamp()
filepath = '../Desktop/'
logdir = '%sbaseline_temp_test-%s.csv' % (filepath, ts)
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP,')
    logfile.write('CYCLE,')
    logfile.write('SET RATE,')
    logfile.write('ACTUAL RATE,')
    logfile.write('SOC,')
    logfile.write('Volt,')
    logfile.write('AVG I\n')
    logfile.flush()

# Test starts here:

# Turn on the battery
ps.all_output('on')
sleep(3)

# Set battery heater setpoint to 273
target_temp = 273
tolerance = 0.05
print 'Setting the heater to %sk...' % target_temp
tom.sendline('power heater 273')
utils.print_line()
ts = utils.get_timestamp()
print 'Soaking for 8 hours...[%s]' % ts
#sleep(28800)

# Check battery temperature after soaking 
utils.print_line()
check_batt_temp(target_temp, tolerance)
ps.all_output('off')
sleep(3)

ts = utils.get_timestamp()
print '****Battery Baseline Temperature Test started...[%s]****' % ts
utils.print_line()

# Erase the SD card for test
print 'Formatting the SD card...'
tom.sendline('fs format')
sleep(20)
utils.print_line()

cycle = 1
current1 = 0.5
current2 = 0.6
wait_time = 3600 # 1hr
monitor_freq = 60 # every min.

while True:

  # Discharge the battery @ two different rate every hr. 
  batt_discharging(current1, wait_time, monitor_freq, cycle)
  batt_discharging(current2, wait_time, monitor_freq, cycle)
  
  # Print Status to screen and to email 
  ts = utils.get_timestamp()
  message1 = '****Cycle %s completed...[%s]****' % (cycle, ts)
  print message1
  utils.print_line()

  soc = safe_blocking_query('battery0_soc_percent')
  current_soc = soc.split("'")[3]
  message2 = 'Battery0_soc_percent is %s' % current_soc
  print message2

  volt = safe_blocking_query('battery0_voltage')
  current_volt = volt.split("'")[3]
  message3 = 'Battery0_voltage is %s' % current_volt
  print message3

  avg_i = safe_blocking_query('battery0_average_current')
  current_avg_i = avg_i.split("'")[3]
  message4 = 'Battery0_average_current is %s' % current_avg_i
  print message4

  utils.send_email('Battery Baseline Test Update', message1 + '\n' + message2 + '\n' + message3 + '\n' + message4)

  cycle = cycle + 1