#!/usr/bin/python
"""Flash Major Tom firmware and execute basic health tests.

This script brings the Major Tom firmware on an attached stack into
sync with the current git hash, then eexecutes basic health checks
to ensure the flash was successful.
"""
import argparse
import os
import subprocess
import sys
import threading
import time

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(base_dir)
from tools import shell
from tools import utils

WAIT_FOR_SCOREBOARD_SECONDS = 2.0


def print_prefixed_output(prefix, output):
  prefix = "%s: " % prefix
  prefixed_output = [prefix + line for line in output.split('\n')]
  print "\n".join(prefixed_output)


def flash_board(board, firmware_dir):
  """Flash the board."""
  print >>sys.stderr, 'Flashing %s...' % board

  app_dir = os.path.join(firmware_dir, 'src/app/%s' % board)
  make_app = os.path.join(app_dir, 'release/%s' % board)
  cobble_app = os.path.join(app_dir, board)

  if os.path.isfile(make_app):
    app_path = make_app
  elif os.path.isfile(cobble_app):
    app_path = cobble_app
  else:
    raise Exception(
        'Cannot find app file for %s in %s' % (board, firmware_dir))

  # OpenOCD cannot handle long pathnames.
  app_path = os.path.relpath(app_path)
  openocd_cfg = os.path.relpath(
      os.path.join(base_dir, 'src', 'app', board, 'openocd.cfg'))
  cmd = ['openocd', '-f', openocd_cfg,
         '-c', 'gdb_port 0',
         '-c', 'tcl_port 0',
         '-c', 'telnet_port 0',
         '-c', 'init',
         '-c', 'reset init',
         '-c', 'flash write_image erase %s' % app_path,
         '-c', 'reset halt',
         '-c', 'resume',
         '-c', 'shutdown']

  print >>sys.stderr, '\tUsing Command: %s' % ' '.join(cmd)

  try:
    # Although we are pulling firmware images out of firmware_dir, we want
    # to pull the openocd cfg from the current tree.
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                     cwd=base_dir)
    print_prefixed_output(board, output)
  except subprocess.CalledProcessError as e:
    print_prefixed_output(board, e.output)
    raise


class BoardFlasher(threading.Thread):
  def __init__(self, board, firmware_dir):
    self._board = board
    self._firmware_dir = firmware_dir
    super(BoardFlasher, self).__init__()

  def run(self):
    try:
      flash_board(self._board, self._firmware_dir)
      self.had_error = False
    except Exception as e:
      self.had_error = True
      raise

  def final_status(self):
    if self.had_error:
      print '** Board %r failed to flash! **' % self._board
    else:
      print 'Board %r flashed successfully.' % self._board


def maybe_power_on(boards_to_flash, pfc_shell, pfc_type, firmware_dir):
  if pfc_shell and pfc_type:
    print 'Powering on...'
    try:
      pfc_shell.send_command('power on acs apex')
      time.sleep(WAIT_FOR_SCOREBOARD_SECONDS)
    except:
      if pfc_type in boards_to_flash:
        print 'Error while powering on, reflashing PFC.'
        flash_board(pfc_type, firmware_dir)
        boards_to_flash.remove(pfc_type)
        time.sleep(WAIT_FOR_SCOREBOARD_SECONDS)
        try:
          pfc_shell.send_command('power on acs')
          time.sleep(WAIT_FOR_SCOREBOARD_SECONDS)
        except:
          print 'Still failed to power on hans.'

def parallel_flash(boards_to_flash, firmware_dir):
  assert boards_to_flash, (
      'Cannot identify boards to flash; must specify with --board')

  pfc_tuple = utils.find_pfc_type()
  detected_pfc_type, pfc_shell_device = (None, None)
  if pfc_tuple:
    detected_pfc_type, pfc_shell_device = pfc_tuple

  pfc_count = 0
  expected_pfc_type = None
  if 'half_stack_hv_pfc' in boards_to_flash:
      pfc_count += 1
      expected_pfc_type = 'half_stack_hv_pfc'

  assert pfc_count <= 1, 'Must specify at most one PFC type.'

  # Flashing a PFC device is requested, so try to verify the PFC attached
  # matches the specified PFC type.
  if pfc_count == 1:
    assert detected_pfc_type, 'Cannot flash pfc, no device found'

    if detected_pfc_type != utils.PFC_TYPE_UNKNOWN:
      assert detected_pfc_type == expected_pfc_type, (
          'Mismatch between actual and expected pfc type.')

  sh = None
  if pfc_shell_device:
    try:
      sh = shell.Shell(pfc_shell_device)
    except Exception:
      print >>sys.stderr, 'Unable to connect to PFC Shell!!!!!'
      sys.exit(1)

  maybe_power_on(boards_to_flash, sh, expected_pfc_type, firmware_dir)

  print 'Flashing boards: %s' % boards_to_flash
  flashing_threads = []
  for board in boards_to_flash:
    flashing_threads.append(BoardFlasher(board, firmware_dir))

  # Flash the boards in parallel.
  for thread in flashing_threads:
    thread.start()
  error = False
  for thread in flashing_threads:
    thread.join()
    error = error or thread.had_error
  # Final report in one place
  for thread in flashing_threads:
    thread.final_status()
  if error:
    sys.exit(1)


def order_boards(boards):
  ret_boards = []
  # Find PFC boards.
  leftover_boards = []
  for board in boards:
    if 'pfc' in board:
      ret_boards.append(board)
    else:
      leftover_boards.append(board)
  return ret_boards + leftover_boards


def prompt_and_flash_boards(boards_to_flash, firmware_dir, disable_prompt):
  flashed_boards = []
  try:
    for board in boards_to_flash:
      if disable_prompt or utils.prompt_yes_no(
          'Do you want to flash the %r board' % board):
        flash_board(board, firmware_dir)
        flashed_boards.append(board)
  finally:
    print 'Successfully flashed boards: %s' % flashed_boards


def sequential_flash(boards_to_flash, available_boards, firmware_dir,
                     force_single):
  if not boards_to_flash:
    boards_to_flash = available_boards
  boards_to_flash = order_boards(boards_to_flash)

  print """\
Prior to powering up anything please ensure the PFC's Iridium connection
a dummy load or antenna attached. Also, don\'t connect/disconnect
flash cable while the circuits are powered up.  Remove power
first."""

  disable_prompt = force_single and len(boards_to_flash) == 1
  prompt_and_flash_boards(boards_to_flash, firmware_dir, disable_prompt)


def get_board_choices():
  # TODO(arsharma): Maybe introduce a set of boards to ignore.
  base_app_dir = os.path.join(base_dir, 'src', 'app')
  possible_boards = os.listdir(base_app_dir)

  boards = []
  for possible in possible_boards:
    full_possible = os.path.join(base_app_dir, possible)
    if os.path.isdir(full_possible):
      boards.append(possible)
  return boards


def main(argv=None):
  """Main entry point."""
  os.chdir(base_dir)

  if argv is None:
    argv = sys.argv

  available_boards = get_board_choices()

  parser = argparse.ArgumentParser(description='flash and sanity check')
  parser.add_argument(
      '--board', nargs='+', choices=available_boards,
      help='subset of boards to flash; will fail if selected boards are not '
           'attached.')
  parser.add_argument(
      '--firmware_dir', default=base_dir,
      help='Specify the directory from which firmware files should be '
           'retrieved. E.g. set this to a major_tom or cobble/latest '
           'directory.  Required if firmware has been selected for packaging.')
  parser.add_argument(
      '--parallel', default=False, action='store_true',
      help='Flash in parallel mode; defaults to a sequential mode with '
           'prompting.')
  parser.add_argument(
      '--force_single', default=False, action='store_true',
      help='When sequential mode, disable prompting if there is a single '
           'board.')
  args = parser.parse_args(argv[1:])

  if args.parallel:
    parallel_flash(args.board, args.firmware_dir)
  else:
    sequential_flash(args.board, available_boards, args.firmware_dir,
                     args.force_single)


if __name__ == '__main__':
  main()
