#!/usr/bin/env python3

import syslog
import subprocess
import time
from datetime import datetime
from google import GoogleSheet
from thingspeak import Thingspeak
from scheduler import Scheduler
import settings


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
            sync_peers = sum(l[0] == ord('*') for l in lines)  # sync peer is labelled with a star
            if sync_peers > 0:
                break
            log('Waiting for NTP')
            time.sleep(5)
    except KeyboardInterrupt:
        log('NTP status check skipped')

    log('NTP status OK')


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
