#!c:\Python27\python

import vxi11Device as vxi11

#import numpy	
import os,sys, time

# FSW
#['Rohde&Schwarz', 'FSW-50', '1312.8000K50/100970', '2.10\n']
#inst = rm.open_resource('TCPIP::10.0.0.160::INSTR')

#SMW200A
#['Rohde&Schwarz', 'SMW200A', '1412.0000K02/101575', '3.1.18.2-3.01.086.171_SP2\n']
#inst = rm.open_resource('TCPIP::10.0.0.225::INSTR')

# Anritsu
#['"Anritsu', 'MT8221B/31/541/542/546', '1350198', '1.77"']
#inst = rm.open_resource('TCPIP::10.0.0.189::INSTR')
#inst  = vxi11.Instrument("10.0.0.189")

# Agilent Power Supply N6705B
#['Agilent Technologies', 'N6705B', 'MY50001691', 'D.01.08\n']
#inst = rm.open_resource('TCPIP::10.0.0.193::INSTR')
#inst  = vxi11.Instrument("10.0.0.193")

# Agilent VSG 
#['Agilent Technologies', ' E4438C', ' MY45093057', ' C.05.83\n']
#inst = vxi11.Vxi11Device("10.0.0.193","inst0")
inst = vxi11.Vxi11Device(host="10.0.0.176",device="inst0")


# R&S LTE DEMOD Software
#['Rohde&Schwarz', 'K10x', '000000/000', 'Version 3.4 Beta 2\n']
#inst = rm.open_resource('TCPIP::127.0.0.1::INSTR')

# JDSU
#inst = rm.open_resource('TCPIP::10.0.0.137::INSTR')

vxi11.timeout(15000)
#idn = inst.query_ascii_values("*IDN?",converter="s")
#print idn
#quit()
#inst.write("CONF:PRES")

res = None
try:
  res = inst.ask("*IDN?")
except Exception,e:
	print "FAILED %s"%e
print res
#quit()

def AnritsuMT8221B():
	#inst.write("FREQuency:CENTer 2.68GHz")
	inst.write("FREQuency:CENTer 2.11GHz")
	inst.write("BANDWidth:RESolution 10")
	time.sleep(3)
	inst.write("CONF:RF SUMM")
	inst.write("CONF:DEMod SUMM")
	#print(inst.query(":MEAsure:DEMod:AVErage?"))
	time.sleep(10)
	#print(inst.query(":FETCh:SUMMary?"))
	#time.sleep(1)
	#inst.write("CONF:DEMod SUMM")
	#time.sleep(10)
	#print(inst.query(":FETCh:SUMMary?"))
	#print(inst.write("INIT"))
	#time.sleep(4)
	#inst.query(":FETCh:RF:ACLR?")
	#inst.write("DISP:TRAC:Y:RLEV:OFFS 49")
	#print(inst.query(":FETCh:SUMMary?"))

	#EVM (rms) in %, EVM (pk) in %,Ref Signal (RS) Power in dBm, Sync Signal (SS) Power in dBm, Carrier Frequency in MHz, Freq Error in Hz, Freq Error in ppm, the Cell ID, and the number of measurements average for Frequency Error.
	print(inst.ask(":FETCh:DEMod:CONStln?"))
	print(inst.ask("FETCh:RF:ACLR?"))
	
	
def RS_SW(inst):
	ok = inst.write("CONF:PRES");
	inst.write("CONF:LTE:DUP FDD")
	inst.write("CONF:LTE:LDIR DL")
	inst.write("FREQ:CENT 2.68GHZ")
	inst.write("DISP:TRAC:Y:RLEV:OFFS 49")
	inst.write("CONF:DL:MIMO:CONF TX2")
	res = dict()
	retry = 0
	print "MEASURE..."
	run = True
	while run == True:
		print(inst.write("INIT"))
		#inst.write("INIT:REFR")
		time.sleep(2)
		retry += 1
		stat = inst.query_ascii_values("SYNC:STAT?",converter="b")	
		print("STATUS: ",stat," Retry:", retry)
		if (stat[0] == 1 & stat[1] == 1 & stat[2] == 1):
			run = False
		if retry > 3:
			print "Cannot Obtain Sync!"
			raise SystemExit
		break
	#for stat 
	#print(stat)
	res['Power'] = inst.query_ascii_values("FETCh:SUMMary:OSTP?")[0]
	res['EVM'] = inst.query_ascii_values("FETC:SUMM:EVM?")[0]
	res['FreqError'] = inst.query_ascii_values("FETC:SUMM:FERR?")[0]
	res['RSPower'] = inst.query_ascii_values("FETCh:SUMMary:RSTP?")[0]
	print res
	print inst.query("SENSe:LTE:ANTenna:SELect?")
	print inst.query("CONFigure:LTE:DL:CC:SYNC:ANTenna?")
	#print inst.query("CONF:DL:SUBF2:ALL3:PREC:AP?")
	#print inst.query("TRACe:DATA?")
	#print "DONE!"
	raw_input()
	
	
#RS_SW(inst)
#AnritsuMT8221B()
