#!/usr/bin/env python3

import spidev
import settings
import time
from statistics import mean


class TemperatureInterface:
    """
    MAX6675 interface.
    """

    # Limit SPI frequency
    spi_frequency = 100e3

    # Chip property
    conversion_time = 0.25

    # Noise filtering
    filter_samples = 16

    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(settings.TEMPERATURE_SPI_BUSN, settings.TEMPERATURE_SPI_DEVN)
        self.spi.max_speed_hz = int(self.spi_frequency)

    def _get_temperature(self):
        data = self.spi.readbytes(2)
        word = (data[0] << 8) + data[1]

        thermocouple_status = word & (1 << 2)
        if thermocouple_status != 0:
            raise Exception('Thermocouple is not connected')

        temperature = (word >> 3) / 4.0
        return temperature

    def get_temperature(self):
        values = []
        for n in range(0, self.filter_samples):
            values.append(self._get_temperature())
            if n != self.filter_samples - 1:
                time.sleep(self.conversion_time)
        return mean(values)


def main():
    t = TemperatureInterface()
    print(t.get_temperature())


if __name__ == '__main__':
    main()
