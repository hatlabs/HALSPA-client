"""Tests for TCA9535 driver with mocked SMBus."""

from unittest.mock import MagicMock, call

import pytest

from halspa.tca9535 import (
    CONFIGURATION_PORT_0,
    CONFIGURATION_PORT_1,
    INPUT_PORT_0,
    INPUT_PORT_1,
    OUTPUT_PORT_0,
    OUTPUT_PORT_1,
    POLARITY_INVERSION_PORT_0,
    POLARITY_INVERSION_PORT_1,
    TCA9535,
    TCA9535Pin,
)


@pytest.fixture
def bus():
    mock = MagicMock()
    mock.read_byte_data.return_value = 0
    return mock


@pytest.fixture
def tca(bus):
    return TCA9535(bus, address=0x20, configuration=0xFFFF, output=0x0000)


class TestTCA9535Init:
    def test_init_writes_output_then_polarity_then_config(self, bus):
        TCA9535(bus, address=0x20, configuration=0x1234, output=0x5678, polarity_inversion=0xABCD)

        calls = bus.write_byte_data.call_args_list
        # Output port 0, output port 1
        assert calls[0] == call(0x20, OUTPUT_PORT_0, 0x78)
        assert calls[1] == call(0x20, OUTPUT_PORT_1, 0x56)
        # Polarity inversion port 0, port 1
        assert calls[2] == call(0x20, POLARITY_INVERSION_PORT_0, 0xCD)
        assert calls[3] == call(0x20, POLARITY_INVERSION_PORT_1, 0xAB)
        # Configuration port 0, port 1
        assert calls[4] == call(0x20, CONFIGURATION_PORT_0, 0x34)
        assert calls[5] == call(0x20, CONFIGURATION_PORT_1, 0x12)


class TestTCA9535ReadWrite:
    def test_read_combines_both_ports(self, tca, bus):
        bus.read_byte_data.side_effect = [0xAB, 0xCD]
        result = tca.read()
        assert result == 0xCDAB
        assert tca.input == 0xCDAB
        bus.read_byte_data.assert_any_call(0x20, INPUT_PORT_0)
        bus.read_byte_data.assert_any_call(0x20, INPUT_PORT_1)

    def test_write_splits_to_both_ports(self, tca, bus):
        bus.write_byte_data.reset_mock()
        tca.write(0x1234)
        assert tca.output == 0x1234
        bus.write_byte_data.assert_any_call(0x20, OUTPUT_PORT_0, 0x34)
        bus.write_byte_data.assert_any_call(0x20, OUTPUT_PORT_1, 0x12)

    def test_write_bit_low_pin(self, tca, bus):
        bus.write_byte_data.reset_mock()
        tca.write_bit(3, True)
        assert tca.output & (1 << 3)
        bus.write_byte_data.assert_called_with(0x20, OUTPUT_PORT_0, 0x08)

    def test_write_bit_high_pin(self, tca, bus):
        bus.write_byte_data.reset_mock()
        tca.write_bit(10, True)
        assert tca.output & (1 << 10)
        bus.write_byte_data.assert_called_with(0x20, OUTPUT_PORT_1, 0x04)

    def test_write_bit_defer_does_not_write(self, tca, bus):
        bus.write_byte_data.reset_mock()
        tca.write_bit(5, True, defer=True)
        assert tca.output & (1 << 5)
        bus.write_byte_data.assert_not_called()

    def test_commit_writes_deferred(self, tca, bus):
        tca.write_bit(5, True, defer=True)
        tca.write_bit(10, True, defer=True)
        bus.write_byte_data.reset_mock()
        tca.commit()
        bus.write_byte_data.assert_any_call(0x20, OUTPUT_PORT_0, 0x20)
        bus.write_byte_data.assert_any_call(0x20, OUTPUT_PORT_1, 0x04)

    def test_read_bit(self, tca, bus):
        bus.read_byte_data.side_effect = [0x08, 0x00]
        assert tca.read_bit(3) is True

        bus.read_byte_data.side_effect = [0x00, 0x00]
        assert tca.read_bit(3) is False

    def test_write_bit_clear(self, tca, bus):
        tca.output = 0xFF
        bus.write_byte_data.reset_mock()
        tca.write_bit(3, False)
        assert not (tca.output & (1 << 3))

    def test_write_bit_invalid_pin_raises(self, tca):
        with pytest.raises(ValueError):
            tca.write_bit(16, True)
        with pytest.raises(ValueError):
            tca.write_bit(-1, True)

    def test_read_bit_invalid_pin_raises(self, tca):
        with pytest.raises(ValueError):
            tca.read_bit(16)
        with pytest.raises(ValueError):
            tca.read_bit(-1)

    def test_get_pin_invalid_pin_raises(self, tca):
        with pytest.raises(ValueError):
            tca.get_pin(16)
        with pytest.raises(ValueError):
            tca.get_pin(-1)


class TestTCA9535Pin:
    def test_pin_read(self, tca, bus):
        pin = tca.get_pin(5)
        bus.read_byte_data.side_effect = [0x20, 0x00]
        assert pin.read() is True

    def test_pin_write(self, tca, bus):
        pin = tca.get_pin(5)
        bus.write_byte_data.reset_mock()
        pin.write(True)
        assert tca.output & (1 << 5)

    def test_pin_toggle_from_low(self, tca, bus):
        pin = tca.get_pin(5)
        # Shadow output is 0, toggle should set to True
        bus.write_byte_data.reset_mock()
        pin.toggle()
        assert tca.output & (1 << 5)

    def test_pin_toggle_from_high(self, tca, bus):
        pin = tca.get_pin(5)
        tca.output = 1 << 5  # Shadow says pin 5 is high
        bus.write_byte_data.reset_mock()
        pin.toggle()
        assert not (tca.output & (1 << 5))

    def test_pin_toggle_uses_shadow_not_input(self, tca, bus):
        """Toggle must use shadow output register, not the input port."""
        pin = tca.get_pin(5)
        tca.output = 1 << 5  # Shadow output: pin 5 HIGH
        # Even if the input port reads LOW (e.g. external load), toggle should
        # flip the output from HIGH to LOW based on the shadow register.
        bus.read_byte_data.side_effect = [0x00, 0x00]
        bus.write_byte_data.reset_mock()
        pin.toggle()
        assert not (tca.output & (1 << 5))

    def test_pin_configure_output(self, tca, bus):
        pin = tca.get_pin(5)
        bus.write_byte_data.reset_mock()
        pin.configure(output=True)
        assert not (tca.configuration & (1 << 5))
        bus.write_byte_data.assert_any_call(0x20, CONFIGURATION_PORT_0, 0xDF)

    def test_pin_configure_input(self, tca, bus):
        tca.configuration = 0x0000  # All outputs
        pin = tca.get_pin(5)
        bus.write_byte_data.reset_mock()
        pin.configure(output=False)
        assert tca.configuration & (1 << 5)
