import ads1x15
from sauce.tca9535 import TCA9535
from machine import I2C, Pin
from micropython import const

from sauce.analog_mux import AnalogMux
from sauce.power_control import PowerControl

SDA_PIN = const(20)
SCL_PIN = const(21)

ADC1_ADDR = const(0x48)
ADC2_ADDR = const(0x49)

ANA_MUX_ADDR = const(0x24)


i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
powcon = PowerControl(i2c)
anamux = AnalogMux(i2c)
adc1 = ads1x15.ADS1115(i2c, ADC1_ADDR, 1)
adc2 = ads1x15.ADS1115(i2c, ADC2_ADDR, 1)

digexp1 = TCA9535(i2c, address=0x22)
digexp2 = TCA9535(i2c, address=0x23)
