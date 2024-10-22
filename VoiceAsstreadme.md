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

### 3. Update Configuration
Replace the placeholders with your actual Azure credentials in the Python script:
- ACS_CONNECTION_STRING
- AZURE_OPENAI_SERVICE_KEY
- AZURE_SEARCH_KEY
- AZURE_SEARCH_ENDPOINT
- AZURE_MAPS_KEY
- Redis Configuration (if Redis is not running locally):
- REDIS_HOST, REDIS_PORT
You can either set these as environment variables or hardcode them into the script (for testing purposes).




