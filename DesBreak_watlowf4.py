##!/usr/bin/python

# Copyright 2014 Google, Inc.
# Routines for talking to the TestEquity 115 (Watlow F4) controller
# Author: Eric Schlaepfer (ejs@)
# Requires minimalmodbus library, available from:
# https://pypi.python.org/pypi/MinimalModbus/0.6

import minimalmodbus
from time import sleep
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
        sleep(0.1) # Allow controller to catch up

    def get_temp(self):
        """Returns chamber temperature in C."""
        v = self.read_register(100, 1, signed=True)
        sleep(0.1) # Allow controller to catch up
        return v

    def conditioning_on(self, switch):
        """Turn on the chamber"""
        if switch == True:
	    self.write_register(2000,1)
            sleep(0.1) # Allow controller to catch up
            print 'Temperature chamber is on!'
        elif switch == False:
            self.write_register(2000,0)
            sleep(0.1) # Allow controller to catch up
            print 'Temperature chamber is off.'

    def ramp_up(self, temperature):
        """Ramp up to variale temp"""
        print 'Ramp up to ' + str(temperature) + 'C'
        self.set_temp(temperature)
        sleep(0.1) # Allow controller to catch up
        current_temp = self.get_temp()
        sleep(0.1) # Allow controller to catch up
        while current_temp != temperature:
	    current_temp = self.get_temp()

    def ramp_down(self, temperature):
        """Ramp down to variale temp"""
        print 'Ramp down to ' + str(temperature) + 'C'
        self.set_temp(temperature)
        sleep(0.1) # Allow controller to catch up
        current_temp = self.get_temp()
        sleep(0.1) # Allow controller to catch up
        while current_temp != temperature:
	    current_temp = self.get_temp()

    def soak_time(self, soaktime):
        """Soak for a period of time"""
        sleep(0.1)
        time_now = time.strftime("%H:%M")
        print str(soaktime) + ' minute soak time starts @ ' + time_now
        time_in_sec = soaktime * 60
        sleep(time_in_sec)
        print 'Finished soaking'


if __name__ == '__main__':

    chamber = WatlowF4('/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A603R0MG-if00-port0')
    # Temperature Profile
    cold_start = -70
    cold_temp = -35
    ambient_temp = 0
    hot_temp = 20
    soaktime = 20

    print "Breakout temperature test started"

    max_cycle = 3
    cycle = 0

    chamber.conditioning_on(True)

    # Burn off excessive moisture
    chamber.ramp_up(hot_temp)
    chamber.soak_time(soaktime)

    while cycle != int(max_cycle):

      cycle = cycle + 1

      # 20 + 20 = 40min
      chamber.ramp_down(cold_start)
      chamber.soak_time(soaktime)

      # 20 + 10 = 30min
      chamber.ramp_up(cold_temp)
      chamber.soak_time(soaktime)

      # 20 + 10 = 30 min
      chamber.ramp_up(ambient_temp)
      chamber.soak_time(soaktime)
     
      # 20 + 10 = 30 min
      chamber.ramp_up(hot_temp)
      chamber.soak_time(soaktime)

      print 'Cycle %s completed.' % cycle

    #clean up
    chamber.ramp_down(ambient_temp)
    chamber.soak_time(soaktime)
    chamber.conditioning_on(False)
    print 'Breakout temperature test completed.'

