import os
import time

connect_126 = "adb connect alt26:4321"
start_126 = 'adb -s alt26:4321 shell "/data/local/dhrystone" &'
connect_101 = "adb connect alt1:4321"
start_101 = 'adb -s alt1:4321 shell "/data/local/dhrystone" &'

os.system(connect_126)
time.sleep(1)
os.system(start_126)
time.sleep(1)
os.system(start_126)
time.sleep(1)
os.system(connect_101)
time.sleep(1)
os.system(start_101)
time.sleep(1)
os.system(start_101)
time.sleep(1)

