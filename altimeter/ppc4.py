import serial
import time
from datetime import datetime, timedelta

STATIC_CONTROL = 0
DYNAMIC_CONTROL = 1

class TimeoutError(Exception):
    pass

class PPC4(object):
    def __init__(self, port, baudrate=9600, bytesize=8, parity='N',
                 stopbits=1):
        self.verbose = False
        self.serial = serial.Serial(port, baudrate, bytesize, parity, stopbits)
        self._reset()
        idn = self._command('*IDN?')
        if not idn.startswith('FLUKE, PPC4,'):
            raise Exception, 'Unknown device on %s (IDN %s)' % (port, idn)

    def _write(self, message):
        """Writes the command test to the PPC4.  As the serial interface
        is a bit flaky, delays are added before each byte."""
        if self.verbose:
            print ">>%s" % message
        for ch in ('%s\r\n' % message):
            time.sleep(0)
            self.serial.write(ch)

    def _read(self, timeout):
        """Reads the command response from the PPC4.  If a response doesn't
        arrive, IOError is raised to indicate the timeout."""
        self.serial.timeout = timeout
        value = self.serial.readline()
        if len(value) == 0:
            if self.verbose:
                print "(timeout)"
            raise IOError, 'Read Timeout'
        value = value.strip()
        if self.verbose:
            print "<<%s" % value
        return value

    def _reset(self):
        """When a normal command inevitably breaks, we need to resynchronize
        our serial connection to the PPC4.  To do this, we keep sending *CLS
        until we get the appropriate reply, OK."""
        for cnt in range(5):
            time.sleep(1)
            self._write('*CLS')
            try:
                if self._read(0.25) == 'OK':
                    return
            except IOError:
                pass
        raise Exception, 'Unable to reinitialize serial connection'

    def _command(self, message, timeout=0.25):
        """Handles a single command exchange with the PPC4.  As the serial
        interface is incredibly flaky, errors and timeouts are extremely
        common.  To mitigate this, errors are supressed until after multiple
        attempts to resynchronize serial communications and reissue the
        command."""
        for cnt in range(5):
            self._write(message)
            try:
                value = self._read(timeout)
                if value.startswith('ERR#'):
                    raise IOError, value
                return value
            except IOError:
                if cnt == 4:
                    raise
                self._reset()
        raise Exception, 'Lost communications with hardware'

    def abort(self):
        """Stops active pressure generation/control.  All control valves are
        closed.  The exhaust and transducer isolation valves are not affected.
        
        This program message has no effect if the PPC4 is not using automated
        pressure control.  When using automated pressure control, it abords
        the control.  This command is recommended to idle the PPC4 before
        setting a new target pressure."""
        self._command('ABORT')

    def autorange(self, limit, units):
        """Read existing AutoRange range or create a new AutoRange range."""
        self._command('ARANGE=%f,%s,A' % (limit, units), 15.0)

    def decrease(self, amount):
        """Decrease the pressure a given amount using the slow speed."""
        self._command('DP=%f' % amount, 4.0)

    def hold_limit(self, limit=None):
        """Read or set the automated pressure control hold limit as a pressure
        value."""
        if limit is None:
            value = self._command('HS')
            return float(value.split()[0])
        else:
            self._command('HS=%f' % limit)

    def decrease_fast(self, enable=True):
        """Open or close the fast decrease gate."""
        if enable:
            self._command('DF=1')
        else:
            self._command('DF=0')

    def increase(self, amount):
        """Increase the pressure a given amount using the slow speed."""
        self._command('IP=%f' % amount, 4.0)

    def increase_fast(self, enable=True):
        """Open or close the fast increase gate."""
        if enable:
            self._command('IF=1')
        else:
            self._command('IF=0')

    def mode(self, newmode=None):
        """Read or set the automated pressure control mode"""
        if newmode is None:
            value = self._command('MODE')
        else:
            value = self._command('MODE=%d' % newmode)
        return int(value[5:])

    def pressure(self, newpressure=None, volume=None):
        """Set a new target pressure and start a pressure generation cycle or
        returns the currently measured pressure."""
        if newpressure is None:
            value = self._command('PR', 4.0).split(' ')
            # (value, ready?)
            return (float(value[1]), value[0]=='R')
        elif volume is None:
            self._command('PS=%f' % newpressure)
        else:
            self._command('PS=%f,%f' % (newpressure, volume))

    def status(self):
        """Returns the next available pressure, rate, on-board barometer
        reading, control status, and the QRPT uncertainty."""
        value = self._command('PRR', 5.0).split(',')
        # (ready, value, rate, atm, status, uncert)
        return (value[0]=='R',
            float(value[1].split()[0]),
            float(value[2].split()[0]),
            float(value[3].split()[0]),
            int(value[4]),
            float(value[5].split()[0]))

    def is_ready(self):
        """Read the next available Ready/Not Ready status"""
        value = self._command('SR', 5.0)
        return value == 'R'

    def stability_limit(self, limit=None):
        """Read or set the current presure stability limit.  The stability
        limit is used as the Ready/Not Ready criterion in static control mode
        and when the PPC4 not controlling."""
        if limit is None:
            value = self._command('SS')
        else:
            value = self._command('SS=%f' % limit)
        value = value.split(None, 1)
        return float(value[0])

    def unit(self, newunit=None, tempref=None):
        """Read or set the pressure unit of measure"""
        if newunit is None:
            return self._command('UNIT')
        elif tempref is None:
            self._command('UNIT=%sa' % newunit)
        else:
            self._command('UNIT=%sa,%d' % (newunit, tempref))

    def vent(self, flag=True):
        """Read, execute or abort a vent process"""
        if flag:
            self._command('VENT=1')
        else:
            self._command('VENT=0')

    def vented(self):
        """Read status of the vent process"""
        return self._command('VENT').startswith('VENT=1')

    def wait_ready(self, stable=None, timeout=None):
        """Waits for the PPC4 to raise the ready signal.
        
        If 'stable' is set, the ready signal just be held for a minimum of
        that duration.  If 'timeout' is set, an exception will be raised
        should the PPC not stabilize within the requested time."""
        # Convert timeouts to appropriate types
        if timeout:
            timeout = timedelta(0, timeout) + datetime.now()
        if stable:
            stable = timedelta(0, stable)
        # Timestamp of last moment of stability
        timestamp = datetime.now()
        # Stability test loop
        ready = False
        while not ready:
            if not self.is_ready():
                # Not ready so reset counter and check for timeout
                timestamp = datetime.now()
                if timeout and (timeout <= timestamp):
                    raise TimeoutError, "Time Out waiting for PPC4 to stabilize"
            elif not stable:
                # No stability delay, so quit immediately
                ready = True
            elif (timestamp + stable) <= datetime.now():
                # Wait for the stability delay
                ready = True

    def wait_pressure(self, newpressure=None, volume=None, stable=None,
            timeout=None, retries=3):
        """Sets the PPC4 pressure and waits for it to stabilize"""
        # The first retries
        for i in range(retries):
            try:
                # Set the pressure and wait
                self.pressure(newpressure, volume)
                self.wait_ready(stable, timeout)
                return
            except TimeoutError:
                # If the PPC screws up, vent and try again
                self.vent()
                while not self.vented():
                    pass
        # If we fail here, allow the error to propogate
        self.pressure(newpressure, volume)
        self.wait_ready(stable, timeout)
