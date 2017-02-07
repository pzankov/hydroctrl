#!/usr/bin/env python3

from ph import PHInterface
from temperature import TemperatureInterface


def main():
    temperature = TemperatureInterface()
    ph = PHInterface()
    while True:
        temp = temperature.get_temperature()
        data = ph.get_ph_with_stat(temp)
        print('%.1fC  %.3fV +- %2.0fmV  %.2fpH +- %.2fpH' %
              (temp, data['voltage'], data['voltage_dev'] * 1e3, data['ph'], data['ph_dev']))


if __name__ == '__main__':
    main()
