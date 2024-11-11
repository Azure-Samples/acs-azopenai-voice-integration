from quart import Quart, Response, request
import logging
import json
import uuid
from urllib.parse import urlencode
from azure.eventgrid import EventGridEvent, SystemEventNames
from azure.core.messaging import CloudEvent

logger = logging.getLogger(__name__)


class CallAutomationApp:
    def __init__(self, config, chat_service, call_service):
        self.config = config
        self.chat_service = chat_service
        self.call_service = call_service
        self.is_call_terminated = False
        self.app = Quart(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/api/incomingCall", methods=["POST"])
        async def incoming_call_handler():
            event_list = await request.json
            return await self.handle_incoming_call(event_list)

        @self.app.route("/api/callbacks/<context_id>", methods=["POST"])
        async def handle_callback(context_id):
            try:
                caller_id = request.args.get("callerId").strip()
                if "+" not in caller_id:
                    caller_id = "+" + caller_id.strip()
                event_list = await request.json
                for event_dict in event_list:
                    event = CloudEvent.from_dict(event_dict)
                    logger.info(
                        "%s event received for call connection ID: %s",
                        event.type,
                        event.data.get("callConnectionId"),
                    )
                    # Handle different event types (Add your event handling logic here)
            except Exception as ex:
                logger.error("Error in event handling: %s", ex)
            return Response(status=200)

        @self.app.route("/")
        async def hello():
            return "Hello ACS CallAutomation! Mous 6.0 is here!"

    async def handle_incoming_call(self, event_list):
        for event_dict in event_list:
            event = EventGridEvent.from_dict(event_dict)
            logger.info("Incoming event data: %s", event.data)

            if (
                event.event_type
                == SystemEventNames.EventGridSubscriptionValidationEventName
            ):
                return self.handle_validation(event.data)
            elif event.event_type == "Microsoft.Communication.IncomingCall":
                return await self.process_incoming_call(event.data)

    def handle_validation(self, data):
        validation_code = data["validationCode"]
        validation_response = {"validationResponse": validation_code}
        return Response(response=json.dumps(validation_response), status=200)

    async def process_incoming_call(self, data):
        caller_id = self.extract_caller_id(data)
        incoming_call_context = data["incomingCallContext"]
        callback_uri = self.generate_callback_uri(caller_id)

        answer_call_result = await self.call_service.client.answer_call(
            incoming_call_context=incoming_call_context,
            cognitive_services_endpoint=self.config.COGNITIVE_SERVICE_ENDPOINT,
            callback_url=callback_uri,
        )

        logger.info(
            "Answered call for connection ID: %s",
            answer_call_result.call_connection_id,
        )
        return Response(status=200)

    @staticmethod
    def extract_caller_id(data):
        if data["from"]["kind"] == "phoneNumber":
            return data["from"]["phoneNumber"]["value"]
        return data["from"]["rawId"]

    def generate_callback_uri(self, caller_id):
        guid = uuid.uuid4()
        query_parameters = urlencode({"callerId": caller_id})
        return f"{self.config.CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"
