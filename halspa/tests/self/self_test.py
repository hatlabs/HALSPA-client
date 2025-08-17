from textwrap import dedent

import pytest

from halspa.adc import ADS1115, ADCChannel
from halspa.analog_mux import AnalogMux
from halspa.digexp import TCA9535
from halspa.pin import Pin
from halspa.power import PowerControl
from halspa.repl import REPL


@pytest.fixture(scope="module")
def repl():
    """
    Fixture to create a REPL instance for testing.
    """
    repl = REPL()
    repl.connect()
    yield repl
    repl.disconnect()


@pytest.fixture(scope="module")
def powcon(repl):
    """
    Fixture to create a PowerControl instance for testing.
    """
    powcon = PowerControl(repl)
    yield powcon


@pytest.fixture(scope="module")
def anamux(repl):
    """
    Fixture to create an AnalogMux instance for testing.
    """
    anamux = AnalogMux(repl)
    yield anamux


@pytest.fixture(scope="module")
def ads1115_2(repl):
    """
    Fixture to create an ADS1115 instance for testing.
    """
    ads1115_2 = ADS1115(repl, 2, 1)
    yield ads1115_2


@pytest.fixture(scope="module")
def ads1115_1(repl):
    """
    Fixture to create an ADS1115 instance for testing.
    """
    ads1115_1 = ADS1115(repl, 1, 1)
    yield ads1115_1


@pytest.fixture(scope="module")
def digexp2(repl):
    """
    Fixture to create a TCA9535 instance for testing.
    """
    digexp2 = TCA9535(repl, 2)
    yield digexp2


def test_enable_power_5v(powcon):
    """
    Test enabling and disabling power rails.
    """
    try:
        powcon.enable_power("5v", True)

        flags = powcon.read_power_fault()
        assert flags == 0
    finally:
        powcon.enable_power("5v", False)


def test_enable_12v_2(powcon):
    """
    Test enabling and disabling power rails.
    """
    try:
        powcon.enable_power("12v_2", True)

        flags = powcon.read_power_fault()
        assert flags == 0
    finally:
        powcon.enable_power("12v_2", False)


def test_anamux(repl, anamux, digexp2, ads1115_1):
    gpio2 = Pin(repl, 2, "output")
    de2_pin2 = digexp2.get_pin(2)

    gpio2.set(False)
    de2_pin2.configure(1)
    de2_pin2.write(0)

    adc1_0 = ADCChannel(ads1115_1, 0)

    anamux.select(1, 1)
    v = adc1_0.read_voltage()

    assert v < 0.1, f"Anamux 1 pin 1 voltage too high: {v}V"

    anamux.select(1, 0)
    v = adc1_0.read_voltage()
    assert v > 3.2, f"Anamux 1 pin 0 voltage too low: {v}V"

    anamux.select(1, 7)
    v = adc1_0.read_voltage()
    assert v < 0.1, f"Anamux 1 pin 7 voltage too high: {v}V"
    de2_pin2.write(1)
    v = adc1_0.read_voltage()
    assert v > 3.1, f"Anamux 1 pin 7 voltage too low: {v}V"


def test_repl(repl):
    output = repl.execute("print('Hello, HALSPA!')")
    assert output.strip() == "Hello, HALSPA!", (
        f"Unexpected REPL output: {output.strip()}"
    )


def test_repl_long_response(repl):
    output = repl.execute("print(('Hello, HALSPA! ' * 1000).strip())")
    assert output.strip() == ("Hello, HALSPA! " * 1000).strip(), (
        f"Unexpected REPL output: {output.strip()}"
    )


def test_repl_long_command(repl):
    command = dedent("""
    print('00000000000000000')
    print('11111111111111111')
    print('22222222222222222')
    print('33333333333333333')
    print('44444444444444444')
    print('55555555555555555')
    print('66666666666666666')
    print('77777777777777777')
    print('88888888888888888')
    print('99999999999999999')
    """).strip()

    output = repl.execute(command)
    expected_output = (
        "00000000000000000\n"
        "11111111111111111\n"
        "22222222222222222\n"
        "33333333333333333\n"
        "44444444444444444\n"
        "55555555555555555\n"
        "66666666666666666\n"
        "77777777777777777\n"
        "88888888888888888\n"
        "99999999999999999"
    )

    assert output.strip() == expected_output, (
        f"Unexpected REPL output: {output.strip()}"
    )
