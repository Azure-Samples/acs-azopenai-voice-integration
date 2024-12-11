import uuid
import json
from urllib.parse import urlencode
from quart import Quart, Response, request
from azure.eventgrid import EventGridEvent, SystemEventNames
from azure.core.messaging import CloudEvent
from azure.communication.callautomation import (
    PhoneNumberIdentifier,
    CallAutomationClient,
)
from azure.core.exceptions import AzureError
import asyncio

from src.config.settings import Config
from src.config.constants import EventTypes, StatusCodes, ApiPayloadKeysForValidation
from src.services.call_handler import CallHandler
from src.services.cache_service import CacheService
from src.services.openai_service import OpenAIService
from src.core.event_handlers import EventHandlers
from src.services.cosmosdb_service import CosmosDBService

from src.utils.logger import setup_logger


class CallAutomationApp:
    """Main application class"""

    def __init__(self):
        self.app = Quart(__name__)
        self.config = Config()
        self.logger = setup_logger(__name__)

        # Initialize services
        self.cache_service = CacheService(
            self.config.REDIS_URL, self.config.REDIS_PASSWORD
        )
        self.call_automation_client = CallAutomationClient.from_connection_string(
            self.config.ACS_CONNECTION_STRING
        )
        self.call_handler = CallHandler(self.config, self.call_automation_client)
        self.openai_service = OpenAIService(self.config)

        # Initialize CosmosDBService
        self.cosmosdb_service = CosmosDBService(self.config)

        # Initialize event handlers with all required services
        self.event_handlers = EventHandlers(
            call_handler=self.call_handler,
            cache_service=self.cache_service,
            openai_service=self.openai_service,
            cosmosdb_service=self.cosmosdb_service,
        )

        self.setup_routes()
        self.logger.info("Application initialized successfully V0.15")

    def setup_routes(self):
        """Set up application routes"""
        self.app.route("/")(self.hello)
        self.app.route("/robots933456.txt")(self.health_check)
        self.app.route("/api/callbacks/<context_id>", methods=["POST"])(
            self.handle_callback
        )
        self.app.route("/api/incomingCall", methods=["POST"])(
            self.incoming_call_handler
        )
        self.app.route("/api/initiateOutboundCall", methods=["POST"])(
            self.initiate_outbound_call
        )

    async def hello(self):
        """Health check endpoint"""
        self.logger.info("async def hello")
        return "Hello ACS Call Automation Service V0.15"

    async def health_check(self):
        """Health check endpoint for Azure App Service"""
        self.logger.info("health_check")
        return Response(
            response="Healthy", status=200, headers={"Content-Type": "text/plain"}
        )

    ## Add incoming_call_handler ##

    async def incoming_call_handler(self):
        """Handle incoming calls"""
        self.logger.info("incoming_call_handler")
        try:
            # Get the raw request data as JSON
            request_data = await request.get_json()
            self.logger.info(
                f"Received incoming call request: {json.dumps(request_data)}"
            )

            # If request_data is not a list, wrap it in a list
            if not isinstance(request_data, list):
                request_data = [request_data]

            for event_dict in request_data:
                self.logger.info(f"Processing event: {json.dumps(event_dict)}")

                # Create EventGridEvent directly from the dictionary
                try:
                    event = EventGridEvent.from_dict(event_dict)
                    self.logger.info(f"Parsed event: {event}")

                    if (
                        event.event_type
                        == SystemEventNames.EventGridSubscriptionValidationEventName
                    ):
                        self.logger.info("Handling validation event")
                        validation_code = event.data["validationCode"]
                        self.logger.info(f"Validation code: {validation_code}")
                        return Response(
                            response=json.dumps(
                                {"validationResponse": validation_code}
                            ),
                            status=StatusCodes.OK,
                            headers={"Content-Type": "application/json"},
                        )

                    elif event.event_type == EventTypes.INCOMING_CALL:
                        self.logger.info("Handling incoming call event")
                        await self._process_incoming_call(event)
                        return Response(status=StatusCodes.OK)

                except Exception as e:
                    self.logger.error(
                        f"Error processing event dict: {str(e)}", exc_info=True
                    )
                    return Response(
                        response=json.dumps(
                            {"error": "Error processing event", "details": str(e)}
                        ),
                        status=StatusCodes.SERVER_ERROR,
                        headers={"Content-Type": "application/json"},
                    )

            # If we get here, no events were processed
            return Response(
                response=json.dumps({"error": "No valid events found in request"}),
                status=StatusCodes.BAD_REQUEST,
                headers={"Content-Type": "application/json"},
            )

        except Exception as e:
            self.logger.error(
                f"Error in incoming call handler: {str(e)}", exc_info=True
            )
            return Response(
                response=json.dumps(
                    {"error": "Internal server error", "details": str(e)}
                ),
                status=StatusCodes.SERVER_ERROR,
                headers={"Content-Type": "application/json"},
            )

    ## Add outgoing_call_handler ##
    def _validate_payload(self, payload_dict: dict) -> None:
        """
        Validate the payload dictionary.
        Args:
            payload_dict (dict): The payload dictionary.
        Returns:
            None
        """
        required_keys = ApiPayloadKeysForValidation.API_KEYS

        for key in required_keys:
            if key not in payload_dict:
                raise ValueError(f"Missing required key: {key}")

    async def _wait_for_cache(self, key: str, timeout: int = 5):
        """Wait until the cache is set for a given key"""
        for _ in range(timeout):
            value = await self.cache_service.get(key)
            if value is not None:
                return True
            await asyncio.sleep(1)
        return False

    async def initiate_outbound_call(self):
        """Initiate an outbound call"""
        self.logger.info("initiate_outbound_call")
        try:
            # extract the payload
            payload_dict = await request.get_json()
            # validate against expected payload
            self._validate_payload(payload_dict=payload_dict)
            self.logger.info(f"Received payload: {json.dumps(payload_dict)}")

            # set the data in the cache for keys, job data and candidate data
            await self.cache_service.set(key="payload_dict", value=payload_dict)
            await self.cache_service.set(
                key="job_data_dict",
                value={
                    key: payload_dict[key]
                    for key in ApiPayloadKeysForValidation.JOB_DATA_KEYS
                },
            )
            await self.cache_service.set(
                key="candidate_data_dict",
                value={
                    key: payload_dict[key]
                    for key in ApiPayloadKeysForValidation.CANDIDATE_DATA_KEYS
                },
            )
            self.config.TARGET_CANDIDATE_PHONE_NUMBER = payload_dict.get("phone_number")

            # await for data to be cached asynchrounously
            # await self._wait_for_cache(key="payload_dict")

            # Get the target participant and source caller
            target_participant = PhoneNumberIdentifier(
                self.config.TARGET_CANDIDATE_PHONE_NUMBER
            )
            source_caller = PhoneNumberIdentifier(self.config.AGENT_PHONE_NUMBER)

            # Generate a callback URI with a unique context ID
            guid = uuid.uuid4()
            query_parameters = urlencode(
                {"calleeId": self.config.TARGET_CANDIDATE_PHONE_NUMBER}
            )
            callback_uri = (
                f"{self.config.CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"
            )

            call_connection_properties = self.call_automation_client.create_call(
                target_participant=target_participant,
                source_caller_id_number=source_caller,
                # call_invite=call_invite,
                callback_url=callback_uri,
                cognitive_services_endpoint=self.config.COGNITIVE_SERVICE_ENDPOINT,
            )

            self.logger.info(
                f"Outbound call initiated with connection ID: {call_connection_properties.call_connection_id}"
            )

            # Simulate an Event Grid event for the outbound call
            event = EventGridEvent(
                subject="OutboundCall",
                event_type=EventTypes.CALL_CONNECTED,
                data={
                    "callConnectionId": call_connection_properties.call_connection_id,
                    "to": {"rawId": self.config.TARGET_CANDIDATE_PHONE_NUMBER},
                    "outboundCallContext": None,  # Not needed for outbound calls
                },
                data_version="1.0",
            )
            await self._process_outbound_call(event)

            return Response(status=StatusCodes.OK)

        except Exception as e:
            self.logger.error(
                f"Error initiating outbound call: {str(e)}", exc_info=True
            )
            return Response(
                response=json.dumps(
                    {"error": "Error initiating outbound call", "details": str(e)}
                ),
                status=StatusCodes.SERVER_ERROR,
                headers={"Content-Type": "application/json"},
            )

    async def _process_outbound_call(self, event: EventGridEvent):
        """Process outbound call connected event"""
        self.logger.info("_process_outbound_call event")

            # Extract call_connection_id from event data
            call_connection_id = event.data.get("callConnectionId")
            if not call_connection_id:
                self.logger.error("Missing callConnectionId in event data")
                return  # Or handle appropriately

            callee_id = self.config.TARGET_CANDIDATE_PHONE_NUMBER
            session_id = self.cosmosdb_service.create_new_session(
                callee_id, event.data["callConnectionId"]
            )

            call_connection_id = event.data["callConnectionId"]

            await self.cache_service.set(
                "participant_id", self.config.TARGET_CANDIDATE_PHONE_NUMBER
            )

            await self.cache_service.set("current_session_id", session_id)
            await self.cache_service.set("current_call_id", call_connection_id)

            self.logger.info(f"New session created with ID: {session_id}")

            # Start the conversation
            # await self.event_handlers.handle_call_connected(event, callee_id)
        except Exception as e:
            self.logger.error(
                f"Error in _process_outbound_call: {str(e)}", exc_info=True
            )
            raise

    async def handle_callback(self, context_id: str):
        """Handle callbacks from the call automation service"""
        try:
            self.logger.info(f"Received callback for context: {context_id}")
            events = await request.json
            self.logger.info(f"Callback events: {json.dumps(events)}")

            # caller_id = self._normalize_caller_id(request.args.get("callerId", ""))
            callee_id = await self.cache_service.get("participant_id")
            # self.logger.info(f"Processing callback for caller: {caller_id}")

            for event_dict in events:
                event = CloudEvent.from_dict(event_dict)
                call_connection_id = event.data.get("callConnectionId")
                if not call_connection_id:
                    self.logger.error("Missing callConnectionId in event data")
                    continue  # Skip processing this event if no call_connection_id is found

                self.logger.info(
                    f"[Call Connection ID: {call_connection_id}] Received callback for context: {context_id}"
                )
                self.logger.info(
                    f"[Call Connection ID: {call_connection_id}] Event data: {json.dumps(event_dict)}"
                )

                # Retrieve callee_id or any other necessary data using call_connection_id
                callee_id = await self.cache_service.get(
                    f"participant_id:{call_connection_id}"
                )

                try:
                    await self._process_event(event, callee_id)
                except Exception as e:
                    self.logger.error(
                        f"Error processing event type {event.type}: {str(e)}",
                        exc_info=True,
                    )

            return Response(status=StatusCodes.OK)

        except Exception as e:
            self.logger.error(f"Error in callback handler: {str(e)}", exc_info=True)
            return Response(
                response={"error": "Internal server error", "details": str(e)},
                status=StatusCodes.SERVER_ERROR,
            )

    async def _process_event(self, event: CloudEvent, caller_id: str):
        """Process different types of events"""
        self.logger.info(f"Processing event type: {event.type}")
        event_handlers = {
            EventTypes.CALL_CONNECTED: self.event_handlers.handle_call_connected,
            EventTypes.RECOGNIZE_COMPLETED: self.event_handlers.handle_recognize_completed,
            EventTypes.PLAY_COMPLETED: self.event_handlers.handle_play_completed,
            EventTypes.RECOGNIZE_FAILED: self.event_handlers.handle_recognize_failed,
            EventTypes.CALL_DISCONNECTED: self.event_handlers.handle_call_disconnected,
            EventTypes.PARTICIPANTS_UPDATED: self.event_handlers.handle_participants_updated,
        }

        handler = event_handlers.get(event.type)
        if handler:
            try:
                await handler(event, caller_id)
            except Exception as e:
                self.logger.error(
                    f"Error in event handler for {event.type}: {str(e)}", exc_info=True
                )
                raise
        else:
            self.logger.warning(f"No handler found for event type: {event.type}")

    async def _answer_call_async(self, incoming_call_context, callback_url):
        self.logger.info("_answer_call_async event")
        # Directly assign without awaiting
        return self.call_automation_client.answer_call(
            incoming_call_context=incoming_call_context,
            cognitive_services_endpoint=self.config.COGNITIVE_SERVICE_ENDPOINT,
            callback_url=callback_url,
        )

    async def _process_incoming_call(self, event: EventGridEvent):
        """Process incoming call event"""
        self.logger.info("_process_incoming_call event")

        try:
            caller_id = self._extract_caller_id(event.data)
            # session_id = self.cosmosdb_service.create_new_session(caller_id, event.data["callConnectionId"])

            incoming_call_context = event.data["incomingCallContext"]
            callback_uri = self._generate_callback_uri(caller_id)

            # Call _answer_call_async and remove await
            answer_call_result = await self._answer_call_async(
                incoming_call_context, callback_uri
            )

            # Log the successful call connection
            self.logger.info(
                f"Answered call for connection id: {answer_call_result.call_connection_id}"
            )

        except Exception as e:
            self.logger.error(
                f"Error in _process_incoming_call: {str(e)}", exc_info=True
            )
            raise

    def _extract_caller_id(self, event_data: dict) -> str:
        """Extract caller ID from event data"""
        if event_data["from"]["kind"] == "phoneNumber":
            return event_data["from"]["phoneNumber"]["value"]
        return event_data["from"]["rawId"]

    def _generate_callback_uri(self, caller_id: str) -> str:
        """Generate callback URI for the call"""
        guid = uuid.uuid4()
        query_parameters = urlencode({"callerId": caller_id})
        return f"{self.config.CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

    def _normalize_caller_id(self, caller_id: str) -> str:
        """Normalize caller ID format"""
        caller_id = caller_id.strip()
        if "+" not in caller_id:
            caller_id = "+" + caller_id
        return caller_id

    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the application"""
        self.app.run(host=host, port=port)
