"""
Unless otherwise stated, following units are used in this project:
- length: metre
- volume: litre
- temperature: Celsius degree
- voltage: Volt
"""

# Specify order and name of data columns
DATA_SPEC = (
    'date',
    'temperature_C',
    'pH',
    'volume_L',
    'nutrients_mL'
)

PH_ADC_I2C_BUSN = 1
PH_ADC_I2C_ADDR = 0x4F

PH_ADC_V_REF = 2.5
PH_ADC_V_OFFSET = 1.251

PH_CALIBRATION = {
    'temperature': 21.2,
    'points': (
        {'ph': 4.0, 'voltage': 1.418},
        {'ph': 7.0, 'voltage': 1.224}
    )
}

DISTANCE_GPIO_TRIG = 23
DISTANCE_GPIO_ECHO = 24

WATER_TANK_CALIBRATION = {
    'points': (
        {'distance': 0.8, 'volume': 0},
        {'distance': 0.5, 'volume': 150},
        {'distance': 0.25, 'volume': 300},
    )
}

PUMP_GPIO_SLEEP = 17
PUMP_GPIO_STEP = 27

PUMP_CALIBRATION = {
    'steps_per_litre': 8.4e6
}

NUTRIENTS_CONCENTRATION_PER_PH = 1.65e-3

MIN_PUMPED_NUTRIENTS = 1e-3

DESIRED_PH = 6.0

SOLUTION_VOLUME = 10

PROPORTIONAL_K = 0.5

CONTROLLER_PERIOD_MINUTES = 5
