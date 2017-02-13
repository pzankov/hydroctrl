#!/usr/bin/env python3

import time
from datetime import datetime
from google import GoogleSheet
from thingspeak import Thingspeak
from scheduler import Scheduler
from utils import log_init, log_info, log_err, log_exception_trace, wait_for_ntp, retry
from temperature import TemperatureInterface
from ph import PHInterface
from pump import PumpInterface
import settings


class Controller:
    """
    Controller class.
    """

    def __init__(self):
        self.database = None
        self.thingspeak = None
        self.scheduler = Scheduler(settings.CONTROLLER_PERIOD_MINUTES, self._do_iteration)
        self.temperature = TemperatureInterface()
        self.ph = PHInterface()
        self.pump = PumpInterface()

    def run(self):
        # Synchronize clock (we don't have a RTC module)
        wait_for_ntp()

        self.database = GoogleSheet()
        self.thingspeak = Thingspeak()

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


def main():
    log_init()

    while True:
        try:
            log_info('Starting controller')
            ctrl = Controller()
            ctrl.run()
            raise Exception('Controller stopped running')
        except Exception:
            log_err('Unexpected controller exception')
            log_exception_trace()
        time.sleep(60)


if __name__ == '__main__':
    main()
