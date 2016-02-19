#!/usr/bin/env python
import altitude
import argparse
import math
import ppc4
import subprocess

from datetime import datetime, timedelta
from time import sleep
from tools import shell

parser = argparse.ArgumentParser(description='NPH-8 Calibration Script')
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
parser.add_argument('--count',
        metavar='num', type=int, default=1,
        help='Number of samples to take at each pressure point')
parser.add_argument('--capture-delay',
        metavar='seconds', type=float, default=2.0,
        help='Time to wait between consequetive samples')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

print "Sweeping from FL%03.0f to FL%03.0f in steps of %.2f FL." \
    % (args.min_altitude, args.max_altitude, args.step_size)

print "Accessing PPC4"
ppc = ppc4.PPC4('/dev/ttyUSB0')
ppc.verbose = args.verbose

print "Venting PPC4"
ppc.vent()
while not ppc.vented():
    pass

print "Configuring PPC4"
ppc.autorange(102, 'kPa')
ppc.mode(ppc4.DYNAMIC_CONTROL)
ppc.hold_limit(args.hold_limit)

print "Preparing logfile"
logfile = open(args.logfile, 'at')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    logfile.write('"TIMESTAMP",')
    # Fluke Pre-Measurements
    logfile.write('"RDY","PRES","RATE","ATM","STATUS","UNCERT",')
    # Measurement
    logfile.write('"CHANNEL","ADC","TEMP_OK",')
    # Second Timestamp
    logfile.write('"TIMESTAMP"\n')
    logfile.flush()

print "Beginning tests"
steps = int(math.floor((args.max_altitude - args.min_altitude)
        / args.step_size))
settle = timedelta(seconds=args.settle)

def run_test(fl):
    # Set the pressure
    meters = fl * 1E2 * altitude.meter_per_foot
    pres = altitude.altitude_to_pressure(meters) / 1E3
    print "Setting pressure to %.3f kPa (FL%03.0f)" % (pres, fl)
    ppc.pressure(pres)
    # Wait for the pressure to settle
    print "  Waiting for Pressure to Settle"
    waitstart = datetime.now()
    ready = False
    while not ready:
        now = datetime.now()
        if not pcc.is_ready():
            waitstart = now
        elif (now - waitstart) >= settle:
            ready = True
    # Take the measurements
    for sample in range(args.count):
        print "  Taking measurement %d of %d" % (sample+1, args.count)
        ts0 = datetime.now().isoformat()
        ppcout = ppc.status()
        adcout = subprocess.check_output(['./read']).strip()
        ts1 = datetime.now().isoformat()
        # Commit to logfile
        logfile.write('%s,' % ts0)
        logfile.write('%d,%f,%f,%f,%d,%f,' % ppcout)
        logfile.write('%s,' % adcout)
        logfile.write('%s\n' % ts1)
        logfile.flush()
        # Delay between samples
        sleep(args.capture_delay)

while True:
    for i in range(steps):
        run_test(args.min_altitude + i * args.step_size)
    for i in range(steps):
        run_test(args.max_altitude - i * args.step_size)
