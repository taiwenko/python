import os
import time
import subprocess
from datetime import datetime

for x in range(1,51):        
    mount_usb = "adb -s alt" + str(x) + ":4321 shell mount -t vfat /dev/block/sda1 /mnt/sdcard > /dev/null"
    connect_alt = "adb connect alt" + str(x) + ":4321 > /dev/null"
    alt_root = "adb -s alt" + str(x) + ":4321 root > /dev/null"
    
    os.system(connect_alt)
    time.sleep(2.5)
    os.system(alt_root)
    time.sleep(2.5)
    os.system(connect_alt)
    time.sleep(2.5)
    os.system(mount_usb)
    time.sleep(2.5)
    mount_sp = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'mount', '-t', 'vfat', '/dev/block/sda1', '/mnt/sdcard'], stdout=subprocess.PIPE)
    output = mount_sp.communicate()[0]
    if not "busy" in output:
        print "Failed to mount USB drive on ALT%d at %s" % (x, str(datetime.now()))
