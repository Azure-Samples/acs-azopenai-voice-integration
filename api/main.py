# main.py
import logging
from config import Config
from chat_service import ChatService
from call_service import CallService
from app import CallAutomationApp

logging.basicConfig(level=logging.INFO)

config = Config()
chat_service = ChatService(config)
call_service = CallService(config)
automation_app = CallAutomationApp(config, chat_service, call_service)
app = automation_app.app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
