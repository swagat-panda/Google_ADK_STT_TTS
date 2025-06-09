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

# Add your Google JSON file here
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "testvertexbot-1a0b45623d70.json"

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

async def start_agent_session(session_id, is_audio=False):
    """Starts an agent session"""
    try:
        # Create a Session
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=session_id,
            session_id=session_id,
        )
        
        if not session:
            logger.error(f"Failed to create session for ID: {session_id}")
            return None

        # Create a Runner
        runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=session_service,
        )
        return runner
    except Exception as e:
        logger.error(f"Error creating agent session: {e}")
        return None

async def call_agent(user_input_topic, SESSION_ID, runner):
    """
    Sends a new topic to the agent and streams the response.
    """
    try:
        current_session = await session_service.get_session(app_name=APP_NAME,
                                                      user_id=SESSION_ID,
                                                      session_id=SESSION_ID)
        if not current_session:
            logger.error("Session not found! Creating new session...")
            runner = await start_agent_session(SESSION_ID)
            if not runner:
                yield {
                    "is_final": True,
                    "text": "I apologize, but I'm having trouble starting our conversation. Please try again."
                }
                return

            current_session = await session_service.get_session(app_name=APP_NAME,
                                                          user_id=SESSION_ID,
                                                          session_id=SESSION_ID)

        current_session.state["user_input"] = user_input_topic
        logger.info(f"Updated session state topic to: {user_input_topic}")

        content = types.Content(role='user', parts=[types.Part(text=f"{user_input_topic}")])
        events = runner.run(user_id=SESSION_ID, session_id=SESSION_ID, new_message=content)

        current_text = ""
        for event in events:
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
                if response_text:
                    # Split the response into words for streaming effect
                    words = response_text.split()
                    for word in words:
                        current_text += word + " "
                        # Add a small delay to simulate streaming
                        await asyncio.sleep(0.1)
                        logger.info(f"Streaming word: {word}")
                        yield {
                            "is_final": False,
                            "text": current_text.strip()
                        }

        # Send final response
        if current_text:
            logger.info(f"Final response: {current_text.strip()}")
            yield {
                "is_final": True,
                "text": current_text.strip()
            }
        else:
            yield {
                "is_final": True,
                "text": "I apologize, but I couldn't process that request. Please try again."
            }

    except Exception as e:
        logger.error(f"Error in call_agent: {e}")
        yield {
            "is_final": True,
            "text": "I apologize, but I encountered an error. Please try again."
        }

# Initialize runner at module level
runner = None

# --- Speech-to-Text (STT) WebSocket Endpoint with Conversational Logic ---
@app.websocket("/ws/stt")
async def websocket_stt_endpoint(websocket: WebSocket):
    """Handles the WebSocket connection for real-time STT and conversational response."""
    global runner
    SESSION_ID = "123456"  # You might want to generate this dynamically
    
    try:
        # Accept the WebSocket connection first
        await websocket.accept()
        logging.info("WebSocket STT connection accepted.")

        if runner is None:
            runner = await start_agent_session(SESSION_ID)
            if not runner:
                await websocket.close()
                return

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
            except Exception as e:
                logging.error(f"Error in get_audio_from_client: {e}")
                await audio_queue.put(None)

        async def run_google_stt():
            """Processes audio from queue, gets transcript, and orchestrates response."""
            try:
                async def audio_generator():
                    """Async generator for Google STT API."""
                    yield speech.StreamingRecognizeRequest(streaming_config=STREAMING_CONFIG)
                    while True:
                        chunk = await audio_queue.get()
                        if chunk is None:
                            break
                        yield speech.StreamingRecognizeRequest(audio_content=chunk)

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
                        user_final_text = transcript
                        
                        # Send user's final text first
                        await websocket.send_json({
                            "is_final": True,
                            "user_text": user_final_text,
                            "is_user": True
                        })
                        
                        # Stream the agent's response
                        async for response_chunk in call_agent(user_final_text, SESSION_ID, runner):
                            if response_chunk["is_final"]:
                                # For the final response, synthesize speech
                                bot_audio_b64 = await synthesize_speech_for_response(response_chunk["text"])
                                await websocket.send_json({
                                    "is_final": True,
                                    "bot_response_text": response_chunk["text"],
                                    "bot_audio_b64": bot_audio_b64,
                                    "is_user": False
                                })
                            else:
                                # For streaming responses, just send the text
                                await websocket.send_json({
                                    "is_final": False,
                                    "bot_response_text": response_chunk["text"],
                                    "is_user": False
                                })
                        break
                    else:
                        # Send interim user transcript
                        await websocket.send_json({
                            "is_final": False,
                            "user_text": transcript,
                            "is_user": True
                        })

            except Exception as e:
                logging.error(f"Error during Google STT processing: {e}")
            finally:
                if websocket.client_state.name == 'CONNECTED':
                    await websocket.close()
                logging.info("STT processing finished for this turn.")

        await asyncio.gather(get_audio_from_client(), run_google_stt())
    except Exception as e:
        logging.error(f"Error in websocket_stt_endpoint: {e}")
        if websocket.client_state.name == 'CONNECTED':
            await websocket.close()


if __name__=="__main__":
    # export GOOGLE_APPLICATION_CREDENTIALS="./testvertexbot-79f3e052a826.json"
    uvicorn.run("main:app",port=5000)