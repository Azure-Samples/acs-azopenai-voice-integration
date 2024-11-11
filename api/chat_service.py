# chat_service.py
import openai
from langchain_community.chat_message_histories import ChatMessageHistory
import logging

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, config):
        self.config = config
        self.setup_openai()
        self.chat_history = ChatMessageHistory()
        self.initialize_chat()

    def setup_openai(self):
        openai.api_key = self.config.OPENAI_API_KEY
        openai.api_base = self.config.OPENAI_API_BASE
        openai.api_type = self.config.OPENAI_API_TYPE
        openai.api_version = self.config.OPENAI_API_VERSION

    def initialize_chat(self):
        system_message = """
        ## CONTEXT ##
        You are Emily, one of the new voice Assistants at SThree...
        [Rest of the system message]
        """
        self.chat_history.add_message({"role": "system", "content": system_message})

    async def get_chat_completion(self, user_prompt):
        logger.info(f"User prompt: {user_prompt}")
        messages = self.chat_history.messages
        messages.append({"role": "user", "content": user_prompt})

        try:
            response = await openai.ChatCompletion.acreate(
                model=self.config.OPENAI_DEPLOYMENT_MODEL,
                deployment_id=self.config.OPENAI_DEPLOYMENT_ID,
                messages=messages,
                max_tokens=800,
            )
            return response["choices"][0]["message"]["content"]
        except Exception as ex:
            logger.error("Error in OpenAI API call: %s", ex)
            return ""
