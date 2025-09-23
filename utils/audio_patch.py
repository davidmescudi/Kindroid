"""
This module patches the LocalAudioOutputTransport to fix audio cracking issues
by specifying a fixed buffer size for the output stream.
"""
from loguru import logger
from pipecat.frames.frames import StartFrame
from pipecat.transports.local.audio import LocalAudioOutputTransport

def apply_patch():
    """Applies the patch to LocalAudioOutputTransport."""
    logger.info("Applying audio output patch for LocalAudioOutputTransport.")

    async def patched_local_audio_output_start(self, frame: StartFrame):
        await super(LocalAudioOutputTransport, self).start(frame)

        if self._out_stream:
            return

        self._sample_rate = self._params.audio_out_sample_rate or frame.audio_out_sample_rate

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

    LocalAudioOutputTransport.start = patched_local_audio_output_start
