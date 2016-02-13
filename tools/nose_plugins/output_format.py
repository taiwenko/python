"""
This plugin formats nosetest's output to look pretty, ideally for field use. It
uses the test's docstring to identify tests to the user and clearly display
which tests passed and which tests fail.

The full test output is saved in the file passed through argument --loon-log.
This argument must be provided to enable this plugin.

Using this plugin without specifying a filename will cause test failure
information to be printed to the screen along with test name and status.

The argument -s must be used with this plugin to disable nosetest's built-in
output capture plugin. TODO(aaronfan): Make this implicit.

Example:

./nose_run -s --loon-log=test_logs/loon_log_file.txt --using=pfc,acs,apex
./nose_run -s --loon-log= --using=pfc,acs,apex

Plugin interface definition available at:

http://nose.readthedocs.org/en/latest/plugins/interface.html

"""
import os
import sys
import time
import tools.utils
import traceback

from StringIO import StringIO
from nose.plugins import Plugin
from nose.util import tolist

from tools.proto import loon_logs

# This plugin must load before nose's default capture plugin, which has a score
# of 1600
PLUGIN_SCORE = 1700

PASS_NOFMT = '[OK]'
FAIL_NOFMT = '[FAIL]'
PASS = PASS_NOFMT
FAIL = FAIL_NOFMT
ALL_PASS = 'All tests pass -- GO!'
ALL_FAIL = 'Tests failed. NO-GO!'

try:
    from blessings import Terminal
    term = Terminal()
    PASS = '{t.bold}{t.white}[{t.green}OK{t.white}]{t.normal}'.format(t=term)
    FAIL = '{t.bold}{t.white}[{t.red}FAIL{t.white}]{t.normal}'.format(t=term)
    ALL_PASS = '{t.bold}{t.green}All tests pass -- GO!{t.normal}'.format(t=term)
    ALL_FAIL = '{t.bold}{t.red}Tests failed. NO-GO!{t.normal}'.format(t=term)

except ImportError:
    print 'Package blessings not found, output will not be formatted.'

TITLE_HEADER = '\n' + '*' * 80

stream = None
current_test_pb = None

def _GetNowInMilliseconds():
    return int(time.time() * 1000.0)


def nose_prompt_yes_no(message):
    if stream is None:
        ret = tools.utils.prompt_yes_no(message)
    else:
        ret = tools.utils.prompt_yes_no(message, stream)
    proto_log('Prompted: "%s"; Response: %s' % (
            message, 'YES' if ret else 'NO'))
    return ret


def nose_print_message(message):
    proto_log(message)
    if stream is None:
        print message
    else:
        stream.writeln(message)


def proto_log(message, deadline=None):
    if not current_test_pb:
        return
    logmsg = current_test_pb.log.add(message=message,
                                     timestamp=_GetNowInMilliseconds())
    if deadline:
        logmsg.deadline = deadline * 1000


def _GetFallbackTestVersion(base_path):
    try:
        import tools.package
    except ImportError:
        # git is probably not available if we don't have package.
        return 'unknown-version'
    return tools.package.GetGitDescriptor(base_path)


def _GetTestVersion():
    base_path = os.path.join(os.path.dirname(__file__), '..', '..')
    version_file = os.path.join(base_path, 'version')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            return f.read().strip()
    else:
        return _GetFallbackTestVersion(base_path)


class LoonOutput(Plugin):
    name = 'loon'
    score = PLUGIN_SCORE
    # Used by nose to determine whether to use this plugin or not
    enabled = False

    def __init__(self):
        super(LoonOutput, self).__init__()
        self.orig_stdout = None
        self.stdout_stack = []
        self.context_stack = []
        self.log_to_file = False
        self.log_pb = None
        self.collect_only = False

    def _WriteTestProto(self, metadata=None, test=None):
        assert metadata or test, 'must pass metadata or test parameters'
        if not self.log_pb:
            return
        pb = loon_logs.TestRun()
        if metadata:
            pb.metadata.CopyFrom(metadata)
        if test:
            pb.test.extend([test])
        self.log_pb.write(pb.SerializeToString())
        self.log_pb.flush()

    def options(self, parser, env):
        """Register command line options"""
        parser.add_option('--loon-log',
                          dest='loon_log_file', action='store',
                          default=None,
                          metavar='COMP',
                          help='Loon log filename. '
                               'No argument will print errors to stdout.')
        parser.add_option('--loon-log-proto',
                          dest='loon_log_proto_file', action='store',
                          default=None,
                          help='Loon log protobuf file for machine readable '
                               'logs. Protobuf logging disabled if not '
                               'specified. This still requires normal logging.')
        parser.add_option('--loon-unit-id',
                          dest='loon_unit_id', action='store',
                          default=env.get('LOON_UNITID'),
                          help='Loon Unit id.')
        parser.add_option('--loon-tested-by',
                          dest='loon_tested_by', action='store',
                          default=None,
                          help='Identifier for the tester performing this '
                               'test run.')

    def _GetComponents(self, components):
        if not components:
            return []
        return tolist(components)

    def _ConfigureProtoLog(self, options):
        log_pb_name = options.loon_log_proto_file
        if not log_pb_name:
            return
        log_pb_name = log_pb_name.strip()
        if not log_pb_name:
            return
        self.log_pb = open(log_pb_name, 'wb')
        testrun_data = loon_logs.TestRunMetadata()
        assert options.loon_unit_id, (
            'Loon unit id required with proto logging')
        testrun_data.unit.id = options.loon_unit_id
        testrun_data.component.extend(self._GetComponents(options.components))
        testrun_data.timestamp = int(time.time())
        testrun_data.tested_by = options.loon_tested_by
        testrun_data.version = _GetTestVersion()
        self._WriteTestProto(metadata=testrun_data)

    def configure(self, options, config):
        log_name = options.loon_log_file
        if log_name is None:
            return

        self.enabled = True

        # Try to disable nosetest's default log capture plugin
        options.capture = False
        if not log_name.strip():
            self.log = None
            self.log_name = None
        else:
            self.log_to_file = True
            self.log_name = log_name
            directory = os.path.dirname(log_name)
            if directory and not os.path.exists(directory):
                raise AssertionError('Output directory not found')
            self.log = open(log_name, 'a')
            self.log.write('Version: %s\n' % _GetTestVersion())

        self._ConfigureProtoLog(options)

        if hasattr(options, 'collect_only'):
            self.collect_only = options.collect_only

    def _RecordTestProto(self):
        global current_test_pb
        if not (self.log_pb and current_test_pb):
            return
        current_test_pb.end_timestamp = _GetNowInMilliseconds()
        self._WriteTestProto(test=current_test_pb)
        current_test_pb = None

    def addSuccess(self, unused_test):
        global current_test_pb
        if self.collect_only:
          return
        stream.writeln(PASS)
        if self.log_to_file:
            self.log.write(PASS_NOFMT + '\n')
            self.log.write(sys.stdout.getvalue())
        sys.stdout = self.stdout_stack.pop()
        if self.log_pb and current_test_pb:
            current_test_pb.status = loon_logs.TEST_PASSED

    def addError(self, unused_test, error):
        self.saveError(error)

    def addFailure(self, unused_test, error):
        self.saveError(error)

    def saveError(self, error):
        global current_test_pb
        stream.writeln(FAIL)
        exception_type, value, traceback_data = error
        error_string = ''.join(traceback.format_exception(exception_type,
                                                          value,
                                                          traceback_data))
        if self.log_pb and current_test_pb:
            current_test_pb.exception_dump = error_string
            current_test_pb.status = loon_logs.TEST_FAILED

        if hasattr(sys.stdout, 'getvalue'):
            error_string += sys.stdout.getvalue()

        if self.log_to_file:
            self.log.write(FAIL_NOFMT + '\n\n')
            self.log.write(error_string)
            stream.writeln('    Cause: ' + str(value).split('\n', 1)[0])
        else:
            stream.write(error_string)
        sys.stdout = self.stdout_stack.pop()

    def afterTest(self, unused_test):
        if self.log_to_file:
            self.log.flush()
        self._RecordTestProto()

    def begin(self):
        self.orig_stdout = sys.stdout
        sys.stdout = StringIO()

    def finalize(self, result):
        if self.log_to_file:
            self.log.write(TITLE_HEADER)
            self.log.write(
                '\nSummary: %d tests run, %d failing, %d errors\n'
                 %(result.testsRun, len(result.failures), len(result.errors)))
        if self.log_pb:
            self.log_pb.close()

        if self.log_name:
            stream.writeln('')
            stream.writeln('Log file path: %s' % os.path.realpath(self.log_name))
            stream.writeln('')

        if len(result.errors) == 0 and len(result.failures) == 0:
            stream.writeln(ALL_PASS)
        else:
            stream.writeln(ALL_FAIL)

        # Restore stdout.
        sys.stdout = self.orig_stdout

    def setOutputStream(self, output_stream):
        global stream
        # Grab for own use.
        stream = output_stream
        # Return dummy stream to hide unwanted output. This way, only the test
        # name and test results are printed, while scoreboard and shell commands
        # are hidden.
        class dummy:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
            def flush(self):
                pass
        dummy_instance = dummy()
        return dummy_instance

    def startContext(self, context):
        self.context_stack.append(context)
        self.stdout_stack.append(sys.stdout)
        sys.stdout = StringIO()

        if self.log_to_file and len(self.context_stack) == 1:
            sys.stdout.write(TITLE_HEADER)
            sys.stdout.write('\nSet Up Actions\n')

    def stopContext(self, context):
        self.context_stack.pop()
        sys.stdout = self.stdout_stack.pop()

        if self.log_to_file and len(self.context_stack) == 1:
            sys.stdout.write(TITLE_HEADER)

    def startTest(self, test):
        # Capture stdout
        self.stdout_stack.append(sys.stdout)
        sys.stdout = StringIO()

        if self.collect_only:
            stream.write(test.id())
            stream.write('\n')
            return

        # Print test name to screen and log
        shortname = test.shortDescription() or str(test)
        shortname = shortname[:70]

        stream.write('%-70s  ' % shortname)

        if self.log_to_file:
            self.log.write(TITLE_HEADER)
            self.log.write('\n%-70s  ' % shortname)

        if self.log_pb:
            global current_test_pb
            current_test_pb = loon_logs.Test(
                    name=str(test), description=shortname,
                    start_timestamp=_GetNowInMilliseconds())
