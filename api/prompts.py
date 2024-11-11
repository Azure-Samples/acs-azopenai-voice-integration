# prompts.py
class Prompts:
    HELLO = (
        "Hello, I am Emily one of the voice assistants at SThree. "
        "We have a job role that matches your skillset. "
        "Do you have a few minutes to discuss it?"
    )
    TIMEOUT_SILENCE = (
        "I am sorry, I did not hear anything. Please could you confirm you are there?"
    )
    GOODBYE = "Thank you for your time. Have a great day. Bye for now!"
    LOCATION_QUESTION = (
        "Could you please let me know where you're currently based? "
        "It'll help me understand how the role aligns with your location."
    )
    THANK_YOU = (
        "Great! For the next steps, I'll follow up with you via email. "
        "Thank you so much for your time today, and I look forward to staying in touch. "
        "Have a wonderful day!"
    )
    WAITING = "Please wait while I find the details."
    ESCALATION = (
        "I'm really sorry, I do not have sufficient information to be able to answer this right now. "
        "Let me check with the team and get back to you."
    )
    CONSENT = (
        "Before we proceed, are you okay for me to record this conversation? "
        "We will use it to improve our services and will not be shared with any third party."
    )
