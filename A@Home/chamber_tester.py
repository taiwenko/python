import serial
import time
import os
from datetime import datetime
   


ser = serial.Serial('/dev/ttyUSB19', baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=False, rtscts=False, dsrdtr=False, timeout=1)
ser.open()
ser.write('read pv 1\r\n')
ser.flush()
temperature = ser.read(5)
while len(ser.read(1)) > 0:
        # print SerDecode(ser.read(1))
    continue
ser.write('read pv 2\r\n')
ser.flush()
humidity = ser.read(5)
ser.close()
print 'Temp = %s and RH = %s at %s' % (temperature, humidity, str(datetime.now()))
      
      
# thermal_chamber
