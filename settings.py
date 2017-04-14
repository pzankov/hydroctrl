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
    'supply_tank_L',
    'nutrients_mL'
)

PH_CONFIG = {
    'adc': {
        'i2c_busn': 1,
        'i2c_addr': 0x4F,
        'v_ref': 2.5 * UR.V,
        'v_off': 1.251 * UR.V,
        'filter_samples': 256
    },
    'calibration': {
        'temperature': 21 * UR.degC,
        'points': (
            {'ph': 4.0 * UR.pH, 'v': 1.418 * UR.V},
            {'ph': 7.0 * UR.pH, 'v': 1.246 * UR.V}
        )
    }
}

SUPPLY_TANK_CONFIG = {
    'adc': {
        'i2c_busn': 1,
        'i2c_addr': 0x48,
        'channel': 2,
        'fsr': 1024 * UR.mV,
        'sps': 64
    },
    'calibration': {
        'pressure_offset': 26.5 * UR.cmH2O,
        'points': (
            {'pressure': 0 * UR.cmH2O, 'volume': 25 * UR.L},
            {'pressure': 5.9 * UR.cmH2O, 'volume': 50 * UR.L},
            {'pressure': 16.3 * UR.cmH2O, 'volume': 100 * UR.L},
            {'pressure': 36.8 * UR.cmH2O, 'volume': 200 * UR.L},
            {'pressure': 58.7 * UR.cmH2O, 'volume': 300 * UR.L},
        )
    }
}

SOLUTION_TANK_CONFIG = {
    'gpio_float_switch': 22,
    'float_switch_state_when_full': 0
}

PUMP_CONFIG = {
    'gpio_sleep': 17,
    'gpio_step': 27,
    'wake_up_time': 1 * UR.ms,
    'max_frequency': 1 * UR.Hz,
    'step_angle': 1.8 * UR.deg,
    'steps_per_volume': 1050 / UR.mL,
    'microsteps': 16
}

CONTROLLER_CONFIG = {
    'valid_temperature_range': (5 * UR.degC, 40 * UR.degC),
    'valid_ph_range': (4 * UR.pH, 8 * UR.pH),
    'valid_supply_tank_volume_range': (0 * UR.L, 325 * UR.L),
    'nutrients_concentration_per_ph': 1.65 * UR.mL / UR.L / UR.pH,
    'min_pumped_nutrients': 1 * UR.mL,
    'desired_ph': 6.0 * UR.pH,
    'solution_volume': 50 * UR.L,
    'proportional_k': 0.5,
    'iteration_period': 15 * UR.min
}
