# Google Agent development kit(ADK) with Speech-to-Text and Text-to-Speech

This project implements a Google Development Kit (ADK) application with integrated speech-to-text (STT) and text-to-speech (TTS) capabilities. It provides a complete solution for voice interaction using Google's SDK.

## Features

- **Google Assistant Integration**: Full integration with Google Assistant SDK
- **Speech-to-Text**: Real-time speech recognition capabilities
- **Text-to-Speech**: Natural language synthesis for voice responses
- **Voice Interaction**: Two-way voice communication with the Assistant
- **Customizable Wake Word**: Support for custom wake word detection
- **Audio Processing**: Efficient audio capture and playback

## Prerequisites

- Python 3.7 or higher
- Google Cloud Platform account
- Google Assistant SDK credentials
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd Google_ADK_STT_TTS
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```env
    GOOGLE_GENAI_USE_VERTEXAI=TRUE

    # Vertex backend config
    GOOGLE_CLOUD_PROJECT=<project-name>
    GOOGLE_CLOUD_LOCATION=<location>
    GOOGLE_CLOUD_STAGING_BUCKET=<cloud-storage-bucket-name>
   ```

4. Set up Google Cloud credentials:
   - Create a project in Google Cloud Console
   - Enable the Google Assistant API
   - Download your credentials file
   - Place the credentials file in your project directory

## Configuration

1. Update the path of credentials json file in `main.py`:

## Usage

1. Start the application:
```bash
python main.py
```

2. The application will:
   - Initialize the Google Assistant
   - Set up audio devices
   - Begin listening for the wake word
   - Process voice commands
   - Provide voice responses

## Project Structure

```
.
├── main.py                 # Main application entry point
├── assistant.py            # Google Assistant integration
├── audio_processor.py      # Audio processing utilities
├── config.json            # Configuration settings
├── .env                   # ADK Environment variables
├── <credentials.json>     # Google Cloud credentials           
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   └── index.html        # Main web interface
└── README.md             # This file
```

## Dependencies

- `google-assistant-sdk`
- `google-cloud-speech`
- `google-cloud-texttospeech`
- `pyaudio`
- `numpy`
- `sounddevice`
- `python-dotenv`
- `fastapi`
- `uvicorn`
- `jinja2`


## Acknowledgments

- Google Assistant SDK team
- Google Cloud Platform
- Contributors and maintainers





