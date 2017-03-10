#!/usr/bin/env python3

from settings import UR, WATER_TANK_CONFIG


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
