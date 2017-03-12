import smbus
from statistics import mean, pstdev


class MCP3221:
    """
    MCP3221 ADC interface.
    """

    adc_bits = 12

    def __init__(self, i2c_busn, i2c_addr, v_ref):
        self.i2c_addr = i2c_addr
        self.v_ref = v_ref
        self.i2c = smbus.SMBus(i2c_busn)

    def value_to_voltage(self, value):
        return float(value) / (1 << self.adc_bits) * self.v_ref

    def get_value(self):
        reading = self.i2c.read_i2c_block_data(self.i2c_addr, 0x00, 2)
        return (reading[0] << 8) + reading[1]

    def get_voltage(self):
        value = self.get_value()
        return self.value_to_voltage(value)


class ADCFilter:
    """
    ADC noise filtering.
    """

    def __init__(self, adc, samples_count=256):
        self.adc = adc
        self.samples_count = samples_count

    def get_voltage(self):
        samples = []
        for n in range(0, self.samples_count):
            samples.append(self.adc.get_value())

        value = mean(samples)
        value_dev = pstdev(samples)

        voltage = self.adc.value_to_voltage(value)
        voltage_dev = self.adc.value_to_voltage(value_dev)

        return voltage.plus_minus(voltage_dev)
