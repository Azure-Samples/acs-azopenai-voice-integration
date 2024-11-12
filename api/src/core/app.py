import uuid
import json
from urllib.parse import urlencode
from quart import Quart, Response, request
from azure.eventgrid import EventGridEvent, SystemEventNames
from azure.core.messaging import CloudEvent
from azure.communication.callautomation import CallAutomationClient
from azure.core.exceptions import AzureError

from src.config.settings import Config
from src.config.constants import EventTypes, StatusCodes
from src.services.call_handler import CallHandler
from src.services.cache_service import CacheService
from src.services.openai_service import OpenAIService
from src.core.event_handlers import EventHandlers

from src.utils.logger import setup_logger

class CallAutomationApp:
    """Main application class"""
    def __init__(self):
        self.app = Quart(__name__)
        self.config = Config()
        self.logger = setup_logger(__name__)
        
        # Initialize services
        self.cache_service = CacheService()
        self.call_automation_client = CallAutomationClient.from_connection_string(
            self.config.ACS_CONNECTION_STRING
        )
        self.call_handler = CallHandler(
            self.config, 
            self.call_automation_client
        )
        self.openai_service = OpenAIService(self.config)
        
        # Initialize event handlers with all required services
        self.event_handlers = EventHandlers(
            call_handler=self.call_handler,
            cache_service=self.cache_service,
            openai_service=self.openai_service
        )
        
        self.setup_routes()
        self.logger.info("Application initialized successfully V0.15")

    def setup_routes(self):
        """Set up application routes"""
        self.app.route("/")(self.hello)
        self.app.route("/robots933456.txt")(self.health_check)
        
        self.app.route("/api/callbacks/<context_id>", methods=["POST"])(self.handle_callback)

        self.app.route("/api/incomingCall", methods=["POST"])(self.incoming_call_handler)

    async def hello(self):
        """Health check endpoint"""
        self.logger.info("async def hello")
        return "Hello ACS Call Automation Service V0.15"

    async def health_check(self):
        """Health check endpoint for Azure App Service"""
        self.logger.info("health_check")
        return Response(
            response="Healthy",
            status=200,
            headers={"Content-Type": "text/plain"}
        )
    
    async def incoming_call_handler(self):
        """Handle incoming calls"""
        self.logger.info("incoming_call_handler")
        try:
            request_data = await request.json
            self.logger.info(f"Received incoming call request: {json.dumps(request_data)}")
            
            for event_dict in request_data:
                event = EventGridEvent.from_dict(event_dict)
                self.logger.info(f"event = {event}")
                
                if event.event_type == SystemEventNames.EventGridSubscriptionValidationEventName:
                    self.logger.info(f"event.event_type: {SystemEventNames.EventGridSubscriptionValidationEventName}")
                    validation_code = event.data["validationCode"]
                    self.logger.info(f"Handling validation request with code: {validation_code}")
                    return Response(
                        response={"validationResponse": validation_code},
                        status=StatusCodes.OK
                    )
                
                elif event.event_type == EventTypes.INCOMING_CALL:
                    try:
                        self.logger.info(f"event.event_type: {EventTypes.INCOMING_CALL}")
                        await self._process_incoming_call(event)
                        return Response(status=StatusCodes.OK)
                    except AzureError as ae:
                        self.logger.error(f"Azure service error in incoming call: {str(ae)}", exc_info=True)
                        return Response(
                            response={"error": "Azure service error", "details": str(ae)},
                            status=StatusCodes.SERVER_ERROR
                        )
                    except Exception as e:
                        self.logger.error(f"Error processing incoming call: {str(e)}", exc_info=True)
                        return Response(
                            response={"error": "Internal server error", "details": str(e)},
                            status=StatusCodes.SERVER_ERROR
                        )
        except Exception as e:
            self.logger.error(f"Error in incoming call handler: {str(e)}", exc_info=True)
            return Response(
                response={"error": "Internal server error", "details": str(e)},
                status=StatusCodes.SERVER_ERROR
            )

    async def handle_callback(self, context_id: str):
        """Handle callbacks from the call automation service"""
        try:
            self.logger.info(f"Received callback for context: {context_id}")
            events = await request.json
            self.logger.info(f"Callback events: {json.dumps(events)}")
            
            caller_id = self._normalize_caller_id(request.args.get("callerId", ""))
            self.logger.info(f"Processing callback for caller: {caller_id}")
            
            for event_dict in events:
                event = CloudEvent.from_dict(event_dict)
                try:
                    await self._process_event(event, caller_id)
                except Exception as e:
                    self.logger.error(
                        f"Error processing event type {event.type}: {str(e)}", 
                        exc_info=True
                    )
            
            return Response(status=StatusCodes.OK)
            
        except Exception as e:
            self.logger.error(f"Error in callback handler: {str(e)}", exc_info=True)
            return Response(
                response={"error": "Internal server error", "details": str(e)},
                status=StatusCodes.SERVER_ERROR
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
            EventTypes.PARTICIPANTS_UPDATED: self.event_handlers.handle_participants_updated
        }
        
        handler = event_handlers.get(event.type)
        if handler:
            try:
                await handler(event, caller_id)
            except Exception as e:
                self.logger.error(
                    f"Error in event handler for {event.type}: {str(e)}", 
                    exc_info=True
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
            incoming_call_context = event.data["incomingCallContext"]
            callback_uri = self._generate_callback_uri(caller_id)

            # Call _answer_call_async and remove await
            answer_call_result = await self._answer_call_async(incoming_call_context, callback_uri)
            
            # Log the successful call connection
            self.logger.info(f"Answered call for connection id: {answer_call_result.call_connection_id}")
            
        except Exception as e:
            self.logger.error(f"Error in _process_incoming_call: {str(e)}", exc_info=True)
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

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the application"""
        self.app.run(host=host, port=port)

    # async def check_services_health(self):
    #     """Check the health of all dependent services"""
    #     health_status = {
    #         "status": "healthy",
    #         "services": {
    #             "acs": "healthy",
    #             "openai": "healthy",
    #             "cache": "healthy"
    #         },
    #         "details": {}
    #     }
        
    #     try:
    #         # Check ACS Connection
    #         await self.call_automation_client.get_supported_languages()
    #     except Exception as e:
    #         health_status["services"]["acs"] = "unhealthy"
    #         health_status["details"]["acs_error"] = str(e)
    #         health_status["status"] = "degraded"

    #     try:
    #         # Check OpenAI Connection
    #         await self.openai_service.get_chat_completion("test")
    #     except Exception as e:
    #         health_status["services"]["openai"] = "unhealthy"
    #         health_status["details"]["openai_error"] = str(e)
    #         health_status["status"] = "degraded"

    #     try:
    #         # Check Cache Service
    #         await self.cache_service.get("test")
    #     except Exception as e:
    #         health_status["services"]["cache"] = "unhealthy"
    #         health_status["details"]["cache_error"] = str(e)
    #         health_status["status"] = "degraded"

    #     return health_status

    # async def health_check(self):
    #     """Health check endpoint"""
    #     try:
    #         # For Azure's specific health probe
    #         if request.path == "/robots933456.txt":
    #             return Response(
    #                 response="Healthy",
    #                 status=200,
    #                 headers={"Content-Type": "text/plain"}
    #             )

    #         # For detailed health check
    #         health_status = await self.check_services_health()
            
    #         return Response(
    #             response=json.dumps(health_status),
    #             status=200 if health_status["status"] == "healthy" else 503,
    #             headers={"Content-Type": "application/json"}
    #         )
    #     except Exception as e:
    #         return Response(
    #             response=json.dumps({
    #                 "status": "unhealthy",
    #                 "error": str(e)
    #             }),
    #             status=503,
    #             headers={"Content-Type": "application/json"}
    #         )        