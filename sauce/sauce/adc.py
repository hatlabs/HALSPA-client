from typing import Callable

import ads1x15


class ADCChannel:
    def __init__(self, adc: ads1x15.ADS1115, adc_channel: int, scale=1.0, rb=None):
        self.adc = adc
        self.adc_channel = adc_channel
        self.scale = scale
        if rb is not None:
            rt = 100e3 - rb
            self.scale = self.scale * (rt + rb) / rb

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
