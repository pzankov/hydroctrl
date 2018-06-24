#!/usr/bin/env python3

from datetime import datetime
from google import GoogleSheet
from thingspeak import Thingspeak
from scheduler import Scheduler
from utils import log_init, log_info, log_warn, log_err, log_exception_trace
from utils import wait_for_ntp, retry, in_range, drop_uncertainty
from ph import PHInterface
from pump import PumpInterface
from solution_tank import SolutionTankInterface
from water_tank import WaterTankInterface
from temperature import TemperatureInterface
from settings import UR
from settings import CONTROLLER_CONFIG, PH_CONFIG, PUMP_X_CONFIG, PUMP_Y_CONFIG, \
    SOLUTION_TANK_CONFIG, SUPPLY_TANK_CONFIG


class FatalException(Exception):
    """
    Throw this to exit the control loop,
    e.g. if a sensor failure was detected.
    """
    pass


class Controller:
    """
    Controller class.
    """

    def __init__(self, config, ph_config, pump_x_config, pump_y_config,
                 solution_tank_config, supply_tank_config):
        self.database = None
        self.thingspeak = None
        self.ph = PHInterface(ph_config)
        self.pump_x = PumpInterface(pump_x_config)
        self.pump_y = PumpInterface(pump_y_config)
        self.solution_tank = SolutionTankInterface(solution_tank_config)
        self.supply_tank = WaterTankInterface(supply_tank_config)
        self.scheduler = Scheduler(config['iteration_period'], self._do_iteration_throw_only_fatal)
        self.valid_ph_range = config['valid_ph_range']
        self.valid_ph_temperature_range = config['valid_ph_temperature_range']
        self.valid_supply_tank_volume_range = config['valid_supply_tank_volume_range']
        self.nutrients_concentration_per_ph = config['nutrients_concentration_per_ph']
        self.pump_volume_limits = config['pump_volume_limits']
        self.desired_ph = config['desired_ph']
        self.solution_volume = config['solution_volume']
        self.proportional_k = config['proportional_k']
        self.solution_tank_is_full = True
        if 'temperature_device_id' in config:
            self.temperature = TemperatureInterface(config['temperature_device_id'])

    def run(self):
        # Synchronize clock (we don't have a RTC module)
        wait_for_ntp()

        # These objects require internet connection
        self.database = GoogleSheet()
        self.thingspeak = Thingspeak()

        # Enter the control loop
        self.scheduler.run()

    def _estimate_nutrients(self, ph):
        if ph < self.desired_ph:
            return 0 * UR.L

        nutrients_per_ph = self.nutrients_concentration_per_ph * self.solution_volume
        ph_error = ph - self.desired_ph

        nutrients = nutrients_per_ph * ph_error * self.proportional_k

        if nutrients < min(self.pump_volume_limits):
            return 0 * UR.L
        elif nutrients > max(self.pump_volume_limits):
            return max(self.pump_volume_limits)
        else:
            return nutrients

    def _do_iteration(self):
        log_info('Starting a new iteration')

        date = datetime.utcnow()

        # Update the solution tank state
        solution_tank_was_full = self.solution_tank_is_full
        self.solution_tank_is_full = self.solution_tank.is_full()

        # Volume is unknown and pH sensor can be dry
        if not self.solution_tank_is_full:
            raise Exception('Solution tank is empty')

        # Skip one more iteration to let the pH readings stabilize
        if not solution_tank_was_full:
            raise Exception('Solution tank has been empty for a while')

        temperature, _, ph = drop_uncertainty(*self.ph.get_t_v_ph())
        if not in_range(ph, self.valid_ph_range):
            raise FatalException('Invalid pH: {:~.3gP}'.format(ph))
        if not in_range(temperature, self.valid_ph_temperature_range):
            raise FatalException('Invalid pH temperature: {:~.3gP}'.format(temperature))

        if hasattr(self, 'temperature'):
            temperature = self.temperature.get_temperature()

        supply_tank_volume = drop_uncertainty(self.supply_tank.get_volume())
        if not in_range(supply_tank_volume, self.valid_supply_tank_volume_range):
            raise FatalException('Invalid supply tank volume: {:~.3gP}'.format(supply_tank_volume))

        nutrients = self._estimate_nutrients(ph)

        data = {
            'date': date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'temperature_C': '%.1f' % temperature.m_as('degC'),
            'pH': '%.2f' % ph.m_as('pH'),
            'supply_tank_L': '%.0f' % supply_tank_volume.m_as('L'),
            'nutrients_mL': '%.1f' % nutrients.m_as('mL')
        }

        retry(lambda: self.database.append(data), 'Database append failed')

        # Data is already in DB, ignore Thingspeak errors
        retry(lambda: self.thingspeak.append(data), 'Thingspeak append failed', rethrow=False)

        # We only add nutrients after their amount was logged to DB
        self.pump_x.pump(nutrients)
        self.pump_y.pump(nutrients)

    def _do_iteration_throw_only_fatal(self):
        try:
            self._do_iteration()
        except FatalException:
            # Stop iterating
            raise
        except Exception as e:
            # Ignore all other possibly transient errors
            log_warn('Iteration failed: ' + str(e))
            log_exception_trace()


def main():
    log_init()
    log_info('Starting controller')

    try:
        ctrl = Controller(CONTROLLER_CONFIG, PH_CONFIG, PUMP_X_CONFIG, PUMP_Y_CONFIG,
                          SOLUTION_TANK_CONFIG, SUPPLY_TANK_CONFIG)
        ctrl.run()

        log_err('Controller stopped running')
    except Exception as e:
        log_err(str(e))
        log_exception_trace()


if __name__ == '__main__':
    main()
