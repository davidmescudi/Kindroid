"""
Tests for the Robot class.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

from kindroid.robot import Robot


@pytest.fixture
def robot():
    """Create a Robot instance with mocked modules."""
    with patch('kindroid.modules.camera.CameraModule') as mock_camera, \
         patch('kindroid.modules.audio.AudioModule') as mock_audio, \
         patch('kindroid.modules.llm.LLMModule') as mock_llm, \
         patch('kindroid.modules.printer.PrinterModule') as mock_printer:
        
        # Setup mock modules
        mock_camera.return_value.initialize.return_value = True
        mock_audio.return_value.initialize.return_value = True
        mock_llm.return_value.initialize.return_value = True
        mock_printer.return_value.initialize.return_value = True
        
        robot = Robot()
        robot.initialize()
        yield robot
        robot.shutdown()


def test_robot_initialization(robot):
    """Test Robot initialization."""
    assert robot.is_initialized
    assert robot.camera is not None
    assert robot.audio is not None
    assert robot.llm is not None
    assert robot.printer is not None


def test_robot_status(robot):
    """Test Robot status reporting."""
    status = robot.get_status()
    assert isinstance(status, dict)
    assert status['initialized'] is True
    assert isinstance(status['camera'], dict)
    assert isinstance(status['audio'], dict)
    assert isinstance(status['llm'], dict)
    assert isinstance(status['printer'], dict)


def test_start_interaction(robot):
    """Test starting interaction."""
    robot.start_interaction()
    assert robot.is_interacting is True
    robot.stop_interaction()


def test_stop_interaction(robot):
    """Test stopping interaction."""
    robot.start_interaction()
    assert robot.is_interacting is True
    robot.stop_interaction()
    assert robot.is_interacting is False


def test_handle_speech(robot):
    """Test speech handling."""
    with patch.object(robot.audio, 'listen', return_value="Test speech"):
        robot.handle_speech()
        assert robot.last_speech == "Test speech"


def test_handle_llm_response(robot):
    """Test LLM response handling."""
    with patch.object(robot.llm, 'chat', return_value="Test response"):
        robot.handle_llm_response("Test input")
        assert robot.last_llm_response == "Test response"


def test_handle_qr_code(robot):
    """Test QR code handling."""
    robot.handle_qr_code("Test QR", "QR_CODE")
    assert robot.last_qr_code == "Test QR"
    assert robot.last_qr_type == "QR_CODE"


def test_uninitialized_robot():
    """Test operations on uninitialized Robot."""
    robot = Robot()
    assert robot.is_initialized is False
    
    with pytest.raises(RuntimeError):
        robot.start_interaction()
    
    with pytest.raises(RuntimeError):
        robot.stop_interaction()
    
    with pytest.raises(RuntimeError):
        robot.handle_speech()
    
    with pytest.raises(RuntimeError):
        robot.handle_llm_response("Test")
    
    with pytest.raises(RuntimeError):
        robot.handle_qr_code("Test", "QR_CODE") 