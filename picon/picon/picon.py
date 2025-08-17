from machine import I2C, Pin
from micropython import const

from picon.adc import ads1x15, CalibratedADS1115
from picon.analog_mux import AnalogMux
from picon.power_control import PowerControl
from picon.tca9535 import TCA9535
from picon.calibration import *

SDA_PIN = const(20)
SCL_PIN = const(21)

ADC1_ADDR = const(0x48)
ADC2_ADDR = const(0x49)

DIGEXP1_ADDR = const(0x22)
DIGEXP2_ADDR = const(0x23)

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))

powcon = PowerControl(i2c)
anamux = AnalogMux(i2c)
# Create calibrated ADS1115 instances (auto-detects ADC number from address)
ads1 = CalibratedADS1115(i2c, ADC1_ADDR, 1)  # Auto-detects adc_num=1
ads2 = CalibratedADS1115(i2c, ADC2_ADDR, 1)  # Auto-detects adc_num=2

digexp1 = TCA9535(i2c, address=DIGEXP1_ADDR)
digexp2 = TCA9535(i2c, address=DIGEXP2_ADDR)

# Auto-calibrated channels - scale is applied automatically
adc1_ch0 = ads1.get_channel(0)
adc1_ch1 = ads1.get_channel(1)
adc1_ch2 = ads1.get_channel(2)
adc1_ch3 = ads1.get_channel(3)

adc2_ch0 = ads2.get_channel(0)
adc2_ch1 = ads2.get_channel(1)
adc2_ch2 = ads2.get_channel(2)
adc2_ch3 = ads2.get_channel(3)
