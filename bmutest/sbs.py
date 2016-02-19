import smbus
from datetime import date, timedelta
from struct import pack, unpack

class Error(Exception):
  """Base class for SBS exceptions"""
  pass
class InvalidValueError(Error):
  """Raised when the value of an SBS property is not valid for the current
  battery state.
  """
  pass

class Device(smbus.Device):
  #
  # Lifecycle
  #
  """Helper class for interaction with SBS devices"""
  def __init__(self, bus=None, addr=0x0B):
    """Initializes a new instance of the SBS class.
    
    Keyword Arguments:
    bus  -- SMBus driver to use.  Creates a new instance by default.
    addr -- Slave address for the SBS device (default 0x0B)
    """
    if bus is None:
      bus = smbus.Bus()
    smbus.Device.__init__(self, bus, addr)
    self._reinit()
  def _reinit(self):
    """(Protected) Reinitializes cached register values in case of register or
    firmware changes.
    """
    specinfo = self.SpecificationInfo()
    self._vscale = specinfo['vscale']
    self._ipscale = specinfo['ipscale']
    self.BatteryMode()
  #
  # Protected Helper Methods
  #
  def _voltage(self, word):
    """(Protected) Converts and scales a voltage retrieved from a register
    access.
    """
    return word / 1000.0 * self._vscale
  def _current(self, word):
    """(Protected) Converts and scales a current retrieved from a register
    access.
    """
    return word / 1000.0 * self._ipscale
  def _capacity(self, word):
    """(Protected) Converts and scales a capacity retrieved from a register
    access.
    """
    if self._capm:
      # CAPM set: data reports in 10 mWh
      return (word / 1E2 * self._ipscale, 'Wh')
    else:
      # CAPM clear: data reports in 1 mAh
      return (word / 1E3 * self._ipscale, 'Ah')
  def _temperature(self, word):
    """(Protected) Converts and scales a temperature retrieved from a register
    access.
    """
    return word / 10.0
  #
  # Core SBS Commands
  #
  def BatteryMode(self, **kwargs):
    """Gets or sets the battery mode (register 0x03).  The mode word is
    expanded into named values in a dict.

    Keyword Arguments (Settable):
    CAPM -- Capacity Mode (True for W*h, False for A*h)
    CHGM -- Charger Mode (True to disable charger broadcasts)
    AM   -- Alarm Bit (True to disable alarm broadcasts)
    PB   -- Primary Battery (True if the battery is in a secondary role)
    CC   -- Charge Controller Enabled

    Keyword Arguments (Read-only):
    CF   -- True when a battery conditioning cycle is active
    PBS  -- Primary Battery Support (True if supported)
    ICC  -- Internal Charge Controller (True if supported)
    """
    mode = self.read_word(0x03)
    # Set/Clear bits as requested
    if len(kwargs) > 0:
      if 'CAPM' in kwargs:
        if kwargs['CAPM']:
          mode = mode |  0x8000
        else:
          mode = mode & ~0x8000
      if 'CHGM' in kwargs:
        if kwargs['CHGM']:
          mode = mode |  0x4000
        else:
          mode = mode & ~0x4000
      if 'AM' in kwargs:
        if kwargs['AM']:
          mode = mode |  0x2000
        else:
          mode = mode & ~0x2000
      if 'PB' in kwargs:
        if kwargs['PB']:
          mode = mode |  0x0200
        else:
          mode = mode & ~0x0200
      if 'CC' in kwargs:
        if kwargs['CC']:
          mode = mode |  0x0100
        else:
          mode = mode & ~0x0100
      self.write_word(0x03, mode)
    # Use this opportunity to keep CAPM up to date
    self._capm = bool(mode & 0x8000)
    return {
        'CAPM': bool(mode & 0x8000),
        'CHGM': bool(mode & 0x4000),
        'AM':   bool(mode & 0x2000),
        'PB':   bool(mode & 0x0200),
        'CC':   bool(mode & 0x0100),
        'CF':   bool(mode & 0x0080),
        'PBS':  bool(mode & 0x0002),
        'ICC':  bool(mode & 0x0001)
    }
  def Temperature(self):
    """Measures the battery temperature (Kelvin)."""
    return self._temperature(self.read_word(0x08))
  def Voltage(self):
    """Measures the aggregate battery output voltage (Volts)."""
    return self._voltage(self.read_word(0x09))
  def Current(self):
    """Measures the battery output current (Amps).  Negative values indicate
    discharge while positive values indicate charge."""
    return self._current(self.read_word_signed(0x0A))
  def AverageCurrent(self):
    """Measures the battery output current (Amps) as averaged over the
    previous minute.  Negative values indicate discharge while positive values
    indicate charge."""
    return self._current(self.read_word_signed(0x0B))
  def MaxError(self):
    """Returns the expected margin of error in the State of Charge estimates
    (Percent)."""
    return self.read_byte(0x0C)
  def RelativeStateOfCharge(self):
    """Estimates the remaining battery capacity as a percentage of
    FullChargeCapacity()."""
    return self.read_byte(0x0D)
  def AbsoluteStateOfCharge(self):
    """Estimates the remaining battery capacity as a percentage of
    DesignCapacity()."""
    return self.read_byte(0x0E)
  def RemainingCapacity(self):
    """Estimates the remaining battery capacity (A*h or W*h)."""
    return self._capacity(self.read_word(0x0F))
  def FullChargeCapacity(self):
    """Estimates the capacity of the battery when fully charged (A*h or W*h)."""
    return self._capacity(self.read_word(0x10))
  def RunTimeToEmpty(self):
    """Estimates the remaining time until the battery is depleted
    (datetime.timedelta).
    
    Raises InvalidValueError if the battery is not currently discharging"""
    minutes = self.read_word(0x11)
    if minutes == 0xFFFF:
      raise InvalidValueError, 'Battery is not currently discharging'
    else:
      return timedelta(minutes=minutes)
  def AverageTimeToEmpty(self):
    """Estimates the remaining time until the battery is depleted based on the
    one-minute average current consumption (datetime.timedelta).
    
    Raises InvalidValueError if the battery is not currently discharging"""
    minutes = self.read_word(0x12)
    if minutes == 0xFFFF:
      raise InvalidValueError, 'Battery is not currently discharging'
    else:
      return timedelta(minutes=minutes)
  def AverageTimeToFull(self):
    """Estimates the remaining time until the battery is fully charged based
    on the one-minute average current consumption (datetime.timedelta).
    
    Raises InvalidValueError if the battery is not currently charging"""
    minutes = self.read_word(0x13)
    if minutes == 0xFFFF:
      raise InvalidValueError, 'Battery is not currently charging'
    else:
      return timedelta(minutes=minutes)
  def ChargingCurrent(self):
    """Returns the design charging current for this battery (Amps)."""
    curr = self.read_word(0x14)
    if curr == 0xFFFF:
      raise Exception, 'Not implemented'
    else:
      return curr / 1000.0
  def ChargingVoltage(self):
    """Returns the design charging voltage for this battery (Volts)."""
    volt = self.read_word(0x15)
    if volt == 0xFFFF:
      raise Exception, 'Not implemented'
    else:
      return volt / 1000.0
  def BatteryStatus(self):
    """Gets the battery status word (register 0x16).  The status word is
    expanded into named values in a dict.

    Keyword Values:
    OCA  -- Overcharged Alarm (True if triggered)
    TCA  -- Terminate Charge Alarm (True if triggered)
    OTA  -- Overtemperature Alarm (True if triggered)
    TDA  -- Terminate Discharge Alarm (True if triggered)
    RCA  -- Remaining Capacity Alarm (True if triggered)
    RTA  -- Remaining Time Alarm (True if triggered)
    INIT -- True if the battery has been initialized
    DSG  -- Charge FET Test (False if the battery is charging)
    FC   -- True if the battery is fully charged
    FD   -- True if the battery is fully discharged
    EC   -- Error Code
    """
    status = self.read_word(0x16)
    return {
        'OCA':  bool(status & 0x8000),
        'TCA':  bool(status & 0x4000),
        'OTA':  bool(status & 0x1000),
        'TDA':  bool(status & 0x0800),
        'RCA':  bool(status & 0x0200),
        'RTA':  bool(status & 0x0100),
        'INIT': bool(status & 0x0080),
        'DSG':  bool(status & 0x0040),
        'FC':   bool(status & 0x0020),
        'FD':   bool(status & 0x0010),
        'EC':   (status & 0x000F)
    }
  def CycleCount(self):
    """Returns the number of full discharge cycles the battery has experienced."""
    cycles = self.read_word(0x17)
    if cycles == 0xFFFF:
      raise InvalidValueError, 'Cycle overflow'
    else:
      return cycles
  def DesignCapacity(self):
    """Returns the design capacity of the battery (A*h or W*h)"""
    return self._capacity(self.read_word(0x18))
  def DesignVoltage(self):
    """Returns the design voltage of the battery (Volts)"""
    return self._voltage(self.read_word(0x19))
  def SpecificationInfo(self):
    """Returns the specification word of the battery.  The specification word
    is expanded into named values in a dict.

    Keyword Values:
    version  -- Specification Version
    revision -- Specification Revision (Always 0x01)
    ipscale  -- Current Scaling Factor
    vscale   -- Voltage Scaling Factor

    The scaling factors are automatically applied in the members of sbs.Device
    """
    specinfo = self.read_word(0x1A)
    ipscale = specinfo >> 12
    vscale = (specinfo >> 8) & 0x0F
    version = (specinfo & 0x00F0) >> 8
    revision = (specinfo & 0x000F)
    return {
        'ipscale' : pow(10, ipscale),
        'vscale'  : pow(10, vscale),
        'version' : version,
        'revision': revision
    }
  def ManufacturerDate(self, newdt=None):
    """Gets or sets the manufacturing date of the battery (datetime.date)"""
    if newdt is not None:
      datenum = (newdt.year - 1980) * 256 + newdt.month * 32 + newdt.day
      self.write_word(0x1B, datenum)
    datenum = self.read_word(0x1B)
    year = 1980 + (datenum >> 8)
    month = (datenum >> 5) & 0x0F
    day = datenum & 0x1F
    return date(year, month, day)
  def SerialNumber(self, newsn=None):
    """Gets or sets the 16-bit serial number of the battery"""
    if newsn is not None:
      self.write_word(0x1C, newsn)
    return self.read_word(0x1C)
  def ManufacturerName(self):
    """Gets the manufacturer's human-readable name (e.g. Texas Instruments)"""
    return self.read_block(0x20)
  def DeviceName(self):
    """Gets the device's human-readable name (e.g. bq78350) """
    return self.read_block(0x21)
  def DeviceChemistry(self):
    """Gets the battery's human-readable chemistry name (e.g. LION)"""
    return self.read_block(0x22)
  def CellVoltage(self, cell):
    """Measures the voltage across a single battery cell (Volts).

    Keyword Arguments:
    cell -- The index of the cell to measure (0 - 15)
    """
    if (cell > 15) or (cell < 0):
      raise Exception, 'Cell out of range'
    return self.read_word(0x3F - cell) / 1000.0
  def ExtAveCellVoltage(self):
    """Returns the external average cell voltage measurement (Volts)."""
    return self._voltage(self.read_word(0x4D))
  def PendingEDV(self):
    """Retrns the next EDV in the fuel guaging algorithm (Volts)."""
    return self._voltage(self.read_word(0x4E))
  # Manufacturer Access (Device-Specific)
  def ManufacturerAccess(self, cmd=None):
    """Gets or sets the value of the manufacturer access word.  The specific
    meaning of this word is device-dependent."""
    if cmd is not None:
      self.write_word(0, cmd)
    else:
      return self.read_word(0)
  def ManufacturerData(self, fmt=None):
    """Gets the manufacturer data block.  The specific meaning of this block
    is device-dependent.
    
    On the BQ78350 (and other devices), this field will change content based
    on the value of the ManufacturerAccess() field."""
    if fmt is None:
      return self.read_block(0x23)
    else:
      return self.read_struct(0x23, fmt)
