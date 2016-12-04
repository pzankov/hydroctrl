"""
Unless otherwise stated, following units are used in this project:
- length: metre
- volume: litre
- temperature: Celsius degree
- voltage: Volt
"""

DATABASE_PATH = '/mnt/database/storage/db'

PH_ADC_I2C_BUSN = 1
PH_ADC_I2C_ADDR = 0x4F

PH_ADC_REF_V = 3.0

PH_CALIBRATION = {
    'temperature': 23,
    'points': (
        {'ph': 4.0, 'voltage': 1.6745},
        {'ph': 7.0, 'voltage': 1.5}
    )
}

TEMPERATURE_SPI_BUSN = 0
TEMPERATURE_SPI_DEVN = 0

DISTANCE_GPIO_TRIG = 23
DISTANCE_GPIO_ECHO = 24

WATER_TANK_CALIBRATION = {
    'points': (
        {'distance': 0.8, 'volume': 0},
        {'distance': 0.5, 'volume': 150},
        {'distance': 0.25, 'volume': 300},
    )
}

PUMP_GPIO_STEP = 27

PUMP_CALIBRATION = {
    'steps_per_litre': 1.6e6
}
