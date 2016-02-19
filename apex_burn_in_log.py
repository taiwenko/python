#!/usr/bin/env python

from time import sleep
import twk_utils
import math
import sys
import tools.utils as tools
from tools import shell
from blessings import Terminal
from datetime import datetime
import argparse

t = Terminal()

utils = twk_utils.Twk_utils()

pfc_path = '/dev/serial/by-id/usb-loon_onboard_motherbrain_pfc-if01-port0'

parser = argparse.ArgumentParser(description=' Test Script')
parser.add_argument('cycle',
        help='Number of cycle')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

def apex_power(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('power on apex')
  sleep(3)
  tom.close()
  sleep(3)

def apex_arm(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('squib @apex hard soft aux arm -f')
  sleep(3)
  tom.close()
  sleep(3)

def apex_fire(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('squib @apex hard soft aux request fire')
  sleep(3)
  tom.close()
  sleep(3)

def apex_unfire(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('squib @apex hard soft aux request unfire')
  sleep(3)
  tom.close()
  sleep(3)

def apex_disarm(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('squib @apex hard soft aux disarm')
  sleep(3)
  tom.close()
  sleep(3)

def apex_stfu(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  tom.sendline('beeper stfu')
  sleep(3)
  tom.close()
  sleep(3)

def squib_status(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  sb = shell.Scoreboard(tom,'apex')
  sleep(3)
  hard = str(sb.query('apex_hard_squib_state'))
  soft = str(sb.query('apex_soft_squib_state'))
  aux = str(sb.query('apex_aux_squib_state'))
  print hard
  print soft
  print aux
  hard = (hard.split("'")[3])
  soft = (soft.split("'")[3])
  aux = (aux.split("'")[3])
  tom.close()
  sleep(3)
  return (hard,soft,aux)

def query_sb(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  sb = shell.Scoreboard(tom,'apex')
  sleep(3)
  msg = str(sb.query('apex'))
  tom.close()
  return msg

def query_specific(pfc_path):
  tom = shell.Shell(pfc_path)
  sleep(3)
  sb = shell.Scoreboard(tom,'apex')
  sleep(3)
  sbmap = sb.query()
  tom.close()
  return sbmap

# Test starts here
tom = shell.Shell(pfc_path)
sb = shell.Scoreboard(tom, None)
sbvars = []
sbvars.append('apex_vin_voltage')
sbvars.append('apex_vin_current')
sbvars.append('apex_reg_5v_voltage')
sbvars.append('apex_buf_5v_voltage')
sbvars.append('apex_ups_in_voltage')
sbvars.append('apex_reg_5v_current')
sbvars.append('apex_buf_5v_current')
sbvars.append('apex_reg_3v3_voltage_direct')
sbvars.append('apex_barometric_pressure_filtered')
sbvars.append('lift_gas_temperature0')
sbvars.append('apex_temperature_top_0')
sbvars.append('apex_temperature_top_1')
sbvars.append('apex_temperature_barometer')
sbvars.append('apex_temperature_dps')
sbvars.append('apex_hard_squib_state')
sbvars.append('apex_soft_squib_state')
sbvars.append('apex_aux_squib_state')
tom.close()

# print "Preparing logfile"
ts = utils.get_timestamp()
logdir = '../apex-burnin-%s.csv' % ts
logfile = open(logdir, 'w')
try:
  if logfile.tell() == 0:
    raise IOError, 'Null Error'
except IOError:
  logfile.write('TIMESTAMP,')
  for var in sbvars:
    logfile.write('"%s",' % var)
    logfile.flush()
  logfile.write('\n')

ts = utils.get_timestamp()
msg = '*** APEX6 H2 Test Started @ %s***' % ts
print msg
msg = msg + '\n'

cur_cycle = 0;

while cur_cycle != int(args.cycle):
  apex_power(pfc_path)
  sleep(10)
  apex_arm(pfc_path)
  sleep(10)
  apex_fire(pfc_path)
  sleep(10)
  apex_unfire(pfc_path)
  sleep(10)
  apex_disarm(pfc_path)
  sleep(10)
  sbmap = query_specific(pfc_path)
  ts = datetime.now().isoformat()
  logfile.write(ts)
  for var in sbvars:
    try:
      logfile.write(',%e' % sbmap[var][1])
    except TypeError:
      logfile.write(',%s' % sbmap[var][1])
  logfile.write('\n')
  cur_cycle = cur_cycle + 1

ts = utils.get_timestamp()
msg1 = '*** APEX6 H2 Test completed @ %s***' % ts
print msg1
msg = msg + msg1 + '\n' + '\n' + '\n' + '\n'

sb = query_sb(pfc_path)
msg = msg + str(sb)

utils.send_email('APEX6 H2 Test Result', msg)

