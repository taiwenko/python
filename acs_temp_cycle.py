#!/usr/bin/env python

## TO-DOs
## Add logs report

from time import sleep
import twk_utils
import math
import sys
import xpf6020
import tools.utils as tools
import watlowf4
from tools import shell
from blessings import Terminal

t = Terminal()

franz_num = raw_input('How many Franz are you testing? [1,2,3,or 4]: ').strip()
cycle_num = raw_input('How many temp cycles would you like to run?: ').strip()

utils = twk_utils.Twk_utils()

print "Accessing the XPF6020 Power Supplies"

ps1_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'
ps2_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A703PO3I-if00-port0'

pfc1_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1a-if01-port0'
pfc2_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_2a-if01-port0'
pfc3_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1b-if01-port0'
pfc4_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_2b-if01-port0'

print "Accessing the Temperature Chamber"
tchamber_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A603R0MG-if00-port0'
chamber = watlowf4.WatlowF4(tchamber_path)
chamber.conditioning_on(True)

# Setup chamber
cold_temp = 10 #-60
soak_time = 1 #45 # min
chamber.ramp_down(cold_temp)
chamber.soak_time(soak_time)

batt_vin = 48
batt_iin = 20

ps1 = xpf6020.Xpf6020(ps1_path)
ps1.reset_ps()
ps2 = xpf6020.Xpf6020(ps2_path)
ps2.reset_ps()

ps1.set_voltage(1, batt_vin)
ps1.set_currentlimit(1, batt_iin)
if franz_num == '2':
  ps1.set_voltage(2, batt_vin)
  ps1.set_currentlimit(2, batt_iin)
elif franz_num == '3':
  ps1.set_voltage(2, batt_vin)
  ps1.set_currentlimit(2, batt_iin)
  ps2.set_voltage(1,batt_vin)
  ps2.set_currentlimit(1,batt_iin)
elif franz_num == '4':
  ps1.set_voltage(2, batt_vin)
  ps1.set_currentlimit(2, batt_iin)
  ps2.set_voltage(1,batt_vin)
  ps2.set_currentlimit(1,batt_iin)
  ps2.set_voltage(2,batt_vin)
  ps2.set_currentlimit(2,batt_iin)
else:
  if franz_num != '1':
    print 'Unknown franz amount. Can only test up to 4 franz at a time.'
    sys.exit()

def ps_measure_check(ch, current_min, current_max, voltage_min, voltage_max, tolerance, max_cycle):

  cycle = 0
  avg_volt = 0
  avg_current = 0

  while cycle != max_cycle:
    if ch == '1':
      [r_mppt_v, r_mppt_i] = ps1.measure('1')
    elif ch == '2':
      [r_mppt_v, r_mppt_i] = ps1.measure('2')
    elif ch == '3':
      [r_mppt_v, r_mppt_i] = ps2.measure('1')
    elif ch == '4':
      [r_mppt_v, r_mppt_i] = ps2.measure('2')
    else:
      print 'Unknown Input Channel'

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

# def sb_query(CH, pfc_path):
#   tom = shell.Shell(pfc_path)
#   sleep(1)
#   sb = shell.Scoreboard(tom,'acs')
#   sleep(3)
#   esc_temp = str(sb.query('acs_temperature_fan_esc'))
#   current_esc_temp = esc_temp.split("'")[3]
#   print current_esc_temp
#   acs_temp = str(sb.query('acs_temperature_top_0'))
#   current_acs_temp = acs_temp.split("'")[3]
#   print current_acs_temp
#   tom.close()
#   sleep(3)
#   return float(current_esc_temp)


def config_burnin(pfc_path, ontime):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('acs descend 0 %s 100 150' % ontime )
  sleep(3)
  tom.close()

# Test starts here

#print "Accessing Major Tom"

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

# print "Preparing logfile"
# ts = utils.get_timestamp()
# logdir = '../acs-burnin-%s.csv' % ts
# logfile = open(logdir, 'wt')
# try:
#     if logfile.tell() == 0:
#         raise IOError, 'Null Error'
# except IOError:
#     logfile.write('TIMESTAMP,')
#     for var in sbvars:
#         logfile.write('"%s",' % var)
#         logfile.write('CH,')
#         logfile.write('VOLT,')
#         logfile.write('CURRENT,')
#     logfile.write('TIMESTAMP\n')
#     logfile.flush()

ts = utils.get_timestamp()
print '*** Franz test started @ %s***' % ts

ps1.ind_output('1','on')
esc1_temp = config_acs(pfc1_path)
if franz_num == '2':
  ps1.ind_output('2','on')
  esc2_temp = config_acs(pfc2_path)
elif franz_num == '3':
  ps1.ind_output('2','on')
  esc2_temp = config_acs(pfc2_path)
  ps2.ind_output('1','on')
  esc3_temp = config_acs(pfc3_path)
elif franz_num == '4':
  ps1.ind_output('2','on')
  esc2_temp = config_acs(pfc2_path)
  ps2.ind_output('1','on')
  esc3_temp = config_acs(pfc3_path)
  ps2.ind_output('2','on')
  esc4_temp = config_acs(pfc4_path)
else:
  if franz_num != '1':
    print 'Unknown Channel'


# Set ESC setpoint using measured temperature + 10C
esc_setpoint = 275
print esc_setpoint
config_acs_setpoint(pfc1_path, esc_setpoint)

config_esc_setpoint(pfc1_path, esc_setpoint)
if franz_num == '2':
  config_acs_setpoint(pfc2_path, esc_setpoint)

  config_esc_setpoint(pfc2_path, esc_setpoint)
elif franz_num == '3':
  config_acs_setpoint(pfc2_path, esc_setpoint)
  config_acs_setpoint(pfc3_path, esc_setpoint)

  config_esc_setpoint(pfc2_path, esc_setpoint)
  config_esc_setpoint(pfc3_path, esc_setpoint)
elif franz_num == '4':
  config_acs_setpoint(pfc2_path, esc_setpoint)
  config_acs_setpoint(pfc3_path, esc_setpoint)
  config_acs_setpoint(pfc4_path, esc_setpoint)

  config_esc_setpoint(pfc2_path, esc_setpoint)
  config_esc_setpoint(pfc3_path, esc_setpoint)
  config_esc_setpoint(pfc4_path, esc_setpoint)
else:
  if franz_num != '1':
    print 'Unknown Channel'

# Give some tolerance
esc_setpoint = esc_setpoint - 3

while True:

  if franz_num == '1':
    esc1_temp = check_esc_temp(pfc1_path)
    if esc1_temp > (esc_setpoint):
      break;
  elif franz_num == '2':
    esc1_temp = check_esc_temp(pfc1_path)
    esc2_temp = check_esc_temp(pfc2_path)
    if esc1_temp > (esc_setpoint):
      if esc2_temp > (esc_setpoint):
        break;
  elif franz_num == '3':
    esc1_temp = check_esc_temp(pfc1_path)
    esc2_temp = check_esc_temp(pfc2_path)
    esc3_temp = check_esc_temp(pfc3_path)
    if esc1_temp > (esc_setpoint):
      if esc2_temp > (esc_setpoint):
        if esc3_temp > (esc_setpoint):
          break;
  elif franz_num == '4':
    esc1_temp = check_esc_temp(pfc1_path)
    esc2_temp = check_esc_temp(pfc2_path)
    esc3_temp = check_esc_temp(pfc3_path)
    esc4_temp = check_esc_temp(pfc4_path)
    if esc1_temp > (esc_setpoint):
      if esc2_temp > (esc_setpoint):
        if esc3_temp > (esc_setpoint):
          if esc4_temp > (esc_setpoint):
            break;
  else:
    print 'Unknown Channel'

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

  config_burnin(pfc1_path, ontime_sec)
  if franz_num == '2':
    config_burnin(pfc2_path, ontime_sec)
  elif franz_num == '3':
    config_burnin(pfc2_path, ontime_sec)
    config_burnin(pfc3_path, ontime_sec)
  elif franz_num == '4':
    config_burnin(pfc2_path, ontime_sec)
    config_burnin(pfc3_path, ontime_sec)
    config_burnin(pfc4_path, ontime_sec)
  else:
    if franz_num != '1':
      print 'Unknown Channel'

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
  while total_cycle < cycle_num:
    ps_measure_check('1', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    if franz_num == '2':
      ps_measure_check('2', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    elif franz_num == '3':
      ps_measure_check('2', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
      ps_measure_check('3', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    elif franz_num == '4':
      ps_measure_check('2', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
      ps_measure_check('3', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
      ps_measure_check('4', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    else:
      if franz_num != '1':
        print 'Unknown franz amount.'
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
  print 'Off for 5 min started @ %s' % ts
  sleep(offtime_sec)
  ts = utils.get_timestamp()
  print 'On for 15 min started @ %s' % ts
  hot_temp = 24
  print 'Ramping up to 24C'
  chamber.set_temp(hot_temp)

ts = utils.get_timestamp()
print '*** Franz test completed @ %s***' % ts
utils.send_email('ACS Burn-In', 'ACS Burn-In is done!!')

#Clean up
ps1.all_output('off')
ps2.all_output('off')
