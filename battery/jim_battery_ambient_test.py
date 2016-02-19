#!/usr/bin/env python

# Routines for the jim_hydra_battery_ambient_test
# Author: TaiWen Ko

import xpf6020
import bk8500
import math
import os
import twk_utils

from datetime import datetime
from time import sleep

utils = twk_utils.Twk_utils()

# Charge battery @ 50V and 2A max
#ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5029ID1-if00-port0'
ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A703U53P-if00-port0'
ps_volt = 50.4
ps_current = 3.3
print "Accessing the XPF6020 Power Supply"
ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1, ps_volt)
ps.set_currentlimit(1, ps_current)

# Discharge battery @ CV mode, 46V, and 50V max
print "Accessing the BK8500 Electronic Load"
bkload = bk8500.Bk8500()
bkload.remote_switch('on')

# Write headers
ts = utils.get_timestamp()
logdir = '../hydra_batt_test-%s.csv' % ts
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP,')
    logfile.write('DIRECTION,')
    logfile.write('VOLTAGE(V),')
    logfile.write('CURRENT(A)\n')
    logfile.flush()

def batt_charging(target_volt, monitor_freq, timeout):

  ts = utils.get_timestamp()
  print 'Charging the battery...[%s]' % ts

  ps.ind_output('1','on')
  sleep(5)

   # Get initial battery voltage
  [current_volt, current_curr] = ps.measure('1')
  current_volt = current_volt.split('V')[0]

  # Monitor battery voltage while charging
  charge_time = 0
  while float(current_volt) < float(target_volt):
    if charge_time < timeout:
      sleep(monitor_freq)
      charge_time = charge_time + monitor_freq
      print charge_time
      [current_volt, current_curr] = ps.measure('1')
      ts = utils.get_timestamp()
      print 'Battery Voltage is %sV...[%s]' % current_volt, ts
      logfile.write('%s,' % ts)
      logfile.write('Charging,')
      logfile.write('%s,' % current_volt)
      logfile.write('%s\n,' % current_curr)
    else:
      break

  ps.set_currentlimit(1,0)
  sleep(5)

  [current_volt, current_curr] = ps.measure('1')
  ts = get_timestamp()
  print 'Battery is now charged to %sV...[%s]' % current_volt, ts

def batt_discharging(target_volt, monitor_freq, current, max_current, timeout):

  ts = utils.get_timestamp()
  print 'Discharging the battery...[%s]' % ts

  bkload.config_cc_mode(current, max_current)
  bkload.load_switch('on')
  sleep(5)

  # Get initial battery voltage
  [current_volt, current_curr] = bk8500.read()

  # Monitor battery voltage while discharging
  discharge_time = 0
  while float(current_volt) > float(target_volt):
    if charge_time < timeout:
      sleep(monitor_freq)
      discharge_time = discharge_time + monitor_freq
      print discharge_time
      [current_volt, current_curr] = bk8500.read()
      ts = utils.get_timestamp()
      print 'Battery Voltage is %sV...[%s]' % current_volt, ts
      logfile.write('%s,' % ts)
      logfile.write('Discharging,')
      logfile.write('%s,' % current_volt)
      logfile.write('%s\n,' % current_curr)
    else:
      break

  bkload.load_switch('off')
  sleep(5)

  [current_volt, current_curr] = bk8500.read()
  ts = utils.get_timestamp()
  print 'Battery is now discharged to %sV...[%s]' % current_volt, ts



# Test starts here:
charge_target = 50.4
discharge_target = 45

# in sec
charge_timeout = 10 #43200 # 12 hours
discharge_timeout = 10 #43200 # 12 hours
monitor_freq = 10

ts = utils.get_timestamp()
print '****Battery Tests started...[%s]****' % ts
utils.print_line()

# Test 1
batt_charging(charge_target, monitor_freq, charge_timeout)
batt_discharging(discharge_target, monitor_freq, 0.3, 2, discharge_timeout)

ts = utils.get_timestamp()
print '****Battery Test 1 completed...[%s]****' % ts
utils.print_line()

# Test 2
batt_charging(charge_target, monitor_freq, charge_timeout)
batt_discharging(discharge_target, monitor_freq, 0.5, 2, discharge_timeout)

ts = utils.get_timestamp()
print '****Battery Test 2 completed...[%s]****' % ts
utils.print_line()

# Test 3
batt_charging(charge_target, monitor_freq, charge_timeout)
batt_discharging(discharge_target, monitor_freq, 0.7, 2, discharge_timeout)

ts = utils.get_timestamp()
print '****Battery Test 3 completed...[%s]****' % ts
utils.print_line()

ts = utils.get_timestamp()
msg = '*** Hydra Battery Tests completed @ %s***' % ts

utils.send_email('Hydra Battery Tests', msg)

