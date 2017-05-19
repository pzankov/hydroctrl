#!/usr/bin/env python3

import sys
from math import ceil
from adc_rpc import ADCClient, ADCTestSignalClient
from scipy import fftpack
import numpy as np
import matplotlib.pyplot as pyplot
import matplotlib.animation as animation


def round_to_multiple(x, multiple):
    return round(x / multiple) * multiple


def ceil_to_multiple(x, multiple):
    return ceil(x / multiple) * multiple


class Oscilloscope:
    voltage_scale_step_mV = 50

    def __init__(self, adc, sampling_frequency_Hz, samples_count, autoscale):
        self.adc = adc
        self.sampling_frequency_Hz = sampling_frequency_Hz
        self.samples_count = samples_count
        self.autoscale = autoscale

        # Shorten var names
        count = self.samples_count
        duration_mS = 1000 * count / sampling_frequency_Hz

        self.x_time = np.linspace(0, duration_mS, count)
        self.x_freq = np.linspace(0, sampling_frequency_Hz / 2, count // 2)

        figure, (ax_time, ax_freq) = pyplot.subplots(2)
        self.ax_time = ax_time

        ax_time.set_xlabel('Time, ms')
        ax_time.set_xlim([0, duration_mS])
        ax_time.set_ylabel('Voltage, mV')
        ax_time.set_ylim([0, 2500])
        self.plot_time, = ax_time.plot(self.x_time, np.zeros(count))

        ax_freq.set_xlabel('Frequency, Hz')
        ax_freq.set_xlim([0, sampling_frequency_Hz / 2])
        ax_freq.set_ylabel('Norm. spectral density')
        ax_freq.set_ylim([0, 1])
        self.plot_freq, = ax_freq.plot(self.x_freq, np.zeros(count // 2))

        self.animation = animation.FuncAnimation(figure, self._animate, None, interval=25)

    def show(self):
        pyplot.show()

    def _animate(self, i):
        # Shorten var names
        sampling_frequency_Hz = self.sampling_frequency_Hz
        count = self.samples_count

        try:
            samples_V = self.adc.get_samples_V(sampling_frequency_Hz, count)
        except Exception as e:
            print(e)
            return self._clear()

        samples_mV = np.array(samples_V) * 1000

        mean_mV = np.mean(samples_mV)
        dev_mV = np.std(samples_mV)

        print('(%3.0f ± %2.0f) mV' % (mean_mV, dev_mV))

        fft = np.abs(fftpack.fft(samples_mV - mean_mV)[:count // 2])
        fft /= max(fft)

        self.plot_time.set_ydata(samples_mV)
        self.plot_freq.set_ydata(fft)

        if self.autoscale:
            self.autoscale = False
            center_mV = round_to_multiple(mean_mV, self.voltage_scale_step_mV)
            span_mV = 3 * ceil_to_multiple(dev_mV, self.voltage_scale_step_mV)
            self.ax_time.set_ylim([center_mV - span_mV, center_mV + span_mV])

        return self.plot_time, self.plot_freq

    def _clear(self):
        self.plot_time.set_ydata(np.ma.array(self.x_time, mask=True))
        self.plot_freq.set_ydata(np.ma.array(self.x_freq, mask=True))
        return self.plot_time, self.plot_freq


def main():
    if len(sys.argv) < 2:
        adc = ADCTestSignalClient(frequency_Hz=50, offset_V=1.25, amplitude_V=0.1)
    else:
        adc = ADCClient(host=sys.argv[1])

    osc = Oscilloscope(adc, sampling_frequency_Hz=500, samples_count=256, autoscale=True)
    osc.show()


if __name__ == '__main__':
    main()
