#!/usr/bin/env python3

from adc import ADS1115, ADCFilter
from settings import UR, SUPPLY_TANK_CONFIG


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

        y_new = y1 + (x_new - x1) / (x2 - x1) * (y2 - y1)

        # Pint forgets to convert Quantity with uncertainty into Measurement
        if type(y_new) == UR.Quantity:
            y_new = UR.Measurement(y_new.magnitude.nominal_value, y_new.magnitude.std_dev, y_new.units)

        return y_new


class PressureSensorCalibration:
    """
    MP3V5050DP pressure sensor calibration.
    """

    # Sensitivity is constant (see Datasheet)
    sensitivity = 54 * UR.mV / UR.kPa

    def __init__(self, pressure_offset):
        self.pressure_offset = pressure_offset

    def compute_pressure(self, voltage):
        return voltage / self.sensitivity - self.pressure_offset


class PressureSensorInterface:
    """
    Complete MP3V5050DP pressure sensor interface with calibration.
    """

    def __init__(self, config):
        adc_sps = config['adc']['sps']

        adc = ADS1115(
            i2c_busn=config['adc']['i2c_busn'],
            i2c_addr=config['adc']['i2c_addr'])

        adc.config(
            channel=config['adc']['channel'],
            fsr=config['adc']['fsr'],
            sps=adc_sps)

        self.adc = ADCFilter(
            adc=adc,
            samples_count=adc_sps)

        self.calibration = PressureSensorCalibration(
            pressure_offset=config['calibration']['pressure_offset'])

    def get_pressure_and_voltage(self):
        voltage = self.adc.get_voltage()
        pressure = self.calibration.compute_pressure(voltage)
        return pressure, voltage

    def get_pressure(self):
        return self.get_pressure_and_voltage()[0]


class WaterTankInterface:
    """
    Complete water tank interface with calibration.
    """

    def __init__(self, config):
        points = config['calibration']['points']
        self.calibration = LinearInterpolation(
            x=[p['pressure'] for p in points],
            y=[p['volume'] for p in points])

        self.sensor = PressureSensorInterface(config)

    def get_volume_and_pressure_and_voltage(self):
        pressure, voltage = self.sensor.get_pressure_and_voltage()
        volume = self.calibration(pressure)
        return volume, pressure, voltage

    def get_volume(self):
        return self.get_volume_and_pressure_and_voltage()[0]


def main():
    tank = WaterTankInterface(SUPPLY_TANK_CONFIG)
    while True:
        try:
            volume, pressure, voltage = tank.get_volume_and_pressure_and_voltage()
            print('{:~.1fP}  {:~.1fP}  {:~.1fP}'.format(voltage.to('mV'), pressure.to('cmH2O'), volume.to('L')))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
