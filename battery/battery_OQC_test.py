#!/usr/bin/env python
from time import sleep
from struct import unpack
import sys
import serial
import time
import smbus
import sbs
import numpy as np
import dcload

def test(condition):
    if condition:
        return "PASS"
    else:
        return "FAIL"

tb = "\t\t"

bus = smbus.Bus()
dev = sbs.BQ78350(bus, 0x16 / 2)

# BK 8514 load comes up as COM5
load8514 = dcload.DCLoad()
load8514.Initialize(5, 38400) # COMx, Baud Rate
load8514.SetRemoteControl()
load8514.TurnLoadOff()
load8514.SetMaxCurrent(40.0)
load8514.SetMaxVoltage(60.0)
load8514.SetMaxPower(500.0)
load8514.SetMode('CC')
load8514.SetCCCurrent(0.0)

# BK XLN6024 comes up as COM4, and we have to subtract one (zero-based index)
xln6024 = serial.Serial(4 - 1, 57600, timeout = 1)
xln6024.write("OUT OFF\r\n")
xln6024.write("VOLT 51.0\r\n")
xln6024.write("CURR 0.0\r\n")

# Get some data from the battery pack
cv = [dev.CellVoltage(cell) for cell in range(0,12)]
da2 = dev.DAStatus2()
ct = np.asarray(da2[2:5]) / 10 - 272.15 # convert temperature to C from deci-K

print "######################################################################"
print "###############       GOOGLE BATTERY TEST SCRIPT       ###############"
print "######################################################################"

print "Hardware Device Type:"
print "%s %s %s" % (tb, hex(dev.DeviceType()), tb), test(dev.DeviceType() == 0x1e9b)
print "Programmed Chem ID:"
print "%s %s %s" % (tb, hex(dev.ChemicalID()), tb), test(dev.ChemicalID() == 0x2009)
print "Min / Max cell voltage:"
print "%s %1.3f V %s" % (tb, min(cv), tb), test(min(cv) >= 3.60)
print "%s %1.3f V %s" % (tb, max(cv), tb), test(max(cv) <= 3.70)
print "Min / Max cell temperature:"
print "%s %2.1f C %s" % (tb, min(ct), tb), test(min(ct) >= 10.0)
print "%s %2.1f C %s" % (tb, max(ct), tb), test(max(ct) <= 40.0)
print "Total pack voltage:"
print "%s %2.1f V %s" % (tb, dev.Voltage(), tb), test((dev.Voltage() >= 43.0) and (dev.Voltage() <= 45.0))
print "Full charge capacity:"
print "%s %2.1f Ah %s" % (tb, dev.FullChargeCapacity(), tb), test(dev.FullChargeCapacity >= 17.0)
print "Measured pack current:"
print "%s %+2.1f A %s" % (tb, dev.Current(), tb), test(dev.Current() <= 0.1)

print "Applying a 10A load current"
load8514.SetCCCurrent(10.0)
load8514.TurnLoadOn()
time.sleep(2)

print "Measured pack current:"
print "%s %+2.1f A %s" % (tb, dev.Current(), tb), test((dev.Current() <= -9.8) and (dev.Current() >= -10.2))
load8514.SetCCCurrent(0.0)
load8514.TurnLoadOff()
load8514.SetLocalControl()

print "Applying a 10A charge current "
xln6024.write("OUT ON\r\n")
xln6024.write("CURR 10.0\r\n")
time.sleep(2)

print "Measured pack current:"
print "%s %+2.1f A %s" % (tb, dev.Current(), tb), test((dev.Current() >= 9.8) and (dev.Current() <= 10.2))
xln6024.write("OUT OFF\r\n")

bus.close()



print "Test Complete - Press Enter to Close"
raw_input()


