from pint import UnitRegistry
from utils import config_file_path


# Instantiate a common units registry
UR = UnitRegistry(autoconvert_offset_to_baseunit=True)
UR.load_definitions(config_file_path('pint.txt'))


# Specify order and name of data columns
DATA_SPEC = (
    'date',
    'temperature_C',
    'pH',
    'water_tank_L',
    'nutrients_mL'
)

PH_CONFIG = {
    'adc': {
        'i2c_busn': 1,
        'i2c_addr': 0x4F,
        'v_ref': 2.5 * UR.V,
        'v_off': 1.251 * UR.V,
    },
    'calibration': {
        'temperature': 21.2 * UR.degC,
        'points': (
            {'ph': 4.0 * UR.pH, 'v': 1.418 * UR.V},
            {'ph': 7.0 * UR.pH, 'v': 1.224 * UR.V}
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
