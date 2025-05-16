from textwrap import dedent

import halspa_client.repl


class PowerControl:
    """
    Class to control the power state of a device.
    """

    def __init__(self, repl: halspa_client.repl.REPL) -> None:
        self.repl = repl
        self.repl.execute(
            dedent("""
                    from sauce.sauce import i2c
                    from sauce.power_control import PowerControl
                    powcon = PowerControl(i2c)
                    """)
        )

    def enable_power(self, rail: str, state: bool = True) -> None:
        """
        Enable or disable a power rail.

        Args:
            rail: The power rail to control ("5v", "3v3", "12v_1", or "12v_2")
            state: True to enable, False to disable
        """
        rail_map = {
            "5v": "enable_5v",
            "3v3": "enable_3v3",
            "12v_1": "enable_12v_1",
            "12v_2": "enable_12v_2",
        }

        if rail not in rail_map:
            raise ValueError(f"Unknown power rail: {rail}")

        method = rail_map[rail]
        self.repl.execute(f"powcon.{method}({state})")

    def enable_current_limit(self, num: int, state: bool = True) -> None:
        """
        Enable or disable the current limit.

        Args:
            num: Current limit number (1-4)
            state: True to enable, False to disable
        """
        if not 1 <= num <= 4:
            raise ValueError(f"Current limit must be 1-4, got {num}")

        self.repl.execute(f"powcon.enable_current_limit_{num}({state})")

    def read_power_fault(self) -> int:
        """
        Read the power fault status.

        Returns:
            int: Power fault status bitmask.
        """
        output = self.repl.execute("print(powcon.read_fault())")

        return int(output.strip())
