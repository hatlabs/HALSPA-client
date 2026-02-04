"""HalspaBoard: top-level object that owns the I2C bus and all HALSPA devices."""

from smbus2 import SMBus

from halspa.adc import ADS1115
from halspa.analog_mux import AnalogMux
from halspa.power import PowerControl
from halspa.tca9535 import TCA9535


class HalspaBoard:
    """HALSPA test jig interface board.

    Opens an SMBus and creates all on-board device drivers.
    Use as a context manager or call close() when done.
    """

    def __init__(self, i2c_bus: int = 1):
        self.bus = SMBus(i2c_bus)
        try:
            self.power = PowerControl(self.bus)
            self.mux = AnalogMux(self.bus)
            self.digexp1 = TCA9535(self.bus, address=0x22)
            self.digexp2 = TCA9535(self.bus, address=0x23)
            self.adc1 = ADS1115(self.bus, address=0x48, gain=1)
            self.adc2 = ADS1115(self.bus, address=0x49, gain=1)
        except Exception:
            self.bus.close()
            raise

    def i2c_scan(self) -> list[int]:
        """Probe all 7-bit I2C addresses and return those that ACK."""
        found = []
        for addr in range(0x03, 0x78):
            try:
                self.bus.read_byte(addr)
                found.append(addr)
            except OSError:
                pass
        return found

    def close(self) -> None:
        """Close the I2C bus."""
        self.bus.close()

    def __enter__(self) -> "HalspaBoard":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
