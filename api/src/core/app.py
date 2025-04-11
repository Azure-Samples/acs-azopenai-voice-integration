from typing import Optional
from typing import Optional
import uuid
import json
from urllib.parse import urlencode, urlparse, urlunparse
from quart import Quart, Response, request, websocket
from quart_schema import validate_request, QuartSchema
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
from src.models.models import OutboundCallPayloadModel
from src.utils.logger import setup_logger


class CallAutomationApp:
    """Main application class"""

    def __init__(self):
        self.app = Quart(__name__)
        QuartSchema(app=self.app)
        self.config = Config()
        self.logger = setup_logger(__name__)

        # Initialize services
        self.cache_service = CacheService(
            self.config.REDIS_URL, self.config.REDIS_PASSWORD
        )
        
        self.call_automation_client = CallAutomationClient.from_connection_string(
            self.config.ACS_CONNECTION_STRING
        )
        
        self.openai_realtime_service = OpenAIRealtimeService(
            self.config, 
            self.cache_service
        )

        # Initialize CosmosDBService
        self.cosmosdb_service = CosmosDBService(self.config)

        self.setup_routes()
        self.logger.info("Application initialized successfully V0.15")

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
        self.app.websocket("/ws/<call_id>")(
            self.ws
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
            await self.cache_service.set(f"payload_dict:{call_connection_id}", payload_dict)

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
                    await self.openai_realtime_service.cleanup_call_resources(call_id=call_connection_id)
                    self.logger.info(f"Received CallDisconnected event for connection id: {call_connection_id}")
                    
                return Response(status=200)

        except Exception as e:
            self.logger.error(f"Error in callback handler: {str(e)}", exc_info=True)
            return Response(
                response={"error": "Internal server error", "details": str(e)},
                status=StatusCodes.SERVER_ERROR,
            )
            
            
    async def ws(self, call_id:str):
        """WebSocket handler"""
        print(f"Client connected to WebSocket for call {call_id}")
        await self.openai_realtime_service.init_incoming_websocket(call_id, websocket)
        await self.openai_realtime_service.start_client(call_id)
        while websocket:
            try:
                data = await websocket.receive()
                await self.openai_realtime_service.acs_to_oai(
                    call_id=call_id, 
                    stream_data=data
                )
            except Exception as e:
                print(f"WebSocket connection closed for call {call_id}: {e}")
                break

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the application"""
        self.app.run(host=host, port=port)
