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
das_dvt2 = LANSCPI("169.254.152.178")
print das_dvt2.Query("*IDN?")
sys.stdout.flush()


