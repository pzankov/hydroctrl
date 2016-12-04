#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import numpy as np
from scipy import interpolate
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


class WaterTankCalibration:
    """
    Convert water depth/height into volume.
    """

    tck = None

    def __init__(self):
        xy = [(p['distance'], p['volume']) for p in settings.WATER_TANK_CALIBRATION]
        xy = sorted(xy, key=lambda p: p[0])
        x = np.array([p[0] for p in xy])
        y = np.array([p[1] for p in xy])
        self.tck = interpolate.splrep(x, y, s=0, k=2)

    def get_volume(self, distance):
        x = np.array([distance])
        y = interpolate.splev(x, self.tck, der=0)
        return y[0]


class WaterTankInterface:
    """
    Complete water tank interface with calibration.
    """

    distanceInterface = None
    calibration = None

    def __init__(self):
        self.distanceInterface = DistanceInterface()
        self.calibration = WaterTankCalibration()

    def get_volume(self):
        distance = self.distanceInterface.get_distance()
        if distance == 0:
            return 0

        volume = self.calibration.get_volume(distance)
        if volume < 0:
            return 0

        return volume


def main():
    tank = WaterTankInterface()
    print("%5.1f" % tank.get_volume())


if __name__ == "__main__":
    main()
