import os
import time
import subprocess
from datetime import datetime

for x in range(1,51):
    get_temp = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'cat', '/sys/devices/platform/omap/omap_temp_sensor.0/temp1_input'], stdout=subprocess.PIPE)
    output = get_temp.communicate()[0]
    output = int(output)
    if output > 95000:
      print "Core temperature above 95C on ALT%d at %s" % (x, str(datetime.now()))
    
