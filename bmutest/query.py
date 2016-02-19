#!/usr/bin/env python
from time import sleep
from struct import unpack
import smbus
import bq78350

with smbus.Bus() as bus:
  with bq78350.Device(bus) as dev:
    print "Mode:        ", dev.BatteryMode()
    print "Status:      ", dev.BatteryStatus()
    print "Spec Info:   ", dev.SpecificationInfo()
    print "Temperature: ", dev.Temperature()
    print "Voltage:     ", dev.Voltage()
    print "Current:     ", dev.Current()
    print "Avg Current: ", dev.AverageCurrent()
    print "Rel St Charg:", dev.RelativeStateOfCharge()
    print "Abs St Charg:", dev.AbsoluteStateOfCharge()
    print "Rem Cap:     ", dev.RemainingCapacity()
    print "Full Cap:    ", dev.FullChargeCapacity()
    print "Cycle Count: ", dev.CycleCount()
    print "Design Cap:  ", dev.DesignCapacity()
    print "Design Volt: ", dev.DesignVoltage()
    print "Charge Volt: ", dev.ChargingVoltage()
    print "Charge Curr: ", dev.ChargingCurrent()
    print "Manuf Date:  ", dev.ManufacturerDate()
    print "Serial:      ", dev.SerialNumber()
    print "Manufacturer:", dev.ManufacturerName()
    print "Device Name: ", dev.DeviceName()
    print "Chemistry:   ", dev.DeviceChemistry()
    print "Ext Ave Cell:", dev.ExtAveCellVoltage()

    for cell in range(15):
      print "Cell %d Voltage:" % (cell+1), dev.CellVoltage(cell)

    print "Device Type: ", '0x%04X' % dev.DeviceType()
    print "Firmware Ver:", dev.FirmwareVersion()
    print "Inst Chksum: ", '0x%08X' % dev.InstructionFlashSignature()
    print "Data Chksum: ", '0x%04X' % dev.StaticDFSignature()
    print "Chemical ID: ", '0x%04X' % dev.ChemicalID()
    print "Chem Chksum: ", '0x%04X' % dev.StaticChemDFSignature()
    print "All DF Chksm:", '0x%04X' % dev.AllDFSignature()
    print "DA Status 1: ", dev.DAStatus1()
    print "DA Status 2: ", dev.DAStatus2()

    print "CUV Thresh:  ", dev.UnderVoltageThreshold()
    print "COV Thresh:  ", dev.OverVoltageThreshold()
    print "OCC Thresh:  ", dev.OverCurrentChargeThreshold()
    print "OCD Thresh:  ", dev.OverCurrentDischargeThreshold()
    print "OTC Thresh:  ", dev.OverTemperatureChargeThreshold()
    print "OTD Thresh:  ", dev.OverTemperatureDischargeThreshold()
    print "UTC Thresh:  ", dev.UnderTemperatureChargeThreshold()
    print "UTD Thresh:  ", dev.UnderTemperatureDischargeThreshold()

    print "Op Status:   ", dev.OperationStatus()
