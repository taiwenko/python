#!/usr/bin/env python

# Routines for the battery acceptance testing

import xpf6020
import bk8500
from datetime import datetime
from time import sleep
import tools.utils as tools
from tools import shell
import twk_utils

utils = twk_utils.Twk_utils()

# Make sure to use the correct serial-to-usb1 cable
ps1_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A703U4HD-if00-port0'
ps2_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AH028NK1-if00-port0'
eload1_path = '/dev/serial/by-path/pci-0000:00:14.0-usb-0:2.1:1.0-port'
eload2_path = '/dev/serial/by-path/pci-0000:00:14.0-usb-0:2.2:1.0-port'
eload3_path = '/dev/serial/by-path/pci-0000:00:14.0-usb-0:2.4:1.0-port'
eload4_path = '/dev/serial/by-path/pci-0000:00:14.0-usb-0:2.7.1:1.0-port'
pfc1_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1a-if01-port0'
pfc2_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_2a-if01-port0'
pfc3_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1b-if01-port0'
pfc4_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_2b-if01-port0'

batt_num = None

while True:
    batt_num = raw_input('How many batteries would you like to test? [ 1 ~ 4 ]: ')
    message = raw_input('Testing %s battery(s). Is this correct? [y/N]' % (batt_num))
    if message == 'y' and (batt_num == '1' or batt_num == '2' or batt_num == '3' or batt_num == '4'):
      break;

print "Accessing the power supplies and electronic loads"
pfc_v = 50
pfc_i = 2

batt_i = 10
batt_i_max = 15

ps1 = xpf6020.Xpf6020(ps1_path)
ps1.reset_ps()
ps1.set_voltage(1, pfc_v)
ps1.set_currentlimit(1, pfc_i)

bkload1 = bk8500.Bk8500(eload1_path)
bkload1.remote_switch('on')
bkload1.config_cc_mode(batt_i, batt_i_max)

if batt_num == '2':
  ps1.set_voltage(2, pfc_v)
  ps1.set_currentlimit(2, pfc_i)
  bkload2 = bk8500.Bk8500(eload2_path)
  bkload2.remote_switch('on')
  bkload2.config_cc_mode(batt_i, batt_i_max)
elif batt_num == '3':
  ps1.set_voltage(2, pfc_v)
  ps1.set_currentlimit(2, pfc_i)
  ps2 = xpf6020.Xpf6020(ps2_path)
  ps2.reset_ps()
  ps2.set_voltage(1, pfc_v)
  ps2.set_currentlimit(1, pfc_i)
  bkload2 = bk8500.Bk8500(eload2_path)
  bkload2.remote_switch('on')
  bkload2.config_cc_mode(batt_i, batt_i_max)
  bkload3 = bk8500.Bk8500(eload3_path)
  bkload3.remote_switch('on')
  bkload3.config_cc_mode(batt_i, batt_i_max)
elif batt_num == '4':
  ps1.set_voltage(2, pfc_v)
  ps1.set_currentlimit(2, pfc_i)
  ps2 = xpf6020.Xpf6020(ps2_path)
  ps2.reset_ps()
  ps2.set_voltage(1, pfc_v)
  ps2.set_currentlimit(1, pfc_i)
  ps2.set_voltage(2, pfc_v)
  ps2.set_currentlimit(2, pfc_i)
  bkload2 = bk8500.Bk8500(eload2_path)
  bkload2.remote_switch('on')
  bkload2.config_cc_mode(batt_i, batt_i_max)
  bkload3 = bk8500.Bk8500(eload3_path)
  bkload3.remote_switch('on')
  bkload3.config_cc_mode(batt_i, batt_i_max)
  bkload4 = bk8500.Bk8500(eload4_path)
  bkload4.remote_switch('on')
  bkload4.config_cc_mode(batt_i, batt_i_max)
elif batt_num != '1':
  raise Exception, 'Unknown command.'

# Wait for loads to turn on
sleep(5)

# Turn on power and apply fs format
ps1.all_output('on')
if batt_num == '3':
  ps2.all_output('on')
  sleep(3)
elif batt_num == '4':
  ps2.all_output('on')

print "Accessing the PFCs"
tom1 = shell.Shell(pfc1_path)
sb1 = shell.Scoreboard(tom1,'battery')
tom1.sendline('fs format')
sleep(5)
if batt_num == '2':
  tom2 = shell.Shell(pfc2_path)
  sb2 = shell.Scoreboard(tom2,'battery')
  tom2.sendline('fs format')
  sleep(5)
elif batt_num == '3':
  tom2 = shell.Shell(pfc2_path)
  sb2 = shell.Scoreboard(tom2,'battery')
  tom2.sendline('fs format')
  sleep(5)
  tom3 = shell.Shell(pfc3_path)
  sb3 = shell.Scoreboard(tom3,'battery')
  tom3.sendline('fs format')
  sleep(5)
elif batt_num == '4':
  tom2 = shell.Shell(pfc2_path)
  sb2 = shell.Scoreboard(tom2,'battery')
  tom2.sendline('fs format')
  sleep(5)
  tom3 = shell.Shell(pfc3_path)
  sb3 = shell.Scoreboard(tom3,'battery')
  tom3.sendline('fs format')
  sleep(5)
  tom4 = shell.Shell(pfc4_path)
  sb4 = shell.Scoreboard(tom4,'battery')
  tom4.sendline('fs format')
  sleep(5)
elif batt_num != '1':
  raise Exception, 'Unknown command.'

# Turn on the loads
bkload1.load_switch('on')
sleep(1)
if batt_num == '2':
  bkload2.load_switch('on')
  sleep(1)
elif batt_num == '3':
  bkload2.load_switch('on')
  sleep(1)
  bkload3.load_switch('on')
  sleep(1)
elif batt_num == '4':
  bkload2.load_switch('on')
  sleep(1)
  bkload3.load_switch('on')
  sleep(1)
  bkload4.load_switch('on')
  sleep(1)
elif batt_num != '1':
  raise Exception, 'Unknown command.'

# Wait for 1 hour
on_duration = 60 # in mins
on_duration_sec = on_duration * 60
sleep(on_duration_sec)

# Turn off the loads
bkload1.load_switch('off')
sleep(1)
if batt_num == '2':
  bkload2.load_switch('off')
  sleep(1)
elif batt_num == '3':
  bkload2.load_switch('off')
  sleep(1)
  bkload3.load_switch('off')
  sleep(1)
elif batt_num == '4':
  bkload2.load_switch('off')
  sleep(1)
  bkload3.load_switch('off')
  sleep(1)
  bkload4.load_switch('off')
  sleep(1)
elif batt_num != '1':
  raise Exception, 'Unknown command.'

# Wait for 2 hours
off_duration = 120 # in mins
off_duration_sec = off_duration * 60
sleep(off_duration_sec)

# Turn off the power supplies
ps1.all_output('off')
if batt_num == '3':
  ps2.all_output('off')
  sleep(3)
elif batt_num == '4':
  ps2.all_output('off')
  sleep(3)

ts = utils.get_timestamp()
message = '*** Test Completed @ %s***' % ts
print message
utils.send_email('Battery Acceptance Test', message)
