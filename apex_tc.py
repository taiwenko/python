#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Author: TaiWen Ko

import xpf6020
import watlowf4
import sys
import twk_utils

from datetime import datetime
from time import sleep

utils = twk_utils.Twk_utils()

from datetime import datetime
from time import sleep
from tools import shell

max_cycle = raw_input('How many temp cycles would you like to run?: ').strip()
pfc_path ='/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1a-if01-port0'

# Charge battery @ 50V and 2A max
#ps_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5029ID1-if00-port0'
ps_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'
ps_volt = 48
ps_current = 2
print "Accessing the XPF6020 Power Supply"
ps = xpf6020.Xpf6020(ps_path)
ps.reset_ps()
ps.set_voltage(1, ps_volt)
ps.set_currentlimit(1, ps_current)

print "Accessing the Temperature Chamber"
tchamber_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A603R0MG-if00-port0'
chamber = watlowf4.WatlowF4(tchamber_path)
chamber.conditioning_on(False)

def fs_format(pfc_path):

  print "Formating SD card..."
  tom = shell.Shell(pfc_path)
  sleep(5)
  tom.sendline('fs format')
  sleep(10)
  tom.close()
  print "Finished formatting"

# Temperature Cycling
# 1. Rise temperature to hot_temp to burn off excess moister in chamber
# 2. Drop temperature to ambient_temp
# 3. Drop temperature to cold_start to test cold start
# 4. Turn on GXPR power and measure SB
# 5. Rise temperature to cold_temp
# 6. Measure SB
# 7. Rise temperature to ambient_temp
# 8. Measure SB
# 9. Rise temperature to hot_temp
# 10. Measure SB

# Temperature Profile
cold_start = -60
cold_temp = -40
ambient_temp = -20
zero_temp = 0
hot_temp = 50
soaktime = 20
sleep_time = 1800
cycle = 0

ts = utils.get_timestamp()
print '****APEX5 Temp Test started...[%s]****' % ts
utils.print_line()

# # Burn off excessive moisture
chamber.conditioning_on(True)
chamber.ramp_up(hot_temp)
chamber.soak_time(soaktime)

while cycle != int(max_cycle):

  cycle = cycle + 1
  # #------------
  # ps.ind_output('1','on')
  # sleep(5)
  # sb_measure(pfc_path)
  # sleep(10)
  # #------------

  chamber.ramp_down(cold_start)
  chamber.soak_time(soaktime)

  # Power on Motherbrain
  ps.ind_output('1','on')
  sleep(10)

  if cycle == 1:
    fs_format(pfc_path)

  # measure @ cold start
  sleep(sleep_time)

  # measure @ cold temp
  chamber.ramp_up(cold_temp)
  chamber.soak_time(soaktime)
  sleep(sleep_time)

  # measure @ ambient temp
  chamber.ramp_up(ambient_temp)
  chamber.soak_time(soaktime)
  sleep(sleep_time)

  # measure @ zero temp
  chamber.ramp_up(zero_temp)
  chamber.soak_time(soaktime)
  sleep(sleep_time)

  print 'Cycle %s/%s completed.' % (str(cycle), str(max_cycle))
  ps.ind_output('1','off')

#clean up
chamber.ramp_up(23)
chamber.soak_time(soaktime)
chamber.conditioning_on(False)
ts = utils.get_timestamp()
msg = '****APEX5 Temp Test completed...[%s]****' % ts
utils.send_email('APEX5 Temp Test', msg)
