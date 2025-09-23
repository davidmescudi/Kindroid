import asyncio
import os
from typing import Union, Literal
from loguru import logger
from pipecat_flows import FlowArgs, FlowConfig, FlowResult

from picamera2 import Picamera2, Preview
from pyzbar.pyzbar import decode
import time
import libcamera


class WayDescriptionResult(FlowResult):
    description: str


class QRCodeResult(FlowResult):
    status: str
    data: str


class ErrorResult(FlowResult):
    status: Literal["error"]
    error: str


# Function handlers for the LLM
async def get_way_description(args: FlowArgs) -> Union[WayDescriptionResult, ErrorResult]:
    """Handler for providing a way description."""
    destination = args.get("destination", "dem Haupteingang")
    logger.debug(f"Providing way description to {destination}")
    #TODO: Anbindung an Backend, und anbindung von Drucker (Frage soll gefragt werden, ob QR Code gedruckt werden soll oder soll einfach immer gedruckt werden?)
    try:
        description = ""
        if "david" in destination.lower():
            description = "David arbeitet nicht hier er ist ein normaler Student deshalb kann ich dir auch keine Wegbeschreibung zu ihm geben."
        elif "philip" in destination.lower():
            description = "Philips Platz ist gleich hier nimm einfach den Fahrstuhl in den vierten Stock. Im vierten Stock findest du ihn meistens in Raum 455."
        elif "vladi" in destination.lower() or "boris" in destination.lower():
            description = f"{destination}s findest du im dritten Stock in der Werkstatt. Nimm einfach den Fahrstuhl in den dritten Stock und direkt rechts vom Fahrstuhl ist die Werkstatt."
        else:
            description = f"Um zu '{destination}' zu gelangen, gehe geradeaus den Flur entlang, nimm die erste links, und du wirst es direkt vor dir sehen."
        
        return WayDescriptionResult(description=description)
    except Exception as e:
        logger.error(f"Error getting way description: {e}")
        return ErrorResult(status="error", error="Wegbeschreibung konnte nicht abgerufen werden.")


async def scan_qr_code() -> Union[QRCodeResult, ErrorResult]:
    """
    Initializes the camera, scans for a QR code within a set timeout,
    and returns the content or an error.
    """
    logger.debug("Initializing camera for QR code scan...")
    picam2 = Picamera2()
    
    try:
        # Configure the camera for QR code detection
        config = picam2.create_preview_configuration(
            main={"size": (640, 480)},
            transform=libcamera.Transform(hflip=0, vflip=0)
        )
        picam2.configure(config)
        picam2.start()
        logger.info("Camera started. Searching for QR code...")

        scan_timeout = 10  # seconds
        start_time = time.time()

        while time.time() - start_time < scan_timeout:
            # Capture an image from the camera
            buffer = picam2.capture_array()

            # Decode QR codes from the image
            decoded_objects = decode(buffer)

            if decoded_objects:
                qr_data = decoded_objects[0].data.decode('utf-8')
                logger.info(f"QR Code found! Content: {qr_data}")
                #TODO: Anbindung an Backend
                return QRCodeResult(status="success", data=qr_data)
            
            # Briefly pause to allow other async tasks to run
            await asyncio.sleep(0.5)

        logger.warning(f"No QR code found within the {scan_timeout}-second timeout.")
        return ErrorResult(status="error", error="QR code scan timed out.")

    except Exception as e:
        logger.error(f"An error occurred during QR code scanning: {e}")
        return ErrorResult(status="error", error="A critical error occurred while scanning.")
        
    finally:
        # Ensure camera resources are always released
        if picam2.is_open:
            picam2.stop()
            logger.info("Camera stopped.")

flow_config: FlowConfig = {
    "initial_node": "greeting",
    "nodes": {
        "greeting": {
            "role_messages": [
                {
                    "role": "system",
                    "content": "Du bist ein hilfreicher Assistent. Deine Antworten werden in Audio umgewandelt, also vermeide bitte Sonderzeichen. Nutze die verfügbaren Funktionen, um dem Benutzer zu helfen.",
                }
            ],
            "task_messages": [
                {
                    "role": "system",
                    "content": "Begrüße den Benutzer und frage ihn, ob er eine Wegbeschreibung benötigt oder einen QR-Code scannen möchte. Warte auf seine Entscheidung, bevor du entweder `get_way_description` oder `scan_qr_code` verwendest.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_way_description",
                        "handler": get_way_description,
                        "description": "Erhält eine Wegbeschreibung zu einem Ziel.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "destination": {"type": "string", "description": "Das gewünschte Ziel"}
                            },
                            "required": ["destination"],
                        },
                        "transition_to": "handle_choice",
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "scan_qr_code",
                        "handler": scan_qr_code,
                        "description": "Scannt einen QR-Code.",
                        "parameters": {"type": "object", "properties": {}},
                        "transition_to": "handle_choice",
                    },
                },
            ],
        },
        "handle_choice": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "Der Benutzer hat eine Wahl getroffen. Frage ihn nach der Bereitstellung der Information, ob er noch etwas benötigt oder das Gespräch beenden möchte. Verwende `end_conversation`, wenn er fertig ist.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_way_description",
                        "handler": get_way_description,
                        "description": "Erhält eine Wegbeschreibung zu einem Ziel.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "destination": {"type": "string", "description": "Das gewünschte Ziel"}
                            },
                            "required": ["destination"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "scan_qr_code",
                        "handler": scan_qr_code,
                        "description": "Scannt einen QR-Code.",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "end_conversation",
                        "description": "Beendet das Gespräch.",
                        "parameters": {"type": "object", "properties": {}},
                        "transition_to": "end",
                    },
                },
            ],
        },
        "end": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "Bedanke dich beim Benutzer und verabschiede dich.",
                }
            ],
            "functions": [],
            "post_actions": [{"type": "end_conversation"}],
        },
    },
}