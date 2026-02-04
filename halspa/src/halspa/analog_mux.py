"""Analog multiplexer control via TCA9535 at 0x21."""

from smbus2 import SMBus

from halspa.tca9535 import TCA9535

ANAMUX_CONFIG = 0x0000  # All pins are outputs
ANAMUX_INITIAL_STATE = 0x8811
ANAMUX_CTRL_ADDR = 0x21

INH_PINS = [0o17, 0o13, 0o00, 0o04]
ADDR_PINS = [0o14, 0o10, 0o01, 0o05]
ADDR_REVERSED = [True, True, False, False]


class AnalogMux:
    """Controls four 8:1 analog multiplexers via a TCA9535 I/O expander."""

    def __init__(self, bus: SMBus):
        self.ctrl = TCA9535(
            bus,
            address=ANAMUX_CTRL_ADDR,
            configuration=ANAMUX_CONFIG,
            output=ANAMUX_INITIAL_STATE,
        )

    def enable(self, mux_num: int, state: bool = True) -> None:
        """Enable or disable a multiplexer (1-4). INH pin is active-low."""
        if not 1 <= mux_num <= 4:
            raise ValueError(f"mux_num must be 1-4, got {mux_num}")

        current = self.ctrl.output
        inh = not state
        inh_pin = INH_PINS[mux_num - 1]
        inh_mask = 0xFFFF & ~(1 << inh_pin)
        current = (current & inh_mask) | (inh << inh_pin)

        self.ctrl.write(current)

    @staticmethod
    def _reverse_bits(value: int, num_bits: int) -> int:
        reversed_value = 0
        for i in range(num_bits):
            if value & (1 << i):
                reversed_value |= 1 << (num_bits - 1 - i)
        return reversed_value

    def set(self, mux_num: int, active_pin: int) -> None:
        """Set the active pin (0-7) for a multiplexer (1-4)."""
        if not 1 <= mux_num <= 4:
            raise ValueError(f"mux_num must be 1-4, got {mux_num}")
        if not 0 <= active_pin <= 7:
            raise ValueError(f"active_pin must be 0-7, got {active_pin}")

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

    def select(self, mux_num: int, active_pin: int) -> None:
        """Disable mux, set address, then re-enable (break-before-make)."""
        self.enable(mux_num, False)
        self.set(mux_num, active_pin)
        self.enable(mux_num, True)
