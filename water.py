#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import settings


class DistanceInterface:
    """
    Ultrasonic distance meter JSN-SR04T
    """

    def __init__(self):
        warmup_time = 0.1

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(settings.DIST_GPIO_TRIG, GPIO.OUT)
        GPIO.setup(settings.DIST_GPIO_ECHO, GPIO.IN)

        GPIO.output(settings.DIST_GPIO_TRIG, False)
        time.sleep(warmup_time)

    def __del__(self):
        GPIO.cleanup()

    def get_distance(self):
        trig_hold_time = 10e-6
        sound_speed = 343.21
        dist_min = 0.23
        dist_max = 2

        # Limit polling loop iterations, this is faster than comparing time
        # Normally less than 5000 iterations are needed
        poll_cycle_limit = 10 * 1000

        GPIO.output(settings.DIST_GPIO_TRIG, True)
        time.sleep(trig_hold_time)
        GPIO.output(settings.DIST_GPIO_TRIG, False)

        start = None
        end = None

        for t in range(0, poll_cycle_limit):
            if GPIO.input(settings.DIST_GPIO_ECHO) == 1:
                start = time.time()
                break

        for t in range(0, poll_cycle_limit):
            if GPIO.input(settings.DIST_GPIO_ECHO) == 0:
                end = time.time()
                break

        if start is None or end is None:
            return 0

        dist = (end - start) * sound_speed / 2

        if dist < dist_min or dist > dist_max:
            return 0

        return dist


def main():
    d = DistanceInterface()
    print("%3.1f" % (d.get_distance() * 100))


if __name__ == "__main__":
    main()
