from halspa.repl import REPL


class Pin:
    """
    Pin class to represent a pin in the HALSPA client.
    """

    def __init__(
        self, repl: REPL, gpio_num: int, pin_type: str, pull: str = "none"
    ) -> None:
        """
        Initialize the Pin class.

        Args:
            repl: The REPL instance to execute commands.
            gpio_num: The GPIO identifier.
            pin_type: The type of the pin (e.g., "input", "output").
            pull: The pull-up/pull-down configuration ("none", "pull-up", "pull-down").
        """
        self.repl = repl
        self.gpio_num = gpio_num
        self.type = pin_type
        self.pull = pull
        self.name = f"gpio{gpio_num}"

        if pin_type not in ["input", "output"]:
            raise ValueError(
                f"Invalid pin type: {pin_type}. Must be 'input' or 'output'."
            )
        if pull not in ["none", "pull-up", "pull-down"]:
            raise ValueError(
                f"Invalid pull configuration: {pull}. Must be 'none', 'pull-up', or 'pull-down'."
            )

        self.repl.execute("from machine import Pin")

        if pin_type == "output":
            self.repl.execute(f"{self.name} = Pin({gpio_num}, Pin.OUT)")
        else:
            pull_strs = {
                "none": None,
                "pull-up": "Pin.PULL_UP",
                "pull-down": "Pin.PULL_DOWN",
            }
            pull_str = pull_strs[pull]
            self.repl.execute(f"{self.name} = Pin({gpio_num}, Pin.IN, {pull_str})")

    def __repr__(self):
        return f"Pin(name={self.name}, type={self.type}, pull={self.pull})"

    def read(self) -> bool:
        """
        Read the value from the pin.
        """
        output = self.repl.call_function(f"{self.name}.value")
        return output

    def set(self, value: bool) -> None:
        """
        Set the value of the pin.
        """
        self.repl.call_function(f"{self.name}.value", value)

    def init(self, pin_type: str, pull: str = "none") -> None:
        """
        Reinitialize the pin with a new type and pull configuration.
        """
        if pin_type not in ["input", "output"]:
            raise ValueError(
                f"Invalid pin type: {pin_type}. Must be 'input' or 'output'."
            )
        if pull not in ["none", "pull-up", "pull-down"]:
            raise ValueError(
                f"Invalid pull configuration: {pull}. Must be 'none', 'pull-up', or 'pull-down'."
            )

        self.type = pin_type
        self.pull = pull

        if pin_type == "output":
            self.repl.execute(f"{self.name}.init(Pin.OUT)")
        else:
            pull_strs = {
                "none": None,
                "pull-up": "Pin.PULL_UP",
                "pull-down": "Pin.PULL_DOWN",
            }
            pull_str = pull_strs[pull]
            self.repl.execute(f"{self.name}.init(Pin.IN, {pull_str})")


class PWM:
    """
    PWM class to control a PWM pin in the HALSPA client.
    """

    def __init__(
        self,
        pin: Pin,
        freq: int,
        duty_u16: int,
    ) -> None:
        """
        Initialize the PWM class.

        Args:
            pin: The Pin instance to control.
        """
        self.pin = pin
        self.freq = freq
        self.duty_u16 = duty_u16
        self.pin.repl.execute("from machine import PWM")
        self.name = f"{pin.name}_pwm"
        self.pin.repl.execute(
            f"{self.name} = PWM({pin.name}, freq={freq}, duty_u16={duty_u16})"
        )

    def __repr__(self):
        return f"PWM(name={self.name}, freq={self.freq}, duty_u16={self.duty_u16})"

    def set_freq(self, freq: int) -> None:
        """
        Set the frequency of the PWM signal.
        """
        self.freq = freq
        self.pin.repl.call_function(f"{self.name}.freq", freq)

    def set_duty_u16(self, duty_u16: int) -> None:
        """
        Set the duty cycle of the PWM signal.
        """
        self.duty_u16 = duty_u16
        self.pin.repl.call_function(f"{self.name}.duty_u16", duty_u16)

    def deinit(self) -> None:
        """
        Deinitialize the PWM signal.
        """
        self.pin.repl.call_function(f"{self.name}.deinit")
