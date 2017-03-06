#!/usr/bin/env python3

from datetime import datetime
from google import GoogleSheet
from thingspeak import Thingspeak
from scheduler import Scheduler
from utils import log_init, log_info, log_warn, log_err, log_exception_trace, wait_for_ntp, retry
from temperature import TemperatureInterface
from ph import PHInterface
from pump import PumpInterface
import settings


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

    def __init__(self):
        self.database = None
        self.thingspeak = None
        self.scheduler = Scheduler(settings.CONTROLLER_PERIOD_MINUTES, self._do_iteration_nothrow)
        self.temperature = TemperatureInterface()
        self.ph = PHInterface(settings.PH)
        self.pump = PumpInterface(settings.PUMP)

    def run(self):
        # Synchronize clock (we don't have a RTC module)
        wait_for_ntp()

        # These objects require internet connection
        self.database = GoogleSheet()
        self.thingspeak = Thingspeak()

        # Enter the control loop
        self.scheduler.run()

    def _estimate_nutrients(self, pH):
        if pH < settings.DESIRED_PH:
            return 0

        nutrients_per_pH = settings.NUTRIENTS_CONCENTRATION_PER_PH * settings.SOLUTION_VOLUME
        pH_error = pH - settings.DESIRED_PH

        nutrients = nutrients_per_pH * pH_error * settings.PROPORTIONAL_K

        if nutrients < settings.MIN_PUMPED_NUTRIENTS:
            return 0

        return nutrients

    def _do_iteration(self):
        log_info('Starting a new iteration')

        date = datetime.utcnow()

        temperature = self.temperature.get_temperature()
        pH = self.ph.get_ph(temperature)
        tank_volume = 250

        nutrients = self._estimate_nutrients(pH)

        data = {
            'date': date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'temperature_C': '%.1f' % temperature,
            'pH': '%.2f' % pH,
            'water_tank_L': '%.0f' % tank_volume,
            'nutrients_mL': '%.1f' % (nutrients * 1e3)
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
        ctrl = Controller()
        ctrl.run()

        log_err('Controller stopped running')
    except Exception as e:
        log_err('Unexpected exception: ' + str(e))
        log_exception_trace()


if __name__ == '__main__':
    main()
