import serial

_queries = {
    'XPDR:MEAS:CAP?': [
        'response',
        'response_modes',
        'modes_state',
        'modes_level'
    ],
    'XPDR:MEAS:ATCR:ACAL?': [
        'allcall',
        'allcall_modea',
        'allcall_modec'
    ],
    'XPDR:MEAS:ATCR:DEC?': [
        'decoder',
        'decoder_inneralow',
        'decoder_innerahigh',
        'decoder_outeralow',
        'decoder_outerahigh',
        'decoder_innerclow',
        'decoder_innerchigh',
        'decoder_outerclow',
        'decoder_outerchigh'
    ],
    'XPDR:MEAS:ATCR:POW?': [
        'power',
        'power_toperp',
        'power_toperp_value',
        'power_boterp',
        'power_boterp_value',
        'power_insterp',
        'power_insterp_value',
        'power_topmtl',
        'power_topmtl_value',
        'power_botmtl',
        'power_botmtl_value',
        'power_instmtl',
        'power_instmtl_value',
        'power_topdiff',
        'power_topdiff_value',
        'power_botdiff',
        'power_botdiff_value',
        'power_instdiff',
        'power_instdiff_value',
        'power_topallcall',
        'power_topallcall_value',
        'power_botallcall',
        'power_botallcall_value',
        'power_installcall',
        'power_installcall_value'
    ],
    'XPDR:MEAS:ATCR:PTIM?': [
        'timing',
        'timing_af1',
        'timing_af1_value',
        'timing_af2',
        'timing_af2_value',
        'timing_af1f2',
        'timing_af1f2_value',
        'timing_cf1',
        'timing_cf1_value',
        'timing_cf2',
        'timing_cf2_value',
        'timing_cf1f2',
        'timing_cf1f2_value'
    ],
    'XPDR:MEAS:ATCR:RDEL?': [
        'delay',
        'delay_modea',
        'delay_modea_value',
        'delay_modec',
        'delay_modec_value'
    ],
    'XPDR:MEAS:ATCR:RDR?': [
        'droop',
        'droop_modea',
        'droop_modea_value',
        'droop_modec',
        'droop_modec_value'
    ],
    'XPDR:MEAS:ATCR:REPL?': [
        'reply',
        'reply_modeacode',
        'reply_modeacode_value',
        'reply_modeaspi',
        'reply_modeaspi_value',
        'reply_modecraw',
        'reply_modecraw_value',
        'reply_modecalt',
        'reply_modecalt_value'
    ],
    'XPDR:MEAS:ATCR:RJIT?': [
        'jitter',
        'jitter_modea',
        'jitter_modea_value',
        'jitter_modec',
        'jitter_modec_value'
    ],
    'XPDR:MEAS:ATCR:RRAT:PERC?': [
        'ratio',
        'ratio_modea',
        'ratio_modea_value',
        'ratio_modec',
        'ratio_modec_value',
        'ratio_modealow',
        'ratio_modealow_value',
        'ratio_modeclow',
        'ratio_modeclow_value'
    ],
    'XPDR:MEAS:ATCR:SLS?': [
        'sls',
        'sls_modeaneg',
        'sls_modeazero',
        'sls_modecneg',
        'sls_modeczero'
    ]
}

_overall = 'overall'
_fields = [ _overall ] + \
    [ item for fields in _queries.values() for item in fields ]

def fields():
    return list(_fields)

class Aeroflex(object):
    def __init__(self, port, baudrate=9600, bytesize=8, parity='N',
                 stopbits=1):
        self.serial = serial.Serial(port, baudrate, bytesize, parity, stopbits)
        self._write('*CLS')
        idn = self._query('*IDN?')
        if not idn.startswith('AEROFLEX,6000,'):
            raise Exception, 'Unknown device on ' + port

    def _write(self, message):
        self.serial.write(message + '\r\n')

    def _read(self, timeout):
        self.serial.timeout = timeout
        value = self.serial.readline()
	if len(value) == 0 or value[-1] != '\n':
            raise IOError, 'Read Timeout'
        return value.strip()

    def _query(self, message, timeout=1.0):
        self._write(message)
        return self._read(timeout)

    def measure(self):
        # Perform the measurement
        result = {}
        result[_overall] = self._query('XPDR:MEAS?', 600.0)
        # Start spooling out the results
        for cmd,names in _queries.iteritems():
            value = self._query(cmd).split(',')
            for i in range(len(value)):
                result[names[i]] = value[i]
        return result
