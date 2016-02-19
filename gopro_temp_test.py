#!/usr/bin/env python
import watlowf4
import xpf6020
import argparse
import math

from datetime import datetime
from time import sleep
from tools import shell

parser = argparse.ArgumentParser(description='GoPro Temp Test Script')
parser.add_argument('majortom',
        help='Serial port connected to Major Tom')
parser.add_argument('sorensen',
        help='Serial port connected to the Sorensen XPF 6020')
parser.add_argument('tchamber',
        help='Serial port connected to the Temperature Chamber')
parser.add_argument('cycle',
        help='Number of temperature cycle')
parser.add_argument('logfile',
        help='CSV file to append new measurements')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

print "Accessing the Power Supply"
sore = xpf6020.Xpf6020(args.sorensen)
sore.reset_ps()
sore.set_voltage(1,40)
sore.set_currentlimit(1,2)
sleep(1)
sore.all_output('on')
sleep(3)

print "Accessing the Temperature Chamber"
chamber = watlowf4.WatlowF4(args.tchamber)

print "Accessing Major Tom"
tom = shell.Shell(args.majortom)
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
sbvars.append('gopro7_video_on')
sbvars.append('gopro7_voltage_camera_5v')
sbvars.append('gopro7_current_camera_5v')
sbvars.append('version_hash_gopro7')

print "Preparing logfile"
logdir = '%s-gopro_temptest.csv' % (args.logfile)
logfile = open(logdir, 'wt')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('TIMESTAMP,')
    logfile.write('TEMPERATURE,')
    for var in sbvars:
        logfile.write('"%s",' % var)
    logfile.write('TIMESTAMP\n')
    logfile.flush()

def gopromeasure():
    print "  Taking GoPro measurements"
    ts0 = datetime.now().isoformat()
    temp = chamber.get_temp()
    sbmap = sb.query()
    ts1 = datetime.now().isoformat()
    # Commit to logfile
    logfile.write('%s,' % ts0)
    logfile.write('%s,' % temp)
    for var in sbvars:
        try:
            logfile.write('%s,' % sbmap[var][1])
        except KeyError:
            logfile.write('UNK,')
    logfile.write('%s\n' % ts1)
    logfile.flush()

# Temperature Profile
cold_start = -50
ambient_temp = 20
hot_temp =  50
soaktime = 10

tom.sendline('power on apex')
sleep(5)

print "GoPro temperature test started"
max_cycle = args.cycle
cycle = 0
max_ontime = 50
ontime = 0

chamber.conditioning_on(True)

# Burn off excessive moisture
chamber.ramp_up(hot_temp) 
chamber.soak_time(soaktime) 

while cycle != int(max_cycle):

  cycle = cycle + 1

  chamber.ramp_down(cold_start)
  chamber.soak_time(soaktime)
  tom.sendline('gopro on')

  while ontime != int(max_ontime):

    ontime = ontime + 1

    gopromeasure()
    sleep(1)

  ontime = 0

  chamber.ramp_up(ambient_temp)
  chamber.soak_time(soaktime)

  while ontime != int(max_ontime):

    ontime = ontime + 1

    gopromeasure()
    sleep(1)

  ontime = 0

  chamber.ramp_up(hot_temp)
  chamber.soak_time(soaktime)

  while ontime != int(max_ontime):

    ontime = ontime + 1

    gopromeasure()
    sleep(1)

  ontime = 0

  print 'Cycle %s completed.' % cycle

#clean up
chamber.ramp_down(ambient_temp)
chamber.soak_time(soaktime)
chamber.conditioning_on(False)
sore.all_output('off')
print 'GoPro temperature test completed.'
