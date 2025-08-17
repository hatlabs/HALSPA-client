from typing import Callable

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
            raise ValueError(f"Unknown ADC I2C address: 0x{addr:02x}. Expected 0x48 (ADC1) or 0x49 (ADC2)")
        
    def get_channel(self, channel: int) -> 'ADCChannel':
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
        
        # Get calibration scale automatically
        from picon.calibration import ADC1_SCALES, ADC2_SCALES
        if calibrated_adc.adc_num == 1:
            self.scale = ADC1_SCALES[adc_channel]
        elif calibrated_adc.adc_num == 2:
            self.scale = ADC2_SCALES[adc_channel]
        else:
            raise ValueError(f"Invalid ADC number: {calibrated_adc.adc_num}")

    def read_raw(self):
        return self.calibrated_adc.read(channel1=self.adc_channel)

    def read_voltage(self):
        raw_voltage = self.calibrated_adc.raw_to_v(self.read_raw())
        return raw_voltage / self.scale


class ADCDiff:
    def __init__(
        self,
        calibrated_adc: CalibratedADS1115,
        adc_channel1: int,
        adc_channel2: int,
        scale: float = 1.0,
    ):
        """
        Differential ADC measurement between two channels.
        
        Args:
            calibrated_adc: CalibratedADS1115 instance
            adc_channel1: Positive channel (0-3)
            adc_channel2: Negative channel (0-3)
            scale: Additional scale factor for differential measurement
        """
        self.calibrated_adc = calibrated_adc
        self.adc_channel1 = adc_channel1
        self.adc_channel2 = adc_channel2
        self.scale = scale

    def read_raw(self):
        return self.calibrated_adc.read(channel1=self.adc_channel1, channel2=self.adc_channel2)

    def read_voltage(self):
        raw_voltage = self.calibrated_adc.raw_to_v(self.read_raw())
        return raw_voltage / self.scale


class AnalogMuxADCChannel:
    def __init__(self, select_pin_func: Callable[[], None], adc_channel: ADCChannel):
        self.select_pin = select_pin_func
        self.adc_channel = adc_channel

    def read_raw(self):
        self.select_pin()
        return self.adc_channel.read_raw()

    def read_voltage(self):
        self.select_pin()
        return self.adc_channel.read_voltage()
