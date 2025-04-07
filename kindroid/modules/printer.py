"""
Printer module for controlling a thermal printer.
"""
import serial
import time
import threading
import qrcode
from PIL import Image
import numpy as np
from typing import Optional, Dict, Any, List, Tuple

from ..core.base import HardwareModule


class PrinterModule(HardwareModule):
    """Printer module for controlling a thermal printer."""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.serial_port = None
        self.port = self.config.get('port', '/dev/ttyUSB0')  # Default port for USB serial
        self.baud_rate = self.config.get('baud_rate', 9600)  # Default baud rate
        self.timeout = self.config.get('timeout', 1.0)  # Serial timeout in seconds
        self.print_delay = self.config.get('print_delay', 0.1)  # Delay between print operations
        self.max_width = self.config.get('max_width', 32)  # Maximum characters per line
        self.is_printing = False
        self.print_queue = []
        self.print_thread = None
    
    def initialize(self) -> bool:
        """Initialize the printer."""
        try:
            # Open serial connection
            self.serial_port = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            
            # Test printer connection
            if self._test_connection():
                self.is_initialized = True
                return True
            return False
        except Exception as e:
            print(f"Failed to initialize printer: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown the printer."""
        self.stop_printing()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_initialized = False
        return True
    
    def get_status(self) -> dict:
        """Get printer status."""
        return {
            "initialized": self.is_initialized,
            "port": self.port,
            "baud_rate": self.baud_rate,
            "is_printing": self.is_printing,
            "queue_length": len(self.print_queue)
        }
    
    def _test_connection(self) -> bool:
        """
        Test the printer connection.
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Send a simple command to check if printer responds
            self._send_command(b'\x1B\x76\x00')  # Print test page command
            time.sleep(1)  # Wait for response
            return True
        except Exception as e:
            print(f"Printer connection test failed: {e}")
            return False
    
    def _send_command(self, command: bytes) -> None:
        """
        Send a command to the printer.
        Args:
            command: Command bytes to send
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        try:
            self.serial_port.write(command)
            self.serial_port.flush()
        except Exception as e:
            print(f"Error sending command to printer: {e}")
    
    def print_text(self, text: str, align: str = 'left', bold: bool = False, 
                  underline: bool = False, size: int = 1) -> bool:
        """
        Print text to the printer.
        Args:
            text: Text to print
            align: Text alignment ('left', 'center', 'right')
            bold: Whether to print in bold
            underline: Whether to underline the text
            size: Text size (1-8)
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        try:
            # Set text alignment
            if align == 'center':
                self._send_command(b'\x1B\x61\x01')  # Center alignment
            elif align == 'right':
                self._send_command(b'\x1B\x61\x02')  # Right alignment
            else:
                self._send_command(b'\x1B\x61\x00')  # Left alignment
            
            # Set text style
            style = 0
            if bold:
                style |= 0x01  # Bold
            if underline:
                style |= 0x80  # Underline
            self._send_command(bytes([0x1B, 0x45, style]))
            
            # Set text size
            if 1 <= size <= 8:
                self._send_command(bytes([0x1D, 0x21, size - 1]))
            
            # Print the text
            self._send_command(text.encode('utf-8'))
            
            # Add a line feed
            self._send_command(b'\n')
            
            # Reset text style
            self._send_command(b'\x1B\x45\x00')
            
            # Reset text size
            self._send_command(b'\x1D\x21\x00')
            
            # Reset alignment
            self._send_command(b'\x1B\x61\x00')
            
            # Add a small delay
            time.sleep(self.print_delay)
            
            return True
        except Exception as e:
            print(f"Error printing text: {e}")
            return False
    
    def print_image(self, image_path: str, width: Optional[int] = None) -> bool:
        """
        Print an image from a file.
        Args:
            image_path: Path to the image file
            width: Desired width in pixels (will maintain aspect ratio)
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        try:
            # Open and resize image
            img = Image.open(image_path)
            
            # Convert to grayscale
            img = img.convert('L')
            
            # Resize if width is specified
            if width:
                aspect_ratio = img.height / img.width
                height = int(width * aspect_ratio)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Convert to printer format (1-bit black and white)
            img_array = (img_array < 128).astype(np.uint8)
            
            # Print image
            self._print_bitmap(img_array)
            
            return True
        except Exception as e:
            print(f"Error printing image: {e}")
            return False
    
    def _print_bitmap(self, bitmap: np.ndarray) -> None:
        """
        Print a bitmap image to the printer.
        Args:
            bitmap: 2D numpy array of 0s and 1s representing the image
        """
        # Get image dimensions
        height, width = bitmap.shape
        
        # Calculate number of bytes needed per line
        bytes_per_line = (width + 7) // 8
        
        # Send bitmap print command
        self._send_command(b'\x1D\x76\x30\x00')  # Print bitmap command
        self._send_command(bytes([width & 0xFF, (width >> 8) & 0xFF]))  # Width
        self._send_command(bytes([height & 0xFF, (height >> 8) & 0xFF]))  # Height
        
        # Convert bitmap to bytes and send
        for y in range(height):
            line_bytes = bytearray()
            for x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < width:
                        byte |= bitmap[y, x + bit] << (7 - bit)
                line_bytes.append(byte)
            self._send_command(bytes(line_bytes))
            time.sleep(self.print_delay)
    
    def print_qr_code(self, data: str, size: int = 3, error_correction: int = 2) -> bool:
        """
        Generate and print a QR code.
        Args:
            data: Data to encode in the QR code
            size: Size of the QR code (1-8)
            error_correction: Error correction level (0-3)
                0: 7% error correction
                1: 15% error correction
                2: 25% error correction
                3: 30% error correction
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_correction,
                box_size=size,
                border=2
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to numpy array
            qr_array = np.array(qr_image)
            
            # Print QR code
            self._print_bitmap(qr_array)
            
            # Print the data below the QR code
            self.feed_paper(1)
            self.print_text(data, align='center', size=1)
            
            return True
        except Exception as e:
            print(f"Error printing QR code: {e}")
            return False
    
    def print_barcode(self, data: str, barcode_type: str = 'CODE39') -> bool:
        """
        Print a barcode.
        Args:
            data: Barcode data
            barcode_type: Type of barcode (CODE39, UPC, EAN, etc.)
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        try:
            # This is a placeholder for barcode printing functionality
            # You would need to implement printer-specific commands for your model
            print(f"Barcode printing not yet implemented for {barcode_type}: {data}")
            return False
        except Exception as e:
            print(f"Error printing barcode: {e}")
            return False
    
    def feed_paper(self, lines: int = 3) -> bool:
        """
        Feed paper by a specified number of lines.
        Args:
            lines: Number of lines to feed
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        try:
            for _ in range(lines):
                self._send_command(b'\n')
                time.sleep(self.print_delay)
            return True
        except Exception as e:
            print(f"Error feeding paper: {e}")
            return False
    
    def cut_paper(self) -> bool:
        """
        Cut the paper.
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        try:
            self._send_command(b'\x1D\x56\x41\x00')  # Full cut
            return True
        except Exception as e:
            print(f"Error cutting paper: {e}")
            return False
    
    def start_printing(self) -> bool:
        """
        Start the printing thread for queued prints.
        Returns:
            True if started successfully
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        if self.is_printing:
            print("Already printing")
            return False
        
        self.is_printing = True
        self.print_thread = threading.Thread(target=self._printing_loop, daemon=True)
        self.print_thread.start()
        return True
    
    def stop_printing(self) -> bool:
        """
        Stop the printing thread.
        Returns:
            True if stopped successfully
        """
        if not self.is_printing:
            return True
        
        self.is_printing = False
        if self.print_thread:
            self.print_thread.join(timeout=1.0)
            self.print_thread = None
        return True
    
    def _printing_loop(self) -> None:
        """Background thread that processes the print queue."""
        while self.is_printing:
            if self.print_queue:
                print_job = self.print_queue.pop(0)
                if print_job['type'] == 'text':
                    self.print_text(
                        print_job['text'],
                        print_job.get('align', 'left'),
                        print_job.get('bold', False),
                        print_job.get('underline', False),
                        print_job.get('size', 1)
                    )
                elif print_job['type'] == 'image':
                    self.print_image(
                        print_job['path'],
                        print_job.get('width')
                    )
                elif print_job['type'] == 'qr_code':
                    self.print_qr_code(
                        print_job['data'],
                        print_job.get('size', 3),
                        print_job.get('error_correction', 2)
                    )
                elif print_job['type'] == 'barcode':
                    self.print_barcode(
                        print_job['data'],
                        print_job.get('barcode_type', 'CODE39')
                    )
                elif print_job['type'] == 'feed':
                    self.feed_paper(print_job.get('lines', 3))
                elif print_job['type'] == 'cut':
                    self.cut_paper()
            else:
                time.sleep(0.1)  # Sleep to prevent CPU hogging
    
    def queue_print(self, print_type: str, **kwargs) -> bool:
        """
        Add a print job to the queue.
        Args:
            print_type: Type of print job ('text', 'image', 'barcode', 'feed', 'cut')
            **kwargs: Additional arguments for the print job
        Returns:
            True if queued successfully
        """
        if not self.is_initialized:
            raise RuntimeError("Printer not initialized")
        
        try:
            print_job = {'type': print_type, **kwargs}
            self.print_queue.append(print_job)
            return True
        except Exception as e:
            print(f"Error queuing print job: {e}")
            return False 