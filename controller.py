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
    Wait until NTP selects a peer.
    """

    log('Waiting for NTP, press Ctrl+C to skip')
    try:
        while True:
            output = subprocess.check_output(['ntpq', '-pn'])
            lines = output.splitlines()[2:]  # skip header lines
            for l in lines:
                if l[0] == ord('*'):  # sync peer is labelled with a star
                    return
            log('Waiting for NTP')
            time.sleep(5)
    except KeyboardInterrupt:
        log('NTP status check skipped')


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
