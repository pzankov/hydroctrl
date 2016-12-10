#!/usr/bin/env python3

import sys
import RPi.GPIO as GPIO
import time
import settings


class PumpInterface:
    """
    Complete stepper pump interface with calibration.
    """

    # Pump properties
    max_rpm = 180
    step_angle = 1.8

    # Driver properties
    wake_up_time = 1e-3
    microsteps = 8

    @property
    def max_step_frequency(self):
        max_rotation_frequency = float(self.max_rpm) / 60
        steps_per_rotation = 360.0 / self.step_angle * self.microsteps
        return max_rotation_frequency * steps_per_rotation

    def __init__(self):
        self.steps_per_litre = settings.PUMP_CALIBRATION['steps_per_litre']

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(settings.PUMP_GPIO_SLEEP, GPIO.OUT)
        GPIO.setup(settings.PUMP_GPIO_STEP, GPIO.OUT)

        GPIO.output(settings.PUMP_GPIO_SLEEP, False)
        GPIO.output(settings.PUMP_GPIO_STEP, False)

    def __del__(self):
        GPIO.cleanup()

    def step(self, count):
        GPIO.output(settings.PUMP_GPIO_SLEEP, True)
        time.sleep(self.wake_up_time)

        for t in range(0, int(count)):
            GPIO.output(settings.PUMP_GPIO_STEP, True)
            time.sleep(0.5 / self.max_step_frequency)
            GPIO.output(settings.PUMP_GPIO_STEP, False)
            time.sleep(0.5 / self.max_step_frequency)

        GPIO.output(settings.PUMP_GPIO_SLEEP, False)

    def pump(self, volume):
        self.step(volume * self.steps_per_litre)


def main():
    ml = float(sys.argv[1])
    p = PumpInterface()
    p.pump(ml / 1e3)


if __name__ == "__main__":
    main()
