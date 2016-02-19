#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the battery_ambient_test
# Author: TaiWen Ko
# Date: 2015-1-16

import xpf6020
import bk8500
import math
import os

from datetime import datetime
from time import sleep

import tools.utils as tools
from tools import shell

# Make sure to use the correct serial-to-usb cable
ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5029ID1-if00-port0'
pfc_path = '/dev/serial/by-id/usb-FTDI_Dual_RS232-HS-if01-port0'

# Charge battery @ 50V and 2A max
print "Accessing the XPF6020 Power Supply"
ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1,50) 
ps.set_currentlimit(1,2)

# Discharge battery @ CV mode, 46V, and 50V max
print "Accessing the BK8500 Electronic Load"
bkload = bk8500.Bk8500()
bkload.remote_switch('on')
bkload.config_cv_mode(46,50)

print "Accessing the Payload"
tom = shell.Shell(pfc_path)
sb = shell.Scoreboard(tom,'battery')


def print_line():

  print ' '

def fs_format():

  print 'Formatting the SD card...'
  tom.sendline('fs format')
  # wait for sd to format
  sleep(20)

def batt_charging():
  
  ts = get_timestamp()
  print 'Charging the battery...[' + ts + ']'
  
  ps.ind_output('1','on')
  sleep(1)
  
  target_soc = 100
  monitor_freq = 5
  check_batt_charge(target_soc, monitor_freq)
  
  ps.set_currentlimit(1,0)
  sleep(1)
  
  soc = str(sb.query('battery0_soc_percent'))
  current_soc = soc.split("'")[3]
  ts = get_timestamp()
  print 'Battery is now charged to ' + current_soc + '%...[' + ts + ']' 

def batt_discharging():
  
  ts = get_timestamp()
  print 'Discharging the battery...[' + ts + ']'
  
  bkload.load_switch('on')
  sleep(2)
  tom.sendline('power on acs')
  sleep(2)
  
  target_soc = 0 
  monitor_freq = 5
  check_batt_discharge(target_soc, monitor_freq)
  
  tom.sendline('power off acs')
  sleep(1)
  bkload.load_switch('off')
  sleep(1)
  
  soc = str(sb.query('battery0_soc_percent'))
  current_soc = soc.split("'")[3]
  ts = get_timestamp()
  print 'Battery is now discharged to ' + current_soc + '%...[' + ts + ']'
  print_line()

def check_batt_charge(target_soc, monitor_freq):

  # Get initial SOC percent
  soc = str(sb.query('battery0_soc_percent'))
  current_soc = soc.split("'")[3]
  
  # Monitor SOC percent
  while float(current_soc) < float(target_soc):
    soc = str(sb.query('battery0_soc_percent'))
    current_soc = soc.split("'")[3]
    sleep(monitor_freq)
    ts = get_timestamp()
    print 'Battery0_soc_percent is ' + current_soc + '...[' + ts + ']'  


def check_batt_discharge(target_soc, monitor_freq):

  # Get initial SOC percent
  soc = str(sb.query('battery0_soc_percent'))
  current_soc = soc.split("'")[3]
  
  # Monitor SOC percent
  while float(current_soc) > float(target_soc):
    soc = str(sb.query('battery0_soc_percent'))
    current_soc = soc.split("'")[3]
    sleep(monitor_freq)
    ts = get_timestamp()
    print 'Battery0_soc_percent is ' + current_soc + '...[' + ts + ']'  
    
    
def get_timestamp():

  dt = datetime.now()
  dt = dt.replace(microsecond=0)
  return str(dt)


# Test starts here: 
print_line()
ts = get_timestamp()
print '****Battery Temperature Test started...[' + ts + ']****'
print_line()
fs_format()
batt_charging()
batt_discharging()
ts = get_timestamp()
print '****Cycle '+ str(cycle) + ' completed...[' + ts + ']****'
