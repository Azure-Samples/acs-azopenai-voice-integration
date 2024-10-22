import json
import redis
import os
from dotenv import load_dotenv
# Redis Configuration (Replace with your Redis details)
load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST")
#REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

redis_client = redis.StrictRedis(host=REDIS_HOST, port=6380, password=REDIS_PASSWORD, ssl=True)

# Helper Functions for Redis Operations
def set_cache(key, value):
    """Set value in Redis cache."""
    redis_client.set(key, json.dumps(value))

def get_cache(key):
    """Get value from Redis cache."""
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def delete_cache(key):
    """Delete a key from Redis cache."""
    redis_client.delete(key)

def upload_initial_cache_data():
    initial_cache_data = {
        "start_message": "Great! Let's get started.",
        "location_question": "Could you please let me know where you’re currently based? It’ll help me understand how the role aligns with your location.",
        "thank_you_message": "Great! For the next steps, I'll follow up with you via email. Thank you so much for your time today, and I look forward to staying in touch. Have a wonderful day!",
        "job_details": "It's at JP Morgan, London, UK. The role is for a Vice President in AI.",
        "user_interested": "Does the job role I just mentioned sound interesting to you?",
        "job_location": "London",
        "job_role": "AI Vice President",
        "competency_questions": "What is your experience with leading GenAI applications?",
        "waiting_message": "Please wait while I find the details.",
        "escalation_message": "I'm really sorry, I do not have sufficient information to be able to answer this right now. Let me check with the team and get back to you.",
        "job_details_shared": False,
        "candidate_location": "",
        "competency_questions_asked": False,
        "consent_message": "Before we proceed, are you okay for me to record this conversation? We will use it to improve our services and will not be shared with any third party."
    }

    # Upload each item to Redis cache
    for key, value in initial_cache_data.items():
        print(f"Uploading {key} to Redis cache.")
        set_cache(key, value)

    print("Initial static cache data uploaded to Redis.")

# def verify_cache_data():
#     # Verify the cache is written correctly
#     keys = [
#         "start_message", "location_question", "thank_you_message", "job_details",
#         "user_interested", "job_location", "job_role", "competency_questions",
#         "waiting_message", "escalation_message", "job_details_shared",
#         "candidate_location", "competency_questions_asked", "consent_message"
#     ]

#     for key in keys:
#         value = get_cache(key)
#         if value is not None:
#             print(f"Key: {key}, Value: {value}")
#         else:
#             print(f"Key: {key} not found in cache.")

if __name__ == "__main__":
    upload_initial_cache_data()
    #verify_cache_data()