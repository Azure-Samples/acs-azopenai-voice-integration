from __future__ import annotations
import asyncio
import os
import json
import base64
import logging
import uuid
import threading
from typing import Dict, Optional
import websocket
from collections import deque
from azure.identity import DefaultAzureCredential

from src.config.constants import OpenAIPrompts
from src.config.settings import Config
from src.services.cache_service import CacheService
from src.interfaces.ai_voice_base import AIVoiceBase


def agent_session_config(sys_msg: str):
    """Session configuration for agent-based voice live"""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 500,
            },
            "input_audio_noise_reduction": {
                "type": "azure_deep_noise_suppression"
            },
            "input_audio_echo_cancellation": {
                "type": "server_echo_cancellation"
            },
            "voice": {
                "name": "en-US-Emma2:DragonHDLatestNeural",
                "type": "azure-standard",
                "temperature": 0.8,
            },
            "instructions": sys_msg,
            "modalities": ["text", "audio"],
        },
        "event_id": ""
    }
    return json.dumps(session_update)


class AgentVoiceLiveConnection:
    """WebSocket connection for Azure Voice Live Agent Service - Microsoft pattern"""
    
    def __init__(self, url: str, headers: Dict[str, str], logger: logging.Logger):
        self._url = url
        self._headers = headers
        self._logger = logger
        self._ws = None
        self._message_queue = deque()
        self._connected = threading.Event()
        self._error = None
        
    def on_open(self, ws):
        """WebSocket opened callback"""
        self._logger.info("Agent WebSocket connection opened")
        self._connected.set()
        
    def on_message(self, ws, message):
        """WebSocket message received callback"""
        self._message_queue.append(message)
        
    def on_error(self, ws, error):
        """WebSocket error callback"""
        self._logger.error(f"Agent WebSocket error: {error}")
        self._error = error
        
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket closed callback"""
        self._logger.info(f"Agent WebSocket closed: {close_status_code} - {close_msg}")
        self._connected.clear()
    
    def connect(self):
        """Connect to WebSocket"""
        self._logger.info(f"Connecting to Agent WebSocket at {self._url[:100]}...")
        
        # Convert headers dict to list format required by WebSocketApp
        header_list = [f"{k}: {v}" for k, v in self._headers.items()]
        self._logger.info(f"Headers: {header_list}")
        
        self._ws = websocket.WebSocketApp(
            self._url,
            header=header_list,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # Run WebSocket in separate thread
        ws_thread = threading.Thread(target=self._ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection
        if not self._connected.wait(timeout=10):
            raise Exception("Failed to connect to Agent WebSocket within timeout")
        
        if self._error:
            raise Exception(f"Agent WebSocket connection error: {self._error}")
            
        return self
        
    def send(self, message: str):
        """Send message to WebSocket"""
        if self._ws and self._connected.is_set():
            self._ws.send(message)
        else:
            raise Exception("WebSocket not connected")
    
    def recv(self) -> Optional[str]:
        """Receive message from WebSocket (non-blocking)"""
        try:
            return self._message_queue.popleft()
        except IndexError:
            return None
    
    def close(self):
        """Close WebSocket connection"""
        if self._ws:
            self._ws.close()
            self._connected.clear()


class AzureVoiceLiveAgent:
    """Azure Voice Live Agent client - Microsoft pattern"""
    
    def __init__(
        self,
        *,
        azure_endpoint: str | None = None,
        api_version: str | None = None,
        api_key: str | None = None,
        project_name: str | None = None,
        agent_id: str | None = None,
        agent_access_token: str | None = None,
        logger: logging.Logger = None
    ) -> None:
        self._azure_endpoint = azure_endpoint
        self._api_version = api_version
        self._api_key = api_key
        self._project_name = project_name
        self._agent_id = agent_id
        self._agent_access_token = agent_access_token
        self._logger = logger or logging.getLogger(__name__)
        self._connection = None

    def connect(self) -> AgentVoiceLiveConnection:
        """Connect to Voice Live Agent Service using Azure AD authentication"""
        self._logger.info("Connecting to the Voice Live Agent API...")
        if self._connection is not None:
            raise ValueError("Already connected to the Voice Live Agent API.")
        
        # Validate required parameters
        if not self._project_name:
            raise ValueError(f"AI_FOUNDRY_PROJECT_NAME is required for agent mode. Current value: {self._project_name}")
        
        if not self._agent_id:
            raise ValueError(f"AI_FOUNDRY_AGENT_ID is required for agent mode. Current value: {self._agent_id}")

        # Get Azure AD token for agent authentication
        # Agent mode requires Azure AD token, NOT API key
        self._logger.info("Obtaining Azure AD token for agent authentication...")
        try:
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            bearer_token = token.token
            self._logger.info("Successfully obtained Azure AD token")
        except Exception as e:
            self._logger.error(f"Failed to obtain Azure AD token: {e}")
            raise ValueError(f"Agent mode requires Azure AD authentication. Please run 'az login' or configure managed identity. Error: {e}")

        # Construct WebSocket URL for agent
        # NOTE: Token should only be in Authorization header, not in URL
        azure_ws_endpoint = self._azure_endpoint.rstrip('/').replace("https://", "wss://")
        url = f"{azure_ws_endpoint}/voice-live/realtime?api-version={self._api_version}&agent-project-name={self._project_name}&agent-id={self._agent_id}"
        
        self._logger.info(f"Agent config - Project: {self._project_name}, Agent ID: {self._agent_id[:10]}..., API Version: {self._api_version}")
        self._logger.info(f"Connecting to URL: {url}")
        
        # Set up headers with Azure AD Bearer token
        request_id = uuid.uuid4()
        headers = {
            "x-ms-client-request-id": str(request_id),
            "Authorization": f"Bearer {bearer_token}"
        }

        try:
            self._connection = AgentVoiceLiveConnection(url, headers, self._logger)
            return self._connection.connect()
        except Exception as e:
            self._logger.error(f"Failed to connect: {e}")
            raise Exception(f"Failed to connect to the Voice Live Agent API: {e}")


class AsyncAzureVoiceLiveAgentService(AIVoiceBase):
    """Azure Voice Live service with Agent Service support"""
    
    def __init__(self, config: Config, cache: CacheService, logger: logging.Logger):
        self.config = config
        self.cache_service = cache
        self.logger = logger
        self.clients = {}
        self.connections = {}
        self.active_websockets = {}
        self.session_ids = {}  # Store session IDs for each call
        
    async def start_client(self, call_id: str):
        """Start Voice Live client with Agent Service - Microsoft WebSocketApp pattern"""
        try:
            sys_msg = await self._get_system_message_persona_from_payload(call_id=call_id, persona='default')
            
            # Create agent client
            client = AzureVoiceLiveAgent(
                azure_endpoint=self.config.AZURE_VOICE_LIVE_ENDPOINT,
                api_version=self.config.AZURE_VOICE_LIVE_API_VERSION,
                api_key=self.config.AZURE_VOICE_LIVE_API_KEY,
                project_name=self.config.AI_FOUNDRY_PROJECT_NAME,
                agent_id=self.config.AI_FOUNDRY_AGENT_ID,
                agent_access_token=self.config.AI_FOUNDRY_AGENT_ACCESS_TOKEN,
                logger=self.logger
            )
            
            # Connect to agent (this runs in separate thread)
            connection = client.connect()
            
            # Cache client and connection
            self.clients[call_id] = client
            self.connections[call_id] = connection
            
            # NOTE: For agent mode, we DON'T send session.update because the agent
            # is already configured in Azure AI Foundry with its own instructions
            # Sending session.update would override the agent's configuration
            self.logger.info(f"Agent uses pre-configured settings from Azure AI Foundry")
            
            # Start receiving audio in async task - this will handle the greeting
            asyncio.create_task(self.receive_audio_and_playback(call_id=call_id))
            
            self.logger.info(f"Started Voice Live Agent client for call {call_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to start agent client for call {call_id}: {e}")
            raise Exception(f"Failed to connect to Voice Live Agent API: {e}")
    
    async def receive_audio_and_playback(self, call_id: str):
        """Receive audio from Voice Live and send to ACS - Microsoft WebSocketApp pattern"""
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
                    
                    # Now that session is ready, trigger the agent to speak first
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
                
                elif event_type == "response.audio_transcript.delta":
                    pass
                
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
        """Send audio to Agent - Microsoft WebSocketApp pattern"""
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
        """Cleanup resources for a call - Microsoft WebSocketApp pattern"""
        if is_acs_id:
            call_id = await self.cache_service.get(f'websocket_id:{call_id}')
        
        connection = self.connections.pop(call_id, None)
        client = self.clients.pop(call_id, None)
        websocket = self.active_websockets.pop(call_id, None)
        session_id = self.session_ids.pop(call_id, None)
        
        if connection:
            self.logger.info(f"Closing Agent WebSocket for call_id {call_id} ...")
            connection.close()  # WebSocketApp close is synchronous
        
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
        """Get system message from cache or use default
        
        Checks the payload for a 'persona' field to determine which system message to use.
        Falls back to the persona parameter if not found in payload.
        """
        try:
            payload_dict = await self.cache_service.get(f'payload_dict:{call_id}')
            if payload_dict:
                # Check if persona is specified in the payload
                requested_persona = payload_dict.get('persona', persona)
                self.logger.info(f"Using persona: {requested_persona} for call {call_id}")
                return OpenAIPrompts.system_message_dict.get(requested_persona, OpenAIPrompts.SYSTEM_MESSAGE_DEFAULT)
            return OpenAIPrompts.system_message_dict.get(persona, OpenAIPrompts.SYSTEM_MESSAGE_DEFAULT)
        except Exception as e:
            self.logger.error(f"Error getting system message: {e}")
            return OpenAIPrompts.SYSTEM_MESSAGE_DEFAULT

