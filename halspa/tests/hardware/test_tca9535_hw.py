"""Hardware tests for TCA9535 digital expanders (digexp1 @ 0x22, digexp2 @ 0x23).

On a bare board with no sandwich/DUT, output pins configured as outputs
should read back the driven value on the input port (pins are unloaded).
"""

import pytest


@pytest.fixture(params=["digexp1", "digexp2"])
def expander(request, board):
    """Yield each digital expander, restoring all-input config on cleanup."""
    exp = getattr(board, request.param)
    yield exp
    # Restore default: all pins as inputs, outputs high
    exp.write(0xFFFF)
    exp.write_configuration(0xFFFF)


def test_write_readback_all_zeros(expander):
    """Configure all pins as outputs, write 0x0000, read back."""
    expander.write_configuration(0x0000)
    expander.write(0x0000)
    assert expander.read() == 0x0000


def test_write_readback_all_ones(expander):
    """Configure all pins as outputs, write 0xFFFF, read back."""
    expander.write_configuration(0x0000)
    expander.write(0xFFFF)
    assert expander.read() == 0xFFFF


def test_write_readback_pattern(expander):
    """Write alternating bit pattern and verify readback."""
    expander.write_configuration(0x0000)
    expander.write(0xA5A5)
    assert expander.read() == 0xA5A5


def test_single_bit_write_read(expander):
    """Write and read individual bits."""
    expander.write_configuration(0x0000)
    expander.write(0x0000)

    for pin in (0, 7, 8, 15):
        expander.write_bit(pin, True)
        assert expander.read_bit(pin) is True

        expander.write_bit(pin, False)
        assert expander.read_bit(pin) is False


def test_pin_object_write_read(expander):
    """Use TCA9535Pin objects to write and read."""
    expander.write_configuration(0x0000)
    expander.write(0x0000)

    pin = expander.get_pin(4)
    pin.write(True)
    assert pin.read() is True

    pin.write(False)
    assert pin.read() is False
