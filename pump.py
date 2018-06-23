#!/usr/bin/env python3

import sys
import RPi.GPIO as GPIO
from utils import delay
from settings import UR, PUMP_X_CONFIG, PUMP_Y_CONFIG


class PumpInterface:
    """
    Stepper pump interface.
    """

    @staticmethod
    def _get_step_period(step_angle, max_frequency):
        step_freq = max_frequency * UR.turn / step_angle
        return 1 / step_freq

    def __init__(self, config):
        self.gpio_sleep = config['gpio_sleep']
        self.gpio_step = config['gpio_step']
        self.wake_up_time_s = config['wake_up_time'].m_as('s')
        self.steps_per_volume = config['steps_per_volume']
        self.microsteps = config['microsteps']
        self.step_period_s = self._get_step_period(
            step_angle=config['step_angle'], max_frequency=config['max_frequency']).m_as('s')

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.gpio_sleep, GPIO.OUT)
        GPIO.setup(self.gpio_step, GPIO.OUT)

        GPIO.output(self.gpio_sleep, False)
        GPIO.output(self.gpio_step, False)

    def __del__(self):
        GPIO.cleanup()

    def step(self, count):
        GPIO.output(self.gpio_sleep, True)
        delay(self.wake_up_time_s)

        delay_s = 0.5 * self.step_period_s / self.microsteps

        for t in range(0, int(count * self.microsteps)):
            GPIO.output(self.gpio_step, True)
            delay(delay_s)
            GPIO.output(self.gpio_step, False)
            delay(delay_s)

        GPIO.output(self.gpio_sleep, False)

    def pump(self, volume):
        self.step(volume * self.steps_per_volume)


def main():
    if len(sys.argv) != 3:
        print('Usage: ./pump.py name volume')
        print('       name     pump name, X or Y')
        print('       volume   amount with units, e.g. 10mL')
        return

    volume = UR(sys.argv[2])
    try:
        volume.to('L')
    except:
        print('Value "{}" does not represent a volume'.format(volume))
        return

    name = sys.argv[1]
    if name.upper() == 'X':
        pump = PumpInterface(PUMP_X_CONFIG)
    elif name.upper() == 'Y':
        pump = PumpInterface(PUMP_Y_CONFIG)
    else:
        print('Invalid pump name "{}"'.format(name))
        return

    print('Pumping {} with {}'.format(volume, name))
    pump.pump(volume)


if __name__ == '__main__':
    main()
