import asyncio
import sys

from dotenv import load_dotenv
from loguru import logger
from gpiozero import Button

from utils.config_loader import AppConfig
from animation.monkey_eyes_lib import EyesController
from utils.audio_patch import apply_patch
from interaction.manager import InteractionManager

# Apply patch before anything else
apply_patch()

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

class Application:
    def __init__(self, test_mode: bool = False):
        self._test_mode = test_mode
        self._config = AppConfig.load_from_yaml("config/agent_config.yaml")
        self._eyes_controller = EyesController()
        self._interaction_running = False
        self._loop = asyncio.get_running_loop()

    async def run(self):
        logger.info("Starting up...")
        self._eyes_controller.start_eyes()
        self._eyes_controller.trigger_concentrate(indefinite=True)
        logger.info("Eyes controller started. Initializing bot...")

        if self._test_mode:
            logger.info("Running in test mode. Press [ENTER] to start an interaction.")
            self._loop.add_reader(sys.stdin, self._handle_keyboard_input)
        else:
            logger.info("Running in normal mode. Interaction flow will be started on button press.")
            try:
                button = Button(self._config.button_pin, pull_up=True, bounce_time=0.1)
                button.when_pressed = self._handle_button_press
                logger.info(f"Button handler installed on GPIO {self._config.button_pin}. Waiting for press...")
            except Exception as e:
                logger.error(f"Failed to set up button handler: {e}")

        await asyncio.Event().wait()

    def shutdown(self):
        logger.info("Shutting down...")
        self._eyes_controller.stop_eyes()
        logger.info("Eyes controller stopped.")
        logger.info("Cleanup complete.")

    def _handle_keyboard_input(self):
        sys.stdin.readline()
        logger.info("Keyboard input received. Starting interaction flow...")
        asyncio.create_task(self.run_interaction_flow())

    def _handle_button_press(self):
        self._loop.call_soon_threadsafe(
            lambda: asyncio.create_task(self.run_interaction_flow())
        )

    async def run_interaction_flow(self):
        if self._interaction_running:
            logger.warning("Interaction already in progress. Ignored.")
            return

        self._interaction_running = True
        try:
            manager = InteractionManager(
                config=self._config,
                eyes_controller=self._eyes_controller,
                test_mode=self._test_mode
            )
            await manager.run()
        except Exception as e:
            logger.error(f"An unexpected error occurred in the interaction manager: {e}")
        finally:
            self._interaction_running = False
            logger.info("Interaction finished. Ready for new input.")


async def main():
    test_mode = "--test" in sys.argv
    app = Application(test_mode=test_mode)
    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received.")
    finally:
        app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application startup interrupted.")
