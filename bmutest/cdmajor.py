#!/usr/bin/env python

import sys, time, serial
from serial.tools import list_ports
import dcload
import xln6024
from struct import pack, unpack
import smbus
import bq78350
import srec

usbid_bk8514 = '067B:2303'
usbid_bkXLN6024 = '10C4:EA60'
sn_xln6024_top = '276D14130'
sn_8514_top = '1687110009'
sn_xln6024_bottom = '276F12110'
sn_8514_bottom = '1687210009'

# BK Precision devices (USB serial ports)
bkdev = {}

shortpause = 1
longpause = 5

i_normal = 5.0
i_overload = 22.0
tol = 0.25

ifmt = "%2.1f, %2.1f, %2.1f\t\t\t\t"

def bootBMU(bus):
  bus.gpio_set(32)
  time.sleep(1)
  bus.gpio_set(0)


def readBK8514Current(dcload):
    return float(dcload.GetInputValues().split('\t')[1].split(' ')[0])


def readChargeCurrents():
    i_pwr = bkdev['ext_pwr'].GetCurrent()
    i_load = readBK8514Current(bkdev['int_load'])
    i_batt = bqDev.Current()
    return (i_pwr, i_load, i_batt)

def readDischargeCurrents():
    i_pwr = bkdev['int_pwr'].GetCurrent()
    i_load = readBK8514Current(bkdev['ext_load'])
    i_batt = abs(bqDev.Current())
    return (i_pwr, i_load, i_batt)


def testBKXLN6024(comport):
    pwr = xln6024.XLN6024()
    print 'Checking for pwr on', comport
    pwr.Initialize(comport, 57600)
    sn = pwr.GetProductInformation()
    if sn:
        sn = sn.split(',')[2]
        return (sn, pwr)
    else:
        pwr.close()
        return ('', '')

def testBK8514(comport):
    load = dcload.DCLoad()
    print 'Checking for load on', comport
    load.Initialize(comport, 38400)
    sn = load.GetProductInformation()
    if sn:
        sn = sn.split('\t')[1]
        return (sn, load)
    else:
        load.sp.close()
        return ('', '')

def bkFindDevices():
    ports = list(list_ports.comports())
    for p in ports:
        if usbid_bk8514 in p[2].upper():
            bk8514_COM = p[0]
            (sn, load) = testBK8514(bk8514_COM)
            print 'Found: ', sn
            if (sn == sn_8514_top):
                bkdev['int_load'] = load
            if (sn == sn_8514_bottom):
                bkdev['ext_load'] = load
        if usbid_bkXLN6024 in p[2].upper():
            bkXLN6024_COM = p[0]
            (sn, pwr) = testBKXLN6024(bkXLN6024_COM)
            print 'Found: ', sn
            if (sn == sn_xln6024_top):
                bkdev['int_pwr'] = pwr
            if (sn == sn_xln6024_bottom):
                bkdev['ext_pwr'] = pwr

def bkInit():
    bkdev['int_pwr'].SetVoltage(44)
    bkdev['int_pwr'].SetCurrent(24)
    bkdev['int_pwr'].TurnPowerOn()

    bkdev['ext_pwr'].TurnPowerOff()
    bkdev['ext_pwr'].SetVoltage(51)
    bkdev['ext_pwr'].SetCurrent(0)

    bkdev['int_load'].SetRemoteControl()
    bkdev['int_load'].TurnLoadOff()
    bkdev['int_load'].SetMaxCurrent(40.0)
    bkdev['int_load'].SetMaxVoltage(60.0)
    bkdev['int_load'].SetMaxPower(1200.0)
    bkdev['int_load'].SetMode('CV')
    bkdev['int_load'].SetCVVoltage(45.0)
    bkdev['int_load'].TurnLoadOn()

    bkdev['ext_load'].SetRemoteControl()
    bkdev['ext_load'].TurnLoadOff()
    bkdev['ext_load'].SetMaxCurrent(40.0)
    bkdev['ext_load'].SetMaxVoltage(60.0)
    bkdev['ext_load'].SetMaxPower(1200.0)
    bkdev['ext_load'].SetMode('CC')
    bkdev['ext_load'].SetCCCurrent(0.0)

def testChargeAcceptance():
    print "Charge acceptance test:"
    bkdev['ext_pwr'].SetCurrent(i_normal)
    bkdev['ext_pwr'].TurnPowerOn()

    time.sleep(longpause)

    (ip, il, ib) = readChargeCurrents()
    thr = i_normal - tol

    bkdev['ext_pwr'].TurnPowerOff()

    print ifmt % (ip,il,ib),
    if (ip > thr) & (il > thr) & (ib > thr):
        print 'PASS'
    else:
        print 'FAIL'


def testChargeOverCurrent():
    print "Charge overcurrent test:"
    bkdev['ext_pwr'].SetCurrent(i_overload)
    bkdev['ext_pwr'].TurnPowerOn()

    time.sleep(shortpause)

    (ip, il, ib) = readChargeCurrents()
    print ifmt % (ip,il,ib)

    time.sleep(longpause)

    (ip, il, ib) = readChargeCurrents()
    thr = 0 + tol

    bkdev['ext_pwr'].TurnPowerOff()
    bkdev['ext_pwr'].SetCurrent(i_normal)

    print ifmt % (ip,il,ib),
    if (ip < thr) & (il < thr) & (ib < thr):
        print 'PASS'
    else:
        print 'FAIL'


def testLoadAcceptance():
    print "Load acceptance test:"
    bkdev['ext_load'].SetCCCurrent(i_normal)
    bkdev['ext_load'].TurnLoadOn()
    time.sleep(longpause)

    (ip, il, ib) = readDischargeCurrents()
    thr = i_normal - tol
    bkdev['ext_load'].TurnLoadOff()

    print ifmt % (ip,il,ib),
    if (ip > thr) & (il > thr) & (ib > thr):
        print 'PASS'
    else:
        print 'FAIL'

def testLoadOverCurrent():
    print "Load overcurrent test:"
    bkdev['ext_load'].SetCCCurrent(i_overload)
    bkdev['ext_load'].TurnLoadOn()

    time.sleep(shortpause)
    (ip, il, ib) = readDischargeCurrents()
    print ifmt % (ip,il,ib)

    time.sleep(longpause)
    (ip, il, ib) = readDischargeCurrents()
    thr = 0 + tol
    bkdev['ext_load'].TurnLoadOff()
    bkdev['ext_load'].SetCCCurrent(i_normal)

    print ifmt % (ip,il,ib),
    if (ip < thr) & (il < thr) & (ib < thr):
        print 'PASS'
    else:
        print 'FAIL'
    time.sleep(longpause)


def bkShutdown():
    bkdev['ext_pwr'].TurnPowerOff()

    bkdev['ext_load'].TurnLoadOff()
    bkdev['ext_load'].SetLocalControl()

    bkdev['int_load'].TurnLoadOff()
    bkdev['int_load'].SetLocalControl()

    bkdev['int_pwr'].TurnPowerOff()

def loadSREC(filename):
    data = srec.Segment(bq78350.data_srec_origin, bq78350.data_segment_size, \
        pack('>B', 0xFF))
    code = srec.Segment(bq78350.code_srec_origin, bq78350.code_segment_size * 4, \
        pack('>L', bq78350.code_default_value))
    linker = srec.Linker(data, code)
    f = srec.Reader(filename)
    linker.link(f)
    return (data, code)

def programBMU(dev, data, code):
    print "Entering ROM Mode"
    with dev.EnterROMMode() as prog:
        # Start programming
        print "  Version ", prog.Version()
        print "Erasing program space"
        prog.EraseCode()
        print "  Checksum", '0x%08X' % prog.CodeChecksum(0)
        print "Erasing data space"
        prog.EraseData()
        print "  Checksum", '0x%04X' % prog.DataChecksum()
        print "Writing out data"
        prog.WriteData(data)
        print "  Checksum", '0x%04X' % prog.DataChecksum()
        print "Writing out code"
        prog.WriteCodeBytes(code)
        print "  Checksum", '0x%08X' % prog.CodeChecksum(0)
        print "Leaving ROM Mode"


# Here is the main thing

# (data, code) = loadSREC('20141031.srec')
with smbus.Bus() as bus:
    bkFindDevices()
    bkInit()
    # bootBMU(bus)
    # with bq78350.Device(bus) as bqDev:
    #     programBMU(bqDev, data, code)
    #     print "Found device:", bqDev.DeviceName()
    #     testChargeAcceptance()
    #     testChargeOverCurrent()
    #     testLoadAcceptance()
    #     testLoadOverCurrent()
    #     testLoadAcceptance()
bkShutdown()
