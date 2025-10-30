#Speech example to test the Azure Voice Live API
from __future__ import annotations
import os
import uuid
import json
import time
import base64
import logging
import threading
import asyncio
import numpy as np
import sounddevice as sd
import queue
import signal
import sys

from collections import deque
from dotenv import load_dotenv
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential
from typing import Dict, Union, Literal, Set, Optional
from typing_extensions import Iterator, TypedDict, Required
import websocket
from websocket import WebSocketApp
from datetime import datetime

# Import application dependencies for service integration
from src.config.constants import OpenAIPrompts
from src.config.settings import Config
from src.services.cache_service import CacheService
from src.interfaces.ai_voice_base import AIVoiceBase

# Global variables for thread coordination (only for standalone mode)
stop_event = threading.Event()
connection_queue = queue.Queue()

# This is the main function to run the Voice Live API client.
def main() -> None: 
    # Set environment variables or edit the corresponding values here.
    endpoint = os.environ.get("AZURE_VOICE_LIVE_ENDPOINT")
    agent_id = os.environ.get("AI_FOUNDRY_AGENT_ID")
    project_name = os.environ.get("AI_FOUNDRY_PROJECT_NAME")
    api_version = os.environ.get("AZURE_VOICE_LIVE_API_VERSION") or "2025-10-01"
    voice_name = os.environ.get("VOICE_NAME") or "en-US-Ava:DragonHDLatestNeural"
    
    # Validate required environment variables
    if not endpoint:
        raise ValueError("AZURE_VOICE_LIVE_ENDPOINT environment variable is required. Please set it in your .env file.")
    if not agent_id:
        raise ValueError("AI_FOUNDRY_AGENT_ID environment variable is required. Please set it in your .env file.")
    if not project_name:
        raise ValueError("AI_FOUNDRY_PROJECT_NAME environment variable is required. Please set it in your .env file.")

    # For the recommended keyless authentication, get and
    # use the Microsoft Entra token instead of api_key:
    credential = DefaultAzureCredential()
    scopes = "https://ai.azure.com/.default"
    token = credential.get_token(scopes)

    client = AzureVoiceLive(
        azure_endpoint = endpoint,
        api_version = api_version,
        token = token.token,
        # api_key = api_key,
    )

    connection = client.connect(
        project_name=project_name,
        agent_id=agent_id,
        agent_access_token=token.token
    )

    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {
                "type": "azure_semantic_vad",
                "threshold": 0.3,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 200,
                "remove_filler_words": False,
                "end_of_utterance_detection": {
                    "model": "semantic_detection_v1",
                    "threshold": 0.01,
                    "timeout": 2,
                },
            },
            "input_audio_noise_reduction": {
                "type": "azure_deep_noise_suppression"
            },
            "input_audio_echo_cancellation": {
                "type": "server_echo_cancellation"
            },
            "voice": {
                "name": voice_name,
                "type": "azure-standard",
                "temperature": 0.8,
            },
        },
        "event_id": ""
    }
    connection.send(json.dumps(session_update))
    print(f"Using voice: {voice_name}")
    print("Session created: ", json.dumps(session_update))


    # Log session configuration
    write_conversation_log(f'Session Config: {json.dumps(session_update)}')

    # Create and start threads
    send_thread = threading.Thread(target=listen_and_send_audio, args=(connection,))
    receive_thread = threading.Thread(target=receive_audio_and_playback, args=(connection,))
    keyboard_thread = threading.Thread(target=read_keyboard_and_quit)

    print("Starting the chat ...")

    send_thread.start()
    receive_thread.start()
    keyboard_thread.start()

    # Wait for any thread to complete (usually the keyboard thread when user quits)
    keyboard_thread.join()

    # Signal other threads to stop
    stop_event.set()

    # Wait for other threads to finish
    send_thread.join(timeout=2)
    receive_thread.join(timeout=2)

    connection.close()
    print("Chat done.")

# --- End of Main Function ---

logger = logging.getLogger(__name__)
AUDIO_SAMPLE_RATE = 24000

class VoiceLiveConnection:
    def __init__(self, url: str, headers: dict) -> None:
        self._url = url
        self._headers = headers
        self._ws = None
        self._message_queue = queue.Queue()
        self._connected = False

    def connect(self) -> None:
        def on_message(ws, message):
            self._message_queue.put(message)

        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
            self._connected = False

        def on_open(ws):
            logger.info("WebSocket connection opened")
            self._connected = True

        self._ws = websocket.WebSocketApp(
            self._url,
            header=self._headers,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        # Start WebSocket in a separate thread
        self._ws_thread = threading.Thread(target=self._ws.run_forever)
        self._ws_thread.daemon = True
        self._ws_thread.start()

        # Wait for connection to be established
        timeout = 10  # seconds
        start_time = time.time()
        while not self._connected and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not self._connected:
            raise ConnectionError("Failed to establish WebSocket connection")

    def recv(self) -> str:
        try:
            return self._message_queue.get(timeout=1)
        except queue.Empty:
            return None

    def send(self, message: str) -> None:
        if self._ws and self._connected:
            self._ws.send(message)

    def close(self) -> None:
        if self._ws:
            self._ws.close()
            self._connected = False

class AzureVoiceLive:
    def __init__(
        self,
        *,
        azure_endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:

        self._azure_endpoint = azure_endpoint
        self._api_version = api_version
        self._token = token
        self._api_key = api_key
        self._connection = None

    def connect(self, project_name: str, agent_id: str, agent_access_token: str) -> VoiceLiveConnection:
        if self._connection is not None:
            raise ValueError("Already connected to the Voice Live API.")
        if not project_name:
            raise ValueError("Project name is required.")
        if not agent_id:
            raise ValueError("Agent ID is required.")
        if not agent_access_token:
            raise ValueError("Agent access token is required.")

        azure_ws_endpoint = self._azure_endpoint.rstrip('/').replace("https://", "wss://")

        url = f"{azure_ws_endpoint}/voice-live/realtime?api-version={self._api_version}&agent-project-name={project_name}&agent-id={agent_id}&agent-access-token={agent_access_token}"

        auth_header = {"Authorization": f"Bearer {self._token}"} if self._token else {"api-key": self._api_key}
        request_id = uuid.uuid4()
        headers = {"x-ms-client-request-id": str(request_id), **auth_header}

        self._connection = VoiceLiveConnection(url, headers)
        self._connection.connect()
        return self._connection

class AudioPlayerAsync:
    def __init__(self):
        self.queue = deque()
        self.lock = threading.Lock()
        self.stream = sd.OutputStream(
            callback=self.callback,
            samplerate=AUDIO_SAMPLE_RATE,
            channels=1,
            dtype=np.int16,
            blocksize=2400,
        )
        self.playing = False

    def callback(self, outdata, frames, time, status):
        if status:
            logger.warning(f"Stream status: {status}")
        with self.lock:
            data = np.empty(0, dtype=np.int16)
            while len(data) < frames and len(self.queue) > 0:
                item = self.queue.popleft()
                frames_needed = frames - len(data)
                data = np.concatenate((data, item[:frames_needed]))
                if len(item) > frames_needed:
                    self.queue.appendleft(item[frames_needed:])
            if len(data) < frames:
                data = np.concatenate((data, np.zeros(frames - len(data), dtype=np.int16)))
        outdata[:] = data.reshape(-1, 1)

    def add_data(self, data: bytes):
        with self.lock:
            np_data = np.frombuffer(data, dtype=np.int16)
            self.queue.append(np_data)
            if not self.playing and len(self.queue) > 0:
                self.start()

    def start(self):
        if not self.playing:
            self.playing = True
            self.stream.start()

    def stop(self):
        with self.lock:
            self.queue.clear()
        self.playing = False
        self.stream.stop()

    def terminate(self):
        with self.lock:
            self.queue.clear()
        self.stream.stop()
        self.stream.close()

def listen_and_send_audio(connection: VoiceLiveConnection) -> None:
    logger.info("Starting audio stream ...")

    stream = sd.InputStream(channels=1, samplerate=AUDIO_SAMPLE_RATE, dtype="int16")
    try:
        stream.start()
        read_size = int(AUDIO_SAMPLE_RATE * 0.02)
        while not stop_event.is_set():
            if stream.read_available >= read_size:
                data, _ = stream.read(read_size)
                audio = base64.b64encode(data).decode("utf-8")
                param = {"type": "input_audio_buffer.append", "audio": audio, "event_id": ""}
                # print("sending - ", param)
                data_json = json.dumps(param)
                connection.send(data_json)
            else:
                time.sleep(0.001)  # Small sleep to prevent busy waiting
    except Exception as e:
        logger.error(f"Audio stream interrupted. {e}")
    finally:
        stream.stop()
        stream.close()
        logger.info("Audio stream closed.")

def receive_audio_and_playback(connection: VoiceLiveConnection) -> None:
    last_audio_item_id = None
    audio_player = AudioPlayerAsync()

    logger.info("Starting audio playback ...")
    try:
        while not stop_event.is_set():
            raw_event = connection.recv()
            if raw_event is None:
                continue

            try:
                event = json.loads(raw_event)
                event_type = event.get("type")
                print(f"Received event:", {event_type})

                if event_type == "session.created":
                    session = event.get("session")
                    logger.info(f"Session created: {session.get('id')}")
                    write_conversation_log(f"SessionID: {session.get('id')}")

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    user_transcript = f'User Input:\t{event.get("transcript", "")}'
                    print(f'\n\t{user_transcript}\n')
                    write_conversation_log(user_transcript)

                elif event_type == "response.text.done":
                    agent_text = f'Agent Text Response:\t{event.get("text", "")}'
                    print(f'\n\t{agent_text}\n')
                    write_conversation_log(agent_text)

                elif event_type == "response.audio_transcript.done":
                    agent_audio = f'Agent Audio Response:\t{event.get("transcript", "")}'
                    print(f'\n\t{agent_audio}\n')
                    write_conversation_log(agent_audio)

                elif event_type == "response.audio.delta":
                    if event.get("item_id") != last_audio_item_id:
                        last_audio_item_id = event.get("item_id")

                    bytes_data = base64.b64decode(event.get("delta", ""))
                    if bytes_data:
                        logger.debug(f"Received audio data of length: {len(bytes_data)}")   
                    audio_player.add_data(bytes_data)

                elif event.get("type") == "input_audio_buffer.speech_started":
                    print("Speech started")
                    audio_player.stop()

                elif event.get("type") == "error":
                    error_details = event.get("error", {})
                    error_type = error_details.get("type", "Unknown")
                    error_code = error_details.get("code", "Unknown")
                    error_message = error_details.get("message", "No message provided")
                    raise ValueError(f"Error received: Type={error_type}, Code={error_code}, Message={error_message}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON event: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in audio playback: {e}")
    finally:
        audio_player.terminate()
        logger.info("Playback done.")

def read_keyboard_and_quit() -> None:
    print("Press 'q' and Enter to quit the chat.")
    while not stop_event.is_set():
        try:
            user_input = input()
            if user_input.strip().lower() == 'q':
                print("Quitting the chat...")
                stop_event.set()
                break
        except EOFError:
            # Handle case where input is interrupted
            break

def write_conversation_log(message: str) -> None:
    """Write a message to the conversation log."""
    with open(f'logs/{logfilename}', 'a') as conversation_log:
        conversation_log.write(message + "\n")


# ============================================================================
# SERVICE CLASS FOR INTEGRATION WITH MAIN APP
# ============================================================================

class AsyncAzureVoiceLiveAgentService(AIVoiceBase):
    """Azure Voice Live Agent Service - integrates with ACS Call Automation"""
    
    def __init__(self, config: Config, cache: CacheService, logger: logging.Logger):
        self.config = config
        self.cache_service = cache
        self.logger = logger
        self.clients = {}
        self.connections = {}
        self.active_websockets = {}
        self.session_ids = {}  # Store session IDs for each call
        
    async def start_client(self, call_id: str):
        """Start Voice Live Agent client"""
        try:
            # Get voice name from payload or use default
            sys_msg = await self._get_system_message_persona_from_payload(call_id=call_id, persona='default')
            voice_name = self.config.VOICE_NAME if hasattr(self.config, 'VOICE_NAME') else "en-US-Ava:DragonHDLatestNeural"
            
            # Get Azure AD token
            credential = DefaultAzureCredential()
            token = credential.get_token("https://ai.azure.com/.default")
            
            # Create agent client
            client = AzureVoiceLive(
                azure_endpoint=self.config.AZURE_VOICE_LIVE_ENDPOINT,
                api_version=self.config.AZURE_VOICE_LIVE_API_VERSION,
                token=token.token,
            )
            
            # Connect to agent
            connection = client.connect(
                project_name=self.config.AI_FOUNDRY_PROJECT_NAME,
                agent_id=self.config.AI_FOUNDRY_AGENT_ID,
                agent_access_token=token.token
            )
            
            # Store client and connection
            self.clients[call_id] = client
            self.connections[call_id] = connection
            
            # Send session configuration with voice name
            session_update = {
                "type": "session.update",
                "session": {
                    "turn_detection": {
                        "type": "azure_semantic_vad",
                        "threshold": 0.3,
                        "prefix_padding_ms": 200,
                        "silence_duration_ms": 200,
                    },
                    "input_audio_noise_reduction": {
                        "type": "azure_deep_noise_suppression"
                    },
                    "input_audio_echo_cancellation": {
                        "type": "server_echo_cancellation"
                    },
                    "voice": {
                        "name": voice_name,
                        "type": "azure-standard",
                        "temperature": 0.8,
                    },
                },
                "event_id": ""
            }
            connection.send(json.dumps(session_update))
            self.logger.info(f"Using voice: {voice_name}")
            
            # Start receiving audio in async task
            asyncio.create_task(self.receive_audio_and_playback(call_id=call_id))
            
            self.logger.info(f"Started Voice Live Agent client for call {call_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start agent client for call {call_id}: {e}")
            raise Exception(f"Failed to connect to Voice Live Agent API: {e}")
    
    async def receive_audio_and_playback(self, call_id: str):
        """Receive audio from Voice Live and send to ACS"""
        connection = self.connections.get(call_id)
        if not connection:
            self.logger.error(f"No connection found for call {call_id}")
            return
        
        last_audio_item_id = None
        session_ready = False
        self.logger.info("Starting audio playback ...")
        
        try:
            while True:
                # Poll for messages (non-blocking with async sleep)
                raw_event = connection.recv()
                if not raw_event:
                    await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
                    continue
                
                event = json.loads(raw_event)
                event_type = event.get("type")
                
                # Log all events for debugging
                self.logger.debug(f"Received event: {event_type}")
                
                if event_type == "session.created":
                    session = event.get("session")
                    session_id = session.get('id')
                    self.logger.info(f"Session created: {session_id}")
                    print(f"\n🎯 AGENT SESSION ID: {session_id} | Call ID: {call_id}\n")
                    
                    # Store session ID in memory and cache
                    self.session_ids[call_id] = session_id
                    await self.cache_service.set(f"voice_live_session_id:{call_id}", session_id)
                    
                    session_ready = True
                    
                    # Trigger the agent to speak first
                    self.logger.info("Triggering agent to introduce itself...")
                    greeting_trigger = {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": "Hello, please introduce yourself"
                                }
                            ]
                        }
                    }
                    connection.send(json.dumps(greeting_trigger))
                    
                    # Request a response from the agent
                    response_create = {"type": "response.create"}
                    connection.send(json.dumps(response_create))
                    self.logger.info("Greeting trigger sent to agent")
                
                elif event_type == "response.audio.delta":
                    if event.get("item_id") != last_audio_item_id:
                        last_audio_item_id = event.get("item_id")
                    await self.oai_to_acs(call_id, event.get("delta", ""))
                
                elif event_type == "input_audio_buffer.speech_started":
                    self.logger.info("Speech started in input audio buffer")
                    await self.stop_audio(call_id)
                
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    self.logger.info(f" >>> User: {event.get('transcript', '????')}")
                
                elif event_type == "response.audio_transcript.done":
                    transcript = event.get('transcript', '????')
                    self.logger.info(f" >>> Agent: {transcript}")
                    if any(keyword in transcript.lower() for keyword in ["bye", "goodbye", "take care", "have a great day", "have a good day"]):
                        self.logger.info("### Should hangup the call ###")
                
                elif event_type == "error":
                    error_details = event.get("error", {})
                    error_type = error_details.get("type", "Unknown")
                    error_code = error_details.get("code", "Unknown")
                    error_message = error_details.get("message", "No message provided")
                    raise ValueError(f"Error received: Type={error_type}, Code={error_code}, Message={error_message}")
                
        except Exception as e:
            self.logger.error(f"Error in audio playback: {e}")
    
    async def oai_to_acs(self, call_id: str, data: str):
        """Send audio from OpenAI to ACS"""
        try:
            payload = {
                "Kind": "AudioData",
                "AudioData": {
                    "Data": data
                },
                "StopAudio": None
            }
            serialized_data = json.dumps(payload)
            await self.send_message(call_id, serialized_data)
        except Exception as e:
            self.logger.error(f"Error sending audio to ACS: {e}")
    
    async def stop_audio(self, call_id: str):
        """Stop audio playback"""
        stop_audio_data = {
            "Kind": "StopAudio",
            "AudioData": None,
            "StopAudio": {}
        }
        json_data = json.dumps(stop_audio_data)
        await self.send_message(call_id, json_data)
    
    async def send_message(self, call_id: str, message: str):
        """Send message to ACS via WebSocket"""
        active_websocket = self.active_websockets.get(call_id)
        try:
            await active_websocket.send(message)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
    
    async def acs_to_oai(self, call_id: str, stream_data: str):
        """Receive audio from ACS and send to OpenAI"""
        try:
            data = json.loads(stream_data)
            kind = data.get('kind')
            if kind == "AudioData":
                audio_data = data["audioData"]["data"]
                await self.audio_to_oai(call_id, audio_data)
        except Exception as e:
            # Only log unexpected errors, not connection closed errors
            if "WebSocket not connected" not in str(e):
                self.logger.error(f'Error processing WebSocket message: {e}')
    
    async def audio_to_oai(self, call_id: str, audioData: str):
        """Send audio to Agent"""
        connection = self.connections.get(call_id)
        if connection:
            param = {
                "type": "input_audio_buffer.append",
                "audio": audioData,
                "event_id": ""
            }
            # WebSocketApp send is synchronous, but we're in async context
            connection.send(json.dumps(param))
    
    async def init_incoming_websocket(self, call_id: str, socket):
        """Initialize incoming WebSocket from ACS"""
        self.active_websockets[call_id] = socket
    
    async def cleanup_call_resources(self, call_id: str, is_acs_id: bool = True):
        """Cleanup resources for a call"""
        if is_acs_id:
            call_id = await self.cache_service.get(f'websocket_id:{call_id}')
        
        connection = self.connections.pop(call_id, None)
        client = self.clients.pop(call_id, None)
        websocket = self.active_websockets.pop(call_id, None)
        session_id = self.session_ids.pop(call_id, None)
        
        if connection:
            self.logger.info(f"Closing Agent WebSocket for call_id {call_id} ...")
            connection.close()
        
        if websocket:
            self.logger.info(f"Closing ACS websocket for call_id {call_id} ...")
            await websocket.close()
        
        # Clean up session ID from cache
        if session_id:
            try:
                await self.cache_service.delete(f"voice_live_session_id:{call_id}")
            except:
                pass
    
    async def get_session_id(self, call_id: str) -> Optional[str]:
        """Get the Voice Live session ID for a call"""
        # Try to get from memory first
        session_id = self.session_ids.get(call_id)
        if session_id:
            return session_id
        
        # Fall back to cache
        return await self.cache_service.get(f"voice_live_session_id:{call_id}")
    
    async def _get_system_message_persona_from_payload(self, call_id: str, persona: str = 'default') -> str:
        """Get system message from cache or use default"""
        try:
            payload_dict = await self.cache_service.get(f'payload_dict:{call_id}')
            if payload_dict:
                requested_persona = payload_dict.get('persona', persona)
                self.logger.info(f"Using persona: {requested_persona} for call {call_id}")
                return OpenAIPrompts.system_message_dict.get(requested_persona, OpenAIPrompts.SYSTEM_MESSAGE_DEFAULT)
            return OpenAIPrompts.system_message_dict.get(persona, OpenAIPrompts.SYSTEM_MESSAGE_DEFAULT)
        except Exception as e:
            self.logger.error(f"Error getting system message: {e}")
            return OpenAIPrompts.SYSTEM_MESSAGE_DEFAULT


# ============================================================================
# STANDALONE MODE
# ============================================================================

if __name__ == "__main__":
    try:
        # Change to the directory where this script is located
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # Add folder for logging
        if not os.path.exists('logs'):
            os.makedirs('logs')
        # Add timestamp for logfiles
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logfilename = f"{timestamp}_conversation.log"
        # Set up logging
        logging.basicConfig(
            filename=f'logs/{timestamp}_voicelive.log',
            filemode="w",
            level=logging.DEBUG,
            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s'
        )
        # Load environment variables from .env file
        load_dotenv("./.env", override=True)

        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            print("\nReceived interrupt signal, shutting down...")
            stop_event.set()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        main()
    except Exception as e:
        print(f"Error: {e}")
        stop_event.set()