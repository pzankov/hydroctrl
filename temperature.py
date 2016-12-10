#!/usr/bin/env python3

import spidev
import settings


class TemperatureInterface:
    """
    MAX6675 interface.
    """

    # Limit frequency
    spi_frequency = 100e3

    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(settings.TEMPERATURE_SPI_BUSN, settings.TEMPERATURE_SPI_DEVN)
        self.spi.max_speed_hz = int(self.spi_frequency)

    def get_temp(self):
        bytes = self.spi.readbytes(2)
        word = (bytes[0] << 8) + bytes[1]

        thermocouple_status = word & (1 << 2)
        if thermocouple_status != 0:
            return 0

        temperature = (word >> 3) / 4.0
        return temperature


def main():
    t = TemperatureInterface()
    print(t.get_temp())


if __name__ == '__main__':
    main()
