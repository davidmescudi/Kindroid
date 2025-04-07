from setuptools import setup, find_packages

setup(
    name="kindroid",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
        "pyserial>=3.5",
        "pyaudio>=0.2.11",
        "SpeechRecognition>=3.8.1",
        "pyttsx3>=2.90",
        "python-dotenv>=0.19.0",
        "pyzbar>=0.1.9",
        "qrcode>=7.4.2",
        "Pillow>=10.0.0",
        "requests>=2.26.0",
        "websockets>=10.0",
        "lmstudio>=0.1.0",
    ],
    python_requires=">=3.11",
) 