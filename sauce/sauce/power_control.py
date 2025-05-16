"""
Power control module for HALSPA DUT power rails and current limits.

This module provides the PowerControl class, which manages enabling and disabling
various power rails and current limiters for the DUT (Device Under Test) via a TCA9535
I2C GPIO expander.

Each enable/disable method (e.g., enable_5v, enable_3v3, enable_current_limit_1, etc.)
can be used in two ways:

1.  As a function: Pass a boolean state (True/False) to immediately enable or disable
    the corresponding rail or limiter.
2.  As a context manager: If called with no state argument (or state=None), the method
    returns a context manager that enables the rail/limiter on entry and disables it
    on exit. This is useful for temporarily powering a rail or enabling a current limit
    for the duration of a code block.

The 'defer' argument (default False) allows batching multiple enable/disable operations
without immediately writing to the hardware. When defer=True, changes are staged in
software and only written to the device when commit() is called. This enables atomic
updates to multiple outputs, reducing the risk of glitches or intermediate states.

Example usage:
    # Immediate enable/disable
    power.enable_5v(True)
    power.enable_3v3(False)

    # Context manager usage
    with power.enable_12v_1():
        # 12V_1 is enabled within this block
        do_something()
    # 12V_1 is automatically disabled here

    # Deferred operation
    power.enable_5v(True, defer=True)
    power.enable_3v3(True, defer=True)
    power.commit()  # Both rails enabled at once

Other methods:
    - disable_all(): Disables all outputs.
    - read_fault(): Returns the current fault status bits.
    - read_power_good(): Returns the current power-good status bits.
"""

from contextlib import contextmanager

from machine import I2C
from micropython import const

from .tca9535 import TCA9535

EN_LIM_1_PIN = const(0o7)
EN_LIM_2_PIN = const(0o5)
EN_LIM_3_PIN = const(0o3)
EN_LIM_4_PIN = const(0o1)

EN_12V_1_PIN = const(0o12)
EN_12V_2_PIN = const(0o10)

EN_3V3D_PIN = const(0o15)
EN_5VD_PIN = const(0o16)

FAULT_LIM_1_PIN = const(0o6)
FAULT_LIM_2_PIN = const(0o4)
FAULT_LIM_3_PIN = const(0o2)
FAULT_LIM_4_PIN = const(0o0)

FAULT_12V_1_PIN = const(0o13)
FAULT_12V_2_PIN = const(0o11)

PG_3V3_PIN = const(0o14)
PG_5VD_PIN = const(0o17)


class PowerControl:
    """
    Controls DUT power rails and current limiters via a TCA9535 I2C GPIO expander.

    This class provides methods to enable or disable various power rails and current
    limiters for the DUT. Each enable/disable method can be used as a function (for
    immediate action) or as a context manager (for temporary enable/disable within a
    block). The 'defer' argument allows batching changes, which are only committed to
    hardware when commit() is called.
    """

    def __init__(self, i2c: I2C):
        """
        Initialize the PowerControl object and configure the TCA9535 GPIO expander.

        Args:
            i2c (I2C): The I2C bus instance to use for communication.
        """
        output_mask = 0xFFFF ^ (
            (1 << EN_LIM_1_PIN)
            | (1 << EN_LIM_2_PIN)
            | (1 << EN_LIM_3_PIN)
            | (1 << EN_LIM_4_PIN)
            | (1 << EN_12V_1_PIN)
            | (1 << EN_12V_2_PIN)
            | (1 << EN_3V3D_PIN)
            | (1 << EN_5VD_PIN)
        )

        act_low_mask = (
            (1 << FAULT_LIM_1_PIN)
            | (1 << FAULT_LIM_2_PIN)
            | (1 << FAULT_LIM_3_PIN)
            | (1 << FAULT_LIM_4_PIN)
            | (1 << FAULT_12V_1_PIN)
            | (1 << FAULT_12V_2_PIN)
        )

        self.tca9535 = TCA9535(
            i2c,
            address=0x20,
            configuration=output_mask,
            polarity_inversion=act_low_mask,
            output=0,
        )

    @contextmanager
    def _power_context(self, pin, defer=False):
        """
        Context manager to enable a power rail or current limiter for the duration of a block.

        Args:
            pin (int): The pin number to control.
            defer (bool): If True, defer hardware update until commit() is called.

        Yields:
            None
        """
        try:
            self.tca9535.write_bit(pin, True, defer)
            yield
        finally:
            self.tca9535.write_bit(pin, False)

    def _maybe_context(self, pin, state: bool | None = None, defer=False):
        """
        Helper to provide dual function/context manager interface for enable methods.

        Args:
            pin (int): The pin number to control.
            state (bool | None): If True/False, immediately enable/disable. If None, return context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        if state is None:
            return self._power_context(pin, defer)  # type: ignore
        else:
            return self.tca9535.write_bit(pin, state, defer)

    def enable_5v(self, state: bool | None = None, defer=False):
        """
        Enable or disable the 5V DUT power supply.

        Args:
            state (bool | None): True to enable, False to disable, or None for context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        return self._maybe_context(EN_5VD_PIN, state, defer)

    def enable_3v3(self, state: bool | None = None, defer=False):
        """
        Enable or disable the 3.3V DUT power supply.

        Args:
            state (bool | None): True to enable, False to disable, or None for context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        return self._maybe_context(EN_3V3D_PIN, state, defer)

    def enable_12v_1(self, state: bool | None = None, defer=False):
        """
        Enable or disable the 12V_1 DUT output.

        Args:
            state (bool | None): True to enable, False to disable, or None for context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        return self._maybe_context(EN_12V_1_PIN, state, defer)

    def enable_12v_2(self, state: bool | None = None, defer=False):
        """
        Enable or disable the 12V_2 DUT output.

        Args:
            state (bool | None): True to enable, False to disable, or None for context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        return self._maybe_context(EN_12V_2_PIN, state, defer)

    def enable_current_limit_1(self, state: bool | None = None, defer=False):
        """
        Enable or disable the current limit for channel 1.

        Args:
            state (bool | None): True to enable, False to disable, or None for context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        return self._maybe_context(EN_LIM_1_PIN, state, defer)

    def enable_current_limit_2(self, state: bool | None = None, defer=False):
        """
        Enable or disable the current limit for channel 2.

        Args:
            state (bool | None): True to enable, False to disable, or None for context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        return self._maybe_context(EN_LIM_2_PIN, state, defer)

    def enable_current_limit_3(self, state: bool | None = None, defer=False):
        """
        Enable or disable the current limit for channel 3.

        Args:
            state (bool | None): True to enable, False to disable, or None for context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        return self._maybe_context(EN_LIM_3_PIN, state, defer)

    def enable_current_limit_4(self, state: bool | None = None, defer=False):
        """
        Enable or disable the current limit for channel 4.

        Args:
            state (bool | None): True to enable, False to disable, or None for context manager.
            defer (bool): If True, defer hardware update until commit() is called.

        Returns:
            Context manager or result of write_bit.
        """
        return self._maybe_context(EN_LIM_4_PIN, state, defer)

    def commit(self):
        """
        Commit all deferred output changes to the hardware.

        Call this after using enable/disable methods with defer=True to apply all
        staged changes at once.
        """
        self.tca9535.commit()

    def disable_all(self):
        """
        Disable all power rails and current limiters immediately.
        """
        self.tca9535.write(0)

    def read_fault(self):
        """
        Read the current fault status bits.

        Returns:
            int: Bitmask of active fault signals.
        """
        fault_mask = (
            (1 << FAULT_LIM_1_PIN)
            | (1 << FAULT_LIM_2_PIN)
            | (1 << FAULT_LIM_3_PIN)
            | (1 << FAULT_LIM_4_PIN)
            | (1 << FAULT_12V_1_PIN)
            | (1 << FAULT_12V_2_PIN)
        )
        return self.tca9535.read() & fault_mask

    def read_power_good(self):
        """
        Read the current power-good status bits.

        Returns:
            int: Bitmask of power-good signals.
        """
        pg_mask = (1 << PG_3V3_PIN) | (1 << PG_5VD_PIN)
        return self.tca9535.read() & pg_mask
