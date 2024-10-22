from pyexpat import model
import uuid
from urllib.parse import urlencode, urljoin
from azure.eventgrid import EventGridEvent, SystemEventNames
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import spacy
from geopy.distance import geodesic
from langchain.memory import ChatMessageHistory
import requests
from quart import Quart, Response, request, json
from logging import INFO
import re
from azure.communication.callautomation import (
    PhoneNumberIdentifier,
    RecognizeInputType,
    TextSource
    )

from azure.communication.callautomation.aio import (
    CallAutomationClient
    )
from azure.core.messaging import CloudEvent
import openai

from openai.api_resources import (
    ChatCompletion
)

# Your ACS resource connection string
ACS_CONNECTION_STRING = "endpoint=https://acs-sthree-v1.unitedstates.communication.azure.com/;accesskey=CcQcuZ5rKnMCAejy1qYv4mBLBKR9mm1CWOJH5CZlaa3d6pBt5cyjJQQJ99AJACULyCpkM33qAAAAAZCSOsL2"

# Cognitive service endpoint
COGNITIVE_SERVICE_ENDPOINT="https://sthree-multiservice.cognitiveservices.azure.com/"

# Cognitive service endpoint
AZURE_OPENAI_SERVICE_KEY = "4443459b8bb2468a9d31f963fbff17fe"

# Open AI service endpoint
AZURE_OPENAI_SERVICE_ENDPOINT="https://ai-aasthamadaanai2659490188550.openai.azure.com/"

# Azure Open AI Deployment Model Name
AZURE_OPENAI_DEPLOYMENT_MODEL_NAME="gpt-4o-2"

# Azure Open AI Deployment Model
AZURE_OPENAI_DEPLOYMENT_MODEL="gpt-4o"

# Agent Phone Number
AGENT_PHONE_NUMBER="+441904545541"
AZURE_SEARCH_INDEX = "vector-1727694978181"
SEARCH_KEY = "CzCRuO8Qa5KC2hsHvqVjeUqfEJz2aKKqfHnZ1FA8dzAzSeA8nbmI"
SEARCH_QUERY_KEY = "12n3xjsQgKOx46I9RuauXD9vtVJfOG2LYGXPITBIQLAzSeDIa4EP" # Your Azure Cognitive query key
AZURE_SEARCH_ENDPOINT = "https://cs-copilot.search.windows.net"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = "ada-sthree"  # The name of your deployment for embeddings in Azure OpenAI
AZURE_MAPS_KEY = "6jQv7YmIcRJTWTIfUtWitXYl9ahuN1aYxANsjRvwcPxQIENgFyCmJQQJ99AFACYeBjFJ0deGAAAgAZMPYjT5"
# Callback events URI to handle callback events.
CALLBACK_URI_HOST = "https://g9rn4h94.uks1.devtunnels.ms:8081"
CALLBACK_EVENTS_URI = "https://g9rn4h94-8081.uks1.devtunnels.ms" + "/api/callbacks"

credential = AzureKeyCredential(SEARCH_KEY)
# Initialize Azure Search Client
search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=AZURE_SEARCH_INDEX, credential=credential)
# Initialize Spacy
nlp = spacy.load("en_core_web_sm")



# Initialize LangChain Chat Message History
chat_history = ChatMessageHistory()


HELLO_PROMPT = "Hello, I am Emily one of the voice assistants at SThree. We have a job role that matches your skillset. Do you have a few minutes to discuss it?"
TIMEOUT_SILENCE_PROMPT = "I am sorry, I did not hear anything. Please could you confirm you are there"
GOODBYE_PROMPT = "Thank you for your time. Have a great day. Bye for now!"
GOODBYE_CONTEXT = "Goodbye"
MAX_TEXT_LENGTH = 400
# START_MESSAGE = "Great! Let's get started."
LOCATION_QUESTION = "Could you please let me know where you’re currently based? "
THANK_YOU_MESSAGE = "Great! For the next steps, I'll follow up with you via email. Thank you so much for your time today, and I look forward to staying in touch. Have a wonderful day!"
# JOB_DETAILS = "Its at JP Morgan, London, UK. The role is for a Vice President in AI. You will be collaborating with CDAO on strategic initiatives and leading the development of GenAI applications into production. "
# USER_INTERESTED = "Does the job role I just mentioned sound interesting to you?"
JOB_LOCATION = "London"
# JOB_ROLE = "AI Vice President"
# COMPETENCY_QUESTIONS = "what is your experience with leading GenAI applications into production?"
WAITING_MESSAGE = "Please wait while I find the details."
ESCALATION_MESSAGE = "I'm really sorry, I do not have sufficient information to be able to answer this right now. Let me check with the team and get back to you."
# # JOB_DETAILS_SHARED = False
# # CANDIDATE_LOCATION = ""
# # COMPETENCY_QUESTIONS_ASKED= False
# CONSENT_MESSAGE = "Before we proceed, are you okay for me to record this conversation? We will use it to improve our services and will not be shared with any third party."

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
    "consent_message": "Before we proceed, are you okay for me to record this conversation? We will use it to improve our services and will not be shared with any third party."

}

system_message = """
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
chat_history.add_message({"role": "system", "content": system_message})

def get_job_details_from_search(str_job_id):
    try:
        search_results = search_client.search(search_text=f"job_id:{str_job_id}", top=1)
        if search_results:
            for result in search_results:
                job_details = result
                chunk_data = json.loads(job_details['chunk'])
                job_role_raw = chunk_data.get("job_role")
                job_role_summary = chunk_data.get("job_summary")
                job_location = chunk_data.get("job_location")
                hiring_org = chunk_data.get("hiring_org")
                cache["job_location"] = job_location
                cache["hiring_org"] = hiring_org
                job_role = f"The job is for {job_role_raw} at {hiring_org} based in {job_location}. {job_role_summary}"
                cache["job_details"] = job_role
                job_question =(f"I need a competency-based question related to the role {job_role_raw} at {hiring_org} and {job_details}. Only respond with the question itself, without any additional comments or context. Do not include any introductory statements like Here's your question: or Let me ask:.Example question format: Can you describe a time when you led a team to develop and implement a generative AI solution?")
                print(f"Job question LLM generated: {job_question}")
                cache["competency_questions"] = job_question
                return job_details
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

CHAT_RESPONSE_EXTRACT_PATTERN = r"\s*Content:(.*)\s*Score:(.*\d+)\s*Intent:(.*)\s*Category:(.*)"

call_automation_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)

recording_id = None
recording_chunks_location = []
max_retry = 2

openai.api_key = "4443459b8bb2468a9d31f963fbff17fe"
openai.api_base = "https://ai-aasthamadaanai2659490188550.openai.azure.com/" # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
openai.api_type = 'azure'
openai.api_version = "2023-06-01-preview" # this may change in the future

app = Quart(__name__)

async def get_chat_completions_async(user_prompt): 
    print(f"User prompt : {user_prompt}")
    openai.api_key = "4443459b8bb2468a9d31f963fbff17fe"
    openai.api_base = "https://ai-aasthamadaanai2659490188550.openai.azure.com/" # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
    openai.api_type = 'azure'
    openai.api_version = "2023-06-01-preview" # this may change in the future
    messages = chat_history.messages
    messages.append({"role":"user", "content": user_prompt})
    global response_content
    try:
        #response = await ChatCompletion.acreate(model="gpt-4o",deployment_id="gpt-4o-2", temperature = 0.7, messages = messages,max_tokens = 1000)
        response = openai.ChatCompletion.create(model="gpt-4o", deployment_id="gpt-4o-2", messages=messages, max_tokens=800)
        print(f"response : {response}") 
    except Exception as ex:
        app.logger.info("error in openai api call : %s",ex)
       
    # Extract the response content
    if response is not None :
         response_content  =  response['choices'][0]['message']['content']
    else :
         response_content=""    
    return response_content  

async def get_chat_gpt_response(speech_input):
   return await get_chat_completions_async(speech_input)

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

async def handle_recognize(replyText,callerId,call_connection_id,context=""):
    play_source = TextSource(text=replyText, voice_name="en-US-AvaMultilingualNeural")
    connection_client = call_automation_client.get_call_connection(call_connection_id)
    try:
        recognize_result = await connection_client.start_recognizing_media( 
        input_type=RecognizeInputType.SPEECH,
        target_participant=PhoneNumberIdentifier(callerId), 
        end_silence_timeout=0.5, 
        play_prompt=play_source,
        operation_context=context)
        app.logger.info("handle_recognize : data=%s",recognize_result)
    except Exception as ex:
        app.logger.info("Error in recognize: %s", ex)

async def handle_play(call_connection_id, text_to_play, context):  
    if len(text_to_play) > MAX_TEXT_LENGTH:
        text_to_play = text_to_play[:MAX_TEXT_LENGTH]   
    play_source = TextSource(text=text_to_play, voice_name= "en-US-AvaMultilingualNeural") 
    await call_automation_client.get_call_connection(call_connection_id).play_media_to_all(
        play_source,
        operation_context=context)

async def handle_hangup(call_connection_id):     
    await call_automation_client.get_call_connection(call_connection_id).hang_up(is_for_everyone=True)   


async def answer_call_async(incoming_call_context,callback_url):
    return await call_automation_client.answer_call(
        incoming_call_context=incoming_call_context,
        cognitive_services_endpoint=COGNITIVE_SERVICE_ENDPOINT,
        callback_url=callback_url)

@app.route("/api/incomingCall",  methods=['POST'])
async def incoming_call_handler():
    for event_dict in await request.json:
            event = EventGridEvent.from_dict(event_dict)
            app.logger.info("incoming event data --> %s", event.data)
            if event.event_type == SystemEventNames.EventGridSubscriptionValidationEventName:
                app.logger.info("Validating subscription")
                validation_code = event.data['validationCode']
                validation_response = {'validationResponse': validation_code}
                return Response(response=json.dumps(validation_response), status=200)
            elif event.event_type =="Microsoft.Communication.IncomingCall":
                app.logger.info("Incoming call received: data=%s", 
                                event.data)  
                if event.data['from']['kind'] =="phoneNumber":
                    caller_id =  event.data['from']["phoneNumber"]["value"]
                else :
                    caller_id =  event.data['from']['rawId'] 
                app.logger.info("incoming call handler caller id: %s",
                                caller_id)
                incoming_call_context=event.data['incomingCallContext']
                guid =uuid.uuid4()
                query_parameters = urlencode({"callerId": caller_id})
                callback_uri = f"{CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

                app.logger.info("callback url: %s",  callback_uri)

                answer_call_result = await answer_call_async(incoming_call_context,callback_uri)
                
                app.logger.info("Answered call for connection id: %s",
                                answer_call_result.call_connection_id)
                return Response(status=200)
            
@app.route("/api/callbacks/<contextId>", methods=["POST"])
async def handle_callback(contextId):
    try:
        global caller_id
        app.logger.info("Request Json: %s", await request.json)
        for event_dict in await request.json:
            event = CloudEvent.from_dict(event_dict)
            app.logger.info("%s event received for call connection id: %s", event.type, event.data['callConnectionId'])
            caller_id = request.args.get("callerId").strip()
            if "+" not in caller_id:
                caller_id = "+" + caller_id.strip()

            app.logger.info("call connected : data=%s", event.data)

            # Check event type and handle accordingly
            if event.type == "Microsoft.Communication.CallConnected":
                await handle_recognize(HELLO_PROMPT, caller_id, event.data['callConnectionId'], context="InitialGreeting")

            elif event.type == "Microsoft.Communication.RecognizeCompleted":
                if event.data['recognitionType'] == "speech":
                    speech_text = event.data['speechResult']['speech']
                    app.logger.info("Recognition completed, speech_text =%s", speech_text)
                    chat_history.add_message({"role": "user", "content": speech_text})

                    # Handle conversation flow based on candidate's response
                    if event.data['operationContext'] == "InitialGreeting":
                        if any(keyword in speech_text.lower() for keyword in ["no", "not interested", "busy"]):
                            await handle_play(event.data['callConnectionId'], "No problem, I understand. Have a good day!", GOODBYE_CONTEXT)
                            await handle_hangup(event.data['callConnectionId'])
                        else:
                            await handle_recognize(cache.get[ "consent_message"], caller_id, event.data['callConnectionId'], context="ConsentRequest")

                    elif event.data['operationContext'] == "ConsentRequest":
                        if "no" in speech_text.lower():
                            decline_message = await get_chat_gpt_response("Candidate does not consent to recording. Generate a response to politely end the call.")
                            await handle_play(event.data['callConnectionId'], decline_message, GOODBYE_CONTEXT)
                            await handle_hangup(event.data['callConnectionId'])
                        else:
                            start_message = await get_chat_gpt_response("Generate a warm response to thank the candidate for consenting and start the conversation.")
                           # await handle_play(event.data['callConnectionId'], start_message, context="ConsentRequest")
                            combined_message = f"{start_message} {LOCATION_QUESTION}"
                            await handle_recognize(combined_message, caller_id, event.data['callConnectionId'], context="LocationRequest")

                            # Wait for playback to finish before proceeding

                    elif event.data['operationContext'] == "LocationRequest":
                        # Handle location response
                        location = extract_location(speech_text)
                        if location:
                            candidate_coords = get_coordinates(location)
                            if candidate_coords and job_coords:
                                distance = geodesic(candidate_coords, job_coords).kilometers

                                if distance <= 50:
                                    await handle_play(event.data['callConnectionId'], f"The job role is located in {JOB_LOCATION}, so it might actually work nicely for you. Let me share some details about it.", context="LocationRequest")
                                    # Wait for playback to finish before proceeding
                                else:
                                    await handle_recognize("The job is located in London. Are you open to commuting if travel expenses are reimbursed?", caller_id, event.data['callConnectionId'], context="CommuteQuestion")
                            else:
                                # If unable to get coordinates, handle gracefully
                                await handle_play(event.data['callConnectionId'], "Thank you for sharing. Let me share some details about the job.", context="LocationRequest")
                                # Wait for playback to finish before proceeding
                        else:
                            # If location extraction fails
                            await handle_play(event.data['callConnectionId'], "Thank you for sharing. Let me share some details about the job.", context="LocationRequest")
                            # Wait for playback to finish before proceeding

                    elif event.data['operationContext'] == "CommuteQuestion":
                        if any(keyword in speech_text.lower() for keyword in ["yes", "okay", "fine", "sure"]):
                            app.logger.info("User is open to commuting")
                            await handle_play(event.data['callConnectionId'], "Great! Let me share some details about the job.", context="LocationRequest")
                            # Wait for playback to finish before proceeding
                        else:
                            await handle_play(event.data['callConnectionId'], "No problem, thank you for your time. Have a good rest of the day!", GOODBYE_CONTEXT)
                            await handle_hangup(event.data['callConnectionId'])

                    elif event.data['operationContext'] == "JobInterest":
                        if any(keyword in speech_text.lower() for keyword in ["no", "not interested"]):
                            await handle_play(event.data['callConnectionId'], "No problem, thank you for your time. Have a great day!", GOODBYE_CONTEXT)
                            await handle_hangup(event.data['callConnectionId'])
                        else:
                            await handle_play(event.data['callConnectionId'], "Thank you so much for your interest! I'd like to ask you a few questions about your experience and skills to understand how well they align with this opportunity.", context="JobInterest")
                            # Wait for playback to finish before proceeding

                    elif event.data['operationContext'] == "CompetencyResponse":
                        # Acknowledge their experience
                        chat_history.add_message({"role": "user", "content": speech_text})
                        gpt_follow_up = await get_chat_gpt_response(f"Acknowledge their experience {speech_text}.")
                        chat_history.add_message({"role": "assistant", "content": gpt_follow_up})
                        # Change context to "NextSteps" to avoid conflict
                        await handle_play(event.data['callConnectionId'], gpt_follow_up, context="NextStepsResponse")
                        # Wait for playback to finish before proceeding

                    elif event.data['operationContext'] == "NextStepsResponse":
                        if any(keyword in speech_text.lower() for keyword in ["yes", "okay", "sure"]):
                            await handle_play(event.data['callConnectionId'], THANK_YOU_MESSAGE, GOODBYE_CONTEXT)
                            await handle_hangup(event.data['callConnectionId'])
                        else:
                            await handle_play(event.data['callConnectionId'], "No problem, thank you for your time. Have a great day!", GOODBYE_CONTEXT)
                            await handle_hangup(event.data['callConnectionId'])

                elif event.data['recognitionType'] == "dtmf":
                    # Handle DTMF inputs if necessary
                    pass

            elif event.type == "Microsoft.Communication.PlayCompleted":
                context = event.data['operationContext']
                if context == "ConsentRequest":
                    # After thanking the candidate, ask for location
                    await handle_recognize(cache.get['location'], caller_id, event.data['callConnectionId'], context="LocationRequest")

                elif context == "LocationRequest":
                    # Now play the actual JOB_DETAILS
                    await handle_play(event.data['callConnectionId'], cache.get["job_details"], context="JobDetails")

                elif context == "JobDetails":
                    # After JOB_DETAILS is played, proceed to ask if the user is interested
                    await handle_recognize(cache.get["user interested"], caller_id, event.data['callConnectionId'], context="JobInterest")

                elif context == "JobInterest":
                    # After introducing competency questions, ask the question
                    await handle_recognize(cache.get["competency_questions"], caller_id, event.data['callConnectionId'], context="CompetencyResponse")

                elif context == "CompetencyResponse":
                    # After acknowledging skills, proceed to next steps
                    await handle_play(event.data['callConnectionId'], "I actually think you could be a very good match for this role. Would it be okay if I forwarded your CV to our client organization?", context="NextStepsResponse")
                    await handle_recognize("Please let me know if that's okay with you.", caller_id, event.data['callConnectionId'], context="NextStepsResponse")
                    
                
                # elif context == "NextSteps":
                #     # After acknowledging skills, proceed to next steps
                #     await handle_play(event.data['callConnectionId'], "I actually think you could be a very good match for this role. Would it be okay if I forwarded your CV to our client organization?", context="NextStepsResponse")
                #     await handle_recognize("Please let me know if that's okay with you.", caller_id, event.data['callConnectionId'], context="NextStepsResponse")


            elif event.type == "Microsoft.Communication.RecognizeFailed":
                resultInformation = event.data['resultInformation']
                reasonCode = resultInformation['subCode']
                context = event.data['operationContext']
                global max_retry
                if reasonCode == 8510 and max_retry > 0:
                    await handle_recognize(TIMEOUT_SILENCE_PROMPT, caller_id, event.data['callConnectionId'], context=context)
                    max_retry -= 1
                else:
                    await handle_play(event.data['callConnectionId'], GOODBYE_PROMPT, GOODBYE_CONTEXT)
                    await handle_hangup(event.data['callConnectionId'])

            elif event.type == "Microsoft.Communication.CallDisconnected":
                # Clean up resources or perform any necessary actions on call disconnect
                app.logger.info("Call disconnected for call connection id: %s", event.data['callConnectionId'])

        return Response(status=200)
    except Exception as ex:
        app.logger.info("Error in event handling: %s", ex)

        
# async def handle_callback(contextId):
#     try:
#         global caller_id
#         app.logger.info("Request Json: %s", await request.json)
#         for event_dict in await request.json:
#             event = CloudEvent.from_dict(event_dict)
#             app.logger.info("%s event received for call connection id: %s", event.type, event.data['callConnectionId'])
#             caller_id = request.args.get("callerId").strip()
#             if "+" not in caller_id:
#                 caller_id = "+".strip() + caller_id.strip()

#             app.logger.info("call connected : data=%s", event.data)

#             # Check event type and handle accordingly
#             if event.type == "Microsoft.Communication.CallConnected":
#                 await handle_recognize(HELLO_PROMPT, caller_id, event.data['callConnectionId'], context="InitialGreeting")

#             elif event.type == "Microsoft.Communication.RecognizeCompleted":
#                 if event.data['recognitionType'] == "speech":
#                     speech_text = event.data['speechResult']['speech']
#                     app.logger.info("Recognition completed, speech_text =%s", speech_text)
#                     chat_history.add_message({"role": "user", "content": speech_text})

#                     # Handle conversation flow based on candidate's response
#                     if event.data['operationContext'] == "InitialGreeting":
#                         if any(keyword in speech_text.lower() for keyword in ["no", "not interested", "busy"]):
#                             await handle_play(event.data['callConnectionId'], "No problem, I understand. Have a good day!", GOODBYE_CONTEXT)
#                         else:
#                             await handle_recognize(CONSENT_MESSAGE, caller_id, event.data['callConnectionId'], context="ConsentRequest")

#                     elif event.data['operationContext'] == "ConsentRequest":
#                         if "no" in speech_text.lower():
#                             decline_message = await get_chat_gpt_response("Candidate does not consent to recording. Generate a response to politely end the call.")
#                             await handle_play(event.data['callConnectionId'], decline_message, GOODBYE_CONTEXT)
#                         else:
#                             start_message = await get_chat_gpt_response("Generate a warm response to thank the candidate for consenting and start the conversation.")
#                             await handle_play(event.data['callConnectionId'], start_message, context="LocationRequest")
#                             await handle_recognize(LOCATION_QUESTION, caller_id, event.data['callConnectionId'], context="LocationRequest")

#                     elif event.data['operationContext'] == "LocationRequest":
#                         chat_history.add_message({"role": "user", "content": speech_text})
#                         # Handle location response
#                         location = extract_location(speech_text)
#                         candidate_coords = get_coordinates(location)
#                         job_coords = get_coordinates(JOB_LOCATION)
#                         distance = geodesic(candidate_coords, job_coords).kilometers

#                         if distance <= 50:
#                             await handle_play(event.data['callConnectionId'], f"The job is located in London so it might actually work out nicely for you! Let me share some details.", context="JobDetails")
#                         else:
#                             await handle_play(event.data['callConnectionId'], "The job is located in London. Are you open to commuting if travel expenses are reimbursed?", context="CommuteQuestion")

#                     elif event.data['operationContext'] == "CommuteQuestion":
#                         if any(keyword in speech_text.lower() for keyword in ["yes", "okay", "fine"]):
#                             app.logger.info("User is open to commuting")
#                             await handle_play(event.data['callConnectionId'], "Great! Let me share some details about the job.", context="JobDetails")
#                             await handle_recognize(JOB_DETAILS, caller_id, event.data['callConnectionId'], context="JobDetails")
#                         else:
#                             await handle_play(event.data['callConnectionId'], "No problem, thank you for your time. Have a good rest of the day!", GOODBYE_CONTEXT)

#                     elif event.data['operationContext'] == "JobDetails":
#                         await handle_play(event.data['callConnectionId'], JOB_DETAILS, context="JobInterest")
#                         await handle_recognize(JOB_DETAILS, caller_id, event.data['callConnectionId'], context="JobInterest")

#                     elif event.data['operationContext'] == "JobInterest":
#                         if any(keyword in speech_text.lower() for keyword in ["no", "not interested"]):
#                             await handle_play(event.data['callConnectionId'], "No problem, thank you for your time. Have a good rest of the day!", GOODBYE_CONTEXT)
#                         else:
#                             await handle_play(event.data['callConnectionId'], "Thank you so much for your interest! I'd like to ask you a few questions about your experience and skills to understand how well they align with this opportunity.", context="CompetencyQuestions")
#                             await handle_recognize(COMPETENCY_QUESTIONS, caller_id, event.data['callConnectionId'], context="CompetencyResponse")

#                     elif event.data['operationContext'] == "CompetencyResponse":
#                         chat_history.add_message({"role": "user", "content": speech_text})
#                         gpt_follow_up = await get_chat_gpt_response(f"Acknowledge their experience {speech_text} is relevant to the {JOB_ROLE}.")
#                         chat_history.add_message({"role": "assistant", "content": gpt_follow_up})
#                         await handle_play(event.data['callConnectionId'], gpt_follow_up, context="FollowUp")
#                         await handle_play(event.data['callConnectionId'], THANK_YOU_MESSAGE, GOODBYE_CONTEXT)

#             elif event.type == "Microsoft.Communication.RecognizeFailed":
#                 resultInformation = event.data['resultInformation']
#                 reasonCode = resultInformation['subCode']
#                 context = event.data['operationContext']
#                 global max_retry
#                 if reasonCode == 8510 and 0 < max_retry:
#                     await handle_recognize(TIMEOUT_SILENCE_PROMPT, caller_id, event.data['callConnectionId'])
#                     max_retry -= 1
#                 else:
#                     await handle_play(event.data['callConnectionId'], GOODBYE_PROMPT, GOODBYE_CONTEXT)

#             elif event.type == "Microsoft.Communication.PlayCompleted":
#                 context = event.data['operationContext']

#         return Response(status=200)
#     except Exception as ex:
#         app.logger.info("error in event handling: %s", ex)

@app.route("/")
def hello():
    return "Hello ACS CallAutomation!..test"

if __name__ == '__main__':
    app.logger.setLevel(INFO)
    app.run(port=8081)
