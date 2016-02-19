"""Smart Battery Specification Interface"""

class Battery(object):
    def __init__(self, i2cbus, addr=0x16):
        self.i2c = i2cbus
        self.addr = addr

    def temperature(self):
        """Current temperature of the battery in Celsius"""
        return self.i2c.read_word_data(self.addr, 0x08) / 10.0 - 273.15
    def voltage(self):
        """Current output voltage of the battery"""
        return self.i2c.read_word_data(self.addr, 0x09) / 1000.0
    def manufacturer(self):
        """Returns the manufacturer name"""
        return self.i2c.read_block_data(self.addr, 0x20)
    def device_name(self):
        """Returns the device name"""
        return self.i2c.read_block_data(self.addr, 0x21)
    def chemistry(self):
        """Returns the device chemistry"""
        return self.i2c.read_block_data(self.addr, 0x22)
    def manufacturer_data(self):
        """Returns the manufacturer data field"""
        return self.i2c.read_block_data(self.addr, 0x23)
