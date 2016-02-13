#!/usr/bin/env python

# Copyright 2014 Google, Inc.
# Routines for talking to the Minicircuit USB8SPDT
# Author: TaiWen Ko
# Requires pyUSB, libusb library

import usb.core
import usb.util

class Inst:
    """Base class for instruments"""
    def __init__(self):
        self._name = ""
        self._address = ""
        self._connected = False

    def is_connected(self):
        """Checks if device has been connected to"""
        return self._connected
    def get_address(self):
        """Gets the address of the device"""
        return self._address
    def set_address(self, address):
        """Sets the address of the device"""
        self._address = address
    def get_name(self):
        """Gets the name of the device"""
        return self._name
    def set_name(self, name):
        """Sets the name of the device"""
        self._name = name

class InstUsb(Inst):
    """Generic USB instrument"""
    def __init__(self):
        Inst.__init__(self)
        self._vendor = 0
        self._product = 0
        self._serial = None
        self._dev = None
        self._was_kernel_driver = False

    def __del__(self):
        if self._connected == True:
            self.disconnect()

    def set_address(self, address):
        """Sets address of the instrument"""
        if self._connected == False:
            Inst.set_address(self, address)
            self._vendor = int(address.split(':')[0], 16)
            self._product = int(address.split(':')[1], 16)

    def _cust_match(self, dev):
        """Custom matching function that checks USB serial number"""
        if (dev.idVendor == self._vendor) and (dev.idProduct == self._product):
            if (self._serial != None):
                serial = usb.util.get_string(dev, 63, dev.iSerialNumber)
                if serial == self._serial:
                    return True
                return False
            else:
                return True

    def connect(self):
        """Connects to USB instrument"""
        if self._connected == False:
            self._dev = usb.core.find(custom_match = self._cust_match)
            if self._dev == None:
                raise IOError("Device not found")
            if (self._dev.is_kernel_driver_active(0) == True):
                self._dev.detach_kernel_driver(0)
                self._was_kernel_driver = True
            else:
                self._was_kernel_driver = False
            self._dev.set_configuration()
            self._connected = True

    def disconnect(self):
        """Disconnects from USB instrument"""
        if self._connected == True:
            self._dev.reset()
            usb.util.dispose_resources(self._dev)
            #if self._was_kernel_driver == True:
            #    self._d.attach_kernel_driver(0)
            self._connected = False

 	
class Usb8spdt(InstUsb):

	def __init__(self):
		InstUsb.__init__(self)
		self._vendor = 0x20ce
		self._product = 0x0022

	def set_address(self, address):
		"""Sets the serial number of the device"""
        if self._connected == False:
            self._address = address
            self._serial = address

	def _write(self, data):
		if self._connected == True:
			return self._dev.ctrl_transfer(bmRequestType=0x21,bRequest=0x09,wValue=0x0200,wIndex=0,data_or_wLength=data,timeout=100)

	def _read(self, length):
		"""Reads raw data from the device"""
		if self._connected == False:
			return None
        response = ''
        try:
            data = self._dev.read(0x82, length, 0, 100)
        except usb.core.USBError:
        	return None
        else:
        	response = list(data)
        	return response

	def _send_cmd(self, cmd, data):
		"""Sends a raw command to the device"""
        length = len(data)
        packet = ''.join([chr(cmd) + chr(length)] +
                         [chr(char) for char in data])
        self._write(packet)

	def _send2(self, data):
		"""Sends data to the device"""
        packet = ''.join([chr(character) for character in data])
        self._write(packet)

	def _get_resp(self):
		"""Gets the raw response from the device"""
        response = self._read(8)
        if response == None:
            return None
        status = response[0]
        length = response[1]
        data = response[2:2 + length]
        return [status, data]

	def init(self):
		"""Sends the initialization sequence"""
        self._send2([0x1F, 0, 0, 0, 0, 0, 0, 0])
        self._send2([0x4A, 0, 0, 0, 0, 0, 0, 0])
        self._send2([0x49, 0, 0, 0, 0, 0, 0, 0])
        self._send2([0x4B, 0, 0, 0, 0, 0, 0, 0])
        self._send2([0x58, 0, 0, 0, 0, 0, 0, 0])
        self._send2([0x55, 0, 0, 0, 0, 0, 0, 0])
        self._send2([0x55, 0, 1, 0, 0, 0, 0, 0])
        self._send2([0x55, 0, 2, 0, 0, 0, 0, 0])
        self._send2([0x55, 0, 3, 0, 0, 0, 0, 0])

	def set_internal(self):
		"""Ignores the external switch input"""
        self._send2([0xD8, 1, 0, 0, 0, 0, 0, 0])

	def _switch(self, ch, state):
		# write the data
      	 self.send2([ch, state, 0, 0, 0, 0, 0, 0, 0, 0, 
      	 	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
      	 	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
      	 	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
      	 	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
      	 	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
      	 	0, 0, 0, 0, 0, 0, 0, 0, 0, 0])



	