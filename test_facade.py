import os
os.environ["CHROMA_TELEMETRY"] = "false"
from application.shared.configuration.app_config import AppConfig
from application.facade.chatbot_facade import ChatbotFacade

config = AppConfig.from_env()
facade = ChatbotFacade(config)

print("Initializing Facade...")
facade.initialize("chatbot.xls")

print("Testing RAG (ask_question)...")
res = facade.handle_message("user123", "internet is slow")
print("Response text:", res.text)
print("Response intent:", res.intent)
print("Response sources:", res.sources_used)
