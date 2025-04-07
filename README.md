<div align="center">

  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/davidmescudi/Kindroid/refs/heads/main/images/logo_dark.svg?token=GHSAT0AAAAAADATBZWOZM3Z3GRASCY3JN6QZ7UGMXQ">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/davidmescudi/Kindroid/refs/heads/main/images/logo_light.svg?token=GHSAT0AAAAAADATBZWPWJTLEZHUXKUSQESAZ7UGMPQ">
    <img alt="kindroid logo" src="https://raw.githubusercontent.com/davidmescudi/Kindroid/refs/heads/main/images/logo_light.svg?token=GHSAT0AAAAAADATBZWPWJTLEZHUXKUSQESAZ7UGMPQ" height="200" style="max-width: 100%;">
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

## Usage

[Usage instructions will be added here]

## License

[License information will be added here]
