"""Hardware tests for ADS1115 ADCs (adc1 @ 0x48, adc2 @ 0x49).

On a bare board, inputs are floating so values are unpredictable,
but conversions must complete without timeout and return valid 16-bit values.
"""

import pytest


@pytest.fixture(params=["adc1", "adc2"])
def adc(request, board):
    return getattr(board, request.param)


class TestSingleEnded:
    @pytest.mark.parametrize("channel", [0, 1, 2, 3])
    def test_read_completes(self, adc, channel):
        """Single-ended read must not timeout."""
        raw = adc.read(channel)
        assert -32768 <= raw <= 32767

    def test_raw_to_voltage_in_range(self, adc):
        """Converted voltage must be within full-scale range."""
        raw = adc.read(0)
        voltage = adc.raw_to_v(raw)
        assert -adc._full_scale <= voltage <= adc._full_scale


class TestDifferential:
    @pytest.mark.parametrize("pos,neg", [(0, 1), (0, 3), (1, 3), (2, 3)])
    def test_read_completes(self, adc, pos, neg):
        """Differential read must not timeout."""
        raw = adc.read_differential(pos, neg)
        assert -32768 <= raw <= 32767
