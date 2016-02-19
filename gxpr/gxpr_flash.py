#!/usr/bin/python2.7

import aeroflex
import xpf6020
import argparse
import os
import sys

from datetime import datetime
from time import sleep
import config_common

import tools.utils as tools
from tools import shell

parser = argparse.ArgumentParser(description='GXPR Flash')
parser.add_argument('--firmware_dir',
                    default=None,
                    help='path to firmware directory (optional)')
args = parser.parse_args()

sorensen_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A5028CFJ-if00-port0'
aero_path = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A40132OD-if00-port0'
bridge_path = '/dev/serial/by-id/usb-loon_gxprbridge_300217-059-if03-port0'

print "Accessing the Power Supply"
sore = xpf6020.Xpf6020(sorensen_path)
sore.reset_ps()
sore.set_voltage(1,20)
sore.set_currentlimit(1,0.5)

print "Accessing the Aeroflex"
aero = aeroflex.Aeroflex(aero_path)

NAME = 'GXPR'
IMAGE_NAME = 'gxpr'

while True:
    
    sore.all_output('on')
    sleep(1)
    unit_id = config_common.prompt_unit(NAME)
    sn = unit_id.split("FL")[1]
    
    # Flash
    config_common.run_flash_firmware(args.firmware_dir, IMAGE_NAME)
    sleep(1)
    sore.all_output('off')
    sleep(5)
    sore.all_output('on')
    sleep(10)
    
    # Flash S/N
    tom = shell.Shell(bridge_path)
    sleep(1)
    sb = shell.Scoreboard(tom,'gxpr_bridge')
    sleep(1)
    print sb.query('version_hash_gxpr')
    tom.sendline('test set_system_info %s' % sn) 
    sleep(3)
    print sb.query('gxpr_serial_number')
    print sb.query('gxpr_fpga_sw_version')
    sleep(1)

    aeromap = aero.measure()

    print "   GXPR Status: " + aeromap['overall']
    print "   GXPR ERP: " + aeromap['power_boterp_value']
    print "   GXPR MTL: " + aeromap['power_botmtl_value']
    print "   GXPR Decoder: " + aeromap['decoder']
    print "   GXPR Power: " + aeromap['power']
    print "   GXPR Timing: " + aeromap['timing']
    print "   GXPR Delay: " + aeromap['delay']
    print "   GXPR Reply: " + aeromap['reply']
    print "   GXPR Jitter: " + aeromap['jitter']
    print "   GXPR ratio: " + aeromap['ratio']
    print "   GXPR Sls: " + aeromap['sls']
           
    sore.all_output('off')
    if not tools.prompt_yes_no('Continue to next %s?' % NAME):
        break;

raw_input('\n\nPress Enter to close.')

