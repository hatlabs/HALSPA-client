from machine import I2C, Pin
from micropython import const

from sauce.adc import ads1x15
from sauce.analog_mux import AnalogMux
from sauce.power_control import PowerControl
from sauce.tca9535 import TCA9535

SDA_PIN = const(20)
SCL_PIN = const(21)

ADC1_ADDR = const(0x48)
ADC2_ADDR = const(0x49)

DIGEXP1_ADDR = const(0x22)
DIGEXP2_ADDR = const(0x23)

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))

powcon = PowerControl(i2c)
anamux = AnalogMux(i2c)
ads1 = ads1x15.ADS1115(i2c, ADC1_ADDR, 1)
ads2 = ads1x15.ADS1115(i2c, ADC2_ADDR, 1)

digexp1 = TCA9535(i2c, address=DIGEXP1_ADDR)
digexp2 = TCA9535(i2c, address=DIGEXP2_ADDR)
