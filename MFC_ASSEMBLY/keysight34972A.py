import vxi11
import time

def chunk(biglist, chunksize):
  for index in xrange(0, len(biglist), chunksize):
    yield biglist[index:index + chunksize]
class Keysight34972A(vxi11.Instrument):
  """The DAQ Switch class."""
  def __init__(self, addr):
    super(Keysight34972A, self).__init__(addr)
    self.get_id()
    self.reset()
    self.write('FORM:READ:TIME ON')
    time.sleep(0.1)
    self.write('FORM:READ:CHAN ON')
    time.sleep(0.1)
    self.verbose = False
  def reset(self):
    """Perform system reset."""
    self.write('SYST:PRES')
    time.sleep(0.1)
  def get_id(self):
    """Get the system id."""
    self.identity = self.ask('*IDN?')
  def get_all_errs(self):
    """Get all the errors."""
    thiserr = self.get_err()
    errors = []
    while thiserr != '+0,"No error"':
      thiserr = self.get_err()
      errors.append(thiserr)
    return errors
  def configure_chans(self, conf, chans):
    """Set measurement type.
    Args:
      conf: A SCPI command like 'VOLT:DC'
      chans: A SCPI channel or channel range, e.g. '201:207'
    """
    self.write('CONF:{:} (@{:})'.format(conf, chans))
  def get_err(self):
    """Get an error."""
    return self.ask('SYST:ERR?')
  def get_cond(self):
    """Get the instrument condition."""
    return self.ask('STAT:OPER:COND?')
  def get_bit_status(self, bitstr, bit):
    """check the bit status."""
    if bit < len(bitstr)-2:
      return bitstr[2:][-1-bit]
    else:
      return '0'
  def any_scans(self, bitstr):
    """Check if any scans are currently running."""
    status = ''
    for b in xrange(8):
      status += self.get_bit_status(bitstr, b)
    return ('1' in status)
  def set_chans(self, chans):
    """set the channels.
    Args:
       chans: SCPI channel specification, e.g. '301' or '301,304', or '301:307'
    """
    self.chans = chans
  def set_trigger_count(self, count):
    """Set the scan trigger count."""
    self.count = count
  def set_timer(self, timer):
    """Set the scan timer."""
    self.timer = timer
  def setup_scan(self):
    """Setup a scan. """
    self.write('TRIG:SOUR IMM')
    time.sleep(0.1)
    self.write('TRIG:COUN {:0.0f}'.format(self.count))
    time.sleep(0.1)
    self.write('ROUT:CHAN:DEL 0')
    time.sleep(0.1)
    self.write('ROUT:SCAN (@{:})'.format(self.chans))
    time.sleep(0.1)
    self.write('VOLT:DC:RANG MAX')
    time.sleep(0.1)
    self.write('VOLT:DC:RES MAX')
    time.sleep(0.1)
    self.write('SENS:ZERO:AUTO ONCE,(@{:})'.format(self.chans))
    time.sleep(0.1)
    self.write('INP:IMP:AUTO ON')
    time.sleep(0.1)
    self.write('SENS:VOLT:DC:APER 0.005')
    time.sleep(0.1)
    self.write('ROUT:MON:STAT OFF')
    time.sleep(0.1)
  def start_scan(self):
    """Start a scan."""
    self.write('DISP:TEXT \'SCANNING\'')
    time.sleep(0.1)
    self.write('INIT')
  def wait_for_scan(self):
    """Wait for a scan to complete. """
    while self.any_scans(bin(int(self.get_cond()))):
      time.sleep(1)
  def abort_scan(self):
    """Abort a scan."""
    if self.any_scans(bin(int(self.get_cond()))):
      print 'aborting scan'
      self.write('ABORt')
      time.sleep(0.1)
    self.cleanup_after_scan()
  def get_scan_data(self):
    """Retrieve data from a switch."""
    self.data = list(chunk(self.ask('FETC?').split(','), 3))
    time.sleep(0.1)
  def cleanup_after_scan(self):
    """Set display back to normal."""
    self.write('DISP:TEXT:CLE')
    time.sleep(0.1)
  def scan_chans_and_wait(self):
    """All scan routines."""
    self.setup_scan()
    self.start_scan()
    self.wait_for_scan()
    self.get_scan_data()
    self.cleanup_after_scan()
    return self.data
  def mon_chan(self, chan):
    """Get some data from just one channel."""
    self.write('ROUT:MON (@{:})'.format(chan))
    self.write('ROUT:MON:STAT ON')
    self.data = []
    self.tic = time.time()
    for x in xrange(100):
      self.data.append(instr.ask('ROUT:MON:DATA?'))
    self.toc = time.time()
    self.elapsed_time = self.toc-self.tic
    if self.verbose:
      print 'elapsed time', self.elapsed_time
      print 'acquisition rate', len(self.data)/self.elapsed_time, 'Hz'
    return self.data

if __name__ == '__main__':
  import pprint
  instr = Keysight34972A('192.168.1.3')
  print instr.get_all_errs()
  print 'set channels',
  instr.set_chans('101:103')
  print instr.chans
  print 'set timer',
  instr.set_timer(0)
  print instr.timer
  print 'set trigger count',
  instr.set_trigger_count(1)
  print instr.count
  print instr.get_all_errs()
  #data = instr.scan_chans_and_wait()
  #pprint.pprint(data)
  print instr.get_all_errs()
  newdata = instr.mon_chan('103')
  pprint.pprint(newdata)
