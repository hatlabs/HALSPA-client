"""Hardware tests for AnalogMux (TCA9535 @ 0x21).

Tests verify the digital control side only (TCA9535 register state).
No analog signal path is verified on a bare board.
"""

import pytest

from halspa.analog_mux import ANAMUX_INITIAL_STATE, INH_PINS


@pytest.fixture(autouse=True)
def reset_mux(board):
    """Restore mux to initial state after each test."""
    yield
    board.mux.ctrl.write(ANAMUX_INITIAL_STATE)


def test_initial_state(board):
    """Mux control register should be at initial state."""
    assert board.mux.ctrl.output == ANAMUX_INITIAL_STATE


@pytest.mark.parametrize("mux_num", [1, 2, 3, 4])
def test_enable_clears_inh(board, mux_num):
    """Enabling a mux clears its INH pin."""
    board.mux.enable(mux_num, True)
    inh_pin = INH_PINS[mux_num - 1]
    assert not (board.mux.ctrl.output & (1 << inh_pin))


@pytest.mark.parametrize("mux_num", [1, 2, 3, 4])
def test_disable_sets_inh(board, mux_num):
    """Disabling a mux sets its INH pin."""
    board.mux.enable(mux_num, True)
    board.mux.enable(mux_num, False)
    inh_pin = INH_PINS[mux_num - 1]
    assert board.mux.ctrl.output & (1 << inh_pin)


@pytest.mark.parametrize("mux_num", [1, 2, 3, 4])
def test_select_enables_mux(board, mux_num):
    """After select(), the mux should be enabled."""
    board.mux.select(mux_num, 0)
    inh_pin = INH_PINS[mux_num - 1]
    assert not (board.mux.ctrl.output & (1 << inh_pin))


@pytest.mark.parametrize("mux_num", [1, 2, 3, 4])
def test_select_different_channels(board, mux_num):
    """Selecting different channels should change the register state."""
    board.mux.select(mux_num, 0)
    state_ch0 = board.mux.ctrl.output

    board.mux.select(mux_num, 3)
    state_ch3 = board.mux.ctrl.output

    # Different channels should produce different register values
    assert state_ch0 != state_ch3


def test_register_readback(board):
    """Shadow register should match actual hardware readback."""
    board.mux.select(1, 5)
    shadow = board.mux.ctrl.output
    actual = board.mux.ctrl.read()
    assert shadow == actual
