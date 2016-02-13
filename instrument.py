##!/usr/bin/env python

"""
Classes for communicating with PC-connected instrumentation
"""
#import sys
#import socket
#import select
#import os
#import fcntl
#import time

#sys.path.append('./pyusb-1.0.0a3')
import usb.core
import usb.util 

#from array import *

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

IOC_NR = 91
IOCTL_INDICATOR_PULSE = (IOC_NR << 8) + 1
IOCTL_CLEAR = (IOC_NR << 8) + 2
IOCTL_ABORT_BULK_OUT = (IOC_NR << 8) + 3
IOCTL_ABORT_BULK_IN = (IOC_NR << 8) + 4
IOCTL_CLEAR_OUT_HALT = (IOC_NR << 8) + 6
IOCTL_CLEAR_IN_HALT = (IOC_NR << 8) + 7

class InstUsbTmc(Inst):
    """Class for USBTMC (Test and Measurement) devices"""
    def __init__(self):
        Inst.__init__(self)
        self._file = None

    def __del__(self):
        self.disconnect()

    def connect(self):
        """Connects to instrument"""
        if self._connected == False:
            self._file = open(self._address, 'r+')

            self._connected = True

    def disconnect(self):
        """Disconnects from instrument"""
        if self._connected == True:
            self._file.close()
            self._connected = False

    def send(self, data):
        """Sends data to instrument"""
        self._file.write(data + "\r\n")
        self._file.flush()

    def recv(self):
        """Receives data from instrument"""
        return self._file.readline().strip()

    def clear(self):
        """Clears input and output buffers"""
#        fcntl.ioctl(self._f.fileno(), IOCTL_CLEAR_IN_HALT)
#        fcntl.ioctl(self._f.fileno(), IOCTL_CLEAR_OUT_HALT)
        fcntl.ioctl(self._file, IOCTL_CLEAR)
    def abort_read(self):
        """Aborts pending read"""
        fcntl.ioctl(self._file.fileno(), IOCTL_ABORT_BULK_OUT)

class InstEth(Inst):
    """Ethernet-connected instrument"""
    def __init__(self):
        Inst.__init__(self)
        self._iport = ""
        self._iaddress = ""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __del__(self):
        if self._connected == True:
            self.disconnect()

    def set_address(self, address):
        """Sets address of instrument"""
        if self._connected == False:
            Inst.set_address(self, address)
            self._iaddress, self._iport = address.split(':')

    def connect(self):
        """Connects to instrument"""
        if self._connected == False:
            try:
                self._socket.connect((self._iaddress, int(self._iport)))
                self._connected = True
            except socket.error as e:
                raise IOError('Could not connect: %s' % e)
        self._poll = select.poll()
        self._poll.register(self._socket.fileno(), select.POLLIN)

    def disconnect(self):
        """Disconnects from instrument"""
        if self._connected == True:
            self._poll.unregister(self._socket.fileno())
            self._connected = False
            self._socket.close()

    def send(self, data):
        """Sends data to instrument"""
        if self._connected == True:
            self._socket.sendall(data) # no '\r\n'

    def recv(self, timeout=0):
        """Receives data from instrument"""
        self._socket.setblocking(0)
        dat = ''

        # Check for data, bail if no data
        p = self._poll.poll(timeout*1000)
        if len(p) < 1:
          self._socket.setblocking(1)
          return None

        start = time.time()
        if self._connected == True:
            while True:

                p = self._poll.poll(0)
                if len(p) > 0:
                    try:
                        d = self._socket.recv(4096)
                        if d:
                            dat += d
                            start = time.time()
                    except:
                        pass
                if time.time() - start > timeout:
                    break
                time.sleep(0.05)
            self._socket.setblocking(1)
            return dat
        else:
            self._socket.setblocking(1)
            return None

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
            

    def _ind_switch(self, ch, state):
        if self._connected == True:
            cfg = self._dev.get_active_configuration()
            intf = cfg[(0,0)]
            ep = usb.util.find_descriptor(
                intf,
                # match the first OUT endpoint
                custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
            assert ep is not None
            ep.write([ch, state, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0 ,0 ,0])


    def _all_switches(self, channels): 
        if self._connected == True:
            cfg = self._dev.get_active_configuration()
            intf = cfg[(0,0)]
            ep = usb.util.find_descriptor(
                intf,
                # match the first OUT endpoint
                custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
            assert ep is not None
            ep.write([9, channels, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 
                0, 0, 0, 0, 0, 0, 0, 0 ,0 ,0])

    def _outchannel(self, ch):
        if self._connected == True:
            if ch is 1:
                self._all_switches(0)
            if ch is 2:
                self._all_switches(1)
            if ch is 3:
                self._all_switches(8)
            if ch is 4:
                self._all_switches(10)
            if ch is 5:
                self._all_switches(64)
            if ch is 6:
                self._all_switches(80)
            if ch is 7:
                self._all_switches(192)
            if ch is 8:
                self._all_switches(224)
            if ch is 9:
                self._all_switches(228)


    def disconnect(self):
        """Disconnects from USB instrument"""
        if self._connected == True:
            self._dev.reset()
            usb.util.dispose_resources(self._dev)
            #if self._was_kernel_driver == True:
            #    self._d.attach_kernel_driver(0)
            self._connected = False

class InstLabBrick (InstUsb):
    """Lab brick attenuator"""
    def __init__(self):
        InstUsb.__init__(self)
        self._vendor = 0x041f
        self._product = 0x1208

    # Device address here refers to specific serial number
    def set_address(self, address):
        """Sets serial number of connected Lab Brick"""
        if self._connected == False:
            self._address = address
            self._serial = address

    def _write(self, data):
        """Writes raw data to the instrument"""
        if self._connected == True:
            # Use HID SET_REPORT
            return self._dev.ctrl_transfer(bmRequestType=0x21,
                                  bRequest=0x09,             # SET_REPORT
                                  wValue=0x0200,             # Report type,
                                                             # report id
                                  wIndex=0,                  # Interface
                                  data_or_wLength=data,
                                  timeout=100)

    def _read(self, length):
        """Reads raw data from the instrument"""
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
        """Sends a raw command to the instrument"""
        length = len(data)
        packet = ''.join([chr(cmd) + chr(length)] +
                         [chr(char) for char in data])
        self._write(packet)

    def _get_resp(self):
        """Gets a raw response from the instrument"""
        data = self._read(8)
        if data == None:
            return None
        status = data[0]
        length = data[1]
        data = data[2:2+length]
        return [status, data]

    def get_attenuation(self):
        """Gets the attenuation setting"""
        ret = 0
        for count in range(10):
            self._send_cmd(0x0D, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            ret = self._get_resp()
            if ret == None:
                return None
            if ret[0] == 0x0D:
                return float(ret[1][0]) * 0.25
        return None

    def set_attenuation(self, atten):
        """Sets the attenuation, in dB"""
        value = int(float(atten) / 0.25)
        if value > 255:
            value = 255
        if value < 0:
            value = 0
        self._send_cmd(0x8D, [value, 0x00, 0x00, 0x00])

class InstLabBrickSwitch (InstUsb):
    """Lab brick switch instrument"""
    def __init__(self):
        InstUsb.__init__(self)
        self._vendor = 0x20ce
        self._product = 0x0022

    # Device address here refers to specific serial number
    def set_address(self, address):
        """Sets the serial number of the device"""
        if self._connected == False:
            self._address = address
            self._serial = address

    def _write(self, data):
        """Writes raw data to the device"""
        if self._connected == True:
            # Use HID SET_REPORT
            return self._dev.ctrl_transfer(bmRequestType=0x21,
                                  bRequest=0x09,             # SET_REPORT
                                  wValue=0x0200,             # Report type,
                                                             # report id
                                  wIndex=0,                  # Interface
                                  data_or_wLength=data,
                                  timeout=100)

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

    #def set_switch(self, pos):
    #    """Sets the switch position"""
    #    value = int(pos)
    #    if value > 1:
    #        value = 1
    #    if value < 0:
    #        value = 0
     #   self._send2([0xD4, 0x1, value, 0, 0, 0, 0, 0])

class Console(InstUsb):
    """m3debug console connection"""
    def __init__(self):
        InstUsb.__init__(self)
        self._vendor = 0x18d1
        self._product = 0xdb04

    # Device address here refers to specific serial number
    def set_address(self, address):
        """Sets the serial number (optional)"""
        if self._connected == False:
            self._address = address
            self._serial = address

    # Writes to endpoint 2
    def write(self, data):
        """Writes data to UART"""
        pkt_len = 1
        data_len = len(data)
        offs = 0
        if self._connected == True:
            while(1):
                if data_len >= pkt_len:
                    self._dev.write(0x02, data[offs:offs + pkt_len], 1, 100)
                    data_len -= pkt_len
                    offs += pkt_len
                else:
                    self._dev.write(0x02, data[offs:data_len], 1, 100)
                    break

    # Reads from endpoint 2
    def read(self):
        """Reads data from UART"""
        if self._connected == True:
            result = ""
            while(1):
                try:
                    data = self._dev.read(0x82, 64, 1, 10) # Time out in 10ms
                    data = ''.join(map(chr, data))
                    result += data
                except usb.core.USBError:
                    break
            return result

    def get_result(self):
        """Gets the entire result (until there's nothing left) from the UART"""
        result = ""
        while(1):
            data = self.read()
            if data == "":
                break
            result += data
        return result

    def sync(self):
        """Syncs to the command prompt"""
        for i in range(500):
            self.write("\n")
            result = self.read()
            if result.find("] ") >= 0:
                return 0
            time.sleep(0.01)
        return -1

#if __name__ == '__main__':
    
    # Parameters
    #a = InstLabBrickSwitch()
    #a.connect()
    #a._switch(1,0)
    #a._switch(2,0)
    #a._switch(3,0)
    #a._switch(4,1)
    #a._switch(1,1)
    #a._switch(1,1)
