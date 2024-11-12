from enum import Enum

class StatusCodes:
    """HTTP Status Codes"""
    OK = 200
    BAD_REQUEST = 400
    SERVER_ERROR = 500

class EventTypes(str, Enum):
    """Azure Communication Service Event Types"""
    INCOMING_CALL = "Microsoft.Communication.IncomingCall"
    CALL_CONNECTED = "Microsoft.Communication.CallConnected"
    RECOGNIZE_COMPLETED = "Microsoft.Communication.RecognizeCompleted"
    PLAY_COMPLETED = "Microsoft.Communication.PlayCompleted"
    RECOGNIZE_FAILED = "Microsoft.Communication.RecognizeFailed"
    CALL_DISCONNECTED = "Microsoft.Communication.CallDisconnected"
    PARTICIPANTS_UPDATED = "Microsoft.Communication.ParticipantsUpdated"

class ErrorMessages:
    """Error and Fallback Messages"""
    PLAY_ERROR = "I apologize, but I'm having trouble responding. Let me try again."
    RECOGNIZE_ERROR = "I apologize, but I need to repeat the question. Could you please respond?"

class ConversationPrompts:
    """Conversation Prompts"""
    HELLO = "Hello, I am Emily V7 one of the voice assistants at SThree. We have a job role that matches your skillset. Do you have a few minutes to discuss it?"
    TIMEOUT_SILENCE = "I am sorry, I did not hear anything. Please could you confirm you are there"
    GOODBYE = "Thank you for your time. Have a great day. Bye for now!"
    LOCATION_QUESTION = "Could you please let me know where you're currently based?"
    THANK_YOU = "Great! For the next steps, I'll follow up with you via email. Thank you so much for your time today, and I look forward to staying in touch. Have a wonderful day!"

class AppConstants:
    """Application Constants"""
    MAX_TEXT_LENGTH = 400
    MAX_RETRY = 2