import time
import sys
import os
import signal
from scpi.lan_scpi import LANSCPI 

def ctrlc_handler(signum, frame):
    print '\r\nFinished'
    sys.exit(0)

# Setup Ctrl-C handling
signal.signal(signal.SIGINT, ctrlc_handler)
signal.signal(signal.SIGTERM, ctrlc_handler)

aud_limit = 0.300
das_dvt2 = LANSCPI("192.168.0.3")
print das_dvt2.Query("*IDN?")
sys.stdout.flush()
das_dvt3 = LANSCPI("192.168.0.4")
print das_dvt3.Query("*IDN?")
sys.stdout.flush()


def readv( obj, chan ):
    obj.Send("ROUT:SCAN (@" + chan + ")")
    obj.Send("CONF:VOLT:DC (@" + chan + ")")
    return obj.Query("READ?", float)

def readacv( obj, chan ):
    obj.Send("ROUT:SCAN (@" + chan + ")")
    obj.Send("CONF:VOLT:AC (@" + chan + ")")
    return obj.Query("READ?", float)

def checkacv( obj, chan, expect, tries):
    while tries:
        got = readacv(obj, chan)
        if got >= expect:
            return 1
        tries = tries - 1
        time.sleep(10)
    return -1*got

skip_list = []

# Check to make sure a list of elements to skip on the ping test was passed
if len(sys.argv) > 1:
    for x in range(1,len(sys.argv)):
        sys.stderr.write("Adding %d to skip list" % int(sys.argv[x]))
        skip_list.append(int(sys.argv[x]))

while 1:        
    for i in range(101,121):
        uid = (i-1)/2 - 49
        if uid in skip_list:
            continue;
        uch = i % 2
        sys.stderr.write("%s: Check unit %d channel %d\n" % ( time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch ))
        sys.stderr.flush()
        neg_acv = checkacv(das_dvt2, "%d" %i, aud_limit, 10)
        if neg_acv != 1:
            print "%s: ERROR, Unit %d audio channel %d output level below limit for 10 cycles. Value = %f" % (time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch, -1*neg_acv)
            sys.stdout.flush()

    for i in range(101,121):
        uid = (i-1)/2 - 49 + 20
        if uid in skip_list:
            continue;
        uch = i % 2
        sys.stderr.write("%s: Check unit %d channel %d\n" % ( time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch ))
        sys.stderr.flush()
        neg_acv = checkacv(das_dvt3, "%d" %i, aud_limit, 10)
        if neg_acv != 1:
            print "%s: ERROR, Unit %d audio channel %d output level below limit for 10 cycles. Value = %f" % (time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch, -1*neg_acv)
            sys.stdout.flush()

    for i in range(201, 221):
        uid = (i-1)/2 - 99 + 10
        if uid in skip_list:
            continue;
        uch = i % 2
        sys.stderr.write("%s: Check unit %d channel %d\n" % ( time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch ))
        sys.stderr.flush()
        neg_acv = checkacv(das_dvt2, "%d" %i, aud_limit, 10)
        if neg_acv != 1:
            print "%s: ERROR, Unit %d audio channel %d output level below limit for 10 cycles. Value = %f" % (time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch, -1*neg_acv)
            sys.stdout.flush()

    for i in range(201, 221):
        uid = (i-1)/2 - 99 + 30
        if uid in skip_list:
            continue;
        uch = i % 2
        sys.stderr.write("%s: Check unit %d channel %d\n" % ( time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch ))
        sys.stderr.flush()
        neg_acv = checkacv(das_dvt3, "%d" %i, aud_limit, 10)
        if neg_acv != 1:
            print "%s: ERROR, Unit %d audio channel %d output level below limit for 10 cycles. Value = %f" % (time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch, -1*neg_acv)
            sys.stdout.flush()

    for i in range(301, 321):
        uid = (i-1)/2 - 149 + 40
        if uid in skip_list:
            continue;
        uch = i % 2
        sys.stderr.write("%s: Check unit %d channel %d\n" % ( time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch ))
        sys.stderr.flush()
        neg_acv = checkacv(das_dvt3, "%d" %i, aud_limit, 10)
        if neg_acv != 1:
            print "%s: ERROR, Unit %d audio channel %d output level below limit for 10 cycles. Value = %f" % (time.strftime("%H:%M:%S %Y:%m:%d"), uid, uch, -1*neg_acv)
            sys.stdout.flush()
