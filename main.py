"""A simpler example where the agent can either get a way description or scan a QR code."""

import asyncio
import os
import sys
from typing import Literal, Union
import httpx

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
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.utils.text.markdown_text_filter import MarkdownTextFilter
#from config.flow_config import flow_config # FlowConfig for the simplified example
#from config.flow_config_child import flow_config # FlowConfig for child example
#from config.flow_config_camera import flow_config #FlowConfig for camera example
from pipecat_flows import FlowArgs, FlowConfig, FlowManager, FlowResult
from config.flow_config import create_flow_config

from utils.config_loader import AppConfig
from custom.speaking_state_manager import SpeakingStateManager
from custom.debounce_stt_mute_filter import DebouncedSTTMuteFilter

from animation.monkey_eyes_lib import EyesController

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

async def main(test: bool = True):
    eyes_controller = EyesController()
    eyes_controller.start_eyes()
    await asyncio.sleep(4)  # Allow time for the eyes controller to start
    #TODO: Make sure the eyes controller is started before the bot runs and before button press
    #TODO: Run below code only once when the button was pressed
    app_config = AppConfig.load_from_yaml("config/agent_config.yaml")
    journey_id = None
    async with httpx.AsyncClient() as client:
        try:
            #TODO: journey_id needed for locations
            if test:
                journey_id = 13
            else:
                #TODO: Get journey id from server
                response = await client.post(app_config.apis["base_url"] + app_config.apis["interaction_started"])
                journey_id = response.json().get("journeyId")
            if not journey_id:
                logger.error("Journey ID not found in response.")
                return
        except httpx.RequestError as e:
            logger.error(f"Error making API request: {e}")

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
    #    config=STTMuteConfig(
    #        strategies={
    #            STTMuteStrategy.ALWAYS,
    #            STTMuteStrategy.FUNCTION_CALL
    #            },
    #    ),
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

    runner = PipelineRunner()
    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())