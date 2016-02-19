#!/usr/bin/env python

# Copyright 2015 Google, Inc.
# Routines for the dual battery charging
# Author: TaiWen Ko
# Date: 2015-1-13

import xpf6020
import bk8500
from datetime import datetime
from time import sleep
import tools.utils as tools
from tools import shell
import twk_utils
import sys
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
charge_v = 50.7 # 50.4 + 0.3 diode drop
charge_i = 7#10
ps1 = xpf6020.Xpf6020(ps1_path)
ps1.reset_ps()
ps2 = xpf6020.Xpf6020(ps2_path)
ps2.reset_ps()

ps1.set_voltage(1, charge_v)
ps1.set_currentlimit(1, charge_i)
ps1.set_voltage(2, charge_v)
ps1.set_currentlimit(2, charge_i)
ps2.set_voltage(1, charge_v)
ps2.set_currentlimit(1, charge_i)
ps2.set_voltage(2, charge_v)
ps2.set_currentlimit(2, charge_i)

def batt_charging(target_volt, target_current, max_temp, min_temp, max_diff, min_diff, monitor_freq, batt_num):

  is_it_done_yet = False

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

  while True:

    for i in range(int(batt_num)):

      print i
      if i == 1:
        path = pfc1_path
      elif i == 2:
        path = pfc2_path
      elif i == 3:
        path = pfc3_path
      elif i == 4:
        path = pfc4_path
      else:
        raise Exception, 'Unknown range.'

      tom = shell.Shell(path)
      sb = shell.Scoreboard(tom,'battery')

      state = check_batt_charge(target_volt, target_current, max_temp, min_temp, max_diff, min_diff, monitor_freq, batt_num)

      if i == 1:
        ch1_state = state
      elif i == 2:
        ch2_state = state
      elif i == 3:
        ch3_state = state
      elif i == 4:
        ch4_state = state
      else:
        raise Exception, 'Unknown range.'

      tom.close()

    if batt_num == '1':

      if ch1_state == 1:
        break

    elif batt_num == '2':

      if ch1_state == 1 and ch2_state == 1:
        break

    elif batt_num == '3':

      if ch1_state == 1 and ch2_state == 1 and ch3_state == 1:
        break

    elif batt_num == '4':

      if ch1_state == 1 and ch2_state == 1 and ch3_state == 1 and ch4_state == 1:
        break

    print "Checking measurement again in another %s seconds" % monitor_freq
    sleep(monitor_freq)

def check_batt_temp(max_temp, min_temp, batt_num):

  temp1 = str(sb.query('battery0_temperature0'))
  current_temp1 = temp1.split("'")[3]
  temp2 = str(sb.query('battery0_temperature1'))
  current_temp2 = temp2.split("'")[3]
  temp3 = str(sb.query('battery0_temperature2'))
  current_temp3 = temp3.split("'")[3]
  print 'Temperature0 = %sC' % current_temp1
  print 'Temperature1 = %sC' % current_temp2
  print 'Temperature2 = %sC' % current_temp3
  overheat_check(current_temp1, current_temp2, current_temp3, max_temp, min_temp, batt_num)

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

def check_cell_diff(max_diff, min_diff, batt_num):

    min_cv = str(sb.query('battery0_min_cell_voltage'))
    current_min_cv = min_cv.split("'")[3]
    max_cv = str(sb.query('battery0_max_cell_voltage'))
    current_max_cv = max_cv.split("'")[3]
    print 'Min cell voltage = %s' % current_min_cv
    print 'Max cell voltage = %s' % current_max_cv
    diff_check(max_cv, min_cv, max_diff, min_diff, batt_num)

def print_status_errors():

    sbvolt = str(sb.query('battery0_voltage'))
    current_sbvolt = sbvolt.split("'")[3]
    sbcurr = str(sb1.query('battery0_current'))
    current_sbcurr = sbcurr.split("'")[3]

    sbstatus = str(sb.query('battery0_status'))
    current_sbstatus = sbstatus.split("'")[3]
    sberror = str(sb1.query('battery0_error'))
    current_sberror = sberror.split("'")[3]
    sbalert = str(sb1.query('battery0_safety_alert'))
    current_sbalert = sbalert.split("'")[3]
    sbopstatus = str(sb.query('battery0_operation_status'))
    current_sbopstatus = sbopstatus.split("'")[3]
    print 'Battery Voltage = %s' % current_sbvolt
    print 'Battery Current = %s' % curren_sbcurr
    print 'Battery Status = %s' % current_sbstatus
    print 'Error = %s' % current_sberror
    print 'Safety Alert = %s' % current_sbalert
    print 'Op Status = %s' % current_sbopstatus

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

def cleanup():

  ps1.all_output('off')
  ps2.all_output('off')
  sys.exit()

def check_batt_charge(target_volt, target_current, max_temp, min_temp, max_diff, min_diff, channel):

  state = 0
  result = t.bold_red('Charging')

  if channel == 1:
    [volt, curr] = ps1.measure('1')
  elif channel == 2:
    [volt, curr] = ps1.measure('2')
  elif channel == 3:
    [volt, curr] = ps2.measure('1')
  elif channel == 4:
    [volt, curr] = ps2.measure('2')

  volt = volt.split("V")[0]
  curr = curr.split("A")[0]

  if float(volt) >= float(target_volt):
    if float(curr) <= float(target_current):
      state = 1
      result = t.bold_green('Charged')
      if channel == 1:
        ps1.set_currentlimit(1, 0)
      elif channel == 2:
        ps1.set_currentlimit(2, 0)
      elif channel == 3:
        ps2.set_currentlimit(1, 0)
      elif channel == 4:
        ps2.set_currentlimit(2, 0)

  print 'Battery state is %s ' % ch1_result
  print 'PS_Reading: Voltage = %sV, Current = %sA' % (volt, curr)
  soc = str(sb.query('battery0_soc_percent'))
  current_soc = soc.split("'")[3]
  print 'BatterySOC is %s %' % current_soc
  check_batt_temp(max_temp, min_temp)
  check_cell_diff(max_diff, min_diff)
  print_status_errors()

target_volt = 50.4
target_current = 0.2
monitor_freq = 60
max_temp = 323
min_temp = 283
max_diff = 4.25
min_diff = 2.5

ts = utils.get_timestamp()
message = '***Battery Charging Started @ %s***' % ts
print message
utils.send_email('Battery Charging', message)

batt_charging(target_volt, target_current, max_temp, min_temp, max_diff, min_diff, monitor_freq, batt_num)

ts = utils.get_timestamp()
message = '***Battery Charging Completed @ %s***' % ts
print message
utils.send_email('Battery Charging', message)
