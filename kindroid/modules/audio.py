"""
Audio module for speech recognition and text-to-speech.
"""
import speech_recognition as sr
import pyttsx3
import threading
import time
from typing import Optional, Callable, Tuple

from ..core.base import HardwareModule


class AudioModule(HardwareModule):
    """Audio module for speech recognition and text-to-speech."""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.recognizer = sr.Recognizer()
        self.engine = None
        self.microphone = None
        self.language = self.config.get('language', 'en-US')
        self.voice_rate = self.config.get('voice_rate', 150)
        self.voice_volume = self.config.get('voice_volume', 1.0)
        self.energy_threshold = self.config.get('energy_threshold', 300)
        self.pause_threshold = self.config.get('pause_threshold', 0.8)
        self.phrase_threshold = self.config.get('phrase_threshold', 0.3)
        self.non_speaking_duration = self.config.get('non_speaking_duration', 0.5)
        self.listening_thread = None
        self.is_listening = False
        self.speech_callback = None
    
    def initialize(self) -> bool:
        """Initialize the audio components."""
        try:
            # Initialize text-to-speech engine
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.voice_rate)
            self.engine.setProperty('volume', self.voice_volume)
            
            # Initialize microphone
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            
            # Set recognition parameters
            self.recognizer.energy_threshold = self.energy_threshold
            self.recognizer.pause_threshold = self.pause_threshold
            self.recognizer.phrase_threshold = self.phrase_threshold
            self.recognizer.non_speaking_duration = self.non_speaking_duration
            
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize audio: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown audio components."""
        self.stop_listening()
        if self.engine:
            self.engine.stop()
        self.is_initialized = False
        return True
    
    def get_status(self) -> dict:
        """Get audio module status."""
        return {
            "initialized": self.is_initialized,
            "language": self.language,
            "voice_rate": self.voice_rate,
            "voice_volume": self.voice_volume,
            "is_listening": self.is_listening,
            "energy_threshold": self.energy_threshold,
            "pause_threshold": self.pause_threshold
        }
    
    def listen_for_speech(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for speech and convert to text.
        Args:
            timeout: Time to wait for speech in seconds
        Returns:
            Recognized text or None if no speech detected
        """
        if not self.is_initialized:
            raise RuntimeError("Audio module not initialized")
        
        try:
            with self.microphone as source:
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout)
                print("Processing speech...")
                text = self.recognizer.recognize_google(audio, language=self.language)
                return text
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except Exception as e:
            print(f"Error in speech recognition: {e}")
            return None
    
    def start_listening(self, callback: Callable[[str], None]) -> bool:
        """
        Start continuous listening for speech with a callback.
        Args:
            callback: Function to call with recognized text
        Returns:
            True if started successfully
        """
        if not self.is_initialized:
            raise RuntimeError("Audio module not initialized")
        
        if self.is_listening:
            print("Already listening")
            return False
        
        self.speech_callback = callback
        self.is_listening = True
        self.listening_thread = threading.Thread(target=self._listening_loop, daemon=True)
        self.listening_thread.start()
        return True
    
    def stop_listening(self) -> bool:
        """
        Stop continuous listening.
        Returns:
            True if stopped successfully
        """
        if not self.is_listening:
            return True
        
        self.is_listening = False
        if self.listening_thread:
            self.listening_thread.join(timeout=1.0)
            self.listening_thread = None
        return True
    
    def _listening_loop(self) -> None:
        """Background thread that continuously listens for speech."""
        while self.is_listening:
            try:
                with self.microphone as source:
                    print("Listening...")
                    audio = self.recognizer.listen(source)
                    print("Processing speech...")
                    text = self.recognizer.recognize_google(audio, language=self.language)
                    if text and self.speech_callback:
                        self.speech_callback(text)
            except sr.UnknownValueError:
                # Speech was unintelligible, continue listening
                pass
            except Exception as e:
                print(f"Error in continuous listening: {e}")
                # Brief pause before retrying
                time.sleep(0.1)
    
    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it.
        Args:
            text: Text to speak
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Audio module not initialized")
        
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return False
    
    def set_voice_properties(self, rate: Optional[int] = None, volume: Optional[float] = None) -> None:
        """Update voice properties."""
        if rate is not None:
            self.voice_rate = rate
            self.engine.setProperty('rate', rate)
        if volume is not None:
            self.voice_volume = volume
            self.engine.setProperty('volume', volume)
    
    def set_recognition_parameters(self, 
                                  energy_threshold: Optional[int] = None,
                                  pause_threshold: Optional[float] = None,
                                  phrase_threshold: Optional[float] = None,
                                  non_speaking_duration: Optional[float] = None) -> None:
        """
        Update speech recognition parameters.
        Args:
            energy_threshold: Minimum audio energy to consider for recording
            pause_threshold: Seconds of non-speaking audio before a phrase is considered complete
            phrase_threshold: Minimum seconds of speaking audio before we consider the speaking audio a phrase
            non_speaking_duration: Seconds of non-speaking audio to keep on both sides of the recording
        """
        if energy_threshold is not None:
            self.energy_threshold = energy_threshold
            self.recognizer.energy_threshold = energy_threshold
        if pause_threshold is not None:
            self.pause_threshold = pause_threshold
            self.recognizer.pause_threshold = pause_threshold
        if phrase_threshold is not None:
            self.phrase_threshold = phrase_threshold
            self.recognizer.phrase_threshold = phrase_threshold
        if non_speaking_duration is not None:
            self.non_speaking_duration = non_speaking_duration
            self.recognizer.non_speaking_duration = non_speaking_duration 