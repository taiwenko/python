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

from blessings import Terminal

t = Terminal()

parser = argparse.ArgumentParser(description='MBPower Test Script')
parser.add_argument('logfile',
        help='CSV file to append new measurements')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()


# Initialize test equipments
print "Accessing the XPF6020 Power Supply"

ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A702WVKF-if00-port0'

batt_vin = 40
batt_iin = 0.30
solar_vin = 40
solar_iin = 0.30

ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1,batt_vin)
ps.set_currentlimit(1,batt_iin)
#ps.set_voltage(2,solar_vin)
#ps.set_currentlimit(2,solar_iin)

#print "Accessing the BK8500 Electronic Load"

#mbp_v = 41
#mbp_v_max = 43

#bkload = bk8500.Bk8500()
#bkload.remote_switch('on')
#bkload.config_cv_mode(mbp_v, mbp_v_max)

print "Accessing the Agilent34972A DAQ"

agilent_path = '192.168.1.3'
daq = agilent34972A.Agilent34972A(agilent_path)
daq.factory_reset()

def charging_measure_check(channel,current,voltage,tolerance):

  ts = datetime.now()
  ts = ts.replace(microsecond=0)

  [r_load_v, r_load_i] = bkload.read()

  current_max = current * (1 + tolerance)
  current_min = current * (1 - tolerance)
  voltage_max = voltage * (1 + tolerance)
  voltage_min = voltage * (1 - tolerance)

  if float(r_load_i) > float(current_max):
    result = t.bold_red('FAILED')
  elif float(r_load_i) < float(current_min):
    result = t.bold_red('FAILED')
  elif float(r_load_v) > float(voltage_max):
    result = t.bold_red('FAILED')
  elif float(r_load_v) < float(voltage_min):
    result = t.bold_red('FAILED')
  else:
    result = t.bold_green('PASSED')

 
  print ('Batt CH %s Charging %s @ %sV, %sA' %(channel,result,r_load_v,r_load_i))

  # Log data to file
  logfile.write('%s,' % ts)
  logfile.write('%s,' % channel)
  logfile.write('Charging,')
  logfile.write('%s,' % r_load_i)
  logfile.write('%s,' % r_load_v)
  logfile.write('%s\n' % result)

def discharging_measure_check(channel,current,voltage,tolerance):

  daq.switch(str(100+channel),'close')
  sleep(5)

  ts = datetime.now()
  ts = ts.replace(microsecond=0)

  [r_mbp_v, r_mbp_i] = ps.measure('1')

  current_max = current * (1 + tolerance)
  current_min = current * (1 - tolerance)
  voltage_max = voltage * (1 + tolerance)
  voltage_min = voltage * (1 - tolerance)

  r_mbp_v = r_mbp_v.split("V")[0]
  r_mbp_i = r_mbp_i.split("A")[0]

  if float(r_mbp_i) > float(current_max):
    result = t.bold_red('FAILED')
  elif float(r_mbp_i) < float(current_min):
    result = t.bold_red('FAILED')
  elif float(r_mbp_v) > float(voltage_max):
    result = t.bold_red('FAILED')
  elif float(r_mbp_v) < float(voltage_min):
    result = t.bold_red('FAILED')
  else:
    result = t.bold_green('PASSED')

  print ('Batt CH %s Discharging %s @ %sV, %sA' %(str(channel-2),result,r_mbp_v, r_mbp_i))

  # Log data to file
  logfile.write('%s,' % ts)
  logfile.write('%s,' % str(channel))
  logfile.write('Discharging,')
  logfile.write('%s,' % r_mbp_i)
  logfile.write('%s,' % r_mbp_v)
  logfile.write('%s\n' % result)

  # Open switch
  daq.switch(str(100+channel),'open')
  sleep(3)

  if result == t.bold_green('PASSED'):

      [r_mbp_v, r_mbp_i] = ps.measure('1')

      current_min = 0.01 

      r_mbp_v = r_mbp_v.split("V")[0]
      r_mbp_i = r_mbp_i.split("A")[0]

      if abs(float(r_mbp_i)) > float(current_min):
        result = t.bold_red('FAILED')
      else:
        result = t.bold_green('PASSED')
      print ('Batt CH %s Opening %s @ %sV, %sA' %(str(channel-2),result,r_mbp_v, r_mbp_i))

  return result

# Parameters
batt_ch = 4
solar_ch = 4

# Limits
charge_current_limit = 0.16
charge_voltage_limit = 40

discharge_current_limit = 0.16
discharge_voltage_limit = 40
tolerance = 0.5

# Write headers
dt = datetime.now()
dt = dt.replace(microsecond=0)
logdir = '%smbp_charge_discharge_test-%s.csv' % (args.logfile, dt)
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP,')
    logfile.write('CHANNEL,')
    logfile.write('DIRECTION,')
    logfile.write('CURRENT(A),')
    logfile.write('VOLTAGE(V),')
    logfile.write('RESULT\n')
    logfile.flush()

dt = datetime.now()
dt = dt.replace(microsecond=0)
print 'MBP test started @ %s' % dt

############
# --Charging
# for ch in range(1, batt_ch+1):

#   print '====== Battery Channel %s Charging Test =====' %ch
#   # Turn on load
#   bkload.load_switch('on')
#   sleep(1)

#   # Turn on ps ch for battery
#   ps.ind_output('1','on')
#   sleep(2)
#   daq.switch(str(100+ch),'close')
#   sleep(1)

#   # Turn on ps ch for solar
#   ps.ind_output('2','on')
#   sleep(2)
#   if (ch < 5):
#     daq.switch(str(112+ch),'close')
#   elif (4 < ch < 9):
#     daq.switch(str(112+ch-4),'close')
#   else:
#     daq.switch(str(112+ch-8),'close')
#   sleep(1)

#   # Check load current
#   charging_measure_check(str(ch), charge_current_limit, charge_voltage_limit, tolerance)

#   # Turn off solar
#   ps.ind_output('2','off')
#   sleep(2)
#   if (ch < 5):
#     daq.switch(str(112+ch),'open')
#   elif (4 < ch < 9):
#     daq.switch(str(112+ch-4),'open')
#   else:
#     daq.switch(str(112+ch-8),'open')
#   sleep(1)

#   # Turn off ps ch for battery
#   ps.ind_output('1','off')
#   sleep(1)
#   daq.switch(str(100+ch),'open')
#   sleep(1)
#   print ""

# # Turn off load
# bkload.load_switch('off')
# sleep(1)

#############
# Disharging

result = 'PASSED'
ch_cnt = 0 
for ch in range(2, batt_ch+1):
  
  print ''
  print '====== Battery Channel %s Discharging Test =====' %ch_cnt
  # Turn on ps ch for battery
  ps.ind_output('1','on')
  sleep(2)

  # Check closed ps current
  result = discharging_measure_check(ch, discharge_current_limit, discharge_voltage_limit, tolerance)

  # Turn off ps ch for battery
  ps.ind_output('1','off')
  sleep(2)
 
  ch_cnt = ch_cnt+1

#############
# Clean up

ps.all_output('off')
#bkload.load_switch('off')
dt = datetime.now()
dt = dt.replace(microsecond=0)
print 'MBP test completed @ %s' % dt

