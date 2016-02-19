#!/usr/bin/env python

# Author: TaiWen Ko

import twk_utils
import xpf6020
import bk8500
import bk8514
import math
import os

from datetime import datetime
from time import sleep

# Accessing emails
utils = twk_utils.Twk_utils()

print "Accessing the XPF6020 Power Supply"

# Battery PS Load
ps1_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5029ID1-if00-port0'

batt_vin = 43
batt_iin = 1.5

ps1 = xpf6020.Xpf6020(ps1_path)
ps1.reset_ps()
ps1.set_voltage(1,batt_vin)
ps1.set_currentlimit(1,batt_iin)
ps1.set_voltage(2,batt_vin)
ps1.set_currentlimit(2,batt_iin)

# Solar PS - Inside MPPT
ps2_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5028CFJ-if00-port0'

# Need to burn 15W on each MPPT channel
solar_vin = 16
solar_iin = 5

ps2 = xpf6020.Xpf6020(ps2_path)
ps2.reset_ps()
ps2.set_voltage(1,solar_vin)
ps2.set_currentlimit(1,solar_iin)
ps2.set_voltage(2,solar_vin)
ps2.set_currentlimit(2,solar_iin)

# Battery PS - Outside MPPT
ps3_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'

ps3 = xpf6020.Xpf6020(ps3_path)
ps3.reset_ps()
ps3.set_voltage(1,solar_vin)
ps3.set_currentlimit(1,solar_iin)
ps3.set_voltage(2,solar_vin)
ps3.set_currentlimit(2,solar_iin)

print "Accessing the BK8500 Electronic Loads"

mppt_v = 46
mppt_v_max = 50

bkload1 = bk8500.Bk8500()
bkload1.remote_switch('on')
bkload1.config_cv_mode(mppt_v, mppt_v_max)

bkload2 = bk8514.Bk8514()
bkload2.remote_switch('on')
bkload2.config_cv_mode(mppt_v, mppt_v_max)

def bkload_measure_check(ch,cycle,current,voltage,tolerance):

  ts = datetime.now()
  ts = ts.replace(microsecond=0)

  if ch == '1':
    [r_load_v, r_load_i] = bkload1.read()
  elif ch == '2':
    [r_load_v, r_load_i] = bkload2.read()
  else:
    print 'Unknown Channel'

  current_max = current * (1 + tolerance)
  current_min = current * (1 - tolerance)
  voltage_max = voltage * (1 + tolerance)
  voltage_min = voltage * (1 - tolerance)

  if float(r_load_i) > float(current_max):
    result = 'FAILED'
  elif float(r_load_i) < float(current_min):
    result = 'FAILED'
  elif float(r_load_v) > float(voltage_max):
    result = 'FAILED'
  elif float(r_load_v) < float(voltage_min):
    result = 'FAILED'
  else:
    result = 'PASSED'

  print ('MPPT Output%s %s @ %sV, %sA...[%s]' %(ch, result,r_load_v,r_load_i,ts))
  
  logfile.write('%s,' % ts)
  logfile.write('Out%s,' % ch)
  logfile.write('%s,' % cycle)
  logfile.write('%s,' % r_load_i)
  logfile.write('%s,' % r_load_v)
  logfile.write('%s\n' % result)

def ps_measure_check(ch,cycle,current,voltage,tolerance):

  ts = datetime.now()
  ts = ts.replace(microsecond=0)
  
  if ch == '1':
    [r_mppt_v, r_mppt_i] = ps2.measure('1')
  elif ch == '2':
    [r_mppt_v, r_mppt_i] = ps2.measure('2')
  elif ch == '3':
    [r_mppt_v, r_mppt_i] = ps3.measure('1')
  elif ch == '4':
    [r_mppt_v, r_mppt_i] = ps3.measure('2')
  else:
    print 'Unknown Channel'

  current_max = current * (1 + tolerance)
  current_min = current * (1 - tolerance)
  voltage_max = voltage * (1 + tolerance)
  voltage_min = voltage * (1 - tolerance)

  r_mppt_v = r_mppt_v.split("V")[0]
  r_mppt_i = r_mppt_i.split("A")[0]

  if float(r_mppt_i) > float(current_max):
    result = 'FAILED'
  elif float(r_mppt_i) < float(current_min):
    result = 'FAILED'
  elif float(r_mppt_v) > float(voltage_max):
    result = 'FAILED'
  elif float(r_mppt_v) < float(voltage_min):
    result = 'FAILED'
  else:
    result = 'PASSED'
  print ('MPPT Input %s %s @ %sV, %sA...[%s]' %(ch, result, r_mppt_v, r_mppt_i, ts))

  logfile.write('%s,' % ts)
  logfile.write('In%s,' % ch)
  logfile.write('%s,' % cycle)
  logfile.write('%s,' % r_mppt_i)
  logfile.write('%s,' % r_mppt_v)
  logfile.write('%s\n' % result)

# Parameters
current_cycle = 1
target_cycle = 12
current_time = 0
target_time = 30#1800
monitor_freq = 10#60 
tolerance = 0.05
offtime = 30#1800

# Burning 15W per channel
input_current_limit = 5
input_voltage_limit = 16
output_current_limit = 2.48
output_voltage_limit = 46

# Write headers
ts = utils.get_timestamp()
filepath = '../Desktop/'
logdir = '%smppt_temp_test-%s.csv' % (filepath, ts)
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP,')
    logfile.write('CHANNEL,')
    logfile.write('CYCLE,')
    logfile.write('CURRENT(A),')
    logfile.write('VOLTAGE(V),')
    logfile.write('RESULT\n')
    logfile.flush()

ts = utils.get_timestamp()
utils.print_line()
message = '*****MPPT test started...[%s]*****' % ts
print message
utils.print_line()
utils.send_email('MPPT Thermo Test Update', message)

# Enable battery
bkload1.load_switch('on')
bkload2.load_switch('on')
sleep(1)
ps1.all_output('on')
sleep(3)

while float(current_cycle) != (float(target_cycle) + 1):
  
  ts = utils.get_timestamp()
  utils.print_line()
  print 'MPPT test cycle %s of %s started @ %s' % (current_cycle, target_cycle, ts)
  utils.print_line()
  
  # Enable Solar Charging
  ps2.all_output('on')
  ps3.all_output('on')
  utils.print_line()
  sleep(10)

  while current_time < target_time:
    # measure inside mppt
    ps_measure_check('1', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    ps_measure_check('2', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    bkload_measure_check('1',current_cycle, output_current_limit, output_voltage_limit, tolerance)
    # measure outside mppt
    ps_measure_check('3', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    ps_measure_check('4', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    bkload_measure_check('2',current_cycle, output_current_limit, output_voltage_limit, tolerance)
    utils.print_line()

    sleep(monitor_freq)
    current_time = current_time + monitor_freq
  
  # Turn off solar charging
  ps2.all_output('off')
  ps3.all_output('off')
  utils.print_line()
  current_time = 0

  # Off for offtime long
  ts = utils.get_timestamp() 
  print 'Turning off the solar inputs for %s seconds...[%s]' % (offtime, ts)
  sleep(offtime)

  ts = utils.get_timestamp()
  message = 'MPPT test cycle %s of %s completed @ %s' % (current_cycle, target_cycle, ts)
  utils.print_line()
  print message
  utils.send_email('MPPT Thermo Test Update', message)

  current_cycle = current_cycle + 1

# after 12 hours, get the same data @ 5min freq for 4 hours.
current_time = 0
target_time = 30#14400 #4*60*60
monitor_freq = 10#300  #5*60

# Enable solar charging
ps2.all_output('on')
ps3.all_output('on')
utils.print_line()
sleep(10)

while current_time < target_time:
  # measure inside mppt 
  ps_measure_check('1', '12+', input_current_limit, input_voltage_limit, tolerance)
  ps_measure_check('2', '12+', input_current_limit, input_voltage_limit, tolerance)
  bkload_measure_check('1', '12+', output_current_limit, output_voltage_limit, tolerance)
  # measure outside mppt
  ps_measure_check('3', '12+', input_current_limit, input_voltage_limit, tolerance)
  ps_measure_check('4', '12+', input_current_limit, input_voltage_limit, tolerance)
  bkload_measure_check('2', '12+', output_current_limit, output_voltage_limit, tolerance)
  utils.print_line()

  sleep(monitor_freq)
  current_time = current_time + monitor_freq

# clean up
ps1.all_output('off')
ps2.all_output('off')
ps3.all_output('off')
bkload1.load_switch('off')
bkload2.load_switch('off')
utils.print_line()
ts = utils.get_timestamp()
message = '*****MPPT test completed @ %s*****' % ts
print message
utils.send_email('MPPT Thermo Test Update', message)
