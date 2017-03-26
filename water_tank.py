#!/usr/bin/env python3

from adc import ADS1115, ADCFilter
from settings import UR, WATER_TANK_CONFIG


class LinearInterpolation:
    """
    Interpolate a 1-D function.

    `x` and `y` are arrays of values used to approximate some function f: ``y = f(x)``.
    """

    def __init__(self, x, y):
        if len(x) != len(y):
            raise Exception('Arrays must have the same number of elements')
        if len(x) < 2:
            raise Exception('At least two points are required')
        self.x = x
        self.y = y

    def __call__(self, x_new):
        distances = [abs(v - x_new) for v in self.x]
        indexes = list(range(len(distances)))
        indexes.sort(key=distances.__getitem__)
        i1 = indexes[0]
        i2 = indexes[1]

        x1 = self.x[i1]
        x2 = self.x[i2]
        y1 = self.y[i1]
        y2 = self.y[i2]

        return y1 + (x_new - x1) / (x2 - x1) * (y2 - y1)


class PressureInterface:
    """
    MP3V5050DP pressure sensor interface.
    """

    # ADC data rate
    adc_sps = 64

    sensitivity = 54 * UR.mV / UR.kPa

    def __init__(self, i2c_busn, i2c_addr, adc_channel, adc_fsr, pressure_offset):
        self.adc = ADS1115(i2c_busn, i2c_addr)
        self.adc.config(adc_channel, adc_fsr, self.adc_sps)
        self.adc = ADCFilter(self.adc, samples_count=self.adc_sps)
        self.pressure_offset = pressure_offset

    def get_pressure_and_voltage(self):
        voltage = self.adc.get_voltage()
        pressure = voltage / self.sensitivity - self.pressure_offset
        return pressure, voltage

    def get_pressure(self):
        return self.get_pressure_and_voltage()[0]


class WaterTankInterface:
    """
    Complete water tank interface with calibration.
    """

    def __init__(self, config):
        pass

    def get_volume(self):
        return 0 * UR.L


def main():
    tank = WaterTankInterface(WATER_TANK_CONFIG)
    while True:
        try:
            volume = tank.get_volume()
            print('{:~5.1fP}'.format(volume.to('L')))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
