#!/usr/bin/env python3

import smbus
from utils import delay
from statistics import mean, pstdev


class MCP3221:
    """
    MCP3221 ADC interface.
    """

    adc_bits = 12

    def __init__(self, i2c_busn, i2c_addr, v_ref):
        self.i2c_addr = i2c_addr
        self.v_ref = v_ref
        self.i2c = smbus.SMBus(i2c_busn)

    def value_to_voltage(self, value):
        return float(value) / (1 << self.adc_bits) * self.v_ref

    def get_value(self):
        reading = self.i2c.read_i2c_block_data(self.i2c_addr, 0x00, 2)
        return (reading[0] << 8) + reading[1]

    def get_voltage(self):
        value = self.get_value()
        return self.value_to_voltage(value)


class ADS1115:
    """
    ADS1115 ADC interface.
    """

    adc_bits = 16

    # Input channel
    cfg_channel = {
        0: 0b100 << 12,
        1: 0b101 << 12,
        2: 0b110 << 12,
        3: 0b111 << 12
    }

    # Full scale voltage range
    cfg_fsr_mV = {
        6144: 0b000 << 9,
        4096: 0b001 << 9,
        2048: 0b010 << 9,
        1024: 0b011 << 9,
        512: 0b100 << 9,
        256: 0b101 << 9
    }

    # Sampling rate
    cfg_sps = {
        8: 0b000 << 5,
        16: 0b001 << 5,
        32: 0b010 << 5,
        64: 0b011 << 5,
        128: 0b100 << 5,
        250: 0b101 << 5,
        475: 0b110 << 5,
        860: 0b111 << 5
    }

    # Comparator
    cfg_comp_disabled = 0b11 << 0

    # Register address
    reg_conversion = 0
    reg_config = 1

    def __init__(self, i2c_busn, i2c_addr):
        self.i2c_addr = i2c_addr
        self.i2c = smbus.SMBus(i2c_busn)
        self.conversion_time = 0
        self.v_lsb = None

    def value_to_voltage(self, value):
        return value * self.v_lsb

    def config(self, channel, fsr, sps):
        prev_conversion_time = self.conversion_time

        # Data rate variation is +/- 10%
        self.conversion_time = 1.15 / sps

        self.v_lsb = fsr * 2 / (1 << self.adc_bits)

        cfg = self.cfg_comp_disabled
        cfg |= self.cfg_channel[channel]
        cfg |= self.cfg_fsr_mV[fsr.m_as('mV')]
        cfg |= self.cfg_sps[sps]
        cfg_bytes = list(cfg.to_bytes(2, 'big'))

        self.i2c.write_i2c_block_data(self.i2c_addr, self.reg_config, cfg_bytes)

        # Wait for the previous conversion to finish
        delay(prev_conversion_time)

    def get_value(self):
        # Wait until next sample is available
        delay(self.conversion_time)

        reading = self.i2c.read_i2c_block_data(self.i2c_addr, self.reg_conversion, 2)
        return (reading[0] << 8) + reading[1]

    def get_voltage(self):
        value = self.get_value()
        return self.value_to_voltage(value)


class ADCFilter:
    """
    ADC noise filtering.
    """

    def __init__(self, adc, samples_count):
        self.adc = adc
        self.samples_count = samples_count

    def get_voltage(self):
        samples = []
        for n in range(0, self.samples_count):
            samples.append(self.adc.get_value())

        value = mean(samples)
        value_dev = pstdev(samples)

        voltage = self.adc.value_to_voltage(value)
        voltage_dev = self.adc.value_to_voltage(value_dev)

        return voltage.plus_minus(voltage_dev)
