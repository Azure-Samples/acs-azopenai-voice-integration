from typing import List, Dict, Any
from openai import AsyncAzureOpenAI
from ..config.settings import Config

class OpenAIService:
    """Service for handling OpenAI API interactions"""
    def __init__(self, config: Config):
        self.config = config
        self.client = AsyncAzureOpenAI(
            api_key=config.AZURE_OPENAI_SERVICE_KEY,
            api_version="2024-08-01-preview",
            azure_endpoint=config.AZURE_OPENAI_SERVICE_ENDPOINT
        )
        self.chat_history: List[Dict[str, Any]] = []
        self._initialize_chat_history()

    def _initialize_chat_history(self):
        """Initialize chat history with system message"""
        self.chat_history = [{
            "role": "system",
            "content": self.SYSTEM_MESSAGE
        }]

    async def get_chat_completion(self, user_prompt: str, max_length: int = 200) -> str:
        """
        Get chat completion from Azure OpenAI
        Args:
            user_prompt: User's input text
            max_length: Maximum length of the response
        """
        try:
            # Add user message to history
            self.chat_history.append({
                "role": "user",
                "content": f"In less than {max_length} characters: {user_prompt}"
            })

            response = await self.client.chat.completions.create(
                model=self.config.AZURE_OPENAI_DEPLOYMENT_MODEL_NAME,
                messages=self.chat_history,
                max_tokens=1000
            )

            response_content = response.choices[0].message.content

            # Add assistant's response to history
            self.chat_history.append({
                "role": "assistant",
                "content": response_content
            })

            return response_content

        except Exception as ex:
            print(f"Error in OpenAI API call: {ex}")
            return ""

    # System message for the AI assistant
    SYSTEM_MESSAGE = """
    ## CONTEXT ## 
    You are Emily, one of the new voice Assistants at SThree. You are helping a job seeker with a job role that matches their skillset. You will ask them some questions and share some details about the role. You will also answer their questions and share some information. Always wait for the job seeker's response before proceeding to the next part of the conversation.
    
    ## CONVERSATION FLOW ## 
    1. Initial greeting and job role mention
    2. Ask for recording consent
    3. Location verification
    4. Job details sharing
    5. Candidate interest confirmation
    6. Skills and experience discussion
    7. Competency-based questions
    8. Next steps and closure
    
    ## GUIDELINES ## 
    - Maintain a polite and friendly tone
    - Use clear and concise language
    - Focus on job-relevant information
    - Be respectful of candidate's time
    - Handle objections professionally
    """