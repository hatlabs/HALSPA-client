"""ADS1115 16-bit ADC driver over smbus2, plus channel abstractions."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from smbus2 import SMBus

if TYPE_CHECKING:
    from halspa.analog_mux import AnalogMux

# ADS1115 register addresses
_CONVERSION_REG = 0x00
_CONFIG_REG = 0x01

# Config register bits
_OS_SINGLE = 1 << 15  # Start single conversion
_OS_NOT_BUSY = 1 << 15  # Conversion complete (read)

# Mux settings (bits 14:12)
_MUX_SINGLE = {0: 0x4000, 1: 0x5000, 2: 0x6000, 3: 0x7000}
_MUX_DIFF = {(0, 1): 0x0000, (0, 3): 0x1000, (1, 3): 0x2000, (2, 3): 0x3000}

# PGA gain settings (bits 11:9)
_PGA = {
    2 / 3: 0x0000,  # +/- 6.144V
    1: 0x0200,  # +/- 4.096V
    2: 0x0400,  # +/- 2.048V
    4: 0x0600,  # +/- 1.024V
    8: 0x0800,  # +/- 0.512V
    16: 0x0A00,  # +/- 0.256V
}

_PGA_VOLTAGE = {
    2 / 3: 6.144,
    1: 4.096,
    2: 2.048,
    4: 1.024,
    8: 0.512,
    16: 0.256,
}

# Mode: single-shot
_MODE_SINGLE = 0x0100

# Data rate: 128 SPS (default)
_DR_128SPS = 0x0080

# Comparator disabled
_COMP_DISABLE = 0x0003


class ADS1115:
    """ADS1115 16-bit, 4-channel ADC driver."""

    def __init__(self, bus: SMBus, address: int = 0x48, gain: float = 1):
        self.bus = bus
        self.address = address
        if gain not in _PGA:
            raise ValueError(f"Invalid gain {gain}. Must be one of {list(_PGA.keys())}")
        self.gain = gain
        self._full_scale = _PGA_VOLTAGE[gain]

    def _write_config(self, config: int) -> None:
        msb = (config >> 8) & 0xFF
        lsb = config & 0xFF
        self.bus.write_i2c_block_data(self.address, _CONFIG_REG, [msb, lsb])

    def _read_config(self) -> int:
        data = self.bus.read_i2c_block_data(self.address, _CONFIG_REG, 2)
        return (data[0] << 8) | data[1]

    def _read_conversion(self) -> int:
        data = self.bus.read_i2c_block_data(self.address, _CONVERSION_REG, 2)
        raw = (data[0] << 8) | data[1]
        # Convert to signed 16-bit
        if raw >= 0x8000:
            raw -= 0x10000
        return raw

    def _wait_conversion(self) -> None:
        """Poll the OS bit until conversion is complete."""
        for _ in range(100):
            if self._read_config() & _OS_NOT_BUSY:
                return
            time.sleep(0.001)
        raise TimeoutError("ADS1115 conversion timed out")

    def read(self, channel: int) -> int:
        """Read a single-ended channel (0-3). Returns signed 16-bit raw value."""
        if channel not in _MUX_SINGLE:
            raise ValueError(f"Invalid channel {channel}. Must be 0-3.")
        config = (
            _OS_SINGLE
            | _MUX_SINGLE[channel]
            | _PGA[self.gain]
            | _MODE_SINGLE
            | _DR_128SPS
            | _COMP_DISABLE
        )
        self._write_config(config)
        self._wait_conversion()
        return self._read_conversion()

    def read_differential(self, pos: int, neg: int) -> int:
        """Read a differential pair. Returns signed 16-bit raw value."""
        key = (pos, neg)
        if key not in _MUX_DIFF:
            raise ValueError(
                f"Invalid differential pair ({pos}, {neg}). "
                f"Must be one of {list(_MUX_DIFF.keys())}."
            )
        config = (
            _OS_SINGLE
            | _MUX_DIFF[key]
            | _PGA[self.gain]
            | _MODE_SINGLE
            | _DR_128SPS
            | _COMP_DISABLE
        )
        self._write_config(config)
        self._wait_conversion()
        return self._read_conversion()

    def raw_to_v(self, raw: int) -> float:
        """Convert a raw ADC reading to voltage."""
        return raw * self._full_scale / 32767


class ADCChannel:
    """Single-ended ADC channel with optional voltage divider scaling."""

    # Voltage divider bottom resistance (shared across all channels)
    rb = 10000.0

    def __init__(
        self, adc: ADS1115, channel: int, scale: float = 1.0, rt: float | None = None
    ):
        self.adc = adc
        self.channel = channel
        self.scale = scale
        if rt is not None:
            self.scale = self.scale * (rt + self.rb) / self.rb

    def read_raw(self) -> int:
        return self.adc.read(self.channel)

    def read_v(self) -> float:
        return self.scale * self.adc.raw_to_v(self.read_raw())


class ADCDiff:
    """Differential ADC reading between two channels."""

    def __init__(
        self, adc: ADS1115, pos_channel: int, neg_channel: int, scale: float = 1.0
    ):
        self.adc = adc
        self.pos_channel = pos_channel
        self.neg_channel = neg_channel
        self.scale = scale

    def read_raw(self) -> int:
        return self.adc.read_differential(self.pos_channel, self.neg_channel)

    def read_v(self) -> float:
        return self.scale * self.adc.raw_to_v(self.read_raw())


class AnalogMuxADCChannel:
    """ADC channel accessed through an analog multiplexer."""

    def __init__(
        self,
        anamux: AnalogMux,
        mux_num: int,
        mux_pin: int,
        adc_channel: ADCChannel,
    ):
        self.anamux = anamux
        self.mux_num = mux_num
        self.mux_pin = mux_pin
        self.adc_channel = adc_channel

    def read_raw(self) -> int:
        self.anamux.select(self.mux_num, self.mux_pin)
        return self.adc_channel.read_raw()

    def read_v(self) -> float:
        self.anamux.select(self.mux_num, self.mux_pin)
        return self.adc_channel.read_v()
