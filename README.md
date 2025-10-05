<div align="center">

  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/davidmescudi/Kindroid/refs/heads/main/images/logo_dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/davidmescudi/Kindroid/refs/heads/main/images/logo_light.svg">
    <img alt="kindroid logo" src="https://raw.githubusercontent.com/davidmescudi/Kindroid/refs/heads/main/images/logo_light.svg" height="200" style="max-width: 100%;">
  </picture>

### Kindroid (from English 'kind', German 'Kind' [child] + 'droid')
</div>

# Kindroid
An interactive robot hardware platform for pediatric healthcare. Integrates LLM-based dialogue, text-to-speech, and onboard printing to explore novel support mechanisms for children and staff.

## Installation

### Prerequisites

- Python 3.11
- Git

#### System Dependencies

##### macOS (only in test mode)
Install [Homebrew](https://brew.sh/) and then run:
```bash
brew install zbar
brew install portaudio
```

##### Linux (Raspberry Pi OS)
```bash
sudo apt-get update
sudo apt-get install -y libzbar0 portaudio19-dev
```

If you are using a brand-new flashed Raspberry Pi, you will also need to enable some features on the Pi itself. Type:
`sudo raspi-config`
Inside the menu that opens up, do the following:
1. Select **3. Interface Options**.
2. Select **I6 Serial Port**.
3. For the question *Would you like a login shell to be accessible over serial?*, select **No**.
4. For the question *Would you like the serial port hardware to be enabled?*, select **Yes**.

### Quick Installation

```bash
git clone https://github.com/davidmescudi/Kindroid.git
cd Kindroid

# Create and activate virtual environment
python -m venv kindroid --system-site-packages
source kindroid/bin/activate

# Pipecat dependencies, logging, http and environment variables
pip install "pipecat-ai[openai,silero,local]" pipecat-ai-flows loguru python-dotenv aiohttp PyYAML gpiozero pygame

# Raspberry Pi camera dependencies. Only works on Raspberry Pi.
pip install picamera2 pyzbar numpy
```

Make sure that a `.env` file with the correct `OPENAI_API_KEY = <your openai api key>` is present. For configuration purposes, e.g., which microphone, speaker, printer, and camera should be used, see the `config/agent_config.yaml`. Important: You also need to configure the correct `monkey_id` in `config/agent_config.yaml`, which the robot uses to communicate with the backend.

## Running
First, ensure the virtual environment you created during installation is active:
```bash
source kindroid/bin/activate
```
To run the main application, which requires an internet connection and all hardware components to be connected, execute the following command:
```bash
python main.py
```

### Stopping the Application
As pipecat is hijacking the `SIGINT` signal from the terminal, pressing `CTRL + C` will only kill the pipecat pipeline, not the whole script. To exit out of the whole script (and get your terminal back), hit `CTRL + \`. Keep in mind that `CTRL + \` only works on most Unix-based systems (e.g., macOS, Ubuntu).

### Test Mode (No Backend)
For testing purposes, you can run the application in a mode that skips all API requests to the backend. This is useful for testing local functionality without the need for a running backend.
```bash
python main.py --test
```
### Running Without Hardware
The application will crash if you run it without the required hardware (camera, printer) connected. To run the software for development without hardware, you must prevent the code from initializing these components.

To do this, open `config/flow_config.py` and comment out the lines that import and call functions from `utils.printer` and `utils.camera`.

### Autostart on Boot
The `setup_autostart_service.sh` script can be used to configure this project to start automatically when the system boots. **Before executing** the script, make sure to edit the file and replace the `REPLACE_WITH_ACTUAL_PATH` placeholder with the correct path.

## Hardware Requirements

| Component | Description | Recommended Model |
|-----------|-------------|------------------|
| Camera | For QR code detection and visual interaction | [Raspberry Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/) |
| Microphone | For speech recognition | [ReSpeaker Lite](https://www.seeedstudio.com/ReSpeaker-Lite-p-5928.html) |
| Speaker | For text-to-speech output | [any usb speaker](https://www.amazon.de/s?k=usb+speaker) |
| Thermal Printer | For printing responses and information | [DFRobot DFR0503 Embedded Thermal Printer V2.0](https://www.dfrobot.com/product-1799.html) |
| Display | For visual feedback and interface | [Waveshare 3.5inch Resistive Touch Screen](https://www.waveshare.com/3.5inch-HDMI-LCD.htm) |
| Microcontroller | For running the Kindroid software | [Raspberry Pi 5 (16GB)](https://www.raspberrypi.com/products/raspberry-pi-5/) or [Jetson Nano (>8GB)](https://developer.nvidia.com/embedded/jetson-nano) with [reComputer J101 Carrier Board](https://www.seeedstudio.com/reComputer-J101-v2-Carrier-Board-for-Jetson-Nano-p-5396.html) | 


## License
This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0). See the [LICENSE](LICENSE) file for the full license text.

**Non-Commercial Use:** You are free to share and adapt the material for noncommercial purposes, provided you give appropriate credit and include the [LICENSE](LICENSE) file.

**Commercial Use:** Any use that is primarily intended for or directed toward commercial advantage or monetary compensation is strictly prohibited without explicit prior written permission from the copyright holder.

**Use in Other Open Source Projects:** If you wish to incorporate Kindroid into another open-source software project, please contact the copyright holder. Permission may be granted, potentially under a different license (e.g., MIT or Apache 2.0), contingent upon a mutually agreed-upon contribution back to the Kindroid project (such as significant code contributions, bug fixes, or feature development). We encourage you to discuss this *before* starting integration.