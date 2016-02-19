#!/usr/bin/env python
import argparse
import datetime
import ppc4
import sys
import time

parser = argparse.ArgumentParser(description='Vacuum Chamber Test Script')
parser.add_argument('port',
        help='Serial port connected to the PPC4')
parser.add_argument('logfile',
        help='CSV file to append new pressure measurements')
parser.add_argument('--low-pressure',
        metavar='kPa', type=float, default=10.0,
        help='Low pressure target')
parser.add_argument('--high-pressure',
        metavar='kPa', type=float, default=95.0,
        help='High pressure target')
parser.add_argument('--inc-time',
        metavar='seconds', type=float, default=30.0,
        help='Duration to keep the gate open when increasing chamber pressure')
parser.add_argument('--dec-time',
        metavar='seconds', type=float, default=30.0,
        help='Duration to keep the gate open when decreasing chamber pressure')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

print "Accessing PPC4"
dev = ppc4.PPC4(args.port)
dev.verbose = args.verbose

print "Venting PPC4"
dev.vent()
while not dev.vented():
    pass
while dev.pressure() < 100:
    pass

print "Configuring PPC4"
dev.autorange(110, 'kPa')
dev.mode(ppc4.STATIC_CONTROL)

print "Beginning tests"
logfile = open(args.logfile, 'at')
pressure = 100
increase = False

while True:
    if increase:
        dev.increase_fast(True)
        time.sleep(args.inc_time)
        dev.increase_fast(False)
    else:
        dev.decrease_fast(True)
        time.sleep(args.dec_time)
        dev.decrease_fast(False)
    # Wait for the gate to actually close
    while not dev.is_ready():
        pass
    # Take measurements over the next minute
    for j in range(60):
        time.sleep(1)
        (ready, pressure, rate, atm, status, uncert) = dev.status()
        timestamp = datetime.datetime.now().isoformat()
        logfile.write('%s,%d,%f,%f,%f,%d,%f\n'
            % (timestamp, ready, pressure, rate, atm, status, uncert))
    logfile.flush()
    # Check for boundary condition
    if pressure >= args.high_pressure:
        print "Decreasing towards %.3f kPa" % args.low_pressure
        increase = False
    elif pressure <= args.low_pressure:
        print "Increasing towards %.3f kPa" % args.high_pressure
        increase = True
