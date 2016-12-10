#!/usr/bin/env python3

import syslog
import subprocess
import time
from datetime import datetime
from google import GoogleSheet
from thingspeak import Thingspeak


def log(msg):
    print(msg)
    syslog.syslog(msg)


def wait_for_ntp():
    """
    Wait until NTP becomes synchronised.
    NOTE: It make take up to 15min for the NTP status to become synchronised.
    """

    try:
        log('Waiting for NTP to synchronize, press Ctrl+C to skip')
        while True:
            code = subprocess.call('ntpstat')
            if code == 0:
                break
            log('Waiting for NTP to synchronise')
            time.sleep(60)
    except KeyboardInterrupt:
        log('NTP status check skipped')
        pass


class Controller:
    """
    Controller class.
    """

    check_period = 10
    task_period = 5 * 60

    def __init__(self):
        self.database = None
        self.thingspeak = None

    def run(self):
        wait_for_ntp()

        self.database = GoogleSheet()
        self.thingspeak = Thingspeak()

        last = 0
        while True:
            now = time.time()
            if now - last > self.task_period:
                last = now
                self._execute_task()
            time.sleep(self.check_period)

    def _execute_task(self):
        log('Task started')

        date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        data = {'date': date, 'temperature_C': 25, 'pH': 6.0, 'volume_L': 250, 'nutrients_mL': 0}

        try:
            self.database.append(data)
        except Exception as e:
            log('Database append failed: ' + str(e))
            return  # this is a fatal error

        try:
            self.thingspeak.append(data)
        except Exception as e:
            log('Thingspeak append failed: ' + str(e))
            pass  # not a fatal error


def main():
    syslog.openlog('hydroctrl')

    while True:
        try:
            ctrl = Controller()
            ctrl.run()
        except Exception as e:
            log('Controller exception: ' + str(e))
            time.sleep(60)


if __name__ == '__main__':
    main()
