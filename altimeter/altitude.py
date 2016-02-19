import math

meter_per_foot = 0.3048
feet_per_meter = 1 / meter_per_foot

_stdtemp = 15 + 273.15
_stdpres = 101325.0
_g = 9.80665
_R = 287.053

_heights = [ 0E3, 11E3, 20E3, 32E3, 47E3, 51E3, 71E3, 84.852E3 ]
_lapsert = [ -6.5E-3, 0, 1E-3, 2.8E-3, 0, -2.8E-3, -2.0E-3, 0 ]
_isotherm = [ False, True, False, False, True, False, False, True ]
_basetemps = [ _stdtemp ]
_basepress = [ _stdpres ]

# Let's compute the T's and P's to the limits of our precision
for i in range(len(_heights)-1):
    _dh = _heights[i+1] - _heights[i]
    _dT = _lapsert[i] * _dh
    _T0 = _basetemps[i]
    _Tn = _dT + _T0
    _l0 = _lapsert[i]
    if _isotherm[i]:
        _Pn = _basepress[i] * math.exp(-_dh * _g / _T0 / _R)
    else:
        _Pn = _basepress[i] * math.pow(_Tn / _T0, -_g / _R / _l0)
    _basetemps.append(_Tn)
    _basepress.append(_Pn)

def standard_temperature(alt):
    """Compute the standard temperature for a given altitude"""
    for i in range(len(_heights)-1,0,-1):
        if alt > _heights[i]:
            return _basetemps[i] + _lapsert[i] * (alt - _heights[i])
    return _stdtemp + _lapsert[0] * alt

def altitude_to_pressure(alt):
    """Convert an altitude (meters) to pressure (Pascals)"""
    for i in range(len(_heights)-1,0,-1):
        h0 = _heights[i]
        T0 = _basetemps[i]
        if alt > h0:
            if _isotherm[i]:
                rP = math.exp(-_g / _R / T0 * (alt - h0))
            else:
                l0 = _lapsert[i]
                rP = math.pow(1 + (alt - h0) * l0 / T0, -_g / _R / l0)
            return _basepress[i] * rP
    l0 = _lapsert[0]
    return _stdpres * math.pow(1 + alt * l0 / _stdtemp, -_g / _R / l0)

def pressure_to_altitude(pres):
    """Convert a pressure (Pascals) to altitude (meters)"""
    for i in range(len(_heights)-1,0,-1):
        P0 = _basepress[i]
        T0 = _basetemps[i]
        if pres < P0:
            if _isotherm[i]:
                dh = _R * T0 / _g * math.log(P0 / pres)
            else:
                l0 = _lapsert[i]
                dh = T0 / l0 * (math.pow(pres / P0, -l0 * _R / _g) - 1)
            return _heights[i] + dh
    l0 = _lapsert[0]
    return _stdtemp / l0 * (math.pow(pres / _stdpres, -l0 * _R / _g) - 1)
