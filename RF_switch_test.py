#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for the gxpr_temp_test
# Author: TaiWen Ko

#TODO: add reading and printing
import instrument
import argparse

from datetime import datetime
from time import sleep

parser = argparse.ArgumentParser(description='Transponder Temperature Test Script')
parser.add_argument('channel',
        help='Switch to which channel')
args = parser.parse_args()

print "Accessing the RF Switch"
mini = instrument.InstLabBrickSwitch()
mini.connect()

mini._outchannel(int(args.channel))
sleep(1)  #wait for switch to settle
