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
import sys
import twk_utils
utils = twk_utils.Twk_utils()
from blessings import Terminal
t = Terminal()

batt_num = None

while True:
    batt_num = raw_input('How many batteries would you like to charge? [ 1, 2, 3, or 4 ]: ')
    message = raw_input('Charging %s battery(s). Is this correct? [y/N]' % batt_num )
    if message == 'y' and (batt_num == '1' or batt_num == '2' or batt_num == '3' or batt_num == '4'):
      break;

# Make sure to use the correct cables
ps1_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AH028NK1-if00-port0'
ps2_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A703U4HD-if00-port0'

pfc1_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1-if01-port0'
pfc2_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_2-if01-port0'
pfc3_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_3-if01-port0'
pfc4_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_4-if01-port0'

print "Accessing the XPF6020 Power Supply"
charge_v = 50
charge_i = 7#10
ps1 = xpf6020.Xpf6020(ps1_path)
ps1.reset_ps()
ps2 = xpf6020.Xpf6020(ps2_path)
ps2.reset_ps()

ps1.set_voltage(1, charge_v)
ps1.set_currentlimit(1, charge_i)

if batt_num == '2':
  ps1.set_voltage(2, charge_v)
  ps1.set_currentlimit(2, charge_i)
elif batt_num == '3':
  ps1.set_voltage(2, charge_v)
  ps1.set_currentlimit(2, charge_i)
  ps2.set_voltage(1, charge_v)
  ps2.set_currentlimit(1, charge_i)
elif batt_num == '4':
  ps1.set_voltage(2, charge_v)
  ps1.set_currentlimit(2, charge_i)
  ps2.set_voltage(1, charge_v)
  ps2.set_currentlimit(1, charge_i)
  ps2.set_voltage(2, charge_v)
  ps2.set_currentlimit(2, charge_i)
else:
  if batt_num != '1':
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
  if batt_num != '1':
    raise Exception, 'Unknown command.'

def batt_charging(target_volt, target_current, max_temp, min_temp, max_diff, min_diff, monitor_freq, batt_num):

  ts = utils.get_timestamp()
  print 'Charging the battery(s)...[%s]' % ts

  ps1.ind_output('1','on')
  sleep(1)

  if batt_num == '2':
    ps1.ind_output('2','on')
    sleep(1)
  elif batt_num == '3':
    ps1.ind_output('2','on')
    sleep(1)
    ps2.ind_output('1','on')
    sleep(1)
  elif batt_num == '4':
    ps1.ind_output('2','on')
    sleep(1)
    ps2.ind_output('1','on')
    sleep(1)
    ps2.ind_output('2','on')
    sleep(1)
  else:
    if batt_num != '1':
      raise Exception, 'Unknown command.'

  check_batt_charge(target_volt, target_current, max_temp, min_temp, max_diff, min_diff, monitor_freq, batt_num)

  check_batt_volt(batt_num)

def check_batt_volt(batt_num):

    # Get initial volt percent
    ts = utils.get_timestamp()
    if batt_num == '1':
      [ch1_volt, ch1_curr] = ps1.measure('1')
      print 'Ch1 battery has %s and is charging with %s @ %s' % (ch1_volt, ch1_curr, ts)
    elif batt_num == '2':
      [ch1_volt, ch1_curr] = ps1.measure('1')
      print 'Ch1 battery has %s and is charging with %s @ %s' % (ch1_volt, ch1_curr, ts)
      [ch2_volt, ch2_curr] = ps1.measure('2')
      print 'Ch2 battery has %s and is charging with %s @ %s' % (ch2_volt, ch2_curr, ts)
    elif batt_num == '3':
      [ch1_volt, ch1_curr] = ps1.measure('1')
      print 'Ch1 battery has %s and is charging with %s @ %s' % (ch1_volt, ch1_curr, ts)
      [ch2_volt, ch2_curr] = ps1.measure('2')
      print 'Ch2 battery has %s and is charging with %s @ %s' % (ch2_volt, ch2_curr, ts)
      [ch3_volt, ch3_curr] = ps2.measure('1')
      print 'Ch3 battery has %s and is charging with %s @ %s' % (ch3_volt, ch3_curr, ts)
    elif batt_num == '4':
      [ch1_volt, ch1_curr] = ps1.measure('1')
      print 'Ch1 battery has %s and is charging with %s @ %s' % (ch1_volt, ch1_curr, ts)
      [ch2_volt, ch2_curr] = ps1.measure('2')
      print 'Ch2 battery has %s and is charging with %s @ %s' % (ch2_volt, ch2_curr, ts)
      [ch3_volt, ch3_curr] = ps2.measure('1')
      print 'Ch3 battery has %s and is charging with %s @ %s' % (ch3_volt, ch3_curr, ts)
      [ch4_volt, ch4_curr] = ps2.measure('2')
      print 'Ch4 battery has %s and is charging with %s @ %s' % (ch4_volt, ch4_curr, ts)
    else:
      raise Exception, 'Unknown command.'

def check_batt_soc(batt_num):

    # Get volt percent
    ts = utils.get_timestamp()
    if batt_num == '1':
      soc1 = str(sb1.query('battery0_soc_percent'))
      current_soc1 = soc1.split("'")[3]
      print 'Battery1 is now charged to %s percent @ %s' % (current_soc1, ts)
    elif batt_num == '2':
      soc1 = str(sb1.query('battery0_soc_percent'))
      current_soc1 = soc1.split("'")[3]
      print 'Battery1 is now charged to %s percent @ %s' % (current_soc1, ts)
      soc2 = str(sb2.query('battery0_soc_percent'))
      current_soc2 = soc2.split("'")[3]
      print 'Battery2 is now charged to %s percent @ %s' % (current_soc2, ts)
    elif batt_num == '3':
      soc1 = str(sb1.query('battery0_soc_percent'))
      current_soc1 = soc1.split("'")[3]
      print 'Battery1 is now charged to %s percent @ %s' % (current_soc1, ts)
      soc2 = str(sb2.query('battery0_soc_percent'))
      current_soc2 = soc2.split("'")[3]
      print 'Battery2 is now charged to %s percent @ %s' % (current_soc2, ts)
      soc3 = str(sb3.query('battery0_soc_percent'))
      current_soc3 = soc3.split("'")[3]
      print 'Battery3 is now charged to %s percent @ %s' % (current_soc3, ts)
    elif batt_num == '4':
      soc1 = str(sb1.query('battery0_soc_percent'))
      current_soc1 = soc1.split("'")[3]
      print 'Battery1 is now charged to %s percent @ %s' % (current_soc1, ts)
      soc2 = str(sb2.query('battery0_soc_percent'))
      current_soc2 = soc2.split("'")[3]
      print 'Battery2 is now charged to %s percent @ %s' % (current_soc2, ts)
      soc3 = str(sb3.query('battery0_soc_percent'))
      current_soc3 = soc3.split("'")[3]
      print 'Battery3 is now charged to %s percent @ %s' % (current_soc3, ts)
      soc4 = str(sb4.query('battery0_soc_percent'))
      current_soc4 = soc4.split("'")[3]
      print 'Battery4 is now charged to %s percent @ %s' % (current_soc4, ts)
    else:
      raise Exception, 'Unknown command.'

def overheat_check(t1, t2, t3, max_temp, min_temp, batt_num):

    if (float(t1) > float(max_temp)) or (float(t2) > float(max_temp)) or (float(t3) > float(max_temp)):
      print ''
      print 'ERROR: Battery%s temperature is over the max limit of %sC!!' % (batt_num, max_temp)
      print ''
      print '***Please let the batteries cool off before restarting the test.***'
      print ''
      cleanup()

    if (float(t1) < float(min_temp)) or (float(t2) < float(min_temp)) or (float(t3) < float(min_temp)):
      print ''
      print 'ERROR: Battery%s temperature is under the min limit of %sC!!' % (batt_num, min_temp)
      print ''
      print '***Please let the batteries warm up before restarting the test.***'
      print ''
      cleanup()

def check_batt_temp(max_temp, min_temp, batt_num):

    # Get volt percent
    ts = utils.get_timestamp()
    if batt_num == '1':

      sb1temp1 = str(sb1.query('battery0_temperature0'))
      current_sb1temp1 = sb1temp1.split("'")[3]
      sb1temp2 = str(sb1.query('battery0_temperature1'))
      current_sb1temp2 = sb1temp2.split("'")[3]
      sb1temp3 = str(sb1.query('battery0_temperature2'))
      current_sb1temp3 = sb1temp3.split("'")[3]
      print 'Battery1 temperature: %sC, %sC, %sC @ %s' % (current_sb1temp1, current_sb1temp2, current_sb1temp3, ts)
      overheat_check(current_sb1temp1, current_sb1temp2, current_sb1temp3, max_temp, min_temp, '1')

    elif batt_num == '2':

      sb1temp1 = str(sb1.query('battery0_temperature0'))
      current_sb1temp1 = sb1temp1.split("'")[3]
      sb1temp2 = str(sb1.query('battery0_temperature1'))
      current_sb1temp2 = sb1temp2.split("'")[3]
      sb1temp3 = str(sb1.query('battery0_temperature2'))
      current_sb1temp3 = sb1temp3.split("'")[3]
      print 'Battery1 temperature: %sC, %sC, %sC @ %s' % (current_sb1temp1, current_sb1temp2, current_sb1temp3, ts)
      overheat_check(current_sb1temp1, current_sb1temp2, current_sb1temp3, max_temp, min_temp, '1')

      sb2temp1 = str(sb2.query('battery0_temperature0'))
      current_sb2temp1 = sb2temp1.split("'")[3]
      sb2temp2 = str(sb2.query('battery0_temperature1'))
      current_sb2temp2 = sb2temp2.split("'")[3]
      sb2temp3 = str(sb2.query('battery0_temperature2'))
      current_sb2temp3 = sb2temp3.split("'")[3]
      print 'Battery2 Temperatures are %sC, %sC, %sC @ %s' % (current_sb2temp1, current_sb2temp2, current_sb2temp3, ts)
      overheat_check(current_sb2temp1, current_sb2temp2, current_sb2temp3, max_temp, min_temp, '2')

    elif batt_num == '3':

      sb1temp1 = str(sb1.query('battery0_temperature0'))
      current_sb1temp1 = sb1temp1.split("'")[3]
      sb1temp2 = str(sb1.query('battery0_temperature1'))
      current_sb1temp2 = sb1temp2.split("'")[3]
      sb1temp3 = str(sb1.query('battery0_temperature2'))
      current_sb1temp3 = sb1temp3.split("'")[3]
      print 'Battery1 temperature: %sC, %sC, %sC @ %s' % (current_sb1temp1, current_sb1temp2, current_sb1temp3, ts)
      overheat_check(current_sb1temp1, current_sb1temp2, current_sb1temp3, max_temp, min_temp, '1')

      sb2temp1 = str(sb2.query('battery0_temperature0'))
      current_sb2temp1 = sb2temp1.split("'")[3]
      sb2temp2 = str(sb2.query('battery0_temperature1'))
      current_sb2temp2 = sb2temp2.split("'")[3]
      sb2temp3 = str(sb2.query('battery0_temperature2'))
      current_sb2temp3 = sb2temp3.split("'")[3]
      print 'Battery2 Temperatures are %sC, %sC, %sC @ %s' % (current_sb2temp1, current_sb2temp2, current_sb2temp3, ts)
      overheat_check(current_sb2temp1, current_sb2temp2, current_sb2temp3, max_temp, min_temp, '2')

      sb3temp1 = str(sb3.query('battery0_temperature0'))
      current_sb3temp1 = sb3temp1.split("'")[3]
      sb3temp2 = str(sb3.query('battery0_temperature1'))
      current_sb3temp2 = sb3temp2.split("'")[3]
      sb3temp3 = str(sb3.query('battery0_temperature2'))
      current_sb3temp3 = sb3temp3.split("'")[3]
      print 'Battery3 Temperatures are %sC, %sC, %sC @ %s' % (current_sb3temp1, current_sb3temp2, current_sb3temp3, ts)
      overheat_check(current_sb3temp1, current_sb3temp2, current_sb3temp3, max_temp, min_temp, '3')

    elif batt_num == '4':

      sb1temp1 = str(sb1.query('battery0_temperature0'))
      current_sb1temp1 = sb1temp1.split("'")[3]
      sb1temp2 = str(sb1.query('battery0_temperature1'))
      current_sb1temp2 = sb1temp2.split("'")[3]
      sb1temp3 = str(sb1.query('battery0_temperature2'))
      current_sb1temp3 = sb1temp3.split("'")[3]
      print 'Battery1 temperature: %sC, %sC, %sC @ %s' % (current_sb1temp1, current_sb1temp2, current_sb1temp3, ts)
      overheat_check(current_sb1temp1, current_sb1temp2, current_sb1temp3, max_temp, min_temp, '1')

      sb2temp1 = str(sb2.query('battery0_temperature0'))
      current_sb2temp1 = sb2temp1.split("'")[3]
      sb2temp2 = str(sb2.query('battery0_temperature1'))
      current_sb2temp2 = sb2temp2.split("'")[3]
      sb2temp3 = str(sb2.query('battery0_temperature2'))
      current_sb2temp3 = sb2temp3.split("'")[3]
      print 'Battery2 Temperatures are %sC, %sC, %sC @ %s' % (current_sb2temp1, current_sb2temp2, current_sb2temp3, ts)
      overheat_check(current_sb2temp1, current_sb2temp2, current_sb2temp3, max_temp, min_temp, '2')

      sb3temp1 = str(sb3.query('battery0_temperature0'))
      current_sb3temp1 = sb3temp1.split("'")[3]
      sb3temp2 = str(sb3.query('battery0_temperature1'))
      current_sb3temp2 = sb3temp2.split("'")[3]
      sb3temp3 = str(sb3.query('battery0_temperature2'))
      current_sb3temp3 = sb3temp3.split("'")[3]
      print 'Battery3 Temperatures are %sC, %sC, %sC @ %s' % (current_sb3temp1, current_sb3temp2, current_sb3temp3, ts)
      overheat_check(current_sb3temp1, current_sb3temp2, current_sb3temp3, max_temp, min_temp, '3')

      sb4temp1 = str(sb4.query('battery0_temperature0'))
      current_sb4temp1 = sb4temp1.split("'")[3]
      sb4temp2 = str(sb4.query('battery0_temperature1'))
      current_sb4temp2 = sb4temp2.split("'")[3]
      sb4temp3 = str(sb4.query('battery0_temperature2'))
      current_sb4temp3 = sb4temp3.split("'")[3]
      print 'Battery4 Temperatures are %sC, %sC, %sC @ %s' % (current_sb4temp1, current_sb4temp2, current_sb4temp3, ts)
      overheat_check(current_sb4temp1, current_sb4temp2, current_sb4temp3, max_temp, min_temp, '4')

    else:
      raise Exception, 'Unknown command.'

def diff_check(max_reading, min_reading, max_limit, min_limit, batt_num):

    if (float(max_reading) > float(max_limit)):
      print ''
      print 'ERROR: Battery%s cell voltage is over the max limit of %sV!!' % (batt_num, max_limit)
      print ''
      print '***Enter solution here.***'
      print ''
      cleanup()

    if (float(min_reading) < float(min_limit)):
      print ''
      print 'ERROR: Battery%s cell voltage is under the min limit of %sV!!' % (batt_num, min_limit)
      print ''
      print '***Enter solution here.***'
      print ''
      cleanup()


def check_cell_diff(max_diff, min_diff, batt_num):

    # Get volt percent
    ts = utils.get_timestamp()
    if batt_num == '1':
      temp1_1 = str(sb1.query('battery0_min_cell_voltage'))
      current_soc1 = soc1.split("'")[3]
      temp1_1 = str(sb1.query('battery0_max_cell_voltage'))
      current_soc1 = soc1.split("'")[3]
      temp1_1 = str(sb1.query('battery0_temperature2'))
      current_soc1 = soc1.split("'")[3]

      print 'Battery1 is now charged to %s percent @ %s' % (current_soc1, ts)
    elif batt_num == '2':
      soc1 = str(sb1.query('battery0_soc_percent'))
      current_soc1 = soc1.split("'")[3]
      print 'Battery1 is now charged to %s percent @ %s' % (current_soc1, ts)
      soc2 = str(sb2.query('battery0_soc_percent'))
      current_soc2 = soc2.split("'")[3]
      print 'Battery2 is now charged to %s percent @ %s' % (current_soc2, ts)
    elif batt_num == '3':
      soc1 = str(sb1.query('battery0_soc_percent'))
      current_soc1 = soc1.split("'")[3]
      print 'Battery1 is now charged to %s percent @ %s' % (current_soc1, ts)
      soc2 = str(sb2.query('battery0_soc_percent'))
      current_soc2 = soc2.split("'")[3]
      print 'Battery2 is now charged to %s percent @ %s' % (current_soc2, ts)
      soc3 = str(sb3.query('battery0_soc_percent'))
      current_soc3 = soc3.split("'")[3]
      print 'Battery3 is now charged to %s percent @ %s' % (current_soc3, ts)
    elif batt_num == '4':

      sb1min = str(sb1.query('battery0_min_cell_voltage'))
      current_sb1min = sb1min.split("'")[3]
      sb1max = str(sb1.query('battery0_max_cell_voltage'))
      current_sb1max = sb1max.split("'")[3]
      print 'Battery1 Cell Voltage: Min = %sV, Max = %sV, @ %s' % (current_sb1min, current_sb1max, ts)
      diff_check(current_sb1max, current_sb1min, max_diff, min_diff, '1')

      sb2min = str(sb2.query('battery0_min_cell_voltage'))
      current_sb2min = sb2min.split("'")[3]
      sb2max = str(sb2.query('battery0_max_cell_voltage'))
      current_sb2max = sb2max.split("'")[3]
      print 'Battery2 Cell Voltage: Min = %sV, Max = %sV, @ %s' % (current_sb2min, current_sb2max, ts)
      diff_check(current_sb2max, current_sb2min, max_diff, min_diff, '2')

      sb3min = str(sb3.query('battery0_min_cell_voltage'))
      current_sb3min = sb3min.split("'")[3]
      sb3max = str(sb3.query('battery0_max_cell_voltage'))
      current_sb3max = sb3max.split("'")[3]
      print 'Battery3 Cell Voltage: Min = %sV, Max = %sV, @ %s' % (current_sb3min, current_sb3max, ts)
      diff_check(current_sb3max, current_sb3min, max_diff, min_diff, '3')

      sb4min = str(sb4.query('battery0_min_cell_voltage'))
      current_sb4min = sb4min.split("'")[3]
      sb4max = str(sb4.query('battery0_max_cell_voltage'))
      current_sb4max = sb4max.split("'")[3]
      print 'Battery4 Cell Voltage: Min = %sV, Max = %sV, @ %s' % (current_sb4min, current_sb4max, ts)
      diff_check(current_sb4max, current_sb4min, max_diff, min_diff, '4')

    else:
      raise Exception, 'Unknown command.'

def cleanup():

  ps1.all_output('off')
  ps2.all_output('off')
  sys.exit()

def check_batt_charge(target_volt, target_current, max_temp, min_temp, max_diff, min_diff, monitor_freq, batt_num):

  ch1_state = 0
  ch2_state = 0
  ch3_state = 0
  ch4_state = 0
  ch1_result = t.bold_red('Charging')
  ch2_result = t.bold_red('Charging')
  ch3_result = t.bold_red('Charging')
  ch4_result = t.bold_red('Charging')

  while True:

    # Get initial volt percent
    if batt_num == '1':
      [ch1_volt, ch1_curr] = ps1.measure('1')
      ch1_volt = ch1_volt.split("V")[0]
      print ch1_volt
      ch1_curr = ch1_curr.split("A")[0]
      print ch2_volt
    elif batt_num == '2':
      [ch1_volt, ch1_curr] = ps1.measure('1')
      ch1_volt = ch1_volt.split("V")[0]
      ch1_curr = ch1_curr.split("A")[0]
      [ch2_volt, ch2_curr] = ps1.measure('2')
      ch2_volt = ch2_volt.split("V")[0]
      ch2_curr = ch2_curr.split("A")[0]
    elif batt_num == '3':
      [ch1_volt, ch1_curr] = ps1.measure('1')
      ch1_volt = ch1_volt.split("V")[0]
      ch1_curr = ch1_curr.split("A")[0]
      [ch2_volt, ch2_curr] = ps1.measure('2')
      ch2_volt = ch2_volt.split("V")[0]
      ch2_curr = ch2_curr.split("A")[0]
      [ch3_volt, ch3_curr] = ps2.measure('1')
      ch3_volt = ch3_volt.split("V")[0]
      ch3_curr = ch3_curr.split("A")[0]
    elif batt_num == '4':
      [ch1_volt, ch1_curr] = ps1.measure('1')
      ch1_volt = ch1_volt.split("V")[0]
      ch1_curr = ch1_curr.split("A")[0]
      [ch2_volt, ch2_curr] = ps1.measure('2')
      ch2_volt = ch2_volt.split("V")[0]
      ch2_curr = ch2_curr.split("A")[0]
      [ch3_volt, ch3_curr] = ps2.measure('1')
      ch3_volt = ch3_volt.split("V")[0]
      ch3_curr = ch3_curr.split("A")[0]
      [ch4_volt, ch4_curr] = ps2.measure('2')
      ch4_volt = ch4_volt.split("V")[0]
      ch4_curr = ch4_curr.split("A")[0]
    else:
      raise Exception, 'Unknown command.'

    if batt_num == '1':

      if float(ch1_volt) >= float(target_volt):
        if float(ch1_curr) <= float(target_current):
          ps1.set_currentlimit(1, 0)
          ch1_state = 1

    elif batt_num == '2':

      if float(ch1_volt) >= float(target_volt):
        if float(ch1_curr) <= float(target_current):
          ps1.set_currentlimit(1, 0)
          ch1_state = 1

      if float(ch2_volt) >= float(target_volt):
        if float(ch2_curr) <= float(target_current):
          ps1.set_currentlimit(2, 0)
          ch2_state = 1

    elif batt_num == '3':

      if float(ch1_volt) >= float(target_volt):
        if float(ch1_curr) <= float(target_current):
          ps1.set_currentlimit(1, 0)
          ch1_state = 1

      if float(ch2_volt) >= float(target_volt):
        if float(ch2_curr) <= float(target_current):
          ps1.set_currentlimit(2, 0)
          ch2_state = 1

      if float(ch3_volt) >= float(target_volt):
        if float(ch3_curr) <= float(target_current):
          ps2.set_currentlimit(1, 0)
          ch3_state = 1

    elif batt_num == '4':

      if float(ch1_volt) >= float(target_volt):
        if float(ch1_curr) <= float(target_current):
          ps1.set_currentlimit(1, 0)
          ch1_state = 1

      if float(ch2_volt) >= float(target_volt):
        if float(ch2_curr) <= float(target_current):
          ps1.set_currentlimit(2, 0)
          ch2_state = 1

      if float(ch3_volt) >= float(target_volt):
        if float(ch3_curr) <= float(target_current):
          ps2.set_currentlimit(1, 0)
          ch3_state = 1

      if float(ch4_volt) >= float(target_volt):
        if float(ch4_curr) <= float(target_current):
          ps2.set_currentlimit(2, 0)
          ch4_state = 1

    else:
      raise Exception, 'Unknown command.'


    if batt_num == '1':

      if ch1_state == 1:
        break
      else:
        ch1_result = t.bold_red('Charging')

    elif batt_num == '2':

      if ch1_state == 1 and ch2_state == 1:
        break

      if ch1_state == 1:
        ch1_result = t.bold_green('Charged')

      if ch2_state == 1:
        ch2_result = t.bold_green('Charged')

    elif batt_num == '3':

      if ch1_state == 1 and ch2_state == 1 and ch3_state == 1:
        break

      if ch1_state == 1:
        ch1_result = t.bold_green('Charged')

      if ch2_state == 1:
        ch2_result = t.bold_green('Charged')

      if ch3_state == 1:
        ch3_result = t.bold_green('Charged')

    elif batt_num == '4':

      if ch1_state == 1 and ch2_state == 1 and ch3_state == 1 and ch4_state == 1:
        break

      if ch1_state == 1:
        ch1_result = t.bold_green('Charged')

      if ch2_state == 1:
        ch2_result = t.bold_green('Charged')

      if ch3_state == 1:
        ch3_result = t.bold_green('Charged')

      if ch4_state == 1:
        ch4_result = t.bold_green('Charged')

    check_batt_volt(batt_num)
    check_batt_soc(batt_num)
    check_batt_temp(max_temp, min_temp, batt_num)
    check_cell_diff(max_diff, min_diff, batt_num)

    print 'Battery1 state is %s ' % ch1_result
    print 'Battery2 state is %s ' % ch2_result
    print 'Battery3 state is %s ' % ch3_result
    print 'Battery4 state is %s ' % ch4_result
    print "Checking measurement again in another %s seconds" % monitor_freq
    sleep(monitor_freq)

# Script starts here:
target_volt = 50.4
target_current = 0.2
monitor_freq = 60
max_temp = 323
min_temp = 283
max_diff = 4.25
min_diff = 2.5

batt_charging(target_volt, target_current, max_temp, min_temp, max_diff, min_diff, monitor_freq, batt_num)
check_batt_soc(batt_num)

ts = utils.get_timestamp()
message = '***Battery Charging Completed @ %s***' % ts
print message
utils.send_email('Battery Charging', message)

