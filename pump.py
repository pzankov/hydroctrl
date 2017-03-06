#!/usr/bin/env python3

import sys
import RPi.GPIO as GPIO
import time
import settings


class PumpInterface:
    """
    Stepper pump interface.
    """

    @staticmethod
    def _get_max_step_frequency(step_angle, microsteps, max_rpm):
        max_rotation_frequency = float(max_rpm) / 60
        steps_per_rotation = 360.0 / step_angle * microsteps
        return max_rotation_frequency * steps_per_rotation

    def __init__(self, config):
        self.gpio_sleep = config['gpio_sleep']
        self.gpio_step = config['gpio_step']
        self.wake_up_time = config['wake_up_time']
        self.steps_per_litre = config['steps_per_litre']
        self.max_step_frequency = self._get_max_step_frequency(
            step_angle=config['step_angle'],
            microsteps=config['microsteps'],
            max_rpm=config['max_rpm'])

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.gpio_sleep, GPIO.OUT)
        GPIO.setup(self.gpio_step, GPIO.OUT)

        GPIO.output(self.gpio_sleep, False)
        GPIO.output(self.gpio_step, False)

    def __del__(self):
        GPIO.cleanup()

    def step(self, count):
        GPIO.output(self.gpio_sleep, True)
        time.sleep(self.wake_up_time)

        for t in range(0, int(count)):
            GPIO.output(self.gpio_step, True)
            time.sleep(0.5 / self.max_step_frequency)
            GPIO.output(self.gpio_step, False)
            time.sleep(0.5 / self.max_step_frequency)

        GPIO.output(self.gpio_sleep, False)

    def pump(self, volume):
        self.step(volume * self.steps_per_litre)


def main():
    ml = float(sys.argv[1])
    p = PumpInterface(settings.PUMP)
    p.pump(ml / 1e3)


if __name__ == '__main__':
    main()
