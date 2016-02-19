import os
import time

for x in range(1,51):
      connect_alt = "adb connect alt" + str(x) + ":4321 > /dev/null"
      alt_root = "adb -s alt" + str(x) + ":4321 root"
      alt_chmod = "adb -s alt" + str(x) + ":4321 shell chmod 777 /data/local/dhrystone"
      start_alt = "adb -s alt" + str(x) + ':4321 shell "/data/local/dhrystone" &'
      
      os.system(connect_alt)
      time.sleep(3)
      os.system(alt_root)
      time.sleep(1)
      os.system(connect_alt)
      time.sleep(3)
      os.system(alt_chmod)
      time.sleep(1)
      os.system(start_alt)  
'''
   alt_connect = "adb connect alt" + str(x) + ":4321"
   alt_root = "adb -s alt" + str(x) + ":4321 root"
   print alt_connect
   print alt_root
   alt_add = "adb -s alt" + str(x) + ":4321" + " push ./dhrystone /data/local"
   print alt_add
   os.system(alt_connect)
   time.sleep(.5)
   os.system(alt_root)
   time.sleep(.5)
   os.system(alt_connect)
   time.sleep(.5)
   os.system(alt_add)
   print "loaded dhrystone on alt" + str(x)
'''
