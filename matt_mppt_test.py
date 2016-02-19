#!/usr/bin/env python

# Author: TaiWen Ko

import xpf6020
import bk8500
import agilent34972A
import argparse
import math
import os

from datetime import datetime
from time import sleep

parser = argparse.ArgumentParser(description='Matt MPPT Temperature Test Script')
parser.add_argument('cycle',
        help='Number of temperature cycle')
parser.add_argument('logfile',
        help='CSV file to append new measurements')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

print "Accessing the XPF6020 Power Supply"

# Battery PS
ps1_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'

batt_vin = 43
batt_iin = 1.5

ps1 = xpf6020.Xpf6020(ps1_path)
ps1.reset_ps()
ps1.set_voltage(1,batt_vin)
ps1.set_currentlimit(1,batt_iin)

# Solar PS 
ps2_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5029ID1-if00-port0'

# Need to burn 15W on each MPPT channel
ps2 = xpf6020.Xpf6020(ps2_path)
ps2.reset_ps()

print "Accessing the BK8500 Electronic Load"

mppt_v = 46
mppt_v_max = 50

bkload = bk8500.Bk8500()
bkload.remote_switch('on')
bkload.config_cv_mode(mppt_v, mppt_v_max)

print "Accessing the Agilent34972A DAQ"

agilent_path = '192.168.1.3'
daq = agilent34972A.Agilent34972A(agilent_path)
daq.factory_reset()

def bkload_measure_check(cycle,current,voltage,tolerance):

  ts = datetime.now()
  ts = ts.replace(microsecond=0)

  [r_load_v, r_load_i] = bkload.read()

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
  print ('MPPT Output %s @ %sV, %sA @ %s' %(result,r_load_v,r_load_i,ts))
  #print ('MPPT Output ' + result + ' @ ' + str(r_load_v) + 'V, ' + str(r_load_i) + 'A @ ' + str(ts))
  logfile.write('%s,' % ts)
  logfile.write('Out,')
  logfile.write('%s,' % cycle)
  logfile.write('%s,' % r_load_i)
  logfile.write('%s,' % r_load_v)
  logfile.write('NONE,')
  logfile.write('NONE,')
  logfile.write('%s\n' % result)

def ps_measure_check(ch,cycle,current,voltage,tolerance):

  ts = datetime.now()
  ts = ts.replace(microsecond=0)
  
  if ch == '1':
    [r_mppt_v, r_mppt_i] = ps2.measure('1',)
  elif ch == '2':
    [r_mppt_v, r_mppt_i] = ps2.measure('2',)
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
  print ('MPPT Input %s %s @ %sV, %sA @ %s' %(ch, result, r_mppt_v, r_mppt_i, ts))
  #print ('MPPT Input ' + ch + ' ' + result + ' @ ' + str(r_mppt_v) + 'V, ' + str(r_mppt_i) + 'A @ ' + str(ts))
  
  if ch == '1':
    temp_q = daq_measure('101','TC','T','C')
    temp_u = daq_measure('102','TC','T','C')
  elif ch == '2':
    temp_q = daq_measure('103','TC','T','C')
    temp_u = daq_measure('104','TC','T','C')
  else:
    print 'Unknown command.'

  logfile.write('%s,' % ts)
  logfile.write('%s,' % ch)
  logfile.write('%s,' % cycle)
  logfile.write('%s,' % r_mppt_i)
  logfile.write('%s,' % r_mppt_v)
  logfile.write('%s,' % temp_q)
  logfile.write('%s,' % temp_u)
  logfile.write('%s\n' % result)

def daq_measure(ch,probe,ptype,unit):
  daq.switch(ch,'close')
  daq.config(ch,probe,ptype,unit)
  print str(daq.measure(ch)) + daq.get_unit(ch)
  return daq.measure(ch)

# Parameters
current_cycle = 1
target_cycle = args.cycle
current_time = 0
target_time = 20 #1800
monitor_freq = 10 #60
input_current_limit = 5
input_voltage_limit = 16
output_current_limit = 2.34
output_voltage_limit = 46
tolerance = 0.05
dutycycle = 5 #1800
target_max_temp = 24#60 #C
target_min_temp = 29#-70 #C

# Write headers
dt = datetime.now()
dt = dt.replace(microsecond=0)
logdir = '%smppt_temp_test-%s.csv' % (args.logfile, dt)
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
    logfile.write('Q_TEMPERATURE(C),')
    logfile.write('U_TEMPERATURE(C),')
    logfile.write('RESULT\n')
    logfile.flush()

dt = datetime.now()
dt = dt.replace(microsecond=0)
print 'MPPT test started @ %s' % dt

while float(current_cycle) != (float(target_cycle) + 1):
  
  dt = datetime.now()
  dt = dt.replace(microsecond=0)
  print 'MPPT test cycle %s of %s started @ %s' % (current_cycle, target_cycle, dt)
  
  # PTCE Step 2 - wait til internal temp is great than target max temp 
  current_temp1 = daq_measure('101','TC','T','C')
  current_temp2 = daq_measure('102','TC','T','C')
  current_temp3 = daq_measure('103','TC','T','C')
  current_temp4 = daq_measure('104','TC','T','C')

  while (current_temp1 < target_max_temp) or (current_temp2 < target_max_temp) or (current_temp3 < target_max_temp) or (current_temp4 < target_max_temp):
    current_temp1 = daq_measure('101','TC','T','C')
    current_temp2 = daq_measure('102','TC','T','C')
    current_temp3 = daq_measure('103','TC','T','C')
    current_temp4 = daq_measure('104','TC','T','C')

  # PTCE Step 3 - Operate the UUT @ peak power condition

  solar_vin = 16
  solar_iin = 5
  ps2.set_voltage(1,solar_vin)
  ps2.set_currentlimit(1,solar_iin)
  ps2.set_voltage(2,solar_vin)
  ps2.set_currentlimit(2,solar_iin)

  bkload.load_switch('on')
  sleep(1)
  ps1.all_output('on')
  sleep(3)
  ps2.all_output('on')
  sleep(10)

  while current_time <= target_time:
    ps_measure_check('1', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    ps_measure_check('2', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    bkload_measure_check(current_cycle, output_current_limit, output_voltage_limit, tolerance)
    sleep(monitor_freq)
    current_time = current_time + monitor_freq
  
  # PTCE Step 4 - Turn off the UUT

  ps2.all_output('off')
  current_time = 0

  # PTCE Step 5 - wait til internal temp is less than target min temp 

  current_temp1 = daq_measure('101','TC','T','C')
  current_temp2 = daq_measure('102','TC','T','C')
  current_temp3 = daq_measure('103','TC','T','C')
  current_temp4 = daq_measure('104','TC','T','C')

  while (current_temp1 > target_min_temp) or (current_temp2 > target_min_temp) or (current_temp3 > target_min_temp) or (current_temp4 > target_min_temp):
    current_temp1 = daq_measure('101','TC','T','C')
    current_temp2 = daq_measure('102','TC','T','C')
    current_temp3 = daq_measure('103','TC','T','C')
    current_temp4 = daq_measure('104','TC','T','C')
  
  # PTCE Step 6 - Run the UUT at min power to check for functionality.
  # 7W per mppt ch 
  solar_vin = 12
  solar_iin = 5
  ps2.set_voltage(1,solar_vin)
  ps2.set_currentlimit(1,solar_iin)
  ps2.set_voltage(2,solar_vin)
  ps2.set_currentlimit(2,solar_iin)

  bkload.load_switch('on')
  sleep(1)
  ps1.all_output('on')
  sleep(3)
  ps2.all_output('on')
  sleep(10)

  while current_time <= target_time:
    ps_measure_check('1', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    ps_measure_check('2', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    bkload_measure_check(current_cycle, output_current_limit, output_voltage_limit, tolerance)
    sleep(monitor_freq)
    current_time = current_time + monitor_freq

  # PTCE Step 7 - Operate the UUT @ peak power condition
  # 15W per mppt ch 
  solar_vin = 16
  solar_iin = 5
  ps2.set_voltage(1,solar_vin)
  ps2.set_currentlimit(1,solar_iin)
  ps2.set_voltage(2,solar_vin)
  ps2.set_currentlimit(2,solar_iin)

  while current_time <= target_time:
    ps_measure_check('1', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    ps_measure_check('2', current_cycle, input_current_limit, input_voltage_limit, tolerance)
    bkload_measure_check(current_cycle, output_current_limit, output_voltage_limit, tolerance)
    sleep(monitor_freq)
    current_time = current_time + monitor_freq
  
  # PTCE Step 8 - Turn off the UUT 

  ps2.all_output('off')
  current_time = 0

  # PTCE Step 9 - Repeat step 2-8
  dt = datetime.now()
  dt = dt.replace(microsecond=0)
  print 'MPPT test cycle %s of %s completed @ %s' % (current_cycle, target_cycle, dt)
  current_cycle = current_cycle + 1

# Clean up
ps1.all_output('off')
ps2.all_output('off')
bkload.load_switch('off')
dt = datetime.now()
dt = dt.replace(microsecond=0)
print 'MPPT test completed @ %s' % dt

