# src/core/event_handlers.py
from azure.core.messaging import CloudEvent
from typing import Dict, Any, Callable, Optional
from ..config.constants import EventTypes, ConversationPrompts
from ..services.call_handler import CallHandler
from ..services.cache_service import CacheService
from ..services.openai_service import OpenAIService
from ..services.cosmosdb_service import CosmosDBService
from ..utils.logger import setup_logger
class EventHandlers:
    """Handles different types of call automation events"""
    def __init__(self, 
                 call_handler: CallHandler, 
                 cache_service: CacheService,
                 openai_service: OpenAIService,
                 cosmosdb_service: CosmosDBService):
        self.call_handler = call_handler
        self.cache_service = cache_service
        self.openai_service = openai_service
        self.cosmosdb_service = cosmosdb_service
        self.max_retry = 2
        self._setup_context_handlers()
        # Initialize logger
        self.logger = setup_logger(__name__)        

    def _setup_context_handlers(self) -> None:
        """Initialize context handlers mapping"""
        self.context_handlers = {
            "InitialGreeting": self._handle_initial_greeting,
            "ConsentRequest": self._handle_consent_request,
            "LocationRequest": self._handle_location_request,
            "CommuteQuestion": self._handle_commute_question,
            "JobInterest": self._handle_job_interest,
            "CompetencyResponse": self._handle_competency_response,
            "NextStepsRequest": self._handle_next_steps_request
        }
        
        self.play_completed_handlers = {
            "ConsentRequest": self._handle_consent_play_completed,
            "LocationRequest": self._handle_location_play_completed,
            "JobDetails": self._handle_job_details_play_completed,
            "GOODBYE_CONTEXT": self._handle_goodbye_play_completed
        }

    # async def handle_call_connected(self, event: CloudEvent, caller_id: str) -> None:
    #     """Handle call connected event"""
    #     await self.call_handler.handle_recognize(
    #         ConversationPrompts.HELLO,
    #         caller_id,
    #         event.data["callConnectionId"],
    #         context="InitialGreeting"
    #     )

    async def handle_call_connected(self, event: CloudEvent, phone_number: str) -> None:
        """
        Handle call connected event with proper error handling
        Args:
            event: CloudEvent containing call data
            phone_number: Caller or Target's phone number depending on whether it's an incoming or outgoing call
        """
        try:
            call_connection_id = event.data.get("callConnectionId")
            if not call_connection_id:
                self.logger.error("Missing callConnectionId in CallConnected event")
                return
            # Create a new session in CosmosDB
            session_id = self.cosmosdb_service.create_new_session(phone_number)
            # Initialize the conversation state
            await self.cache_service.set("call_active", True)
            await self.cache_service.set("current_session_id", session_id)
            await self.cache_service.set("current_call_id", call_connection_id)
            result = None  # Initialize result

            participant_id = await self.cache_service.get("participant_id")
            

            if participant_id:
                result = await self.call_handler.handle_recognize(
                    ConversationPrompts.HELLO,
                    participant_id,
                    call_connection_id,
                    context="InitialGreeting"
                )
            else:
                self.logger.info("Participant ID not available yet. Waiting for ParticipantsUpdated event.")
            
            if result is None:
                self.logger.error("Initial greeting recognition failed")
                # await self.call_handler.hangup(call_connection_id)
                
        except Exception as e:
            self.logger.error(f"Error in handle_call_connected: {str(e)}", exc_info=True)
            if call_connection_id:
                await self.call_handler.hangup(call_connection_id)

    async def handle_participants_updated(self, event: CloudEvent, caller_id: str) -> None:
        """Handle participants updated event""" 
        try:
            call_connection_id = event.data.get("callConnectionId")
            participants = event.data.get("participants", [])
            for participant in participants:
                if participant['identifier']['rawId'].split(":")[1] == caller_id:
                    participant_id = participant['identifier']['rawId'].split(":")[1]
                    await self.cache_service.set("participant_id", participant_id)
            
            # Log participants update
            self.logger.info(f"Participants updated for call {call_connection_id}")
            self.logger.info(f"Current participants: {participants}")
            
            # Store participants in cache if needed
            await self.cache_service.set("current_participants", participants)
                        
        except Exception as e:
            self.logger.error(f"Error in handle_participants_updated: {str(e)}", exc_info=True)

    async def handle_recognize_completed(self, event: CloudEvent, caller_id: str) -> None:
        """Handle recognize completed event"""
        if event.data["recognitionType"] == "speech":
            # Log user message to CosmosDB
            speech_result = event.data.get("speechResult", {})
            speech_text = speech_result.get("speech")
            session_id = await self.cache_service.get("current_session_id")
            if session_id and speech_text:
                self.cosmosdb_service.append_message_to_session(
                    session_id, caller_id, "user", speech_text
                )
            await self._handle_speech_recognition(event, caller_id)
        elif event.data["recognitionType"] == "dxtmf":
            await self._handle_dtmf_recognition(event, caller_id)

    async def _handle_speech_recognition(self, event: CloudEvent, caller_id: str) -> None:
        """Handle speech recognition completion"""
        speech_text = event.data["speechResult"]["speech"]
        context = event.data["operationContext"]
        call_connection_id = event.data["callConnectionId"]

        handler = self.context_handlers.get(context)
        if handler:
            await handler(speech_text, caller_id, call_connection_id)
        else:
            print(f"No handler found for context: {context}")

    async def _handle_initial_greeting(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle initial greeting response"""
        if any(keyword in speech_text.lower() for keyword in ["no", "not interested", "busy"]):
            await self.call_handler.handle_play(
                call_connection_id,
                "No problem, I understand. Have a good day!",
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)
        else:
            consent_message = await self.cache_service.get("consent_message")
            await self.call_handler.handle_recognize(
                consent_message,
                caller_id,
                call_connection_id,
                context="ConsentRequest"
            )

    async def _handle_consent_request(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle consent request response"""
        if "no" in speech_text.lower():
            await self.call_handler.handle_play(
                call_connection_id,
                "I understand. Thank you for your time. Have a great day!",
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)
        else:
            location_question = await self.cache_service.get("location_question")
            await self.call_handler.handle_recognize(
                location_question,
                caller_id,
                call_connection_id,
                context="LocationRequest"
            )

    async def _handle_location_request(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle location request response"""
        # Store the location in cache
        await self.cache_service.set("candidate_location", speech_text)
        
        # Get job location and details
        job_location = await self.cache_service.get("job_location")
        job_details = await self.cache_service.get("job_details")
        
        # In a real implementation, you would validate the location here
        # For now, just proceed with job details
        await self.call_handler.handle_play(
            call_connection_id,
            f"The role is based in {job_location}. {job_details}",
            context="JobDetails"
        )

    async def _handle_commute_question(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle commute question response"""
        if any(keyword in speech_text.lower() for keyword in ["yes", "okay", "fine", "sure"]):
            job_details = await self.cache_service.get("job_details")
            await self.call_handler.handle_play(
                call_connection_id,
                f"Great! {job_details}",
                context="JobDetails"
            )
        else:
            await self.call_handler.handle_play(
                call_connection_id,
                "I understand. Thank you for your time. Have a great day!",
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)

    async def _handle_job_interest(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle job interest response"""
        if any(keyword in speech_text.lower() for keyword in ["no", "not interested"]):
            await self.call_handler.handle_play(
                call_connection_id,
                "I understand. Thank you for your time. Have a great day!",
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)
        else:
            # Get competency question from cache or generate one
            competency_question = await self.openai_service.get_chat_completion(
                "Generate a relevant competency question for an AI Vice President role"
            )
            await self.call_handler.handle_recognize(
                competency_question,
                caller_id,
                call_connection_id,
                context="CompetencyResponse"
            )

    async def _handle_competency_response(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle competency question response"""
        # Generate acknowledgment using OpenAI
        acknowledgment = await self.openai_service.get_chat_completion(
            f"Generate a positive acknowledgment for this experience: {speech_text}"
        )
        
        await self.call_handler.handle_play(
            call_connection_id,
            acknowledgment,
            context="Acknowledgement"
        )
        
        # Ask about next steps
        next_steps = "Based on your experience, I think you would be a great fit for this role. Would it be okay if I forwarded your CV to our client?"
        await self.call_handler.handle_recognize(
            next_steps,
            caller_id,
            call_connection_id,
            context="NextStepsRequest"
        )

    async def _handle_next_steps_request(
        self, 
        speech_text: str, 
        caller_id: str, 
        call_connection_id: str
    ) -> None:
        """Handle next steps request response"""
        if any(keyword in speech_text.lower() for keyword in ["yes", "okay", "sure"]):
            await self.call_handler.handle_play(
                call_connection_id,
                ConversationPrompts.THANK_YOU,
                "GOODBYE_CONTEXT"
            )
        else:
            await self.call_handler.handle_play(
                call_connection_id,
                ConversationPrompts.GOODBYE,
                "GOODBYE_CONTEXT"
            )
        await self.call_handler.hangup(call_connection_id)

    async def handle_play_completed(self, event: CloudEvent, caller_id: str) -> None:
        """Handle play completed event"""
        context = event.data["operationContext"]
        call_connection_id = event.data["callConnectionId"]

        # Log the playback completion or message played
        session_id = await self.cache_service.get("current_session_id")
        if session_id:
            # You might store the message that was played in cache or retrieve it from the context
            # For this example, we'll log a generic message
            self.cosmosdb_service.append_message_to_session(
                session_id, caller_id, "application", f"Playback completed for context: {context}"
            )

        handler = self.play_completed_handlers.get(context)
        if handler:
            await handler(event, caller_id)
        elif context == "GOODBYE_CONTEXT":
            await self.call_handler.hangup(call_connection_id)

    async def _handle_consent_play_completed(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle consent play completed"""
        location_question = await self.cache_service.get("location_question")
        await self.call_handler.handle_recognize(
            location_question,
            caller_id,
            event.data["callConnectionId"],
            context="LocationRequest"
        )

    async def _handle_location_play_completed(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle location play completed"""
        job_details = await self.cache_service.get("job_details")
        await self.call_handler.handle_play(
            event.data["callConnectionId"],
            job_details,
            context="JobDetails"
        )

    async def _handle_job_details_play_completed(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle job details play completed"""
        interest_question = await self.cache_service.get("user_interested")
        await self.call_handler.handle_recognize(
            interest_question,
            caller_id,
            event.data["callConnectionId"],
            context="JobInterest"
        )

    async def _handle_goodbye_play_completed(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle goodbye play completed"""
        await self.call_handler.hangup(event.data["callConnectionId"])

    async def _handle_dtmf_recognition(
        self, 
        event: CloudEvent, 
        caller_id: str
    ) -> None:
        """Handle DTMF recognition"""
        # Implement DTMF handling if needed
        pass

    async def handle_recognize_failed(self, event: CloudEvent, caller_id: str) -> None:
        """Handle recognize failed event"""
        result_information = event.data["resultInformation"]
        reason_code = result_information["subCode"]
        context = event.data["operationContext"]
        call_connection_id = event.data["callConnectionId"]

        if reason_code == 8510 and self.max_retry > 0:
            await self.call_handler.handle_recognize(
                ConversationPrompts.TIMEOUT_SILENCE,
                caller_id,
                call_connection_id,
                context=context
            )
            self.max_retry -= 1
        else:
            await self.call_handler.handle_play(
                call_connection_id,
                ConversationPrompts.GOODBYE,
                "GOODBYE_CONTEXT"
            )
            await self.call_handler.hangup(call_connection_id)

    async def handle_call_disconnected(self, event: CloudEvent, caller_id: str) -> None:
        """Handle call disconnected event"""
        print(f"Call disconnected for call connection id: {event.data['callConnectionId']}")
        await self.cache_service.clear()  # Clean up the cache for this session