import asyncio
from loguru import logger

from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    StartFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    STTMuteFrame,
    InputAudioRawFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    StartInterruptionFrame,
    FunctionCallInProgressFrame,
    FunctionCallResultFrame
)

from animation.monkey_eyes_lib import EyesController

class DebouncedSTTMuteFilter(FrameProcessor):
    """
    A custom FrameProcessor that mutes STT when the bot is speaking and for a
    configurable debounce period after the bot stops speaking.

    Args:
        debounce_seconds: The time in seconds to wait after the bot stops
                          speaking before unmuting STT.
    """

    def __init__(self, eyes_controller: EyesController, debounce_seconds: float = 0.5, **kwargs):
        super().__init__(**kwargs)
        self.debounce_seconds = debounce_seconds
        self._is_muted = False
        self._bot_is_speaking = False
        self._debounce_task = None
        self._user_interrupted = False
        self._function_call_in_progress = False
        self._first_bot_speech_complete_handled = False
        self._eyes_controller = eyes_controller
        logger.info(f"DebouncedSTTMuteFilter initialisiert mit {debounce_seconds}s Debounce.")

    async def _set_mute_state(self, mute: bool):
        """Atomically sets the mute state and pushes the STTMuteFrame if the state changes."""
        if self._is_muted != mute:
            self._is_muted = mute
            logger.debug(f"Aktion: STT wird {'stummgeschaltet' if mute else 'aktiviert'}.")
            await self.push_frame(STTMuteFrame(mute=self._is_muted))

    async def _start_unmute_debounce(self):
        """Coroutine that waits for the debounce period and then unmutes."""
        try:
            await asyncio.sleep(self.debounce_seconds)
            logger.debug(f"Logik: Debounce-Zeit abgelaufen. Setze alle Zustände zurück und aktiviere STT.")
            # Reset everything to a clean state.
            self._bot_is_speaking = False
            self._user_interrupted = False
            self._debounce_task = None
            self._eyes_controller.stop_not_listening()
            await self._set_mute_state(False)
        except asyncio.CancelledError:
            logger.debug("Logik: Debounce zum Aktivieren wurde abgebrochen (Bot spricht wieder).")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Processes frames to manage STT mute state and suppresses frames when muted."""

        await super().process_frame(frame, direction)

        if self._is_muted:
            self._eyes_controller.start_not_listening()

        if isinstance(frame, StartFrame):
            if not self._first_bot_speech_complete_handled:
                logger.info("Start des Gesprächs: STT wird initial stummgeschaltet, bis der Bot geantwortet hat.")
                await self._set_mute_state(True)
            # Frame trotzdem weiterleiten
            await self.push_frame(frame, direction)
            return
    
        if isinstance(frame, BotStartedSpeakingFrame):
            self._bot_is_speaking = True
            logger.debug("EVENT: BotStartedSpeakingFrame. Schalte STT stumm.")
            if self._debounce_task:
                self._debounce_task.cancel()
                self._debounce_task = None
            await self._set_mute_state(True)
            return

        elif isinstance(frame, BotStoppedSpeakingFrame):
            if not self._first_bot_speech_complete_handled:
                logger.info("Erste Bot-Antwort empfangen. STT wird aktiviert.")
                self._first_bot_speech_complete_handled = True
            
            self._bot_is_speaking = False
            logger.debug(f"EVENT: BotStoppedSpeakingFrame. Starte Debounce zum Zurücksetzen und Aktivieren.")
            if self._debounce_task:
                self._debounce_task.cancel()
            self._debounce_task = asyncio.create_task(self._start_unmute_debounce())
            return
        
        elif isinstance(frame, FunctionCallInProgressFrame):
            self._function_call_in_progress = True
            logger.debug("EVENT: FunctionCallInProgressFrame. Schalte STT stumm.")
            if self._debounce_task:
                self._debounce_task.cancel()
                self._debounce_task = None
            await self._set_mute_state(True)
            return
        
        elif isinstance(frame, FunctionCallResultFrame):
            self._function_call_in_progress = False
            logger.debug("EVENT: FunctionCallResultFrame. Starte Debounce zum Zurücksetzen und Aktivieren.")
            if not self._bot_is_speaking and not self._function_call_in_progress:
                await self._set_mute_state(False)
            return
        
        elif isinstance(frame, UserStartedSpeakingFrame):
            if self._is_muted:
                logger.debug("LOGIK: User hat während der Stummschaltung zu sprechen begonnen. Unterbrechung markiert.")
                self._user_interrupted = True
            else:
                self._eyes_controller.trigger_listening()

        elif isinstance(frame, UserStoppedSpeakingFrame):
            if self._user_interrupted:
                logger.debug("LOGIK: Ende einer markierten Unterbrechung. Flag wird zurückgesetzt.")
                self._user_interrupted = False
                # The UserStoppedSpeakingFrame should still be suppressed.
                return
            elif not self._is_muted:
                self._eyes_controller.stop_listening()

        # 2. Frames filtern/unterdrücken basierend auf dem Mute-Status
        frames_to_suppress = (
            InputAudioRawFrame,
            TranscriptionFrame,
            InterimTranscriptionFrame,
            UserStartedSpeakingFrame,
            UserStoppedSpeakingFrame,
            StartInterruptionFrame,
        )

        if isinstance(frame, frames_to_suppress):
            if self._is_muted or self._user_interrupted:
                logger.trace(f"Unterdrückt: {type(frame).__name__} (mute: {self._is_muted}, interrupted: {self._user_interrupted})")
                return

        # 3. Alle anderen Frames (oder nicht unterdrückte Frames) normal weiterleiten
        await self.push_frame(frame, direction)

