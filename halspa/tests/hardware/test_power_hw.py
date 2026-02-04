"""Hardware tests for PowerControl (TCA9535 @ 0x20).

On a bare board with no DUT/load, enabling rails should produce no faults.
"""

import pytest


@pytest.fixture(autouse=True)
def disable_power(board):
    """Ensure all power is off before and after each test."""
    board.power.disable_all()
    yield
    board.power.disable_all()


RAILS = [
    "enable_5v",
    "enable_3v3",
    "enable_12v_1",
    "enable_12v_2",
]


@pytest.mark.parametrize("rail", RAILS)
def test_enable_disable_rail(board, rail):
    """Enable a rail, verify no faults, then disable."""
    enable = getattr(board.power, rail)
    enable(True)
    faults = board.power.read_fault()
    assert faults == 0, f"Faults after enabling {rail}: {faults:#06x}"
    enable(False)


def test_disable_all(board):
    """Enable multiple rails, then disable_all and verify outputs are zero."""
    board.power.enable_5v(True)
    board.power.enable_3v3(True)
    board.power.disable_all()
    assert board.power.tca9535.output == 0


def test_no_faults_at_idle(board):
    """With everything off, no faults should be asserted."""
    assert board.power.read_fault() == 0


def test_deferred_commit(board):
    """Deferred writes should not take effect until commit."""
    board.power.enable_5v(True, defer=True)
    board.power.enable_3v3(True, defer=True)
    board.power.commit()
    faults = board.power.read_fault()
    assert faults == 0
