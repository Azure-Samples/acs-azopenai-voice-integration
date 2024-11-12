from typing import Dict, Any

class CacheService:
    """
    Cache service for conversation state management
    TODO: Replace with Redis implementation
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {
            "start_message": "Great! Let's get started.",
            "location_question": "Could you please let me know where you're currently based?",
            "thank_you_message": "Great! For the next steps, I'll follow up with you via email.",
            "job_details": "Its at JP Morgan, London, UK. The role is for a Vice President in AI.",
            "user_interested": "Does the job role I just mentioned sound interesting to you?",
            "job_location": "London, United Kingdom",
            "job_role": "AI Vice President",
            "competency_questions": "what is your experience with leading GenAI applications?",
            "waiting_message": "Please wait while I find the details.",
            "escalation_message": "I'm really sorry, I do not have sufficient information.",
            "job_details_shared": False,
            "candidate_location": "",
            "competency_questions_asked": False,
            "consent_message": "Before we proceed, are you okay for me to record this conversation?"
        }
        self.is_call_terminated = False
        self.recording_id = None
        self.recording_chunks_location = []

    async def get(self, key: str) -> Any:
        """Get value from cache"""
        return self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self._cache[key] = value

    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()