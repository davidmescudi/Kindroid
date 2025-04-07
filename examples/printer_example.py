"""
Example script demonstrating the printer module usage.
"""
import time
from kindroid.modules.printer import PrinterModule

def main():
    # Initialize printer with default settings
    printer = PrinterModule()
    
    # Initialize the printer
    if not printer.initialize():
        print("Failed to initialize printer")
        return
    
    try:
        # Print some text with different styles
        printer.print_text("Hello, World!", align='center', bold=True, size=2)
        printer.feed_paper(1)
        
        printer.print_text("This is a test of the thermal printer.", align='left')
        printer.feed_paper(1)
        
        # Print a QR code
        printer.print_qr_code("https://github.com/davidmescudi/Kindroid", size=3)
        printer.feed_paper(2)
        
        # Print a barcode
        printer.print_barcode("123456789", barcode_type="CODE39")
        printer.feed_paper(2)
        
        # Queue multiple print jobs
        printer.queue_print('text', text="Queued print job 1", align='center')
        printer.queue_print('qr_code', data="https://example.com", size=2)
        printer.queue_print('text', text="Queued print job 2", bold=True)
        printer.queue_print('feed', lines=2)
        printer.queue_print('cut')
        
        # Start the printing thread to process queued jobs
        printer.start_printing()
        
        # Wait for printing to complete
        time.sleep(5)
        
        # Stop printing
        printer.stop_printing()
        
    finally:
        # Cleanup
        printer.shutdown()

if __name__ == "__main__":
    main() 