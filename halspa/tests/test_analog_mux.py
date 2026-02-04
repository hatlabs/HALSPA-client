"""Tests for AnalogMux with mocked SMBus."""

from unittest.mock import MagicMock

import pytest

from halspa.analog_mux import (
    ADDR_PINS,
    ADDR_REVERSED,
    ANAMUX_INITIAL_STATE,
    INH_PINS,
    AnalogMux,
)


@pytest.fixture
def bus():
    mock = MagicMock()
    mock.read_byte_data.return_value = 0
    return mock


@pytest.fixture
def mux(bus):
    return AnalogMux(bus)


class TestAnalogMuxInit:
    def test_initial_state(self, mux):
        assert mux.ctrl.output == ANAMUX_INITIAL_STATE

    def test_all_pins_configured_as_outputs(self, mux):
        assert mux.ctrl.configuration == 0x0000


class TestAnalogMuxEnable:
    def test_enable_mux_1(self, mux):
        inh_pin = INH_PINS[0]
        mux.enable(1, True)
        # INH is active-low: enable=True means INH bit=0
        assert not (mux.ctrl.output & (1 << inh_pin))

    def test_disable_mux_1(self, mux):
        inh_pin = INH_PINS[0]
        mux.enable(1, False)
        assert mux.ctrl.output & (1 << inh_pin)

    def test_enable_mux_4(self, mux):
        inh_pin = INH_PINS[3]
        mux.enable(4, True)
        assert not (mux.ctrl.output & (1 << inh_pin))

    def test_invalid_mux_number_raises(self, mux):
        with pytest.raises(ValueError):
            mux.enable(0)
        with pytest.raises(ValueError):
            mux.enable(5)


class TestAnalogMuxSet:
    def test_set_mux_3_pin_5(self, mux):
        """Mux 3 is not reversed, so address bits should match pin number."""
        addr_pin = ADDR_PINS[2]  # mux 3
        assert not ADDR_REVERSED[2]  # mux 3 not reversed

        mux.set(3, 5)
        addr_bits = (mux.ctrl.output >> addr_pin) & 0b111
        assert addr_bits == 5

    def test_set_mux_1_pin_5_reversed(self, mux):
        """Mux 1 is reversed, so 5 (0b101) should become 0b101 reversed = 0b101."""
        addr_pin = ADDR_PINS[0]
        assert ADDR_REVERSED[0]

        mux.set(1, 5)
        addr_bits = (mux.ctrl.output >> addr_pin) & 0b111
        # 5 = 0b101, reversed 3-bit = 0b101 = 5
        assert addr_bits == 5

    def test_set_mux_1_pin_3_reversed(self, mux):
        """Mux 1 is reversed, so 3 (0b011) should become 0b110 = 6."""
        addr_pin = ADDR_PINS[0]
        mux.set(1, 3)
        addr_bits = (mux.ctrl.output >> addr_pin) & 0b111
        assert addr_bits == 6

    def test_set_mux_4_pin_0(self, mux):
        """Mux 4 is not reversed."""
        addr_pin = ADDR_PINS[3]
        mux.set(4, 0)
        addr_bits = (mux.ctrl.output >> addr_pin) & 0b111
        assert addr_bits == 0

    def test_invalid_pin_raises(self, mux):
        with pytest.raises(ValueError):
            mux.set(1, 8)
        with pytest.raises(ValueError):
            mux.set(1, -1)


class TestAnalogMuxSelect:
    def test_select_disables_sets_enables(self, mux, bus):
        """select() should disable, set address, then enable."""
        inh_pin = INH_PINS[2]  # mux 3

        mux.select(3, 5)

        # After select, mux should be enabled (INH=0)
        assert not (mux.ctrl.output & (1 << inh_pin))

        # Address should be set
        addr_pin = ADDR_PINS[2]
        addr_bits = (mux.ctrl.output >> addr_pin) & 0b111
        assert addr_bits == 5


class TestReverseBits:
    def test_reverse_0(self):
        assert AnalogMux._reverse_bits(0b000, 3) == 0b000

    def test_reverse_1(self):
        assert AnalogMux._reverse_bits(0b001, 3) == 0b100

    def test_reverse_symmetric(self):
        assert AnalogMux._reverse_bits(0b101, 3) == 0b101

    def test_reverse_asymmetric(self):
        assert AnalogMux._reverse_bits(0b011, 3) == 0b110
