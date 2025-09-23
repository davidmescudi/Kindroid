import asyncio
import os
from typing import Union, Literal
from loguru import logger
from pipecat_flows import FlowArgs, FlowConfig, FlowResult


class WayDescriptionResult(FlowResult):
    description: str


class QRCodeResult(FlowResult):
    status: str


class ErrorResult(FlowResult):
    status: Literal["error"]
    error: str


# Function handlers for the LLM
async def get_way_description(args: FlowArgs) -> Union[WayDescriptionResult, ErrorResult]:
    """
    Handler, der eine kinderfreundliche Wegbeschreibung gibt.
    Diese Funktion stellt sicher, dass der Hinweis auf die Belohnung bei jeder
    erfolgreichen Wegbeschreibung zuverlässig hinzugefügt wird.
    """
    destination = args.get("destination", "irgendwohin")
    logger.debug(f"Gebe eine Wegbeschreibung zum Ziel: {destination}")
    try:
        description = ""
        # Die Belohnungs-Nachricht, die immer angehängt wird
        reward_notice = " Und vergiss nicht, den QR-Code, den ich für dich drucke, meinem Affen-Bruder am Ziel zu zeigen. Dann bekommst du eine tolle Belohnung!"

        # Prüfe bekannte Ziele. Wenn eines passt, erstelle die Beschreibung UND hänge den Hinweis an.
        if "spielzimmer" in destination.lower():
            description = "Oh, zum Spielzimmer! Das ist ein super Ort! Laufe einfach diesen Gang entlang bis zur großen bunten Tür mit den vielen Tieren darauf. Da bist du richtig!" + reward_notice
        elif "röntgen" in destination.lower():
            description = "Zum Röntgen? Kein Problem! Folge einfach den blauen Fußspuren auf dem Boden. Sie führen dich direkt zur Tür mit dem Bild von einer Kamera." + reward_notice
        elif "cafeteria" in destination.lower() or "essen" in destination.lower():
            description = "Möchtest du zur Cafeteria? Lecker! Nimm den Aufzug mit dem Apfel-Symbol nach ganz unten. Wenn du aussteigst, kannst du das Essen schon riechen!" + reward_notice
        else:
            # Wenn kein bekanntes Ziel gefunden wurde, gib eine Standard-Antwort OHNE Belohnungs-Hinweis.
            description = f"Upsi, den Weg zu '{destination}' kenne ich leider nicht. Aber frag doch mal eine der netten Krankenschwestern, die können dir sicher helfen."
        
        return WayDescriptionResult(description=description)
    except Exception as e:
        logger.error(f"Fehler bei der Wegbeschreibung: {e}")
        return ErrorResult(status="error", error="Upsi, ich habe mich im Dschungel der Gänge verirrt und konnte den Weg nicht finden.")


async def scan_qr_code() -> Union[QRCodeResult, ErrorResult]:
    """Handler, der einen QR-Code scannt und eine lustige Rückmeldung gibt."""
    logger.debug("Simuliere einen QR-Code-Scan")
    try:
        return QRCodeResult(status="Super! Ich habe den Code erkannt. Jetzt kann das Abenteuer weitergehen!")
    except Exception as e:
        logger.error(f"Fehler beim Scannen des QR-Codes: {e}")
        return ErrorResult(status="error", error="Oh oh, meine Affen-Augen können den Code gerade nicht lesen.")


flow_config: FlowConfig = {
    "initial_node": "greeting",
    "nodes": {
        "greeting": {
            "role_messages": [
                {
                    "role": "system",
                    "content": "Du bist Koko, ein fröhlicher Roboter-Affe in einem Krankenhaus. Deine Aufgabe ist es, Kindern zu helfen und sie aufzuheitern. Sprich einfach und freundlich. Ganz wichtig: Deine Antworten werden direkt in Sprache umgewandelt. Deshalb darfst du auf gar keinen Fall Emojis, Smileys oder andere Sonderzeichen (wie *, #, etc.) verwenden. Deine Antwort muss immer reiner, einfacher Text sein, der vorgelesen werden kann. Nutze die verfügbaren Funktionen, um den Kindern zu helfen.",
                }
            ],
            "task_messages": [
                {
                    "role": "system",
                    "content": "Begrüße das Kind fröhlich als Koko, der Roboter-Affe. Frage es, ob du ihm den Weg zu einem tollen Ort im Krankenhaus zeigen oder einen geheimen QR-Code für es scannen sollst. Warte auf die Antwort, bevor du `get_way_description` oder `scan_qr_code` aufrufst.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_way_description",
                        "handler": get_way_description,
                        "description": "Gibt dem Kind eine einfache Wegbeschreibung zu einem Ort im Krankenhaus.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "destination": {"type": "string", "description": "Der Ort, zu dem das Kind möchte, z.B. 'Spielzimmer'"}
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
                        "description": "Scannt einen QR-Code für das Kind.",
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
                    "content": "Eine Funktion hat eine Antwort im 'tool'-Kontext geliefert. Deine Aufgabe ist es jetzt, eine Antwort für das Kind zu formulieren. Beginne, indem du den Inhalt des 'description'-Feldes aus dem 'tool'-Resultat **exakt und wortwörtlich wiedergibst, ohne jegliche Änderung oder Hinzufügung.** Frage direkt im Anschluss daran, ob das Kind noch etwas braucht ('Sollen wir noch ein Abenteuer erleben?') oder ob das Gespräch beendet werden soll. Verwende `end_conversation`, wenn das Kind fertig ist.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_way_description",
                        "handler": get_way_description,
                        "description": "Gibt dem Kind eine weitere Wegbeschreibung.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "destination": {"type": "string", "description": "Der neue Ort, zu dem das Kind möchte"}
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
                        "description": "Scannt einen weiteren QR-Code.",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "end_conversation",
                        "description": "Beendet das Gespräch, wenn das Kind keine weitere Hilfe braucht.",
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
                    "content": "Verabschiede dich auf eine lustige und herzliche Affen-Art vom Kind. Wünsche ihm noch ganz viel Spaß und einen schönen Tag.",
                }
            ],
            "functions": [],
            "post_actions": [{"type": "end_conversation"}],
        },
    },
}