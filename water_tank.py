#!/usr/bin/env python3

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
