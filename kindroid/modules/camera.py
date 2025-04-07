"""
Camera module for QR code reading and image capture.
"""
import cv2
import threading
import time
import numpy as np
from pyzbar.pyzbar import decode
from typing import Optional, Tuple, List, Callable, Dict, Any

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
        self.width = self.config.get('width', 640)
        self.height = self.config.get('height', 480)
        self.fps = self.config.get('fps', 30)
        self.is_capturing = False
        self.frame = None
        self.last_frame_time = 0
        self.frame_count = 0
        self.start_time = 0
    
    def initialize(self) -> bool:
        """Initialize the camera."""
        try:
            self.camera = cv2.VideoCapture(self.camera_id)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            if not self.camera.isOpened():
                print(f"Failed to open camera {self.camera_id}")
                return False
            
            self.is_initialized = True
            
            # Start the background scanning thread
            self.running = True
            self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.scan_thread.start()
            
            return True
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
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "scanning": self.running,
            "callback_registered": self.qr_callback is not None,
            "is_capturing": self.is_capturing,
            "frame_count": self.frame_count
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
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a frame from the camera.
        Returns:
            The captured frame as a numpy array, or None if capture failed
        """
        if not self.is_initialized:
            raise RuntimeError("Camera not initialized")
        
        try:
            ret, frame = self.camera.read()
            if ret:
                self.frame = frame
                self.frame_count += 1
                return frame
            return None
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None
    
    def detect_qr_codes(self) -> List[Dict[str, Any]]:
        """
        Detect QR codes in the current frame.
        Returns:
            List of dictionaries containing QR code data and position
        """
        if not self.is_initialized:
            raise RuntimeError("Camera not initialized")
        
        if self.frame is None:
            self.capture_frame()
        
        if self.frame is None:
            return []
        
        try:
            # Convert frame to grayscale for better QR detection
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            
            # Detect QR codes
            codes = decode(gray)
            
            # Convert to list of dictionaries with standardized format
            results = []
            for code in codes:
                # Convert bytes to string
                data = code.data.decode('utf-8')
                
                # Get QR code position
                points = code.polygon
                if points:
                    # Convert points to list of (x,y) tuples
                    points = [(p.x, p.y) for p in points]
                else:
                    # If no polygon points, use the rect
                    points = [
                        (code.rect.left, code.rect.top),
                        (code.rect.left + code.rect.width, code.rect.top),
                        (code.rect.left + code.rect.width, code.rect.top + code.rect.height),
                        (code.rect.left, code.rect.top + code.rect.height)
                    ]
                
                results.append({
                    'data': data,
                    'type': code.type,
                    'points': points
                })
            
            return results
        except Exception as e:
            print(f"Error detecting QR codes: {e}")
            return []
    
    def start_capture(self) -> bool:
        """
        Start continuous frame capture.
        Returns:
            True if started successfully
        """
        if not self.is_initialized:
            raise RuntimeError("Camera not initialized")
        
        if self.is_capturing:
            return False
        
        self.is_capturing = True
        self.start_time = time.time()
        self.frame_count = 0
        return True
    
    def stop_capture(self) -> bool:
        """
        Stop continuous frame capture.
        Returns:
            True if stopped successfully
        """
        if not self.is_capturing:
            return True
        
        self.is_capturing = False
        return True
    
    def get_fps(self) -> float:
        """
        Get the current frames per second.
        Returns:
            Current FPS
        """
        if not self.is_capturing or self.frame_count == 0:
            return 0.0
        
        elapsed_time = time.time() - self.start_time
        if elapsed_time == 0:
            return 0.0
        
        return self.frame_count / elapsed_time 