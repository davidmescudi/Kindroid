import asyncio
import os
from typing import Union, Literal, Optional
import httpx
from loguru import logger
from pipecat_flows import FlowArgs, FlowConfig, FlowResult
import json

from utils.printer import setup_printer, print_qr, feed_paper_lines, close_printer, print_text, print_ice_cream
from utils.camera import _scan_qr_code_sync
from utils.config_loader import AppConfig

from animation.monkey_eyes_lib import EyesController

class WayDescriptionResult(FlowResult):
    description: str


class QRCodeResult(FlowResult):
    status: Literal["success", "not_found", "error"]
    data: Optional[str] = None


class ErrorResult(FlowResult):
    status: Literal["error"]
    error: str

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "agent_config.yaml")
app_config = AppConfig.load_from_yaml(config_path)

def create_flow_config(journey_id: int, eyes_controller: EyesController, test: bool) -> FlowConfig:
    # Function handlers for the LLM
    async def get_way_description(args: FlowArgs) -> Union[WayDescriptionResult, ErrorResult]:
        """Handler for providing a way description."""
        destination = args.get("destination", "dem Haupteingang")
        logger.debug(f"Providing way description to {destination}")
        
        try:
            async with httpx.AsyncClient() as client:
                if test:
                    locations = [{"id": 1, "name": "Haupteingang"}, {"id": 2, "name": "Optometrist"}, {"id": 3, "name": "Radiologie"}, {"id": 4, "name": "Notaufnahme"}, {"id": 149, "name": "Oncology"}]
                else:
                    locations_response = await client.get(app_config.apis["base_url"] + app_config.apis["locations_url"])
                    locations = locations_response.json()
                logger.debug(f"Received locations: {locations}")

                target_location = None
                for location in locations:
                    if location["name"].lower() == destination.lower():
                        target_location = location
                        break

            description = ""
            if target_location:
                async with httpx.AsyncClient() as client:
                    location_id = target_location["id"]
                    if test:
                        description_data = {
                            "routeDescription": f"Dies ist eine Testbeschreibung für {target_location['name']}.",
                            "qrCode": {                            
                                "token": "205299c9467fcd596f3d629f99364602",
                                "destinationId": location_id,
                                "journeyId": journey_id
                            }
                        }
                    else:
                        post_data = {
                            "destinationLocationId": location_id,
                            "journeyId": journey_id
                        }
                        description_response = await client.post(
                            app_config.apis["base_url"] + app_config.apis["directions_url"], 
                            json=post_data)
                        description_data = description_response.json()
                    
                    description = description_data.get("routeDescription", "Keine Wegbeschreibung gefunden.")
                    qr_code_data = description_data.get("qrCode", None)
            else:
                description = f"Leider konnte ich keinen Ort namens '{destination}' finden. Bitte versuchen Sie es mit einem der folgenden Orte: " + ", ".join([loc['name'] for loc in locations]) + "."

            eyes_controller.trigger_smile(2000)  
            setup_printer()
            print_qr(json.dumps(qr_code_data))
            print_text(description)
            feed_paper_lines(15)
            close_printer()
            return WayDescriptionResult(description=description)
        except httpx.RequestError as e:
            logger.error(f"Error making API request: {e}")
            return ErrorResult(status="error", error="Wegbeschreibungsinformationen konnten nicht vom Server abgerufen werden.")
        except Exception as e:
            logger.error(f"Error getting way description: {e}")
            return ErrorResult(status="error", error="Wegbeschreibung konnte nicht abgerufen werden.")


    async def scan_qr_code() -> Union[QRCodeResult, ErrorResult]:
        """Handler for a QR code scan."""
        logger.debug("Simulating QR code scan")
        try:
            loop = asyncio.get_running_loop()
            if test:
                qr_data = {"token": "205299c9467fcd596f3d629f99364602", "destinationId": 2, "journeyId": journey_id}
            else:
                #TODO: Evlt. hier das preview der Kamera anzeigen lassen? Damit user sieht ob er den QR-Code richtig hält
                eyes_controller.trigger_loading()
                qr_data = await loop.run_in_executor(None, _scan_qr_code_sync) #{"token": "205299c9467fcd596f3d629f99364602", "destinationId": 2, "journeyId": journey_id}
                eyes_controller.stop_loading()
            #qr_data = {'token': 'df35d46f3dc0322e20eab30698f7ad30', 'destinationId': 3, 'journeyId': 17}
            if qr_data:
                async with httpx.AsyncClient() as client:
                    try:
                        if test:
                            qr_data = qr_data
                        else:
                            if isinstance(qr_data, str):
                                qr_data = json.loads(qr_data)
                            else:
                                qr_data = qr_data
                            
                            if isinstance(qr_data, str):
                                qr_data = json.loads(qr_data)
                            
                            qr_data = await client.post(app_config.apis["base_url"] + app_config.apis["qr_code_process_url"], json=qr_data)
                            qr_data = qr_data.json()
                    except httpx.RequestError as e:
                        logger.error(f"Error making API request: {e}")
                        return ErrorResult(status="error", error="QR-Code konnte nicht an den Server gesendet werden.")
                    
                    eyes_controller.trigger_star(2000)
                    #TODO: Print the banana ASCI art
                    setup_printer()
                    print_ice_cream()
                    feed_paper_lines(15)
                    close_printer()
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
                        "content": "Du bist Koko, ein fröhlicher Roboter-Affe in einem Gebäude. Deine Aufgabe ist es, Menschen zu helfen und sie aufzuheitern. Sprich einfach und freundlich. Ganz wichtig: Deine Antworten werden direkt in Sprache umgewandelt. Deshalb darfst du auf gar keinen Fall Emojis, Smileys oder andere Sonderzeichen (wie *, #, etc.) verwenden. Deine Antwort muss immer reiner, einfacher Text sein, der vorgelesen werden kann. Nutze die verfügbaren Funktionen, um dem Mensch zu helfen.",
                    }
                ],
                "task_messages": [
                    {
                        "role": "system",
                        "content": "Begrüße den Mensch fröhlich als Koko, der Roboter-Affe. Frage es, ob du ihm den Weg zu einem tollen Ort im Gebäude zeigen oder einen geheimen QR-Code für es scannen sollst. Warte auf die Antwort, bevor du `get_way_description` oder `scan_qr_code` aufrufst.",
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
                    {
                        "type": "function",
                        "function": {
                            "name": "end_conversation",
                            "description": "Beendet das Gespräch, wenn der Benutzer keine Hilfe benötigt oder sich verabschiedet.",
                            "parameters": {"type": "object", "properties": {}},
                            "transition_to": "end",
                        },
                    },
                ],
            },
            "handle_choice": {
                "task_messages": [
                    {
                        "role": "system",
                        "content": "Eine Funktion hat eine Antwort im 'tool'-Kontext geliefert. Deine Aufgabe ist es jetzt, eine Antwort für den Benutzer zu formulieren. Beginne, indem du den Inhalt des 'description'-Feldes aus dem 'tool'-Resultat **exakt und wortwörtlich wiedergibst, ohne jegliche Änderung oder Hinzufügung.** Frage direkt im Anschluss daran, ob der Benutzer noch etwas braucht oder ob das Gespräch beendet werden soll. Verwende `end_conversation`, wenn der Benutzer fertig ist.",
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
                        "content": "Verabschiede dich auf eine lustige und herzliche Affen-Art vom Benutzer. Wünsche ihm noch ganz viel Spaß und einen schönen Tag.",
                    }
                ],
                "functions": [],
                "post_actions": [{"type": "end_conversation"}],
            },
        },
    }
    return flow_config