#!/usr/bin/env python

from time import sleep
import twk_utils
import math
import sys
import xpf6020
import tools.utils as tools
from tools import shell

franz_num = raw_input('How many Franz are you testing? [1,2,3,or 4]: ').strip()

utils = twk_utils.Twk_utils()

print "Accessing the XPF6020 Power Supplies"

ps1_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'
ps2_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A703PO3I-if00-port0'

pfc1_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1a-if01-port0'
pfc2_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_1b-if01-port0'
pfc3_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_2a-if01-port0'
pfc4_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc_2b-if01-port0'

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

def ps_measure_check(ch, current, voltage, tolerance, max_cycle):
  
  cycle = 0
  avg_volt = 0
  avg_current = 0
  print 'Averaging %d measurement...' % max_cycle 

  while cycle != max_cycle:
    if ch == '1':
      [r_mppt_v, r_mppt_i] = ps2.measure('1')
    elif ch == '2':
      [r_mppt_v, r_mppt_i] = ps2.measure('2')
    elif ch == '3':
      [r_mppt_v, r_mppt_i] = ps1.measure('2')
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

  current_max = float(current) * (1 + tolerance)
  current_min = float(current) * (1 - tolerance)
  voltage_max = float(voltage) * (1 + tolerance)
  voltage_min = float(voltage) * (1 - tolerance)

  print 'Checking measurement...' 
  print 'Input voltage should be within %f to %fV' %(voltage_min, voltage_max)
  print 'Input current should be within %f to %fA' %(current_min, current_max)

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
  
  print 'MPPT Input%s %s @ %sV, %sA' %(ch, result, r_mppt_v, r_mppt_i)

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
  sleep(3)
  print sb.query('acs_fan_esc_switch_on')
  esc_temp = str(sb.query('acs_temperature_fan_esc'))
  current_esc_temp = esc_temp.split("'")[3]
  print current_esc_temp
  tom.close()
  sleep(3)
  return float(current_esc_temp)

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
  tom.close()
  sleep(3)
  return float(current_esc_temp)

def config_burnin(pfc_path, ontime):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('acs descend 0 %s 100 300' % ontime ) 
  sleep(3)
  tom.close()

# Test starts here
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
esc_setpoint = (( esc1_temp ) / 1 ) + 10
print esc_setpoint
config_esc_setpoint(pfc1_path, esc_setpoint)
if franz_num == '2':
  esc_setpoint = (( esc1_temp + esc2_temp ) / 2 ) + 10
  config_esc_setpoint(pfc2_path, esc_setpoint)
elif franz_num == '3':
  esc_setpoint = (( esc1_temp + esc2_temp + esc3_temp ) / 3 ) + 10
  config_esc_setpoint(pfc2_path, esc_setpoint)
  config_esc_setpoint(pfc3_path, esc_setpoint)
elif franz_num == '4':
  esc_setpoint = (( esc1_temp + esc2_temp + esc3_temp + esc4_temp ) / 4 ) + 10
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

ontime = 1 #30
sec = ontime*60

ts = utils.get_timestamp()
print '*** %s min burn-in started @ %s***' % (ontime, ts)

config_burnin(pfc1_path, sec)
if franz_num == '2':
  config_burnin(pfc2_path, sec)
elif franz_num == '3':
  config_burnin(pfc2_path, sec)
  config_burnin(pfc3_path, sec)
elif franz_num == '4':
  config_burnin(pfc2_path, sec)
  config_burnin(pfc3_path, sec)
  config_burnin(pfc4_path, sec)
else:
  if franz_num != '1':
    print 'Unknown Channel'

sec = sec + 20
sleep(sec)

ts = utils.get_timestamp()
print '*** Franz test completed @ %s***' % ts
utils.send_email('ACS Burn-In', 'ACS Burn-In is done!!')

#Clean up
ps1.all_output('off')
ps2.all_output('off')
