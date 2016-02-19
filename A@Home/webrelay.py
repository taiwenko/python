import urllib
import sys

BASE_URL = "http://192.168.1.2/state.xml?relay1State="

if sys.argv[1] == "on":
   wrly = urllib.urlopen(BASE_URL + "1")
else:
   wrly = urllib.urlopen(BASE_URL + "0")
if wrly.getcode() != 200:
   sys.exit("Failed to set relay state")
wrly.close()
