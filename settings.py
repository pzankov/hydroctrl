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
    'water_tank_L',
    'nutrients_mL'
)

PH = {
    'adc': {
        'i2c_busn': 1,
        'i2c_addr': 0x4F,
        'v_ref': 2.5,
        'v_off': 1.251,
    },
    'calibration': {
        'temperature': 21.2,
        'points': (
            {'ph': 4.0, 'voltage': 1.418},
            {'ph': 7.0, 'voltage': 1.224}
        )
    }
}

WATER_TANK = {
}

PUMP = {
    'gpio_sleep': 17,
    'gpio_step': 27,
    'wake_up_time': 1e-3,
    'step_angle': 1.8,
    'microsteps': 8,
    'max_rpm': 180,
    'steps_per_litre': 8.4e6
}

NUTRIENTS_CONCENTRATION_PER_PH = 1.65e-3

MIN_PUMPED_NUTRIENTS = 1e-3

DESIRED_PH = 6.0

SOLUTION_VOLUME = 10

PROPORTIONAL_K = 0.5

CONTROLLER_PERIOD_MINUTES = 5
