"""Pythonic utility classes for interacting with OpenOCD """

import pexpect

class Openocd():
    def __init__(self, port, config_file_folder, logfile=None):
        self._cmd = 'openocd \
                     --command "gdb_port {:d}"\
                     --command "tcl_port 0"\
                     --command "telnet_port 0"\
                     --file openocd.cfg'.format(port)

        self._config_file_folder = config_file_folder
        self.logfile = logfile
        self._openocd = pexpect.spawn(self._cmd,
                                      cwd=self._config_file_folder,
                                      logfile=logfile)

    def close(self):
        self._openocd.sendcontrol('c')
        self._openocd.expect(pexpect.EOF, timeout=5)
        self._openocd.close(force=True)

    def restart(self):
        self.close()
        self._openocd = pexpect.spawn(self._cmd,
                                      cwd=self._config_file_folder,
                                      logfile=self.logfile)
