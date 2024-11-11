import os
from pyexpat import model
import uuid
from urllib.parse import urlencode, urljoin
from azure.eventgrid import EventGridEvent, SystemEventNames
import requests
from quart import Quart, Response, request, json
from logging import INFO
import re
from azure.communication.callautomation import (
    PhoneNumberIdentifier,
    RecognizeInputType,
    TextSource,
)

from azure.communication.callautomation.aio import CallAutomationClient
from azure.core.messaging import CloudEvent

from openai import OpenAI
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv

load_dotenv()
# Your ACS resource connection string
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")

# Cognitive service endpoint
COGNITIVE_SERVICE_ENDPOINT = os.getenv("COGNITIVE_SERVICE_ENDPOINT")

# Cognitive service endpoint
AZURE_OPENAI_SERVICE_KEY = os.getenv("AZURE_OPENAI_SERVICE_KEY")

# Open AI service endpoint
AZURE_OPENAI_SERVICE_ENDPOINT = os.getenv("AZURE_OPENAI_SERVICE_ENDPOINT")


# Azure Open AI Deployment Model Name
AZURE_OPENAI_DEPLOYMENT_MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_MODEL_NAME")


# Azure Open AI Deployment Model
AZURE_OPENAI_DEPLOYMENT_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_MODEL")


# Agent Phone Number
AGENT_PHONE_NUMBER = "+448081098061"

# Callback events URI to handle callback events.
CALLBACK_URI_HOST = "https://app-api-tf-ai-aivoice-dev-api.azurewebsites.net"
CALLBACK_EVENTS_URI = CALLBACK_URI_HOST + "/api/callbacks"
#--------------------------------------------

MAX_TEXT_LENGTH = 400
LOCATION_QUESTION = "Could you please let me know where you’re currently based? "
THANK_YOU_MESSAGE = "Great! For the next steps, I'll follow up with you via email. Thank you so much for your time today, and I look forward to staying in touch. Have a wonderful day!"
JOB_LOCATION = "London"
WAITING_MESSAGE = "Please wait while I find the details."
ESCALATION_MESSAGE = "I'm really sorry, I do not have sufficient information to be able to answer this right now. Let me check with the team and get back to you."

#--------------------------------------------
ANSWER_PROMPT_SYSTEM_TEMPLATE = """ 
    You are an assistant designed to answer the customer query and analyze the sentiment score from the customer tone. 
    You also need to determine the intent of the customer query and classify it into categories such as sales, marketing, shopping, etc.
    Use a scale of 1-10 (10 being highest) to rate the sentiment score. 
    Use the below format, replacing the text in brackets with the result. Do not include the brackets in the output: 
    Content:[Answer the customer query briefly and clearly in two lines and ask if there is anything else you can help with] 
    Score:[Sentiment score of the customer tone] 
    Intent:[Determine the intent of the customer query] 
    Category:[Classify the intent into one of the categories]
    """

CONNECT_AGENT_PROMPT = "I'm sorry, I was not able to assist you with your request. Let me transfer you to an agent who can help you further. Please hold the line, and I willl connect you shortly."
CALLTRANSFER_FAILURE_PROMPT = "It looks like I can not connect you to an agent right now, but we will get the next available agent to call you back as soon as possible."
AGENT_PHONE_NUMBER_EMPTY_PROMPT = "I am sorry, we are currently experiencing high call volumes and all of our agents are currently busy. Our next available agent will call you back as soon as possible."
END_CALL_PHRASE_TO_CONNECT_AGENT = (
    "Sure, please stay on the line. I am going to transfer you to an agent."
)

TRANSFER_FAILED_CONTEXT = "TransferFailed"
CONNECT_AGENT_CONTEXT = "ConnectAgent"

#--------------------------------------------

HELLO_PROMPT = "Hello, I am Emily V6 one of the voice assistants at SThree. We have a job role that matches your skillset. Do you have a few minutes to discuss it?"
TIMEOUT_SILENCE_PROMPT = (
    "I am sorry, I did not hear anything. Please could you confirm you are there"
)
GOODBYE_PROMPT = "Thank you for your time. Have a great day. Bye for now!"
GOODBYE_CONTEXT = "Goodbye"
MAX_TEXT_LENGTH = 400
LOCATION_QUESTION = "Could you please let me know where you’re currently based? "
THANK_YOU_MESSAGE = "Great! For the next steps, I'll follow up with you via email. Thank you so much for your time today, and I look forward to staying in touch. Have a wonderful day!"
WAITING_MESSAGE = "Please wait while I find the details."
ESCALATION_MESSAGE = "I'm really sorry, I do not have sufficient information to be able to answer this right now. Let me check with the team and get back to you."



CHAT_RESPONSE_EXTRACT_PATTERN = (
    r"\s*Content:(.*)\s*Score:(.*\d+)\s*Intent:(.*)\s*Category:(.*)"
)

call_automation_client = CallAutomationClient.from_connection_string(
    ACS_CONNECTION_STRING
)

recording_id = None
recording_chunks_location = []
max_retry = 2

import openai
# openai.api_key = AZURE_OPENAI_SERVICE_KEY
# openai.api_base = AZURE_OPENAI_SERVICE_ENDPOINT  # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
# openai.api_type = "azure"
# openai.api_version = "2024-08-06"  # this may change in the future

app = Quart(__name__)



client = AsyncAzureOpenAI(
    api_key=AZURE_OPENAI_SERVICE_KEY,
    api_version="2024-08-01-preview",
    azure_endpoint=AZURE_OPENAI_SERVICE_ENDPOINT
)

async def get_chat_completions_async(system_prompt: str, user_prompt: str) -> str:
    """
    Get chat completions from Azure OpenAI
    """
    try:
        chat_request = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"In less than 200 characters: respond to this question: {user_prompt}?"
            }
        ]
        global response_content

        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_MODEL_NAME,
            messages=chat_request,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as ex:
        print(f"Error in OpenAI API call: {ex}")
        return ""

async def get_chat_gpt_response(speech_input):
    return await get_chat_completions_async(ANSWER_PROMPT_SYSTEM_TEMPLATE, speech_input)


async def handle_recognize(replyText, callerId, call_connection_id, context=""):
    play_source = TextSource(text=replyText, voice_name="en-US-NancyNeural")
    connection_client = call_automation_client.get_call_connection(call_connection_id)
    try:
        recognize_result = await connection_client.start_recognizing_media(
            input_type=RecognizeInputType.SPEECH,
            target_participant=PhoneNumberIdentifier(callerId),
            end_silence_timeout=5,
            play_prompt=play_source,
            operation_context=context,
        )
        print(f"handle_recognize : data={recognize_result}")
    except Exception as ex:
        print(f"Error in recognize: {ex}")


async def handle_play(call_connection_id, text_to_play, context):
    play_source = TextSource(text=text_to_play, voice_name="en-US-NancyNeural")
    await call_automation_client.get_call_connection(
        call_connection_id
    ).play_media_to_all(play_source, operation_context=context)


async def handle_hangup(call_connection_id):
    await call_automation_client.get_call_connection(call_connection_id).hang_up(
        is_for_everyone=True
    )


async def detect_escalate_to_agent_intent(speech_text, logger):
    return await has_intent_async(
        user_query=speech_text, intent_description="talk to agent", logger=logger
    )


async def has_intent_async(user_query, intent_description, logger):
    is_match = False
    system_prompt = "You are a helpful assistant"
    combined_prompt = (
        f"In 1 word: does {user_query} have a similar meaning as {intent_description}?"
    )
    # combined_prompt = base_user_prompt.format(user_query, intent_description)
    response = await get_chat_completions_async(system_prompt, combined_prompt)
    if "yes" in response.lower():
        is_match = True
    logger.info(
        f"OpenAI results: is_match={is_match}, customer_query='{user_query}', intent_description='{intent_description}'"
    )
    return is_match


def get_sentiment_score(sentiment_score):
    pattern = r"(\d)+"
    regex = re.compile(pattern)
    match = regex.search(sentiment_score)
    return int(match.group()) if match else -1


async def answer_call_async(incoming_call_context, callback_url):
    return await call_automation_client.answer_call(
        incoming_call_context=incoming_call_context,
        cognitive_services_endpoint=COGNITIVE_SERVICE_ENDPOINT,
        callback_url=callback_url,
    )


@app.route("/api/incomingCall", methods=["POST"])
async def incoming_call_handler():
    for event_dict in await request.json:
        event = EventGridEvent.from_dict(event_dict)
        print(f"incoming event data --> {event.data}")
        if (
            event.event_type
            == SystemEventNames.EventGridSubscriptionValidationEventName
        ):
            print("Validating subscription")
            validation_code = event.data["validationCode"]
            validation_response = {"validationResponse": validation_code}
            return Response(response=json.dumps(validation_response), status=200)
        elif event.event_type == "Microsoft.Communication.IncomingCall":
            print(f"Incoming call received: data={event.data}")
            if event.data["from"]["kind"] == "phoneNumber":
                caller_id = event.data["from"]["phoneNumber"]["value"]
            else:
                caller_id = event.data["from"]["rawId"]
            print(f"incoming call handler caller id: {caller_id}" )
            incoming_call_context = event.data["incomingCallContext"]
            guid = uuid.uuid4()
            query_parameters = urlencode({"callerId": caller_id})
            callback_uri = f"{CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

            print(f"callback url: {callback_uri}" )

            answer_call_result = await answer_call_async(
                incoming_call_context, callback_uri)

            print(f"Answered call for connection id: {answer_call_result.call_connection_id}")
            return Response(status=200)


@app.route("/api/callbacks/<contextId>", methods=["POST"])
async def handle_callback(contextId):
    try:
        global caller_id
        print("Request Json: %s", await request.json)
        for event_dict in await request.json:
            event = CloudEvent.from_dict(event_dict)
            # print(f"{event.type} event received for call connection id: {event.data["callConnectionId"]}")
            print(f"{event.type} event received for call connection id")
            caller_id = request.args.get("callerId").strip()
            if "+" not in caller_id:
                caller_id = "+".strip() + caller_id.strip()

            print(f"call connected : data={event.data}")
            if event.type == "Microsoft.Communication.CallConnected":
                await handle_recognize(
                    HELLO_PROMPT,
                    caller_id,
                    event.data["callConnectionId"],
                    context="GetFreeFormText",
                )

            elif event.type == "Microsoft.Communication.RecognizeCompleted":
                if event.data["recognitionType"] == "speech":
                    speech_text = event.data["speechResult"]["speech"]
                    print(f"Recognition completed, speech_text = {speech_text}")
                    if speech_text is not None and len(speech_text) > 0:
                        detect_escalate = await detect_escalate_to_agent_intent(
                            speech_text=speech_text, logger=app.logger
                        )
                        if detect_escalate:
                            await handle_play(
                                call_connection_id=event.data["callConnectionId"],
                                text_to_play=END_CALL_PHRASE_TO_CONNECT_AGENT,
                                context=CONNECT_AGENT_CONTEXT,
                            )
                        else:
                            chat_gpt_response = await get_chat_gpt_response(speech_text)
                            print(f"Chat GPT response:{chat_gpt_response}")
                            regex = re.compile(CHAT_RESPONSE_EXTRACT_PATTERN)
                            match = regex.search(chat_gpt_response)
                            if match:
                                answer = match.group(1)
                                sentiment_score = match.group(2).strip()
                                intent = match.group(3)
                                category = match.group(4)
                                print(f"Chat GPT Answer={answer}, Sentiment Rating={sentiment_score}, Intent={intent}, Category={category}")
                                score = get_sentiment_score(sentiment_score)
                                print(f"Score={score}")
                                if -1 < score < 5:
                                    print(f"Score is less than 5")
                                    await handle_play(
                                        call_connection_id=event.data[
                                            "callConnectionId"
                                        ],
                                        text_to_play=CONNECT_AGENT_PROMPT,
                                        context=CONNECT_AGENT_CONTEXT,
                                    )
                                else:
                                    print(f"Score is more than 5")
                                    await handle_recognize(
                                        answer,
                                        caller_id,
                                        event.data["callConnectionId"],
                                        context="OpenAISample",
                                    )
                            else:
                                print("No match found")
                                await handle_recognize(
                                    chat_gpt_response,
                                    caller_id,
                                    event.data["callConnectionId"],
                                    context="OpenAISample",
                                )
            elif event.type == "Microsoft.Communication.RecognizeFailed":
                resultInformation = event.data["resultInformation"]
                reasonCode = resultInformation["subCode"]
                context = event.data["operationContext"]
                global max_retry
                if reasonCode == 8510 and 0 < max_retry:
                    await handle_recognize(
                        TIMEOUT_SILENCE_PROMPT,
                        caller_id,
                        event.data["callConnectionId"],
                    )
                    max_retry -= 1
                else:
                    await handle_play(
                        event.data["callConnectionId"], GOODBYE_PROMPT, GOODBYE_CONTEXT
                    )

            elif event.type == "Microsoft.Communication.PlayCompleted":
                context = event.data["operationContext"]
                if (
                    context.lower() == TRANSFER_FAILED_CONTEXT.lower()
                    or context.lower() == GOODBYE_CONTEXT.lower()
                ):
                    await handle_hangup(event.data["callConnectionId"])
                elif context.lower() == CONNECT_AGENT_CONTEXT.lower():
                    if not AGENT_PHONE_NUMBER or AGENT_PHONE_NUMBER.isspace():
                        print(f"Agent phone number is empty")
                        await handle_play(
                            call_connection_id=event.data["callConnectionId"],
                            text_to_play=AGENT_PHONE_NUMBER_EMPTY_PROMPT,
                        )
                    else:
                        print(f"Initializing the Call transfer...")
                        transfer_destination = PhoneNumberIdentifier(AGENT_PHONE_NUMBER)
                        call_connection_client = (
                            call_automation_client.get_call_connection(
                                call_connection_id=event.data["callConnectionId"]
                            )
                        )
                        await call_connection_client.transfer_call_to_participant(
                            target_participant=transfer_destination
                        )
                        print(f"Transfer call initiated: {context}")

            elif event.type == "Microsoft.Communication.CallTransferAccepted":
                print(
                    f"Call transfer accepted event received for connection id: {event.data['callConnectionId']}"
                )

            elif event.type == "Microsoft.Communication.CallTransferFailed":
                print(
                    f"Call transfer failed event received for connection id: {event.data['callConnectionId']}"
                )
                resultInformation = event.data["resultInformation"]
                sub_code = resultInformation["subCode"]
                # check for message extraction and code
                print(
                    f"Encountered error during call transfer, message=, code=, subCode={sub_code}"
                )
                await handle_play(
                    call_connection_id=event.data["callConnectionId"],
                    text_to_play=CALLTRANSFER_FAILURE_PROMPT,
                    context=TRANSFER_FAILED_CONTEXT,
                )
        return Response(status=200)
    except Exception as ex:
        print("error in event handling")


@app.route("/")
def hello():
    return "Hello ACS NEW!..test"


if __name__ == "__main__":
    app.logger.setLevel(INFO)
    # app.run(port=8081)
    app.run(host="0.0.0.0", port=8000)
