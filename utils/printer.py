import serial
import time
import json
import textwrap

my_serial = None # Global variable for the serial object

def feed_paper_lines(lines: int):
    """
    Vorschub des Papiers um eine bestimmte Anzahl von Zeilen.
    """
    if not my_serial or not my_serial.is_open:
        print("Serielle Verbindung nicht initialisiert für Papierausgabe.")
        return
    if not (0 <= lines <= 255):
        print(f"Warnung: Ungültige Zeilenanzahl für Papierausgabe: {lines}. Muss zwischen 0 und 255 liegen.")
        return

    try:
        # ESC d n command
        command = bytes([0x1B, 0x64, lines])
        my_serial.write(command)
        print(f"Papier um {lines} Zeilen vorgeschoben.")
    except Exception as e:
        print(f"Fehler beim Vorschub des Papiers: {e}")

def generate_custom_qr_code_data(content: str, module_size: int = 10) -> bytes:
    """
    Generates the byte sequence for printing a QR code using ESC/POS commands
    based on the DFRobot documentation.
    """
    qr_content_bytes = content.encode('ascii') # Ensure content is ASCII or printer-compatible
    k = len(qr_content_bytes)

    # pL + pH*256 = number of data bytes (k) + 3 (for storing QR data command)
    data_len_param = k + 3
    pL = data_len_param % 256
    pH = data_len_param // 256

    qr_commands = []

    # 1. Initialize Printer (ESC @) - Often good practice even if mode is set
    qr_commands.extend([0x1B, 0x40])

    # 2. Set QR Code Size/Module (GS ( k ... cn=49, fn=67)
    # Module size n (1-16, example uses 0x05)
    if not (1 <= module_size <= 16):
        print(f"Warnung: Ungültige Modulgröße {module_size}. Verwende Standardgröße 5.")
        module_size_byte = 0x05
    else:
        module_size_byte = module_size

    #qr_commands.extend([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x43, 0x05]) # Size 5
    qr_commands.extend([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x43, module_size_byte])

    # 3. Set QR Code Error Correction Level (GS ( k ... cn=49, fn=69)
    # n: 48='L'(7%), 49='M'(15%), 50='Q'(25%), 51='H'(30%). Example uses 0x30 (ASCII '0' for Level L).
    qr_commands.extend([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x45, 0x30]) # Error Level L

    # 4. Store QR Code Data in Symbol Storage (GS ( k ... cn=49, fn=80)
    qr_commands.extend([0x1D, 0x28, 0x6B, pL, pH, 0x31, 0x50, 0x30])
    qr_commands.extend(list(qr_content_bytes)) # Add the actual content

    # 5. Center the QR Code (ESC a n) (Optional)
    qr_commands.extend([0x1B, 0x61, 0x01]) # Center alignment

    # 6. Print QR Code from Symbol Storage (GS ( k ... cn=49, fn=81)
    # m = 48 (default). Example uses 0x30 (ASCII '0').
    qr_commands.extend([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x51, 0x30])

    # 7. "Verify" / Transmit data command (GS ( k ... cn=49, fn=82) (from DFRobot docs example)
    # Kept for consistency with DFRobot examples, may not be strictly necessary for all printers.
    qr_commands.extend([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x52, 0x30])

    return bytes(qr_commands)

def setup_printer(SERIAL_PORT_MYSERIAL: str = '/dev/ttyAMA0', BAUDRATE_MYSERIAL: int = 115200):
    global my_serial
    # Command for "ReceiptMode" from your working script
    Com_receipt_mode = bytes([0x1F, 0x2F, 0x0B, 0x00, 0x01, 0x00, 0x00])

    # Command for "Label verification" from your working script
    Com1_label_verification = bytes([0x1F, 0x63])

    try:
        my_serial = serial.Serial(SERIAL_PORT_MYSERIAL, BAUDRATE_MYSERIAL, timeout=1)
        print(f"Serielle Schnittstelle {SERIAL_PORT_MYSERIAL} mit {BAUDRATE_MYSERIAL} Baud geöffnet.")
    except serial.SerialException as e:
        print(f"Fehler beim Öffnen der seriellen Schnittstelle {SERIAL_PORT_MYSERIAL}: {e}")
        exit()

    # Send your working initialization commands
    my_serial.write(Com_receipt_mode)
    print(f"Com_receipt_mode gesendet: {Com_receipt_mode.hex()}")
    time.sleep(0.2) # Short delay after mode set

    my_serial.write(Com1_label_verification)
    print(f"Com1_label_verification gesendet: {Com1_label_verification.hex()}")
    time.sleep(0.2) # Short delay

    # It's good practice to ensure the printer is in a known state.
    # The generate_custom_qr_code_data function includes an ESC @ (initialize)
    # which should be fine.
    # Alternatively, send one initialize command here:
    # my_serial.write(bytes([0x1B, 0x40])) # ESC @ Initialize printer
    # time.sleep(0.1)

    print("Setup abgeschlossen.")

def print_text(text_to_print: str):
    if not my_serial or not my_serial.is_open:
        print("Serielle Verbindung nicht initialisiert für Textdruck.")
        return
    try:
        my_serial.write(text_to_print.encode('cp437'))
        print(f"Text gesendet: {text_to_print.strip()}")
    except Exception as e:
        print(f"Fehler beim Senden von Text: {e}")

def print_qr(content_for_qr: str):
    if not my_serial or not my_serial.is_open:
        print("Serielle Verbindung nicht initialisiert für QR-Druck.")
        return
    try:
        qr_payload = generate_custom_qr_code_data(content_for_qr)
        print(f"Sende QR-Code für: '{content_for_qr}' ({len(qr_payload)} Bytes): {qr_payload.hex().upper()}")
        my_serial.write(qr_payload)
        # Add some line feeds for spacing after the QR code
        my_serial.write(b'\n\n\n')
        print("QR-Code-Daten gesendet.")
    except Exception as e:
        print(f"Fehler beim Senden des QR-Codes: {e}")

def print_ice_cream():
    """
    Druckt eine vordefinierte ASCII-Art von Eis auf den Thermodrucker.
    """
    if not my_serial or not my_serial.is_open:
        print("Serielle Verbindung nicht initialisiert für den Eis-Druck.")
        return

    ice_cream_art = r'''
Ziel erfolgreich gefunden.
Kleine Belohnung und Abkuehlung:
        _.-.
      ,'/ //\
     /// // /)
    /// // //|
   /// // ///
  /// // ///
  (`: // ///
   `;`: ///
   / /:`:/
  / /  `'
 / /
(_/
    '''
    
    try:
        # Set alignment to left to preserve ASCII art formatting
        align_left_command = bytes([0x1B, 0x61, 0x00])
        my_serial.write(align_left_command)

        # This acts as a "kick" to ensure the printer is ready for the first line of art.
        my_serial.write(b' \n')

        # Clean the art string before printing.
        # This removes the indentation from the code block itself.
        processed_art = textwrap.dedent(ice_cream_art).strip()

        # Print each line of the art
        for line in processed_art.split('\n'):
            line_to_print = line + '\n' # Add a newline character to each line
            my_serial.write(line_to_print.encode('cp437'))

    except Exception as e:
        print(f"Fehler beim Drucken des Eises: {e}")

def close_printer():
    if my_serial and my_serial.is_open:
        my_serial.close()
        print("Serielle Schnittstelle geschlossen.")
