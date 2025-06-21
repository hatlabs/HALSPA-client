from textwrap import dedent

from halspa.repl import REPL


class AnalogMux:
    """
    Class to control the analog multiplexer.
    """

    def __init__(self, repl: REPL):
        self.repl = repl
        self.name = "anamux"
        self.repl.execute(
            dedent(f"""
                    from sauce.sauce import i2c
                    from sauce.analog_mux import AnalogMux
                    {self.name} = AnalogMux(i2c)
                    """)
        )

    def enable(self, mux_num, state: bool = True) -> None:
        """
        Enable or disable the analog multiplexer.

        Args:
            mux_num: The multiplexer number (0-3).
            state: True to enable, False to disable.
        """
        return self.repl.call_function("anamux.enable", state)

    def set(self, mux_num: int, active_pin: int) -> None:
        """
        Directly set the active pin for the specified multiplexer.

        Args:
            mux_num: The multiplexer number (0-3).
            active_pin: The active pin number (0-7).
        """
        return self.repl.call_function("anamux.set", mux_num, active_pin)

    def select(self, mux_num: int, active_pin: int) -> None:
        """
        Select the active pin for the specified multiplexer.

        The output is disabled before setting the pin and re-enabled after.

        Args:
            mux_num: The multiplexer number (0-3).
            active_pin: The active pin number (0-7).
        """
        return self.repl.call_function("anamux.select", mux_num, active_pin)
