#!/usr/bin/env python

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
    result_count = 1
  elif float(r_mppt_i) < float(current_min):
    result = t.bold_red('FAILED')
    result_count = 1
  elif float(r_mppt_v) > float(voltage_max):
    result = t.bold_red('FAILED')
    result_count = 1
  elif float(r_mppt_v) < float(voltage_min):
    result = t.bold_red('FAILED')
    result_count = 1
  else:
    result = t.bold_green('PASSED')
    result_count = 0

  print 'Franz CH%s @ %sV, %sA....[%s]' %(ch, r_mppt_v, r_mppt_i, result)
  print ''
  return result_count

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
  tom.close()

def clean_acs(pfc_path):
  sleep(5)
  tom = shell.Shell(pfc_path)
  sleep(1)
  sb = shell.Scoreboard(tom,'acs')
  sleep(1)
  tom.sendline('power off acs')
  sleep(3)
  print sb.query('power_acs_enabled')
  sleep(1)
  tom.close()


# Test starts here
offtime = 1 #15 #mins
offtime_sec = offtime * 60
run_count = 0
max_run_count = cycle_num
ch1result = 0
ch2result = 0
ch3result = 0
ch4result = 0

ts = utils.get_timestamp()
print '*** Franz test started @ %s***' % ts

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

# Setup chamber
cold_temp = 20 #-60
soak_time = 1 #45 # min
chamber.ramp_down(cold_temp)
chamber.soak_time(soak_time)

while True:

  # Turn on power supplies
  ps1.ind_output('1','on')
  if franz_num == '2':
    ps1.ind_output('2','on')
  elif franz_num == '3':
    ps1.ind_output('2','on')
    ps2.ind_output('1','on')
  elif franz_num == '4':
    ps1.ind_output('2','on')
    ps2.ind_output('1','on')
    ps2.ind_output('2','on')
  else:
    if franz_num != '1':
      print 'Unknown Channel'

  sleep(5)

  # Turn on ACS using PFC
  config_acs(pfc1_path)
  if franz_num == '2':
    config_acs(pfc2_path)
  elif franz_num == '3':
    config_acs(pfc2_path)
    config_acs(pfc3_path)
  elif franz_num == '4':
    config_acs(pfc2_path)
    config_acs(pfc3_path)
    config_acs(pfc4_path)
  else:
    if franz_num != '1':
      print 'Unknown Channel'

  sleep(5)

  # Measure current draw from PS
  measurement_count = 5
  print 'Averaging %d measurement...' % measurement_count

  current = 0.12
  voltage = 48
  tolerance = 0.05
  current_max = float(current) * (1 + tolerance)
  current_min = float(current) * (1 - tolerance)
  voltage_max = float(voltage) * (1 + tolerance)
  voltage_min = float(voltage) * (1 - tolerance)

  print 'Voltage Limits should be within %f to %fV' %(voltage_min, voltage_max)
  print 'Current Limits should be within %f to %fA' %(current_min, current_max)
  print ''

  rc1 = ps_measure_check('1', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
  ch1result = ch1result + rc1
  if franz_num == '2':
    rc2 = ps_measure_check('2', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    ch2result = ch2result + rc2
  elif franz_num == '3':
    rc2 = ps_measure_check('2', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    ch2result = ch2result + rc2
    rc3 = ps_measure_check('3', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    ch3result = ch3result + rc3
  elif franz_num == '4':
    rc2 = ps_measure_check('2', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    ch2result = ch2result + rc2
    rc3 = ps_measure_check('3', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    ch3result = ch3result + rc3
    rc4 = ps_measure_check('4', current_min, current_max, voltage_min, voltage_max, tolerance, measurement_count)
    ch4result = ch4result + rc4
  else:
    if franz_num != '1':
      print 'Unknown franz amount.'

  # Turn off ACS using PFC
  clean_acs(pfc1_path)
  if franz_num == '2':
    clean_acs(pfc2_path)
  elif franz_num == '3':
    clean_acs(pfc2_path)
    clean_acs(pfc3_path)
  elif franz_num == '4':
    clean_acs(pfc2_path)
    clean_acs(pfc3_path)
    clean_acs(pfc4_path)
  else:
    if franz_num != '1':
      print 'Unknown Channel'

  sleep(5)

  # Turn off power supplies
  ps1.all_output('off')
  ps2.all_output('off')

  run_count = run_count + 1
  if run_count == int(max_run_count):
    break;

  ts = utils.get_timestamp()
  print 'Off for %s min started @ %s' % (offtime, ts)
  sleep(offtime_sec)

hot_temp = 24
print 'Ramping up to 24C'
chamber.ramp_up(hot_temp)

ts = utils.get_timestamp()
msg = '*** ACS test completed @ %s***' % ts
msg = msg + ', CH1 failed %s out of %s cycles' % (ch1result, max_run_count)
msg = msg + ', CH2 failed %s out of %s cycles' % (ch2result, max_run_count)
msg = msg + ', CH3 failed %s out of %s cycles' % (ch3result, max_run_count)
msg = msg + ', CH4 failed %s out of %s cycles' % (ch4result, max_run_count)

print msg
utils.send_email('ACS Cold-Start', msg)


