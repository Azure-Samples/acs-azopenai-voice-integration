from typing import Optional, Dict, Any
from azure.communication.callautomation import (
    TextSource,
    RecognizeInputType,
    PhoneNumberIdentifier,
    CallAutomationClient
)
from ..config.settings import Config
from ..config.constants import AppConstants, ErrorMessages

class CallHandler:
    """Handles direct call-related operations"""
    def __init__(self, config: Config, call_automation_client: CallAutomationClient):
        self.config = config
        self.call_automation_client = call_automation_client

    async def handle_play(
        self,
        call_connection_id: str,
        text_to_play: str,
        context: str
    ) -> Optional[dict]:
        """
        Handle playing text to the call
        Args:
            call_connection_id: Active call connection ID
            text_to_play: Text to be played
            context: Operation context
        """
        try:
            if not text_to_play or not text_to_play.strip():
                text_to_play = ErrorMessages.PLAY_ERROR
            
            if len(text_to_play) > AppConstants.MAX_TEXT_LENGTH:
                text_to_play = text_to_play[:AppConstants.MAX_TEXT_LENGTH]
            
            play_source = TextSource(
                text=text_to_play,
                voice_name=self.config.VOICE_NAME
            )
            
            connection = self.call_automation_client.get_call_connection(call_connection_id)
            await connection.play_media_to_all(
                play_source,
                operation_context=context
            )
            return {'data': '200 OK'}
            
        except Exception as ex:
            print(f"Error in handle_play: {ex}")
            return {'Error in handle_play': ex}
            # Could add more sophisticated error handling here

    async def handle_recognize(
        self,
        reply_text: str,
        caller_id: str,
        call_connection_id: str,
        context: str = ""
    ) -> Optional[dict]:
        """
        Handle speech recognition
        Args:
            reply_text: Text to play before recognition
            caller_id: Caller's phone number
            call_connection_id: Active call connection ID
            context: Operation context
        Returns:
            Optional[dict]: Recognition result
        """
        try:
            if not reply_text or not reply_text.strip():
                reply_text = ErrorMessages.RECOGNIZE_ERROR
                
            if len(reply_text) > AppConstants.MAX_TEXT_LENGTH:
                reply_text = reply_text[:AppConstants.MAX_TEXT_LENGTH]
                
            play_source = TextSource(
                text=reply_text,
                voice_name=self.config.VOICE_NAME
            )
            
            connection = self.call_automation_client.get_call_connection(call_connection_id)
            await connection.start_recognizing_media(
                input_type=RecognizeInputType.SPEECH,
                target_participant=PhoneNumberIdentifier(caller_id),
                end_silence_timeout=self.config.END_SILENCE_TIMEOUT,
                play_prompt=play_source,
                operation_context=context,
                #interrupt_prompt=True,
                #initial_silence_timeout=30
            )
                     
            return {'data': '200 OK'}
            
        except Exception as ex:
            #print(f"Error in recognize: {ex}")
            return {'Error in recognize': ex}
        
    
    async def handle_communicate(
        self,
        reply_text: str,
        call_connection_id: str,
        context: str = "",
        caller_id: Optional[str] = None
    ) -> Optional[dict]:
        """Evaluates if it should use handle_recognize or handle_play based on the context"""
        if "goalAchieved" in context:
            await self.handle_play(
                call_connection_id=call_connection_id,
                text_to_play=reply_text,
                context=context
            )
            
        #elif "endCall" in context:
        #    await handle_play(
        #        call_connection_id=call_connection_id,
        #        text_to_play=text_to_play,
        #        context=context
        #    )
            
        else:
            await self.handle_recognize(
                reply_text=reply_text,
                caller_id=caller_id,
                call_connection_id=call_connection_id,
                context=context
            )
        
    async def hangup(self, call_connection_id: str) -> None:
        """
        Hang up the call
        Args:
            call_connection_id: Active call connection ID
        """
        try:
            await self.call_automation_client.get_call_connection(
                call_connection_id
            ).hang_up(is_for_everyone=True)
        except Exception as ex:
            print(f"Error in hangup: {ex}")            