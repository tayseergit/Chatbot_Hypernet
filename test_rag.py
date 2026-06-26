import os
os.environ["CHROMA_TELEMETRY"] = "false"
from application.rag.rag_service import RAGService
from application.shared.configuration.app_config import RAGConfig

config = RAGConfig()
config.knowledge_file = "chatbot.xls"
rag = RAGService(config)

print("Initializing RAG...")
rag.initialize("chatbot.xls")
print("Querying RAG...")
raw_res = rag._retriever.retrieve("internet", n_results=5)
print("Raw distances:", raw_res['distances'])
res = rag.query("internet")
with open("result.txt", "w", encoding="utf-8") as f:
    f.write(f"Success: {res.success}\n")
    f.write(f"Data: {res.data}\n")
print("Done writing to result.txt")
