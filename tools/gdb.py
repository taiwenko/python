"""Pythonic utility classes for interacting with GDB."""
import os
import pexpect

from functools import wraps

# Timeout in seconds
COMMAND_TIMEOUT = 7  # Longest OpenOCD polling delay is 6.3 seconds
FLASH_TIMEOUT = 400

# What GDB says when commands are given
GDB_RESPONSES = ['(gdb) ',
                 'Continuing.',
                 'A program is being debugged already.']

# Keep these in sync with GDB response indices
GDB_PROMPT = 0
GDB_CONTINUING = 1
GDB_ALREADY_BEING_DEBUGGED = 2

class Gdb():
    def __init__(self, port, binary, logfile=None):
        self._gdb = GdbInterface(port, binary, logfile=logfile)
        self._maybe_running = False
        self._port = port

        self.reconnect()
        self.reset()
        self._gdb.send_command('set height 0')
        self.delete_breakpoints()
        self._gdb.logfile = logfile

        # If the build_root.txt file exists, set substitute-path for finding
        # packaged sources.
        # The ELF files contain absolute paths to the source files at the time
        # of compilation, so the search path has to be altered to look for files
        # in the proper location in the test execution environment.
        root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        try:
            with open(os.path.join(root, 'build_root.txt'), 'r') as f:
                build_root = f.read().replace('\n', '')
                self._gdb.send_command('set substitute-path \'%s\' \'%s\'' % (
                                       build_root, root))
        except:
            pass

    def start_error_log(self, logfile):
        self._gdb.logfile_read = logfile

    def stop_error_log(self):
        self._gdb.logfile_read = None

    def close(self):
        self._gdb.close()

    def _must_be_paused(func):
        """Decorator ensuring the program is paused."""
        @wraps(func)
        def inner(gdb_instance, *args, **kwargs):
            if gdb_instance.is_running():
                gdb_instance.pause()
            func(gdb_instance, *args, **kwargs)
        return inner

    def is_running(self):
        """Check for new terminal prompt, indicating the program is halted."""
        if self._maybe_running:
            try:
                self._gdb.wait_for_ready(0)
            except pexpect.TIMEOUT:
                return True
            self._maybe_running = False
        return False

    @_must_be_paused
    def add_breakpoint(self, location):
        self._gdb.send_command('b {:s}'.format(location))

    @_must_be_paused
    def run(self):
        index = self._gdb.send_command('continue')
        if index == GDB_CONTINUING:
            self._maybe_running = True

    def pause(self):
        self._gdb.send_control('c')
        self._maybe_running = False

    @_must_be_paused
    def backtrace(self):
        self._gdb.send_command('backtrace')

    @_must_be_paused
    def delete_breakpoints(self):
        self._gdb.send_command_unchecked('delete')
        result = self._gdb.expect_exact(['Delete all breakpoints',
                                         GDB_RESPONSES[GDB_PROMPT]],
                                        COMMAND_TIMEOUT)
        if result == 0:
            self._gdb.send_command('y')

    @_must_be_paused
    def flash(self):
        self._gdb.send_command('monitor reset init')
        self._gdb.send_command('load', FLASH_TIMEOUT)
        self._gdb.send_command('monitor reset halt')

    @_must_be_paused
    def reconnect(self):
        self._gdb.send_command(
                'target remote localhost:{:d}'.format(self._port))

    @_must_be_paused
    def reset(self):
        self._gdb.send_command('monitor reset halt')

    @_must_be_paused
    def info_all_registers(self):
        self._gdb.send_command('info all-registers')

    @_must_be_paused
    def info_locals(self):
        self._gdb.send_command('info locals')

    @_must_be_paused
    def list_lines(self):
        self._gdb.send_command('list')

    @_must_be_paused
    def disassemble_pc(self, radius=None):
        if radius is not None:
            self._gdb.send_command(
                'disassemble $pc-{:d},$pc+{:d}'.format(radius, radius))
        else:
            self._gdb.send_command('disassemble')

    @_must_be_paused
    def restart(self):
        self._maybe_running = False
        self.reconnect()
        self.reset()
        self.run()

class GdbInterface(pexpect.spawn):
    """Provides a handy interface for interacting with GDB."""
    def __init__(self, port, binary, logfile):
        cmd = 'arm-none-eabi-gdb -q {:s}'.format(binary)
        super(GdbInterface, self).__init__(cmd, logfile=logfile)
        self.wait_for_ready()

    def __enter__(self):
        return self

    def __exit__(self, unused_type, unused_value, unused_traceback):
        self.close()

    def wait_for_ready(self, timeout=COMMAND_TIMEOUT):
        """Handles GDB responses to input."""

        index = -1
        while True:
            index = self.expect_exact(GDB_RESPONSES,
                                      timeout)
            if index == GDB_ALREADY_BEING_DEBUGGED:
                self.send_command_unchecked('y')
            else:
                break;
        return index

    def close(self):
        """Read any leftover bits of GDB's output before closing."""
        self.send_control('c')
        self.send_control_unchecked('d')
        self.send_control_unchecked('d')
        self.expect(pexpect.EOF)
        super(GdbInterface, self).close(force=True)

    def send_control(self, command, timeout=COMMAND_TIMEOUT):
        """Sends CTRL-<command> and waits for response."""
        self.sendcontrol(command)
        return self.wait_for_ready(timeout)

    def send_control_unchecked(self, command):
        """Sends CTRL-<command> but does not wait for response."""
        self.sendcontrol(command)

    def send_command(self, command, timeout=COMMAND_TIMEOUT):
        """Sends command and waits for response."""
        self.sendline(command)
        return self.wait_for_ready(timeout)

    def send_command_unchecked(self, command):
        """Sends command, but does not wait for response."""
        self.sendline(command)
