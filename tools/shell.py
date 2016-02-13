"""Pythonic utility classes for interacting with the Major Tom shell."""
import pexpect
import sys
import time

import pexpect

from tools import utils
import tools.lazy as lazy

SHELL_ERROR_PREFIX = 'Command status'
SHELL_PROMPT = '\n> '
# Full or near full SD cards can cause the shell to respond in just over a
# second. Give the shell a bit extra time to remove false failures.
SHELL_TIMEOUT_DEFAULT = 1.5

# Woerms message counts are now updated only on Woerms heartbeats. This means
# that a report may legitimately be up to 2 seconds old. This constant defines
# the time to wait, including a little padding.
WOERMS_UPDATE_PERIOD = 2.5  # seconds


class ScoreboardTimeout(AssertionError):
    """Raised by a Scoreboard if a timed operation times out."""



class ScoreboardAssertion(AssertionError):
    """Raised by a Scoreboard if an assertion fails on a value predicate."""


class CommandRetriesExceeded(Exception):
    """Raised when sendline command retries exceeded."""


class StaleScoreboardEntryException(Exception):
    """Raised when a value or expression's age is above the limit."""


class CommandFailure(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
         return repr(self.value)


class AgeValuePair(object):
    """An age and value pair with name benefits."""

    def __init__(self, age, value):
        self.age = age
        self.value = value
        self._counter = 0

    def __iter__(self):
        self._counter = 0
        return self

    def next(self):
        if self._counter == 0:
            self._counter += 1
            return self.age
        elif self._counter == 1:
            self._counter += 1
            return self.value
        else:
            raise StopIteration

    def __repr__(self):
        if self.age is None:
            return '(None, %s)' % (str(self.value))
        return '(%0.2f, %s)' % (self.age, str(self.value))

    def _eval_age(self, maybe_pair):
        if isinstance(maybe_pair, AgeValuePair):
            return maybe_pair.age
        else:
            return 0

    def _eval_value(self, maybe_pair):
        if isinstance(maybe_pair, AgeValuePair):
            return maybe_pair.value
        else:
            return maybe_pair

    def __eq__(self, other):
        new_age = max(self._eval_age(other), self.age)
        new_value = self.value == self._eval_value(other)
        return AgeValuePair(new_age, new_value)

    def __ne__(self, other):
        new_age = max(self._eval_age(other), self.age)
        new_value = self.value != self._eval_value(other)
        return AgeValuePair(new_age, new_value)

    def __gt__(self, other):
        # If either value is None, override Python2's default behavior and
        # always return false.
        new_age = max(self._eval_age(other), self.age)

        other_val = self._eval_value(other)
        no_none_values = self.value is not None and other_val is not None
        new_value = self.value > other_val and no_none_values

        return AgeValuePair(new_age, new_value)

    def __lt__(self, other):
        # If either value is None, override Python2's default behavior and
        # always return false.
        new_age = max(self._eval_age(other), self.age)

        other_val = self._eval_value(other)
        no_none_values = self.value is not None and other_val is not None
        new_value = self.value < other_val and no_none_values

        return AgeValuePair(new_age, new_value)

    def __ge__(self, other):
        # If either value is None, override Python2's default behavior and
        # always return false.
        new_age = max(self._eval_age(other), self.age)

        other_val = self._eval_value(other)
        no_none_values = self.value is not None and other_val is not None
        new_value = self.value >= other_val and no_none_values

        return AgeValuePair(new_age, new_value)

    def __le__(self, other):
        # If either value is None, override Python2's default behavior and
        # always return false.
        new_age = max(self._eval_age(other), self.age)

        other_val = self._eval_value(other)
        no_none_values = self.value is not None and other_val is not None
        new_value = self.value <= other_val and no_none_values

        return AgeValuePair(new_age, new_value)

    def __and__(self, other):
        new_age = max(self._eval_age(other), self.age)
        new_value = int(self.value) & int(self._eval_value(other))
        return AgeValuePair(new_age, new_value)

    def __or__(self, other):
        new_age = max(self._eval_age(other), self.age)
        new_value = int(self.value) | int(self._eval_value(other))
        return AgeValuePair(new_age, new_value)

    def is_in(self, sequence):
        new_age = max(self._eval_age(sequence), self.age)
        new_value = self.value in sequence
        return AgeValuePair(new_age, new_value)


class LazyScoreboardEntry(lazy.LazyNamedValue):
    def __init__(self, sb, name, eval_func=None):
        self._sb = sb

        if not eval_func:
            self.age = LazyScoreboardEntry(sb,
                                           name + '.age',
                                           self._eval_age)
            self.raw_age_value = LazyScoreboardEntry(sb,
                                                     name + '.raw_age_value',
                                                     self._eval_raw_age_value)

            # By default, we only evaluate based on the value.
            eval_func = self._eval_age_value

        super(LazyScoreboardEntry, self).__init__(name, eval_func)

    def _eval_age(self):
        age, _ = self._sb.query_exact(self._name)
        return AgeValuePair(0, age)

    def _eval_raw_age_value(self):
        age, val = self._sb.query_exact(self._name)
        return AgeValuePair(age, val)

    def _eval_age_value(self):
        age, val = self._eval_raw_age_value()
        return AgeValuePair(age, utils.mt_apply_type(val))


class Scoreboard(object):
    """Proxy class for performing operations based on the MT scoreboard."""

    def __init__(self, shell, log):
        self._shell = shell
        self._log = log
        self._deadline = None

    def query(self, item=None):
        """Reads the scoreboard.

        If an item is given, then only the age and value for the items
        matching that substring are returned. Otherwise, return a mapping of all
        items from the current scoreboard snapshot.
        """
        sb_map = utils.DictAttrReadAdapter()
        data_pattern = '(\w+)\s*:\s+([0-9\.]+)\s+?([^\r\n]+?)?[\r\n]'
        none_pattern = '(\w+)\s*:\s+NONE[\r\n]'
        cmd = 'sb human'
        if item:
            cmd = cmd + ' %s' % item
        self._shell.sendline(cmd)

        while True:
            pat = self._shell.expect([SHELL_PROMPT, data_pattern, none_pattern])
            if pat == 0:
                break

            key = self._shell.match.group(1)
            age = None
            val = None

            if pat == 1:
                age = float(self._shell.match.group(2))
                val = self._shell.match.group(3)
                # val is really an empty string if it was not found.
                if val is None:
                  val = ''

            sb_map[key] = (age, val)

        return sb_map

    def query_exact(self, item):
        return self.query(item)[item]

    def process_predicate(self, predicate):
        """Evaluate a predicate and return a age/value tuple."""
        result = predicate()
        if isinstance(result, AgeValuePair): # This is age/value pair
            return (result.age, result.value)
        else:
            return (0, result)

    def __getattr__(self, attr):
        """Returns the value only for a given scoreboard item."""
        return LazyScoreboardEntry(self, attr)

    def human(self, query):
        """Returns the result of 'sb human' for some query as a map"""
        result = self.query(query)
        width = max([len(x) for x in result.keys()])
        fmt = ("  %%-%ds" % width) + "\t%s\t%s"
        for key, val in result.iteritems():
            self._log(fmt % (key, val[0], val[1]), deadline=self._deadline)

    def wait(self, predicate, timeout, max_age=WOERMS_UPDATE_PERIOD):
        """Waits until timeout for some predicate to become true."""
        start_time = time.time()
        self._deadline = start_time + timeout
        last_predicate = None
        age = 0
        unevaluated_predicate_str = str(predicate)
        try:
            while time.time() - start_time < timeout:
                age, value = self.process_predicate(predicate)
                pretty_predicate = str(predicate)
                if value and (age <= max_age or max_age is None):
                    self._log('=   %s' % pretty_predicate)
                    return
                if last_predicate is None:
                    self._log('Waiting for %s' % unevaluated_predicate_str)
                if pretty_predicate != last_predicate:
                    self._log('    %s' % pretty_predicate,
                              deadline=self._deadline)
                    last_predicate = pretty_predicate
            if age > max_age and max_age is not None:
                self._log('FAIL: %s; max allowable age: %0.3f' %
                          (str(predicate), max_age))
                raise StaleScoreboardEntryException, (
                    '%s; max age = %0.3f' % (repr(predicate), max_age))
            else:
                self._log('FAIL: %s' % str(predicate))
                raise ScoreboardTimeout, predicate
        finally:
            self._deadline = None

    def wait_for_change(self, predicate, timeout, max_age=WOERMS_UPDATE_PERIOD):
        """Waits until timeout for a predicate to change value."""
        age, original_value = self.process_predicate(predicate)
        self.wait(predicate != original_value, timeout)

    def check(self, predicate, max_age=WOERMS_UPDATE_PERIOD):
        age, value = self.process_predicate(predicate)
        if age > max_age and max_age is not None:
            raise StaleScoreboardEntryException, (
                '%s; max allowable age: %0.3f' % (repr(predicate), max_age))
        if not value:
            raise ScoreboardAssertion, predicate
        self._log('=   %r' % predicate)

class Shell(pexpect.spawn):
    """Utility methods for interacting with a Major Tom shell"""
    # Too many public methods inherited from pexpect. pylint: disable=R0904
    def __init__(self, device, log=None, serial_log=None):
        # Prefer picocom, fall back to cu.
        if utils.which('picocom'):
            cmd = 'picocom --nolock -b 115200 ' + device
            self._terminal_ready_str = 'Terminal ready.'
        else:
            cmd = 'cu -l %s -s 115200' % device
            self._terminal_ready_str = 'Connected.'

        super(Shell, self).__init__(cmd, timeout=SHELL_TIMEOUT_DEFAULT,
                                    logfile=serial_log)
        self._ready = False
        self._log_func = log
        self.scoreboard = Scoreboard(self, self.log)

        self._wait_for_ready()

    def __enter__(self):
        return self

    def __exit__(self, unused_type, unused_value, usused_traceback):
        self.close()

    def reset(self):
        """Move pexpect's read cursor up to the most recent prompt.

        Mainly used if the board was recently reset, creating multiple prompts
        """
        while (True):
            index = self.expect([pexpect.TIMEOUT, SHELL_PROMPT], timeout=1)
            if index == 0:
                break

    def vars(self):
        """Returns the result of the 'var' command.

        Returns a mapping of all built-in variables and their current values.
        """
        var_map = utils.DictAttrReadAdapter()
        var_pattern = '([\.\w]+)\t(.+?)\r'
        self.sendline('var')

        while self.expect([SHELL_PROMPT, var_pattern]):
            # Can't infer type of 'match.' pylint:disable=E1103
            key = self.match.group(1)
            try:
                val = int(self.match.group(2))
            except ValueError:
                val = self.match.group(2)
            var_map[key] = val
        return var_map

    def send_command(self, command, timeout=5):
        """Executes a command on the shell, expecting a prompt in response."""
        self.log('> ' + command)
        self.sendline(command)

        index = self.expect([SHELL_PROMPT, SHELL_ERROR_PREFIX], timeout=timeout)
        if index == 1:
            try:
                self.expect(SHELL_PROMPT, timeout=SHELL_TIMEOUT_DEFAULT)
            except:
                pass

            raise CommandFailure(command)

        return self.before

    def log(self, logstr, *args, **kwargs):
        """Logs an informative string."""
        if self._log_func:
            self._log_func(logstr, *args, **kwargs)
        else:
            print logstr

    def _wait_for_ready(self):
        """Handshaking with the underlying terminal program."""
        if not self._ready:
            self.expect(self._terminal_ready_str, timeout=15)
            self._ready = True
        return self

    def sendline(self, s=''):
        retries = 3
        while retries > 0:
            retries -= 1
            num_sent = self.send(s)
            if self.expect_exact([pexpect.TIMEOUT, s], timeout=0.25) == 1:
                self.send('\n')
                return
            self.log('Shell corruption! sent %r, received %r' %
                     (s, self.before))
            self.send('\b' * len(s))
        if sys.exc_info() == (None, None, None):
            raise CommandRetriesExceeded('Shell corruption too much!')
        else:
            self.log('Shell corruption too much; not throwing exception '
                     'because one is already being handled.')

    def power_cycle(self, time=None):
        if time is None:
            self.sendline('power cycle')
            timeout = 7
        else:
            self.sendline('power cycle %d' % time)
            timeout = time + 5
        self.expect('Diagnostic Shell Started', timeout=timeout)
        self.expect(SHELL_PROMPT, timeout=5)
