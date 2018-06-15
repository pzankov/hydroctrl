#!/usr/bin/env python3

from settings import UR, PH_CONFIG
from adc import MCP3221, ADCFilter
from temperature import TemperatureInterface, ConstTemperatureInterface


class PHTheory:
    """
    A set of pH electrode functions.

    Functions are derived from the following equation:
    V = Voffset - slope * R * T * LN10 / F * (pH - 7)
    Voffset = V_pH7 + V_ADC_Offset
    """

    @staticmethod
    def ideal_slope(temp):
        """Slope of the ideal pH electrode, in V/pH"""

        # Make sure value is valid
        if temp < 0 * UR.degC or temp > 100 * UR.degC:
            raise Exception('Temperature is out of range')

        # Properties of this Universe
        gas_const = 8.3144
        faraday_const = 96485
        ln_10 = 2.3026

        temp_K = temp.to('degK').magnitude
        slope_V_pH = gas_const * temp_K * ln_10 / faraday_const

        return slope_V_pH * UR.volt / UR.pH

    @staticmethod
    def compute_slope(temp, ph1, v1, ph2, v2):
        """Relative slope."""
        return (v1 - v2) / (ph2 - ph1) / PHTheory.ideal_slope(temp)

    @staticmethod
    def compute_offset(temp, slope, ph, v):
        """Offset voltage (including the ADC offset)."""
        return v + slope * PHTheory.ideal_slope(temp) * (ph - 7 * UR.pH)

    @staticmethod
    def compute_ph(temp, offset, slope, v):
        ph = 7 * UR.pH + (offset - v) / (slope * PHTheory.ideal_slope(temp))

        # Pint forgets to convert Quantity with uncertainty into Measurement
        if type(ph) == UR.Quantity:
            ph = UR.Measurement(ph.magnitude.nominal_value, ph.magnitude.std_dev, ph.units)

        return ph


class PHCalibration:
    """
    pH electrode calibration.
    """

    # Acceptable electrode properties
    max_slope_drift = 0.2
    max_offset_drift = 30 * UR.mV

    def __init__(self, adc_offset, temp, points):
        if len(points) != 2:
            raise Exception('Only two point calibration is supported')

        self.slope = PHTheory.compute_slope(
            temp,
            points[0]['ph'], points[0]['v'],
            points[1]['ph'], points[1]['v'])

        self.offset = PHTheory.compute_offset(
            temp, self.slope,
            points[0]['ph'], points[0]['v'])

        # Check slope
        if abs(self.slope - 1) > self.max_slope_drift:
            raise Exception('pH electrode slope {:~.2f} is unacceptable'.format(self.slope))

        # Check offset
        offset = self.offset - adc_offset
        if abs(offset) > self.max_offset_drift:
            raise Exception('pH electrode offset {:~.0f} is unacceptable'.format(offset.to('mV')))

        print('pH electrode slope={:~.2f} offset={:~.0f}'.format(self.slope, offset.to('mV')))

    def compute_ph(self, temp, v):
        return PHTheory.compute_ph(temp, self.offset, self.slope, v)


class PHInterface:
    """
    Complete pH electrode interface with
    calibration and temperature compensation.
    """

    def __init__(self, config):
        adc = MCP3221(
            i2c_busn=config['adc']['i2c_busn'],
            i2c_addr=config['adc']['i2c_addr'],
            v_ref=config['adc']['v_ref'])

        self.adc = ADCFilter(
            adc=adc,
            samples_count=config['adc']['filter_samples'])

        self.calibration = PHCalibration(
            adc_offset=config['adc']['v_off'],
            temp=config['calibration']['temperature'],
            points=config['calibration']['points'])

        if 'device_id' in config['temperature']:
            self.temperature = TemperatureInterface(config['temperature']['device_id'])
        else:
            self.temperature = ConstTemperatureInterface(config['temperature']['value'])

    def get_t_v_ph(self):
        temperature = self.temperature.get_temperature()
        voltage = self.adc.get_voltage()
        ph = self.calibration.compute_ph(temperature, voltage)
        return temperature, voltage, ph


def main():
    interface = PHInterface(PH_CONFIG)
    while True:
        try:
            t, v, ph = interface.get_t_v_ph()
            print('{:~.1fP}  {:~.3fP}  {:~.2fP}'.format(t.to('degC'), v.to('V'), ph.to('pH')))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
