# main.py
import os
import logging
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.cloud import speech, texttospeech
import asyncio

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from verification.agent import root_agent
from dotenv import load_dotenv

import uvicorn
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
APP_NAME = "ADK Streaming example"
session_service = InMemorySessionService()
load_dotenv()

# --- FastAPI and Jinja2 Setup ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- Google Cloud API Clients ---
speech_client = speech.SpeechAsyncClient()
tts_client = texttospeech.TextToSpeechAsyncClient()

# --- STT Configuration ---
STREAMING_CONFIG = speech.StreamingRecognitionConfig(
    config=speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True,
    ),
    interim_results=True,
)


# --- HTML Frontend Endpoint ---
@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    """Serves the initial HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})


# --- TTS Helper Function ---
# REFACTORED to be a reusable helper for our new conversational flow
async def synthesize_speech_for_response(text: str) -> str:
    """Synthesizes speech from text and returns Base64 encoded audio."""
    logging.info(f"Synthesizing speech for: {text}")
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = await tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return base64.b64encode(response.audio_content).decode('utf-8')


# --- Original Text-to-Speech (TTS) Endpoint
# We keep this for testing or if you want to use the text input field
@app.post("/api/tts")
async def text_to_speech(request: Request):
    """Handles text-to-speech conversion from a direct API call."""
    data = await request.json()
    text_to_synthesize = data.get("text", "")
    audio_base64 = await synthesize_speech_for_response(text_to_synthesize)
    return {"audio_content": audio_base64}

def start_agent_session(session_id, is_audio=False):
    """Starts an agent session"""

    # Create a Session
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )

    # Create a Runner
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )
    return runner

def call_agent(user_input_topic,SESSION_ID,runner):
    """
    Sends a new topic to the agent (overwriting the initial one if needed)
    and runs the workflow.
    """
    current_session = session_service.get_session(app_name=APP_NAME,
                                                  user_id=SESSION_ID,
                                                  session_id=SESSION_ID)
    if not current_session:
        logger.error("Session not found!")
        return

    current_session.state["user_input"] = user_input_topic
    logger.info(f"Updated session state topic to: {user_input_topic}")

    content = types.Content(role='user', parts=[types.Part(text=f"{user_input_topic}")])
    events = runner.run(user_id=SESSION_ID, session_id=SESSION_ID, new_message=content)

    final_response = "No final response captured."
    for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            logger.info(f"Potential final response from [{event.author}]: {event.content.parts[0].text}")
            final_response = event.content.parts[0].text

    print("\n--- Agent Interaction Result ---")
    print("Agent Final Response: ", final_response)

    final_session = session_service.get_session(app_name=APP_NAME,
                                                user_id=SESSION_ID,
                                                session_id=SESSION_ID)
    print("Final Session State:")
    import json
    print(json.dumps(final_session.state, indent=2))
    print("-------------------------------\n")
    return final_response

runner=start_agent_session("123456")

# --- Speech-to-Text (STT) WebSocket Endpoint with Conversational Logic ---
@app.websocket("/ws/stt")
async def websocket_stt_endpoint(websocket: WebSocket):
    """Handles the WebSocket connection for real-time STT and conversational response."""
    await websocket.accept()
    logging.info("WebSocket STT connection accepted.")

    audio_queue = asyncio.Queue()

    async def get_audio_from_client():
        """Receives audio chunks from client and puts them in a queue."""
        try:
            while True:
                audio_chunk = await websocket.receive_bytes()
                await audio_queue.put(audio_chunk)
        except WebSocketDisconnect:
            logging.info("Client disconnected.")
            await audio_queue.put(None)

    async def run_google_stt():
        """Processes audio from queue, gets transcript, and orchestrates response."""

        async def audio_generator():
            """Async generator for Google STT API."""
            yield speech.StreamingRecognizeRequest(streaming_config=STREAMING_CONFIG)
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    break
                yield speech.StreamingRecognizeRequest(audio_content=chunk)

        try:
            responses = await speech_client.streaming_recognize(requests=audio_generator())

            async for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript

                if result.is_final:
                    logging.info(f"Final transcript received: {transcript}")

                    # --- THIS IS THE CORE CONVERSATIONAL LOGIC ---
                    # 1. User's final speech is ready.
                    user_final_text = transcript
                    bot_response_text = call_agent(user_final_text, "123456", runner)
                    # 2. Perform your internal process to get a response.
                    #    (Here we simulate it with a simple echo).
                    #    In a real app, you'd call a database, an LLM, etc.
                    # bot_response_text = f"You said: {user_final_text}"
                    logging.info(f"Generated bot response: {bot_response_text}")

                    # 3. Synthesize the response text to audio.
                    bot_audio_b64 = await synthesize_speech_for_response(bot_response_text)

                    # 4. Send a comprehensive JSON object to the client.
                    await websocket.send_json({
                        "is_final": True,
                        "user_text": user_final_text,
                        "bot_response_text": bot_response_text,
                        "bot_audio_b64": bot_audio_b64
                    })
                    # We break here because this implementation handles one full
                    # turn (user speech -> bot response) per connection.
                    break
                else:
                    # Send interim results for a live-typing effect.
                    await websocket.send_json({
                        "is_final": False,
                        "text": transcript
                    })

        except Exception as e:
            logging.error(f"Error during Google STT processing: {e}")
        finally:
            if websocket.client_state.name == 'CONNECTED':
                await websocket.close()
            logging.info("STT processing finished for this turn.")

    await asyncio.gather(get_audio_from_client(), run_google_stt())


if __name__=="__main__":
    # export GOOGLE_APPLICATION_CREDENTIALS="./testvertexbot-1a0b45623d70.json"
    uvicorn.run("main:app",port=5000)