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

Kindroid requires Python 3.11 and uses a combination of conda and pip for package management. Some packages with complex binary dependencies are best installed through conda, while others work well with pip.

### Prerequisites

- [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Python 3.11
- Git

#### System Dependencies

##### macOS
Install [Homebrew](https://brew.sh/) and then run:
```bash
brew install zbar
brew install portaudio
```

##### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y libzbar0 portaudio19-dev
```

### Quick Installation

```bash
git clone https://github.com/davidmescudi/Kindroid.git
cd Kindroid

# Create and activate conda environment
conda create -n kindroid python=3.11
conda activate kindroid

# Install conda dependencies
conda install -c conda-forge numpy opencv pyaudio pillow

# Install the Kindroid package in development mode
pip install -e .

# Install additional pip dependencies
pip install -r requirements.txt
```

If you dont want to install the development dependencies just comment out all packages under `# Development dependencies` in the `requirements.txt`

## Hardware List

| Component | Description | Recommended Model |
|-----------|-------------|------------------|
| Camera | For QR code detection and visual interaction | [Placeholder] |
| Microphone | For speech recognition | [Placeholder] |
| Speaker | For text-to-speech output | [Placeholder] |
| Thermal Printer | For printing responses and information | [Placeholder] |
| Display | For visual feedback and interface | [Placeholder] |
| Microcontroller | For running the Kindroid software | [Placeholder] |

## Usage

[Usage instructions will be added here]

## License
This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0). See the [LICENSE](LICENSE) file for the full license text.

**Non-Commercial Use:** You are free to share and adapt the material for noncommercial purposes, provided you give appropriate credit and include the [LICENSE](LICENSE) file.

**Commercial Use:** Any use that is primarily intended for or directed toward commercial advantage or monetary compensation is strictly prohibited without explicit prior written permission from the copyright holder.

**Use in Other Open Source Projects:** If you wish to incorporate Kindroid into another open-source software project, please contact the copyright holder. Permission may be granted, potentially under a different license (e.g., MIT or Apache 2.0), contingent upon a mutually agreed-upon contribution back to the Kindroid project (such as significant code contributions, bug fixes, or feature development). We encourage you to discuss this *before* starting integration.