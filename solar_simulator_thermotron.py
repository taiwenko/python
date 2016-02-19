#!/usr/bin/env python

from time import sleep
import bk8500
import math
import sys
import xpf6020
from blessings import Terminal

t = Terminal()

mppt_num = raw_input('How many MPPTs are you testing? [1 or 2]: ').strip()

print "Accessing the XPF6020 Power Supplies"

ps1_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5029ID1-if00-port0'
ps2_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5028CFJ-if00-port0'

batt_vin = 46
batt_iin = 2
solar_vin = 12
solar_iin = 5

if mppt_num == '1':
  ps1 = xpf6020.Xpf6020(ps1_path)
  ps1.reset_ps()
  ps1.set_voltage(1,batt_vin)
  ps1.set_currentlimit(1,batt_iin)
elif mppt_num == '2':
  ps1 = xpf6020.Xpf6020(ps1_path)
  ps1.reset_ps()
  ps1.set_voltage(1,batt_vin)
  ps1.set_currentlimit(1,batt_iin)
  ps1.set_voltage(2,solar_vin)
  ps1.set_currentlimit(2,solar_iin)
else:
  print 'Unknown MPPT amount. Can only test up to 2 MPPTs at a time.'
  sys.exit()

# Setup solar inputs for MPPT1
ps2 = xpf6020.Xpf6020(ps2_path)
ps2.reset_ps()
ps2.set_voltage(1,solar_vin)
ps2.set_currentlimit(1,solar_iin)
ps2.set_voltage(2,solar_vin)
ps2.set_currentlimit(2,solar_iin)

print "Accessing the BK8500 Electronic Load"

mppt_v = 49
mppt_v_max = 55

bkload = bk8500.Bk8500()
bkload.remote_switch('on')
bkload.config_cv_mode(mppt_v, mppt_v_max)

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

  print 'Input voltage should be within %f to %fV' %(voltage_min, voltage_max)
  print 'Input current should be within %f to %fA' %(current_min, current_max)
  print ''

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

  print 'MPPT Input%s @ %sV, %sA....[%s]' %(ch, r_mppt_v, r_mppt_i, result)
  print ''

def bkload_measure_check(current, voltage, tolerance, max_cycle):

  cycle = 0
  avg_volt = 0
  avg_current = 0
  print 'Averaging %d measurement...' % max_cycle

  while cycle != max_cycle:

    [r_mppt_v, r_mppt_i] = bkload.read()

    volt = r_mppt_v
    curr = r_mppt_i
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

  print 'Output voltage should be within %f to %fV' %(voltage_min, voltage_max)
  print 'Output current should be within %f to %fA' %(current_min, current_max)

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
  print 'MPPT Output %s @ %sV, %sA' % (result, r_mppt_v, r_mppt_i)


while True:

  print '*** MPPT test started ***'
  current_limit1 = 1.0
  current_limit2 = 1.5
  voltage_limit = 50.2
  tolerance_in = 0.50
  tolerance_out = 0.05
  max_cycle = 5

  # Enable Battery
  bkload.load_switch('on')
  sleep(1)
  ps1.all_output('on')
  sleep(5)

  # Enable Solar
  ps2.all_output('on')
  sleep(15)
  if mppt_num == '1':
    ps_measure_check('1', solar_iin, solar_vin, tolerance_in, max_cycle)
    ps_measure_check('2', solar_iin, solar_vin, tolerance_in, max_cycle)
    bkload_measure_check(current_limit1, voltage_limit, tolerance_out, max_cycle)
  elif mppt_num == '2':
    ps_measure_check('1', solar_iin, solar_vin, tolerance_in, max_cycle)
    ps_measure_check('2', solar_iin, solar_vin, tolerance_in, max_cycle)
    ps_measure_check('3', solar_iin, solar_vin, tolerance_in, max_cycle)
    bkload_measure_check(current_limit2, voltage_limit, tolerance_out, max_cycle)
  else:
    print 'Unknown Channel'

  #Clean up
  ps1.all_output('off')
  ps2.all_output('off')
  bkload.load_switch('off')

  more = raw_input(' MPPT test completed.  Continue to next UUT? [y/N]: ')

  if more != 'y':
    if more != 'Y':
      break;

raw_input('\n\nPress Enter to close.')
