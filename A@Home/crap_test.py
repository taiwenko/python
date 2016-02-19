import subprocess
import os
import time

def check_connectivity(ip):
    ret = subprocess.call("ping -c 1 %s" % ip, shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT) 
    if ret == 0: 
        return True 
    else: 
#        print "%s: did not respond" % ip 
        return False

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
