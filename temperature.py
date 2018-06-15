#!/usr/bin/env python3

import os
from os import path
from settings import UR


class TemperatureInterface:
    """
    DS18B20 interface.
    """

    bus_devices_path = '/sys/bus/w1/devices'
    family_code = 0x28

    @classmethod
    def discover_devices(cls):
        prefix = '{:02x}-'.format(cls.family_code)
        bus_devices = os.listdir(cls.bus_devices_path)
        return [x for x in bus_devices if x.startswith(prefix)]

    def __init__(self, device_id):
        self.device_id = device_id
        self.file_path = path.join('/sys/bus/w1/devices', device_id, 'w1_slave')
        if not path.isfile(self.file_path):
            raise Exception('File %s does not exist' % self.file_path)

    def get_temperature(self):
        lines = [line.strip() for line in open(self.file_path)]
        if len(lines) != 2:
            raise Exception('Invalid lines count')

        if not lines[0].endswith(' YES'):
            raise Exception('CRC check failed')

        value = lines[1][lines[1].rindex('=') + 1:]
        temp_C = int(value) / 1000.0

        return temp_C * UR.degC


class ConstTemperatureInterface:
    def __init__(self, value):
        self.value = value

    def get_temperature(self):
        return self.value


def main():
    devices = TemperatureInterface.discover_devices()
    if len(devices) == 0:
        raise Exception('No devices found')

    sensors = [TemperatureInterface(id) for id in devices]
    while True:
        try:
            for s in sensors:
                temperature = s.get_temperature()
                print('{} {}'.format(s.device_id, temperature))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
