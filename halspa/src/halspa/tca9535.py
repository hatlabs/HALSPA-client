"""TCA9535 I2C 16-bit GPIO expander driver over smbus2."""

from smbus2 import SMBus

INPUT_PORT_0 = 0x00
INPUT_PORT_1 = 0x01
OUTPUT_PORT_0 = 0x02
OUTPUT_PORT_1 = 0x03
POLARITY_INVERSION_PORT_0 = 0x04
POLARITY_INVERSION_PORT_1 = 0x05
CONFIGURATION_PORT_0 = 0x06
CONFIGURATION_PORT_1 = 0x07


class TCA9535Pin:
    def __init__(self, tca9535: "TCA9535", pin: int):
        self.tca9535 = tca9535
        self.pin = pin

    def read(self) -> bool:
        """Read the input state of this pin."""
        return self.tca9535.read_bit(self.pin)

    def write(self, value: bool, defer: bool = False) -> None:
        """Set the output state of this pin."""
        self.tca9535.write_bit(self.pin, value, defer)

    def toggle(self) -> None:
        """Toggle the output state of this pin (uses shadow output register)."""
        current = bool(self.tca9535.output & (1 << self.pin))
        self.tca9535.write_bit(self.pin, not current)

    def configure(self, output: bool) -> None:
        """Configure pin direction. output=True for output, False for input."""
        if output:
            self.tca9535.configuration &= ~(1 << self.pin)
        else:
            self.tca9535.configuration |= 1 << self.pin
        self.tca9535.write_configuration(self.tca9535.configuration)


class TCA9535:
    """TCA9535 I2C 16-bit GPIO expander driver."""

    def __init__(
        self,
        bus: SMBus,
        address: int = 0x20,
        configuration: int = 0xFFFF,
        output: int = 0xFFFF,
        polarity_inversion: int = 0x0000,
    ):
        self.bus = bus
        self.address = address

        # Shadow registers
        self.input = 0x0000
        self.output = output
        self.polarity_inversion = polarity_inversion
        self.configuration = configuration

        # Initialize the device
        self.write(self.output)
        self.write_polarity_inversion(self.polarity_inversion)
        self.write_configuration(self.configuration)

    def read(self) -> int:
        """Read both input ports. Returns combined 16-bit value."""
        input0 = self.bus.read_byte_data(self.address, INPUT_PORT_0)
        input1 = self.bus.read_byte_data(self.address, INPUT_PORT_1)
        self.input = input0 | (input1 << 8)
        return self.input

    def write(self, value: int) -> None:
        """Write a 16-bit value to both output ports."""
        self.bus.write_byte_data(self.address, OUTPUT_PORT_0, value & 0xFF)
        self.bus.write_byte_data(self.address, OUTPUT_PORT_1, (value >> 8) & 0xFF)
        self.output = value

    def write_bit(self, pin: int, value: bool, defer: bool = False) -> None:
        """Set a single output pin. If defer=True, don't write to hardware."""
        if not 0 <= pin <= 15:
            raise ValueError(f"Pin must be 0-15, got {pin}")
        if value:
            self.output |= 1 << pin
        else:
            self.output &= ~(1 << pin)
        if not defer:
            if pin < 8:
                self.bus.write_byte_data(
                    self.address, OUTPUT_PORT_0, self.output & 0xFF
                )
            else:
                self.bus.write_byte_data(
                    self.address, OUTPUT_PORT_1, (self.output >> 8) & 0xFF
                )

    def read_bit(self, pin: int) -> bool:
        """Read the input state of a single pin."""
        if not 0 <= pin <= 15:
            raise ValueError(f"Pin must be 0-15, got {pin}")
        self.read()
        return bool(self.input & (1 << pin))

    def commit(self) -> None:
        """Write the current shadow output register to hardware."""
        self.write(self.output)

    def write_configuration(self, value: int) -> None:
        """Write the 16-bit configuration register (1=input, 0=output)."""
        self.bus.write_byte_data(
            self.address, CONFIGURATION_PORT_0, value & 0xFF
        )
        self.bus.write_byte_data(
            self.address, CONFIGURATION_PORT_1, (value >> 8) & 0xFF
        )
        self.configuration = value

    def write_polarity_inversion(self, value: int) -> None:
        """Write the 16-bit polarity inversion register."""
        self.bus.write_byte_data(
            self.address, POLARITY_INVERSION_PORT_0, value & 0xFF
        )
        self.bus.write_byte_data(
            self.address, POLARITY_INVERSION_PORT_1, (value >> 8) & 0xFF
        )
        self.polarity_inversion = value

    def get_pin(self, pin: int) -> TCA9535Pin:
        """Return a TCA9535Pin object for the given pin number (0-15)."""
        if not 0 <= pin <= 15:
            raise ValueError(f"Pin must be 0-15, got {pin}")
        return TCA9535Pin(self, pin)
