#!/usr/bin/env python

# rffe functional test
# Author: TaiWen Ko

import xpf6020
import bk8500
import math
import os

from time import sleep
from blessings import Terminal
t = Terminal()

print "Accessing the Power Supply"

ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A403OT39-if00-port0'

ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_currentlimit(1,3)

print "Accessing the BK Electronic Load"

bkload = bk8500.Bk8500()
bkload.remote_switch('on')

def measure_check(vin,iin,ch_v,ch_i,ch_i_max):

  ps.set_voltage(1,vin)
  bkload.config_cc_mode(ch_i,ch_i_max)

  bkload.load_switch('on')
  ps.ind_output('1','on')
  sleep(10)

  [p_ch_v, p_ch_i] = ps.measure('1')
  volt = float(p_ch_v.split("V")[0])
  curr = float(p_ch_i.split("A")[0])
  tolerance = 0.03
  p_current_max = iin * (1 + tolerance)
  p_current_min = iin * (1 - tolerance)
  p_voltage_max = vin * (1 + tolerance)
  p_voltage_min = vin * (1 - tolerance)
  sleep(1)

  if float(curr) > float(p_current_max):
    result = t.bold_red('FAILED')
  elif float(curr) < float(p_current_min):
    result = t.bold_red('FAILED')
  elif float(volt) > float(p_voltage_max):
    result = t.bold_red('FAILED')
  elif float(volt) < float(p_voltage_min):
    result = t.bold_red('FAILED')
  else:
    result = t.bold_green('PASSED')
  print ('UUT input ' + result + ' @ ' + str(volt) + 'V, ' + str(curr) + 'A')

  [r_ch_v, r_ch_i] = bkload.read()
  current_max = ch_i * (1 + tolerance)
  current_min = ch_i * (1 - tolerance)
  voltage_max = ch_v * (1 + tolerance)
  voltage_min = ch_v * (1 - tolerance)
  sleep(1)

  if float(r_ch_i) > float(current_max):
    result = t.bold_red('FAILED')
  elif float(r_ch_i) < float(current_min):
    result = t.bold_red('FAILED')
  elif float(r_ch_v) > float(voltage_max):
    result = t.bold_red('FAILED')
  elif float(r_ch_v) < float(voltage_min):
    result = t.bold_red('FAILED')
  else:
    result = t.bold_green('PASSED')
  print ('UUT output ' + result + ' @ ' + str(r_ch_v) + 'V, ' + str(r_ch_i) + 'A')

  # clean up
  bkload.load_switch('off')
  ps.all_output('off')

while True:

  measure_check(24,1.15,5.25,4,5)
  measure_check(10,2.75,5.25,4,5)

  more = raw_input('AIS power test completed.  Continue to next UUT? [y/N]  ')

  if more != 'y':
    bkload.remote_switch('off')
    break;

raw_input('\n\nPress Enter to close.')
