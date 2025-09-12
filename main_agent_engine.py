# main.py
import os
import logging
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.cloud import speech, texttospeech
import asyncio
import uuid
import json
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
# from verification.agent import root_agent
from dotenv import load_dotenv
from vertexai import agent_engines
resource_id="7998507287419289600"
user_id=uuid.uuid4().int

import uvicorn

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "testvertexbot-1a0b45623d70.json"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
APP_NAME = "ADK Streaming example"
remote_app = agent_engines.get(resource_id)
# session_service = InMemorySessionService()
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
def create_session(user_id: str) -> None:
    """Creates a new session for the specified user."""
    remote_session = remote_app.create_session(user_id=user_id,state={"user_authenticated":0})
    print("Created session:",remote_session)
    return remote_session['id']

session_id=create_session(str(user_id))

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
                    # bot_response_text = call_agent(user_final_text, "123456", runner)
                    for event in remote_app.stream_query(
                            user_id=user_id,
                            session_id=session_id,
                            message=user_final_text,
                    ):
                        try:
                            res=event['content']
                            print(json.dumps(res, indent=4))
                            res = res['parts'][0]['text']
                            logging.info(f"Generated bot response: {res}")
                            bot_audio_b64 = await synthesize_speech_for_response(res)
                            await websocket.send_json({
                                "is_final": True,
                                "user_text": user_final_text,
                                "bot_response_text": res,
                                "bot_audio_b64": bot_audio_b64
                            })
                        except Exception as e:
                            logging.info(f"Generated bot response: {res}")
                            res="Sure, give me a moment"
                            logging.error(e)

                        # logging.info(f"Generated bot response: {res}")
                        # bot_audio_b64 = await synthesize_speech_for_response(res)
                        # await websocket.send_json({
                        #     "is_final": True,
                        #     "user_text": user_final_text,
                        #     "bot_response_text": res,
                        #     "bot_audio_b64": bot_audio_b64
                        # })

                    # 2. Perform your internal process to get a response.
                    #    (Here we simulate it with a simple echo).
                    #    In a real app, you'd call a database, an LLM, etc.
                    # bot_response_text = f"You said: {user_final_text}"


                    # 3. Synthesize the response text to audio.
                    # bot_audio_b64 = await synthesize_speech_for_response(bot_response_text)

                    # 4. Send a comprehensive JSON object to the client.
                    # await websocket.send_json({
                    #     "is_final": True,
                    #     "user_text": user_final_text,
                    #     "bot_response_text": bot_response_text,
                    #     "bot_audio_b64": bot_audio_b64
                    # })
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