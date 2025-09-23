import asyncio
from loguru import logger
from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
)
"""
OLD! NOT IN USE ANYMORE!
"""

class SpeakingStateManager:
    """
    Diese Klasse verwaltet den Sprechzustand des Benutzers und des Bots.
    Sie wird verwendet, um UserSpokeFrames zu filtern (zu verwerfen),
    während der Bot spricht, um ein "Barge-in" zu verhindern.
    """

    def __init__(self, debounce_seconds: float = 0.5):
        self.bot_speaking = False
        self.user_speaking = False
        self.user_interrupted = False
        self._debounce_seconds = debounce_seconds
        self._debounce_task = None
        logger.debug(f"Initialisiere SpeakingStateManager mit Debounce-Zeit: {self._debounce_seconds}s")

    async def _debounce_bot_stop(self):
        try:
            await asyncio.sleep(self._debounce_seconds)
            logger.debug(f"Debounce von {self._debounce_seconds}s beendet. Bot gilt jetzt als still.")
            self.bot_speaking = False
            self._debounce_task = None
        except asyncio.CancelledError:
            logger.debug("Debounce-Task für Bot-Stopp wurde abgebrochen.")

    async def filter_logic(self, frame: Frame) -> bool:
        """
        Führt die Filterlogik für den Sprechzustand aus.

        Gibt zurück:
            bool: True, um den Frame zu verwerfen, False, um ihn durchzulassen.
        """
        if isinstance(frame, InputAudioRawFrame):
            if self.user_interrupted:
                # Gib True zurück, um diesen Audio-Frame zu verwerfen.
                # Der STT-Service wird ihn nie erhalten.
                # Wir loggen dies nicht für jeden Frame, da es zu "spammy" wäre.
                return False
            return True
        
        if isinstance(frame, BotStartedSpeakingFrame):
            logger.debug("EVENT: BotStartedSpeakingFrame erkannt.")
            # Wenn der Bot anfängt zu sprechen, breche Debounce-Tasks ab
            if self._debounce_task:
                self._debounce_task.cancel()
                self._debounce_task = None
            self.bot_speaking = True
            return True
        
        if isinstance(frame, BotStoppedSpeakingFrame):
            logger.debug("EVENT: BotStoppedSpeakingFrame erkannt. Starte Debounce...")
            if self._debounce_task:
                self._debounce_task.cancel() # Abbrechen des alten Tasks, falls vorhanden
            self._debounce_task = asyncio.create_task(self._debounce_bot_stop())
            return True
        
        if isinstance(frame, UserStartedSpeakingFrame):
            logger.debug("EVENT: UserStartedSpeakingFrame erkannt.")
            self.user_speaking = True

            if self.bot_speaking:
                logger.debug("LOGIK: User hat Bot unterbrochen. Setze 'user_interrupted' Flag.")
                self.user_interrupted = True
                return False
            else:
                return True

        if isinstance(frame, UserStoppedSpeakingFrame):
            logger.debug("EVENT: UserStoppedSpeakingFrame erkannt.")
            self.user_speaking = False

            if self.bot_speaking or self.user_interrupted:
                logger.debug("LOGIK: User hatte Bot unterbrochen oder Bot spricht.")
                self.user_interrupted = False
                return False
            else:
                return True

        # Alle anderen Frame-Typen standardmäßig durchlassen
        return not self.bot_speaking
