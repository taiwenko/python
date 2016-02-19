from array  import array
from struct import calcsize, unpack
from time   import sleep
import sbs
import sys

# Number of bytes in one data block
data_block_size = 32
# Total size of the data flash in bytes (includes reserved bytes)
data_segment_size = 0x800
# Size of the data flash excluding reserved bytes
writable_data_size = 0x7C0
# Origin of the data flash in the memory space
data_origin = 0x4000
# Origin of the data segment in an SREC file
data_srec_origin = 0x4000

# Number of 22-bit words in one flash row
code_row_size = 32
# Number of rows in the instruction flash
code_segment_rows = 0x300
# Total size of the instruction flash in 22-bit words
code_segment_size = code_segment_rows * code_row_size
# Value of an uninitialized word in the instruction flash
code_default_value = 0x03FFFFF
# Origin of the code segment in an SREC file
code_srec_origin = 0x100000

# Alias bq78350.Error to sbs.Error
Error = sbs.Error

class AddressOutOfRange(Error):
  """Raised when attempting to access a word outside the flash segment"""
  def __init__(self, addr, count, msg=None):
    self.addr = addr
    self.count = count
    self.msg = msg
class ProgrammingError(Error):
  """Raised when an error occurs during device programming"""
  pass

class Device(sbs.Device):
  """Refines the generic SBS driver to include functionality specific to the
  Texas Instruments BQ78350."""
  #
  # Expanded Manufacturer Access
  #
  def ReadManufacturerBlock(self, fmt=None):
    """(Protected) Reads the value of the ManufacturerBlockAccess register"""
    if fmt is None:
      return self.read_block(0x44)
    else:
      return self.read_struct(0x44, fmt)
  def WriteManufacturerBlock(self, fmt, *args):
    """(Protected) Writes to the ManufacturerBlockAccess register"""
    self.write_struct(0x44, fmt, *args)
  #
  # Normal Commands
  #
  def DeviceType(self):
    """Returns the IC part number (78350)"""
    self.ManufacturerAccess(0x0001)
    return self.ManufacturerData('<H')
  def FirmwareVersion(self):
    """Returns the firmware version string as the tuple
    (DeviceNumber, Version, Unknown, FirmwareType, CDEV_Version, Reserved)
    """
    self.ManufacturerAccess(0x0002)
    return self.ManufacturerData('<HHHBHH')
  def HardwareVersion(self):
    """Returns the hardware version word"""
    self.ManufacturerAccess(0x0003)
    return self.ManufacturerData('<H')
  def InstructionFlashSignature(self):
    """Returns the checksum of the instruction flash."""
    self.ManufacturerAccess(0x0004)
    sleep(0.250)
    return self.ManufacturerData('<I')
  def StaticDFSignature(self):
    """Returns the checksum of the static regions of the data flash."""
    self.ManufacturerAccess(0x0005)
    sleep(0.250)
    return self.ManufacturerData('<H')
  def ChemicalID(self):
    """Returns the checksum of the chemistry regions of the data flash."""
    self.ManufacturerAccess(0x0006)
    return self.ManufacturerData('<H')
  def StaticChemDFSignature(self):
    """Returns the checksum of the static chemistry regions of the data
    flash."""
    self.ManufacturerAccess(0x0008)
    sleep(0.250)
    return self.ManufacturerData('<H')
  def AllDFSignature(self):
    """Returns the checksum of the entire data flash, including variable
    sections."""
    self.ManufacturerAccess(0x0009)
    sleep(0.250)
    return self.ManufacturerData('<H')
  def DeviceReset(self):
    """Resets the BQ78350 microcontroller."""
    self.ManufacturerAccess(0x0041)
  def OperationStatus(self):
    """Returns the operation status word.  The status word is returned as
    named values in a dict.
    
    Keyword Values:
    KEYIN  -- True if KEYIN has been detected
    CB     -- True if cell balancing is active
    INIT   -- True if the BQ78350 has fully initialized after reset
    SLEEPM -- True if sleep mode is active
    CAL    -- True if calibration mode is active
    AUTH   -- True if authentication is in progress
    LED    -- True if the LED display is on
    SDM    -- True if the shutdown command has been triggered
    SLEEP  -- True if the conditions for sleep mode have been met
    XCHG   -- True if charging has been disabled
    XDSG   -- True if discharging has been disabled
    PF     -- True if permanent failure mode is active
    SS     -- True is safety mode is active
    SDV    -- True if shutdown was triggered by low battery voltage
    SEC    -- Security Mode (1=Unsealed, 2=Full Access, 3=Sealed)
    SAFE   -- True if the SAFE pin is active
    PCHG   -- True if the precharge FET is active
    DSG    -- True if the discharge FET is active
    CHG    -- True if the charge FET is active
    PRES   -- True if system present is pulled low
    """
    self.ManufacturerAccess(0x0054)
    word = self.ReadManufacturerBlock('<HL')[1]
    return {
      'KEYIN': bool(word & 0x80000000),
      'CB':    bool(word & 0x10000000),
      'INIT':  bool(word & 0x01000000),
      'SLEEPM':bool(word & 0x00800000),
      'CAL':   bool(word & 0x00100000),
      'AUTH':  bool(word & 0x00040000),
      'LED':   bool(word & 0x00020000),
      'SDM':   bool(word & 0x00010000),
      'SLEEP': bool(word & 0x00008000),
      'XCHG':  bool(word & 0x00004000),
      'XDSG':  bool(word & 0x00002000),
      'PF':    bool(word & 0x00001000),
      'SS':    bool(word & 0x00000800),
      'SDV':   bool(word & 0x00000400),
      'SEC':   (word & 0x00000300) >> 8,
      'SAFE':  bool(word & 0x00000020),
      'PCHG':  bool(word & 0x00000008),
      'DSG':   bool(word & 0x00000004),
      'CHG':   bool(word & 0x00000002),
      'PRES':  bool(word & 0x00000001)
    }
  def DAStatus1(self):
    """Gets the battery voltages (Volts)"""
    self.ManufacturerAccess(0x0071)
    return [self._voltage(word) for word in self.ManufacturerData('<16H')]
  def DAStatus2(self):
    """Gets the external voltages (Volts) and temperatures (Kelvin) as the list
    [ExtAveCellVoltage, VAUX_Voltage, TS1Temp, TS2Temp, TS3Temp, CellTemp]"""
    self.ManufacturerAccess(0x0072)
    data = self.ManufacturerData('<6H')
    return [self._voltage(word) for word in data[0:2]] + \
           [self._temperature(word) for word in data[2:6]]
  #
  # Data Flash Access
  #
  def ReadFlash(self, addr, fmt=None, count=32):
    """Reads a block of bytes out of the data flash while in the battery's
    normal operating mode.
    
    Keyword Arguments:
    addr  -- Start address of the access
    count -- Number of bytes to read
    fmt   -- Optional format string to automatically unpack (overrides count)"""
    # Check if we have a packing format
    if type(fmt) is str:
      count = calcsize(fmt)
    elif fmt is not None:
      count = fmt.size
    # Make sure addr is in range
    if addr < data_origin:
      raise AddressOutOfRange, addr, count
    if addr+count > data_origin+data_segment_size:
      raise AddressOutOfRange, addr, count
    # Read N bytes, looping as necessary
    result = ''
    while len(result) < count:
      self.WriteManufacturerBlock('<H', addr)
      data = self.ReadManufacturerBlock('<H32s')
      if data[0] != addr:
        raise SBSException, 'Unexpected memory block received'
      addr = addr + 32
      result = result + data[1]
    result = result[0:count]
    # Optional unpacking
    if type(fmt) is str:
      return unpack(fmt, result)
    elif fmt is not None:
      return fmt.unpack(result)
    return result
  def UnderVoltageThreshold(self):
    """Returns the configured battery under-voltage threshold (Volts)"""
    return self._voltage(self.ReadFlash(0x4486, '>H')[0])
  def OverVoltageThreshold(self):
    """Returns the configured battery over-voltage threshold (Volts)"""
    return self._voltage(self.ReadFlash(0x448B, '>H')[0])
  def OverCurrentChargeThreshold(self):
    """Returns the configured battery under-current charging threshold
    (Amps)"""
    # Stored in units of mA instead of 10mA
    return self._current(self.ReadFlash(0x4490, '>h')[0] / 10.0)
  def OverCurrentDischargeThreshold(self):
    """Returns the configured battery under-current discharging threshold
    (Amps)"""
    # Stored in units of mA instead of 10mA
    return self._current(self.ReadFlash(0x4496, '>h')[0] / 10.0)
  def OverTemperatureChargeThreshold(self):
    """Returns the configured maximum charging temperature (Celsius)"""
    return self._temperature(self.ReadFlash(0x44A4, '>h')[0])
  def OverTemperatureDischargeThreshold(self):
    """Returns the configured maximum discharging temperature (Celsius)"""
    return self._temperature(self.ReadFlash(0x44A9, '>h')[0])
  def UnderTemperatureChargeThreshold(self):
    """Returns the configured minimum charging temperature (Celsius)"""
    return self._temperature(self.ReadFlash(0x44AE, '>h')[0])
  def UnderTemperatureDischargeThreshold(self):
    """Returns the configured minimum discharging temperature (Celsius)"""
    return self._temperature(self.ReadFlash(0x44B3, '>h')[0])
  #
  # ROM Mode (Firmware Bootstrapping)
  #
  def EnterROMMode(self, *kargs, **kwargs):
    """Enters ROM mode and returns an object to manipulate the device's
    firmware.
    
    Normal usage:
    # Enters ROM Mode and returns an instance of Programmer
    with dev.EnterROMMode() as prog:
      prog.WriteCodeWord(0, 1, 0x123456)
    # Exiting the 'with' block will automatically call LeaveROMMode()
    """
    return Programmer(self, *kargs, **kwargs)
  def LeaveROMMode(self):
    """Forces the device to leave ROM mode.  Should not be explicitly called when
    using the Programmer object."""
    self.send_byte(0x08)
    sleep(1.0)
    self._reinit()

class Programmer(object):
  """Explicit lifetime object to handle programming the device's firmware.  When
  used with python's 'with' keyword, it will automatically leave ROM mode."""
  #
  # Lifecycle
  #
  def __init__(self, device, autoclose=True):
    """Initializes a new instance of the Programmer class
    
    Keyword Arguments:
    device    -- Instance of sb78350.Device to modify
    autoclose -- close() the Programmer when leaving the 'with' block
    
    Normal usage:
    # Enters ROM Mode and returns an instance of Programmer
    with bq78350.Programmer(dev) as prog:
      prog.WriteCodeWord(0, 1, 0x123456)
    # Exiting the 'with' block will automatically call LeaveROMMode() unless
    # Programmer was initialized with autoclose set to False
    """
    self._device = device
    self.autoclose = autoclose
    device.ManufacturerAccess(0x0F00)
  def close(self):
    """Closes the Programmer object by leaving the bootstrap"""
    self._device.LeaveROMMode()
  #
  # "with" keyword support
  #
  def __enter__(self):
    return self
  def __exit__(self, type, value, tb):
    if self.autoclose and (type is None):
      self.close()
    return False
  #
  # Informational Commands
  #
  def Version(self):
    """Gets the version number of the BQ78350 bootstrap ROM"""
    version = self._device.read_word(0x0D)
    return (version >> 8, version & 0x0FF)
  #
  # Data Segment Commands
  #
  def EraseData(self, row=None):
    """Erases the data segment, either in its entirety or a single row.
    
    Keyword Arguments:
    row -- Address to erase a specific 32-byte row (optional)"""
    if row is None:
      self._device.write_word(0x12, 0x83DE)
      sleep(0.620)
    else:
      self._device.write_word(0x11, row)
      sleep(0.020)
  def WriteDataByte(self, addr, value):
    """Writes a single byte to the data space.

    Keyword Arguments:
    addr  -- Address in the data space to access (0x4000 - 0x47C0)
    value -- Byte to write to the specified address (0x00 - 0xFF)
    """
    if addr < data_origin:
      raise AddressOutOfRange
    elif addr >= (data_origin + writable_data_size):
      raise AddressOutOfRange
    self._device.write_struct(0x0F, '<HB', addr, value)
    sleep(0.002)
  def DataChecksum(self):
    """Returns the checksum for the entire writable data segment
    (0x4000 - 0x47C0)."""
    return self._device.read_word(0x0E)
  def WriteData(self, data):
    """Copies an entire block into the BQ78350's data segment and verifies
    the checksum.  The data segment must have already been erased."""
    length = min(len(data), writable_data_size)
    chksum = 0
    for offset in range(0, length):
      byte = data[offset]
      self.WriteDataByte(data_origin + offset, byte)
      chksum = chksum + byte
    for offset in range(length, writable_data_size):
      chksum = chksum + 0xFF
    chksum = chksum & 0x0FFFF
    if chksum != self.DataChecksum():
      raise ProgrammingError, 'Data Checksum Error'
  def ReadDataByte(self, addr):
    """Reads one byte from the data space.
    
    Keyword Arguments:
    addr -- Address of the byte to access"""
    self._device.write_word(0x09, addr)
    return self._device.read_word(0x0B) & 0x0FF
  def ReadDataBlock(self, addr):
    """Returns a block of 32 bytes from the data space.
    
    Keyword Arguments:
    addr -- Address of the lowest byte in the block to access"""
    self._device.write_word(0x09, addr)
    return self._device.read_struct(0x0C, '32s')[0]
  #
  # Code Segment Commands
  #
  def EraseCode(self, row=None):
    """Erases the code segment, either in its entirety or a single row.
    
    Keyword Arguments:
    row -- Address to erase a specific 32-word row (optional)"""
    if row is None:
      self._device.write_word(0x07, 0x83DE)
      sleep(0.620)
    else:
      if (row < 0) or (row >= code_segment_rows):
        raise AddressOutOfRange
      self._device.write_word(0x06, row)
      sleep(0.020)
  def WriteCodeWord(self, row, col, value):
    """Writes a single word to the code space.

    Keyword Arguments:
    row   -- Row in the code space to modify (0x000 - 0x300)
    col   -- Column in the specified row to modify (0 - 31)
    value -- 22-Bit word to write (0x000000 - 0x3FFFFF)
    """
    if (row < 0) or (row >= code_segment_rows):
      raise AddressOutOfRange
    if (col < 0) or (col >= code_row_size):
      raise AddressOutOfRange
    self._device.write_struct(0x04, '<HBHB', row, col, value & 0x0FFFF, value >> 16)
    sleep(0.002)
  def CodeChecksum(self, row):
    """Returns the checksum for a single row in the code segment.
    
    Keyword Arguments:
    row -- Row in the code space to access (0x000 - 0x300)"""
    if (row < 0) or (row >= code_segment_rows):
      raise AddressOutOfRange
    self._device.write_struct(0x00, '<HB', row, 0)
    return self._device.read_struct(0x03, '<L')[0]
  def WriteCodeWords(self, program):
    """Copies an entire block into the BQ78350's code segment and verifies
    the checksums.  The code segment must have already been erased."""
    # Core writing
    for row in range(code_segment_rows):
      # Write out row at a time
      chksum = 0
      for col in range(code_row_size):
        # Linear location in the segment
        pos = row * code_row_size + col
        # Saved as BE in the SREC file
        # Skip row 0, col 5 for the first pass
        if ((row == 0) and (col == 5)) or (pos >= len(program)):
          word = code_default_value
        else:
          word = program[pos]
        chksum = chksum + word
        # Save time by skipping uninitialized words
        if word != code_default_value:
          self.WriteCodeWord(row, col, word)
      sys.stdout.write('.')
      # Checksums are per-row
      chksum = chksum & 0x0FFFFFFFF
      if chksum != self.CodeChecksum(row):
        raise ProgrammingError, 'Checksum Mismatch in Code Row %d' % row
    # Write out the boot address after everything else is known correct
    self.WriteCodeWord(0, 5, program[5])
    chksum = sum(program[0:code_row_size]) & 0x0FFFFFFFF
    # This exception is particularly fatal because it means the device
    # will boot into an invalid state.  We leave the memory intact in case
    # the client wishes to inspect it, but the client should erase memory
    # before giving up for good.
    if chksum != self.CodeChecksum(0):
      raise ProgrammingError, 'Checksum Mismatch in Boot Row'
  def WriteCodeBytes(self, program):
    """Copies an entire block into the BQ78350's code segment and verifies
    the checksums.  The code segment must have already been erased."""
    if len(program) % 4 != 0:
      raise ProgrammingError, 'Code segment is not an integer number of words'
    # Refactor program into words
    words = array('L', [0] * (len(program) / 4))
    for offset in range(len(words)):
      words[offset] = (program[offset*4+0] << 24) | \
                      (program[offset*4+1] << 16) | \
                      (program[offset*4+2] <<  8) | \
                      (program[offset*4+3] <<  0)
    return self.WriteCodeWords(words)
  def ReadCodeWord(self, row, col):
    """Reads one word from the code space.
    
    Keyword Arguments:
    row -- Row in the code space to access (0x000 - 0x300)
    col -- Column in the specified row to read (0 - 31)"""
    if (row < 0) or (row >= code_segment_rows):
      raise AddressOutOfRange
    if (col < 0) or (col >= code_row_size):
      raise AddressOutOfRange
    self._device.write_struct(0x00, '<HB', row, col)
    data = self.read_struct(0x01, '<HB')
    return (data[1] << 16) | data[0]
  def ReadCodeRow(self, row):
    """Returns an entire row of 32 words from the code space.
    
    Keyword Arguments:
    row -- Row in the code space to access (0x000 - 0x300)"""
    if (row < 0) or (row >= code_segment_rows):
      raise AddressOutOfRange
    self._device.write_struct(0x00, '<HB', row, 0)
    # The words are packed in as 24 bit words
    data = self._device.read_block(0x02, 128)
    result = array('L', [0] * code_row_size)
    for pos in range(code_row_size):
      result[pos] = ord(data[3*pos]) | (ord(data[3*pos+1])<<8) | \
          (ord(data[3*pos+2])<<16)
    return result
