#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the mppt_power_test
# Author: TaiWen Ko
# Date: 2015-1-7

import xpf6020
import chroma62020H
import bk8500
import agilent34972A
import argparse
import math
import os

from datetime import datetime
from time import sleep

# parser = argparse.ArgumentParser(description='MPPT Power Test Script')
# parser.add_argument('logfile',
#         help='CSV file to append new measurements')
# parser.add_argument('-v', '--verbose',
#         action='store_true',
#         help='Tee serial communications to the console')
# args = parser.parse_args()

# Make sure to use the correct serial-to-usb cable
#ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A602FGGN-if00-port0'
ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5028CFJ-if00-port0'
chroma_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A603QW14-if00-port0'
agilent_path = '192.168.1.2'

# Input
vin = 43
iin = 1.5

# Output (BK8500)
mppt_v = 46 # can't be greater than mppt_v_max
mppt_v_max = 50 

print "Accessing the XPF6020 Power Supply"
ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1,vin)
ps.set_currentlimit(1,iin)

print "Accessing the BK8500 Electronic Load"
bkload = bk8500.Bk8500()
bkload.remote_switch('on')
bkload.config_cv_mode(mppt_v, mppt_v_max)

print "Accessing the Chroma62020H Power Supply"
chroma = chroma62020H.Chroma62020H(chroma_path)
chroma.reset()
chroma.set_mode('SAS')
chroma.set_sas_voc('25.67')
chroma.set_sas_isc('5.629')
chroma.set_sas_vmpp('20.12')
chroma.set_sas_impp('4.971')

print "Accessing the Agilent34972A DAQ"
daq = agilent34972A.Agilent34972A(agilent_path)
daq.factory_reset()

# Write headers
# dt = datetime.now()
# dt = dt.replace(microsecond=0)
# logdir = '%smppt_power_test-%s.csv' % (args.logfile, dt)
# logfile = open(logdir, 'wt')
# try:
#     if logfile.tell() == 0:
#         raise IOError, 'Null Error'
# except IOError:
#     logfile.write('TIMESTAMP,')
#     logfile.write('CURRENT(A),')
#     logfile.write('VOLTAGE(V),')
#     logfile.write('TEMPERATURE(C),')
#     logfile.write('RESULT\n')
#     logfile.flush()


def bkload_measure_check(current,voltage):
  
  ts = datetime.now().isoformat()

  [r_mppt_v, r_mppt_i] = bkload.read()

  tolerance = 0.05
  current_max = current * (1 + tolerance)
  current_min = current * (1 - tolerance)
  voltage_max = voltage * (1 + tolerance)
  voltage_min = voltage * (1 - tolerance)

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
  print ('MPPT ' + result + ' @ ' + str(r_mppt_v) + 'V, ' + str(r_mppt_i) + 'A')
  # logfile.write('%s,' % ts)
  # logfile.write('%s,' % r_mppt_i)
  # logfile.write('%s,' % r_mppt_v)
  # logfile.write('%s\n' % result)

print " MPPT power test started"
bkload.load_switch('on')
ps.ind_output('1','on')
chroma.set_output('on') 
sleep(10)
bkload_measure_check(2, 46)
sleep(5)
bkload_measure_check(2, 46)
daq.switch('112','close')
daq.config('112','TC','J')
print daq.measure('112')

#clean up
chroma.set_output('off')
ps.ind_output('1','off')
bkload.load_switch('off')

print ' MPPT power test completed'
