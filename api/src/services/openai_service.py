from typing import List, Dict, Any, Optional
from openai import AsyncAzureOpenAI
from ..config.settings import Config
from ..config.constants import OpenAIPrompts
from ..utils.helpers import AgentPersonaType


class OpenAIService:
    """Service for handling OpenAI API interactions"""

    def __init__(self, config: Config):
        self.config = config
        self.client = AsyncAzureOpenAI(
            api_key=config.AZURE_OPENAI_SERVICE_KEY,
            api_version="2024-08-01-preview",
            azure_endpoint=config.AZURE_OPENAI_SERVICE_ENDPOINT,
        )
        self.chat_history: List[Dict[str, Any]] = []
        self.system_message_dict = OpenAIPrompts.system_message_dict
        self._initialize_chat_history()

    def _initialize_chat_history(
        self,
        system_prompt_str: str = "You are a helpful AI assistant.",
    ) -> None:
        """Initialize chat history with system message defined by the agent persona of choice"""
        self.chat_history = [{"role": "system", "content": system_prompt_str}]

    def update_agent_persona(
        self,
        agent_persona: AgentPersonaType,
        assistant_message_to_include: Optional[str] = None,
        user_message_to_include: Optional[str] = None,
    ) -> None:
        """Update the agent persona for the conversation
        Args:
            agent_persona: Agent persona type
            assistant_message_to_include: Optional assistant message to include in the chat history
            user_message_to_include: Optional user message to include in the chat history
        """
        self.chat_history.clear()
        agent = agent_persona.value
        self._initialize_chat_history(self.system_message_dict[agent])
        if assistant_message_to_include:
            self.chat_history.append(
                {"role": "assistant", "content": assistant_message_to_include}
            )
        if user_message_to_include:
            self.chat_history.append(
                {"role": "user", "content": user_message_to_include}
            )

    async def get_chat_completion(self, user_prompt: str, max_length: int = 200) -> str:
        """
        Get chat completion from Azure OpenAI
        Args:
            user_prompt: User's input text
            max_length: Maximum length of the response
        """
        try:
            # Add user message to history
            self.chat_history.append(
                {
                    "role": "user",
                    "content": f"In less than {max_length} characters: {user_prompt}",
                }
            )

            response = await self.client.chat.completions.create(
                model=self.config.AZURE_OPENAI_DEPLOYMENT_MODEL_NAME,
                messages=self.chat_history,
                max_tokens=1000,
            )

            response_content = response.choices[0].message.content

            # Add assistant's response to history
            self.chat_history.append({"role": "assistant", "content": response_content})

            return response_content

        except Exception as ex:
            print(f"Error in OpenAI API call: {ex}")
            return ""
