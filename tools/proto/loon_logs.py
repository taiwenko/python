"""Regenerate and import the loon_logs_pb2.py file if needed."""


def _GenerateProtobuf():
  # Imports and constants under this function to not pollute the namespace.
  import os
  import subprocess
  import sys

  _SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
  _OUTPUT_PATH = os.path.join(_SCRIPT_PATH, 'release')
  _PROTO_FILE = os.path.join(_SCRIPT_PATH, 'loon_logs.proto')
  if not os.path.exists(_OUTPUT_PATH):
      os.makedirs(_OUTPUT_PATH)
      command = 'touch %s' % os.path.join(_OUTPUT_PATH, '__init__.py')
      if subprocess.call(command, shell=True) != 0:
        sys.exit('Python __init__.py module generation failed: %s' %
                 command)
  command = 'protoc --python_out=%s --proto_path=%s %s' % (
      _OUTPUT_PATH, _SCRIPT_PATH, _PROTO_FILE)
  if subprocess.call(command, shell=True) != 0:
    sys.exit('protobuf generation failed: %s' % command)

_GenerateProtobuf()

from release.loon_logs_pb2 import *
