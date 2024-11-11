# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("AZURE_OPENAI_SERVICE_KEY")
    OPENAI_API_BASE = os.getenv("AZURE_OPENAI_SERVICE_ENDPOINT")
    OPENAI_API_TYPE = os.getenv("AZURE_OPENAI_API_TYPE")
    OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    OPENAI_DEPLOYMENT_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_MODEL")
    OPENAI_DEPLOYMENT_ID = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID")

    # Azure Communication Services
    ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
    COGNITIVE_SERVICE_ENDPOINT = os.getenv("COGNITIVE_SERVICE_ENDPOINT")

    # Azure Search
    SEARCH_KEY = os.getenv("SEARCH_KEY")
    AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")

    # Callback Settings
    CALLBACK_URI_HOST = os.getenv("CALLBACK_URI_HOST")
    CALLBACK_EVENTS_URI = os.getenv("CALLBACK_EVENTS_URI")

    # Voice Assistant Settings
    MAX_TEXT_LENGTH = 400
    MAX_RETRY = 2
    VOICE_NAME = "en-US-AvaMultilingualNeural"
