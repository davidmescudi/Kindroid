"""
Main Robot class that coordinates all hardware modules.
"""
from typing import Optional, Dict, Any, Callable
import json
import os
import threading

from .modules.camera import CameraModule
from .modules.audio import AudioModule
from .modules.llm import LLMModule


class Robot:
    """Main Robot class that coordinates all hardware modules."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the robot with optional configuration.
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path) if config_path else {}
        
        # Initialize modules
        self.camera = CameraModule(self.config.get('camera', {}))
        self.audio = AudioModule(self.config.get('audio', {}))
        self.llm = LLMModule(self.config.get('llm', {}))
        
        self.is_initialized = False
        self.qr_callback = None
        self.speech_callback = None
        self.interaction_thread = None
        self.is_interacting = False
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def initialize(self) -> bool:
        """Initialize all robot modules."""
        try:
            camera_ok = self.camera.initialize()
            audio_ok = self.audio.initialize()
            llm_ok = self.llm.initialize()
            
            self.is_initialized = all([camera_ok, audio_ok, llm_ok])
            
            # Register the QR callback if one is set
            if self.is_initialized and self.qr_callback:
                self.camera.register_qr_callback(self.qr_callback)
            
            return self.is_initialized
        except Exception as e:
            print(f"Error initializing robot: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown all robot modules."""
        try:
            self.stop_interaction()
            self.camera.shutdown()
            self.audio.shutdown()
            self.llm.shutdown()
            self.is_initialized = False
            return True
        except Exception as e:
            print(f"Error shutting down robot: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all modules."""
        return {
            "initialized": self.is_initialized,
            "camera": self.camera.get_status(),
            "audio": self.audio.get_status(),
            "llm": self.llm.get_status(),
            "is_interacting": self.is_interacting
        }
    
    def process_interaction(self) -> Optional[str]:
        """
        Process a complete interaction cycle:
        1. Listen for speech
        2. Generate LLM response
        3. Speak the response
        Returns:
            The generated response or None if failed
        """
        if not self.is_initialized:
            raise RuntimeError("Robot not initialized")
        
        # Listen for speech
        user_input = self.audio.listen_for_speech()
        if not user_input:
            return None
        
        # Generate response
        response = self.llm.generate_response(user_input)
        if not response:
            return None
        
        # Speak response
        if self.audio.speak(response):
            return response
        return None
    
    def start_interaction(self, callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Start continuous interaction with speech recognition and LLM responses.
        Args:
            callback: Optional callback function to receive the LLM responses
        Returns:
            True if started successfully
        """
        if not self.is_initialized:
            raise RuntimeError("Robot not initialized")
        
        if self.is_interacting:
            print("Already in interaction mode")
            return False
        
        self.speech_callback = callback
        self.is_interacting = True
        
        # Start the interaction thread
        self.interaction_thread = threading.Thread(target=self._interaction_loop, daemon=True)
        self.interaction_thread.start()
        
        return True
    
    def stop_interaction(self) -> bool:
        """
        Stop continuous interaction.
        Returns:
            True if stopped successfully
        """
        if not self.is_interacting:
            return True
        
        self.is_interacting = False
        if self.interaction_thread:
            self.interaction_thread.join(timeout=1.0)
            self.interaction_thread = None
        
        # Also stop any ongoing speech recognition
        self.audio.stop_listening()
        
        return True
    
    def _interaction_loop(self) -> None:
        """Background thread that handles continuous interaction."""
        def handle_speech(text: str) -> None:
            """Handle recognized speech by generating and speaking a response."""
            if not text:
                return
            
            # Generate response
            response = self.llm.generate_response(text)
            if not response:
                return
            
            # Speak response
            if self.audio.speak(response):
                # Call the callback if provided
                if self.speech_callback:
                    self.speech_callback(response)
        
        # Start continuous speech recognition
        self.audio.start_listening(handle_speech)
        
        # Keep the thread alive while interaction is active
        while self.is_interacting:
            # Sleep to prevent CPU hogging
            import time
            time.sleep(0.1)
    
    def register_qr_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Register a callback function to be called when a QR code is detected.
        Args:
            callback: Function that takes (data, type) as arguments
        """
        self.qr_callback = callback
        if self.is_initialized:
            self.camera.register_qr_callback(callback)
    
    def read_qr_code(self) -> Optional[str]:
        """
        Read a QR code using the camera.
        Returns:
            QR code data or None if no code found
        """
        if not self.is_initialized:
            raise RuntimeError("Robot not initialized")
        
        results = self.camera.read_qr_code()
        if results:
            return results[0][0]  # Return first QR code's data
        return None
    
    def update_llm_settings(self, **kwargs) -> bool:
        """Update LLM module settings."""
        return self.llm.update_settings(**kwargs)
    
    def update_audio_settings(self, rate: Optional[int] = None, volume: Optional[float] = None) -> None:
        """Update audio module settings."""
        self.audio.set_voice_properties(rate=rate, volume=volume)
    
    def update_recognition_settings(self, **kwargs) -> None:
        """Update speech recognition settings."""
        self.audio.set_recognition_parameters(**kwargs) 