#!/usr/bin/env python3

import time
from datetime import datetime
from google import GoogleSheet
from thingspeak import Thingspeak
from scheduler import Scheduler
from utils import log_init, log, log_exception, wait_for_ntp
import settings


class Controller:
    """
    Controller class.
    """

    def __init__(self):
        self.database = None
        self.thingspeak = None
        self.scheduler = Scheduler(settings.CONTROLLER_PERIOD_MINUTES, self._sample)

    def run(self):
        wait_for_ntp()

        self.database = GoogleSheet()
        self.thingspeak = Thingspeak()

        self.scheduler.run()

    def _sample(self):
        log('Sampling data')

        date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {'date': date, 'temperature_C': 25, 'pH': 6.0, 'volume_L': 250, 'nutrients_mL': 0}

        try:
            self.database.append(data)
        except Exception:
            log_exception('Database append failed')
            return  # this is a fatal error

        try:
            self.thingspeak.append(data)
        except Exception:
            log_exception('Thingspeak append failed')
            pass  # not a fatal error


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
