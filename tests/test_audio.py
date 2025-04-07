"""
Tests for the audio module.
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from kindroid.modules.audio import AudioModule


@pytest.fixture
def audio():
    """Create an audio instance with mocked PyAudio."""
    with patch('pyaudio.PyAudio') as mock_pyaudio:
        mock_pyaudio.return_value.open.return_value = MagicMock()
        audio = AudioModule()
        audio.initialize()
        yield audio
        audio.shutdown()


def test_audio_initialization(audio):
    """Test audio initialization."""
    assert audio.is_initialized
    assert audio.pyaudio is not None
    assert audio.stream is not None


def test_audio_status(audio):
    """Test audio status reporting."""
    status = audio.get_status()
    assert isinstance(status, dict)
    assert status['initialized'] is True
    assert isinstance(status['sample_rate'], int)
    assert isinstance(status['channels'], int)
    assert isinstance(status['chunk_size'], int)


def test_listen(audio):
    """Test listening for speech."""
    with patch('speech_recognition.Recognizer.recognize_google') as mock_recognize:
        mock_recognize.return_value = "Test speech"
        text = audio.listen()
        assert isinstance(text, str)
        assert text == "Test speech"


def test_speak(audio):
    """Test text-to-speech."""
    with patch('pyttsx3.Engine.say') as mock_say:
        result = audio.speak("Test text")
        assert result is True
        mock_say.assert_called_once_with("Test text")


def test_start_listening(audio):
    """Test starting continuous listening."""
    with patch('speech_recognition.Recognizer.recognize_google') as mock_recognize:
        mock_recognize.return_value = "Test speech"
        audio.start_listening(lambda text: None)
        assert audio.is_listening is True
        audio.stop_listening()


def test_stop_listening(audio):
    """Test stopping continuous listening."""
    audio.start_listening(lambda text: None)
    assert audio.is_listening is True
    audio.stop_listening()
    assert audio.is_listening is False


def test_uninitialized_audio():
    """Test operations on uninitialized audio."""
    audio = AudioModule()
    assert audio.is_initialized is False
    
    with pytest.raises(RuntimeError):
        audio.listen()
    
    with pytest.raises(RuntimeError):
        audio.speak("Test")
    
    with pytest.raises(RuntimeError):
        audio.start_listening(lambda text: None)
    
    with pytest.raises(RuntimeError):
        audio.stop_listening() 