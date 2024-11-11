# call_service.py
from azure.communication.callautomation import (
    PhoneNumberIdentifier,
    RecognizeInputType,
    TextSource,
)
from azure.communication.callautomation.aio import CallAutomationClient
import logging

logger = logging.getLogger(__name__)


class CallService:
    def __init__(self, config):
        self.config = config
        self.client = CallAutomationClient.from_connection_string(
            config.ACS_CONNECTION_STRING
        )

    async def handle_recognize(
        self, reply_text, caller_id, call_connection_id, context=""
    ):
        play_source = TextSource(text=reply_text, voice_name=self.config.VOICE_NAME)
        connection_client = self.client.get_call_connection(call_connection_id)

        try:
            return await connection_client.start_recognizing_media(
                input_type=RecognizeInputType.SPEECH,
                target_participant=PhoneNumberIdentifier(caller_id),
                end_silence_timeout=0.5,
                play_prompt=play_source,
                operation_context=context,
            )
        except Exception as ex:
            logger.error("Error in recognize: %s", ex)

    async def handle_play(self, call_connection_id, text_to_play, context):
        if len(text_to_play) > self.config.MAX_TEXT_LENGTH:
            text_to_play = text_to_play[: self.config.MAX_TEXT_LENGTH]

        play_source = TextSource(text=text_to_play, voice_name=self.config.VOICE_NAME)
        try:
            await self.client.get_call_connection(call_connection_id).play_media_to_all(
                play_source, operation_context=context
            )
        except Exception as ex:
            logger.error("Error in play_media_to_all: %s", ex)

    async def handle_hangup(self, call_connection_id):
        try:
            await self.client.get_call_connection(call_connection_id).hang_up(
                is_for_everyone=True
            )
        except Exception as ex:
            logger.error("Error in hang_up: %s", ex)
