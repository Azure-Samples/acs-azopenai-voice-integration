from enum import Enum

class AgentPersonaType(Enum):
    """
    Enum for the different types of agent personas.
    Options:
    - INTRO: Handles the introduction of the call
    - INTERVIEW: Handles the competency-based interview
    - CLOSURE: Handles the end of the interview
    - GENERAL: general agent persona for E2E call, but less performant.
    """
    INTRO = "intro"
    INTERVIEW = "interview"
    CLOSURE = "closure"
    GENERAL = "general"