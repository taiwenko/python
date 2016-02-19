#!/usr/bin/python

###############################################################################
# This program will be used to control ALT tesing parameters
# and to monitor for failures.
# 
# Created By: Clinton Lazzari
# Last Modified By: Clinton Lazzari
#
# Revisions
# Rev 0.1 - 01/09/12 - Initial documentation and pseudo code
# Rev 0.2 - 06/05/12 - Adding a ping test to the actual code
# Rev 0.3 - Unknown  - Troy added HDMI, USB and WiFi tests
# Rev 0.4 - 04/27/13 - Added chamber status on failures
#
# External Requirements: None
# 
# Written and tested on Python 2.7.2
#
###############################################################################

###############################################################################
#
# Imports used for the full program
#
###############################################################################

import urllib
import sys
import time
import socket
import os
import signal
from datetime import datetime
import subprocess
import shlex
import hdmi_sw_matrix
import thermal_chamber

###############################################################################
#
# Constants
#
###############################################################################
    
BASE_STATE_URL = "http://192.168.0.2/state.xml?relay1State="
ADDRESS = '192.168.0.2'
PORT = 80

###############################################################################
#
# Handler for Ctrl-C
#
###############################################################################

def ctrlc_handler(signum, frame):
# Power off units
    wrly = urllib.urlopen(BASE_STATE_URL + "0")
    thermal_chamber.stop()
    print '\r\nFinished'

    sys.exit(0)

###############################################################################
#
# Initial Setup Section:
#
# This section sets up the environment and configures the equipment as needed
#
###############################################################################

# Setup Ctrl-C handling
signal.signal(signal.SIGINT, ctrlc_handler)
signal.signal(signal.SIGTERM, ctrlc_handler)


###############################################################################
#
# Function to start dhrystone on ALT units
#
###############################################################################

def dhrystone_start():
    # print "Starting Dhrystone"
    adb_server_kill = "adb kill-server"
    os.system(adb_server_kill)
    time.sleep(2.5)
    for x in range(1,51):
      ip_to_ping="192.168.0."+str(x+100)
      if(check_connectivity(ip_to_ping) == True):
        connect_alt = "adb connect alt" + str(x) + ":4321 > /dev/null"
        # adb_chk = subprocess.Popen(['adb', 'connect', 'alt' + str(x) + ':4321'], stdout=subprocess.PIPE)
        # output = adb_chk.communicate()[0]
        # if "error: device not found" in output or "error: protocol fault (no status)" in output:
        #  print "ADB crapped out. Starting a new iteration."
        #  continue
        alt_root = "adb -s alt" + str(x) + ":4321 root > /dev/null"
        alt_chmod = "adb -s alt" + str(x) + ":4321 shell chmod 777 /data/local/dhrystone > /dev/null"
        start_alt = "adb -s alt" + str(x) + ':4321 shell "/data/local/dhrystone" &'
        os.system(connect_alt)
        time.sleep(2.5)
        os.system(alt_root)
        time.sleep(.5)
        os.system(connect_alt)
        time.sleep(2.5)
        os.system(alt_chmod)
        time.sleep(.5)
        os.system(start_alt)
        time.sleep(.5)
        os.system(start_alt)

###############################################################################
#
# Function to test USB
#
###############################################################################

def usb_test():
  # print "Starting USB test"
  for x in range(1,51):
      ip_to_ping="192.168.0."+str(x+100)
      if(check_connectivity(ip_to_ping) == True):
        mount_usb = "adb -s alt" + str(x) + ":4321 shell mount -t vfat /dev/block/sda1 /mnt/sdcard > /dev/null"
        connect_alt = "adb connect alt" + str(x) + ":4321 > /dev/null"
        alt_root = "adb -s alt" + str(x) + ":4321 root > /dev/null"
        os.system(connect_alt)
        time.sleep(2)
        os.system(alt_root)
        time.sleep(2)
        os.system(connect_alt)
        time.sleep(2)
        os.system(mount_usb)
        time.sleep(2)
        mount_sp = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'mount', '-t', 'vfat', '/dev/block/sda1', '/mnt/sdcard'], stdout=subprocess.PIPE)
        output = mount_sp.communicate()[0]
        if not "busy" in output:
          print "Failed to mount USB drive on ALT%d at %s" % (x, str(datetime.now()))
          thermal_chamber.status()


###############################################################################
#
# Function to check core temperature
#
###############################################################################

def temp_test():
  # print "Starting Core Temp test"
  for x in range(1,51):
      ip_to_ping="192.168.0."+str(x+100)
      if(check_connectivity(ip_to_ping) == True):
        get_temp = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'cat', '/sys/devices/platform/omap/omap_temp_sensor.0/temp1_input'], stdout=subprocess.PIPE)
        output = get_temp.communicate()[0]
        output = int(output)
        if output > 95000:
          print "Core temperature is %d on ALT%d at %s" % (output/1000, x, str(datetime.now()))
          thermal_chamber.status()

###############################################################################
#
# Function to check wifi
#
###############################################################################

def wifi_test():
  # print "Starting Wifi test"
  for x in range(1,51):
      ip_to_ping="192.168.0."+str(x+100)
      if(check_connectivity(ip_to_ping) == True):
        scan = "adb -s alt" + str(x) + ':4321 shell "wpa_cli scan" > /dev/null'
        os.system(scan)
        time.sleep(3)
        scan_res = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'wpa_cli', 'scan_results'], stdout=subprocess.PIPE)
        output = scan_res.communicate()[0]
        # print output
        if not "GoogleGuest" in output:
           print "Wifi issues on ALT%d at %s" % (x, str(datetime.now()))
           thermal_chamber.status()


###############################################################################
#
# Wrapper for ping test
#
###############################################################################



def check_connectivity(ip):
    ret = subprocess.call("ping -c 1 %s" % ip, shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT) 
    if ret == 0: 
        return True 
    else: 
#        print "%s: did not respond" % ip 
        return False

# Setup communication link to DAQs

# Setup log file(s)

###############################################################################
#
# Initial configuration procedures
#
# This section sets up all of the equipment
#
################################################################################

# Configure thermal chamber to cycle from -5C/0%RH to 55C/85%RH
#  One hour ramp, 3 hours soak

# Configure power supply for 115VAC/60Hz sine wave

# Configure DAQs for VAC auto scale on channels 101:120-301:320

###############################################################################
#
# Actual Program Section:
#
# This is the meat and potatoes of the testing program
#
###############################################################################

skip_list = []


# Check to make sure a list of elements to skip on the ping test was passed
if len(sys.argv) > 1:
    for x in range(1,len(sys.argv)):
        print "Adding %d to skip list" % int(sys.argv[x])
        skip_list.append(int(sys.argv[x]))


# Setup a counter for number of power cycles
count = 0

# Setup an error counter
errors = 0
ip_fault = [0]*50

# Start thermal chamber cycling
print "Starting thermal chamber now"
thermal_chamber.start()

# Give the chamber time to start
time.sleep(2)

# Start data collection
# print "Start thermal and audio data collection now"

cycles = 4

#while True:
for x in range(1,4):
# Start a timer so that we get an accurate loop time
    start = time.time()

# Setup elapsed timer
    elapsed = 0

# Increment iteration
    count += 1

# Notify of iteration count
    print "Starting iteration %d at %s" % (count, str(datetime.now()))
    thermal_chamber.status()

# Start power supply
    print "Units powered on at %s" % str(datetime.now())
    wrly = urllib.urlopen(BASE_STATE_URL + "1")

# Sleep for 2 minutes to let everyone come up
    time.sleep(120)

# Start dhrystone on ALT units
    dhrystone_start()

# Start HDMI tests
    #print "Starting HDMI test"
    hdmi_sw_matrix.hdmi_test()

    while(elapsed <= 3240):
    
# Start a ping test to make sure everyone is up
        # print "Starting Ping test"
        for x in range(101,151):
            if x in skip_list:
                if 0:
                    print "Ignoring 192.168.0."+str(x)
            else:
                ip_to_ping="192.168.0."+str(x)
                if(check_connectivity(ip_to_ping) == False):
                    ip_fault[x-101] = 1
                    print "Failed to connect to ALT%d at %s" % ((x-100), str(datetime.now()))
                    thermal_chamber.status()
                else:
                    ip_fault[x-101] = 0

# Check for faults
        for y in range(0,50):
            if ip_fault[y] == 1:
                errors = 1
                break
            else:
                errors = 0
        elapsed = time.time()-start
        time.sleep(120)


# start Wifi tests
        #print "Running Wifi tests"
        wifi_test()
        
# start USB tests
        #print "Running USB tests"
        usb_test()

# start Temp tests
        #print "Running Temperature tests"
        temp_test()

# Once timer expires
# For now the timer goes for 1 hour minus however long it took to get here and minus the delay afterwards
#   print time.time()
    elapsed = time.time()-start
    print "Total elapsed time in seconds = %d" % elapsed
#   time.sleep(3600-elapsed-60)
# Power off units
# FIXME hardwired to make it power cycle every time for now
# Hack done by MAS on Oct 25, 2012 to force errors=0
    errors = 0;
    if errors == 0:
        wrly = urllib.urlopen(BASE_STATE_URL + "0")

# Wait for the units to completely power off
    time.sleep(60)
    elapsed = 0

# Finishing iteration
    print "Finished iteration %d at %s" % (count, str(datetime.now()))


