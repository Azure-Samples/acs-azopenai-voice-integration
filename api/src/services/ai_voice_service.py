from __future__ import annotations
import asyncio
from openai import AsyncAzureOpenAI
from azure.core.credentials import AzureKeyCredential
from quart import Websocket

from src.config.constants import OpenAIPrompts
from src.config.settings import Config
from src.services.cache_service import CacheService


##
import os
import sys
import uuid
import json
import asyncio
import base64
import logging
import threading
import numpy as np

from collections import deque
from dotenv import load_dotenv
#from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from typing import Dict, Optional, Union, Literal, Set
from typing_extensions import AsyncIterator, TypedDict, Required
from websockets.asyncio.client import connect as ws_connect
from websockets.asyncio.client import ClientConnection as AsyncWebsocket
from websockets.asyncio.client import HeadersLike
from websockets.typing import Data
from websockets.exceptions import WebSocketException

from src.interfaces.ai_voice_base import AIVoiceBase
##

## TODO: Implement use of interface for AI Voice Service

def session_config(sys_msg: str):
    session_update = {
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "azure_semantic_vad",
                    "threshold": 0.2,
                    "prefix_padding_ms": 600,
                    "silence_duration_ms": 200,
                },
                "input_audio_transcription": {
                    "model": "azure-speech"
                },
                "input_audio_noise_reduction": {
                    "type": "azure_deep_noise_suppression"
                },
                "input_audio_echo_cancellation": {
                    "type": "server_echo_cancellation"
                },
                "voice": {
                    "name": "en-GB-ollie:DragonHDV2Neural",
                    "type": "azure-standard",
                    "temperature": 0.8,
                },
                'input_audio_format': 'pcm16', 
                'output_audio_format': 'pcm16', 
                "instructions": sys_msg,
                "modalities": ["text", "audio"],
                "tools": [
                    {
                        "type": "function",
                        "name": "show_product_carousel",
                        "description": "Display an interactive carousel of products for the customer to browse. Use this when showing multiple product options based on customer needs.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "category": {
                                    "type": "string",
                                    "enum": ["phones", "tablets", "accessories"],
                                    "description": "The category of products to display"
                                },
                                "filter": {
                                    "type": "string",
                                    "enum": ["camera-focused", "gaming", "budget", "premium", "all"],
                                    "description": "Filter to apply to the product selection"
                                },
                                "max_price": {
                                    "type": "number",
                                    "description": "Maximum price in GBP for products to show"
                                }
                            },
                            "required": ["category"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "show_product_details",
                        "description": "Display detailed information about a specific product including specifications, pricing, and images.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "product_id": {
                                    "type": "string",
                                    "description": "The unique identifier of the product (e.g., 'iphone-15-pro', 'samsung-s24-ultra')"
                                },
                                "storage_option": {
                                    "type": "string",
                                    "description": "The storage capacity option (e.g., '128GB', '256GB', '512GB')"
                                }
                            },
                            "required": ["product_id"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "show_plan_options",
                        "description": "Display available monthly plans and pricing for a selected device.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "product_id": {
                                    "type": "string",
                                    "description": "The product ID to show plans for"
                                },
                                "contract_length": {
                                    "type": "string",
                                    "enum": ["12", "24", "36"],
                                    "description": "Contract length in months"
                                }
                            },
                            "required": ["product_id"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "confirm_purchase",
                        "description": "Display purchase confirmation summary with all selected items and pricing. Use this after customer agrees to purchase.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "product_id": {
                                    "type": "string",
                                    "description": "The product ID being purchased"
                                },
                                "storage": {
                                    "type": "string",
                                    "description": "Selected storage option"
                                },
                                "plan_id": {
                                    "type": "string",
                                    "description": "Selected plan ID (if applicable)"
                                },
                                "contract_length": {
                                    "type": "string",
                                    "description": "Contract length in months (if applicable)"
                                }
                            },
                            "required": ["product_id"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "show_accessories",
                        "description": "Display compatible accessories for the purchased product (cases, earphones, chargers, etc.). Use this after purchase is confirmed.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "product_id": {
                                    "type": "string",
                                    "description": "The product ID to show accessories for"
                                }
                            },
                            "required": ["product_id"]
                        }
                    }
                ],
                "tool_choice": "auto",
            },
            "event_id": ""
        }
    return json.dumps(session_update)
    

class AsyncAzureVoiceLiveService(AIVoiceBase):
    def __init__(self, config:Config, cache: CacheService, logger: logging.Logger, cosmosdb_service=None):
        self.config = config
        self.cache_service = cache
        self.logger = logger
        self.cosmosdb_service = cosmosdb_service
        self.clients = {}
        self.connection_managers = {}
        self.connections={}
        self.active_websockets = {}
        self.session_ids = {}  # Store session IDs for each call
        self.silence_timers = {}  # Track silence detection timers for each call
        self.silence_threshold = 5.0  # 5 seconds threshold (allow time for AI to think)
        self.response_in_progress = {}  # Track if AI is generating a response
    
    active_websocket = None
    
    async def _start_silence_timer(self, call_id: str):
        """Start a timer to detect AI silence after user stops speaking"""
        # Cancel any existing timer for this call
        await self._cancel_silence_timer(call_id)
        
        async def silence_timeout():
            try:
                await asyncio.sleep(self.silence_threshold)
                # Timer expired - AI hasn't responded
                self.logger.warning(f"⚠️ AI Silence detected for call {call_id} after {self.silence_threshold}s")
                await self._handle_silence_fallback(call_id)
            except asyncio.CancelledError:
                # Timer was cancelled - AI responded in time
                self.logger.info(f"✅ Silence timer cancelled for call {call_id} - AI responded")
        
        # Create and store the timer task
        timer_task = asyncio.create_task(silence_timeout())
        self.silence_timers[call_id] = timer_task
        self.logger.info(f"⏰ Started silence timer for call {call_id} ({self.silence_threshold}s)")
    
    async def _cancel_silence_timer(self, call_id: str):
        """Cancel the silence detection timer for a call"""
        if call_id in self.silence_timers:
            timer_task = self.silence_timers[call_id]
            if not timer_task.done():
                timer_task.cancel()
                try:
                    await timer_task
                except asyncio.CancelledError:
                    pass
            del self.silence_timers[call_id]
    
    async def _handle_silence_fallback(self, call_id: str):
        """Handle AI silence by logging it (fallback disabled to avoid WebSocket issues)"""
        try:
            # Check if a response is already in progress
            if self.response_in_progress.get(call_id, False):
                self.logger.info(f"⏭️ Response already in progress for call {call_id}, skipping fallback")
                return
            
            # Just log the silence - don't try to trigger response as it closes the WebSocket
            self.logger.warning(f"🔇 AI is silent for call {call_id}. Possible causes:")
            self.logger.warning(f"   - User speech was unclear or not detected properly")
            self.logger.warning(f"   - AI needs more context to respond")
            self.logger.warning(f"   - Connection issue with Azure OpenAI")
            self.logger.warning(f"   User may need to speak again or rephrase their question.")
            
            # Note: Automatic fallback triggering is disabled because sending response.create
            # in this state causes the WebSocket to close unexpectedly.
            # The AI will respond when the user speaks again.
            
        except Exception as e:
            self.logger.error(f"Error in silence fallback handler: {e}")
    
    
    async def start_client(self, call_id: str):
        """Method to start the client"""
        sys_msg = await self._get_system_message_persona_from_payload(call_id=call_id, persona='joyce')
        try:
            client = AsyncAzureVoiceLive(
                azure_endpoint=self.config.AZURE_VOICE_LIVE_ENDPOINT,
                api_version=self.config.AZURE_VOICE_LIVE_API_VERSION,
                #token=None,  # Use API key instead
                api_key=self.config.AZURE_VOICE_LIVE_API_KEY,
                #model=self.config.AZURE_VOICE_LIVE_DEPLOYMENT or self.config.VOICE_LIVE_MODEL
            )
            
            connection_manager = client.connect(
                self.config.AZURE_VOICE_LIVE_DEPLOYMENT
            )
            
            active_connection = await connection_manager.enter()
            
            # caching session
            self.clients[call_id] = client
            self.connection_managers[call_id] = connection_manager
            self.connections[call_id] = active_connection
            await active_connection.send(message=session_config(sys_msg))
            #await active_connection.
            # there's more stuff here but I think ACS handles it
            asyncio.create_task(self.receive_audio_and_playback(call_id=call_id))
        
        except Exception as e:
            self.logger.error(f"Failed to start client for call {call_id}: {e}")
            raise Exception(f"Failed to connect to the Voice Live API: {e}")
        
        
    async def audio_to_aoi(self, call_id: str, audio_data: str) -> None:
        connection: AsyncVoiceLiveConnection = self.connections.get(call_id)
        await connection.send(message=audio_data)
        
        
    async def receive_audio_and_playback(self, call_id: str) -> None:
        connection: AsyncVoiceLiveConnection = self.connections.get(call_id)
        #await connection
        last_audio_item_id = None
        #audio_player = AudioPlayerAsync()

        self.logger.info("Starting audio playback ...")
        try:
            #while True:
            async for raw_event in connection:
                if not raw_event:
                    self.logger.warning("Received empty event, skipping...")
                    continue
                event = json.loads(raw_event)
                #print(f"Received event:", {event.get('type')})
                
                event_type = event.get("type")
                
                if event_type == "conversation.item.truncated":
                    self.logger.info("Conversation item truncated")
                    pass

                elif event_type == "session.created":
                    session = event.get("session")
                    session_id = session.get('id')
                    self.logger.info(f"Session created: {session_id}")
                    print(f"\n🎯 SESSION ID: {session_id} | Call ID: {call_id}\n")
                    
                    # Store session ID in memory and cache
                    self.session_ids[call_id] = session_id
                    await self.cache_service.set(f"voice_live_session_id:{call_id}", session_id)

                elif event_type == "response.created":
                    # Response generation started
                    self.response_in_progress[call_id] = True
                    self.logger.debug(f"📝 Response created for call {call_id}")
                
                elif event_type == "response.audio.delta":
                    # AI is responding with audio - cancel silence timer
                    await self._cancel_silence_timer(call_id)
                    
                    if event.get("item_id") != last_audio_item_id:
                        last_audio_item_id = event.get("item_id")
                    #print(f"#########   {event}")
                    await self.oai_to_acs(call_id, event.get("delta", ""))
                    pass

                #bytes_data = base64.b64decode(event.get("delta", ""))
                #audio_player.add_data(bytes_data)
                elif event_type == "response.audio_transcript.delta":
                    # AI is generating transcript - cancel silence timer
                    await self._cancel_silence_timer(call_id)
                    pass
                    
                elif event_type == "input_audio_buffer.speech_started":
                    self.logger.info("Speech started in input audio buffer")
                    # User started speaking - cancel any silence timer
                    await self._cancel_silence_timer(call_id)
                    await self.stop_audio(call_id)
                
                elif event_type == "input_audio_buffer.speech_stopped":
                    self.logger.info("👂 Speech stopped in input audio buffer - starting silence timer")
                    # User stopped speaking - start silence timer
                    await self._start_silence_timer(call_id)
                
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    user_transcript = event.get('transcript', '????')
                    print(f" >>> User: {user_transcript}")
                    
                    # Store user transcript in Cosmos DB
                    await self._store_transcript(call_id, "user", user_transcript)
                
                elif event_type == "response.audio_transcript.done":
                    ai_transcript = event.get('transcript', '????')
                    print(f" >>> AI: {ai_transcript}")
                    
                    # Store AI transcript in Cosmos DB
                    await self._store_transcript(call_id, "assistant", ai_transcript)
                    
                    if any(keyword in ai_transcript.lower() for keyword in ["bye", "goodbye", "take care", "have a great day", "have a good day"]):
                        # await _handle_hangup(acs_call_connection_id)
                        # TODO: implement hangup
                        #await self.cleanup_call_resources(call_id)
                        print("### Should hangup the call ###")
                
                elif event_type == "response.function_call_arguments.done":
                    # Handle tool call completion
                    function_name = event.get('name', '')
                    call_id_event = event.get('call_id', '')
                    arguments = event.get('arguments', '{}')
                    
                    print(f" >>> Tool Call: {function_name}({arguments})")
                    
                    # Store tool call in Cosmos DB as a special message type
                    await self._store_tool_call(call_id, function_name, arguments, call_id_event)
                    
                    # Automatically send tool response to keep conversation flowing
                    # Since UI is view-only, we just acknowledge the tool was called
                    await self._send_automatic_tool_response(call_id, call_id_event, function_name, arguments)
                
                elif event_type == "response.done":
                    # Response complete
                    self.response_in_progress[call_id] = False
                    self.logger.debug(f"✅ Response completed for call {call_id}")
                    
                    # Check if there were any tool calls
                    response = event.get('response', {})
                    output = response.get('output', [])
                    
                    for item in output:
                        if item.get('type') == 'function_call':
                            # Tool call detected but not yet handled
                            pass
            
                elif event_type == "error":
                    error_details = event.get("error", {})
                    error_type = error_details.get("type", "Unknown")
                    error_code = error_details.get("code", "Unknown")
                    error_message = error_details.get("message", "No message provided")
                    raise ValueError(f"Error received: Type={error_type}, Code={error_code}, Message={error_message}")
                
                else:
                    pass

        except Exception as e:
            self.logger.error(f"Error in audio playback: {e}")
    
    
    async def oai_to_acs(self, call_id:str, data):
        try:
            payload = {
                "Kind": "AudioData",
                "AudioData": {
                        "Data":  data
                },
                "StopAudio": None
            }

            # Serialize the server streaming data
            serialized_data = json.dumps(payload)
            await self.send_message(call_id, serialized_data)
            
        except Exception as e:
            self.logger.error(e)
    
    
    async def stop_audio(self, call_id: str):
        stop_audio_data = {
            "Kind": "StopAudio",
            "AudioData": None,
            "StopAudio": {}
        }
        json_data = json.dumps(stop_audio_data)
        await self.send_message(call_id, json_data)
        
        
    async def send_message(self, call_id:str, message: str):
        active_websocket = self.active_websockets.get(call_id)
        try:
            await active_websocket.send(message)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")


    async def handle_hangup(self):
        pass    

    
    async def acs_to_oai(self, call_id, stream_data):
        try:            
            data = json.loads(stream_data)
            kind = data['kind']
            if kind == "AudioData":
                audio = data["audioData"]["data"]
                #audio = base64.b64encode(audio_data).decode("utf-8")
                param = {"type": "input_audio_buffer.append", "audio": audio, "event_id": ""}
                data_json = json.dumps(param)
                await self.audio_to_aoi(call_id, data_json)
        except Exception as e:
            # Only log unexpected errors, not connection closed errors
            if "WebSocket not connected" not in str(e):
                print(f'Error processing WebSocket message: {e}')


    async def cleanup_call_resources(self, call_id:str, is_acs_id:bool=True):
        """Method to cleanup resources for a call
        :param call_id: The call_id or acs_id to cleanup resources for
        :param is_acs_id: A boolean flag to indicate if the call_id is an acs_id or websocket_id
        """
        if is_acs_id:
            call_id = await self.cache_service.get(f'websocket_id:{call_id}')
        
        # Get ACS call ID for Cosmos DB cleanup
        acs_call_id = await self.cache_service.get(f"acs_call_id:{call_id}")
        
        # Cancel any active silence timer
        await self._cancel_silence_timer(call_id)
        
        # Clean up response tracking
        self.response_in_progress.pop(call_id, None)
        
        connection = self.connections.pop(call_id, None)
        connection_manager = self.connection_managers.pop(call_id, None)    
        client = self.clients.pop(call_id, None)
        websocket = self.active_websockets.pop(call_id, None)
        session_id = self.session_ids.pop(call_id, None)
        
        if websocket:
            print(f"Closing websocket for call_id {call_id} ...")
            await websocket.close()
        if connection_manager:
            print(f"Closing connection manager for call_id {call_id} ...")
            await connection_manager.close(None, None, None)
        if connection:
            print(f"Closing connection for call_id {call_id} ...")
            await connection.close(None, None, None)
        
        # Close Cosmos DB session
        if self.cosmosdb_service and self.cosmosdb_service.enabled and acs_call_id:
            try:
                # Get caller ID
                caller_id = await self.cache_service.get(f"caller_id:{acs_call_id}")
                if not caller_id:
                    payload_dict = await self.cache_service.get(f'payload_dict:{acs_call_id}')
                    if payload_dict:
                        caller_id = payload_dict.get('phone_number', 'unknown')
                    else:
                        caller_id = self.config.TARGET_CANDIDATE_PHONE_NUMBER or 'unknown'
                
                self.cosmosdb_service.close_session(
                    session_id=acs_call_id,
                    caller_id=caller_id
                )
                self.logger.info(f"Closed Cosmos DB session for call {call_id}")
            except Exception as e:
                self.logger.error(f"Error closing Cosmos DB session: {e}")
        
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
    
    async def _store_transcript(self, call_id: str, sender: str, message: str):
        """Store transcript in Cosmos DB"""
        if not self.cosmosdb_service or not self.cosmosdb_service.enabled:
            self.logger.debug("Cosmos DB not enabled, skipping transcript storage")
            return
        
        try:
            # Get the ACS call connection ID (Cosmos DB session ID)
            acs_call_id = await self.cache_service.get(f"acs_call_id:{call_id}")
            if not acs_call_id:
                self.logger.warning(f"Could not find ACS call ID for call {call_id}")
                return
            
            # Get caller ID (phone number)
            caller_id = await self.cache_service.get(f"caller_id:{acs_call_id}")
            if not caller_id:
                # Try to get from payload
                payload_dict = await self.cache_service.get(f'payload_dict:{acs_call_id}')
                if payload_dict:
                    caller_id = payload_dict.get('phone_number', 'unknown')
                else:
                    caller_id = self.config.TARGET_CANDIDATE_PHONE_NUMBER or 'unknown'
            
            # Store the message in Cosmos DB
            self.cosmosdb_service.append_message_to_session(
                session_id=acs_call_id,
                caller_id=caller_id,
                sender=sender,
                message=message
            )
            self.logger.debug(f"Stored {sender} transcript in Cosmos DB for call {call_id}")
        except Exception as e:
            self.logger.error(f"Error storing transcript in Cosmos DB: {e}")
    
    async def _store_tool_call(self, call_id: str, function_name: str, arguments: str, tool_call_id: str):
        """Store tool call in Cosmos DB as a special message type"""
        if not self.cosmosdb_service or not self.cosmosdb_service.enabled:
            self.logger.debug("Cosmos DB not enabled, skipping tool call storage")
            return
        
        try:
            # Get the ACS call connection ID
            acs_call_id = await self.cache_service.get(f"acs_call_id:{call_id}")
            if not acs_call_id:
                self.logger.warning(f"Could not find ACS call ID for call {call_id}")
                return
            
            # Get caller ID
            caller_id = await self.cache_service.get(f"caller_id:{acs_call_id}")
            if not caller_id:
                payload_dict = await self.cache_service.get(f'payload_dict:{acs_call_id}')
                if payload_dict:
                    caller_id = payload_dict.get('phone_number', 'unknown')
                else:
                    caller_id = self.config.TARGET_CANDIDATE_PHONE_NUMBER or 'unknown'
            
            # Parse arguments
            try:
                args_dict = json.loads(arguments)
            except:
                args_dict = {}
            
            # Create a special message object for the tool call
            tool_message = json.dumps({
                "type": "tool_call",
                "function_name": function_name,
                "arguments": args_dict,
                "tool_call_id": tool_call_id
            })
            
            # Store as assistant message with special format
            self.cosmosdb_service.append_message_to_session(
                session_id=acs_call_id,
                caller_id=caller_id,
                sender="tool_call",
                message=tool_message
            )
            self.logger.info(f"Stored tool call {function_name} in Cosmos DB for call {call_id}")
        except Exception as e:
            self.logger.error(f"Error storing tool call in Cosmos DB: {e}")
    
    async def _send_automatic_tool_response(self, call_id: str, tool_call_id: str, function_name: str, arguments: str):
        """Automatically send tool response to keep conversation flowing"""
        try:
            connection: AsyncVoiceLiveConnection = self.connections.get(call_id)
            if not connection:
                self.logger.error(f"No active connection for call {call_id}")
                return
            
            # Parse arguments to create a meaningful response
            try:
                args = json.loads(arguments)
            except:
                args = {}
            
            # Create appropriate response based on tool
            response_messages = {
                "show_product_carousel": f"Displayed {args.get('category', 'product')} options for customer to view.",
                "show_product_details": f"Displayed detailed information for {args.get('product_id', 'product')}.",
                "show_plan_options": f"Displayed available plan options for customer to review.",
                "confirm_purchase": "Displayed purchase confirmation summary.",
                "show_accessories": "Displayed compatible accessories for customer to view."
            }
            
            result = {
                "status": "displayed",
                "message": response_messages.get(function_name, "UI component displayed successfully."),
                "customer_viewing": True
            }
            
            # Format the tool response for OpenAI Realtime API
            tool_response = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": tool_call_id,
                    "output": json.dumps(result)
                }
            }
            
            await connection.send(message=json.dumps(tool_response))
            
            # Trigger a response generation so AI continues speaking
            response_create = {
                "type": "response.create"
            }
            await connection.send(message=json.dumps(response_create))
            
            self.logger.info(f"Sent automatic tool response for {function_name}, call_id {tool_call_id}")
        except Exception as e:
            self.logger.error(f"Error sending automatic tool response: {e}")
    
    async def send_tool_response(self, call_id: str, tool_call_id: str, result: dict):
        """Send tool response back to the AI (kept for compatibility)"""
        try:
            connection: AsyncVoiceLiveConnection = self.connections.get(call_id)
            if not connection:
                self.logger.error(f"No active connection for call {call_id}")
                return
            
            # Format the tool response for OpenAI Realtime API
            tool_response = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": tool_call_id,
                    "output": json.dumps(result)
                }
            }
            
            await connection.send(message=json.dumps(tool_response))
            
            # Also trigger a response generation
            response_create = {
                "type": "response.create"
            }
            await connection.send(message=json.dumps(response_create))
            
            self.logger.info(f"Sent tool response for call {call_id}, tool_call_id {tool_call_id}")
        except Exception as e:
            self.logger.error(f"Error sending tool response: {e}")
        
        
    async def init_incoming_websocket(self, call_id:str, socket:Websocket):
        #global active_websocket
        self.active_websockets[call_id] = socket

AUDIO_SAMPLE_RATE = 24000

class AsyncVoiceLiveConnection:
    _connection: AsyncWebsocket

    def __init__(self, url: str, additional_headers: HeadersLike) -> None:
        self._url = url
        self._additional_headers = additional_headers
        self._connection = None

    async def __aenter__(self) -> AsyncVoiceLiveConnection:
        try:
            print(f"Connecting to WebSocket at {self._url} with {self._additional_headers} ...")
            self._connection = await ws_connect(self._url, additional_headers=self._additional_headers)
        except WebSocketException as e:
            raise ValueError(f"Failed to establish a WebSocket connection: {e}")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None

    enter = __aenter__
    close = __aexit__

    async def __aiter__(self) -> AsyncIterator[Data]:
         async for data in self._connection:
             yield data

    async def recv(self) -> Data:
        return await self._connection.recv()

    async def recv_bytes(self) -> bytes:
        return await self._connection.recv()

    async def send(self, message: Data) -> None:
        await self._connection.send(message)

class AsyncAzureVoiceLive:
    def __init__(
        self,
        *,
        azure_endpoint: str | None = None,
        api_version: str | None = None,
        token: str | None = None,
        api_key: str | None = None
    ) -> None:

        self._azure_endpoint = azure_endpoint
        self._api_version = api_version
        self._token = token
        self._api_key = api_key
        self._connection = None
        

    def connect(self, model:str) -> AsyncVoiceLiveConnection:
        print("Connecting to the Voice Live API ...")
        if self._connection is not None:
            raise ValueError("Already connected to the Voice Live API.")
        #if not model:
        #    raise ValueError("Model name is required.")

        url = f"{self._azure_endpoint.rstrip('/')}/voice-live/realtime?api-version={self._api_version}&model={model}&debug=on"
        url = url.replace("https://", "wss://")
        print(f"Connecting to {url} ...")
        auth_header = {"Authorization": f"Bearer {self._token}"} if self._token else {"api-key": self._api_key}
        request_id = uuid.uuid4()
        headers = {"x-ms-client-request-id": str(request_id), **auth_header}

        #print(f"Using headers: {headers}")
        try:
            self._connection = AsyncVoiceLiveConnection(
                url,
                additional_headers=headers,
            )
            return self._connection
        except Exception as e:
            raise Exception(f"Failed to connect to the Voice Live API: {e}")






#class AudioPlayerAsync:
#    def __init__(self):
#        self.queue = deque()
#        self.lock = threading.Lock()
#        self.stream = sd.OutputStream(
#            callback=self.callback,
#            samplerate=AUDIO_SAMPLE_RATE,
#            channels=1,
#            dtype=np.int16,
#            blocksize=2400,
#        )
#        self.playing = False
#
#    def callback(self, outdata, frames, time, status):
#        if status:
#            logger.warning(f"Stream status: {status}")
#        with self.lock:
#            data = np.empty(0, dtype=np.int16)
#            while len(data) < frames and len(self.queue) > 0:
#                item = self.queue.popleft()
#                frames_needed = frames - len(data)
#                data = np.concatenate((data, item[:frames_needed]))
#                if len(item) > frames_needed:
#                    self.queue.appendleft(item[frames_needed:])
#            if len(data) < frames:
#                data = np.concatenate((data, np.zeros(frames - len(data), dtype=np.int16)))
#        outdata[:] = data.reshape(-1, 1)
#
#    def add_data(self, data: bytes):
#        with self.lock:
#            np_data = np.frombuffer(data, dtype=np.int16)
#            self.queue.append(np_data)
#            if not self.playing and len(self.queue) > 10:
#                self.start()
#
#    def start(self):
#        if not self.playing:
#            self.playing = True
#            self.stream.start()
#
#    def stop(self):
#        with self.lock:
#            self.queue.clear()
#        self.playing = False
#        self.stream.stop()
#
#    def terminate(self):
#        with self.lock:
#            self.queue.clear()
#        self.stream.stop()
#        self.stream.close()
#
#async def listen_and_send_audio(self, connection: AsyncVoiceLiveConnection) -> None:
#    self.logger.info("Starting audio stream ...")
#
#    stream = sd.InputStream(channels=1, samplerate=AUDIO_SAMPLE_RATE, dtype="int16")
#    try:
#        stream.start()
#        read_size = int(AUDIO_SAMPLE_RATE * 0.02)
#        while True:
#            if stream.read_available >= read_size:
#                data, _ = stream.read(read_size)
#                audio = base64.b64encode(data).decode("utf-8")
#                param = {"type": "input_audio_buffer.append", "audio": audio, "event_id": ""}
#                data_json = json.dumps(param)
#                await connection.send(data_json)
#    except Exception as e:
#        logger.error(f"Audio stream interrupted. {e}")
#    finally:
#        stream.stop()
#        stream.close()
#        logger.info("Audio stream closed.")
#
#async def receive_audio_and_playback(self, call_id: str, connection: Optional[AsyncVoiceLiveConnection]=None) -> None:
#    connection = self.connections.get(call_id)
#    last_audio_item_id = None
#    audio_player = AudioPlayerAsync()
#
#    logger.info("Starting audio playback ...")
#    try:
#        while True:
#            async for raw_event in connection:
#                event = json.loads(raw_event)
#                print(f"Received event:", {event.get('type')})
#
#                if event.get("type") == "session.created":
#                    session = event.get("session")
#                    logger.info(f"Session created: {session.get('id')}")
#
#                elif event.get("type") == "response.audio.delta":
#                    if event.get("item_id") != last_audio_item_id:
#                        last_audio_item_id = event.get("item_id")
#
#                    bytes_data = base64.b64decode(event.get("delta", ""))
#                    audio_player.add_data(bytes_data)
#
#                elif event.get("type") == "error":
#                    error_details = event.get("error", {})
#                    error_type = error_details.get("type", "Unknown")
#                    error_code = error_details.get("code", "Unknown")
#                    error_message = error_details.get("message", "No message provided")
#                    raise ValueError(f"Error received: Type={error_type}, Code={error_code}, Message={error_message}")
#
#    except Exception as e:
#        logger.error(f"Error in audio playback: {e}")
#    finally:
#        audio_player.terminate()
#        logger.info("Playback done.")
#
#async def read_keyboard_and_quit() -> None:
#    print("Press 'q' and Enter to quit the chat.")
#    while True:
#        # Run input() in a thread to avoid blocking the event loop
#        user_input = await asyncio.to_thread(input)
#        if user_input.strip().lower() == 'q':
#            print("Quitting the chat...")
#            break
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#    async def start_client(self, call_id: str) -> AsyncVoiceLiveConnection:
#        sys_msg = await self._get_system_message_persona_from_payload(call_id=call_id)
#        
#        #if self._connection is not None:
#        #    raise ValueError("Already connected to the Voice Live API.")
#        model = self.config.AZURE_VOICE_LIVE_DEPLOYMENT or self.config.VOICE_LIVE_MODEL
#        endpoint = self.config.AZURE_VOICE_LIVE_ENDPOINT 
#        api_version = self.config.AZURE_VOICE_LIVE_API_VERSION 
#        if not model or not endpoint or not api_version:
#            raise ValueError(
#                f"Model, endpoint, and API version must be specified on the environment variables. Current values: "+
#                f"model={model}, endpoint={endpoint}, api_version={api_version}")
#        
#        #if not self.config.SHOULD_USE_KEYS:
#        #    scopes = "https://cognitiveservices.azure.com/.default"
#        #    credential = DefaultAzureCredential()
#        #    token = await credential.get_token(scopes)
#
#        url = f"{endpoint.rstrip('/')}/voice-live/realtime?api-version={api_version}&model={model}"
#        url = url.replace("https://", "wss://")
#        #print(f"Connecting to {url} ...")
#        auth_header = {"api-key": self.config.AZURE_VOICE_LIVE_API_KEY} # if self.config.SHOULD_USE_KEYS else {"Authorization": f"Bearer {self}"}
#        request_id = uuid.uuid4()
#        headers = {"x-ms-client-request-id": str(request_id), **auth_header}
#
#        try:
#            connection = AsyncVoiceLiveConnection(
#                url,
#                additional_headers=headers,
#            )
#            
#            
#            active_connection = await connection.enter()
#            self.connections[call_id] = active_connection
#            
#        
#        except Exception as e:
#            raise Exception(f"Failed to connect to the Voice Live API: {e}")
#
#
#
#class AsyncVoiceLiveConnection:
#    _connection: AsyncWebsocket
#
#    def __init__(self, url: str, additional_headers: HeadersLike) -> None:
#        self._url = url
#        self._additional_headers = additional_headers
#        self._connection = None
#
#    async def __aenter__(self) -> AsyncVoiceLiveConnection:
#        try:
#            print(f"Connecting to WebSocket at {self._url} with {self._additional_headers} ...")
#            self._connection = await ws_connect(self._url, additional_headers=self._additional_headers)
#        except WebSocketException as e:
#            raise ValueError(f"Failed to establish a WebSocket connection: {e}")
#        return self
#
#    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
#        if self._connection:
#            await self._connection.close()
#            self._connection = None
#
#    enter = __aenter__
#    close = __aexit__
#
#    async def __aiter__(self) -> AsyncIterator[Data]:
#         async for data in self._connection:
#             yield data
#
#    async def recv(self) -> Data:
#        return await self._connection.recv()
#
#    async def recv_bytes(self) -> bytes:
#        return await self._connection.recv()
#
#    async def send(self, message: Data) -> None:
#        await self._connection.send(message)
#
#
#
#
#
#class AIVoiceService:
#    def __init__(self, config: Config):
#        self.config = config
#        self.aoai_client = AsyncAzureOpenAI(
#            endpoint=config.AZURE_OPENAI_SERVICE_ENDPOINT,
#            key=AzureKeyCredential(config.AZURE_OPENAI_SERVICE_KEY),
#            deployment_model=config.AZURE_OPENAI_DEPLOYMENT_MODEL_NAME
#        )
#
#    async def start_conversation(self):
#        pass