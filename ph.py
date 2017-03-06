#!/usr/bin/env python3

import settings
from adc import MCP3221, ADCFilter
from temperature import TemperatureInterface


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

        # To be sure value is valid
        if temp < 0 or temp > 100:
            raise Exception('Temperature is out of range')

        # Properties of this Universe
        gas_const = 8.3144
        faraday_const = 96485
        abs_zero_temp = -273.15
        ln_10 = 2.3026

        return gas_const * (temp - abs_zero_temp) * ln_10 / faraday_const

    @staticmethod
    def compute_slope(temp, ph1, v1, ph2, v2):
        """Relative slope of the pH electrode. Equals 1 for the ideal electrode."""
        return (v1 - v2) / (ph2 - ph1) / PHTheory.ideal_slope(temp)

    @staticmethod
    def compute_offset(temp, slope, ph, v):
        """Offset voltage"""
        return v + slope * PHTheory.ideal_slope(temp) * (ph - 7)

    @staticmethod
    def compute_ph(temp, offset, slope, v):
        return 7 + (offset - v) / (slope * PHTheory.ideal_slope(temp))


class PHCalibration:
    """
    pH electrode calibration.
    """

    # Acceptable electrode properties (compared to ideal electrode)
    max_slope_drift = 0.2
    max_v_ph7_drift = 30e-3

    def __init__(self, adc_offset, temp, points):
        if len(points) != 2:
            raise Exception('Only two point calibration is supported')

        self.slope = PHTheory.compute_slope(
            temp,
            points[0]['ph'], points[0]['voltage'],
            points[1]['ph'], points[1]['voltage'])

        self.offset = PHTheory.compute_offset(
            temp, self.slope,
            points[0]['ph'], points[0]['voltage'])

        # Check slope
        if abs(self.slope - 1) > self.max_slope_drift:
            raise Exception('Electrode slope %.2f is out of range, replace the electrode' % self.slope)

        # Check offset
        v_ph7 = self.offset - adc_offset
        if abs(v_ph7) > self.max_v_ph7_drift:
            raise Exception('Electrode offset %.0f mV is out of range, replace the electrode' % (v_ph7 * 1e3))

        print('pH electrode status: slope %.2f, offset %.0f mV' % (self.slope, v_ph7 * 1e3))

    def compute_ph(self, temp, v):
        return PHTheory.compute_ph(temp, self.offset, self.slope, v)


class PHInterface:
    """
    Complete pH electrode interface with
    calibration and temperature compensation.
    """

    def __init__(self, config):
        self.adc = MCP3221(
            i2c_busn=config['adc']['i2c_busn'],
            i2c_addr=config['adc']['i2c_addr'],
            v_ref=config['adc']['v_ref'])

        self.adc = ADCFilter(self.adc)

        self.calibration = PHCalibration(
            adc_offset=config['adc']['v_off'],
            temp=config['calibration']['temperature'],
            points=config['calibration']['points'])

    def get_ph(self, temp):
        voltage = self.adc.get_voltage()
        return self.calibration.compute_ph(temp, voltage)

    def get_ph_with_stat(self, temp):
        data = self.adc.get_voltage_with_stat()
        data['ph'] = self.calibration.compute_ph(temp, data['voltage'])
        data['ph_dev'] = data['voltage_dev'] / PHTheory.ideal_slope(temp)
        return data


def main():
    temperature = TemperatureInterface()
    ph = PHInterface(settings.PH)
    while True:
        try:
            temp = temperature.get_temperature()
            data = ph.get_ph_with_stat(temp)
            print('%.1fC  %.3fV +- %2.0fmV  %.2fpH +- %.2fpH' %
                  (temp, data['voltage'], data['voltage_dev'] * 1e3, data['ph'], data['ph_dev']))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
