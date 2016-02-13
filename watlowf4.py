##!/usr/bin/python

# Copyright 2014 Google, Inc.
# Routines for talking to the TestEquity 115 (Watlow F4) controller
# Author: Eric Schlaepfer (ejs@)
# Requires minimalmodbus library, available from:
# https://pypi.python.org/pypi/MinimalModbus/0.6

import minimalmodbus
import time

class WatlowF4(minimalmodbus.Instrument):
    """Instrument class for Watlow F4 temperature controller.
    Comms via Modbus RTU (RS232)

    Args:
        * portname(str): name of port
        * slaveaddress(int): slave address in range of 1 to 247
    """

    def __init__(self, portname, slaveaddress=1):
        minimalmodbus.Instrument.__init__(self, portname, slaveaddress)
        self.serial.baudrate = 9600

    def set_temp(self, temperature):
        """Sets temperature in C."""
        self.write_register(300, temperature, 1, signed=True)
        time.sleep(0.1) # Allow controller to catch up

    def get_temp(self):
        """Returns chamber temperature in C."""
        v = self.read_register(100, 1, signed=True)
        time.sleep(0.1) # Allow controller to catch up
        return v

    def conditioning_on(self, switch):
        """Turn on the chamber"""
        if switch == True:
	    self.write_register(2000,1)
            time.sleep(0.1) # Allow controller to catch up
            print 'Temperature chamber is on!'
        elif switch == False:
            self.write_register(2000,0)
            time.sleep(0.1) # Allow controller to catch up
            print 'Temperature chamber is off.'

    def ramp_up(self, temperature):
        """Ramp up to variale temp"""
        print 'Ramp up to ' + str(temperature) + 'C'
        self.set_temp(temperature)
        time.sleep(0.1) # Allow controller to catch up
        current_temp = self.get_temp()
        time.sleep(0.1) # Allow controller to catch up
        while current_temp != temperature:
	    current_temp = self.get_temp()

    def ramp_down(self, temperature):
        """Ramp down to variale temp"""
        print 'Ramp down to ' + str(temperature) + 'C'
        self.set_temp(temperature)
        time.sleep(0.1) # Allow controller to catch up
        current_temp = self.get_temp()
        time.sleep(0.1) # Allow controller to catch up
        while current_temp != temperature:
	    current_temp = self.get_temp()

    def soak_time(self, soaktime):
        """Soak for a period of time"""
        time.sleep(0.1)
        time_now = time.strftime("%H:%M")
        print str(soaktime) + ' minute soak time starts @ ' + time_now 
        time_in_sec = soaktime * 60
        time.sleep(time_in_sec)
        print 'Finished soaking'
        

