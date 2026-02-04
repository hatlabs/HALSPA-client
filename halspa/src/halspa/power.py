"""Power control for HALSPA DUT power rails and current limiters.

Each enable/disable method can be used in two ways:

1. As a function: Pass a boolean to immediately enable or disable.
2. As a context manager: Call with no argument to enable on entry, disable on exit.

The 'defer' argument batches changes without writing to hardware until commit().
"""

from contextlib import AbstractContextManager, contextmanager

from smbus2 import SMBus

from halspa.tca9535 import TCA9535

EN_LIM_1_PIN = 0o7
EN_LIM_2_PIN = 0o5
EN_LIM_3_PIN = 0o3
EN_LIM_4_PIN = 0o1

EN_12V_1_PIN = 0o12
EN_12V_2_PIN = 0o10

EN_3V3D_PIN = 0o15
EN_5VD_PIN = 0o16

FAULT_LIM_1_PIN = 0o6
FAULT_LIM_2_PIN = 0o4
FAULT_LIM_3_PIN = 0o2
FAULT_LIM_4_PIN = 0o0

FAULT_12V_1_PIN = 0o13
FAULT_12V_2_PIN = 0o11

PG_3V3_PIN = 0o14
PG_5VD_PIN = 0o17


class PowerControl:
    """Controls DUT power rails and current limiters via TCA9535 at 0x20."""

    def __init__(self, bus: SMBus):
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
            bus,
            address=0x20,
            configuration=output_mask,
            polarity_inversion=act_low_mask,
            output=0,
        )

    @contextmanager
    def _power_context(self, pin: int, defer: bool = False):
        try:
            self.tca9535.write_bit(pin, True, defer)
            yield
        finally:
            self.tca9535.write_bit(pin, False)

    def _maybe_context(
        self, pin: int, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        if state is None:
            return self._power_context(pin, defer)
        else:
            self.tca9535.write_bit(pin, state, defer)
            return None

    def enable_5v(
        self, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        return self._maybe_context(EN_5VD_PIN, state, defer)

    def enable_3v3(
        self, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        return self._maybe_context(EN_3V3D_PIN, state, defer)

    def enable_12v_1(
        self, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        return self._maybe_context(EN_12V_1_PIN, state, defer)

    def enable_12v_2(
        self, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        return self._maybe_context(EN_12V_2_PIN, state, defer)

    def enable_current_limit_1(
        self, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        return self._maybe_context(EN_LIM_1_PIN, state, defer)

    def enable_current_limit_2(
        self, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        return self._maybe_context(EN_LIM_2_PIN, state, defer)

    def enable_current_limit_3(
        self, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        return self._maybe_context(EN_LIM_3_PIN, state, defer)

    def enable_current_limit_4(
        self, state: bool | None = None, defer: bool = False
    ) -> AbstractContextManager[None] | None:
        return self._maybe_context(EN_LIM_4_PIN, state, defer)

    def commit(self) -> None:
        """Write all deferred changes to hardware."""
        self.tca9535.commit()

    def disable_all(self) -> None:
        """Disable all power rails and current limiters."""
        self.tca9535.write(0)

    def read_fault(self) -> int:
        """Read fault status bits. Returns bitmask of active faults."""
        fault_mask = (
            (1 << FAULT_LIM_1_PIN)
            | (1 << FAULT_LIM_2_PIN)
            | (1 << FAULT_LIM_3_PIN)
            | (1 << FAULT_LIM_4_PIN)
            | (1 << FAULT_12V_1_PIN)
            | (1 << FAULT_12V_2_PIN)
        )
        return self.tca9535.read() & fault_mask

    def read_power_good(self) -> int:
        """Read power-good status bits."""
        pg_mask = (1 << PG_3V3_PIN) | (1 << PG_5VD_PIN)
        return self.tca9535.read() & pg_mask
