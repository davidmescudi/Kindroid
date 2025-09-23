import asyncio
import os
from typing import Union, Literal, Optional
from loguru import logger
from pipecat_flows import FlowArgs, FlowConfig, FlowResult

from utils.printer import setup_printer, print_qr, feed_paper_lines, close_printer, print_text
from utils.camera import _scan_qr_code_sync

class WayDescriptionResult(FlowResult):
    description: str


class QRCodeResult(FlowResult):
    status: Literal["success", "not_found", "error"]
    data: Optional[str] = None


class ErrorResult(FlowResult):
    status: Literal["error"]
    error: str


# Function handlers for the LLM
async def get_way_description(args: FlowArgs) -> Union[WayDescriptionResult, ErrorResult]:
    """Handler for providing a way description."""
    destination = args.get("destination", "dem Haupteingang")
    logger.debug(f"Providing way description to {destination}")
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
        
        setup_printer()
        print_qr(f"Wegbeschreibung zu {destination}")
        print_text(description)
        close_printer()
        return WayDescriptionResult(description=description)
    except Exception as e:
        logger.error(f"Error getting way description: {e}")
        return ErrorResult(status="error", error="Wegbeschreibung konnte nicht abgerufen werden.")


async def scan_qr_code() -> Union[QRCodeResult, ErrorResult]:
    """Handler for a QR code scan."""
    logger.debug("Simulating QR code scan")
    try:
        loop = asyncio.get_running_loop()
        qr_data = await loop.run_in_executor(None, _scan_qr_code_sync)

        if qr_data:
            return QRCodeResult(status="success", data=qr_data)
        else:
            logger.warning("No QR code found during scan")
            return QRCodeResult(status="not_found")
    except Exception as e:
        logger.error(f"Error scanning QR code: {e}")
        return ErrorResult(status="error", error="QR-Code konnte nicht gescannt werden.")


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