#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import numpy as np
from scipy import interpolate
import settings


class DistanceInterface:
    """
    Ultrasonic distance meter JSN-SR04T.
    """

    sound_speed = 343.21  # at 20 C

    # Must be enough to finish send-receive sequence
    warmup_time = 0.1

    # Sensor properties
    trig_hold_time = 10e-6
    dist_min = 0.23
    dist_max = 4

    # Limit polling loop iterations, this is faster than comparing time.
    # Looping speed is limited by GPIO speed. Normally less than 5000 iterations are needed.
    poll_cycle_limit = 10 * 1000

    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(settings.DISTANCE_GPIO_TRIG, GPIO.OUT)
        GPIO.setup(settings.DISTANCE_GPIO_ECHO, GPIO.IN)

        GPIO.output(settings.DISTANCE_GPIO_TRIG, False)
        time.sleep(self.warmup_time)

    def __del__(self):
        GPIO.cleanup()

    def get_distance(self):
        GPIO.output(settings.DISTANCE_GPIO_TRIG, True)
        time.sleep(self.trig_hold_time)
        GPIO.output(settings.DISTANCE_GPIO_TRIG, False)

        start = None
        end = None

        for t in range(0, self.poll_cycle_limit):
            if GPIO.input(settings.DISTANCE_GPIO_ECHO) == 1:
                start = time.time()
                break

        for t in range(0, self.poll_cycle_limit):
            if GPIO.input(settings.DISTANCE_GPIO_ECHO) == 0:
                end = time.time()
                break

        if start is None:
            raise Exception('Could not detect echo start')

        if end is None:
            raise Exception('Could not detect echo end')

        dist = (end - start) * self.sound_speed / 2

        if dist < self.dist_min or dist > self.dist_max:
            raise Exception('Distance is out of range')

        return dist


class WaterTankCalibration:
    """
    Convert water depth/height into volume.
    """

    def __init__(self):
        xy = [(p['distance'], p['volume']) for p in settings.WATER_TANK_CALIBRATION['points']]
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

    def __init__(self):
        self.distanceInterface = DistanceInterface()
        self.calibration = WaterTankCalibration()

    def get_volume(self):
        distance = self.distanceInterface.get_distance()

        volume = self.calibration.get_volume(distance)
        if volume < 0:
            return 0

        return volume


def main():
    tank = WaterTankInterface()
    print('%5.1f' % tank.get_volume())


if __name__ == '__main__':
    main()
