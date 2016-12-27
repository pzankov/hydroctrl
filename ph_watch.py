#!/usr/bin/env python3

from ph import PHInterface
from temperature import TemperatureInterface


def main():
    temperature = TemperatureInterface()
    ph = PHInterface()
    while True:
        temp = temperature.get_temperature()
        data = ph.get_voltage_and_ph(temp)
        print('%.1fC %.3fV %.2fpH' % (temp, data['voltage'], data['ph']))


if __name__ == '__main__':
    main()
