import serial

class Mensor6180(object):
    def __init__(self, port, baudrate=19200, bytesize=8, parity='N',
                 stopbits=1):
        self.serial = serial.Serial(port, baudrate, bytesize, parity, stopbits)

    def _write(self, message):
        self.serial.write(message + '\r\n')

    def _read(self, timeout):
        self.serial.timeout = timeout
        value = self.serial.readline()
	if len(value) == 0 or value[-1] != '\n':
            raise IOError, 'Read Timeout'
        return value.strip()

    def _query(self, message, timeout=1.0):
        self._write(message)
        return self._read(timeout)

    def measure(self):
        """Returns the currently measured pressure in kPa"""
        value = self._query('#1?')
        if len(value) < 4:
            raise Exception, 'Unknown Response'
        return float(value[4:])
