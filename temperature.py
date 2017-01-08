#!/usr/bin/env python3

import glob
from os import path


class TemperatureInterface:
    """
    DS18B20 interface.
    """

    def __init__(self):
        devices = glob.glob('/sys/bus/w1/devices/28-*')
        if len(devices) == 0:
            raise Exception('No devices found')
        if len(devices) > 1:
            raise Exception('Found too many devices')

        self.file_path = path.join(devices[0], 'w1_slave')
        if not path.isfile(self.file_path):
            raise Exception('File %s does not exist' % self.file_path)

    def get_temperature(self):
        lines = [line.strip() for line in open(self.file_path)]
        if len(lines) != 2:
            raise Exception('Invalid lines count')

        if not lines[0].endswith(' YES'):
            raise Exception('CRC check failed')

        value = lines[1][-5:]
        return int(value) / 1e3


def main():
    t = TemperatureInterface()
    print(t.get_temperature())


if __name__ == '__main__':
    main()
