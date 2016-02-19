from array import array

class Record(object):
  def link(self, linker):
    pass
class HeaderRecord(Record):
  def __init__(self, data, address=None, **kwargs):
    self.data = data
  def __str__(self):
    return 'Header: ' + self.data
  def link(self, linker):
    linker.header = self.data
class DataRecord(Record):
  def __init__(self, address, data, **kwargs):
    self.address = address
    self.data = data
  def __str__(self):
    return ('0x%X:' % self.address) + self.data.encode('hex')
  def link(self, linker):
    linker.map(self.address, self.data)
class CountRecord(Record):
  def __init__(self, address, data=None, **kwargs):
    self.count = address
  def __str__(self):
    return '%d Record(s)' % self.count
class StartAddressRecord(Record):
  def __init__(self, address, data=None, **kwargs):
    self.address = address
  def __str__(self):
    return 'Start at 0x%X' % self.address
  def link(self, linker):
    linker.start = self.address

class FormatError(Exception):
  pass
class LinkerError(Exception):
  pass

# SREC Type -> WrapperClass, AddressCharacters
_fieldtypes = {
  '0': (HeaderRecord, 2),
  '1': (DataRecord, 2),
  '2': (DataRecord, 3),
  '3': (DataRecord, 4),
  '5': (CountRecord, 2),
  '6': (CountRecord, 3),
  '7': (StartAddressRecord, 4),
  '8': (StartAddressRecord, 3),
  '9': (StartAddressRecord, 2),
}

def _parse(text, *kargs, **kwargs):
  # General Format: Stllaaaa(aa(aa))dd..ddcc
  # Treat any line not starting with 'S' as a comment
  if not text.startswith('S'):
    return None
  try:
    (type, addrlen) = _fieldtypes[text[1]]
  except IndexError:
    raise FormatError, 'Unknown field type'
  # Verify minimum length
  length = int(text[2:4], 16)
  if length < addrlen+1:
    raise FormatError, 'Length too small for field type'
  # Verify checksum
  sum = length
  for pos in range(length):
    sum = sum + int(text[pos*2+4:pos*2+6], 16)
  if (sum & 0xFF) != 0xFF:
    raise FormatError, 'Checksum error in SREC record'
  # Extract address
  address = int(text[4:addrlen*2+4], 16)
  # Extract payload
  data = text[addrlen*2+4:length*2+2].decode("hex")
  # Generate object
  return type(address=address, data=data, *kargs, **kwargs)

class Reader(object):
  """Reads a file as a sequence of Motorola S-Records"""
  def __init__(self, filename):
    self._filename = filename
    self._lineno = 1
    self._file = open(filename, 'rU')
  def __iter__(self):
    return self
  def close(self):
    self._file.close()
  def next(self):
    for text in self._file:
      try:
        record = _parse(text, filename=self._filename, line=self._lineno)
      finally:
        self._lineno = self._lineno + 1
      if record:
        return record
    raise StopIteration

class Segment(object):
  """Manages the image of a segment of addressable space for the linker"""
  def __init__(self, start, size, init=chr(0xFF)):
    if size % len(init) != 0:
      raise Exception, 'Segment size is not an integer multiple of the init string'
    self.start = start
    self._buffer = array('B', init) * (size / len(init))
    self.end = start + size
    self.size = size
  def __len__(self):
    return len(self._buffer)
  def __getitem__(self, key):
    return self._buffer[key]
  def __setitem__(self, key, value):
    self._buffer[key - self.start] = value
  def __iter__(self):
    return iter(self._buffer)
  def __str__(self):
    return 'Segment: Origin 0x%X, %d Bytes' % \
        (self._start, len(self._buffer))
  def map(self, address, data):
    """Copies a piece of data into the segment"""
    # Verify data fits within segment
    offset = address - self.start
    last = offset + len(data)
    if (offset < 0) or (last > self.size):
      raise LinkerError, 'Data does not fit within segment space'
    # Splice in data
    self._buffer[offset:last] = array('B', data)

class Linker(object):
  """Consumes a sequence of S-Records and constructs an image in memory"""
  def __init__(self, *segments):
    self._segments = segments
    self.start = None
    self.header = None
  def __len__(self):
    return len(self._segments)
  def __getitem__(self, key):
    return self._segments[key]
  def __iter__(self):
    return iter(self._segments)
  def map(self, address, data):
    """Maps addressed data into the target segments"""
    end = address + len(data)
    for segment in self._segments:
      if (address >= segment.start) and (end <= segment.end):
        segment.map(address, data)
        break
    else:
      raise LinkerError, 'Address 0x%X does not map to known segment' % address
  def link(self, record):
    """Links one or more records into the target segments"""
    if isinstance(record, Record):
      # Parse the record appropriately
      record.link(self)
    else:
      # Assume it's a list of records
      for x in record:
        self.link(x)
