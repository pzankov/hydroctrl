import time
from math import sin, pi
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client


class ADCServer:
    def __init__(self, adc, host='0.0.0.0', port=8000):
        self.adc = adc

        self.server = SimpleXMLRPCServer((host, port))
        self.server.register_function(self.get_samples_V, 'get_samples_V')

    def serve_forever(self):
        self.server.serve_forever()

    def get_samples_V(self, sampling_frequency_Hz, samples_count):
        samples_raw = []

        sample_time = time.monotonic() + 1 / sampling_frequency_Hz

        for _ in range(0, samples_count):
            if time.monotonic() > sample_time:
                raise Exception('Sampling takes too long, try reducing the sampling frequency')

            while time.monotonic() < sample_time:
                pass
            sample_time += 1 / sampling_frequency_Hz

            samples_raw.append(self.adc.get_value())

        samples_V = [self.adc.value_to_voltage(x).m_as('V') for x in samples_raw]

        return samples_V


class ADCClient:
    def __init__(self, host, port=8000):
        self.client = xmlrpc.client.ServerProxy('http://{}:{}/'.format(host, port))

    def get_samples_V(self, sampling_frequency_Hz, samples_count):
        return self.client.get_samples_V(sampling_frequency_Hz, samples_count)


class ADCTestSignalClient:
    def __init__(self, frequency_Hz, offset_V, amplitude_V):
        self.frequency_Hz = frequency_Hz
        self.offset_V = offset_V
        self.amplitude_V = amplitude_V

    def get_samples_V(self, sampling_frequency_Hz, samples_count):
        samples_V = []

        for n in range(0, samples_count):
            phase = self.frequency_Hz * 2 * pi * n / sampling_frequency_Hz
            samples_V.append(self.offset_V + self.amplitude_V * sin(phase))

        return samples_V
