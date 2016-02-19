#!/usr/bin/env python
import sbs
import cp2112

i2c = cp2112.CP2112()
batt = sbs.Battery(i2c)

print "Manufacturer:", batt.manufacturer()
print "Device Name: ", batt.device_name()
print "Chemistry:   ", batt.chemistry()
print "Temperature: ", batt.temperature(), "C"
print "Voltage:     ", batt.voltage(), "V"
print "Aux Data:    ", batt.manufacturer_data()
