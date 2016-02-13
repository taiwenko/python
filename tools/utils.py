import argparse
import os
import subprocess
import sys
import yaml

# This label is for the special case of running the tests on OSX which do not
# support detecting the PFC type.
PFC_TYPE_UNKNOWN = '_UNKNOWN'

_KNOWN_RESULTS_SINGLETON = None


def _parse_prompt_file(prompt_path):
  with open(prompt_path) as prompt_file:
    prompts = yaml.safe_load(prompt_file)
  assert isinstance(prompts, dict), 'prompt file must have mappings'
  for prompt, response in prompts.iteritems():
    print prompt, response
    _KNOWN_RESULTS_SINGLETON[prompt.strip()] = str(response).strip()


def _cache_known_results():
  global _KNOWN_RESULTS_SINGLETON
  if _KNOWN_RESULTS_SINGLETON is not None:
    return
  _KNOWN_RESULTS_SINGLETON = {}
  parser = argparse.ArgumentParser('Util file prompt responses')
  parser.add_argument('--prompt-responses', dest='prompt_responses',
                      help='Fills in prompts with responses from a YAML file.')
  args, _ = parser.parse_known_args()
  if not args.prompt_responses:
    return
  _parse_prompt_file(args.prompt_responses)


def _get_known_result(prompt):
  _cache_known_results()
  return _KNOWN_RESULTS_SINGLETON.get(prompt.strip(), None)


"""Utility functions."""
class DictAttrReadAdapter(dict):
    """Allows accessing a dictionary item as an attribute."""
    def __getattr__(self, attr):
        return self.__getitem__(attr)


def mt_bool(string):
    """Convert a string from Major Tom's bool notation to a python bool."""
    if string == 'true':
        return True
    if string == 'false':
        return False
    raise ValueError


def mt_apply_type(string):
    """Convert a pretty-printed string from Major Tom to a typed value."""
    # Objects that are None get no conversion.
    if string is None:
        return None

    # Otherwise, convert the string to a typed value.
    typed_val = None

    for cls in [mt_bool, float, int, str]:
        try:
            typed_val = cls(string)
            break
        except ValueError:
            pass
    if typed_val is None:
        typed_val = string

    return typed_val


def which(program):
    """Like the unix program 'which', walks PATH to find an executable"""
    def is_exe(fpath):
        """Does the path point to an executable file?"""
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def prompt_string(message, extra_message=None, iostream=sys.stdout):
    response = _get_known_result(message)
    if response is not None:
      return response
    iostream.write(message)
    if extra_message:
      iostream.write(' ')
      iostream.write(extra_message)
    return raw_input().strip()


def prompt_yes_no(message, iostream=sys.stdout):
    response = None
    while response not in ['y', 'n']:
        response = prompt_string(message, '(y/n) ', iostream).lower()
    return response == 'y'


def prompt_integer_range(message, lower_bound, upper_bound,
                         iostream=sys.stdout):
    response = None
    extra_message = '[%d..%d] ' % (lower_bound, upper_bound)
    while True:
        try:
            response = int(prompt_string(message, extra_message, iostream))
        except ValueError:
            continue
        if response >= lower_bound and response <= upper_bound:
            return response


# TODO(craigt): Replace this with a broader "enumerate payload" library, and
# feed that into --with-loon and flash.py.
def find_pfc_type():
    """Returns a tuple of the attached 'PFC' type and serial port device path.

    On Linux, the supported PFC types are:
        half_stack_hv_pfc - high voltage half stack PFC with half power board

    On OSX, the PFC type will always return PFC_TYPE_UNKNOWN since detecting
    the PFC type is not supported.

    This function is not supported on all other systems.
    """
    platform = sys.platform
    if platform == 'darwin':
        # As a basic technique for finding the PFC, use the highest labeled
        # serial port.
        from glob import glob
        port_list = glob('/dev/tty.usbserial*')
        if port_list:
            port_list.sort()
            return (PFC_TYPE_UNKNOWN, port_list[-1])
        else:
            return None

    elif platform == 'linux2':
        list_usb_path = os.path.join(os.path.dirname(__file__),
                                     '../openocd/list_usb.sh')

        p = subprocess.Popen([list_usb_path], stdout = subprocess.PIPE)
        out, err = p.communicate()
        maybe_hs_pfc = False
        for line in out.splitlines():
            if line == "0403|6010|loon|onboard|half_stack_hv_pfc":
                return ('half_stack_hv_pfc',
                        '/dev/serial/by-id/usb-loon_onboard_half_stack_hv_pfc-if01-port0')
            # TODO(craigt): Eliminate support for non-programmed eeproms
            if line == '0403|6010|FTDI|Dual RS232-HS|':
                maybe_hs_pfc = True
        if maybe_hs_pfc:
            return (PFC_TYPE_UNKNOWN,
                    '/dev/serial/by-id/usb-FTDI_Dual_RS232-HS-if01-port0')
        return None

    else:
        raise NotImplementedError('Cannot automatically find PFC on '
                                  'unsupported platform: %s.' % platform)
