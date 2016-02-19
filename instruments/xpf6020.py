#!/usr/bin/python

# Copyright 2014 Google, Inc.
# Routines for talking to the Sorensen XPF 60-20DP
# Author: TaiWen Ko
# Requires serial library

import serial
import time

class Xpf6020(object):
    def __init__(self, port, baudrate=9600, bytesize=8, parity='N',
                 stopbits=1):
        self.serial = serial.Serial(port, baudrate, bytesize, parity, stopbits)
        self._write('*CLS')
        idn = self._query('*IDN?')
        if not idn.startswith('SORENSEN, XPF'):
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

    def measure(self, ch):
        current = self._query('I%sO?' % ch)
        voltage = self._query('V%sO?' % ch)
        #return float(voltage,current)
        return [str(voltage),str(current)]

    def set_voltage(self, ch, volt):
        self._write('V' + str(ch) + ' ' + str(volt)) 
        time.sleep(0.1)

    def set_currentlimit(self, ch, current):
        self._write('I' + str(ch) + ' ' + str(current)) 
        time.sleep(0.1)

    def reset_ps(self):
	self._write('*RST')
        time.sleep(0.1)

    def ind_output(self, ch, switch):
        if switch == 'off':
	    self._write('OP' + str(ch) + ' 0')
            time.sleep(0.1) # Allow controller to catch up
            print 'XPF6020 Power Supply Ch' + str(ch) + ' is off.'
        elif switch == 'on':
            self._write('OP' + str(ch) + ' 1')
            time.sleep(0.1) # Allow controller to catch up
            print 'XPF6020 Power Supply Ch' + str(ch) + ' is on!'

    def all_output(self, switch):
        if switch == 'off':
	    self._write('OPALL 0')
            time.sleep(0.1) # Allow controller to catch up
            print 'XPF6020 Power supply channels are off.'
        elif switch == 'on':
            self._write('OPALL 1')
            time.sleep(0.1) # Allow controller to catch up
            print 'XPF6020 Power supply channels are on!'

if __name__ == '__main__':
    
    # Parameters
    ps = Xpf6020('/dev/ttyUSB1')
    ps.reset_ps()
    print ps.measure('1')
    print ps.measure('2')
