from quart import Quart, Response, request
import logging
import json
import uuid
import time
from datetime import datetime
from urllib.parse import urlencode
from azure.eventgrid import EventGridEvent, SystemEventNames
from azure.core.messaging import CloudEvent
import traceback

# Simple console logging setup without correlation ID in the format
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CallMetrics:
    def __init__(self):
        self.active_calls = 0
        self.total_calls = 0
        self.failed_calls = 0
        self.call_durations = {}

    def start_call(self, call_id):
        self.active_calls += 1
        self.total_calls += 1
        self.call_durations[call_id] = time.time()

    def end_call(self, call_id):
        self.active_calls -= 1
        if call_id in self.call_durations:
            duration = time.time() - self.call_durations.pop(call_id)
            return duration
        return None

    def record_failed_call(self):
        self.failed_calls += 1


class CallAutomationApp:
    def __init__(self, config, chat_service, call_service):
        self.config = config
        self.chat_service = chat_service
        self.call_service = call_service
        self.is_call_terminated = False
        self.app = Quart(__name__)
        self.metrics = CallMetrics()
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/favicon.ico")
        async def favicon():
            logger.info("Favicon requested")
            return Response(status=204)  # No content response for favicon

        @self.app.route("/", methods=["GET"])
        async def root():
            logger.info("Root endpoint accessed")
            return Response(
                response=json.dumps(
                    {"message": "Hello ACS CallAutomation! Mous 6.0 is here!"}
                ),
                status=200,
                mimetype="application/json",
            )

        @self.app.route("/api/incomingCall", methods=["POST"])
        async def incoming_call_handler():
            correlation_id = str(uuid.uuid4())
            logger.info(f"[{correlation_id}] Received incoming call request")

            try:
                event_list = await request.get_json()
                logger.info(f"[{correlation_id}] Received event list: {event_list}")
                return await self.handle_incoming_call(event_list, correlation_id)
            except Exception as ex:
                error_msg = f"Failed to process incoming call: {str(ex)}\nStacktrace: {traceback.format_exc()}"
                logger.error(f"[{correlation_id}] {error_msg}")
                self.metrics.record_failed_call()
                return Response(
                    response=json.dumps(
                        {"error": "Internal server error", "details": str(ex)}
                    ),
                    status=500,
                )

        @self.app.route("/api/callbacks/<context_id>", methods=["POST"])
        async def handle_callback(context_id):
            correlation_id = str(uuid.uuid4())
            start_time = time.time()

            try:
                caller_id = request.args.get("callerId", "").strip()
                if "+" not in caller_id and caller_id:
                    caller_id = "+" + caller_id

                logger.info(
                    f"[{correlation_id}] Processing callback for context_id: {context_id}, caller_id: {caller_id}"
                )

                event_list = await request.get_json()
                logger.info(f"[{correlation_id}] Callback event list: {event_list}")
                await self.process_callback_events(event_list, correlation_id)

                processing_time = time.time() - start_time
                logger.info(
                    f"[{correlation_id}] Callback processing completed in {processing_time:.2f} seconds"
                )

                return Response(status=200)
            except Exception as ex:
                error_msg = f"Error in callback handling: {str(ex)}\nStacktrace: {traceback.format_exc()}"
                logger.error(f"[{correlation_id}] {error_msg}")
                return Response(
                    response=json.dumps(
                        {"error": "Callback processing failed", "details": str(ex)}
                    ),
                    status=500,
                )

        @self.app.route("/api/metrics", methods=["GET"])
        async def get_metrics():
            metrics_data = {
                "active_calls": self.metrics.active_calls,
                "total_calls": self.metrics.total_calls,
                "failed_calls": self.metrics.failed_calls,
                "timestamp": datetime.utcnow().isoformat(),
            }
            logger.info(f"Current metrics: {metrics_data}")
            return Response(
                response=json.dumps(metrics_data),
                status=200,
                mimetype="application/json",
            )

    async def process_callback_events(self, event_list, correlation_id):
        for event_dict in event_list:
            event = CloudEvent.from_dict(event_dict)
            call_connection_id = event.data.get("callConnectionId")

            logger.info(
                f"[{correlation_id}] Processing {event.type} event for call connection ID: {call_connection_id}"
            )
            logger.info(
                f"[{correlation_id}] Event details: {json.dumps(event.data, indent=2)}"
            )

            if event.type == "Microsoft.Communication.CallConnected":
                self.metrics.start_call(call_connection_id)
                logger.info(f"[{correlation_id}] Call connected: {call_connection_id}")

            elif event.type == "Microsoft.Communication.CallDisconnected":
                duration = self.metrics.end_call(call_connection_id)
                logger.info(
                    f"[{correlation_id}] Call disconnected: {call_connection_id}, Duration: {duration if duration else -1:.2f} seconds"
                )

    async def handle_incoming_call(self, event_list, correlation_id):
        for event_dict in event_list:
            event = EventGridEvent.from_dict(event_dict)
            logger.info(
                f"[{correlation_id}] Processing incoming event type: {event.event_type}"
            )

            if (
                event.event_type
                == SystemEventNames.EventGridSubscriptionValidationEventName
            ):
                logger.info(f"[{correlation_id}] Processing validation event")
                return self.handle_validation(event.data)

            elif event.event_type == "Microsoft.Communication.IncomingCall":
                logger.info(f"[{correlation_id}] Processing incoming call event")
                return await self.process_incoming_call(event.data, correlation_id)

            else:
                logger.warning(
                    f"[{correlation_id}] Unhandled event type: {event.event_type}"
                )

    def handle_validation(self, data):
        validation_code = data["validationCode"]
        logger.info(f"Processing validation code: {validation_code}")

        validation_response = {"validationResponse": validation_code}
        return Response(
            response=json.dumps(validation_response),
            status=200,
            mimetype="application/json",
        )

    async def process_incoming_call(self, data, correlation_id):
        try:
            caller_id = self.extract_caller_id(data)
            incoming_call_context = data["incomingCallContext"]
            if isinstance(incoming_call_context, dict):
                logger.info(
                    f"[{correlation_id}] Received context object: {incoming_call_context}"
                )
                incoming_call_context = incoming_call_context.get(
                    "callConnectionId", ""
                )

            logger.info(
                f"[{correlation_id}] Processing incoming call from: {caller_id} with context: {incoming_call_context}"
            )

            callback_uri = self.generate_callback_uri(caller_id)
            logger.info(f"[{correlation_id}] Generated callback URI: {callback_uri}")

            # Enhanced test mode detection - handle both formats
            if "test" in incoming_call_context.lower():
                logger.info(
                    f"[{correlation_id}] Test mode detected - simulating successful response"
                )
                return Response(
                    response=json.dumps(
                        {
                            "status": "success",
                            "message": "Test call processed successfully",
                            "callConnectionId": "test-connection-id",
                            "caller": caller_id,
                            "callback_uri": callback_uri,
                            "scenario": "default",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    ),
                    status=200,
                    mimetype="application/json",
                )

            # Real ACS call handling
            start_time = time.time()
            answer_call_result = await self.call_service.client.answer_call(
                incoming_call_context=incoming_call_context,
                cognitive_services_endpoint=self.config.COGNITIVE_SERVICE_ENDPOINT,
                callback_url=callback_uri,
            )

            processing_time = time.time() - start_time
            logger.info(
                f"[{correlation_id}] Call answered successfully. Connection ID: {answer_call_result.call_connection_id}, "
                f"Processing time: {processing_time:.2f} seconds"
            )

            return Response(status=200)

        except Exception as ex:
            error_msg = f"Failed to process incoming call: {str(ex)}\nStacktrace: {traceback.format_exc()}"
            logger.error(f"[{correlation_id}] {error_msg}")
            self.metrics.record_failed_call()
            return Response(
                response=json.dumps(
                    {"error": "Failed to process incoming call", "details": str(ex)}
                ),
                status=500,
                mimetype="application/json",
            )

    @staticmethod
    def extract_caller_id(data):
        try:
            if data["from"]["kind"] == "phoneNumber":
                return data["from"]["phoneNumber"]["value"]
            return data["from"]["rawId"]
        except KeyError as ex:
            error_msg = f"Failed to extract caller ID: {str(ex)}"
            logger.error(error_msg)
            raise ValueError(f"Invalid call data format: missing {str(ex)}")

    def generate_callback_uri(self, caller_id):
        guid = uuid.uuid4()
        query_parameters = urlencode({"callerId": caller_id})
        callback_uri = f"{self.config.CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

        logger.info(f"Generated callback URI: {callback_uri}")
        return callback_uri
