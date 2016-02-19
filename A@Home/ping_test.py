#!/usr/bin/python

###############################################################################
# This program will be used to validate a ping test setup only
#
# 
# Created By: Clinton Lazzari
# Last Modified By: Clinton Lazzari
#
# Revisions
# Rev 0.1 - 06/05/12 - Initial release
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

def check_connectivity(ip):
    ret = subprocess.call("ping -c 1 %s" % ip, shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT) 
    if ret == 0: 
        return True 
    else: 
        print "%s: did not respond" % ip 
        return False


count = 0

# Setup an error counter
errors = 0
ip_fault = [0]*50

while True:

    count += 1

# Start a timer so that we get an accurate loop time
    start = time.time()

# Notify of iteration count
    print "Starting iteration %d" % count
    print str(datetime.now())


# Start a ping test to make sure everyone is up
    for x in range(101,151):
        ip_to_ping="192.168.0."+str(x)
        if(check_connectivity(ip_to_ping) == False):
            print "Error connecting to "+ip_to_ping
            ip_fault[x-101] = 1
        else:
            ip_fault[x-101] = 0

# Check for faults
    for y in range(0,50):
        if ip_fault[y] == 1:
            errors = 1
            break
        else:
            errors = 0

    print "Error Count = %d" % errors
