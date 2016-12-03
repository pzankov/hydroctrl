DATABASE_PATH = '/mnt/database/storage/db'

PH_ADC_I2C_BUSN = 1
PH_ADC_I2C_ADDR = 0x4F

PH_ADC_REF_V = 3.0
PH_ADC_BITS = 12

PH_CALIBRATION = {
    'temp': 23,
    'points': (
        {'ph': 4.0, 'v': 1.6745},
        {'ph': 7.0, 'v': 1.5}
    )
}

TEMP_SPI_BUSN = 0
TEMP_SPI_DEVN = 0

DIST_GPIO_TRIG = 23
DIST_GPIO_ECHO = 24
