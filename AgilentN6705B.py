"""Agilent N6705B Power Supply SCIPI Class.

Copyright (c) 2014 The Project Loon Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file
"""
__author__ = "Alfred Cohen"
__email__ = "alfredcohen@google.com"

import time


class Driver(object):
  """Agilent N6705B Power Supply - Driver specific Class."""

  def __init__(self, inst, cfg=None):
    """Initialize the specific driver."""
    self.i = inst
    if not cfg:
      self.i.set_error("Configuration File for this instrument not available")
      return
    self.cfg = cfg["cfg"]
    self.power = cfg["power"]

  def __del__(self):
    """Destroy and cleanup/shutdown power."""
    self.set_power(0)
    return

  def get_params(self):
    """Dictionary holding all driver specific parameter mappings.

    Returns:
      Structure in the format:
      PARM: p = "SCIPI:PARAMETER",
            u = "Units" to append,
            v = "param = paramdevice"
    """
    return {
        "Volt": {"p": "VOLT "},
        "Curr": {"p": "CURR "},
        "VoltMax": {"p": "VOLT:PROT:LEV "},
        "CurrMax": {"p": "CURR:PROT:LEV "}
        }

  def setup(self):
    """Set-up the device according to the supplied configuration."""
    # Prevent resetting parameters if specific configuration setting exists.
    if "no_setup" in self.cfg and self.cfg["no_setup"]:
      return True
    ok = []
    self.i.set("*RST")
    seq = self.get_channels("list", all=True)
    for ch in seq:
      chan = str(ch)
      for param in self.cfg[chan]:
        cmd = self.getcmd(param, chan)
        if not cmd:
          continue
        res = self.i.set(cmd)
        if res:
          ok.append(True)
        else:
          ok.append(False)
    self.i.get("*OPC?")
    return all(ok)

  def getcmd(self, p="", ch=""):
    """Use the Global Wrapper to get full SCIPI Command for the parameter."""
    if not p:
      return
    channel = ("" if not ch else ", (@%s)"%ch)
    cmd = self.i.getcmd(p, self.cfg[str(ch)])
    if not cmd:
      return
    return cmd + channel

  def set_power(self, on=0, chnls=None):
    """Turn Power On/Off for all power channels or selected ones."""
    ok = []
    mode = "ON " if on == 1 else "OFF "
    seq = chnls if chnls else self.get_channels("list")
    if on == 0:
      seq = reversed(seq)
    delay = 0.8 if "delay" not in self.power else self.power["delay"]
    for ch in seq:
      res = self.i.set("OUTP %s, (@%s)"%(mode, ch))
      ok.append(res)
      time.sleep(delay)
    return all(ok)

  def get_channels(self, mtype="str", all=True):
    """Obtain All configured Channels in order and return a list or string."""
    seq = self.power["seq"] if "seq" in self.power else []
    if all and "main" in self.power:
      if self.power["main"] not in seq:
        seq.append(self.power["main"])
    return ",".join(map(str, seq)) if mtype is "str" else seq

  def get_meas(self, mtype="VOLT"):
    """Perform Measurement of the specified type for the used channels."""
    cmd = "OUTP?" if mtype == "ON" else "MEAS:%s?"%mtype
    vals = self.i.geta("%s (@%s)"%(cmd, self.get_channels("str", all=True)))
    data = []
    if not vals:
      return data
    for v in vals:
      newval = int(v) if mtype == "ON" else float(v)
      data.append(newval)
    return data

  def action(self, *args):
    """Perform Default Driver Action. In this case Turn on/off power."""
    return self.set_power(*args)

  def get_measure(self):
    """Perform a complete measurement, with all most important readings."""
    ok = []
    res = {}
    self.i.set_error()
    raw = {}
    for q in ("VOLT", "CURR", "ON"):
      meas = self.get_meas(q)
      ok.append(bool(meas))
      raw[q] = meas

    if not all(ok):
      self.i.set_error("Measurement Read Fail: OK=%s/%s (%s)"%
                       (sum(ok), len(ok), self.i.get_error()))
      return ({}, False)

    chans = self.get_channels("list")
    for ch in chans:
      key = self.cfg[str(ch)]["name"]
      idx = chans.index(ch)
      res[key] = {"Volt": raw["VOLT"][idx],
                  "Curr": raw["CURR"][idx],
                  "Watt": raw["VOLT"][idx] * raw["CURR"][idx],
                  "On": raw["ON"][idx]
                 }
    return (res, all(ok))
