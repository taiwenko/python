#!/usr/bin/env python
import aeroflex
import altitude
import argparse
import math
import ppc4

from datetime import datetime
from time import sleep
from tools import shell

parser = argparse.ArgumentParser(description='Avionics Calibration Script')
parser.add_argument('majortom',
        help='Serial port connected to Major Tom')
parser.add_argument('ppc4',
        help='Serial port connected to the Fluke PPC4')
parser.add_argument('logfile',
        help='CSV file to append new measurements')
parser.add_argument('--min-altitude',
        metavar='flight-level', type=float, default=10.0,
        help='Lowest altitude to include in altitude sweep')
parser.add_argument('--max-altitude',
        metavar='flight-level', type=float, default=800.0,
        help='Highest altitude to include in altitude sweep')
parser.add_argument('--step-size',
        metavar='flight-levels', type=float, default=1.0,
        help='Size of each step when sweeping the altitude')
parser.add_argument('--settle',
        metavar='seconds', type=float, default=30.0,
        help='Delay to permit pressure to settle after changes')
parser.add_argument('--hold-limit',
        metavar='kPa', type=float, default=0.001,
        help='Required precision for the PPC4')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

print "Sweeping from FL%03.0f to FL%03.0f in steps of %.2f FL." \
    % (args.min_altitude, args.max_altitude, args.step_size)

print "Accessing PPC4"
ppc = ppc4.PPC4(args.ppc4)
ppc.verbose = args.verbose

print "Accessing Major Tom"
tom = shell.Shell(args.majortom)
sb = shell.Scoreboard(tom, None)
sbvars = []
sbvars.append('gxpr_bridge_barometric_pressure')
sbvars.append('gxpr_bridge_barometer_temperature')
sbvars.append('gxpr_bridge_temperature')
sbvars.append('gxpr_bridge_heater_on')

print "Preparing logfile"
logfile = open(args.logfile, 'at')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('"TIMESTAMP",')
    # Fluke Pre-Measurements
    logfile.write('"RDY","PRES","RATE","ATM","STATUS","UNCERT",')
    # Major Tom Variables
    logfile.write('"TIMESTAMP",')
    for var in sbvars:
        logfile.write('"%s",' % var)
    # Fluke Post-Measurements
    logfile.write('"TIMESTAMP",')
    logfile.write('"RDY","PRES","RATE","ATM","STATUS","UNCERT",')
    logfile.write('"TIMESTAMP"\n')
    logfile.flush()

print "Beginning tests"
steps = int(math.floor((args.max_altitude - args.min_altitude)
        / args.step_size))

while True:
    # Wait for the pressure to settle
    sleep(args.settle)
    # Take the measurements
    print "  Taking measurements"
    ts0 = datetime.now().isoformat()
    premeasure = ppc.status()
    ts1 = datetime.now().isoformat()
    sbmap = sb.query()
    ts2 = datetime.now().isoformat()
    postmeasure = ppc.status()
    ts3 = datetime.now().isoformat()
    # Commit to logfile
    logfile.write('%s,' % ts0)
    logfile.write('%d,%f,%f,%f,%d,%f,' % premeasure)
    logfile.write('%s,' % ts1)
    for var in sbvars:
        try:
            logfile.write('%s,' % sbmap[var][1])
        except KeyError:
            logfile.write('UNK,')
    logfile.write('%s,' % ts2)
    logfile.write('%d,%f,%f,%f,%d,%f,' % postmeasure)
    logfile.write('%s\n' % ts3)
    logfile.flush()
