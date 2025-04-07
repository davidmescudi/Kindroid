"""
Camera module for QR code reading and image capture.
"""
import cv2
import threading
import time
from pyzbar.pyzbar import decode
from typing import Optional, Tuple, List, Callable

from ..core.base import HardwareModule


class CameraModule(HardwareModule):
    """Camera module for QR code reading and image capture."""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.camera = None
        self.camera_id = self.config.get('camera_id', 0)
        self.resolution = self.config.get('resolution', (640, 480))
        self.scan_interval = self.config.get('scan_interval', 0.1)  # seconds between scans
        self.qr_callback = None
        self.scan_thread = None
        self.running = False
        self.last_detected_codes = set()  # Track recently detected codes to avoid duplicates
    
    def initialize(self) -> bool:
        """Initialize the camera."""
        try:
            self.camera = cv2.VideoCapture(self.camera_id)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.is_initialized = self.camera.isOpened()
            
            if self.is_initialized:
                # Start the background scanning thread
                self.running = True
                self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
                self.scan_thread.start()
            
            return self.is_initialized
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Release the camera."""
        self.running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=1.0)
        
        if self.camera:
            self.camera.release()
            self.is_initialized = False
        return True
    
    def get_status(self) -> dict:
        """Get camera status."""
        return {
            "initialized": self.is_initialized,
            "camera_id": self.camera_id,
            "resolution": self.resolution,
            "scanning": self.running,
            "callback_registered": self.qr_callback is not None
        }
    
    def register_qr_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Register a callback function to be called when a QR code is detected.
        Args:
            callback: Function that takes (data, type) as arguments
        """
        self.qr_callback = callback
    
    def _scan_loop(self) -> None:
        """Background thread that continuously scans for QR codes."""
        while self.running:
            try:
                if not self.is_initialized:
                    time.sleep(self.scan_interval)
                    continue
                
                ret, frame = self.camera.read()
                if not ret:
                    time.sleep(self.scan_interval)
                    continue
                
                decoded_objects = decode(frame)
                current_codes = set()
                
                for obj in decoded_objects:
                    data = obj.data.decode('utf-8')
                    code_type = obj.type
                    current_codes.add(data)
                    
                    # Only trigger callback for newly detected codes
                    if data not in self.last_detected_codes and self.qr_callback:
                        self.qr_callback(data, code_type)
                
                # Update the set of recently detected codes
                self.last_detected_codes = current_codes
                
            except Exception as e:
                print(f"Error in QR scan loop: {e}")
            
            time.sleep(self.scan_interval)
    
    def read_qr_code(self) -> List[Tuple[str, str]]:
        """
        Read QR codes from the camera feed.
        Returns a list of tuples (data, type).
        """
        if not self.is_initialized:
            raise RuntimeError("Camera not initialized")
        
        ret, frame = self.camera.read()
        if not ret:
            return []
        
        decoded_objects = decode(frame)
        return [(obj.data.decode('utf-8'), obj.type) for obj in decoded_objects]
    
    def capture_frame(self) -> Optional[cv2.Mat]:
        """Capture a single frame from the camera."""
        if not self.is_initialized:
            raise RuntimeError("Camera not initialized")
        
        ret, frame = self.camera.read()
        return frame if ret else None 