"""
Tests for the printer module.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from kindroid.modules.printer import PrinterModule


@pytest.fixture
def printer():
    """Create a printer instance with mocked serial port."""
    with patch('serial.Serial') as mock_serial:
        mock_serial.return_value.is_open = True
        printer = PrinterModule()
        printer.initialize()
        yield printer
        printer.shutdown()


def test_printer_initialization(printer):
    """Test printer initialization."""
    assert printer.is_initialized
    assert printer.port == '/dev/ttyUSB0'
    assert printer.baud_rate == 9600


def test_printer_status(printer):
    """Test printer status reporting."""
    status = printer.get_status()
    assert isinstance(status, dict)
    assert status['initialized'] is True
    assert status['port'] == '/dev/ttyUSB0'
    assert status['baud_rate'] == 9600
    assert isinstance(status['is_printing'], bool)
    assert isinstance(status['queue_length'], int)


def test_print_text(printer):
    """Test text printing."""
    result = printer.print_text("Test text", align='center', bold=True, size=2)
    assert result is True


def test_print_qr_code(printer):
    """Test QR code printing."""
    result = printer.print_qr_code("https://example.com", size=3)
    assert result is True


def test_feed_paper(printer):
    """Test paper feeding."""
    result = printer.feed_paper(lines=2)
    assert result is True


def test_cut_paper(printer):
    """Test paper cutting."""
    result = printer.cut_paper()
    assert result is True


def test_print_queue(printer):
    """Test print queue functionality."""
    # Add jobs to queue
    assert printer.queue_print('text', text="Test 1")
    assert printer.queue_print('qr_code', data="https://example.com")
    assert printer.queue_print('feed', lines=2)
    assert printer.queue_print('cut')
    
    # Check queue length
    assert len(printer.print_queue) == 4
    
    # Start printing
    assert printer.start_printing() is True
    assert printer.is_printing is True
    
    # Stop printing
    assert printer.stop_printing() is True
    assert printer.is_printing is False


def test_invalid_print_type(printer):
    """Test handling of invalid print type."""
    with pytest.raises(KeyError):
        printer.queue_print('invalid_type')


def test_uninitialized_printer():
    """Test operations on uninitialized printer."""
    printer = PrinterModule()
    assert printer.is_initialized is False
    
    with pytest.raises(RuntimeError):
        printer.print_text("Test")
    
    with pytest.raises(RuntimeError):
        printer.print_qr_code("Test")
    
    with pytest.raises(RuntimeError):
        printer.feed_paper()
    
    with pytest.raises(RuntimeError):
        printer.cut_paper() 