import httpx
from loguru import logger

from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat_flows import FlowManager

from utils.config_loader import AppConfig
from animation.monkey_eyes_lib import EyesController
from config.flow_config import create_flow_config
from pipeline.builder import create_pipeline

class InteractionManager:
    def __init__(self, config: AppConfig, eyes_controller: EyesController, test_mode: bool = False):
        self._config = config
        self._eyes_controller = eyes_controller
        self._test_mode = test_mode

    async def run(self):
        logger.info("Starting interaction flow...")
        self._eyes_controller.trigger_loading()

        try:
            journey_id = await self._get_journey_id()
            if not journey_id:
                return

            pipeline, llm, context_aggregator, tts = create_pipeline(self._config, self._eyes_controller)
            task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=False))
            
            generated_flow_config = create_flow_config(journey_id, self._eyes_controller, test=self._test_mode)

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
            await runner.run(task)
            logger.info("Pipeline finished.")

        except Exception as e:
            logger.error(f"An error occurred during the interaction flow: {e}")
        finally:
            self._eyes_controller.stop_loading()
            self._eyes_controller.stop_listening()
            self._eyes_controller.stop_not_listening()
            self._eyes_controller.stop_error()
            self._eyes_controller.trigger_concentrate(indefinite=True)
            logger.info("Interaction cleanup complete.")

    async def _get_journey_id(self) -> int | None:
        if self._test_mode:
            logger.debug("Using test journey ID.")
            return 13

        async with httpx.AsyncClient() as client:
            url = self._config.apis["base_url"] + self._config.apis["interaction_started"]
            logger.debug(f"Requesting journey ID from {url}")
            try:
                response = await client.post(url)
                response.raise_for_status()
                data = response.json()
                journey_id = data.get("journeyId")
                if not journey_id:
                    logger.error(f"Journey ID not found in response: {data}")
                    return None
                logger.info(f"Received journey ID: {journey_id}")
                return journey_id
            except httpx.RequestError as e:
                logger.error(f"Error making API request to start interaction: {e}")
                return None
            except Exception as e:
                logger.error(f"An unexpected error occurred when getting journey ID: {e}")
                return None
