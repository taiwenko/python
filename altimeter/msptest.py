#!/usr/bin/env python
import math
import re
import serial

N = 100
port = serial.Serial('/dev/ttyUSB0', 9600)
port.setRTS(True)

while True:
    # Reset counters
    n = 0
    Sx = 0.0
    Sx2 = 0.0
    cts = 0
    # Collect data
    while n < N:
        line = port.readline()
        match = re.match(r'ADC (-?\d+)', line)
        if match:
            x = float(match.group(1))
            n = n + 1
            Sx = Sx + x
            Sx2 = Sx2 + x * x
            if port.getCTS():
                cts = cts + 1
    # Display results
    mean = Sx / n
    var = (Sx2 - Sx * Sx / n) / (n - 1)
    sigma = math.sqrt(var)
    cts = float(n) / cts
    print "<x> = %.0f\ns_x = %g\ncts score %g" % (mean, sigma, cts)
