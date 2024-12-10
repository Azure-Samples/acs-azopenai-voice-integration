import requests
import json
import uuid
from datetime import datetime

# Base URL for the API
BASE_URL = "https://tf-ai-aivoice-dev-aiapi.azurewebsites.net/api"


# Utility function to create event payload
def create_event(event_type, data):
    return {
        "eventType": event_type,
        "data": data,
        "id": str(uuid.uuid4()),
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "dataVersion": "1.0",
        "metadataVersion": "1",
    }


# Simulate Microsoft EventGrid Subscription Validation Event
def simulate_validation_event():
    validation_code = "123456"
    event_data = {"validationCode": validation_code}
    event = create_event("Microsoft.EventGrid.SubscriptionValidationEvent", event_data)

    response = requests.post(
        f"{BASE_URL}/incomingCall",
        headers={"Content-Type": "application/json"},
        data=json.dumps([event]),
    )
    print("Validation Event Response:")
    print(response.status_code, response.text)


# Simulate Incoming Call Event
def simulate_incoming_call_event():
    event = [
        {
            "id": str(uuid.uuid4()),  # Generate a unique ID
            "topic": "/subscriptions/{subscription-id}/resourcegroups/{group-name}/providers/microsoft.communication/communicationservices/{communication-services-resource-name}",
            "subject": "/caller/8:acs:caller-id/recipient/8:acs:recipient-id",
            "data": {
                "to": {
                    "kind": "communicationUser",
                    "rawId": "8:acs:recipient-id",
                    "communicationUser": {"id": "8:acs:recipient-id"},
                },
                "from": {
                    "kind": "communicationUser",
                    "rawId": "8:acs:caller-id",
                    "communicationUser": {"id": "8:acs:caller-id"},
                },
                "serverCallId": "server-call-id",
                "callerDisplayName": "John Doe",
                "customContext": {"voipHeaders": {"voipHeaderName": "value"}},
                "incomingCallContext": "sample-incoming-call-context",  # Replace with a valid context string
                "correlationId": str(uuid.uuid4()),  # Generate a unique correlation ID
            },
            "eventType": "Microsoft.Communication.IncomingCall",
            "dataVersion": "1.0",
            "metadataVersion": "1",
            "eventTime": datetime.utcnow().isoformat()
            + "Z",  # Current time in ISO format
        }
    ]

    response = requests.post(
        f"{BASE_URL}/incomingCall",
        headers={"Content-Type": "application/json"},
        data=json.dumps(event),
    )

    print("Incoming Call Event Response:")
    print(response.status_code, response.text)


# Simulate Callbacks for Context ID
def simulate_callback(context_id):
    callback_events = [
        {
            "type": "CallConnected",
            "source": "test-source",
            "data": {"connectionId": "test-connection-id"},
            "id": str(uuid.uuid4()),
        }
    ]

    response = requests.post(
        f"{BASE_URL}/callbacks/{context_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(callback_events),
    )
    print("Callback Event Response:")
    print(response.status_code, response.text)


# Execute simulations
if __name__ == "__main__":
    print("Simulating API Calls...\n")
    simulate_validation_event()
    simulate_incoming_call_event()
    simulate_callback(context_id="example-context-id")
