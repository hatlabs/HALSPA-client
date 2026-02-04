"""Tests for HalspaBoard with mocked SMBus."""

from unittest.mock import MagicMock, patch

import pytest

from halspa.board import HalspaBoard


@pytest.fixture
def mock_smbus():
    with patch("halspa.board.SMBus") as MockSMBus:
        mock_bus = MagicMock()
        mock_bus.read_byte_data.return_value = 0
        MockSMBus.return_value = mock_bus
        yield MockSMBus, mock_bus


class TestHalspaBoardInit:
    def test_opens_smbus(self, mock_smbus):
        MockSMBus, mock_bus = mock_smbus
        board = HalspaBoard(i2c_bus=1)
        MockSMBus.assert_called_once_with(1)

    def test_creates_all_devices(self, mock_smbus):
        _, mock_bus = mock_smbus
        board = HalspaBoard()
        assert board.power is not None
        assert board.mux is not None
        assert board.digexp1 is not None
        assert board.digexp2 is not None
        assert board.adc1 is not None
        assert board.adc2 is not None

    def test_digexp_addresses(self, mock_smbus):
        _, mock_bus = mock_smbus
        board = HalspaBoard()
        assert board.digexp1.address == 0x22
        assert board.digexp2.address == 0x23

    def test_adc_addresses(self, mock_smbus):
        _, mock_bus = mock_smbus
        board = HalspaBoard()
        assert board.adc1.address == 0x48
        assert board.adc2.address == 0x49


class TestHalspaBoardInitFailure:
    def test_closes_bus_on_device_init_failure(self, mock_smbus):
        _, mock_bus = mock_smbus
        # Make the first I2C write fail (PowerControl init)
        mock_bus.write_byte_data.side_effect = OSError("I2C device not responding")
        with pytest.raises(OSError):
            HalspaBoard()
        mock_bus.close.assert_called_once()


class TestHalspaBoardContextManager:
    def test_context_manager_closes_bus(self, mock_smbus):
        _, mock_bus = mock_smbus
        with HalspaBoard() as board:
            pass
        mock_bus.close.assert_called_once()

    def test_context_manager_returns_board(self, mock_smbus):
        with HalspaBoard() as board:
            assert isinstance(board, HalspaBoard)


class TestHalspaBoardScan:
    def test_i2c_scan_finds_devices(self, mock_smbus):
        _, mock_bus = mock_smbus

        def read_byte_side_effect(addr):
            if addr in [0x20, 0x21, 0x22, 0x23, 0x48, 0x49]:
                return 0
            raise OSError("No device")

        mock_bus.read_byte.side_effect = read_byte_side_effect

        board = HalspaBoard()
        found = board.i2c_scan()
        assert found == [0x20, 0x21, 0x22, 0x23, 0x48, 0x49]

    def test_i2c_scan_empty_bus(self, mock_smbus):
        _, mock_bus = mock_smbus
        mock_bus.read_byte.side_effect = OSError("No device")

        board = HalspaBoard()
        found = board.i2c_scan()
        assert found == []
