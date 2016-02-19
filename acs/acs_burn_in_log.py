#!/usr/bin/env python

from time import sleep
import twk_utils
import math
import sys
import tools.utils as tools
from tools import shell
from blessings import Terminal

t = Terminal()

utils = twk_utils.Twk_utils()

pfc_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1a-if01-port0'

def ps_measure_check(ch, current_min, current_max, voltage_min, voltage_max, tolerance, max_cycle):

  cycle = 0
  avg_volt = 0
  avg_current = 0

    volt = float(r_mppt_v.split("V")[0])
    curr = float(r_mppt_i.split("A")[0])
    avg_volt = avg_volt + volt
    avg_current = avg_current + curr
    cycle = cycle + 1
    sleep(1)

  r_mppt_v = avg_volt / cycle;
  r_mppt_i = avg_current / cycle;

  if float(r_mppt_i) > float(current_max):
    result = t.bold_red('FAILED')
  elif float(r_mppt_i) < float(current_min):
    result = t.bold_red('FAILED')
  elif float(r_mppt_v) > float(voltage_max):
    result = t.bold_red('FAILED')
  elif float(r_mppt_v) < float(voltage_min):
    result = t.bold_red('FAILED')
  else:
    result = t.bold_green('PASSED')

  print 'Franz CH%s @ %sV, %sA....[%s]' %(ch, r_mppt_v, r_mppt_i, result)
  print ''

def config_acs(pfc_path):
  sleep(5)
  tom = shell.Shell(pfc_path)
  sleep(1)
  sb = shell.Scoreboard(tom,'acs')
  sleep(1)
  tom.sendline('power on acs')
  sleep(3)
  print sb.query('power_acs_enabled')
  sleep(1)
  tom.sendline('acs esc on')
  sleep(5)
  esc_state = str(sb.query('acs_fan_esc_power_state'))
  current_esc_state = esc_state.split("'")[3]
  sleep(3)

  while current_esc_state != 'On':
    tom.sendline('acs esc on')
    sleep(6)
    esc_state = str(sb.query('acs_fan_esc_power_state'))
    current_esc_state = esc_state.split("'")[3]
    print current_esc_state
    sleep(2)

  print sb.query('acs_fan_esc_switch_on')
  esc_temp = str(sb.query('acs_temperature_fan_esc'))
  current_esc_temp = esc_temp.split("'")[3]
  print current_esc_temp
  tom.close()
  sleep(3)
  return float(current_esc_temp)

def config_acs_setpoint(pfc_path, esc_setpoint):
  tom = shell.Shell(pfc_path)
  sleep(1)
  sb = shell.Scoreboard(tom,'acs')
  tom.sendline('heater set acs.main %s' % esc_setpoint)
  sleep(3)
  acs_sp = str(sb.query('acs_heater_setpoint_main'))
  current_acs_sp = acs_sp.split("'")[3]
  print 'ACS setpoint was set to %s' % current_acs_sp
  tom.close()

def config_esc_setpoint(pfc_path, esc_setpoint):
  tom = shell.Shell(pfc_path)
  sleep(1)
  sb = shell.Scoreboard(tom,'acs')
  tom.sendline('heater set acs.esc.on %s' % esc_setpoint)
  sleep(3)
  tom.sendline('acs esc_activation_temperature %s' % esc_setpoint)
  sleep(3)
  esc_sp = str(sb.query('acs_heater_setpoint_fan_esc'))
  current_esc_sp = esc_sp.split("'")[3]
  print 'ESC setpoint was set to %s' % current_esc_sp
  tom.close()

def check_esc_temp(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(1)
  sb = shell.Scoreboard(tom,'acs')
  sleep(3)
  esc_temp = str(sb.query('acs_temperature_fan_esc'))
  current_esc_temp = esc_temp.split("'")[3]
  print current_esc_temp
  acs_temp = str(sb.query('acs_temperature_top_0'))
  current_acs_temp = acs_temp.split("'")[3]
  print current_acs_temp
  tom.close()
  sleep(3)
  return float(current_esc_temp)

def config_burnin(pfc_path, ontime):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('acs descend 0 %s 100 400' % ontime )
  sleep(3)
  tom.close()

# Test starts here

# print "Accessing Major Tom"

# tom = shell.Shell()
# sb = shell.Scoreboard(tom, None)
# sbvars = []
# sbvars.append('acs_error')
# sbvars.append('acs_state')
# sbvars.append('power_acs_enabled')
# sbvars.append('acs_fan_esc_power_state')
# sbvars.append('acs_heater_setpoint_main')
# sbvars.append('acs_heater_setpoint_fan_esc')
# sbvars.append('acs_temperature_fan_esc')
# sbvars.append('acs_temperature_top_0')

# # print "Preparing logfile"
# ts = utils.get_timestamp()
# logdir = '../acs-burnin-%s.csv' % ts
# logfile = open(logdir, 'wt')
# try:
#     if logfile.tell() == 0:
#          raise IOError, 'Null Error'
# except IOError:
#       logfile.write('TIMESTAMP,')
#      for var in sbvars:
#          logfile.write('"%s",' % var)
#          logfile.write('CH,')
#          logfile.write('VOLT,')
#          logfile.write('CURRENT,')
#      logfile.write('TIMESTAMP\n')
#      logfile.flush()

ts = utils.get_timestamp()
print '*** Franz test started @ %s***' % ts

esc_temp = config_acs(pfc_path)

# Set ESC setpoint using measured temperature + 10C
esc_setpoint = 275
print esc_setpoint
config_acs_setpoint(pfc_path, esc_setpoint)
config_esc_setpoint(pfc_path, esc_setpoint)
# Give some tolerance
esc_setpoint = esc_setpoint - 3

while True:
  esc1_temp = check_esc_temp(pfc_path)
  if esc1_temp > (esc_setpoint):
    break;

max_cycle = 15
total_cycle = 0
ontime = 15 # for 15 mins
ontime_sec = ontime * 60
offtime = 5
offtime_sec = offtime * 60
total_time = ontime * 2 + offtime
run_count = 0
max_run_count = 2

ts = utils.get_timestamp()
print '*** %s min burn-in started @ %s***' % (total_time, ts)
print 'On for 15 min started @ %s' % (ts)

while True:

  config_burnin(pfc_path, ontime_sec)

  measurement_count = 5
  print 'Averaging %d measurement...' % measurement_count

  current = 3.4
  voltage = 48
  tolerance = 0.3
  current_max = float(current) * (1 + tolerance)
  current_min = float(current) * (1 - tolerance)
  voltage_max = float(voltage) * (1 + tolerance)
  voltage_min = float(voltage) * (1 - tolerance)

  print 'Voltage Limits should be within %f to %fV' %(voltage_min, voltage_max)
  print 'Current Limits should be within %f to %fA' %(current_min, current_max)
  print ''

  # On for 15 min, while total
  while total_cycle < max_cycle:
    sleep(40) # check ps at every min (40+20 for checking) for 15 cycles
    total_cycle = total_cycle + 1
    ts = utils.get_timestamp()
    print 'Check %s/%s completed @ %s***' % (total_cycle, max_cycle, ts)
    print ''

  total_cycle = 0

  run_count = run_count + 1
  if run_count == max_run_count:
    break;

ts = utils.get_timestamp()
print '*** Franz test completed @ %s***' % ts
utils.send_email('ACS Burn-In', 'ACS Burn-In is done!!')

