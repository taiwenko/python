#!/usr/bin/env python

# Copyright 2015 Google, Inc.
# Routines for the dual battery charging
# Author: TaiWen Ko
# Date: 2015-1-13

import xpf6020

from datetime import datetime
from time import sleep 

import tools.utils as tools
from tools import shell

# Make sure to use the correct serial-to-usb1 cable
ps_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'
ps1_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'
pfc1_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc-if01-port0'
pfc2_path = '/dev/serial/by-id/usb-FTDI_Dual_RS232-HS-if01-port0'
pfc3_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc-if01-port0'
pfc4_path = '/dev/serial/by-id/usb-FTDI_Dual_RS232-HS-if01-port0'

batt_num = None

while True:
    batt_num = raw_input('How many batteries would you like to charge? [ 1 ~ 4 ]: ')
    message = raw_input('Charging %s battery(s). Is this correct? [y/N]' % (batt_num))
    if message == 'y' and (batt_num == '1' or batt_num == '2' or batt_num == '3' or batt_num == '4'):
      break;

print "Accessing the XPF6020 Power Supply"
charge_v = 50 
charge_i = 10
ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1, charge_v) 
ps.set_currentlimit(1, charge_i)
if batt_num == '2':
  ps.set_voltage(2, charge_v)
  ps.set_currentlimit(2, charge_i)
elif: batt_num == '3':
  ps.set_voltage(2, charge_v)
  ps.set_currentlimit(2, charge_i)
  ps1 = xpf6020.Xpf6020(ps_path1)
  ps1.reset_ps()
  ps1.set_voltage(1, charge_v)
  ps1.set_currentlimit(1, charge_i)
elif: batt_num == '4':
  ps.set_voltage(2, charge_v)
  ps.set_currentlimit(2, charge_i)
  ps1 = xpf6020.Xpf6020(ps_path1)
  ps1.reset_ps()
  ps1.set_voltage(1, charge_v)
  ps1.set_currentlimit(1, charge_i)
  ps1.set_voltage(2, charge_v)
  ps1.set_currentlimit(2, charge_i)
else:
  raise Exception, 'Unknown command.'


print "Accessing the PFCs"
tom1 = shell.Shell(pfc1_path)
sb1 = shell.Scoreboard(tom1,'battery')
if batt_num == '2':
  tom2 = shell.Shell(pfc2_path)
  sb2 = shell.Scoreboard(tom2,'battery')
elif batt_num == '3':
  tom2 = shell.Shell(pfc2_path)
  sb2 = shell.Scoreboard(tom2,'battery')
  tom3 = shell.Shell(pfc3_path)
  sb3 = shell.Scoreboard(tom3,'battery')
elif batt_num == '4':
  tom2 = shell.Shell(pfc2_path)
  sb2 = shell.Scoreboard(tom2,'battery')
  tom3 = shell.Shell(pfc3_path)
  sb3 = shell.Scoreboard(tom3,'battery')
  tom4 = shell.Shell(pfc4_path)
  sb4 = shell.Scoreboard(tom4,'battery')
else:
  raise Exception, 'Unknown command.'


def batt_charging(target_soc, monitor_freq, batt_num):
  
  ts = get_timestamp()
  print 'Charging the battery(s)...[' + ts + ']'
  
  if batt_num == '3':
    ps.all_output('on')
    ps1.all_output('on')
  else:
    ps.all_output('on')
  
  sleep(1)
  
  check_batt_charge(target_soc, monitor_freq, batt_num)
  
  ts = get_timestamp()
  soc1 = str(sb1.query('battery0_soc_percent'))
  current_soc1 = soc1.split("'")[3]
  print 'Battery1 is now charged to ' + current_soc1 + '%...[' + ts + ']'
  if batt_num == '2':
    soc2 = str(sb2.query('battery0_soc_percent'))
    current_soc2 = soc2.split("'")[3]
    print 'Battery2 is now charged to ' + current_soc2 + '%...[' + ts + ']'
  elif batt_num == '3':
    soc2 = str(sb2.query('battery0_soc_percent'))
    current_soc2 = soc2.split("'")[3]
    print 'Battery2 is now charged to ' + current_soc2 + '%...[' + ts + ']'
    soc3 = str(sb3.query('battery0_soc_percent'))
    current_soc3 = soc3.split("'")[3]
    print 'Battery3 is now charged to ' + current_soc3 + '%...[' + ts + ']'
  elif batt_num == '4':
    soc2 = str(sb2.query('battery0_soc_percent'))
    current_soc2 = soc2.split("'")[3]
    print 'Battery2 is now charged to ' + current_soc2 + '%...[' + ts + ']'
    soc3 = str(sb3.query('battery0_soc_percent'))
    current_soc3 = soc3.split("'")[3]
    print 'Battery3 is now charged to ' + current_soc3 + '%...[' + ts + ']'
    soc4 = str(sb4.query('battery0_soc_percent'))
    current_soc4 = soc4.split("'")[3]
    print 'Battery4 is now charged to ' + current_soc4 + '%...[' + ts + ']'
  else:
    raise Exception, 'Unknown command.'

def check_batt_charge(target_soc, monitor_freq, batt_num):

  # Get initial SOC percent
  ts = get_timestamp()
  soc1 = str(sb1.query('battery0_soc_percent'))
  current_soc1 = soc1.split("'")[3]
  print 'Battery1 soc_percent is ' + current_soc1 + '%...[' + ts + ']'
  if batt_num == '2':
    soc2 = str(sb2.query('battery0_soc_percent'))
    current_soc2 = soc2.split("'")[3]
    print 'Battery2 soc_percent is ' + current_soc2 + '%...[' + ts + ']'
  elif batt_num == '3':
    soc2 = str(sb2.query('battery0_soc_percent'))
    current_soc2 = soc2.split("'")[3]
    print 'Battery2 soc_percent is ' + current_soc2 + '%...[' + ts + ']'
    soc3 = str(sb3.query('battery0_soc_percent'))
    current_soc3 = soc3.split("'")[3]
    print 'Battery3 soc_percent is ' + current_soc3 + '%...[' + ts + ']'
  elif batt_num == '4':
    soc2 = str(sb2.query('battery0_soc_percent'))
    current_soc2 = soc2.split("'")[3]
    print 'Battery2 soc_percent is ' + current_soc2 + '%...[' + ts + ']'
    soc3 = str(sb3.query('battery0_soc_percent'))
    current_soc3 = soc3.split("'")[3]
    print 'Battery3 soc_percent is ' + current_soc3 + '%...[' + ts + ']'
    soc4 = str(sb4.query('battery0_soc_percent'))
    current_soc4 = soc4.split("'")[3]
    print 'Battery4 soc_percent is ' + current_soc4 + '%...[' + ts + ']'
  else:
    raise Exception, 'Unknown command.'
  
  # Monitor SOC percent
  if batt_num == '2': 
    while float(current_soc2) < float(target_soc):
      sleep(monitor_freq)
      ts = get_timestamp()
      if float(current_soc1) >= float(target_soc):
        ps.set_currentlimit(1, 0)
      else:
        soc1 = str(sb1.query('battery0_soc_percent'))
        current_soc1 = soc1.split("'")[3]
      soc2 = str(sb2.query('battery0_soc_percent'))
      current_soc2 = soc2.split("'")[3]
      print 'Battery1 soc_percent is ' + current_soc1 + '%...[' + ts + ']'
      print 'Battery2 soc_percent is ' + current_soc2 + '%...[' + ts + ']'

    ps.set_currentlimit(2, 0)

    while float(current_soc1) < float(target_soc):
      sleep(monitor_freq)
      ts = get_timestamp()
      soc1 = str(sb1.query('battery0_soc_percent'))
      current_soc1 = soc1.split("'")[3]
      soc2 = str(sb2.query('battery0_soc_percent'))
      current_soc2 = soc2.split("'")[3]
      print 'Battery1 soc_percent is ' + current_soc1 + '%...[' + ts + ']'
      print 'Battery2 soc_percent is ' + current_soc2 + '%...[' + ts + ']'

    ps.set_currentlimit(1, 0)

  else:

    while float(current_soc1) < float(target_soc):
      sleep(monitor_freq)
      ts = get_timestamp()
      soc1 = str(sb1.query('battery0_soc_percent'))
      current_soc1 = soc1.split("'")[3]
      print 'Battery1 soc_percent is ' + current_soc1 + '%...[' + ts + ']'

    ps.set_currentlimit(1, 0)
    ps.set_currentlimit(2, 0)

def get_timestamp():

  dt = datetime.now()
  dt = dt.replace(microsecond=0)
  return str(dt)

# Script starts here: 
# target_soc = args.soc
# monitor_freq = args.freq
target_soc = 90
monitor_freq = 60
batt_charging(target_soc, monitor_freq, batt_num)
