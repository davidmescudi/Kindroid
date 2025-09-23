from picamera2 import Picamera2, Preview
from pyzbar.pyzbar import decode
import time
import libcamera
from typing import Union, Literal, Optional
from loguru import logger

# NEU: Helper-Funktion für den synchronen Kameracode
def _scan_qr_code_sync(timeout: int = 30) -> Optional[str]:
    """
    Initialisiert die Kamera, sucht nach QR-Codes und gibt den Inhalt des ersten
    gefundenen Codes zurück oder None nach einem Timeout.
    Diese Funktion ist synchron und sollte in einem Thread ausgeführt werden.
    """
    picam2 = None
    try:
        logger.debug("Initialisiere Kamera...")
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"size": (640, 480)},
            transform=libcamera.Transform(hflip=0, vflip=0)
        )
        picam2.configure(config)

        # Die Vorschau ist für einen Agenten meist nicht nötig und kann
        # zu Problemen führen, wenn keine GUI läuft.
        #picam2.start_preview(Preview.QTGL) 
        
        picam2.start()
        logger.info("Kamera gestartet. Suche nach QR-Codes...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            buffer = picam2.capture_array()
            decoded_objects = decode(buffer)

            if decoded_objects:
                # Nimm den ersten gefundenen Code
                qr_data = decoded_objects[0].data.decode('utf-8')
                logger.info(f"QR-Code gefunden! Inhalt: {qr_data}")
                return qr_data # Wichtig: Daten zurückgeben

            time.sleep(0.5) # Kurze Pause

        logger.warning(f"Kein QR-Code innerhalb von {timeout} Sekunden gefunden.")
        return None

    except Exception as e:
        logger.error(f"Ein Fehler ist bei der Kameranutzung aufgetreten: {e}")
        # Mögliche Fehler: Kamera wird bereits verwendet, oder ist nicht angeschlossen.
        return None
    finally:
        if picam2:
            if picam2.is_open:
                picam2.stop()
                logger.info("Kamera gestoppt.")
            picam2.close()
            logger.info("Kamera geschlossen.")
