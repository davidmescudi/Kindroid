import os

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.utils.text.markdown_text_filter import MarkdownTextFilter

from custom.debounce_stt_mute_filter import DebouncedSTTMuteFilter
from utils.config_loader import AppConfig
from animation.monkey_eyes_lib import EyesController


def create_pipeline(
    config: AppConfig,
    eyes_controller: EyesController,
):
    transport = LocalAudioTransport(
        params=LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(
                confidence=config.vad_settings["confidence"],
                start_secs=config.vad_settings["start_secs"],
                stop_secs=config.vad_settings["stop_secs"],
                min_volume=config.vad_settings["min_volume"],
            )),
            audio_in_device_name=config.microphone["device_name"],
            audio_out_device_name=config.speaker["device_name"],
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

    return pipeline, llm, context_aggregator, tts
