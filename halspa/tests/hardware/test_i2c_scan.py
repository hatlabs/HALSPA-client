"""Verify all HALSPA I2C devices are present on the bus."""

from .conftest import EXPECTED_ADDRESSES


def test_all_devices_respond(board):
    found = set(board.i2c_scan())
    missing = EXPECTED_ADDRESSES - found
    assert not missing, f"Missing I2C devices: {[hex(a) for a in sorted(missing)]}"


def test_no_unexpected_devices(board):
    """Flag unexpected addresses (informational, not a hard failure)."""
    found = set(board.i2c_scan())
    unexpected = found - EXPECTED_ADDRESSES
    # Not asserting — unexpected devices may be on the bus legitimately.
    # But we print them so they're visible in test output.
    if unexpected:
        print(f"Unexpected I2C addresses: {[hex(a) for a in sorted(unexpected)]}")
