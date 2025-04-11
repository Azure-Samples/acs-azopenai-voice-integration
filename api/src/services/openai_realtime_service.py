import asyncio
import json
from azure.core.credentials import AzureKeyCredential

from openai import AsyncAzureOpenAI
from openai.types.beta.realtime.session import Session
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection, AsyncRealtimeConnectionManager

from src.config.settings import Config
from src.services.cache_service import CacheService
from src.config.constants import OpenAIPrompts
import random

def session_config(sys_msg: str):
    """Returns a random value from the predefined list."""
    values = ['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse']
    ### for details on available param: https://platform.openai.com/docs/api-reference/realtime-sessions/create
    SESSION_CONFIG={
        "input_audio_transcription": {
            "model": "whisper-1",
        },
        "turn_detection": {
            "threshold": 0.4,
            "silence_duration_ms": 600,
            "type": "server_vad"
        },
        "instructions": sys_msg,
        "voice": random.choice(values),
        "modalities": ["text", "audio"] ## required to solicit the initial welcome message
    }
    return SESSION_CONFIG

class OpenAIRealtimeService:
    def __init__(self, config:Config, cache: CacheService):
        self.config = config
        self.cache_service = cache
        self.clients = {}
        self.connection_managers = {}
        self.connections={}
        self.active_websockets = {}
    
    active_websocket = None

    async def _get_system_message_persona_from_payload(
        self, 
        call_id:str,
        promtps:OpenAIPrompts = OpenAIPrompts, 
        persona:str='default'
    ):
        """Method to add logic to configure agent persona leveraging the system prompt and candidate and job cached data"""
        ## Add your logic ##
        acs_call_id = await self.cache_service.get(f'acs_call_id:{call_id}')
        req_payload = await self.cache_service.get(f'payload_dict:{acs_call_id}')
        sys_msg = self._construct_system_message(
            promtps.system_message_dict.get(persona), 
            [
                "\n## ADDITIONAL INFORMATION\n" + json.dumps(req_payload)
            ]
        )
        print(f"\n\n{sys_msg}\n\n")
        return sys_msg
    
    def _construct_system_message(
        self,
        sys_msg:str, 
        str_list_to_append: list[str]=None
    )-> str:
        """Method to construct the system message based on the standard plus customizations"""
        if str_list_to_append:
            return f"{sys_msg} {' '.join(str_list_to_append)}"
        return sys_msg

#start_conversation > start_client
    async def start_client(self, call_id: str):
        """
        Method to start a conversation with the Azure OpenAI service via the RTLowLevelClient.
        Official voice options: 'amuch', 'dan', 'elan', 'marilyn', 'meadow', 'breeze', 'cove', 'ember', 'jupiter', 'alloy', 'echo', and 'shimmer'
        Note that these voices are in preview and will depend on the version of the RTClient your using.
        - ...
        """
        sys_msg = await self._get_system_message_persona_from_payload(call_id)
        client = AsyncAzureOpenAI(
                azure_endpoint=self.config.AZURE_OPENAI_SERVICE_ENDPOINT,
                azure_deployment=self.config.AZURE_OPENAI_DEPLOYMENT_MODEL_NAME,
                api_key=AzureKeyCredential(self.config.AZURE_OPENAI_SERVICE_KEY), 
                api_version="2024-10-01-preview",
            )
        connection_manager = self.client.beta.realtime.connect(
                    model=self.config.AZURE_OPENAI_DEPLOYMENT_MODEL_NAME,
        )
        active_connection = await connection_manager.enter()

        self.clients[call_id] = client
        self.connection_managers[call_id] = connection_manager
        self.connections[call_id] = active_connection
        await active_connection.session.update(session=session_config(sys_msg))
        await active_connection.response.create()
        
        # maybe start by sending welcome message
        asyncio.create_task(self.receive_oai_messages(call_id=call_id))

#send_audio_to_external_ai > audio_to_oai             
    async def audio_to_oai(self, call_id:str, audioData: str):
        connection = self.connections.get(call_id)
        await connection.input_audio_buffer.append(audio=audioData)

#receive_messages > receive_oai_messages
    async def receive_oai_messages(self, call_id: str):
                connection = self.connections.get(call_id)
                async for event in connection:
                    if event is None:
                        continue
                    match event.type:
                        case "session.created":
                            print("Session Created Message")
                            print(f"  Session Id: {event.session.id}")
                            pass
                        case "error":
                            print(f"  Error: {event.error}")
                            pass
                        case "input_audio_buffer.cleared":
                            print("Input Audio Buffer Cleared Message")
                            pass
                        case "input_audio_buffer.speech_started":
                            print(f"Voice activity detection started at {event.audio_start_ms} [ms]")
                            await self.stop_audio(call_id)
                            pass
                        case "input_audio_buffer.speech_stopped":
                            pass
                        case "conversation.item.input_audio_transcription.completed":
                            print(f" User:-- {event.transcript}")
                        case "conversation.item.input_audio_transcription.failed":
                            print(f"  Error: {event.error}")
                        case "response.done":
                            print("Response Done Message")
                            print(f"  Response Id: {event.response.id}")
                            if event.response.status_details:
                                print(f"  Status Details: {event.response.status_details.model_dump_json()}")
                        case "response.audio_transcript.done":
                            print(f" AI:-- {event.transcript}")
                            if any(keyword in event.transcript.lower() for keyword in ["bye", "goodbye", "take care"]):
                                # await _handle_hangup(acs_call_connection_id)
                                # TODO: implement hangup
                                #await self.cleanup_call_resources(call_id)
                                print("### Should hangup the call ###")
                        case "response.audio.delta":
                            await self.oai_to_acs(call_id, event.delta)
                            pass
                        case _:
                            pass

    async def _handle_hangup(self, call_connection_id:str):
        pass        

#init_websocket -> init_incoming_websocket (incoming)
    async def init_incoming_websocket(self, call_id:str, socket):
        #global active_websocket
        self.active_websockets[call_id] = socket

#receive_audio_for_outbound > oai_to_acs
    async def oai_to_acs(self, call_id:str, data):
        try:
            data = {
                "Kind": "AudioData",
                "AudioData": {
                        "Data":  data
                },
                "StopAudio": None
            }

            # Serialize the server streaming data
            serialized_data = json.dumps(data)
            await self.send_message(call_id, serialized_data)
            
        except Exception as e:
            print(e)

# stop oai talking when detecting the user talking
    async def stop_audio(self, call_id: str):
            stop_audio_data = {
                "Kind": "StopAudio",
                "AudioData": None,
                "StopAudio": {}
            }

            json_data = json.dumps(stop_audio_data)
            await self.send_message(call_id, json_data)

# send_message > send_message
    async def send_message(self, call_id:str, message: str):
        active_websocket = self.active_websockets.get(call_id)
        try:
            await active_websocket.send(message)
        except Exception as e:
            print(f"Failed to send message: {e}")
            
#mediaStreamingHandler.process_websocket_message_async -> acs_to_oai
    async def acs_to_oai(self, call_id, stream_data):
        try:
            data = json.loads(stream_data)
            kind = data['kind']
            if kind == "AudioData":
                audio_data = data["audioData"]["data"]
                await self.audio_to_oai(call_id, audio_data)
        except Exception as e:
            print(f'Error processing WebSocket message: {e}')
       
    async def cleanup_call_resources(self, call_id:str, is_acs_id:bool=True):
        """Method to cleanup resources for a call
        :param call_id: The call_id or acs_id to cleanup resources for
        :param is_acs_id: A boolean flag to indicate if the call_id is an acs_id or websocket_id
        """
        if is_acs_id:
            call_id = await self.cache_service.get(f'websocket_id:{call_id}')
        
        connection = self.connections.pop(call_id, None)
        connection_manager = self.connection_managers.pop(call_id, None)    
        client = self.clients.pop(call_id, None)
        websocket = self.active_websockets.pop(call_id, None)
        if websocket:
            print(f"Closing websocket for call_id {call_id} ...")
            await websocket.close()
        if connection:
            print(f"Closing client for call_id {call_id} ...")
            await connection.close()
