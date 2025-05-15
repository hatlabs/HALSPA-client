"""TCA9535 I2C GPIO Expander Driver"""

from machine import I2C, Pin
from micropython import const

INPUT_PORT_0 = const(0x00)
INPUT_PORT_1 = const(0x01)
OUTPUT_PORT_0 = const(0x02)
OUTPUT_PORT_1 = const(0x03)
POLARITY_INVERSION_PORT_0 = const(0x04)
POLARITY_INVERSION_PORT_1 = const(0x05)
CONFIGURATION_PORT_0 = const(0x06)
CONFIGURATION_PORT_1 = const(0x07)


class TCA9535Pin:
    def __init__(self, tca9535: "TCA9535", pin: int):
        self.tca9535 = tca9535
        self.pin = pin

    def read(self):
        """Read the state of the pin."""
        return self.tca9535.read_bit(self.pin)

    def write(self, value):
        """Set the state of the pin."""
        self.tca9535.write_bit(self.pin, value)

    def toggle(self):
        """Toggle the state of the pin."""
        self.tca9535.write_bit(self.pin, not self.read())


class TCA9535:
    """TCA9535 I2C GPIO Expander Driver"""

    def __init__(
        self,
        i2c: I2C,
        address=0x20,
        interrupt_pin: Pin | None = None,
        configuration=0xFFFF,
        output=0xFFFF,
        polarity_inversion=0x0000,
    ):
        """
        Initialize the TCA9535 GPIO expander.

        Args:
            i2c (I2C): The I2C bus instance.
            address (int): The I2C address of the device (default: 0x20).
            interrupt_pin (Pin | None): Optional interrupt pin (default: None).
            configuration (int): Initial configuration register value (default: 0xFFFF).
            output (int): Initial output register value (default: 0xFFFF).
            polarity_inversion (int): Initial polarity inversion register value (default: 0x0000).
        """
        self.i2c = i2c
        self.address = address
        self.interrupt_pin = interrupt_pin

        # Shadow registers
        self.input = 0x0000
        self.output = output
        self.polarity_inversion = polarity_inversion
        self.configuration = configuration

        # Initialize the device
        self.write(self.output)
        self.write_polarity_inversion(self.polarity_inversion)
        self.write_configuration(self.configuration)

    def read(self):
        """
        Read the input state of both ports.

        Returns:
            int: The combined 16-bit input state of both ports.
        """
        input0 = self.i2c.readfrom_mem(self.address, INPUT_PORT_0, 1)[0]
        input1 = self.i2c.readfrom_mem(self.address, INPUT_PORT_1, 1)[0]
        self.input = input0 | (input1 << 8)
        return self.input

    def write(self, value):
        """
        Set all outputs bits according to the given 16-bit value.

        Args:
            value (int): The bits to write to the output pins as a 16-bit value.
        """
        value0 = value & 0xFF
        value1 = (value >> 8) & 0xFF
        self.i2c.writeto_mem(self.address, OUTPUT_PORT_0, bytearray([value0]))
        self.i2c.writeto_mem(self.address, OUTPUT_PORT_1, bytearray([value1]))
        self.output = value

    def write_bit(self, pin, value, defer=False):
        """
        Set the output state of a single pin.

        Args:
            pin (int): The pin number (0-15) to write.
            value (bool): The value to write (True for 1, False for 0).
            defer (bool): If True, defer writing to the device (default: False).
        """
        if value:
            self.output |= 1 << pin
        else:
            self.output &= ~(1 << pin)
        if not defer:
            if pin < 8:
                self.i2c.writeto_mem(
                    self.address, OUTPUT_PORT_0, bytearray([self.output & 0xFF])
                )
            else:
                self.i2c.writeto_mem(
                    self.address,
                    OUTPUT_PORT_1,
                    bytearray([(self.output >> 8) & 0xFF]),
                )
        return value

    def read_bit(self, pin):
        """
        Read the state of a single pin.

        Args:
            pin (int): The pin number (0-15) to read.

        Returns:
            bool: The state of the pin (True for 1, False for 0).
        """
        self.read()
        return bool(self.input & (1 << pin))

    def commit(self):
        """
        Commit the current output state to the device.

        Only applicable if defer=True was used with write_bit().
        """
        self.write(self.output)

    def read_configuration(self):
        """
        Read the configuration register values.

        Returns:
            int: The combined 16-bit configuration register value.
        """
        conf0 = self.i2c.readfrom_mem(self.address, CONFIGURATION_PORT_0, 1)[0]
        conf1 = self.i2c.readfrom_mem(self.address, CONFIGURATION_PORT_1, 1)[0]
        self.configuration = conf0 | (conf1 << 8)
        return self.configuration

    def write_configuration(self, value):
        """
        Set the configuration register value.

        Args:
            value (int): The 16-bit value to write to the configuration register.
        """
        self.i2c.writeto_mem(
            self.address,
            CONFIGURATION_PORT_0,
            bytearray([value & 0xFF]),
        )
        self.i2c.writeto_mem(
            self.address,
            CONFIGURATION_PORT_1,
            bytearray([(value >> 8) & 0xFF]),
        )
        self.configuration = value

    def read_polarity_inversion(self):
        """
        Read the polarity inversion register value.

        Returns:
            int: The combined 16-bit polarity inversion register value.
        """
        polarity0 = self.i2c.readfrom_mem(self.address, POLARITY_INVERSION_PORT_0, 1)[0]
        polarity1 = self.i2c.readfrom_mem(self.address, POLARITY_INVERSION_PORT_1, 1)[0]
        self.polarity_inversion = polarity0 | (polarity1 << 8)
        return self.polarity_inversion

    def write_polarity_inversion(self, value):
        """
        Write a 16-bit value to the polarity inversion register.

        Args:
            value (int): The 16-bit value to write to the polarity inversion register.
        """
        self.i2c.writeto_mem(
            self.address,
            POLARITY_INVERSION_PORT_0,
            bytearray([value & 0xFF]),
        )
        self.i2c.writeto_mem(
            self.address,
            POLARITY_INVERSION_PORT_1,
            bytearray([(value >> 8) & 0xFF]),
        )
        self.polarity_inversion = value

    def get_pin(self, pin):
        """
        Get a TCA9535Pin object for the specified pin.

        Args:
            pin (int): The pin number (0-15).

        Returns:
            TCA9535Pin: The TCA9535Pin object for the specified pin.
        """
        return TCA9535Pin(self, pin)
