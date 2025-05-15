from time import sleep

from machine import Pin
from micropython import const

from sauce.analog_mux import ADCChannel, AnalogMuxADCChannel
from sauce.pwm import pwm_context_manager
from sauce.sauce import *

SDA_PIN = const(20)
SCL_PIN = const(21)


def main():
    powcon.enable_12v_1(True)
    sleep(1.0)

    powcon.disable_all()

    print("Faults:", bin(powcon.read_fault()))

    print("ADC1 channel 0:", adc1.raw_to_v(adc1.read(6, 0)))
    print("ADC1 channel 1:", adc1.raw_to_v(adc1.read(6, 1)))
    print("ADC1 channel 2:", adc1.raw_to_v(adc1.read(6, 2)))
    print("ADC1 channel 3:", adc1.raw_to_v(adc1.read(6, 3)))


def test_analog():
    adc1_ch0 = ADCChannel(adc1, 0, rt=67.2e3)
    select_lpfilt_output = anamux.get_pin_selector(1, 1)
    select_opamp_output = anamux.get_pin_selector(1, 0)
    select_level_shifter_output = anamux.get_pin_selector(1, 2)
    select_12vl2cs = anamux.get_pin_selector(1, 3)

    digout_gp2 = Pin(2, Pin.OUT)
    digout_gp4 = Pin(4, Pin.OUT)

    gp2_exp_pin = digexp1.get_pin(0)
    gp4_exp_pin = digexp2.get_pin(0o14)

    pwm_via_lpfilt = AnalogMuxADCChannel(select_lpfilt_output, adc1_ch0)
    pwm_via_opamp_mux = AnalogMuxADCChannel(select_opamp_output, adc1_ch0)
    lshifter_via_mux = AnalogMuxADCChannel(select_level_shifter_output, adc1_ch0)

    p12vlimit2cs = AnalogMuxADCChannel(select_12vl2cs, adc1_ch0)

    pwm_via_opamp = ADCChannel(adc1, 1, scale=2.733 / 0.379)
    output_limit_12v1 = ADCChannel(adc1, 2, rt=89.83e3)
    raw_3v3 = ADCChannel(adc1, 3, rt=53.91e3)

    sleep(0.1)

    with pwm_context_manager(15, freq=100000, duty_u16=32768) as pwm:  # type: ignore
        print("PWM via LPFilt:", pwm_via_lpfilt.read_v())
        print("PWM via OpAmp Mux:", pwm_via_opamp_mux.read_v())
        print("PWM via OpAmp:", pwm_via_opamp.read_v())

    print("Raw 3V3:", raw_3v3.read_v())

    print("12V Output Limit 1:", output_limit_12v1.read_v())

    with powcon.enable_12v_1():  # type: ignore
        sleep(0.1)
        print("12V Output Limit 1:", output_limit_12v1.read_v())
    sleep(0.1)
    print("12V Output Limit 1:", output_limit_12v1.read_v())

    digout_gp2.value(0)
    print("Level shifter output:", lshifter_via_mux.read_v())
    print("Digital expander GP2:", gp2_exp_pin.read())
    print("Dig exp 1 input:", bin(digexp1.read()))
    digout_gp2.value(1)
    print("Level shifter output:", lshifter_via_mux.read_v())
    print("Digital expander GP2:", gp2_exp_pin.read())
    print("Dig exp 1 input:", bin(digexp1.read()))

    digout_gp4.value(0)
    print("Digital expander GP4:", gp4_exp_pin.read())
    print("Dig exp 2 input:", bin(digexp2.read()))
    digout_gp4.value(1)
    print("Digital expander GP4:", gp4_exp_pin.read())
    print("Dig exp 2 input:", bin(digexp2.read()))

    with powcon.enable_12v_2():  # type: ignore
        sleep(0.1)
        print("12V Output Limit 2 current:", 2 * p12vlimit2cs.read_v())
