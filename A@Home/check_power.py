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
das_dvt2 = LANSCPI("192.168.0.47")
print das_dvt2.Query("*IDN?")
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

