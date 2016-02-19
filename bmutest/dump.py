#!/usr/bin/env python
import bq78350
import smbus
from array import array
from struct import pack

# Access device
with smbus.Bus() as bus:
  with bq78350.Device(bus) as dev:
    with dev.EnterROMMode() as prog:
      # Dump Data Area
      data = array('B', [0xFF] * bq78350.writable_data_size)
      for addr in range(0, len(data), bq78350.data_block_size):
        data[addr:addr+bq78350.data_block_size] = \
            array('B', prog.ReadDataBlock(bq78350.data_origin + addr))
      for addr in range(0, len(data), 35):
        end = min(addr + 35, len(data))
        line = pack('>BL', end-addr+5, bq78350.data_srec_origin + addr) + \
            data[addr:end].tostring()
        chksum = ~sum([ord(ch) for ch in line]) & 0x0FF
        line = line + chr(chksum)
        print "S3" + line.encode('hex').upper()

      # Dump Code Area
      data = array('B', pack('>L', bq78350.code_default_value) * 0x6000)
      for addr in range(0, len(data) / 4, bq78350.code_row_size):
        row = prog.ReadCodeRow(addr / bq78350.code_row_size)
        for col in range(len(row)):
          data[(addr+col)*4+0] = (row[col] >> 24) & 0x0FF
          data[(addr+col)*4+1] = (row[col] >> 16) & 0x0FF
          data[(addr+col)*4+2] = (row[col] >>  8) & 0x0FF
          data[(addr+col)*4+3] = (row[col] >>  0) & 0x0FF
      for addr in range(0, len(data), 35):
        end = min(addr + 35, len(data))
        line = pack('>BL', end-addr+4+1, bq78350.code_srec_origin + addr) + \
            data[addr:end].tostring()
        chksum = ~sum([ord(ch) for ch in line]) & 0x0FF
        line = line + chr(chksum)
        print "S3" + line.encode('hex').upper()
