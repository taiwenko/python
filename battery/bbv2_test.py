#!/usr/bin/env python

# Copyright 2015 Google, Inc.
# Routines for the dual battery charging
# Author: TaiWen Ko
# Date: 2015-1-13

import xpf6020
import bk8500a
import bk8500b
from datetime import datetime
from time import sleep
import tools.utils as tools
from tools import shell
import twk_utils
import sys
utils = twk_utils.Twk_utils()

from blessings import Terminal
t = Terminal()

int_v = 44
int_i = 20

ext_v = 51
ext_i = 0

int_load_volt = 45
int_load_volt_max = 60

ext_load_curr = 1#0
ext_load_curr_max = 40

shortpause = 1
longpause = 5

i_normal = 5.0
i_overload = 5#22.0
tol = 0.25

ifmt = "%s, %s, %s\t\t\t\t"

print "Accessing the instruments"

# Make sure to use the correct cables
pwr_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'
pfc_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc-if01-port0'

pwr = xpf6020.Xpf6020(pwr_path)
pwr.reset_ps()

int_load = bk8500a.Bk8500()
ext_load = bk8500b.Bk8500()

tom = shell.Shell(pfc_path)
sb = shell.Scoreboard(tom,'battery')

def readChargeCurrents():
    [v_pwr, i_pwr] = pwr.measure('2')
    [v_load, i_load] = int_load.read()
    current_i_batt = str(sb.query('battery0_current'))
    i_batt = current_i_batt.split("'")[3]

    return (i_pwr, i_load, i_batt)

def readDischargeCurrents():
    [v_pwr, i_pwr] = pwr.measure('1')
    [v_load, i_load] = ext_load.read()
    current_i_batt = str(sb.query('battery0_current')) # need to be abs()
    i_batt = current_i_batt.split("'")[3]
    return (i_pwr, i_load, i_batt)

def instr_config():

  pwr.set_voltage(1, int_v)
  pwr.set_currentlimit(1, int_i)
  pwr.ind_output('1','on')

  pwr.set_voltage(2, ext_v)
  pwr.set_currentlimit(2, ext_i)
  pwr.ind_output('2','off')

  int_load.remote_switch('on')
  int_load.load_switch('off')
  int_load.config_cv_mode(int_load_volt, int_load_volt_max)

  ext_load.remote_switch('on')
  ext_load.load_switch('off')
  ext_load.config_cc_mode(ext_load_curr, ext_load_curr_max)

def testChargeAcceptance():
  print ""
  print "Charge acceptance test:"
  print ""
  pwr.set_currentlimit(2, i_normal)
  pwr.ind_output('2', 'on')

  sleep(longpause)

  (ip, il, ib) = readChargeCurrents()

  thr = i_normal - tol

  pwr.ind_output('2', 'off')

  print ifmt % (ip,il,ib),

  if (ip > thr) & (il > thr) & (ib > thr):
      print t.bold_green('PASS')
  else:
      print t.bold_red('FAIL')

def testChargeOverCurrent():
  print ""
  print "Charge overcurrent test:"
  print ""
  pwr.set_currentlimit(2, i_overload)
  pwr.ind_output('2', 'on')

  sleep(shortpause)

  (ip, il, ib) = readChargeCurrents()
  print ifmt % (ip,il,ib)

  sleep(longpause)

  (ip, il, ib) = readChargeCurrents()
  thr = 0 + tol

  pwr.ind_output('2', 'off')
  pwr.set_currentlimit(2, i_normal)

  print ifmt % (ip,il,ib),
  if (ip < thr) & (il < thr) & (ib < thr):
      print t.bold_green('PASS')
  else:
      print t.bold_red('FAIL')


def testLoadAcceptance():
  print ""
  print "Load acceptance test:"
  print ""
  ext_load.config_cc_mode(i_normal, ext_load_curr_max)
  ext_load.load_switch('on')
  sleep(longpause)

  (ip, il, ib) = readDischargeCurrents()
  thr = i_normal - tol
  ext_load.load_switch('off')

  print ifmt % (ip,il,ib),
  if (ip > thr) & (il > thr) & (ib > thr):
      print t.bold_green('PASS')
  else:
      print t.bold_red('FAIL')

def testLoadOverCurrent():
  print ""
  print "Load overcurrent test:"
  print ""
  ext_load.config_cc_mode(i_overload, ext_load_curr_max)
  ext_load.load_switch('on')

  sleep(shortpause)
  (ip, il, ib) = readDischargeCurrents()
  print ifmt % (ip,il,ib)

  sleep(longpause)
  (ip, il, ib) = readDischargeCurrents()
  thr = 0 + tol
  ext_load.load_switch('off')
  ext_load.config_cc_mode(i_normal, ext_load_curr_max)

  print ifmt % (ip,il,ib),
  if (ip < thr) & (il < thr) & (ib < thr):
      print t.bold_green('PASS')
  else:
      print t.bold_red('FAIL')
  sleep(longpause)


def instr_shutdown():

    pwr.ind_output('2','off')

    ext_load.load_switch('off')
    ext_load.remote_switch('off')

    int_load.load_switch('off')
    int_load.remote_switch('off')

    pwr.ind_output('1','off')

    tom.close()

# Here is the main thing
instr_config()
#flash BMU
testChargeAcceptance()
testChargeOverCurrent()
testLoadAcceptance()
testLoadOverCurrent()
testLoadAcceptance()
instr_shutdown()
