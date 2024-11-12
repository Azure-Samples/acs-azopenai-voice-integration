import os
from pyexpat import model
import uuid
from urllib.parse import urlencode, urljoin
from azure.eventgrid import EventGridEvent, SystemEventNames
import requests
from quart import Quart, Response, request, json
from logging import INFO
import re
from azure.communication.callautomation import TextSource, RecognizeInputType, PhoneNumberIdentifier
from typing import Optional
from azure.communication.callautomation.aio import CallAutomationClient
from azure.core.messaging import CloudEvent

from openai import OpenAI
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv

from langchain_community.chat_message_histories import ChatMessageHistory
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

HELLO_PROMPT = "Hello, I am Emily V6 one of the voice assistants at SThree. We have a job role that matches your skillset. Do you have a few minutes to discuss it?"
TIMEOUT_SILENCE_PROMPT = (
    "I am sorry, I did not hear anything. Please could you confirm you are there"
)
GOODBYE_PROMPT = "Thank you for your time. Have a great day. Bye for now!"
GOODBYE_CONTEXT = "Goodbye"
#--------------------------------------------


CHAT_RESPONSE_EXTRACT_PATTERN = (
    r"\s*Content:(.*)\s*Score:(.*\d+)\s*Intent:(.*)\s*Category:(.*)"
)

call_automation_client = CallAutomationClient.from_connection_string(
    ACS_CONNECTION_STRING
)

recording_id = None
recording_chunks_location = []
max_retry = 2
is_call_terminated = False

app = Quart(__name__)


cache = {
    "start_message": "Great! Let's get started.",
    "location_question": "Could you please let me know where you’re currently based? It’ll help me understand how the role aligns with your location.",
    "thank_you_message": "Great! For the next steps, I'll follow up with you via email. Thank you so much for your time today, and I look forward to staying in touch. Have a wonderful day!",
    "job_details": "Its at JP Morgan, London, UK. The role is for a Vice President in AI.",
    "user interested": "Does the job role I just mentioned sound interesting to you?",
    "job_location": "London, United Kingdom",
    "job_role": "AI Vice President",
    "competency_questions": "what is your experience with leading GenAI applications?",
    "waiting_message": "Please wait while I find the details.",
    "escalation_message": "I'm really sorry, I do not have sufficient information to be able to answer this right now. Let me check with the team and get back to you.",
    "job_details_shared": False,
    "candidate_location": "",
    "competency_questions_asked": False,
    "consent_message": "Before we proceed, are you okay for me to record this conversation? We will use it to improve our services and will not be shared with any third party.",
}

SYSTEM_MESSAGE = """
## CONTEXT ## 
You are Emily, one of the new voice Assistants at SThree. You are helping a job seeker with a job role that matches her skillset. You will ask her some questions and share some details about the role. You will also answer her questions and share some information. Always wait for the job seeker's response before proceeding to the next part of the conversation.
## CONVERSATION FLOW ## 
You initiate the conversation with greetings. Then let the candidate (job seeker) know that we have a job role that matches their skillset. Do you have a few minutes to discuss it? If the candidate agrees, thank them and ask if they are okay with you recording the conversation. Let them know that we will use it to improve our services and not share it outside SThree. If the user agrees, thank them, and ask them about their location. If the user's location is within 50km of the job location, thank them for sharing and say, "The job role is located in {job_location}, so it might actually work nicely for you. Let me share some details about it." 
If not: find out where they're located, and see if they're open to commuting to London if the company reimburses the travel expenses. 
If the user says yes: proceed by sharing a summary of the job role and ask the candidate if it sounds interesting to them. If the candidate agrees, then ask the candidate to give a brief overview of their skills and experience relevant to the job role. Once the candidate provides this, thank them and say you actually think the candidate will be a very good match for this role. And you just have a couple of questions for them. ask a competency-based question. Once the candidate provides a response, thank them and reiterate how you think they are a very good match for the role and if they agree, you would like to forward their CV to your client organization. Ask them to share their availability and once they do, thank them and end the conversation politely, wishing them a good day and thanking them for their time.
## GUIDELINES ## 
- Address the candidate by their first name during the conversation. 
- Maintain a polite and friendly tone like a real-world recruiter. Do not repeat questions until the candidate asks you to. 
- Use the job role description from the data sources to ground the competency-based questions, job role summary, and responses to the candidate's questions about the job role. 
- For any questions you do not have an answer for, let the candidate know that you will come back to them and check with the hiring manager. 
- When using the content or reading the content from the job description, do not read out the markdowns or special characters. Read it out as a human would do.
"""


def clean_response(response):
    response = re.sub(r'\[.*?\]\(.*?\)', '', response)
    response = re.sub(r'\[.*?\]', '', response)
    response = re.sub(r'[^a-zA-Z0-9\s\.\,\?\!]', '', response)
    response = re.sub(r'\s+', ' ', response).strip()
    return response

def extract_location(user_response):
    doc = nlp(user_response)
    for ent in doc.ents:
        if ent.label_ == "GPE":
            return ent.text
    return None


def get_coordinates(location_name):
    url = f"https://atlas.microsoft.com/search/address/json?api-version=1.0&query={location_name}&subscription-key={AZURE_MAPS_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['results']:
        coordinates = data['results'][0]['position']
        return [coordinates['lat'], coordinates['lon']]
    return None

job_coords = get_coordinates(cache["job_location"])

# Initialize LangChain Chat Message History
chat_history = ChatMessageHistory()
chat_history.add_message({"role": "system", "content": SYSTEM_MESSAGE})


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
    return await get_chat_completions_async(SYSTEM_MESSAGE, speech_input)


async def handle_play(call_connection_id: str, text_to_play: str, context: str) -> None:
    """
    Handle playing text with simplified async pattern
    """
    try:
        # Validate the text
        if not text_to_play or not text_to_play.strip():
            print(f"Warning: Empty text provided for play in context {context}")
            text_to_play = "I apologize, but I'm having trouble responding. Let me try again."
        
        if len(text_to_play) > MAX_TEXT_LENGTH:
            text_to_play = text_to_play[:MAX_TEXT_LENGTH]
        
        # Create play source
        play_source = TextSource(
            text=text_to_play,
            voice_name="en-US-AvaMultilingualNeural"
        )
        
        # Get connection and play
        connection = call_automation_client.get_call_connection(call_connection_id)
        await connection.play_media_to_all(
            play_source,
            operation_context=context
        )
        
        print(f"Successfully played message in context: {context}")
        
    except Exception as ex:
        print(f"Error in handle_play: {ex}")
        error_code = getattr(ex, 'status_code', None)
        
        if error_code == 400:
            print(f"Cognitive Services error in context {context}: {str(ex)}")
            try:
                # Try fallback voice
                alternate_source = TextSource(
                    text=text_to_play,
                    voice_name="en-US-AvaMultilingualNeural"
                )
                await connection.play_media_to_all(
                    alternate_source,
                    operation_context=context
                )
            except Exception as fallback_ex:
                print(f"Fallback play failed: {fallback_ex}")

async def handle_recognize(
    reply_text: str, 
    caller_id: str, 
    call_connection_id: str, 
    context: str = ""
) -> Optional[dict]:
    """
    Handle recognition with simplified async pattern
    """
    try:
        # Validate inputs
        if not reply_text or not reply_text.strip():
            print(f"Warning: Empty reply text in context {context}")
            reply_text = "I apologize, but I need to repeat the question. Could you please respond?"
            
        if len(reply_text) > MAX_TEXT_LENGTH:
            reply_text = reply_text[:MAX_TEXT_LENGTH]
            
        play_source = TextSource(
            text=reply_text,
            voice_name="en-US-AvaMultilingualNeural"
        )
        
        connection_client = call_automation_client.get_call_connection(call_connection_id)
        if not caller_id or not isinstance(caller_id, str):
            raise ValueError(f"Invalid caller ID: {caller_id}")
            
        # Execute recognition
        result = await connection_client.start_recognizing_media(
            input_type=RecognizeInputType.SPEECH,
            target_participant=PhoneNumberIdentifier(caller_id),
            end_silence_timeout=0.5,
            play_prompt=play_source,
            operation_context=context,
        )
        
        print(f"handle_recognize : data={result}")
        return result
        
    except Exception as ex:
        print(f"Error in recognize: {ex}")
        error_code = getattr(ex, 'status_code', None)
        
        if error_code == 400:
            try:
                # Try fallback voice
                alternate_source = TextSource(
                    text=reply_text,
                    voice_name="en-US-AvaMultilingualNeural"
                )
                result = await connection_client.start_recognizing_media(
                    input_type=RecognizeInputType.SPEECH,
                    target_participant=PhoneNumberIdentifier(caller_id),
                    end_silence_timeout=0.5,
                    play_prompt=alternate_source,
                    operation_context=context,
                )
                return result
            except Exception as fallback_ex:
                print(f"Fallback recognize failed: {fallback_ex}")
                return None
        
        return None
             

async def handle_hangup(call_connection_id):
    await call_automation_client.get_call_connection(call_connection_id).hang_up(
        is_for_everyone=True
    )


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
            print(f"{event.type} event received for call connection id")
            caller_id = request.args.get("callerId").strip()
            print(f"caller_id id {caller_id}")

            if "+" not in caller_id:
                caller_id = "+" + caller_id.strip()

            print(f"call connected : data={event.data}")

            # Check event type and handle accordingly
            if event.type == "Microsoft.Communication.CallConnected":
                await handle_recognize(
                    HELLO_PROMPT,
                    caller_id,
                    event.data["callConnectionId"],
                    context="InitialGreeting",
                )

            elif event.type == "Microsoft.Communication.RecognizeCompleted":
                if event.data["recognitionType"] == "speech":
                    speech_text = event.data["speechResult"]["speech"]
                    print(f"Recognition completed, speech_text =%s", speech_text)
                    chat_history.add_message({"role": "user", "content": speech_text})

                    # Handle conversation flow based on candidate's response
                    if event.data["operationContext"] == "InitialGreeting":
                        if any(
                            keyword in speech_text.lower()
                            for keyword in ["no", "not interested", "busy"]
                        ):
                            await handle_play(
                                event.data["callConnectionId"],
                                "No problem, I understand. Have a good day!",
                                GOODBYE_CONTEXT,
                            )
                            await handle_hangup(event.data["callConnectionId"])
                        else:
                            await handle_recognize(
                                cache.get("consent_message"),
                                caller_id,
                                event.data["callConnectionId"],
                                context="ConsentRequest",
                            )

                    elif event.data["operationContext"] == "ConsentRequest":
                        if "no" in speech_text.lower():
                            decline_message = await get_chat_gpt_response(
                                "Candidate does not consent to recording. Generate a response to politely end the call."
                            )
                            await handle_play(
                                event.data["callConnectionId"],
                                decline_message,
                                GOODBYE_CONTEXT,
                            )
                            await handle_hangup(event.data["callConnectionId"])
                        else:
                            start_message = await get_chat_gpt_response(
                                "Generate a warm response to thank the candidate for consenting and start the conversation."
                            )
                            # await handle_play(event.data['callConnectionId'], start_message, context="ConsentRequest")
                            combined_message = f"{start_message} {LOCATION_QUESTION}"
                            await handle_recognize(
                                combined_message,
                                caller_id,
                                event.data["callConnectionId"],
                                context="LocationRequest",
                            )

                            # Wait for playback to finish before proceeding

                    elif event.data["operationContext"] == "LocationRequest":
                        # Handle location response
                        location = ""#extract_location(speech_text)
                        if location:
                            candidate_coords = [1.4556,1.35325] #get_coordinates(location)
                            if candidate_coords and job_coords:
                                distance = 100 #calculate_distance(candidate_coords, job_coords)

                                if distance <= 50:
                                    await handle_play(
                                        event.data["callConnectionId"],
                                        f"The job role is located in {JOB_LOCATION}, so it might actually work nicely for you. Let me share some details about it.",
                                        context="LocationRequest",
                                    )
                                    # Wait for playback to finish before proceeding
                                else:
                                    await handle_recognize(
                                        "The job is located in London. Are you open to commuting if travel expenses are reimbursed?",
                                        caller_id,
                                        event.data["callConnectionId"],
                                        context="CommuteQuestion",
                                    )
                            else:
                                # If unable to get coordinates, handle gracefully
                                await handle_play(
                                    event.data["callConnectionId"],
                                    "Thank you for sharing. Let me share some details about the job.",
                                    context="LocationRequest",
                                )
                                # Wait for playback to finish before proceeding
                        else:
                            # If location extraction fails
                            await handle_play(
                                event.data["callConnectionId"],
                                "Thank you for sharing. Let me share some details about the job.",
                                context="LocationRequest",
                            )
                            # Wait for playback to finish before proceeding

                    elif event.data["operationContext"] == "CommuteQuestion":
                        if any(
                            keyword in speech_text.lower()
                            for keyword in ["yes", "okay", "fine", "sure"]
                        ):
                            print("User is open to commuting")
                            await handle_play(
                                event.data["callConnectionId"],
                                "Great! Let me share some details about the job.",
                                context="LocationRequest",
                            )
                            # Wait for playback to finish before proceeding
                        else:
                            await handle_play(
                                event.data["callConnectionId"],
                                "No problem, thank you for your time. Have a good rest of the day!",
                                GOODBYE_CONTEXT,
                            )
                            await handle_hangup(event.data["callConnectionId"])

                    elif event.data["operationContext"] == "JobInterest":
                        if any(
                            keyword in speech_text.lower()
                            for keyword in ["no", "not interested"]
                        ):
                            await handle_play(
                                event.data["callConnectionId"],
                                "No problem, thank you for your time. Have a great day!",
                                GOODBYE_CONTEXT,
                            )
                            await handle_hangup(event.data["callConnectionId"])
                        else:
                            await handle_play(
                                event.data["callConnectionId"],
                                "Thank you so much for your interest! I'd like to ask you a few questions about your experience and skills to understand how well they align with this opportunity.",
                                context="JobInterest",
                            )
                            # Wait for playback to finish before proceeding

                    elif event.data["operationContext"] == "CompetencyResponse":
                        # Acknowledge their experience
                        chat_history.add_message(
                            {"role": "user", "content": speech_text}
                        )
                        gpt_follow_up = await get_chat_gpt_response(
                            f"Acknowledge candidate experience {speech_text}. Only provide a positive acknowledgment, without any additional questions or prompts."
                        )
                        chat_history.add_message(
                            {"role": "assistant", "content": gpt_follow_up}
                        )
                        # Change context to "NextSteps" to avoid conflict
                        # Play the follow-up acknowledgment message
                        await handle_play(
                            event.data["callConnectionId"],
                            gpt_follow_up,
                            context="Acknowledgement",
                        )

                        # Ask about next steps after acknowledging
                        next_steps_message = "I actually think you will be a good match for this role. Would it be okay if I forwarded your CV to our client organization?"
                        await handle_recognize(
                            next_steps_message,
                            caller_id,
                            event.data["callConnectionId"],
                            context="NextStepsRequest",
                        )  # Wait for playback to finish before proceeding

                    elif event.data["operationContext"] == "NextStepsRequest":
                        if any(
                            keyword in speech_text.lower()
                            for keyword in ["yes", "okay", "sure"]
                        ):
                            await handle_play(
                                event.data["callConnectionId"],
                                THANK_YOU_MESSAGE,
                                GOODBYE_CONTEXT,
                            )
                            await handle_hangup(event.data["callConnectionId"])
                        else:
                            await handle_play(
                                event.data["callConnectionId"],
                                "No problem, thank you for your time. Have a great day!",
                                GOODBYE_CONTEXT,
                            )
                            await handle_hangup(event.data["callConnectionId"])

                elif event.data["recognitionType"] == "dtmf":
                    # Handle DTMF inputs if necessary
                    pass

            elif event.type == "Microsoft.Communication.PlayCompleted":
                context = event.data["operationContext"]
                if context == "ConsentRequest":
                    # After thanking the candidate, ask for location
                    await handle_recognize(
                        cache.get("location"),
                        caller_id,
                        event.data["callConnectionId"],
                        context="LocationRequest",
                    )

                elif context == "LocationRequest":
                    # Now play the actual JOB_DETAILS
                    await handle_play(
                        event.data["callConnectionId"],
                        cache.get("job_details"),
                        context="JobDetails",
                    )

                elif context == "JobDetails":
                    # After JOB_DETAILS is played, proceed to ask if the user is interested
                    await handle_recognize(
                        cache.get("user interested"),
                        caller_id,
                        event.data["callConnectionId"],
                        context="JobInterest",
                    )

                elif context == "JobInterest":
                    # After introducing competency questions, ask the question
                    await handle_recognize(
                        cache.get("competency_questions"),
                        caller_id,
                        event.data["callConnectionId"],
                        context="CompetencyResponse",
                    )

                elif context == "CompetencyResponse":
                    # After acknowledging skills, proceed to next steps
                    await handle_play(
                        event.data["callConnectionId"],
                        "I actually think you could be a very good match for this role. Would it be okay if I forwarded your CV to our client organization?",
                        context="NextStepsResponse",
                    )
                    await handle_recognize(
                        "Please let me know if that's okay with you.",
                        caller_id,
                        event.data["callConnectionId"],
                        context="NextStepsResponse",
                    )

                elif context == "Acknowledgement":
                    # After acknowledging skills, proceed to ask about the next steps
                    next_steps_message = "I actually think you could be a very good match for this role. Would it be okay if I forwarded your CV to our client organization?"
                    await handle_recognize(
                        next_steps_message,
                        caller_id,
                        event.data["callConnectionId"],
                        context="NextStepsRequest",
                    )
                # elif context == "NextSteps":
                #     # After acknowledging skills, proceed to next steps
                #     await handle_play(event.data['callConnectionId'], "I actually think you could be a very good match for this role. Would it be okay if I forwarded your CV to our client organization?", context="NextStepsResponse")
                #     await handle_recognize("Please let me know if that's okay with you.", caller_id, event.data['callConnectionId'], context="NextStepsResponse")

                elif context == "NextStepsResponse":
                    if (
                        "yes" in speech_text.lower()
                        or "okay" in speech_text.lower()
                        or "sure" in speech_text.lower()
                    ):
                        await handle_play(
                            event.data["callConnectionId"],
                            THANK_YOU_MESSAGE,
                            GOODBYE_CONTEXT,
                        )
                    else:
                        await handle_play(
                            event.data["callConnectionId"],
                            "No problem, thank you for your time. Have a great day!",
                            GOODBYE_CONTEXT,
                        )

                elif context == "GOODBYE_CONTEXT":
                    if not is_call_terminated:
                        # After playing goodbye message, hang up the call
                        await handle_hangup(event.data["callConnectionId"])
                        is_call_terminated = True

            elif event.type == "Microsoft.Communication.RecognizeFailed":
                resultInformation = event.data["resultInformation"]
                reasonCode = resultInformation["subCode"]
                context = event.data["operationContext"]
                global max_retry
                if reasonCode == 8510 and max_retry > 0:
                    await handle_recognize(
                        TIMEOUT_SILENCE_PROMPT,
                        caller_id,
                        event.data["callConnectionId"],
                        context=context,
                    )
                    max_retry -= 1
                else:
                    await handle_play(
                        event.data["callConnectionId"], GOODBYE_PROMPT, GOODBYE_CONTEXT
                    )
                    await handle_hangup(event.data["callConnectionId"])

            elif event.type == "Microsoft.Communication.CallDisconnected":
                # Clean up resources or perform any necessary actions on call disconnect
                print("Call disconnected for call connection id: %s",event.data["callConnectionId"])

        return Response(status=200)
    except Exception as ex:
        print("Error in event handling: %s", ex)

@app.route("/")
def hello():
    return "Hello ACS S3!..test"


if __name__ == "__main__":
    app.logger.setLevel(INFO)
    # app.run(port=8081)
    app.run(host="0.0.0.0", port=8000)