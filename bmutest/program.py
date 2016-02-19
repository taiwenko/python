#!/usr/bin/env python
from struct import pack
import bq78350
import smbus
import srec
import sys
import time

# Load SREC
data = srec.Segment(bq78350.data_srec_origin, bq78350.data_segment_size, \
    pack('>B', 0xFF))
code = srec.Segment(bq78350.code_srec_origin, bq78350.code_segment_size * 4, \
    pack('>L', bq78350.code_default_value))
linker = srec.Linker(data, code)
f = srec.Reader(sys.argv[1])
linker.link(f)

# Access device
with smbus.Bus() as bus:
  bus.gpio_set(32)
  time.sleep(1)
  bus.gpio_set(0)
  with bq78350.Device(bus) as dev:
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
    # Verify we booted up
    print "Temperature:", dev.Temperature()
    print "Voltage:    ", dev.Voltage()
    print "Rel SoC:    ", dev.RelativeStateOfCharge()
    print "Abs SoC:    ", dev.AbsoluteStateOfCharge()
    print "Rem Capcity:", dev.RemainingCapacity()
    print "Capacity:   ", dev.FullChargeCapacity()
