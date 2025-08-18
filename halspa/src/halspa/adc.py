from textwrap import dedent
from typing import Dict, List

import halspa.repl
from halspa.analog_mux import AnalogMux


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
                    from picon.adc import CalibratedADS1115
                    from picon.picon import i2c, ADC1_ADDR, ADC2_ADDR
                    {self.name} = CalibratedADS1115(i2c, ADC{ads_num}_ADDR, {gain})
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
    Uses automatic calibration from the picon calibration system.
    """

    def __init__(
        self,
        ads1115: ADS1115,
        channel: int,
    ) -> None:
        """
        Initialize the ADC class with automatic calibration.

        Args:
            ads1115: ADS1115 instance
            channel: Channel number (0-3)
        """
        self.ads1115 = ads1115
        self.name = f"ads{ads1115.ads_num}_ch{channel}"
        self.channel = channel
        self.ads1115.repl.execute(
            f"{self.name} = {ads1115.name}.get_channel({channel})"
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

    def read_uncalibrated_voltage(self) -> float:
        """
        Read the uncalibrated voltage from the specified channel.
        """
        output = self.ads1115.repl.execute(
            f"print({self.name}.read_uncalibrated_voltage())"
        )

        try:
            return float(output)
        except ValueError:
            raise RuntimeError(
                f"Invalid ADC uncalibrated voltage value received: {output}"
            )
        except TypeError:
            raise RuntimeError(
                f"Invalid ADC uncalibrated voltage value type received: {type(output)}"
            )

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


class ADCDiff:
    """
    ADC class for differential measurements using the ADS1115.
    """

    def __init__(
        self,
        ads1115: ADS1115,
        channel1: int,
        channel2: int,
    ) -> None:
        """
        Initialize differential ADC measurement with automatic gain calibration.

        Args:
            ads1115: ADS1115 instance
            channel1: Positive channel (0-3)
            channel2: Negative channel (0-3)
            
        Raises:
            ValueError: If channel gains differ by more than 1% (raised by picon side)
        """
        self.ads1115 = ads1115
        self.name = f"ads{ads1115.ads_num}_diff_{channel1}_{channel2}"
        self.channel1 = channel1
        self.channel2 = channel2

        self.ads1115.repl.execute(
            dedent(f"""
                    from picon.adc import ADCDiff
                    {self.name} = ADCDiff({ads1115.name}, {channel1}, {channel2})
                    """)
        )

    def read_raw(self) -> int:
        """Read the raw differential ADC value."""
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


class AnalogMuxADCChannel:
    """
    Convenience class for using an analog multiplexer with the ADS1115 ADC.
    """

    def __init__(
        self,
        anamux: AnalogMux,
        mux_num: int,
        mux_ch: int,
        adc_channel: ADCChannel,
    ) -> None:
        self.anamux = anamux
        self.mux_num = mux_num
        self.mux_ch = mux_ch
        self.adc_channel = adc_channel

        self.name = f"{self.adc_channel.name}_mux{self.mux_num}_ch{self.mux_ch}"

        cmd = dedent(f"""
                    from picon.adc import AnalogMuxADCChannel
                    {self.name} = AnalogMuxADCChannel({self.anamux.name}.get_pin_selector({self.mux_num}, {self.mux_ch}), {self.adc_channel.name})
                    """)

        self.anamux.repl.execute(cmd)

    def read_raw(self) -> int:
        """
        Read the raw ADC value from the analog multiplexer channel.
        """
        output = self.anamux.repl.execute(f"print({self.name}.read_raw())")

        try:
            return int(output)
        except ValueError:
            raise RuntimeError(f"Invalid ADC raw value received: {output}")
        except TypeError:
            raise RuntimeError(f"Invalid ADC raw value type received: {type(output)}")

    def read_voltage(self) -> float:
        """
        Read the voltage from the analog multiplexer channel.
        """
        output = self.anamux.repl.execute(f"print({self.name}.read_voltage())")

        try:
            return float(output)
        except ValueError:
            raise RuntimeError(f"Invalid ADC voltage value received: {output}")
        except TypeError:
            raise RuntimeError(
                f"Invalid ADC voltage value type received: {type(output)}"
            )


def measure_all_channels(ads1: ADS1115, ads2: ADS1115) -> Dict[int, List[Dict]]:
    """
    Measure all channels on both ADCs and return structured data.
    
    Args:
        ads1: ADS1115 instance for ADC1
        ads2: ADS1115 instance for ADC2
    
    Returns:
        Dictionary with ADC numbers as keys and list of channel measurements as values.
        Each measurement contains: channel, raw_value, uncalibrated_voltage, calibrated_voltage, error
    """
    measurements = {}
    
    for adc_num, ads in [(1, ads1), (2, ads2)]:
        measurements[adc_num] = []
        
        for channel in range(4):
            measurement = {
                'channel': channel,
                'raw_value': None,
                'uncalibrated_voltage': None,
                'calibrated_voltage': None,
                'error': None
            }
            
            try:
                adc_channel = ADCChannel(ads, channel)
                measurement['raw_value'] = adc_channel.read_raw()
                measurement['uncalibrated_voltage'] = adc_channel.read_uncalibrated_voltage()
                measurement['calibrated_voltage'] = adc_channel.read_voltage()
            except Exception as e:
                measurement['error'] = str(e)
            
            measurements[adc_num].append(measurement)
    
    return measurements


def print_measurements(measurements: Dict[int, List[Dict]]) -> None:
    """
    Print measurements in formatted output.
    
    Args:
        measurements: Dictionary returned by measure_all_channels()
    """
    for adc_num, channel_data in measurements.items():
        print(f"ADC{adc_num} (I2C 0x{0x47 + adc_num:02x}) Uncalibrated Voltages:")
        print("-" * 40)
        
        for measurement in channel_data:
            channel = measurement['channel']
            
            if measurement['error']:
                print(f"  Channel {channel}: Error - {measurement['error']}")
            else:
                uncal_v = measurement['uncalibrated_voltage']
                cal_v = measurement['calibrated_voltage']
                raw = measurement['raw_value']
                print(f"  Channel {channel}: {uncal_v:8.4f}V uncal, {cal_v:8.4f}V cal (raw: {raw:5d})")
        
        print()