from typing import Optional
import uuid
import json
from urllib.parse import urlencode, urlparse, urlunparse
from quart import Quart, Response, request, websocket
from quart_schema import validate_request, QuartSchema
from azure.eventgrid import EventGridEvent, SystemEventNames
from azure.core.messaging import CloudEvent
from azure.communication.callautomation import (
    MediaStreamingOptions,
    AudioFormat,
    MediaStreamingTransportType,
    MediaStreamingContentType,
    MediaStreamingAudioChannelType,
    PhoneNumberIdentifier
    )
from azure.communication.callautomation.aio import CallAutomationClient
from azure.core.exceptions import AzureError
import asyncio

from src.config.settings import Config
from src.config.constants import EventTypes, StatusCodes, ApiPayloadKeysForValidation
from src.services.call_handler import CallHandler
from src.services.cache_service import CacheService
#from src.core.event_handlers import EventHandlers
from src.services.cosmosdb_service import CosmosDBService
from src.services.openai_realtime_service import OpenAIRealtimeService
from src.services.ai_voice_service import AsyncAzureVoiceLiveService
from src.services.ai_voice_agent_service import AsyncAzureVoiceLiveAgentService
from src.models.models import OutboundCallPayloadModel
from src.utils.logger import setup_logger
from src.interfaces.ai_voice_base import AIVoiceBase


class CallAutomationApp:
    """Main application class"""

    def __init__(self):
        self.app = Quart(__name__)
        QuartSchema(app=self.app)
        self.config = Config()
        self.logger = setup_logger(__name__)
        
        # Setup CORS for HTTP routes (not WebSocket)
        self._setup_cors()

        # Initialize services
        self.cache_service = CacheService(
            self.config.REDIS_URL, self.config.REDIS_PASSWORD
        )
        
        self.call_automation_client = CallAutomationClient.from_connection_string(
            self.config.ACS_CONNECTION_STRING
        )
        
        # Initialize CosmosDBService
        self.cosmosdb_service = CosmosDBService(self.config)
        
        # Initialize both AI voice services (non-agent and agent)
        self.ai_voice_service: AIVoiceBase = AsyncAzureVoiceLiveService(
            config=self.config,
            logger=self.logger,
            cache=self.cache_service,
            cosmosdb_service=self.cosmosdb_service,
        )
        
        self.ai_voice_agent_service: AIVoiceBase = AsyncAzureVoiceLiveAgentService(
            config=self.config,
            cache=self.cache_service,
            logger=self.logger,
            cosmosdb_service=self.cosmosdb_service,
        )
        
        #self.openai_realtime_service = OpenAIRealtimeService(
        #    self.config, 
        #    self.cache_service, 
        #    self.logger
        #)

        self.setup_routes()
        self.logger.info("Application initialized successfully V0.15")
    
    def _setup_cors(self):
        """Setup CORS headers for HTTP routes without breaking WebSocket"""
        @self.app.after_request
        async def add_cors_headers(response):
            # Only add CORS headers to HTTP responses, not WebSocket upgrades
            if response.status_code != 101:  # 101 = WebSocket upgrade
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response.headers['Access-Control-Max-Age'] = '3600'
            return response
        
        @self.app.before_request
        async def handle_preflight():
            # Handle OPTIONS preflight requests
            if request.method == 'OPTIONS':
                response = Response('', 200)
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response.headers['Access-Control-Max-Age'] = '3600'
                return response

    def setup_routes(self):
        """Set up application routes"""
        self.app.route("/")(
            self.hello
        )
        self.app.route("/robots933456.txt")(
            self.health_check
        )
        self.app.route("/api/callbacks", methods=["POST"])(
            self.handle_callback
        )
        self.app.route("/api/callbacks/<context_id>", methods=["POST"])(
            self.handle_callback
        )
        self.app.route("/api/incomingCall", methods=["POST"])(
            self.incoming_call_handler
        )
        self.app.route("/api/initiateOutboundCall", methods=["POST"])(
            self.initiate_outbound_call
        )
        self.app.route("/api/transcript/<session_id>", methods=["GET"])(
            self.get_transcript
        )
        self.app.route("/api/personas", methods=["GET"])(
            self.get_personas
        )
        self.app.route("/api/tool_response", methods=["POST"])(
            self.send_tool_response
        )
        self.app.websocket("/ws/<call_id>")(
            self.ws
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
    
    async def get_transcript(self, session_id: str):
        """Get transcript for a specific session from Cosmos DB"""
        self.logger.info(f"Fetching transcript for session: {session_id}")
        try:
            if not self.cosmosdb_service or not self.cosmosdb_service.enabled:
                return Response(
                    response=json.dumps({
                        "callerId": "Unknown",
                        "callStartTime": None,
                        "callEndTime": None,
                        "conversation": []
                    }),
                    status=StatusCodes.OK,
                    headers={"Content-Type": "application/json"},
                )
            
            # Query Cosmos DB for the session
            query = f"SELECT * FROM c WHERE c.id = '{session_id}'"
            items = list(self.cosmosdb_service.container.query_items(
                query=query, 
                enable_cross_partition_query=True
            ))
            
            if not items:
                # Return empty conversation instead of error
                return Response(
                    response=json.dumps({
                        "id": session_id,
                        "callerId": "Unknown",
                        "callStartTime": None,
                        "callEndTime": None,
                        "conversation": []
                    }),
                    status=StatusCodes.OK,
                    headers={"Content-Type": "application/json"},
                )
            
            session_data = items[0]
            return Response(
                response=json.dumps(session_data),
                status=StatusCodes.OK,
                headers={"Content-Type": "application/json"},
            )
            
        except Exception as e:
            # Log the error but return empty conversation so UI doesn't break
            self.logger.error(f"Error fetching transcript (Cosmos DB may be blocked): {str(e)}")
            return Response(
                response=json.dumps({
                    "id": session_id,
                    "callerId": "Unknown",
                    "callStartTime": None,
                    "callEndTime": None,
                    "conversation": [],
                    "error": "Cosmos DB unavailable - check firewall settings"
                }),
                status=StatusCodes.OK,
                headers={"Content-Type": "application/json"},
            )
    
    async def get_personas(self):
        """Get available AI personas from constants"""
        try:
            from src.config.constants import OpenAIPrompts
            
            # Get all available personas with friendly names
            personas = []
            for key in OpenAIPrompts.system_message_dict.keys():
                # Convert key to friendly display name
                display_name = key.replace('_', ' ').title()
                personas.append({
                    "value": key,
                    "label": display_name
                })
            
            return Response(
                response=json.dumps({"personas": personas}),
                status=StatusCodes.OK,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            self.logger.error(f"Error fetching personas: {str(e)}", exc_info=True)
            return Response(
                response=json.dumps({
                    "error": "Failed to fetch personas",
                    "personas": [{"value": "default", "label": "Default"}]
                }),
                status=StatusCodes.OK,
                headers={"Content-Type": "application/json"},
            )
    
    async def send_tool_response(self):
        """Send tool response back to the AI agent"""
        try:
            data = await request.get_json()
            session_id = data.get('session_id')
            tool_call_id = data.get('tool_call_id')
            result = data.get('result', {})
            use_agent_mode = data.get('use_agent_mode', False)
            
            if not session_id or not tool_call_id:
                return Response(
                    response=json.dumps({"error": "session_id and tool_call_id are required"}),
                    status=StatusCodes.BAD_REQUEST,
                    headers={"Content-Type": "application/json"},
                )
            
            # Get the websocket call ID from the ACS call connection ID
            websocket_call_id = await self.cache_service.get(f"websocket_id:{session_id}")
            if not websocket_call_id:
                return Response(
                    response=json.dumps({"error": "Active call session not found"}),
                    status=StatusCodes.BAD_REQUEST,
                    headers={"Content-Type": "application/json"},
                )
            
            # Send the tool response through the appropriate AI service
            if use_agent_mode:
                await self.ai_voice_agent_service.send_tool_response(
                    websocket_call_id, tool_call_id, result
                )
            else:
                await self.ai_voice_service.send_tool_response(
                    websocket_call_id, tool_call_id, result
                )
            
            self.logger.info(f"Tool response sent for session {session_id}, tool_call_id {tool_call_id}")
            
            return Response(
                response=json.dumps({"success": True}),
                status=StatusCodes.OK,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            self.logger.error(f"Error sending tool response: {str(e)}", exc_info=True)
            return Response(
                response=json.dumps({"error": str(e)}),
                status=StatusCodes.SERVER_ERROR,
                headers={"Content-Type": "application/json"},
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
                    
                    elif event.event_type in [
                        EventTypes.CALL_STARTED,
                        EventTypes.CALL_ENDED,
                        EventTypes.CALL_PARTICIPANT_ADDED,
                        EventTypes.CALL_PARTICIPANT_REMOVED,
                        EventTypes.CALL_CONNECTED,
                        EventTypes.CALL_DISCONNECTED
                    ]:
                        self.logger.info(f"Acknowledging event: {event.event_type}")
                        return Response(status=StatusCodes.OK)
                    
                    else:
                        self.logger.warning(f"Unhandled event type: {event.event_type}")
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

    ## Unused function - not necessary, validation done via pydantic models ##
    def _validate_payload(
        self, 
        payload_dict: dict, 
        required_keys:Optional[list[str]]=None
    ) -> None:
        """
        Validate the payload dictionary contgains the required keys. 
        If required_keys is None, the default list of required keys is used.
        If any key is missing, raise a ValueError.
        ### Args:
            - `payload_dict` (`dict`): The payload dictionary.
            - `required_keys` (`list[str]`): The list of required keys. Default uses `["phone_number", "candidate_name", "candidate_data", "job_data"]`. Pass an empty list to skip validation.
        ### Returns:
            `None`
        """
        #if required_keys is None:
        #    required_keys=[
        #        "phone_number", 
        #        "candidate_name", 
        #        "candidate_data",
        #        "job_data"
        #    ]
        #for key in required_keys:
        #    if key not in payload_dict:
        #        raise ValueError(f"Missing required key: {key}")
        pass
         
            
    ## unused function - not necessary ##
    async def _wait_for_cache(self, key: str, timeout:int=5):
        """Wait until the cache is set for a given key"""
        for _ in range(timeout):
            value = await self.cache_service.get(key)
            if value is not None:
                return True
            await asyncio.sleep(1)
        return False


    #@validate_request(OutboundCallPayloadModel)
    async def initiate_outbound_call(self):
        """Initiate an outbound call, with OutboundCallPayloadModel as the payload validation"""
        self.logger.info("Initiating outbound call...")
        try:
            # extract the payload
            payload_dict = await request.get_json()
            # validate against expected payload
            #self._validate_payload(payload_dict=payload_dict)
            #self._validate_payload(payload_dict=payload_dict)
            self.logger.info(f"Received payload: {json.dumps(payload_dict)}")
            
            # check the phone number is been passed
            if payload_dict.get("phone_number") is not None:
                self.config.TARGET_CANDIDATE_PHONE_NUMBER = payload_dict.get("phone_number")
            elif self.config.TARGET_CANDIDATE_PHONE_NUMBER is None:
                raise ValueError(
                    "Missing phone number in payload or environment variable 'TARGET_CANDIDATE_PHONE_NUMBER'"
                )
            
            # Get the target participant and source caller            
            target_participant = PhoneNumberIdentifier(self.config.TARGET_CANDIDATE_PHONE_NUMBER)
            # TODO: Expand to pool of agents
            source_caller = PhoneNumberIdentifier(self.config.AGENT_PHONE_NUMBER)
            
            # Generate a callback URI with a unique context ID
            guid = uuid.uuid4()
            parsed_url = urlparse(self.config.CALLBACK_EVENTS_URI)
            websocket_url = urlunparse(('wss',parsed_url.netloc,f'/ws/{guid}','', '', ''))
            
            self.logger.info(f"WebSocket URL for ACS: {websocket_url}")
            self.logger.info(f"Callback Events URI: {self.config.CALLBACK_EVENTS_URI}")
            
            # Create media streaming options (preview feature)
            media_streaming_options = MediaStreamingOptions(
                transport_url=websocket_url,
                transport_type=MediaStreamingTransportType.WEBSOCKET,
                content_type=MediaStreamingContentType.AUDIO,
                audio_channel_type=MediaStreamingAudioChannelType.MIXED,
                start_media_streaming=True,
                enable_bidirectional=True,
                audio_format=AudioFormat.PCM24_K_MONO
            ) 
            
            # create the ob call
            try:
                new_call_created = await self.call_automation_client.create_call(
                    target_participant=target_participant, 
                    source_caller_id_number=source_caller,
                    callback_url=self.config.CALLBACK_EVENTS_URI,
                    cognitive_services_endpoint=self.config.COGNITIVE_SERVICE_ENDPOINT,
                    media_streaming=media_streaming_options
                )
            except Exception as e:
                self.logger.error(f"Error creating call: {e}")
                
                
            call_connection_id = new_call_created.call_connection_id
            
            # log the call connection id
            self.logger.info(
                f"Created call with connection id: {call_connection_id}"
            )  
            
            # create a new session in CosmosDB
            session_id = self.cosmosdb_service.create_new_session(
                caller_id=self.config.TARGET_CANDIDATE_PHONE_NUMBER, 
                acs_connection_id=call_connection_id
            )
            self.logger.info(f"Created new Cosmos DB session with id: {session_id}")
            
            # Store data using call_connection_id as the namespace on Redis
            await self.cache_service.set(f"current_call_id:{call_connection_id}", call_connection_id)
            await self.cache_service.set(f"current_session_id:{call_connection_id}", session_id)
            await self.cache_service.set(f"websocket_id:{call_connection_id}", str(guid))
            await self.cache_service.set(f"acs_call_id:{str(guid)}", call_connection_id) # not great... what if they clash when scaling?
            await self.cache_service.set(f"caller_id:{call_connection_id}", self.config.TARGET_CANDIDATE_PHONE_NUMBER)
            await self.cache_service.set(f"payload_dict:{call_connection_id}", payload_dict)
            
            # Store use_agent flag for this call (convert to boolean)
            use_agent = payload_dict.get("use_agent", False)
            if isinstance(use_agent, str):
                use_agent = use_agent.lower() == "true"
            await self.cache_service.set(f"use_agent:{str(guid)}", use_agent)
            self.logger.info(f"Call {call_connection_id} using {'agent' if use_agent else 'non-agent'} mode")

            # Return success with call details for UI, but also support old clients expecting 200 OK
            response_data = {
                "success": True,
                "call_connection_id": call_connection_id,
                "session_id": session_id,
                "message": "Call initiated successfully"
            }
            
            return Response(
                response=json.dumps(response_data),
                status=StatusCodes.OK,
                headers={"Content-Type": "application/json"}
            )

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


    async def handle_callback(self, context_id: Optional[str] = None):
        """Handle callbacks from the call automation service"""
        try:
            self.logger.info(f"Received callback for context: {context_id}")
            events = await request.json
            self.logger.info(f"Callback events: {json.dumps(events)}")

            for event in await request.json:
                # Parsing callback events
                #global call_connection_id
                event_data = event['data']
                call_connection_id = event_data["callConnectionId"]
                self.logger.info(f"Received Event:-> {event['type']}, Correlation Id:-> {event_data['correlationId']}, CallConnectionId:-> {call_connection_id}")
                
                if event['type'] == "Microsoft.Communication.CallConnected":
                    call_connection_properties = await self.call_automation_client.get_call_connection(call_connection_id).get_call_properties()
                    media_streaming_subscription = call_connection_properties.media_streaming_subscription
                    self.logger.info(f"MediaStreamingSubscription:--> {media_streaming_subscription}")
                    self.logger.info(f"Received CallConnected event for connection id: {call_connection_id}")
                    self.logger.info("CORRELATION ID:--> %s", event_data["correlationId"])
                    self.logger.info("CALL CONNECTION ID:--> %s", event_data["callConnectionId"])
                    print("call connected for call connection id: ", call_connection_id)
                    
                elif event['type'] == "Microsoft.Communication.MediaStreamingStarted":
                    self.logger.info(f"Media streaming content type:--> {event_data['mediaStreamingUpdate']['contentType']}")
                    self.logger.info(f"Media streaming status:--> {event_data['mediaStreamingUpdate']['mediaStreamingStatus']}")
                    self.logger.info(f"Media streaming status details:--> {event_data['mediaStreamingUpdate']['mediaStreamingStatusDetails']}")
            
                elif event['type'] == "Microsoft.Communication.MediaStreamingStopped":
                    self.logger.info(f"Media streaming content type:--> {event_data['mediaStreamingUpdate']['contentType']}")
                    self.logger.info(f"Media streaming status:--> {event_data['mediaStreamingUpdate']['mediaStreamingStatus']}")
                    self.logger.info(f"Media streaming status details:--> {event_data['mediaStreamingUpdate']['mediaStreamingStatusDetails']}")
                
                elif event['type'] == "Microsoft.Communication.MediaStreamingFailed":
                    self.logger.info(f"Code:->{event_data['resultInformation']['code']}, Subcode:-> {event_data['resultInformation']['subCode']}")
                    self.logger.info(f"Message:->{event_data['resultInformation']['message']}")
                
                elif event['type'] == "Microsoft.Communication.CallDisconnected":
                    #acs_client.get_call_connection(call_connection_id).hangup()
                    # Clean up resources from the appropriate service
                    websocket_id = await self.cache_service.get(f'websocket_id:{call_connection_id}')
                    use_agent = await self.cache_service.get(f"use_agent:{websocket_id}")
                    
                    if use_agent:
                        await self.ai_voice_agent_service.cleanup_call_resources(call_id=call_connection_id)
                    else:
                        await self.ai_voice_service.cleanup_call_resources(call_id=call_connection_id)
                    
                    self.logger.info(f"Received CallDisconnected event for connection id: {call_connection_id}")
                    
                return Response(status=200)

        except Exception as e:
            self.logger.error(f"Error in callback handler: {str(e)}", exc_info=True)
            return Response(
                response={"error": "Internal server error", "details": str(e)},
                status=StatusCodes.SERVER_ERROR,
            )
            
            
    async def ws(self, call_id:str):
        """WebSocket handler - supports both agent and non-agent modes with automatic fallback"""
        self.logger.info(f"🔌 WebSocket connection attempt for call {call_id}")
        print(f"🔌 Client connected to WebSocket for call {call_id}")
        
        # Determine which service to use based on use_agent flag
        use_agent = await self.cache_service.get(f"use_agent:{call_id}")
        self.logger.info(f"Using {'agent' if use_agent else 'non-agent'} mode for WebSocket call {call_id}")
        
        # Select the appropriate AI voice service with fallback
        if use_agent:
            try:
                service = self.ai_voice_agent_service
                self.logger.info(f"Attempting to use Agent Service for call {call_id}")
                
                # Initialize the service - if this fails, fall back
                await service.init_incoming_websocket(call_id, websocket)
                await service.start_client(call_id)
                self.logger.info(f"Successfully started Agent Service for call {call_id}")
                
            except Exception as e:
                self.logger.warning(f"Agent Service failed for call {call_id}: {e}")
                self.logger.info(f"Falling back to Non-Agent Service for call {call_id}")
                
                # Clean up failed agent resources to prevent lingering errors
                try:
                    await self.ai_voice_agent_service.cleanup_call_resources(call_id, is_acs_id=False)
                except Exception as cleanup_error:
                    self.logger.debug(f"Agent cleanup error (expected): {cleanup_error}")
                
                # Fallback to non-agent mode
                service = self.ai_voice_service
                await service.init_incoming_websocket(call_id, websocket)
                await service.start_client(call_id)
                
                # Update cache to reflect actual service used
                await self.cache_service.set(f"use_agent:{call_id}", False)
        else:
            service = self.ai_voice_service
            self.logger.info(f"Using Non-Agent Service for call {call_id}")
            await service.init_incoming_websocket(call_id, websocket)
            await service.start_client(call_id)
        
        # Handle WebSocket messages
        while websocket:
            try:
                data = await websocket.receive()
                await service.acs_to_oai(
                    call_id=call_id, 
                    stream_data=data
                )
            except Exception as e:
                print(f"WebSocket connection closed for call {call_id}: {e}")
                break

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the application"""
        self.app.run(host=host, port=port)
