"""Tests for ADS1115 driver with mocked SMBus."""

from unittest.mock import MagicMock, call

import pytest

from halspa.adc import ADS1115, ADCChannel, ADCDiff, AnalogMuxADCChannel


@pytest.fixture
def bus():
    mock = MagicMock()
    # Default: config read returns OS bit set (not busy)
    mock.read_i2c_block_data.return_value = [0x80, 0x00]
    return mock


@pytest.fixture
def adc(bus):
    return ADS1115(bus, address=0x48, gain=1)


class TestADS1115:
    def test_invalid_gain_raises(self, bus):
        with pytest.raises(ValueError, match="Invalid gain"):
            ADS1115(bus, gain=3)

    def test_read_single_channel_0(self, adc, bus):
        # First read_i2c_block_data call: config read (OS bit set = ready)
        # Second read_i2c_block_data call: conversion result
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],  # Config: OS=1 (ready)
            [0x40, 0x00],  # Conversion: 0x4000 = 16384
        ]
        raw = adc.read(0)
        assert raw == 0x4000

        # Check config was written with correct mux for channel 0 (0x4000)
        write_call = bus.write_i2c_block_data.call_args
        assert write_call[0][1] == 0x01  # Config register
        config_msb = write_call[0][2][0]
        # Channel 0 single-ended: MUX = 100 (bits 14:12)
        assert config_msb & 0x70 == 0x40

    def test_read_single_channel_3(self, adc, bus):
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x20, 0x00],
        ]
        raw = adc.read(3)
        assert raw == 0x2000

        config_msb = bus.write_i2c_block_data.call_args[0][2][0]
        # Channel 3 single-ended: MUX = 111 (bits 14:12)
        assert config_msb & 0x70 == 0x70

    def test_read_invalid_channel_raises(self, adc):
        with pytest.raises(ValueError, match="Invalid channel"):
            adc.read(4)

    def test_read_negative_value(self, adc, bus):
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0xFF, 0xFE],  # -2 in two's complement
        ]
        raw = adc.read(0)
        assert raw == -2

    def test_read_differential(self, adc, bus):
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x10, 0x00],
        ]
        raw = adc.read_differential(0, 1)
        assert raw == 0x1000

        config_msb = bus.write_i2c_block_data.call_args[0][2][0]
        # Diff 0,1: MUX = 000 (bits 14:12)
        assert config_msb & 0x70 == 0x00

    def test_read_differential_invalid_pair(self, adc):
        with pytest.raises(ValueError, match="Invalid differential pair"):
            adc.read_differential(1, 2)

    def test_raw_to_v_gain_1(self, adc):
        # Gain 1 = +/- 4.096V, full scale = 32767
        v = adc.raw_to_v(32767)
        assert abs(v - 4.096) < 0.001

        v = adc.raw_to_v(0)
        assert v == 0.0

        v = adc.raw_to_v(-32768)
        assert v < 0

    def test_conversion_timeout(self, adc, bus):
        # Always return OS=0 (busy)
        bus.read_i2c_block_data.return_value = [0x00, 0x00]
        with pytest.raises(TimeoutError, match="timed out"):
            adc.read(0)


class TestADCChannel:
    def test_read_v_no_scaling(self, adc, bus):
        ch = ADCChannel(adc, 0)
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x40, 0x00],  # 16384
        ]
        v = ch.read_v()
        expected = 16384 * 4.096 / 32767
        assert abs(v - expected) < 0.001

    def test_read_v_with_voltage_divider(self, adc, bus):
        # rt=10000 with rb=10000 gives scale=2.0
        ch = ADCChannel(adc, 0, rt=10000)
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x40, 0x00],
        ]
        v = ch.read_v()
        expected = 2.0 * 16384 * 4.096 / 32767
        assert abs(v - expected) < 0.001

    def test_read_v_with_explicit_scale(self, adc, bus):
        ch = ADCChannel(adc, 0, scale=3.0)
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x40, 0x00],
        ]
        v = ch.read_v()
        expected = 3.0 * 16384 * 4.096 / 32767
        assert abs(v - expected) < 0.001


class TestADCDiff:
    def test_read_v(self, adc, bus):
        diff = ADCDiff(adc, 0, 1)
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x10, 0x00],
        ]
        v = diff.read_v()
        expected = 0x1000 * 4.096 / 32767
        assert abs(v - expected) < 0.001

    def test_read_v_with_scale(self, adc, bus):
        diff = ADCDiff(adc, 0, 1, scale=4.0)
        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x10, 0x00],
        ]
        v = diff.read_v()
        expected = 4.0 * 0x1000 * 4.096 / 32767
        assert abs(v - expected) < 0.001


class TestAnalogMuxADCChannel:
    def test_read_v_selects_mux_first(self, adc, bus):
        mux = MagicMock()
        ch = ADCChannel(adc, 0)
        mux_ch = AnalogMuxADCChannel(mux, 2, 4, ch)

        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x40, 0x00],
        ]
        mux_ch.read_v()
        mux.select.assert_called_once_with(2, 4)

    def test_read_raw_selects_mux_first(self, adc, bus):
        mux = MagicMock()
        ch = ADCChannel(adc, 0)
        mux_ch = AnalogMuxADCChannel(mux, 3, 1, ch)

        bus.read_i2c_block_data.side_effect = [
            [0x80, 0x00],
            [0x20, 0x00],
        ]
        raw = mux_ch.read_raw()
        mux.select.assert_called_once_with(3, 1)
        assert raw == 0x2000
