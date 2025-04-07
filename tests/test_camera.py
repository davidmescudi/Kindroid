"""
Tests for the camera module.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from kindroid.modules.camera import CameraModule


@pytest.fixture
def camera():
    """Create a camera instance with mocked RealSense pipeline."""
    with patch('pyrealsense2.pipeline') as mock_pipeline:
        mock_pipeline.return_value.start.return_value = True
        mock_pipeline.return_value.stop.return_value = True
        camera = CameraModule()
        camera.initialize()
        yield camera
        camera.shutdown()


def test_camera_initialization(camera):
    """Test camera initialization."""
    assert camera.is_initialized
    assert camera.pipeline is not None


def test_camera_status(camera):
    """Test camera status reporting."""
    status = camera.get_status()
    assert isinstance(status, dict)
    assert status['initialized'] is True
    assert isinstance(status['fps'], float)
    assert isinstance(status['resolution'], tuple)
    assert len(status['resolution']) == 2


def test_capture_frame(camera):
    """Test frame capture."""
    frame = camera.capture_frame()
    assert isinstance(frame, np.ndarray)
    assert frame.ndim == 3  # Should be a color image
    assert frame.shape[2] == 3  # Should have 3 color channels


def test_capture_depth(camera):
    """Test depth capture."""
    depth_frame = camera.capture_depth()
    assert isinstance(depth_frame, np.ndarray)
    assert depth_frame.ndim == 2  # Should be a grayscale image


def test_detect_qr_codes(camera):
    """Test QR code detection."""
    # Mock a frame with a QR code
    mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    with patch.object(camera, 'capture_frame', return_value=mock_frame):
        codes = camera.detect_qr_codes()
        assert isinstance(codes, list)


def test_uninitialized_camera():
    """Test operations on uninitialized camera."""
    camera = CameraModule()
    assert camera.is_initialized is False
    
    with pytest.raises(RuntimeError):
        camera.capture_frame()
    
    with pytest.raises(RuntimeError):
        camera.capture_depth()
    
    with pytest.raises(RuntimeError):
        camera.detect_qr_codes() 