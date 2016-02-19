#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the gxpr_temp_test with Major Tom
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

# change the order of sbvars will effect the matlab script
sbvars = []
sbvars.append('avionics_barometric_pressure')
sbvars.append('avionics_barometer_temperature')
sbvars.append('pfc_temperature_mppt')
sbvars.append('pfc_temperature_iridium')
sbvars.append('pfc_temperature_top_edge')
sbvars.append('pfc_temperature_mcu')
sbvars.append('flashers_voltage')
sbvars.append('transponder_voltage')
sbvars.append('power_5v0_voltage')
sbvars.append('power_3v3_voltage')
sbvars.append('power_vplus_voltage')
sbvars.append('power_solar0_voltage')
sbvars.append('power_mppt0_voltage')
sbvars.append('power_mppt1_voltage')
sbvars.append('power_mppt2_voltage')
sbvars.append('power_downlink_voltage')
sbvars.append('power_mesh_voltage')
sbvars.append('power_despin_voltage')
sbvars.append('power_backhaul_voltage')
sbvars.append('power_payload_voltage')
sbvars.append('power_aux_voltage')
sbvars.append('power_nav_voltage')
sbvars.append('power_iridium_voltage')
sbvars.append('envelope_voltage')

i2cvars = []
i2cvars.append('i2c2.addr_nacks')
i2cvars.append('i2c1.last_nack_addr')
i2cvars.append('i2c2.timeouts')
i2cvars.append('i2c1.txn_successes')
i2cvars.append('i2c1.addr_nacks')
i2cvars.append('i2c1.tx_nacks')
i2cvars.append('i2c2.txn_successes')
i2cvars.append('i2c2.tx_nacks')
i2cvars.append('i2c1.bus_errors')
i2cvars.append('i2c2.arb_losts')
i2cvars.append('i2c1.unstick_attempts')
i2cvars.append('i2c1.wtf_events')
i2cvars.append('i2c2.last_nack_addr')
i2cvars.append('i2c2_sched.last_violation_index')
i2cvars.append('i2c1.timeouts')
i2cvars.append('i2c2.last_wtf_details')
i2cvars.append('i2c2.unstick_attempts')
i2cvars.append('i2c2.bus_errors')
i2cvars.append('i2c2_sched.violation_count')
i2cvars.append('i2c1.last_wtf_details')
i2cvars.append('i2c1_sched.violation_count')
i2cvars.append('i2c1_sched.last_violation_index')
i2cvars.append('i2c2.wtf_events')
i2cvars.append('i2c1.arb_losts')

max_cycle = raw_input('How many temp cycles would you like to run?: ').strip()
pfc_path ='/dev/serial/by-id/usb-loon_onboard_motherbrain_pfc-if01-port0'

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

# Discharge battery @ CV mode, 46V, and 50V max
# print "Accessing the BK8500 Electronic Load"
# bkload = bk8500.Bk8500()
# bkload.remote_switch('on')

print "Accessing the Temperature Chamber"
tchamber_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A603R0MG-if00-port0'
chamber = watlowf4.WatlowF4(tchamber_path)
chamber.conditioning_on(False)

# Write headers
ts = utils.get_timestamp()
logdir = '../motherbrain_tc_test-%s.csv' % ts
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP')
    for sbvar in sbvars:
        logfile.write(',%s' % sbvar)
    for i2cvar in i2cvars:
        logfile.write(',%s' % i2cvar)
    logfile.write(',\n')
    logfile.flush()


def sb_measure(pfc_path):

  print "Recording MB SB data..."
  tom = shell.Shell(pfc_path)
  sleep(2)
  sb = shell.Scoreboard(tom,'')
  sleep(2)
  ts = utils.get_timestamp()
  logfile.write(ts)
  for sbvar in sbvars:
      logfile.write(',%s' % str(sb.query(sbvar)).split("'")[3])
  vardata = str(sb.query_i2c())
  for i in range(24):
      vdata = vardata.split(",")[i-1]
      data = vdata.split(":")[1]
      logfile.write(',%s' % data)
  logfile.write(',\n')
  tom.close()
  print "Finished recording data"


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
cold_start = -40
cold_temp = -20
zero_temp = 0
ambient_temp = 23
hot_temp = 50
soaktime = 20
cycle = 0
max_count = 300
count = 1
monitor_freq = 1

fs_format(pfc_path)

ts = utils.get_timestamp()
print '****Motherbrain Temp Test started...[%s]****' % ts
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

  # measure @ cold start
  while count < max_count:
    sb_measure(pfc_path)
    count = count + 1
    sleep(monitor_freq)
  count = 1

  # measure @ cold temp
  chamber.ramp_up(cold_temp)
  chamber.soak_time(soaktime)
  while count < max_count:
    sb_measure(pfc_path)
    count = count + 1
    sleep(monitor_freq)
  count = 1

  # measure @ zero temp
  chamber.ramp_up(zero_temp)
  chamber.soak_time(soaktime)
  while count < max_count:
    sb_measure(pfc_path)
    count = count + 1
    sleep(monitor_freq)
  count = 1

  # measure @ ambient temp
  chamber.ramp_up(ambient_temp)
  chamber.soak_time(soaktime)
  while count < max_count:
    sb_measure(pfc_path)
    count = count + 1
    sleep(monitor_freq)
  count = 1

  # measure @ hot temp
  chamber.ramp_up(hot_temp)
  chamber.soak_time(soaktime)
  while count < max_count:
    sb_measure(pfc_path)
    count = count + 1
    sleep(monitor_freq)
  count = 1

  print 'Cycle %s/%s completed.' % (str(cycle), str(max_cycle))
  ps.ind_output('1','off')

#clean up
chamber.ramp_down(ambient_temp)
chamber.soak_time(soaktime)
chamber.conditioning_on(False)
ts = utils.get_timestamp()
msg = '****Motherbrain Temp Test completed...[%s]****' % ts
utils.send_email('Motherbrain Temp Test', msg)
