#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import numpy as np
from scipy import interpolate
import settings


class DistanceMeterInterface:
    """
    Ultrasonic distance meter JSN-SR04T.
    """

    # Noise filtering
    filter_samples = 32

    # How much distances can differ, usually they fit into 1cm range
    filter_precision = 0.03

    # At 20 C
    sound_speed = 343.21

    # Time for signal reflections to fully decay
    decay_time = 0.1

    # Sensor properties
    trig_hold_time = 10e-6

    # Limit polling loop iterations.
    # This is faster (and thus more precise) than comparing timestamps.
    # NOTE: Looping speed is only limited by CPU/GPIO speed.
    # Normally less than 5000 iterations are needed.
    poll_cycle_limit = 10 * 1000

    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(settings.DISTANCE_METER_GPIO_TRIG, GPIO.OUT)
        GPIO.setup(settings.DISTANCE_METER_GPIO_ECHO, GPIO.IN)

        GPIO.output(settings.DISTANCE_METER_GPIO_TRIG, False)

    def __del__(self):
        GPIO.cleanup()

    def _get_distance(self):
        time.sleep(self.decay_time)

        GPIO.output(settings.DISTANCE_METER_GPIO_TRIG, True)
        time.sleep(self.trig_hold_time)
        GPIO.output(settings.DISTANCE_METER_GPIO_TRIG, False)

        start = None
        end = None

        for t in range(0, self.poll_cycle_limit):
            if GPIO.input(settings.DISTANCE_METER_GPIO_ECHO) == 1:
                start = time.time()
                break

        for t in range(0, self.poll_cycle_limit):
            if GPIO.input(settings.DISTANCE_METER_GPIO_ECHO) == 0:
                end = time.time()
                break

        if start is None:
            raise Exception('Could not detect echo start')

        if end is None:
            raise Exception('Could not detect echo end')

        dist = (end - start) * self.sound_speed / 2

        return dist

    def get_distance(self):
        values = []

        # NOTE: Exceptions are intentionally propagated to fail the whole sequence
        for n in range(0, self.filter_samples):
            values.append(self._get_distance())

        low = min(values)
        high = max(values)

        # Spreading can be caused by side reflections or other interference
        if high - low > self.filter_precision:
            raise Exception('Distance values are too spread (from %.2fm to %.2fm)' % (low, high))

        # Ultrasonic distance meter emits a train of pulses after being triggered.
        # Depending on which of those pulses is received, distance will vary a bit.
        # We aim for the first pulse, thus return the lowest distance from the set.
        return low


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
        self.distanceInterface = DistanceMeterInterface()
        self.calibration = WaterTankCalibration()

    def get_volume_and_distance(self):
        distance = self.distanceInterface.get_distance()
        volume = self.calibration.get_volume(distance)
        return volume, distance

    def get_volume(self):
        return self.get_volume_and_distance()[0]


def main():
    tank = WaterTankInterface()
    while True:
        try:
            volume, distance = tank.get_volume_and_distance()
            print('%5.1fcm %5.1fL' % (distance * 100, volume))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
