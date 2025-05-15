from typing import Callable

import ads1x15
from machine import I2C
from micropython import const

from .tca9535 import TCA9535

ANAMUX_CONFIG = const(0x0000)  # All pins are outputs
ANAMUX_INITIAL_STATE = const(0x8811)

ANAMUX_CTRL_ADDR = const(0x21)  # TCA9535 I2C address for the analog mux

INH_PINS = [0o17, 0o13, 0o00, 0o04]
ADDR_PINS = [0o14, 0o10, 0o01, 0o05]
ADDR_REVERSED = [True, True, False, False]


class AnalogMux:
    def __init__(self, i2c: I2C):
        self.ctrl = TCA9535(
            i2c,
            address=ANAMUX_CTRL_ADDR,
            configuration=ANAMUX_CONFIG,
            output=ANAMUX_INITIAL_STATE,
        )

    def enable(self, mux_num, state=True):
        assert 1 <= mux_num <= 4

        current = self.ctrl.output

        inh = not state

        inh_pin = INH_PINS[mux_num - 1]
        inh_mask = 0xFFFF & ~(1 << inh_pin)
        current = (current & inh_mask) | (inh << inh_pin)

        self.ctrl.write(current)

    def _reverse_bits(self, value, num_bits):
        reversed_value = 0
        for i in range(num_bits):
            if value & (1 << i):
                reversed_value |= 1 << (num_bits - 1 - i)
        return reversed_value

    def set(self, mux_num, active_pin):
        """
        Set the active pin for the specified multiplexer.

        Args:
            mux_num (int): The multiplexer number (1-4).
            active_pin (int): The active pin number (0-7).
        """
        assert 1 <= mux_num <= 4
        assert 0 <= active_pin <= 7

        current = self.ctrl.output

        addr_pin = ADDR_PINS[mux_num - 1]
        addr_mask = 0xFFFF & ~(0b111 << addr_pin)
        addr = (
            self._reverse_bits(active_pin, 3)
            if ADDR_REVERSED[mux_num - 1]
            else active_pin
        )
        current = (current & addr_mask) | (addr << addr_pin)

        self.ctrl.write(current)

    def select(self, mux_num, active_pin):
        self.enable(mux_num, False)
        self.set(mux_num, active_pin)
        self.enable(mux_num, True)

    def get_pin_selector(self, mux_num, pin):
        return lambda: self.select(mux_num, pin)


class ADCChannel:
    rb = 10000.0  # voltage divider bottom resistance

    def __init__(self, adc: ads1x15.ADS1115, adc_channel: int, scale=1.0, rt=None):
        self.adc = adc
        self.adc_channel = adc_channel
        self.scale = scale
        if rt is not None:
            self.scale = self.scale * (rt + self.rb) / self.rb

    def read_raw(self):
        return self.adc.read(channel1=self.adc_channel)

    def read_v(self):
        return self.scale * self.adc.raw_to_v(self.read_raw())


class AnalogMuxADCChannel:
    def __init__(self, select_pin_func: Callable[[], None], adc_channel: ADCChannel):
        self.select_pin = select_pin_func
        self.adc_channel = adc_channel

    def read_raw(self):
        self.select_pin()
        return self.adc_channel.read_raw()

    def read_v(self):
        self.select_pin()
        return self.adc_channel.read_v()
