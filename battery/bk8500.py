#!/usr/bin/python

# Copyright 2014 Google, Inc.
# Routines for talking to the B&K8500 Electronic Load
# Author: TaiWen Ko
# Requires serial library

import serial
from decimal import *
length_packet = 26 # Number of bytes in a packet
port_path = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0'
baudrate = 4800

class Bk8500(object):

	def _write(self, cmd):
		self.serial.write(cmd)
		self.DumpCommand(cmd)

	def DumpCommand(self, bytes):
	    assert(len(bytes) == length_packet)
	    header = " "*3
	    array = ''
	    #print header,
	    for i in xrange(length_packet):
			#if i % 10 == 0 and i != 0:
			#    print
			#    print header,
			#if i % 5 == 0:
			#    print " ",
			s = "%02x" % ord(bytes[i])
			if s == "00":
			    s = chr(250)*2
			#print s,
			array += s
	    #print
	    return array

	def CalculateChecksum(self, cmd):
	    assert((len(cmd) == length_packet - 1) or (len(cmd) == length_packet))
	    checksum = 0
	    for i in xrange(length_packet - 1):
		checksum += ord(cmd[i])
	    checksum %= 256
	    return checksum

	# Enable remote control
	def remote(self, switch):
	    cmd = chr(0xAA) + chr(0x00) + chr(0x20)
	    if switch == 'off':
	    	cmd += chr(0x00) + chr(0x00)*(length_packet - 1 - 4)
	    elif switch == 'on':
	    	cmd += chr(0x01) + chr(0x00)*(length_packet - 1 - 4)
	    cmd += chr(self.CalculateChecksum(cmd))
	    assert(len(cmd) == length_packet)
	    return cmd

	# Set mode
	def mode(self, num):
	    cmd = chr(0xAA) + chr(0x00) + chr(0x28)
	    if num == 'CC':
	    	cmd += chr(0x00) + chr(0x00)*(length_packet - 1 - 4)
	    elif num == 'CV':
	    	cmd += chr(0x01) + chr(0x00)*(length_packet - 1 - 4)
	    elif num == 'CW':
	    	cmd += chr(0x02) + chr(0x00)*(length_packet - 1 - 4)
	    elif num == 'CR':
	    	cmd += chr(0x03) + chr(0x00)*(length_packet - 1 - 4)
	    cmd += chr(self.CalculateChecksum(cmd))
	    assert(len(cmd) == length_packet)
	    return cmd

	# Enable input terminal
	def input(self, switch):
	    cmd = chr(0xAA) + chr(0x00) + chr(0x21)
	    if switch == 'off':
	    	cmd += chr(0x00) + chr(0x00)*(length_packet - 1 - 4)
	    	print 'BK8500 Electronic Load is off.'
	    elif switch == 'on':
	    	cmd += chr(0x01) + chr(0x00)*(length_packet - 1 - 4)
	    	print 'BK8500 Electronic Load is on!'
	    cmd += chr(self.CalculateChecksum(cmd))
	    assert(len(cmd) == length_packet)
	    return cmd

	# Set CC mode current
	def set_cc_current(self, value):
	    value = float(value) * int(10000)
	    hexstr = hex(int(value))
	    hexstr1 = '0x%s%s' %(hexstr[4],hexstr[5])
	    hexstr2 = '0x%s%s' %(hexstr[2],hexstr[3])
	    hex1 = int(hexstr1, 16)
	    hex2 = int(hexstr2, 16)
	    cmd = chr(0xAA) + chr(0x00) + chr(0x2A)
	    cmd += chr(hex1) + chr(hex2) + chr(0x00) + chr(0x00) + chr(0x00)*(length_packet - 1 - 7)
	    cmd += chr(self.CalculateChecksum(cmd))
	    assert(len(cmd) == length_packet)
	    return cmd

	# Set CV mode voltage
	def set_cv_voltage(self, value):
	    value = float(value) * int(1000)
	    hexstr = hex(int(value))
	    hexstr1 = '0x%s%s' %(hexstr[4],hexstr[5])
	    hexstr2 = '0x%s%s' %(hexstr[2],hexstr[3])
	    hex1 = int(hexstr1, 16)
	    hex2 = int(hexstr2, 16)
	    cmd = chr(0xAA) + chr(0x00) + chr(0x2C)
	    cmd += chr(hex1) + chr(hex2) + chr(0x00) + chr(0x00) + chr(0x00)*(length_packet - 1 - 7)
	    cmd += chr(self.CalculateChecksum(cmd))
	    assert(len(cmd) == length_packet)
	    return cmd

	# Set max current
	def set_max_current(self, value):
	    value = float(value) * int(10000) # 0.1mA res
	    hexstr = hex(int(value))
	    hexstr1 = '0x%s%s' %(hexstr[4],hexstr[5])
	    hexstr2 = '0x%s%s' %(hexstr[2],hexstr[3])
	    hex1 = int(hexstr1, 16)
	    hex2 = int(hexstr2, 16)
	    cmd = chr(0xAA) + chr(0x00) + chr(0x24)
	    cmd += chr(hex1) + chr(hex2) + chr(0x00) + chr(0x00) + chr(0x00)*(length_packet - 1 - 7)
	    cmd += chr(self.CalculateChecksum(cmd))
	    assert(len(cmd) == length_packet)
	    return cmd

	# Set max voltage
	def set_max_voltage(self, value):
	    value = float(value) * int(1000) # 1mV res
	    hexstr = hex(int(value))
	    hexstr1 = '0x%s%s' %(hexstr[4],hexstr[5])
	    hexstr2 = '0x%s%s' %(hexstr[2],hexstr[3])
	    hex1 = int(hexstr1, 16)
	    hex2 = int(hexstr2, 16)
	    cmd = chr(0xAA) + chr(0x00) + chr(0x22)
	    cmd += chr(hex1) + chr(hex2) + chr(0x00) + chr(0x00) + chr(0x00)*(length_packet - 1 - 7)
	    cmd += chr(self.CalculateChecksum(cmd))
	    assert(len(cmd) == length_packet)
	    return cmd

	# Read display values
	def read_display(self):
		cmd = chr(0xAA) + chr(0x00) + chr(0x5F)
		cmd += chr(0x00) + chr(0x00)*(length_packet - 1 - 4)
		cmd += chr(self.CalculateChecksum(cmd))
		assert(len(cmd) == length_packet)
		return cmd


	def config_cc_mode(self, current, max_i):
		# Initiate
	    port = port_path
	    baud = baudrate
	    sp = serial.Serial(port, baud)

	    # Set current protection
	    cmd = self.set_max_current(max_i)
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)

	    # Change to CC mode
	    cmd = self.mode('CC')
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)

	    # Set CC mode current
	    cmd = self.set_cc_current(current)
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)

	def config_cv_mode(self, voltage, max_v):
		# Initiate
	    port = port_path
	    baud = baudrate
	    sp = serial.Serial(port, baud)

	    # Set current protection
	    cmd = self.set_max_voltage(max_v)
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)

	    # Change to CV mode
	    cmd = self.mode('CV')
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)

	    # Set CV mode current
	    cmd = self.set_cv_voltage(voltage)
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)

	def load_switch(self, switch):
	    # Initiate
	    port = port_path
	    baud = baudrate
	    sp = serial.Serial(port, baud)

	    # Turn the input terminal on/off
	    if switch == 'off':
	    	cmd = self.input('off')
	    elif switch == 'on':
	    	cmd = self.input('on')
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)

	def read(self):
		# Initiate
	    port = port_path
	    baud = baudrate
	    sp = serial.Serial(port, baud)

	    # Read display
	    cmd = self.read_display()
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)
	    s = self.DumpCommand(response)
	    v = '0x%s%s%s%s' %(s[8],s[9],s[6],s[7])
	    i = '0x%s%s%s%s' %(s[16],s[17],s[14],s[15])
	    try:
	    	voltage = Decimal(int(v, 16))/1000
	    except ValueError:
	    	print 'BK8500 cannot determine display value. Set value to 0'
	    	voltage = 0
	    try:
	    	current = Decimal(int(i, 16))/10000
	    except ValueError:
	        print 'BK8500 cannot determine display value. Set value to 0'
	    	current = 0
	    return [voltage,current]

	def remote_switch(self, switch):
		# Initiate
	    port = port_path
	    baud = baudrate
	    sp = serial.Serial(port, baud)

	    # Enable/Disable remote control
	    if switch == 'off':
	    	cmd = self.remote('off')
	    elif switch == 'on':
	    	cmd = self.remote('on')
	    sp.write(cmd)
	    response = sp.read(length_packet)
	    assert(len(response) == length_packet)

if __name__ == '__main__':

	print 'yes'
	bkload = Bk8500()
	bkload.remote_switch('on')


