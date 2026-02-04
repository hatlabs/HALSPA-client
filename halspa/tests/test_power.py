"""Tests for PowerControl with mocked SMBus."""

from unittest.mock import MagicMock

import pytest

from halspa.power import (
    EN_12V_1_PIN,
    EN_12V_2_PIN,
    EN_3V3D_PIN,
    EN_5VD_PIN,
    EN_LIM_1_PIN,
    EN_LIM_2_PIN,
    FAULT_12V_1_PIN,
    FAULT_LIM_1_PIN,
    PG_3V3_PIN,
    PG_5VD_PIN,
    PowerControl,
)


@pytest.fixture
def bus():
    mock = MagicMock()
    mock.read_byte_data.return_value = 0
    return mock


@pytest.fixture
def power(bus):
    return PowerControl(bus)


class TestPowerControlInit:
    def test_output_starts_at_zero(self, power):
        assert power.tca9535.output == 0

    def test_configuration_sets_output_pins(self, power):
        # Enable pins should be configured as outputs (bit=0)
        config = power.tca9535.configuration
        for pin in [EN_5VD_PIN, EN_3V3D_PIN, EN_12V_1_PIN, EN_12V_2_PIN,
                    EN_LIM_1_PIN, EN_LIM_2_PIN]:
            assert not (config & (1 << pin)), f"Pin {pin} should be output"


class TestPowerControlEnable:
    def test_enable_5v(self, power):
        power.enable_5v(True)
        assert power.tca9535.output & (1 << EN_5VD_PIN)

    def test_disable_5v(self, power):
        power.enable_5v(True)
        power.enable_5v(False)
        assert not (power.tca9535.output & (1 << EN_5VD_PIN))

    def test_enable_3v3(self, power):
        power.enable_3v3(True)
        assert power.tca9535.output & (1 << EN_3V3D_PIN)

    def test_enable_12v_1(self, power):
        power.enable_12v_1(True)
        assert power.tca9535.output & (1 << EN_12V_1_PIN)

    def test_enable_12v_2(self, power):
        power.enable_12v_2(True)
        assert power.tca9535.output & (1 << EN_12V_2_PIN)

    def test_enable_current_limit_1(self, power):
        power.enable_current_limit_1(True)
        assert power.tca9535.output & (1 << EN_LIM_1_PIN)

    def test_enable_current_limit_2(self, power):
        power.enable_current_limit_2(True)
        assert power.tca9535.output & (1 << EN_LIM_2_PIN)


class TestPowerControlContextManager:
    def test_context_manager_enables_then_disables(self, power):
        with power.enable_12v_1():
            assert power.tca9535.output & (1 << EN_12V_1_PIN)
        assert not (power.tca9535.output & (1 << EN_12V_1_PIN))

    def test_context_manager_disables_on_exception(self, power):
        with pytest.raises(RuntimeError):
            with power.enable_5v():
                assert power.tca9535.output & (1 << EN_5VD_PIN)
                raise RuntimeError("test")
        assert not (power.tca9535.output & (1 << EN_5VD_PIN))


class TestPowerControlDefer:
    def test_deferred_enable_does_not_write_immediately(self, power, bus):
        bus.write_byte_data.reset_mock()
        power.enable_5v(True, defer=True)
        power.enable_3v3(True, defer=True)
        # Shadow register updated but only init writes happened
        assert power.tca9535.output & (1 << EN_5VD_PIN)
        assert power.tca9535.output & (1 << EN_3V3D_PIN)
        # No write_byte_data calls for the deferred bits
        bus.write_byte_data.assert_not_called()

    def test_commit_writes_deferred(self, power, bus):
        power.enable_5v(True, defer=True)
        power.enable_3v3(True, defer=True)
        bus.write_byte_data.reset_mock()
        power.commit()
        assert bus.write_byte_data.call_count == 2  # Port 0 and port 1


class TestPowerControlStatus:
    def test_disable_all(self, power, bus):
        power.enable_5v(True)
        power.enable_3v3(True)
        bus.write_byte_data.reset_mock()
        power.disable_all()
        assert power.tca9535.output == 0

    def test_read_fault(self, power, bus):
        # Simulate fault on LIM1 (pin 6) and 12V_1 (pin 14)
        bus.read_byte_data.side_effect = [
            (1 << FAULT_LIM_1_PIN) & 0xFF,  # Port 0
            ((1 << FAULT_12V_1_PIN) >> 8) & 0xFF,  # Port 1
        ]
        fault = power.read_fault()
        assert fault & (1 << FAULT_LIM_1_PIN)
        assert fault & (1 << FAULT_12V_1_PIN)

    def test_read_power_good(self, power, bus):
        bus.read_byte_data.side_effect = [
            0x00,  # Port 0
            ((1 << PG_3V3_PIN) | (1 << PG_5VD_PIN)) >> 8,  # Port 1
        ]
        pg = power.read_power_good()
        assert pg & (1 << PG_3V3_PIN)
        assert pg & (1 << PG_5VD_PIN)
