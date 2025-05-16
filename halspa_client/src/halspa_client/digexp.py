from textwrap import dedent

from halspa_client.repl import REPL


class TCA9535Pin:
    """
    Pin class to represent a pin in the TCA9535 digital expander.
    """

    def __init__(self, tca9535: "TCA9535", pin_num: int) -> None:
        """
        Initialize the TCA9535Pin class.

        Args:
            repl: The REPL instance to execute commands.
            pin_num: The pin number in the TCA9535 expander.
        """
        self.tca9535 = tca9535
        self.pin_num = pin_num
        self.name = f"{tca9535.name}_pin{pin_num}"
        self.tca9535.repl.execute(f"{self.name} = {tca9535.name}.get_pin({pin_num})")

    def __repr__(self):
        return f"TCA9535Pin(name={self.name}, pin_num={self.pin_num})"

    def read(self) -> bool:
        """
        Read the value from the pin.
        """
        return self.tca9535.repl.call_function(f"{self.name}.read") == 1

    def write(self, value: bool) -> None:
        """
        Write a value to the pin.
        """
        self.tca9535.repl.call_function(f"{self.name}.write", value)

    def toggle(self) -> None:
        """
        Toggle the value of the pin.
        """
        self.tca9535.repl.call_function(f"{self.name}.toggle")

    def configure(self, mode: int) -> None:
        """
        Configure the pin mode.

        Args:
            mode: The mode to set (0 for input, 1 for output).
        """
        self.tca9535.repl.call_function(f"{self.name}.configure", mode)


class TCA9535:
    """
    DigitalExpander class to access the HALSPA digital expander functionality.
    """

    def __init__(
        self,
        repl: REPL,
        expander_num: int,
        configuration: int = 0xFFFF,
        output: int = 0xFFFF,
    ) -> None:
        """
        Initialize the TCA9535 class.
        """
        self.repl = repl
        self.expander_num = expander_num
        self.configuration = configuration
        self.output = output
        self.name = f"digexp{expander_num}"
        self.repl.execute(
            dedent("""
                    from sauce.sauce import i2c, DIGEXP1_ADDR, DIGEXP2_ADDR
                    from sauce.tca9535 import TCA9535
                    """)
        )
        self.repl.execute(
            f"{self.name} = TCA9535(i2c, DIGEXP{self.expander_num}_ADDR, {self.configuration}, {self.output})"
        )

    def __repr__(self):
        return f"TCA9535(name={self.name}, configuration={self.configuration}, output={self.output})"

    def read(self) -> int:
        """
        Read the value from the digital expander.
        """
        return self.repl.call_function(f"{self.name}.read")

    def write(self, value: int) -> None:
        """
        Write a value to the digital expander.
        """
        self.repl.call_function(f"{self.name}.write", value)

    def read_bit(self, pin: int) -> bool:
        """
        Read a specific bit from the digital expander.
        """
        return self.repl.call_function(f"{self.name}.read_bit", pin) == 1

    def write_bit(self, pin: int, value: bool, defer=False) -> None:
        """
        Write a specific bit to the digital expander.
        """
        self.repl.call_function(f"{self.name}.write_bit", pin, value, defer)

    def commit(self) -> None:
        """
        Commit the changes to the digital expander.
        """
        self.repl.call_function(f"{self.name}.commit")

    def read_configuration(self) -> int:
        """
        Read the configuration register of the digital expander.
        """
        return self.repl.call_function(f"{self.name}.read_configuration")

    def write_configuration(self, configuration: int) -> None:
        """
        Write a new configuration to the digital expander.
        """
        self.repl.call_function(f"{self.name}.write_configuration", configuration)
        self.configuration = configuration

    def get_pin(self, pin_num: int) -> TCA9535Pin:
        """
        Get a specific pin from the digital expander.

        Args:
            pin_num: The pin number in the TCA9535 expander.

        Returns:
            TCA9535Pin: The pin object.
        """
        return TCA9535Pin(self, pin_num)
