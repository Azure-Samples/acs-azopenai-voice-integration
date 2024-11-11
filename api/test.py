from quart import Quart
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Environment variables
AZURE_OPENAI_SERVICE_KEY = os.getenv("AZURE_OPENAI_SERVICE_KEY")
AZURE_OPENAI_SERVICE_ENDPOINT = os.getenv("AZURE_OPENAI_SERVICE_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_MODEL_NAME")

# Initialize Quart app
app = Quart(__name__)

# Initialize Azure OpenAI client
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

        response = await client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_MODEL_NAME,
            messages=chat_request,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as ex:
        print(f"Error in OpenAI API call: {ex}")
        return ""

# Example route
@app.route("/chat")
async def chat():
    response = await get_chat_completions_async(
        "You are a helpful assistant.",
        "Explain Where is egypt?"
    )
    return {"response": response}

if __name__ == "__main__":
    app.run(debug=True)