import aardvark_py as api
from array import array
from struct import pack, unpack, calcsize

class I2CError(Exception):
    pass

# Text for various I2C Errors
_i2c_errors = (
  'No Error',
  'Bus Error',
  'Address Acknowledged',
  'Address Not Acknowledged',
  'Data Not Acknowledged',
  'Arbitration Lost',
  'Bus Locked',
  'Last Data Byte Acked'
)

# Text for various Aardvark Errors
_sys_errors = {
  api.AA_UNABLE_TO_LOAD_LIBRARY:   'Unable to Load Library',
  api.AA_UNABLE_TO_LOAD_DRIVER:    'Unable to Load Driver',
  api.AA_UNABLE_TO_LOAD_FUNCTION:  'Unable to Load Function',
  api.AA_INCOMPATIBLE_LIBRARY:     'Incompatible Library',
  api.AA_INCOMPATIBLE_DEVICE:      'Incompatible Device',
  api.AA_COMMUNICATION_ERROR:      'Communication Error',
  api.AA_UNABLE_TO_OPEN:           'Unable to Open',
  api.AA_UNABLE_TO_CLOSE:          'Unable to Close',
  api.AA_INVALID_HANDLE:           'Invalid Handle',
  api.AA_CONFIG_ERROR:             'Configuration Error',
  api.AA_I2C_NOT_AVAILABLE:        'I2C Not Available',
  api.AA_I2C_NOT_ENABLED:          'I2C Not Enabled',
  api.AA_I2C_READ_ERROR:           'Read Error',
  api.AA_I2C_WRITE_ERROR:          'Write Error',
  api.AA_I2C_SLAVE_BAD_CONFIG:     'Bad Slave Configuration',
  api.AA_I2C_SLAVE_READ_ERROR:     'Slave Read Error',
  api.AA_I2C_SLAVE_TIMEOUT:        'Slave Timeout',
  api.AA_I2C_DROPPED_EXCESS_BYTES: 'Dropped Excess Bytes',
  api.AA_I2C_BUS_ALREADY_FREE:     'Bus Already Free'
}

# Helper function to find the first available Aardvark device
def _find_aardvark():
  (num, ports, unique_ids) = api.aa_find_devices_ext(16, 16)
  for port in ports:
    if not (port & api.AA_PORT_NOT_FREE):
      return port
  raise Exception, 'Could not locate SMBus interface device'
# Checks the return value from an Aardvark API function and throws an
# appropriate exception
def _check_result(result):
  try:
    code = result[0]
  except:
    code = result
  if code < 0:
    try:
      raise I2CError, _sys_errors[code]
    except KeyError:
      raise I2CError, 'Unknown Error %d' % code
  return result
# Checks the return value from an Aardvark I2C function and throws an
# appropriate exception
def _check_i2c(result):
  _check_result(result)
  if result[0] > 0:
    if result[0] < len(_i2c_errors):
      raise I2CError, _i2c_errors[result[0]]
    else:
      raise I2CError, 'I2C Bus Error %d' % result[0]
  return result

class Bus(object):
  """Provides an object-oriented interface to the Aardvark I2C/SPI USB
  driver
  """
  #
  # Object Lifecycle
  #
  def __init__(self):
    """Initialize a new instance of the Bus class.  This will access the
    Aardvark API and open the first available Aardvark USB device.  If no
    device is available, an exception will be raised.
    """
    self._port = _find_aardvark()
    self._open = False
    self._handle = _check_result(api.aa_open(self._port))
    self._open = True
    _check_result(api.aa_configure(self._handle, api.AA_CONFIG_GPIO_I2C)) # AA_CONFIG_SPI_I2C
    _check_result(api.aa_i2c_pullup(self._handle, api.AA_I2C_PULLUP_BOTH))
    _check_result(api.aa_i2c_bitrate(self._handle, 100))
    _check_result(api.aa_gpio_set(self._handle, 0x00)) # Initialize to zeros
    _check_result(api.aa_gpio_direction(self._handle, 0xFF)) # All outputs
  def _close(self):
    """(Protected) Closes the device handle opened by __init__(), returning
    the result code.  Called by __del__(), __exit__(), and close().
    """
    if self._open:
      result = api.aa_close(self._handle)
      self._open = False
      self._handle = None
      return result
    else:
      return 0
  def __del__(self):
    """Destructor for Bus.  Closes the handle openned by __init__() but does
    not raise an exception in case of error.
    """
    self._close()
  def close(self):
    """Closes the device handle opened by __init__(), raising an exception in
    case of error.
    """
    _check_result(self._close())
  #
  # "with" Keyword support
  #
  def __enter__(self):
    return self
  def __exit__(self, type, value, tb):
    self._close()
    return False
  #
  # Raw device access
  #
  def gpio_set(self, bitmask):
    result = api.aa_gpio_set(self._handle, int(bitmask))
    return _check_result(result)
  def write(self, addr, data):
    """Writes an array of bytes to the addressed I2C device.
    
    Keyword arguments:
    addr -- I2C Slave Address (0x00 - 0x7F)
    data -- Bytes to send
    """
    if type(data) is not array:
      data = array('B', data)
    result = api.aa_i2c_write(self._handle, addr, api.AA_I2C_NO_FLAGS, data)
    return _check_result(result)
  def read(self, addr, length):
    """Reads an array of bytes from the addressed I2C device.

    Keyword arguments:
    addr   -- I2C Slave Address (0x00 - 0x7F)
    length -- Number of bytes to receive
    """
    (count, data) = api.aa_i2c_read(self._handle, addr, \
            api.AA_I2C_NO_FLAGS, length)
    _check_result(count)
    return data.tostring()
  def write_read(self, addr, wrdata, rdlength):
    """Performs a write followed by a read (seperated by restart) on an
    addressed I2C device.

    Keyword arguments:
    addr     -- I2C Slave Address (0x00 - 0x7F)
    wrdata   -- Bytes to write
    rdlength -- Number of bytes to receive
    """
    if type(wrdata) is not array:
      wrdata = array('B', wrdata)
    (result, wrcount, rddata, rdcount) = _check_i2c(api.aa_i2c_write_read(\
        self._handle, addr, api.AA_I2C_NO_FLAGS, wrdata, rdlength))
    return rddata.tostring()

class Device(object):
  """Provides an object-oriented interface to a single I2C device connected to
  an Aardvark I2C controller.
  """
  def __init__(self, bus, addr):
    """Initialize a new instance of the Device class.

    Keyword Arguments:
    bus  -- Instance of Bus used to communicate with the device
    addr -- I2C Slave Address (0x00 - 0x7F)
    """
    self._bus = bus
    self._addr = addr
  #
  # "with" Keyword support
  #
  def __enter__(self):
    return self
  def __exit__(self, type, value, tb):
    return False
  #
  # Raw device access
  #
  def write(self, data):
    """Writes an array of bytes to the addressed I2C device.
    
    Keyword arguments:
    data -- Bytes to send
    """
    return self._bus.write(self._addr, data)
  def read(self, length):
    """Reads an array of bytes from the addressed I2C device.

    Keyword arguments:
    length -- Number of bytes to receive
    """
    return self._bus.read(self._addr, length)
  def write_read(self, wrdata, rdlength):
    """Performs a write followed by a read (seperated by restart) on an
    addressed I2C device.

    Keyword arguments:
    wrdata   -- Bytes to write
    rdlength -- Number of bytes to receive
    """
    return self._bus.write_read(self._addr, wrdata, rdlength)
  #
  # SMBus Device Primitives
  #
  def quick_command(self, value):
    """Performs a Quick Command as per 5.5.1.  This uses the Rd/Wr bit to send
    a single boolean value to the device.

    Keyword Arguments:
    value -- Boolean value to transfer to the device
    """
    if value:
      self.read(0)
    else:
      self.write('')
  def send_byte(self, byte):
    """Performs a Send Byte as per 5.5.2.

    Keyword Arguments:
    byte -- Byte value to transfer to the device (0x00 - 0xFF)
    """
    self.write(pack('B', byte))
  def receive_byte(self):
    """Performs a Receive Byte as per 5.5.3."""
    return unpack('B', self.read(1))[0]
  def receive_byte_signed(self):
    """Performs a Receive Byte as per 5.5.3 but interprets it as signed."""
    return unpack('b', self.read(1))[0]
  def write_byte(self, cmd, byte):
    """Performs a Write Byte as per 5.5.4.
    
    Keyword Arguments:
    cmd  -- Register to access
    byte -- Byte value to store in the register (0x00 - 0xFF)
    """
    return self.write(pack('BB', cmd, byte))
  def write_word(self, cmd, word):
    """Performs a Write Word as per 5.5.4.
    
    Keyword Arguments:
    cmd  -- Register to access
    word -- 16-Bit Word value to store in the register (0x0000 - 0xFFFF)
    """
    return self.write(pack('<BH', cmd, word))
  def read_byte(self, cmd):
    """Performs a Read Byte as per 5.5.5.
    
    Keyword Arguments:
    cmd  -- Register to access
    """
    return unpack('B', self.write_read(pack('B', cmd), 1))[0]
  def read_byte(self, cmd):
    """Performs a Read Byte as per 5.5.5 but interprets it as signed.
    
    Keyword Arguments:
    cmd  -- Register to access
    """
    return unpack('b', self.write_read(pack('B', cmd), 1))[0]
  def read_word(self, cmd):
    """Performs a Read Word as per 5.5.5.
    
    Keyword Arguments:
    cmd  -- Register to access
    """
    return unpack('<H', self.write_read(pack('B', cmd), 2))[0]
  def read_word_signed(self, cmd):
    """Performs a Read Word as per 5.5.5 but interprets it as signed.
    
    Keyword Arguments:
    cmd  -- Register to access
    """
    return unpack('<h', self.write_read(pack('B', cmd), 2))[0]
  def write_block(self, cmd, block):
    """Performs a Block Write as per 5.5.7.
    
    Keyword Arguments:
    cmd   -- Register to access
    block -- Data to write to the register (binary packed string)
    """
    if len(block) > 255:
      raise I2CError, 'Block length exceeds maximum permissible length'
    return self.write(pack('BB', cmd, len(block)) + block)
  def read_block(self, cmd, maxblock=32):
    """Performs a Block Read as per 5.5.7.
    
    Keyword Arguments:
    cmd      -- Register to access
    maxblock -- Maximum size of the block to read
    """
    data = self.write_read(pack('B', cmd), maxblock + 1)
    length = unpack('B', data[0])[0]
    if length > maxblock:
      raise I2CError, 'Block length exceeds maximum permissible length'
    return data[1:1+length]
  #
  # SMBus Device Wrappers
  #
  def write_struct(self, cmd, fmt, *kargs):
    """Wraps write_block() in a call to struct.pack.
    
    Keyword Arguments:
    cmd -- Register to access
    fmt -- Format to use when packing the block

    Positional Arguments:
    v1, v2, ... -- Values to pack into the block
    """
    if type(fmt) is str:
      return self.write_block(cmd, pack(fmt, *kargs))
    else:
      return self.write_block(cmd, fmt.pack(*kargs))
  def read_struct(self, cmd, fmt):
    """Wraps read_block() in a call to struct.unpack.
    
    Keyword Arguments:
    cmd -- Register to access
    fmt -- Format to use when unpacking the block
    """
    if type(fmt) is str:
      return unpack(fmt, self.read_block(cmd, calcsize(fmt)))
    else:
      return fmt.unpack(self.read_block(cmd))
