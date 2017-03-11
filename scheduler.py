#!/usr/bin/env python3

import time
from datetime import datetime, timedelta
from settings import UR


class Scheduler:
    """
    Execute job on schedule.

    Keeps per-hour schedule constant.
    E.g. if job is set to run every 20 minutes, it will always be
    executed at HH:00, HH:20 and HH:40.
    """

    def __init__(self, period, job):
        period_minutes = period.m_as('min')
        if not isinstance(period_minutes, int):
            raise Exception('Period must be an integer')
        if period_minutes == 0:
            raise Exception('Period must be greater than zero')
        if 60 % period_minutes != 0:
            raise Exception('Period must be a divider of 60')

        self.period_minutes = period_minutes
        self.job = job

    @staticmethod
    def round_int(value, base):
        return int(value) - int(value) % int(base)

    def round_date(self, date):
        minute = self.round_int(date.minute, self.period_minutes)
        return date.replace(minute=minute, second=0)

    def next_run(self, last_run):
        return self.round_date(last_run) + timedelta(minutes=self.period_minutes)

    def run(self):
        next_run = self.next_run(datetime.utcnow())
        while True:
            now = datetime.utcnow()
            if now > next_run:
                next_run = self.next_run(now)
                self.job()
            time.sleep(1)


def main():
    s = Scheduler(3 * UR.min, None)

    last_run = datetime.now()
    for n in range(1, 3600):
        next_run = s.next_run(last_run)
        print('%s %s' % (last_run.strftime('%H:%M:%S'), next_run.strftime('%H:%M:%S')))
        last_run += timedelta(seconds=1)


if __name__ == '__main__':
    main()
