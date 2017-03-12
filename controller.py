#!/usr/bin/env python3

from datetime import datetime
from google import GoogleSheet
from thingspeak import Thingspeak
from scheduler import Scheduler
from utils import log_init, log_info, log_warn, log_err, log_exception_trace, wait_for_ntp, retry
from temperature import TemperatureInterface
from ph import PHInterface
from pump import PumpInterface
from settings import UR, PH_CONFIG, PUMP_CONFIG, CONTROLLER_CONFIG


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

    def __init__(self, config):
        self.database = None
        self.thingspeak = None
        self.scheduler = Scheduler(config['iteration_period'], self._do_iteration_nothrow)
        self.temperature = TemperatureInterface()
        self.ph = PHInterface(PH_CONFIG)
        self.pump = PumpInterface(PUMP_CONFIG)
        self.nutrients_concentration_per_ph = config['nutrients_concentration_per_ph']
        self.min_pumped_nutrients = config['min_pumped_nutrients']
        self.desired_ph = config['desired_ph']
        self.solution_volume = config['solution_volume']
        self.proportional_k = config['proportional_k']

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

        if nutrients < self.min_pumped_nutrients:
            return 0 * UR.L

        return nutrients

    def _do_iteration(self):
        log_info('Starting a new iteration')

        date = datetime.utcnow()

        temperature = self.temperature.get_temperature()
        ph = self.ph.get_ph(temperature).value
        tank_volume = 250 * UR.L

        nutrients = self._estimate_nutrients(ph)

        data = {
            'date': date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'temperature_C': '%.1f' % temperature.m_as('degC'),
            'pH': '%.2f' % ph.m_as('pH'),
            'water_tank_L': '%.0f' % tank_volume.m_as('L'),
            'nutrients_mL': '%.1f' % nutrients.m_as('mL')
        }

        retry(lambda: self.database.append(data), 'Database append failed')

        # Data is already in DB, ignore Thingspeak errors
        retry(lambda: self.thingspeak.append(data), 'Thingspeak append failed', rethrow=False)

        # We only add nutrients after their amount was logged to DB
        self.pump.pump(nutrients)

    def _do_iteration_nothrow(self):
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
        ctrl = Controller(CONTROLLER_CONFIG)
        ctrl.run()

        log_err('Controller stopped running')
    except Exception as e:
        log_err('Unexpected exception: ' + str(e))
        log_exception_trace()


if __name__ == '__main__':
    main()
