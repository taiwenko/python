"""Represents a device with shell and gdb interface."""

import os
from tools import gdb, openocd, shell

STARTING_GDB_PORT = 3333


class DebugTarget():
    next_gdb_port = STARTING_GDB_PORT

    def __init__(self, name, app_dir):
        self.initialized = False
        self.name = name
        self.app_dir = app_dir
        self.debug_port = None
        self.serial_device = None
        self.command_logfunc = None
        self.serial_log = None
        self.log_gdb_flag = None

        self.openocd = None
        self.gdb = None
        self.shell = None

        self.powered_on = True
        self.default_on = True
        self.gdb_enabled = False

    def enable_gdb(self, log_gdb_flag):
        self.debug_port = DebugTarget.next_gdb_port
        DebugTarget.next_gdb_port += 1
        self.log_gdb_flag = log_gdb_flag
        self.gdb_enabled = True

    def set_serial_interface(self, serial_device, command_logfunc, serial_log):
        self.serial_device = serial_device
        self.command_logfunc = command_logfunc
        self.serial_log = serial_log

    def initialize(self):
        if self.initialized:
            return

        if self.gdb_enabled:
            config_dir = os.path.join(os.path.dirname(__file__), '../src/app')
            make_binary = os.path.join(self.app_dir,
                                       '{0:s}/release/{0:s}'.format(self.name))
            cobble_binary = os.path.join(self.app_dir,
                                       '{0:s}/{0:s}'.format(self.name))
            openocd_cfg = os.path.join(config_dir, '{0:s}'.format(self.name))

            binary = cobble_binary
            if os.path.isfile(make_binary):
                binary = make_binary

            openocd_log = None
            gdb_log = None
            if self.log_gdb_flag:
                if not os.path.exists('test_logs'):
                    os.mkdir('test_logs')
                gdb_log = open(
                        'test_logs/{:s}_gdb_log.txt'.format(self.name), 'w')
                openocd_log = open(
                        'test_logs/{:s}_openocd_log.txt'.format(self.name), 'w')

            self.openocd = openocd.Openocd(self.debug_port,
                                           openocd_cfg,
                                           openocd_log)
            self.gdb = gdb.Gdb(self.debug_port, binary, gdb_log)

        if self.serial_device:
            self.shell = shell.Shell(self.serial_device,
                                     self.command_logfunc,
                                     self.serial_log)
            self.scoreboard = self.shell.scoreboard

        self.initialized = True

    def reset_shell_scoreboard(self):
        if self.shell:
            self.shell.reset()

    def close(self):
        if self.shell:
            self.shell.close()
        if self.gdb:
            self.openocd.close()
            self.gdb.close()

    def is_running(self):
        assert self.powered_on, 'Device is not powered on.'
        return self.gdb.is_running()

    def run(self):
        assert self.powered_on, 'Device is not powered on.'
        self.gdb.run()

    def pause(self):
        self.gdb.pause()

    def add_breakpoints(self):
        self.gdb.add_breakpoint('__assert_func')
        self.gdb.add_breakpoint('vApplicationMallocFailedHook')
        if self.name == 'pfc':
            self.gdb.add_breakpoint('Default_Handler')

    def start_error_log(self, logfile):
        self.gdb.start_error_log(logfile)

    def stop_error_log(self):
        self.gdb.stop_error_log()

    def dump(self):
        self.gdb.pause()
        self.gdb.list_lines()
        self.gdb.backtrace()
        self.gdb.disassemble_pc()
        self.gdb.info_locals()

    def restart_interfaces(self):
        self.openocd.restart()
        self.gdb.restart()
        if self.shell:
            self.shell.reset()
