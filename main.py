from docx import Document
from sentence_transformers import SentenceTransformer
import chromadb
import requests
import msvcrt
import os
import threading
import time


# =========================
# CONFIGURATIONS
# =========================

CONFIG = {
    # File
    "docx_path": "D:\\chat_bot\\call_center_rag_ready.docx",

    # Chunking
    "chunk_size": 300,
    "overlap": 50,

    # Embedding
    "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",

    # Vector DB
    "collection_name": "isp_knowledge",
    "n_results": 5,

    # Ollama
    "ollama_url": "http://localhost:11434/api/generate",
    "ollama_model": "dagbs/qwen2.5-coder-7b-instruct-abliterated:latest",

            
    # Model generation
    "temperature": 0.1,
    "top_p": 0.8,
    "top_k": 40,
    "num_ctx": 4096,
}


# =========================
# 1. Read DOCX file
# =========================

def read_docx(path):
    doc = Document(path)
    text = []

    for p in doc.paragraphs:
        if p.text.strip():
            text.append(p.text.strip())

    return "\n".join(text)


# =========================
# 2. Split text into chunks
# =========================

def split_text(text, chunk_size, overlap):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# =========================
# 3. Embedding functions
# =========================

def embed_document(model, text):
    return model.encode("passage: " + text).tolist()


def embed_question(model, question):
    return model.encode("query: " + question).tolist()


# =========================
# 4. Ask local model using Ollama
# =========================

def ask_ollama(question, context):
    prompt = f"""
أنت مساعد ذكي لشركة إنترنت ومركز خدمة عملاء.

أجب باللغة العربية فقط.
اعتمد فقط على المعلومات الموجودة في السياق.
لا تشترط أن تكون كلمات السؤال مطابقة تماماً لكلمات السياق.
إذا كان المعنى موجوداً في السياق، أجب بناءً عليه.
إذا لم تجد أي معلومة مرتبطة بالسؤال داخل السياق، قل فقط:
لا توجد معلومات كافية في قاعدة المعرفة.

السياق:
{context}

السؤال:
{question}

الإجابة:
"""

    response = requests.post(
        CONFIG["ollama_url"],
        json={
            "model": CONFIG["ollama_model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": CONFIG["temperature"],
                "top_p": CONFIG["top_p"],
                "top_k": CONFIG["top_k"],
                "num_ctx": CONFIG["num_ctx"]
            }
        }
    )

    response.raise_for_status()
    return response.json()["response"]


# =========================
# 5. ESC exit
# =========================

def exit_on_esc():
    while True:
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch == b'\x1b':
                print("\n\nExiting... (Esc pressed)")
                os._exit(0)
            else:
                msvcrt.ungetch(ch)

        time.sleep(0.05)


# =========================
# 6. Main RAG
# =========================

docx_path = CONFIG["docx_path"]

text = read_docx(docx_path)

print("=" * 50)
print("DOCUMENT CONTENT:")
print("=" * 50)
print(text[:3000])
print("=" * 50)
print(f"Total characters: {len(text)}")

chunks = split_text(
    text,
    chunk_size=CONFIG["chunk_size"],
    overlap=CONFIG["overlap"]
)

print(f"Total chunks: {len(chunks)}")

embedding_model = SentenceTransformer(CONFIG["embedding_model"])

chroma_client = chromadb.Client()

try:
    chroma_client.delete_collection(CONFIG["collection_name"])
except:
    pass

collection = chroma_client.create_collection(CONFIG["collection_name"])

for i, chunk in enumerate(chunks):
    embedding = embed_document(embedding_model, chunk)

    collection.add(
        ids=[str(i)],
        documents=[chunk],
        embeddings=[embedding]
    )

threading.Thread(target=exit_on_esc, daemon=True).start()

print("\nRAG is ready. Ask your question. Press ESC to exit.")

while True:
    try:
        question = input("\nQuestion: ")

        if not question.strip():
            continue

        question_embedding = embed_question(embedding_model, question)

        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=CONFIG["n_results"],
            include=["documents", "distances"]
        )

        context = "\n\n".join(results["documents"][0])

        print("\n===== RETRIEVED CONTEXT =====")

        for doc, dist in zip(results["documents"][0], results["distances"][0]):
            print(f"\nDistance: {dist}")
            print(doc[:500])

        print("============================\n")

        answer = ask_ollama(question, context)

        print("\nAnswer:")
        print(answer)

    except (KeyboardInterrupt, EOFError):
        break
    except Exception as e:
        print("Error:", e)