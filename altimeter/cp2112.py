"""CP2112->SMBus Driver"""
from struct import pack, unpack
import usb

CP2112_VID = 0x10C4
CP2112_PID = 0xEA90

# HID related constants
HID_GET_REPORT = 0x01
HID_SET_REPORT = 0x09
HID_REPORT_TYPE_INPUT = 0x10
HID_REPORT_TYPE_OUTPUT = 0x20
HID_REPORT_TYPE_FEATURE = 0x30

# Destinations for USB read/write
CONTROL_REQUEST_TYPE_IN = usb.ENDPOINT_IN | usb.TYPE_CLASS \
        | usb.RECIP_INTERFACE
CONTROL_REQUEST_TYPE_OUT = usb.ENDPOINT_OUT | usb.TYPE_CLASS \
        | usb.RECIP_INTERFACE
INTERRUPT_REQUEST_IN = usb.ENDPOINT_IN | 0x01
INTERRUPT_REQUEST_OUT = usb.ENDPOINT_OUT | 0x01

# Maximum packet size of the CP2112
PACKET_SIZE = 64

# Report ID's for the CP2112
REPORTID_SMBCONF = 0x02
REPORTID_DATAREAD = 0x10
REPORTID_DATAWRITEREAD = 0x11
REPORTID_DATAREADFORCE = 0x12
REPORTID_DATARESPONSE = 0x13
REPORTID_DATAWRITE = 0x14
REPORTID_STATUSREQUEST = 0x15
REPORTID_STATUSRESPONSE = 0x16
REPORTID_CANCEL = 0x17

class I2CError(IOError):
    pass

class TimeoutError(I2CError):
    pass

class CP2112(object):
    def __init__(self, dev = None):
        # Defaults
        self.wrtimeout = 100;
        self.rdtimeout = 100;
        self.retries = 10;
        self.clock = 100000;
        self.usbtimeout = 1000;
        # Associate with device
        if dev:
            self.dev = dev
        else:
            # Search for the first CP2112
            # TODO: Skip if we can't associate?
            for bus in usb.busses():
                for dev in bus.devices:
                    if dev.idProduct == CP2112_PID \
                            and dev.idVendor == CP2112_VID:
                        self.dev = dev.open()
                        break
                else:
                    continue
                break
            else:
                raise I2CError, "Could not locate CP2112"
        # Prepare it for access
        try:
            self.dev.detachKernelDriver(0)
        except:
            # detachKernelDriver will fail if there is currently no driver
            # attached.  We really don't care in that case.  Any other error
            # will be discovered later.
            pass
        self.dev.claimInterface(0)
        # Empty any buffers
        try:
            while True:
                self.dev.interruptRead(
                        endpoint=INTERRUPT_REQUEST_IN,
                        size=PACKET_SIZE,
                        timeout=self.usbtimeout)
        except:
            pass
        self._writeconfig()

    def _setfeature(self, reportid, payload):
        """Sends a SET_REPORT for to the CP2112"""
        return self.dev.controlMsg(
                requestType=CONTROL_REQUEST_TYPE_OUT,
                request=HID_SET_REPORT,
                value=reportid | HID_REPORT_TYPE_FEATURE,
                index=0,
                buffer=payload,
                timeout=self.usbtimeout)

    def _writeconfig(self):
        """Rewrites the SMBus configuration to the CP2112"""
        # Build the configuration file
        pkt = pack('>LBbHHbH',
                self.clock,     # Clock Speed (Hz, 4 Bytes)
                2,              # Master Address (Byte)
                0,              # Disable Read Auto Send (Byte)
                self.wrtimeout, # Write Timeout (ms, 2 Bytes)
                self.rdtimeout, # Read Timeout (ms, 2 Bytes)
                1,              # Enable SCL Low Timeout (Byte)
                self.retries)   # Retry Limit (2 Bytes)
        self._setfeature(REPORTID_SMBCONF, pkt)

    def _datawait(self):
        """Wait for I/O completion"""
        request = pack('>BB',
            REPORTID_STATUSREQUEST, # Report Id (Byte)
            0x01)                   # SMBus Indicator
        while True:
            # Request bus status
            self.dev.interruptWrite(
                    endpoint=INTERRUPT_REQUEST_OUT,
                    buffer=request,
                    timeout=self.usbtimeout)
            # Wait for response
            response = self.dev.interruptRead(
                    endpoint=INTERRUPT_REQUEST_IN,
                    size=PACKET_SIZE,
                    timeout=self.usbtimeout)
            # Parse response
            if response[0] != REPORTID_STATUSRESPONSE:
                raise Exception, 'TODO: Protocol error'
            elif response[1] == 0x02:
                break
            elif response[1] == 0x03:
                raise Exception, 'I2C Error'
            elif response[1] != 0x01:
                raise Exception, 'TODO: Protocol error'
        # Done
        pass

    def _readwait(self, length):
        """Waits for completion of a read or writeread"""
        self._datawait()
        # Query the device status
        request = pack('>BH',
            REPORTID_DATAREADFORCE, # Report Id (Byte)
            61)
        buffer = ''
        while len(buffer) < length:
            # Request bus status
            self.dev.interruptWrite(
                    endpoint=INTERRUPT_REQUEST_OUT,
                    buffer=request,
                    timeout=self.usbtimeout)
            # Wait for response
            response = self.dev.interruptRead(
                    endpoint=INTERRUPT_REQUEST_IN,
                    size=PACKET_SIZE,
                    timeout=self.usbtimeout)
            # Parse response
            if response[0] != REPORTID_DATARESPONSE:
                raise Exception, 'TODO: Protocol error'
            buffer = buffer + response[3:3+ord(response[2])]
        return buffer

    def write(self, addr, data):
        """Executes an I2C write to a slave device"""
        if (len(data) < 1) or (len(data) > 61):
            raise ValueError, "write is limited to 61 bytes"
        # Send the write data
        pkt = pack('>BBB',
                REPORTID_DATAWRITE, # Report Id (Byte)
                addr & 0xF7,        # Slave Address (Byte)
                len(data)           # Data Length (Byte)
                ) + data            # User Data
        self.dev.interruptWrite(
                endpoint=INTERRUPT_REQUEST_OUT,
                buffer=pkt,
                timeout=self.usbtimeout)
        # Wait for I/O completion
        self._datawait()
        return len(data)

    def read(self, addr, count):
        """Executes an I2C read from a slave device"""
        if (count < 1) or (count > 512):
            raise ValueError, "read is limited to 512 bytes"
        pkt = pack('>BBH',
                REPORTID_DATAREAD, # Report Id (Byte)
                addr & 0xF7,       # Slave Address (Byte)
                count)             # Read Length (Word)
        self.dev.interruptWrite(INTERRUPT_REQUEST_OUT, pkt)
        # Wait for completion
        return self._readwait(count)

    def writeread(self, addr, data, count):
        """Executes an I2C write followed by a read to a slave device"""
        if (len(data) < 1) or (len(data) > 16):
            raise ValueError, "write size is limited to 16 bytes"
        if (count < 1) or (count > 512):
            raise ValueError, "read size is limited to 512 bytes"
        pkt = pack('>BBHB',
                REPORTID_DATAWRITEREAD, # Report Id (Byte)
                addr & 0xF7,            # Slave Address (Byte)
                count,                  # Read Length (Word)
                len(data)               # Write Length (Byte)
                ) + data                # User Data
        self.dev.interruptWrite(INTERRUPT_REQUEST_OUT, pkt)
        # Wait for completion
        return self._readwait(count)

    def read_byte(self, addr):
        """Reads a single byte without specifying a device register"""
        return unpack('<B', self.read(addr, 1))
    def write_byte(sef, addr, val):
        """Sends a single byte to the device"""
        return self.write(addr, pack('<B', val))
    def read_byte_data(self, addr, cmd):
        """Reads a single byte from a device register"""
        return unpack('<B', self.writeread(addr, pack('<B', cmd), 1))
    def write_byte_data(self, addr, cmd, val):
        """Writes a single byte to a device register"""
        return self.write(addr, pack('<BB', cmd, val))
    def read_word_data(self, addr, cmd):
        """Reads a word (16 bits) from a device register"""
        return unpack('<H', self.writeread(addr, pack('<B', cmd), 2))
    def write_word_data(self, addr, cmd, val):
        """Writes a word (16 bits) to a device register"""
        return self.write(addr, pack('<BH', cmd, val))
    def read_block_data(self, addr, cmd):
        """Reads a block from a device register.  The block is assumed to be
        prefixed with the block length which is discarded before returning
        data from the function."""
        data = self.writeread(addr, pack('<B', cmd), 257)
        return data[1:1+ord(data[0])]
    def write_block_data(self, addr, cmd, vals):
        """Writes a block to a device register.  The block will be prefixed
        with the length of the block."""
        if len(vals) > 255:
            raise ValueError, "block size is limited to 255 bytes"
        return self.write(addr, pack('<BB', cmd, len(vals)) + vals)
