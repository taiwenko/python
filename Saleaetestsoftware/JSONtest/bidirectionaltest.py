#!/usr/bin/env python

import socket
import time
import json
import subprocess

NULL_CHAR = "\x00"

TCP_IP = '127.0.0.1'
TCP_PORT = 10429
BUFFER_SIZE = 1024

#using purely time is not reliable
#TODO: check terminal output to verify Logic.exe is running and initialized
#subprocess.Popen(["C:\Program Files\Saleae LLC\Logic.exe"])
#for x in range(0,2):
#    print("sleeping 10")
#    time.sleep(10)

with open('result.json') as config_file:
    config_data = json.load(config_file)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

#this communicates a strict set of messages
#TODO: consider dynamically messaging based on config_file contents
MESSAGE = "GET_CONNECTED_DEVICES" + NULL_CHAR
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
print "data:", data

MESSAGE = "SET_NUM_SAMPLES," + config_data['capture_samples'] + NULL_CHAR
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
print "data:", data

MESSAGE = "SET_SAMPLE_RATE," + config_data['digital_sample_rate'] + "," + config_data["analog_sample_rate"] + NULL_CHAR
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
print "data:", data

MESSAGE = "SET_ACTIVE_CHANNELS," + "DIGITAL_CHANNELS," + config_data['active_digital_channels'] + ","\
                                 + "ANALOG_CHANNELS," + config_data['active_analog_channels'] + NULL_CHAR
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
print "data:", data

MESSAGE = "CAPTURE" + NULL_CHAR
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
print "data:", data

print("sleeping 5")
time.sleep(5)

MESSAGE = "EXPORT_DATA," + config_data['capture_filename'] + "," + "ALL_CHANNELS," + "VOLTAGE," + "ALL_TIME," + "ADC," + "CSV," + "HEADERS," + "COMMA," + "TIME_STAMP," + "SEPARATE," + "DEC" + NULL_CHAR
          #"CSV," + "HEADERS," + "TIME_STAMP," + "DEC," + "EACH_SAMPLE," + "VOLTAGE" + NULL_CHAR
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
print "data:", data

s.close()

time.sleep(5) # delays for 5 seconds
