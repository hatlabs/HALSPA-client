import ads1x15


class CalibratedADS1115(ads1x15.ADS1115):
    """
    ADS1115 with automatic calibration based on I2C address.
    Inherits all ADS1115 functionality and adds calibration awareness.
    """

    # I2C address to ADC number mapping
    _ADDR_TO_ADC_NUM = {
        0x48: 1,  # ADC1_ADDR
        0x49: 2,  # ADC2_ADDR
    }

    def __init__(self, i2c, addr, gain):
        """
        Initialize calibrated ADS1115.

        Args:
            i2c: I2C bus instance
            addr: I2C address (0x48 for ADC1, 0x49 for ADC2)
            gain: ADS1115 gain setting
        """
        super().__init__(i2c, addr, gain)

        # Auto-detect ADC number from I2C address
        if addr in self._ADDR_TO_ADC_NUM:
            self.adc_num = self._ADDR_TO_ADC_NUM[addr]
        else:
            raise ValueError(
                f"Unknown ADC I2C address: 0x{addr:02x}. Expected 0x48 (ADC1) or 0x49 (ADC2)"
            )

    def get_channel(self, channel: int) -> "ADCChannel":
        """Get a calibrated ADC channel"""
        return ADCChannel(self, channel)


class ADCChannel:
    def __init__(self, calibrated_adc: CalibratedADS1115, adc_channel: int):
        """
        Args:
            calibrated_adc: CalibratedADS1115 instance
            adc_channel: Channel number (0-3)
        """
        self.calibrated_adc = calibrated_adc
        self.adc_channel = adc_channel

        # Get calibration gain automatically
        from picon.calibration import ADC1_GAINS, ADC2_GAINS

        if calibrated_adc.adc_num == 1:
            self.gain = ADC1_GAINS[adc_channel]
        elif calibrated_adc.adc_num == 2:
            self.gain = ADC2_GAINS[adc_channel]
        else:
            raise ValueError(f"Invalid ADC number: {calibrated_adc.adc_num}")

    def read_raw(self):
        return self.calibrated_adc.read(channel1=self.adc_channel)

    def read_uncalibrated_voltage(self):
        return self.calibrated_adc.raw_to_v(self.read_raw())

    def read_voltage(self):
        raw_voltage = self.calibrated_adc.raw_to_v(self.read_raw())
        return raw_voltage / self.gain


class ADCDiff:
    def __init__(
        self,
        calibrated_adc: CalibratedADS1115,
        adc_channel1: int,
        adc_channel2: int,
    ):
        """
        Differential ADC measurement between two channels with automatic gain calibration.

        Args:
            calibrated_adc: CalibratedADS1115 instance
            adc_channel1: Positive channel (0-3)
            adc_channel2: Negative channel (0-3)

        Raises:
            ValueError: If channel gains differ by more than 1%
        """
        self.calibrated_adc = calibrated_adc
        self.adc_channel1 = adc_channel1
        self.adc_channel2 = adc_channel2

        # Get calibration gains automatically
        from picon.calibration import ADC1_GAINS, ADC2_GAINS

        if calibrated_adc.adc_num == 1:
            ch1_gain = ADC1_GAINS[adc_channel1]
            ch2_gain = ADC1_GAINS[adc_channel2]
        elif calibrated_adc.adc_num == 2:
            ch1_gain = ADC2_GAINS[adc_channel1]
            ch2_gain = ADC2_GAINS[adc_channel2]
        else:
            raise ValueError(f"Invalid ADC number: {calibrated_adc.adc_num}")

        # Validate gains are within 1% of each other
        if abs(ch1_gain - ch2_gain) / ch1_gain > 0.01:
            raise ValueError(
                f"Channel gains differ by more than 1%: "
                f"ch{adc_channel1}={ch1_gain:.4f}, ch{adc_channel2}={ch2_gain:.4f}"
            )

        # Use channel1 gain for automatic scaling
        self.gain = ch1_gain

    def read_raw(self):
        return self.calibrated_adc.read(
            channel1=self.adc_channel1, channel2=self.adc_channel2
        )

    def read_voltage(self):
        raw_voltage = self.calibrated_adc.raw_to_v(self.read_raw())
        return raw_voltage / self.gain


class AnalogMuxADCChannel:
    def __init__(self, select_pin_func, adc_channel):
        self.select_pin = select_pin_func
        self.adc_channel = adc_channel

    def read_raw(self):
        self.select_pin()
        return self.adc_channel.read_raw()

    def read_voltage(self):
        self.select_pin()
        return self.adc_channel.read_voltage()
