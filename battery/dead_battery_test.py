#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the battery_baseline_temp_test
# Author: TaiWen Ko
# Date: 2015-02-03
from time import sleep
import sys

import tools.utils as tools
from tools import shell

pfc_path = '/dev/serial/by-id/usb-FTDI_Dual_RS232-HS-if01-port0'

print "Accessing the Payload"
tom = shell.Shell(pfc_path)
sb = shell.Scoreboard(tom,'battery')

def shutdown():
  print 'Received shutdown signal.  Shutting off.'
  sys.exit(0)

def safe_blocking_query(field):
  value = None
  num_tries = 1
  max_tries = 2
  while value is None and num_tries <= max_tries:
    try:
      value = str(sb.query(field))
    except:
      sleep(10)
      num_tries += 1
  
  if num_tries > max_tries:
    print 'Querying field %s failed after %d tries.' % (field, max_tries)
    shutdown()
  return value

while True:
    
    soc = str(safe_blocking_query('envelope_power'))
    current_soc = soc.split("'")[3]
    print 'envelope_power is %s' % (current_soc)
    sleep(5)