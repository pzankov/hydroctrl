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
        return float(value) * self.v_ref / (1 << self.adc_bits)

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

    def _get_samples(self):
        values = []
        for n in range(0, self.samples_count):
            values.append(self.adc.get_value())
        return values

    def get_value(self):
        values = self._get_samples()
        return mean(values)

    def get_voltage(self):
        value = self.get_value()
        return self.adc.value_to_voltage(value)

    def get_value_with_stat(self):
        values = self._get_samples()
        return {'value': mean(values), 'value_dev': pstdev(values)}

    def get_voltage_with_stat(self):
        data = self.get_value_with_stat()
        data['voltage'] = self.adc.value_to_voltage(data['value'])
        data['voltage_dev'] = self.adc.value_to_voltage(data['value_dev'])
        return data
