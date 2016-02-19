#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the battery_temp_test
# Author: TaiWen Ko
# Date: 2015-1-13

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

# Charge battery @ 12V and 5A max
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

def batt_init_check():
  
  target_temp = 263
  tolerance = 0.05
  check_batt_temp(target_temp, tolerance)

  print 'Formatting the SD card...'
  tom.sendline('fs format')
  # wait for sd to format
  sleep(20)

def batt_charging():
  
  ts = get_timestamp()
  print 'Charging the battery...[' + ts + ']'
  
  ps.ind_output('1','on')
  sleep(1)
  
  target_soc = 40 #95
  monitor_freq = 5
  check_batt_charge(target_soc, monitor_freq)

  print 'Setting the heater to 303k...'
  tom.sendline('power heater 303')
  
  target_temp_min = 303
  target_temp_max = 323
  wait_batt_temp(target_temp_min,target_temp_max) 
  
  ps.set_currentlimit(1, 0)
  sleep(1)

  print 'Setting the heater to 263k...'
  tom.sendline('power heater 263')
  
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
  
  target_soc = 20 
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

def wait_batt_temp(target_temp_min, target_temp_max):

  temp0 = str(sb.query('battery0_temperature0'))
  temp1 = str(sb.query('battery0_temperature1'))
  current_temp0 = temp0.split("'")[3]
  current_temp1 = temp1.split("'")[3]

  while float(target_temp_min) > float(current_temp0):
    ts = get_timestamp()
    if float(current_temp1) > float(target_temp_max):
      print 'Battery0_temperature1 exceeded max temp (323k) @ ' + current_temp1 + '...[' + ts + ']'
    else:
      print 'Battery0_temperature0 is ' + current_temp0 + 'k and Battery0_temperature1 is ' + current_temp1 + 'k...[' + ts + ']'
      temp0 = str(sb.query('battery0_temperature0'))
      temp1 = str(sb.query('battery0_temperature1'))
      current_temp0 = temp0.split("'")[3]
      current_temp1 = temp1.split("'")[3]

  while float(target_temp_min) > float(current_temp1):
    ts = get_timestamp()
    if float(current_temp0) > float(target_temp_max):
      print 'Battery0_temperature0 exceeded max temp (323k) @ ' + current_temp0 + '...[' + ts + ']'
    elif float(current_temp0) < float(target_temp_min):
      print 'Battery0_temperature0 dropped below min temp (303k) @ ' + current_temp0 + '...[' + ts + ']'
    else:
      print 'Battery0_temperature0 is ' + current_temp0 + 'k and Battery0_temperature1 is ' + current_temp1 + 'k...[' + ts + ']'
      temp0 = str(sb.query('battery0_temperature0'))
      temp1 = str(sb.query('battery0_temperature1'))
      current_temp0 = temp0.split("'")[3]
      current_temp1 = temp1.split("'")[3]
  
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
    
    # debug use only
    #current_soc = target_soc

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
    
    # debug use only
    #current_soc = target_soc

def get_timestamp():

  dt = datetime.now()
  dt = dt.replace(microsecond=0)
  return str(dt)


# Test starts here: 
print_line()
ts = get_timestamp()
print '****Battery Temperature Test started...[' + ts + ']****'
print_line()
batt_init_check()
cycle = 1

while True:
  batt_charging()
  batt_discharging()
  ts = get_timestamp()
  print '****Cycle '+ str(cycle) + ' completed...[' + ts + ']****'
  print_line()
  cycle = cycle + 1
