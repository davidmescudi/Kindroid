# Kindroid
## Setup
First we need some c dependencies installed for this run:
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev
```
If you are using a brand-new flashed Raspberry Pi, you will also need to enable some features on the Pi itself. Type:
`sudo raspi-config`
Inside the menu that opens up, do the following:
1. Select **3. Interface Options**.
2. Select **I6 Serial Port**.
3. For the question *Would you like a login shell to be accessible over serial?*, select **No**.
4. For the question *Would you like the serial port hardware to be enabled?*, select **Yes**.

To start the project, create a virtual environment on the Raspberry Pi 5 and activate it:
```bash
python -m venv kindroid --system-site-packages
source kindroid/bin/activate
```

Then, install the required packages. Keep in mind that some of them will only work on Linux/Raspberry systems:
```bash
# Pipecat dependencies, logging, http and environment variables
pip install "pipecat-ai[openai,silero,local]" pipecat-ai-flows loguru python-dotenv aiohttp PyYAML gpiozero

# Raspberry Pi camera dependencies. Only works on Raspberry Pi.
pip install picamera2 pyzbar numpy

# Animation library dependencies
pip install pygame
```

Make sure that a `.env` file with the correct `OPENAI_API_KEY = <your openai api key>` is present. For configuration purposes, e.g., which microphone, speaker, printer, and camera should be used, see the `config/agent_config.yaml`. Important: You also need to configure the correct `monkey_id` in `config/agent_config.yaml`, which the robot uses to communicate with the backend.

## Misc
As pipecat is hijacking the `SIGINT` signal from the terminal, pressing `CTRL + C` will only kill the pipecat pipeline, not the whole script. To exit out of the whole script (and get your terminal back), hit `CTRL + \`. Keep in mind that `CTRL + \` only works on most Unix-based systems (e.g., macOS, Ubuntu).