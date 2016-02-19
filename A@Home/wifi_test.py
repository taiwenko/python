import os
import time
import subprocess
from datetime import datetime

for x in range(1,51):
    scan = "adb -s alt" + str(x) + ':4321 shell "wpa_cli scan" > /dev/null'
    os.system(scan)
    time.sleep(4)
    scan_res = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'wpa_cli', 'scan_results'], stdout=subprocess.PIPE)
    output = scan_res.communicate()[0]
    # print output
    if not "GoogleGuest" in output:
       print "Wifi issues on ALT%d at %s" % (x, str(datetime.now()))
