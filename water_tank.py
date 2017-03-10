#!/usr/bin/env python3

import settings


class WaterTankInterface:
    """
    Complete water tank interface with calibration.
    """

    def __init__(self, config):
        pass

    def get_volume(self):
        return 0


def main():
    tank = WaterTankInterface(settings.WATER_TANK)
    while True:
        try:
            volume = tank.get_volume()
            print('%5.1fL' % volume)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
