#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the battery_baseline_temp_test
# Author: TaiWen Ko
# Date: 2015-02-03

import twk_utils
import bk8500
import math
import os

from time import sleep

import tools.utils as tools
from tools import shell

# Accessing emails
utils = twk_utils.Twk_utils()

pfc_path = '/dev/serial/by-id/usb-FTDI_Dual_RS232-HS-if01-port0'

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

  while float(current_time) < float(wait_time):
    soc = str(sb.query('battery0_soc_percent'))
    current_soc = soc.split("'")[3]
    ts = utils.get_timestamp()
    print 'Battery0_soc_percent is %s...[%s]' % (current_soc, ts)
    [r_load_v, r_load_i] = bkload.read()
    logfile.write('%s,' % ts)
    logfile.write('%s,' % cycle)
    logfile.write('%s,' % current)
    logfile.write('%s,' % r_load_i)
    logfile.write('%s\n' % current_soc)
    sleep(monitor_freq)
    current_time = current_time + monitor_freq

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
    logfile.write('SOC\n')
    logfile.flush()

# Test starts here:
ts = utils.get_timestamp()
print 'Soaking for 8 hours...[%s]' % ts
sleep(28800)
utils.print_line()

ts = utils.get_timestamp()
print '****Battery Baseline Temperature Test started...[%s]****' % ts
utils.print_line()

print 'Formatting the SD card...'
tom.sendline('fs format')
sleep(20)
utils.print_line()

cycle = 1
current1 = 0.6
current2 = 0.4
wait_time = 3600 # 1hr
monitor_freq = 60 # every min.

while True:

  batt_discharging(current1, wait_time, monitor_freq, cycle)
  batt_discharging(current2, wait_time, monitor_freq, cycle)

  ts = utils.get_timestamp()
  message1 = '****Cycle %s completed...[%s]****' % (cycle, ts)
  print message1
  utils.print_line()

  soc = str(sb.query('battery0_soc_percent'))
  current_soc = soc.split("'")[3]
  message2 = 'Battery0_soc_percent is %s' % current_soc
  print message2

  utils.send_email('Battery Baseline Test Update', message1 + ' ; ' + message2)

  cycle = cycle + 1