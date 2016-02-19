import logging
import serial
import time
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def start():
    ser = serial.Serial('/dev/ttyUSB19', baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=False, rtscts=False, dsrdtr=False, timeout=0.5)
    ser.open()
    while len(ser.read(1)) > 0:
        continue
    ser.write('start system\r\n')
    ser.flush()
    time.sleep(0.5)
    while len(ser.read(1)) > 0:
        continue
    ser.write('start program\r\n')
    ser.flush()
    time.sleep(0.5)
    while len(ser.read(1)) > 0:
        continue
    ser.close()

def stop():
    ser = serial.Serial('/dev/ttyUSB19', baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=False, rtscts=False, dsrdtr=False, timeout=0.5)
    ser.open()
    # Error checking for serial port open here
    while len(ser.read(1)) > 0:
        continue
    ser.write('stop program\r\n')
    ser.flush()
    time.sleep(0.5)
    while len(ser.read(1)) > 0:
        continue
    ser.write('set setpoint 1=25.0\r\n')
    ser.flush()
    time.sleep(0.5)
    while len(ser.read(1)) > 0:
        continue
    ser.close()   


def status():
    ser = serial.Serial('/dev/ttyUSB19', baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=False, rtscts=False, dsrdtr=False, timeout=0.5)
    ser.open()
    while len(ser.read(1)) > 0:
        continue
    ser.write('read pv 1\r\n')
    ser.flush()
    time.sleep(1)
    temperature = ser.read(5)
    while len(ser.read(1)) > 0:
        continue
    ser.write('read pv 2\r\n')
    ser.flush()
    time.sleep(1)
    humidity = ser.read(5)
    while len(ser.read(1)) > 0:
        continue
    ser.close()
    logger.info('Temp = %s and RH = %s' % (temperature, humidity))
      
      
# thermal_chamber
