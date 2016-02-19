#!/usr/bin/env python
import argparse
import math
import twk_utils

from datetime import datetime
from time import sleep
from tools import shell

pfc_path = '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc-if01-port0'

utils = twk_utils.Twk_utils()

print "Accessing Major Tom"

tom = shell.Shell(pfc_path)
sb = shell.Scoreboard(tom, None)
sbvars = []
sbvars.append('gopro_target_video_on')
sbvars.append('gopro0_video_on')
sbvars.append('gopro0_voltage_camera_5v')
sbvars.append('gopro0_current_camera_5v')
sbvars.append('version_hash_gopro0')
sbvars.append('gopro1_video_on')
sbvars.append('gopro1_voltage_camera_5v')
sbvars.append('gopro1_current_camera_5v')
sbvars.append('version_hash_gopro1')
sbvars.append('gopro2_video_on')
sbvars.append('gopro2_voltage_camera_5v')
sbvars.append('gopro2_current_camera_5v')
sbvars.append('version_hash_gopro2')
sbvars.append('gopro3_video_on')
sbvars.append('gopro3_voltage_camera_5v')
sbvars.append('gopro3_current_camera_5v')
sbvars.append('version_hash_gopro3')
sbvars.append('gopro4_video_on')
sbvars.append('gopro4_voltage_camera_5v')
sbvars.append('gopro4_current_camera_5v')
sbvars.append('version_hash_gopro4')
sbvars.append('gopro5_video_on')
sbvars.append('gopro5_voltage_camera_5v')
sbvars.append('gopro5_current_camera_5v')
sbvars.append('version_hash_gopro5')
sbvars.append('gopro6_video_on')
sbvars.append('gopro6_voltage_camera_5v')
sbvars.append('gopro6_current_camera_5v')
sbvars.append('version_hash_gopro6')
# sbvars.append('gopro7_video_on')
# sbvars.append('gopro7_voltage_camera_5v')
# sbvars.append('gopro7_current_camera_5v')
# sbvars.append('version_hash_gopro7')

print "Preparing logfile"
ts = datetime.now().isoformat()
logdir = '../gopro-vibetest-%s.csv' % ts
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP,')
    for var in sbvars:
        logfile.write('"%s",' % var)
    logfile.write('TIMESTAMP\n')
    logfile.flush()

def gopromeasure():
    print "  Taking GoPro measurements"
    ts0 = datetime.now().isoformat()
    sbmap = sb.query()
    ts1 = datetime.now().isoformat()
    # Commit to logfile
    logfile.write('%s,' % ts0)
    for var in sbvars:
        try:
            logfile.write('%s,' % sbmap[var][1])
        except KeyError:
            logfile.write('UNK,')
    logfile.write('%s\n' % ts1)
    logfile.flush()

ts = utils.get_timestamp()
print "***GoPro vibe test started @ %s***", % ts 
max_cycle = 10
monitor_freq = 5 # in sec
cycle = 0
data = ''

tom.sendline('power on apex')
sleep(5)
tom.sendline('gopro on')
sleep(10)

while cycle != int(max_cycle):

  cycle = cycle + 1

  gopromeasure()

  print 'Cycle %s completed.' % cycle
  ts = datetime.now().isoformat()
  sbmap = sb.query()
  for var in sbvars:
    try:
        print sbmap[var][1]
        data = data + sbmap[var][1] + '\n'
    except KeyError:
        data = data + 'UNK,'
  message = ts + '\n' + data
  utils.send_email('GoPro Vibe Test', message)

  sleep(monitor_freq)

ts = utils.get_timestamp()
print '***GoPro vibe test completed @ %s***', % ts
tom.sendline('gopro off')
sleep(5)
tom.sendline('power off apex')
sleep(5)
tom.close()
utils.send_email('GoPro Vibe Test', 'Test Completed!!')