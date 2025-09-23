"""A simpler example where the agent can either get a way description or scan a QR code."""

import asyncio
import os
import sys
from typing import Literal, Union
import httpx

# Fix audio cracks
from pipecat.frames.frames import StartFrame
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams, LocalAudioOutputTransport

original_local_audio_output_start = LocalAudioOutputTransport.start

async def patched_local_audio_output_start(self, frame: StartFrame):
    # This part is from the original `super().start(frame)` call's logic,
    # which is needed since we are replacing the whole method.
    # We await the original BaseOutputTransport.start from the superclass.
    await super(LocalAudioOutputTransport, self).start(frame)

    if self._out_stream:
        return

    self._sample_rate = self._params.audio_out_sample_rate or frame.audio_out_sample_rate

    # --- THE FIX IS HERE ---
    # We add `frames_per_buffer` to stabilize the output stream.
    # 2048 is a robust, common buffer size that should prevent underruns.
    # You can experiment with 1024 or 4096 if needed.
    buffer_size = 2048
    logger.debug(f"Patching PyAudio output stream with frames_per_buffer={buffer_size}")

    self._out_stream = self._py_audio.open(
        format=self._py_audio.get_format_from_width(2),
        channels=self._params.audio_out_channels,
        rate=self._sample_rate,
        output=True,
        output_device_index=self._params.output_device_index,
        frames_per_buffer=buffer_size,
    )
    self._out_stream.start_stream()

    await self.set_transport_ready(frame)

# 3. Overwrite the original method with our patched version
LocalAudioOutputTransport.start = patched_local_audio_output_start

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
#from pipecat.processors.filters.stt_mute_filter import STTMuteConfig, STTMuteFilter, STTMuteStrategy
#from pipecat.processors.filters.function_filter import FunctionFilter
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.utils.text.markdown_text_filter import MarkdownTextFilter
#from config.flow_config import flow_config # FlowConfig for the simplified example
#from config.flow_config_child import flow_config # FlowConfig for child example
#from config.flow_config_camera import flow_config #FlowConfig for camera example
from pipecat_flows import FlowArgs, FlowConfig, FlowManager, FlowResult
from config.flow_config_update import create_flow_config

from utils.config_loader import AppConfig
from custom.speaking_state_manager import SpeakingStateManager
from custom.debounce_stt_mute_filter import DebouncedSTTMuteFilter

from animation.monkey_eyes_lib import EyesController

from gpiozero import Button

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

app_config = AppConfig.load_from_yaml("config/agent_config.yaml")

interaction_running = False

async def run_interaction_flow(eyes_controller: EyesController, test: bool = False):
    global interaction_running
    if interaction_running:
        logger.warning("Interaction already in progress. Button press ignored.")
        return

    interaction_running = True

    logger.info("Button pressed, starting interaction flow...")
    eyes_controller.trigger_loading()
    try:
        journey_id = None
        async with httpx.AsyncClient() as client:
            try:
                if test:
                    journey_id = 13
                else:
                    response = await client.post(app_config.apis["base_url"] + app_config.apis["interaction_started"])
                    journey_id = response.json().get("journeyId")
                    if not journey_id:
                        logger.error("Journey ID not found in response.")
                        return
            except httpx.RequestError as e:
                logger.error(f"Error making API request: {e}")
                #TODO: Should we retry or handle this differently?
                return
        
        """Main function to set up and run the simplified bot."""

        transport = LocalAudioTransport(
            params=LocalAudioTransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(params=VADParams(
                    confidence=app_config.vad_settings["confidence"],
                    start_secs=app_config.vad_settings["start_secs"],
                    stop_secs=app_config.vad_settings["stop_secs"],
                    min_volume=app_config.vad_settings["min_volume"],
                )),
                # Make sure these audio devices are correct for your system
                audio_in_device_name=app_config.microphone["device_name"],
                audio_out_device_name=app_config.speaker["device_name"],
                audio_out_block_size=4096,
            ),
        )

        stt = OpenAISTTService(
            api_key=os.getenv("OPENAI_API_KEY"),
            language="de"
        )

        tts = OpenAITTSService(
            api_key=os.getenv("OPENAI_API_KEY"),
            voice="alloy",
            text_filters=[MarkdownTextFilter()],
        )
        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

        context = OpenAILLMContext()
        context_aggregator = llm.create_context_aggregator(context)

        #stt_mute_processor = STTMuteFilter(
        # config=STTMuteConfig(
        # strategies={
        # STTMuteStrategy.ALWAYS,
        # STTMuteStrategy.FUNCTION_CALL
        # },
        # ),
        #)

        #stt_mute_processor = FunctionFilter(filter=SpeakingStateManager(debounce_seconds=0.5).filter_logic)

        stt_mute_processor = DebouncedSTTMuteFilter(eyes_controller=eyes_controller, debounce_seconds=1)

        pipeline = Pipeline(
            [
                transport.input(),
                stt_mute_processor,
                stt,
                context_aggregator.user(),
                llm,
                tts,
                transport.output(),
                context_aggregator.assistant(),
            ]
        )

        task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=False))

        generated_flow_config = create_flow_config(journey_id, eyes_controller, test=test)

        flow_manager = FlowManager(
            task=task,
            llm=llm,
            context_aggregator=context_aggregator,
            tts=tts,
            flow_config=generated_flow_config,
        )

        await flow_manager.initialize()

        logger.info("Starting pipeline runner...")
        runner = PipelineRunner()
        logger.info("Pipeline finished.")
        eyes_controller.stop_loading()
        await runner.run(task)

    except Exception as e:
        logger.error(f"An error occurred during the interaction flow: {e}")
    finally:
        interaction_running = False
        eyes_controller.stop_loading()
        eyes_controller.stop_listening()
        eyes_controller.stop_not_listening()
        eyes_controller.stop_error()
        eyes_controller.trigger_concentrate(indefinite=True)
        logger.info("Interaction finished. Ready for new button press.")


async def main(eyes_controller: EyesController, test: bool = False):
    loop = asyncio.get_running_loop()

    if test:
        logger.info("Running in test mode. Interaction flow will be started on keyboard press.")

        def handle_keyboard_input():
            sys.stdin.readline()
            logger.info("Keyboard input received. Starting interaction flow...")
            asyncio.create_task(run_interaction_flow(eyes_controller, test=True))

        logger.info("Press [ENTER] to start the interaction.")
        loop.add_reader(sys.stdin, handle_keyboard_input)
    else:
        logger.info("Running in normal mode. Interaction flow will be started on button press.")

        def button_press_callback():
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(run_interaction_flow(eyes_controller, test=False))
            )

        try:
            button = Button(app_config.button_pin, pull_up=True, bounce_time=0.1)
            button.when_pressed = button_press_callback
            logger.info(f"Button handler installed on GPIO {app_config.button_pin}. Waiting for press...")
        except Exception as e:
            logger.error(f"Failed to set up button handler: {e}")

    await asyncio.Event().wait()

if __name__ == "__main__":
    test_mode = "--test" in sys.argv

    logger.info("Starting up...")
    eyes_controller = EyesController()
    eyes_controller.start_eyes()
    eyes_controller.trigger_concentrate(indefinite=True)
    logger.info("Eyes controller started. Initializing bot...")

    try:
        asyncio.run(main(eyes_controller=eyes_controller, test=test_mode))
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
        eyes_controller.stop_eyes()
        logger.info("Eyes controller stopped.")
        logger.info("Cleanup complete.")
    finally:
        logger.info("Shutting down eyes controller...")
        eyes_controller.stop_eyes()
        logger.info("Eyes controller stopped.")
        logger.info("Cleanup complete.") 