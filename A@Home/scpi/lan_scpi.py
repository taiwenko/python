#!/usr/bin/python
# Copyright (c) 2011 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


'''
SCPI-over-TCP controller.
'''


import inspect
import logging
import re
import signal
import socket
import struct
import time
from contextlib import contextmanager


class Error(Exception):
    '''
    A SCPI error.

    Properties:
        error_id: The numeric SCPI error code, if any.
        error_msg: The SCPI error message, if any.
    '''
    def __init__(self, msg, error_id=None, error_msg=None):
        super(Error, self).__init__(msg)
        self.error_id = error_id
        self.error_msg = error_msg


class TimeoutError(Error):
    pass


MAX_LOG_LENGTH = 800
def _TruncateForLogging(msg):
    if len(msg) > MAX_LOG_LENGTH:
        msg = msg[0:MAX_LOG_LENGTH] + '<truncated>'
    return msg


@contextmanager
def Timeout(secs):
    def handler(signum, frame):
        raise TimeoutError('Timeout')

    if secs:
        if signal.alarm(secs):
            raise Error('Alarm was already set')

    signal.signal(signal.SIGALRM, handler)

    try:
        yield
    finally:
        if secs:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, lambda signum, frame: None)


class LANSCPI(object):
    '''A SCPI-over-TCP controller.'''
    def __init__(self, host, port=5025, timeout=60):
        '''
        Connects to a device using SCPI-over-TCP.

        Parameters:
            host: Host to connect to.
            port: Port to connect to.
            timeout: Timeout in seconds.  (Uses the ALRM signal.)
        '''
        self.timeout = timeout
        self.logger = logging.getLogger('SCPI')
        self.host = host
        self.port = port

        self._Connect()

    def _Connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        with Timeout(self.timeout):
            self.logger.debug('] Connecting to %s:%d...' % (
                    self.host, self.port))
            self.socket.connect((self.host, self.port))

        self.rfile = self.socket.makefile('rb', -1)  # Default buffering
        self.wfile = self.socket.makefile('wb', 0)   # No buffering

        self.logger.debug('Connected')

        self.id = self.Query('*IDN?')

    def Close(self):
        self.logger.debug('Destroying')
        self.rfile.close()
        self.wfile.close()
        self.socket.close()

    def Reopen(self):
        '''
        Closes and reopens the connection.
        '''
        self.Close()
        time.sleep(1)
        self._Connect()

    def Send(self, commands, wait=True):
        '''
        Sends a command or series of commands.

        Args:
            commands: The commands to send.  May be list, or a string if
                just a single command.
            wait: If True, issues an *OPC? command after the final
                command to block until all commands have completed.
        '''
        if type(commands) == str:
            self.Send([commands], wait)
            return

        self._WriteLine('*CLS')
        for command in commands:
            if command[-1] == '?':
                raise Error('Called Send with query %r' % command)
            self._WriteLine(command)
            self._WriteLine('SYST:ERR?')

        errors = []
        error_id = None
        error_msg = None
        for i in range(len(commands)):
            ret = self._ReadLine()
            if ret != '+0,"No error"':
                errors.append(
                    'Issuing command %r: %r' % (commands[i], ret))
            if not error_id:
                # We don't have an error ID for the exception yet;
                # try to parse the SCPI error.
                match = re.match(r'^([-+]?\d+),"(.+)"$', ret)
                if match:
                    error_id = int(match.group(1))
                    error_msg = match.group(2)

        if errors:
            raise Error('; '.join(errors), error_id, error_msg)

        if wait:
            self._WriteLine('*OPC?')
            ret = self._ReadLine()
            if int(ret) != 1:
                raise Error('Expected 1 after *OPC? but got %r' % ret)

    def Query(self, command, format=None):
        '''
        Issues a query, returning the result.

        Args:
            command: The command to issue.
            format: If present, a function that will be applied to the query
                response to parse it.  The formatter may be int(), float(), a
                function from the "Formatters" section at the bottom of this
                file, or any other function that accepts a single string
                argument.
        '''
        if '?' not in command:
            raise Error('Called Query with non-query %r' % command)
        self._WriteLine('*CLS')
        self._WriteLine(command)

        self._WriteLine('*ESR?')
        self._WriteLine('SYST:ERR?')

        line1 = self._ReadLine()
        line2 = self._ReadLine()
        # On success, line1 is the queried value and line2 is the status
        # register.  On failure, line1 is the status register and line2
        # is the error string.  We do this to make sure that we can
        # detect an unknown header rather than just waiting forever.
        if ',' in line2:
            raise Error('Error issuing command %r: %r' % (command, line2))

        # Success!  Get SYST:ERR, which should be +0
        line3 = self._ReadLine()
        if line3 != '+0,"No error"':
            raise Error('Error issuing command %r: %r' % (command, line3))

        if format:
            line1 = format(line1)
        return line1

    def Quote(self, string):
        '''
        Quotes a string.
        '''
        # TODO(jsalz): Use the real IEEE 488.2 string format.
        return '"%s"' % string

    def _ReadLine(self):
        '''
        Reads a single line, timing out in self.timeout seconds.
        '''

        with Timeout(self.timeout):
            if not self.timeout:
                self.logger.debug('[ (waiting)')
            ch = self.rfile.read(1)

            if ch == '#':
                # Binary format, which is:
                #
                # 1. A pound sign
                # 2. A base-10 representation of the number of characters in the
                #    base-10 representation of the payload length
                # 3. The payload length, in base-10
                # 4. The payload
                # 5. A newline character
                #
                # E.g., "#17FOO BAR\n" (where 7 is the length of "FOO BAR" and
                # 1 is the length of "7").
                #
                # Note that if any of this goes haywire, the connection will be
                # basically unusable since there is no way to know where we
                # are in the binary data.
                length_length = int(self.rfile.read(1))
                length = int(self.rfile.read(length_length))
                ret = self.rfile.read(length)
                ch = self.rfile.read(1)
                if ch != '\n':
                    raise Error('Expected newline at end of binary data')

                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug('[binary %r' % _TruncateForLogging(ret))
                return ret
            elif ch == '\n':
                # Empty line
                self.logger.debug('[empty')
                return ''
            else:
                ret = ch + self.rfile.readline().rstrip('\n')
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug('[ %s' % _TruncateForLogging(ret))
                return ret

    def _WriteLine(self, command):
        '''
        Writes a single line.
        '''
        if '\n' in command:
            raise Error('Newline in command: %r' % command)
        self.logger.debug('] %s' % command)
        print >>self.wfile, command


#
# Formatters.
#

FLOATS = lambda s: [float(f) for f in s.split(",")]

def BINARY_FLOATS(bin):
    if len(bin) % 4:
        raise Error('Binary float data contains %d bytes '
                    '(not a multiple of 4)' % len(bin))
    return struct.unpack('>' + 'f' * (len(bin)/4), bin)

def BINARY_FLOATS_WITH_LENGTH(expected_length):
    def formatter(bin):
        ret = BINARY_FLOATS(bin)
        if len(ret) == 1 and math.isnan(ret[0]):
            raise Error('Unable to retrieve array')
        if len(ret) != expected_length:
            raise Error('Expected %d elements but got %d' % (
                    expected_length, len(ret)))
        return ret

    return formatter
