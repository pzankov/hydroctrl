#!/usr/bin/env python3

import time
from datetime import datetime
from google import GoogleSheet
from thingspeak import Thingspeak
from scheduler import Scheduler
from utils import log_init, log, log_exception, wait_for_ntp
from temperature import TemperatureInterface
from ph import PHInterface
import settings


class Controller:
    """
    Controller class.
    """

    try_attempts = 3

    def __init__(self):
        self.database = None
        self.thingspeak = None
        self.scheduler = Scheduler(settings.CONTROLLER_PERIOD_MINUTES, self._sample)
        self.temperature = TemperatureInterface()
        self.ph = PHInterface()

    def run(self):
        wait_for_ntp()

        self.database = GoogleSheet()
        self.thingspeak = Thingspeak()

        self.scheduler.run()

    def _try(self, task, exception_msg):
        attempts_left = self.try_attempts
        while True:
            try:
                task()
                return True
            except Exception:
                attempts_left -= 1
                log_exception('%s, %d attempts left' % (exception_msg, attempts_left))
                if attempts_left == 0:
                    return False
            time.sleep(1)

    def _get_data(self):
        date = datetime.utcnow()

        temperature = self.temperature.get_temperature()
        pH = self.ph.get_ph(temperature)
        volume = 250

        data = {
            'date': date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'temperature_C': '%.1f' % temperature,
            'pH': '%.2f' % pH,
            'volume_L': '%.0f' % volume,
            'nutrients_mL': 0
        }

        return data

    def _save_data(self, data):
        # Database is a primary storage
        if not self._try(lambda: self.database.append(data), 'Database append failed'):
            return False

        # It is hard to make an atomic transaction for multiple data storage providers.
        # Simply ignore all other errors.

        self._try(lambda: self.thingspeak.append(data), 'Thingspeak append failed')

        return True

    def _sample(self):
        log('Making a new sample')

        data = self._get_data()
        if data is None:
            log('Failed to get data')
            return

        if not self._save_data(data):
            log('Failed to save data')
            return


def main():
    log_init()

    while True:
        try:
            log('Starting controller')
            ctrl = Controller()
            ctrl.run()
            raise Exception('Controller stopped running')
        except Exception:
            log_exception('Unexpected controller exception')
        time.sleep(60)


if __name__ == '__main__':
    main()
