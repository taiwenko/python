import sys, time, serial

eol = '\r\n'

class XLN6024():
    _public_methods_ = [
        "Initialize",
        "SetVoltage",
        "SetCurrent",
        "GetCurrent",
        "TurnPowerOn",
        "TurnPowerOff",
        "GetProductInformation",
        ]
    def Initialize(self, com_port, baudrate):
        self.sp = serial.Serial(com_port, baudrate, timeout = 1)
    def SetVoltage(self, v):
        return self.sp.write('VOLT ' + ('%.1f' % v) + eol)
    def SetCurrent(self, i):
        return self.sp.write('CURR ' + ('%.1f' % i) + eol)
    def GetCurrent(self):
        self.sp.write('IOUT?' + eol)
        return float(self.sp.readline())
    def TurnPowerOn(self):
        self.sp.write('OUT ON' + eol)
    def TurnPowerOff(self):
        self.sp.write('OUT OFF' + eol)
    def GetProductInformation(self):
        self.sp.write("*IDN?\r\n")
        return self.sp.readline()

