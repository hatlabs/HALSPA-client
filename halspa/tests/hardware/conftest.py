"""Fixtures for HALSPA hardware integration tests.

These tests require a physical HALSPA board connected via I2C.
When no hardware is present, all tests skip automatically.
"""

import pytest

from halspa.board import HalspaBoard

EXPECTED_ADDRESSES = {0x20, 0x21, 0x22, 0x23, 0x48, 0x49}


@pytest.fixture(scope="session")
def board():
    """Session-scoped HalspaBoard instance. Skips if hardware unavailable."""
    try:
        b = HalspaBoard()
    except OSError:
        pytest.skip("HALSPA board not available (I2C bus open failed)")
    yield b
    b.power.disable_all()
    b.close()
