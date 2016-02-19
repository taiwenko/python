"""VXI-11 (VISA) SCIPI over TCPIP Wrapper.

Copyright (c) 2014 The Project Loon Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file
"""
__author__ = "Alfred Cohen"
__email__ = "alfredcohen@google.com"

import os
import re

import vxi11Device as vxi11
import logs

logger = None


class VisaWrapper(object):
  """Initialize the VXI-11 VISA Wrapper Class."""

  def __init__(self, cfg=None, log_level=logs.ERROR):
    """Initialize the Instrument.

    Args:
      cfg: Holds connectivity and settings parameters.
           cfg = { "connection": {"name": "VSA",
                            "use": True,
                            "protocol": "visa",
                            "addr": "10.0.0.189",
                            "debug": False,
                            "timeout": 20
                            },
                    "cfg": {"Freq": "2110",
                            "BW": "10",
                            "ExtAtt": "49",
                            "Duplex": "FDD",
                            "Dir": "DL"
                            }
                  }
      log_level: one of logging.levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global logger
    logger = logs.get_log("VisaWrap", level=log_level)
    self.inst = None
    self.drv = None
    self.set_error()
    if not cfg:
      self.set_error("No Configuration parameters provided.")
      return
    self.cfg = cfg
    if "connection" not in cfg or not cfg["connection"]:
      self.set_error("Connectivity Parameters not provided")
      return
    con = cfg["connection"]
    self.debug = con.get("debug", False)
    self.ip_address = str(con.get("addr", "127.0.0.1"))
    self.timeout = con.get("timeout", 15)
    self.instance = str(con.get("instance", "inst0"))

    try:
      self.inst = vxi11.Vxi11Device(self.ip_address, self.instance)
      vxi11.timeout(self.timeout)
    except Exception:
      self.set_error("Initialization error, IP:%s"%self.ip_address)
      return

  # TODO(alfredcohen): Figure out if we need to close the client properly,
  #                    upon abnormal shutdown
  def __del__(self):
    self.close()
    return

  def close(self):
    """Issue Client Close Command (if needed?)."""
    if self.inst:
      vxi11.clnt_destroy(self.inst.clnt)
    return

  def get_error(self):
    """Get the last known Error."""
    return self.__lasterror

  def set_error(self, err=""):
    """Set the last known Error!"""
    self.__lasterror = err
    if err:
      logger.error("%s: %s"%(self.drv, err))

  def get(self, cmd):
    """Generic SCPI Read (Ask)."""
    self.set_error()
    if not self.inst:
      self.set_error("Read, Cannot access: %s"%self.ip_address)
      return ""
    logger.debug("%s Read Command: %s"%(self.drv, cmd))
    try:
      res = self.inst.ask(cmd)
    except Exception, e:
      self.set_error("%s Read Exception [%s]"%(self.drv, str(e)))
      return ""
    if not res:
      logger.debug("%s Command %s did not return any results"%(self.drv, cmd))
    return res.rstrip()

  def set(self, cmd):
    """Generic SCPI Write."""
    self.set_error()
    if not hasattr(self, "inst"):
      self.set_error("Write, Cannot access : %s"%self.ip_address)
      return False
    logger.debug("%s Write Command: %s"%(self.drv, cmd))
    try:
      self.inst.write(cmd)
    except Exception, e:
      self.set_error("Write Exception [%s]"%str(e))
      return False
    return True

  def geta(self, cmd):
    """Convert the SCIPI output to array from from comma separated string.

    If additional type conversion is required (Ex: float,int),
    needs to be done in calling function
    Args:
      cmd: SCIPI Command
    Returns:
      Quote stripped list result
    """
    res = self.get(cmd)
    if not res:
      return []
    # Get rid of quotes
    if re.match("^\"(.+)\"$", res):
      res = re.sub(r"\"", "", res)
    return  res.split(",")

  def idn(self):
    """Obtain Device Identification Array."""
    return self.geta("*IDN?")

  def __namecleanup(self, name):
    """Get rid of special chars from IDN string and use first word=Vendor."""
    pattern = re.compile("^([a-zA-Z_0-9]+)$")
    if not re.match(pattern, name):
      name = re.sub(r"^([a-zA-Z_0-9]+).+", "\\1", name)
    return re.sub(r"\s|\n|\t", "", name)

  def getdriver(self):
    """Create Driver name based on vendor and model."""
    idn = self.idn()
    if not idn:
      logger.warning("IDN not found %s.")
      return
    vendor = self.__namecleanup(idn[0])
    model = self.__namecleanup(idn[1])
    self.vendormodel = vendor + model
    return self.vendormodel

  def open_driver(self):
    """Find Driver based on the specific model and load it!"""
    drv = self.getdriver()
    if not drv:
      logger.warning("Driver name cannot be identified.")
      return False
    drvfile = "%s.py"%drv
    drvpath = os.path.join(os.path.dirname(__file__), drvfile)
    if not os.path.isfile(drvpath):
      self.set_error("Driver %s not found!"%drv)
      return False
    self.drv = drv
    module = __import__(drv)
    if not module:
      logger.warning("Driver %s cannot be imported/not found!"%drv)
      return False
    self.drv = module.Driver(self, self.cfg)
    return self.drv

  def getcmd(self, p="", cfg=None):
    """Obtain the equipment SCIPI Command (maps param to Driver specific)."""
    if not p:
      return
    # Obtain Parameter Mappings from the driver
    params = self.drv.get_params()
    # Use the supplied config or the driver config
    cfg = cfg if cfg else self.drv.cfg
    # Skip this command if no parameter mapping available
    if p not in params:
      return
    # Skip this command parameter not part of configuration
    if p not in cfg:
      return
    par = params[p]
    cmd = par["p"]
    # Assign Value as specified in the configuration
    val = str(cfg[p])
    # Override value of specific mapping is available per param & driver
    if "v" in par and val in par["v"]:
      val = par["v"][val]
    # Append Units if available per driver
    if par.has_key("u"):
      val += par["u"]
    # Return Full SCIPI Command
    logger.debug("Get SCIPI cmd: %s%s"%(cmd, val))
    return cmd + val

  def get_measure(self, retries=1):
    """Redirect Measurement to driver.

    Args:
        retries: Number of attempts to perform the measurment
    Returns:
        (MeasurementDataStructure, Success)
    """
    if not hasattr(self.drv, "get_measure"):
      logger.warning("Get measure not defined in driver.")
      return ({}, False)
    res = {}
    ok = False
    for x in range(retries):
      res, ok = self.drv.get_measure()
      logger.debug("Get measure read: %s (retry: %s/%s)"%(ok, x+1, retries))
      if ok:
        break
    return (res, ok)

  def action(self, *args):
    """Redirect to execute the default driver action."""
    if not hasattr(self.drv, "action"):
      logger.warning("%s Driver does not support default action!"%self.drv)
      return
    return self.drv.action(*args)

  def set_mode(self, mode=""):
    """Find Mode/Bundle of commands definition and issue mode configuration."""
    logger.debug("%s Setting Mode/Batch: %s"%(self.drv, mode))
    if not mode:
      logger.warning("Set Mode bundle %s, not specified."%mode)
      return False
    if mode not in self.cfg:
      logger.warning("Set Mode bundle %s, not found in cfg."%mode)
      return False
    # Iterate over all mode parameters and configure accordingly
    modecfg = self.cfg[mode]
    ok = []
    if not modecfg:
      logger.warning("Set Mode bundle %s, empty configuration."%mode)
      return False
    for param, val in modecfg.items():
      # Perform a Driver Specific command override if such a function exists
      # the format is set_paramname (lowercase)
      driverfunc = "set_%s"%param.lower()
      logger.debug("Set Mode bundle %s, Calling driver function %s."%(
          mode, driverfunc))
      if hasattr(self.drv, driverfunc):
        drvfunc = getattr(self.drv, driverfunc)
        ok.append(drvfunc(val))
      # Perform a configuration set as provided in the config file
      else:
        cmd = self.getcmd(param, modecfg)
        if not cmd:
          logger.debug("Set Mode %s, param cmd not found: %s, skipping..."%(
              mode, param))
          # SKIP Commands that are specified in the config
          # but not a matching SCIPI Commands is found
          # TO RE-ENABLE: ok.append(False)
          continue
        cmdok = self.set(cmd)
        logger.debug("Set Mode Command: %s, returned: %s"%(cmd, cmdok))
        ok.append(cmdok)
    return all(ok)
