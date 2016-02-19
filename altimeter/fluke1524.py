import serial

class Fluke1524(object):
    def __init__(self, port, baudrate=9600, bytesize=8, parity='N',
                 stopbits=1):
        self.serial = serial.Serial(port, baudrate, bytesize, parity, stopbits)
        self._write('*CLS')
        idn = self._query('*IDN?')
        if not idn.startswith('FLUKE,1524,'):
            raise Exception, 'Unknown device on ' + port

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
        value = self._query('READ?1')
        return float(value)
