from textwrap import dedent

import halspa.repl


class ADS1115:
    """
    Class to represent the ADS1115 ADC.
    """

    def __init__(self, repl: halspa.repl.REPL, ads_num: int, gain: int):
        """Initialize the ADS1115 class.

        Args:
            repl: The REPL instance to execute commands.
            ads_num: The ADS1115 number (1 or 2).
            gain: The gain setting for the ADC.

        Gain values:
            0 : 6.144V # 2/3x
            1 : 4.096V # 1x
            2 : 2.048V # 2x
            3 : 1.024V # 4x
            4 : 0.512V # 8x
            5 : 0.256V # 16x
        """
        self.repl = repl
        self.ads_num = ads_num
        self.gain = gain
        self.name = f"ads{ads_num}"
        self.repl.execute(
            dedent(f"""
                    from sauce.sauce import i2c, ADC1_ADDR, ADC2_ADDR
                    from ads1x15 import ADS1115
                    {self.name} = ADS1115(i2c, ADC{ads_num}_ADDR, {gain})
                    """)
        )

    def read_value(self, channel: int, rate: int = 7) -> int:
        """
        Read the ADC value from the specified channel.

        Args:
            channel: The channel number to read from (0-3).
            rate: The rate of the ADC conversion (0-7).

        Returns:
            int: The ADC value (0-65535).
        """
        output = self.repl.execute(f"print({self.name}.read({rate}, {channel}))")

        try:
            return int(output)
        except ValueError:
            raise RuntimeError(f"Invalid ADC value received: {output}")
        except TypeError:
            raise RuntimeError(f"Invalid ADC value type received: {type(output)}")

    def read_voltage(self, channel: int, rate: int = 7) -> float:
        """
        Read the voltage from the specified ADC channel.

        Args:
            channel: The channel number to read from (0-3).
            rate: The rate of the ADC conversion (0-7).

        Returns:
            float: The voltage value.
        """
        output = self.repl.execute(
            f"print({self.name}.raw_to_v({self.name}.read({rate}, {channel})))"
        )

        try:
            return float(output)
        except ValueError:
            raise RuntimeError(f"Invalid ADC voltage value received: {output}")
        except TypeError:
            raise RuntimeError(
                f"Invalid ADC voltage value type received: {type(output)}"
            )


class ADCChannel:
    """
    ADC class to access the HALSPA ADC (Analog-to-Digital Converter) functionality.
    """

    def __init__(
        self,
        ads1115: ADS1115,
        channel: int,
        scale: float = 1.0,
        rb: float | None = None,
    ) -> None:
        """
        Initialize the ADC class.
        """
        self.ads1115 = ads1115
        self.name = f"ads1115_{ads1115.ads_num}_ch{channel}"
        self.channel = channel
        self.scale = scale
        self.rb = rb
        self.ads1115.repl.execute(
            dedent(f"""
                    from sauce.adc import ADCChannel

                    {self.name} = ADCChannel({ads1115.name}, {channel}, {scale}, {rb})
                    """)
        )

    def read_raw(self) -> int:
        """
        Read the raw ADC value from the specified channel.
        """
        output = self.ads1115.repl.execute(f"print({self.name}.read_raw())")

        try:
            return int(output)
        except ValueError:
            raise RuntimeError(f"Invalid ADC raw value received: {output}")
        except TypeError:
            raise RuntimeError(f"Invalid ADC raw value type received: {type(output)}")

    def read_voltage(self) -> float:
        """
        Read the voltage from the specified channel.
        """
        output = self.ads1115.repl.execute(f"print({self.name}.read_voltage())")

        try:
            return float(output)
        except ValueError:
            raise RuntimeError(f"Invalid ADC voltage value received: {output}")
        except TypeError:
            raise RuntimeError(
                f"Invalid ADC voltage value type received: {type(output)}"
            )
