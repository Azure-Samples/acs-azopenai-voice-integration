# Recruitment Voice Assistant 

## Features
- **PSTN Calling**: Users can call a phone number, and the voice assistant will interact with them using speech-to-text and text-to-speech capabilities.
- **OpenAI GPT-4o Integration**: Generates dynamic recruitment filtering chat for the potential candidate based on job description.
- **Event-Driven Architecture**: Uses **Azure EventGrid** for event-driven routing of call-related events.
- **Redis Caching**: Stores precomputed job details, competency questions, and location data to minimize repeated API calls and reduce latency.
- **Azure Services**: Leverages **Azure Maps**, **Azure Search**, and **Azure Cognitive Services** for grounding the call into relevant job description and in future in the candidate CV. 
- **Session History**: Session data and call recordings are stored in **Cosmos DB** for long-term storage.
---

## Architecture Overview
The following Azure services and technologies are used in this project:

1. **Azure Communication Services (ACS)**: Handles incoming and (to be implemented) outgoing PSTN calls.
2. **Azure OpenAI GPT-4o**: Generates responses to user inputs using large language models.
3. **Azure Cognitive Services**: Provides speech-to-text and text-to-speech capabilities for interacting with the caller.
4. **Azure EventGrid**: Routes call events (CallConnected, RecognizeCompleted, etc.) to the **Quart API**.
5. **Azure Search**: Queries job details and other information for candidate interaction.
6. **Azure Maps**: Provides geographic location data for determining candidate proximity to job roles.
7. **Redis Cache**: Caches job details and other global variables to reduce API calls and improve performance.
8. **Azure Cosmos DB**: Stores call session data, including recordings and conversation history, for long-term storage.
---

## Prerequisites 
- **Azure Communication Services (ACS)** resource for PSTN calling.
- **Azure Cognitive Services** for speech-to-text and text-to-speech processing.
- **Azure OpenAI GPT-4** model deployment for generating responses.
- **Azure Search** for querying job descriptions.
- **Azure Maps** for geographic information.
- **Redis** for caching job details and competency questions.
- **Azure Cosmos DB** for session history and call recordings.
- **Python 3.8+** installed on your local environment.
- **Azure Tunnel** for handling ACS callback URLs when testing locally.
- **Spacy** for entity extraction 

---

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-repository-name/voice-assistant
cd voice-assistant
```

### 2. Install Python Dependencies
Create a virtual environment and install the required Python libraries listed in `requirements.txt`.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Call Automation - Quick Start Sample

This is a sample application demonstrated during Microsoft Build 2023. It highlights an integration of Azure Communication Services with Azure OpenAI Service to enable intelligent conversational agents.

## Prerequisites

- Create an Azure account with an active subscription. For details, see [Create an account for free](https://azure.microsoft.com/free/)
- Create an Azure Communication Services resource. For details, see [Create an Azure Communication Resource](https://docs.microsoft.com/azure/communication-services/quickstarts/create-communication-resource). You'll need to record your resource **connection string** for this sample.
- An Calling-enabled telephone number. [Get a phone number](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/telephony/get-phone-number?tabs=windows&pivots=platform-azp).
- Azure Dev Tunnels CLI. For details, see  [Enable dev tunnel](https://docs.tunnels.api.visualstudio.com/cli)
- Create an Azure Cognitive Services resource. For details, see [Create an Azure Cognitive Services Resource](https://learn.microsoft.com/en-us/azure/cognitive-services/cognitive-services-apis-create-account)
- Create and host a Azure Dev Tunnel. Instructions [here](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started)
- [Python](https://www.python.org/downloads/) 3.7 or above.

### Setup and host your Azure DevTunnel

[Azure DevTunnels](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/overview) is an Azure service that enables you to share local web services hosted on the internet. Use the commands below to connect your local development environment to the public internet. This creates a tunnel with a persistent endpoint URL and which allows anonymous access. We will then use this endpoint to notify your application of calling events from the ACS Call Automation service.

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8080
devtunnel host
```

### Deploy and set up the infrastructure

> **Disclaimer:** The infrastructure and code provided is **not production-ready** and isn't fully dynamic. If having dynamic IaC is relevant for you, please review the templates and add modifications as needed. Additionally, some steps are left to be done manual due to the potential conflicts with Azure Policies implemented in your targeted tenant/subscription.

Deploy the bicep template by navigating to the `infra` folder and running:
```azcli
az deployment group create --resource-group rg-sthree-poc-sandbox --template-file main.bicep
```
Optionally, add the flag `--mode Complete` to avoid inconsistences when carrying out redeployments

Once deployed, proceed manually with the following:
1. Navigate into the Event Grid System Topic created and add a subscription pointing to the Dev Tunnel url that was generated on the step above.
2. Generate an index on Azure AI Search to have a vectorized data for the RAG feature of the model. Feel free to do it via the GUI or code, as preferred.
3. Navigate into Az Communications Service (ACS) and [acquire a phone number by purchasing it on the portal or via code](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/telephony/get-phone-number?tabs=windows&pivots=platform-azp)
4. Create a service principal for ACS within Azure App Registrations for permissions and access.
5. Extract the necessary environment variables to run the app and add them onto the `.env` file.



### Configuring application

Open `main.py` file to configure the following settings

1. - `CALLBACK_URI_HOST`: your dev tunnel endpoint
2. - `COGNITIVE_SERVICE_ENDPOINT`: The Cognitive Services endpoint
3. - `ACS_CONNECTION_STRING`: Azure Communication Service resource's connection string.
4. - `AZURE_OPENAI_SERVICE_KEY`: Open AI's Service Key
5. - `AZURE_OPENAI_SERVICE_ENDPOINT`: Open AI's Service Endpoint
6. - `AZURE_OPENAI_DEPLOYMENT_MODEL_NAME`: Open AI's Model name
6. - `AGENT_PHONE_NUMBER`: Agent Phone Number to transfer call

## Run app locally

1. Navigate to `callautomation-openai-sample` folder and run `main.py` in debug mode or use command `python ./main.py` to run it from PowerShell, Command Prompt or Unix Terminal
2. Browser should pop up with the below page. If not navigate it to `http://localhost:8080/` or your dev tunnel url.
3. Register an EventGrid Webhook for the IncomingCall Event that points to your DevTunnel URI. Instructions [here](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/incoming-call-notification).

Once that's completed you should have a running application. The best way to test this is to place a call to your ACS phone number and talk to your intelligent agent.





