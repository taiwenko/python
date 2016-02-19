#!/usr/bin/env python
import aeroflex
import altitude
import argparse
import math
import ppc4

from datetime import datetime
from time import sleep
from tools import shell

parser = argparse.ArgumentParser(description='Transponder Vacuum Soak Script')
parser.add_argument('majortom',
        help='Serial port connected to Major Tom')
parser.add_argument('aeroflex',
        help='Serial port connected to the Aeroflex IRF 6000')
parser.add_argument('logfile',
        help='CSV file to append new measurements')
parser.add_argument('-v', '--verbose',
        action='store_true',
        help='Tee serial communications to the console')
args = parser.parse_args()

print "Accessing the Aeroflex"
aero = aeroflex.Aeroflex(args.aeroflex)
aerovars = aeroflex.fields()

print "Accessing Major Tom"
tom = shell.Shell(args.majortom)
sb = shell.Scoreboard(tom, None)
sbvars = []
sbvars.append('avionics_barometric_pressure')
sbvars.append('avionics_barometric_pressure_filtered')
sbvars.append('avionics_barometric_pressure_variance')
sbvars.append('avionics_barometer_temperature')
sbvars.append('avionics_secondary_barometric_pressure')
sbvars.append('avionics_secondary_barometer_temperature')
sbvars.append('apex_temperature_barometer')
sbvars.append('apex_barometric_pressure')
sbvars.append('apex_barometric_pressure_filtered')
sbvars.append('apex_barometric_pressure_variance')
sbvars.append('gxpr_bridge_barometric_pressure')
sbvars.append('gxpr_bridge_barometer_temperature')
sbvars.append('gxpr_1_2_rail_voltage')
sbvars.append('gxpr_3_3_rail_voltage')
sbvars.append('gxpr_6_0_rail_voltage')
sbvars.append('gxpr_28_rail_voltage')
sbvars.append('gxpr_vin_rail_voltage')
sbvars.append('gxpr_tx_temperature')
sbvars.append('gxpr_mode_a_interrogation_count')
sbvars.append('gxpr_mode_a_transmission_count')
sbvars.append('gxpr_mode_c_interrogation_count')
sbvars.append('gxpr_mode_c_transmission_count')
sbvars.append('transponder_voltage')
sbvars.append('transponder_current')
sbvars.append('transponder_power')
sbvars.append('transponder_pressure_altitude')
sbvars.append('hs_temperature_supercaps')
sbvars.append('hs_temperature_iridium')
sbvars.append('hs_temperature_top_edge')
sbvars.append('hs_temperature_mcu')

print "Preparing logfile"
logfile = open(args.logfile, 'at')
try:
    if logfile.tell() == 0:
        raise IOError, 'Null Error'
except IOError:
    # Major Tom Variables
    logfile.write('"TIMESTAMP",')
    for var in sbvars:
        logfile.write('"%s",' % var)
    # Aeroflex Variables
    logfile.write('"TIMESTAMP",')
    for var in aerovars:
        logfile.write('"%s",' % var)
    logfile.write('"TIMESTAMP"\n')
    logfile.flush()

print "Beginning log"

while True:
    print "Starting measurement at %s" % datetime.now().isoformat()
    # Take the measurements
    ts0 = datetime.now().isoformat()
    sbmap = sb.query()
    ts1 = datetime.now().isoformat()
    aeromap = aero.measure()
    ts2 = datetime.now().isoformat()
    print "  Transponder tests: %s" % aeromap['overall']
    # Commit to logfile
    logfile.write('%s,' % ts0)
    for var in sbvars:
        try:
            logfile.write('%s,' % sbmap[var][1])
        except KeyError:
            logfile.write('UNK,')
    logfile.write('%s,' % ts1)
    for var in aerovars:
        try:
            logfile.write('%s,' % aeromap[var])
        except KeyError:
            logfile.write('UNK,')
    logfile.write('%s\n' % ts2)
    logfile.flush()
