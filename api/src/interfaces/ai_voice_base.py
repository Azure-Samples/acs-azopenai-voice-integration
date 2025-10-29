from abc import ABC, abstractmethod
import logging
import json

from quart import Websocket

from src.config.constants import OpenAIPrompts
from src.config.settings import Config
from src.services.cache_service import CacheService


class AIVoiceBase(ABC):
    """
    Base class for AI voice interfaces.
    This class can be extended to implement specific AI voice functionalities.
    """
    def __init__(
        self,
        cache_service: CacheService,
        config: Config,
        logger=logging.Logger
    ):
        self.cache_service = cache_service
        self.logger = logger
        self.config = config
    
    
    @abstractmethod
    async def start_client(self, call_id: str):
        """Method to start the AI voice client for a given call ID."""
        pass
    
    @abstractmethod
    async def receive_audio_and_playback(self, call_id: str):
        """Method to receive audio from the AI voice client and integrate with ACS."""
        pass
    
    @abstractmethod
    async def init_incoming_websocket(self, call_id:str, socket:Websocket):
        """Initializes the incoming WebSocket connection for AI voice interactions."""
        pass
    
    @abstractmethod
    async def acs_to_oai(self, call_id: str, stream_data):  # choose the stream data type
        pass
    
    @abstractmethod
    async def cleanup_call_resources(self, call_id: str, is_acs_id: bool):
        """Method to clean up resources for a call."""
        pass
    
    async def _get_system_message_persona_from_payload(
        self, 
        call_id:str,
        promtps:OpenAIPrompts = OpenAIPrompts, 
        persona:str='default'
    ):
        """Method to add logic to configure agent persona leveraging the system prompt and candidate and job cached data
        
        Checks the payload for a 'persona' field to determine which system message to use.
        Falls back to the persona parameter if not found in payload.
        Available personas: 'default' (travel agent), 'recruitment' (job interview)
        """
        ## Add your logic ##
        acs_call_id = await self.cache_service.get(f'acs_call_id:{call_id}')
        req_payload = await self.cache_service.get(f'payload_dict:{acs_call_id}')
        
        # Check if persona is specified in the payload, otherwise use the parameter
        if req_payload and 'persona' in req_payload:
            requested_persona = req_payload.get('persona', persona)
            print(f"Using persona from payload: {requested_persona}")
        else:
            requested_persona = persona
            print(f"Using default persona: {requested_persona}")
        
        sys_msg = self._construct_system_message(
            promtps.system_message_dict.get(requested_persona, promtps.SYSTEM_MESSAGE_DEFAULT), 
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