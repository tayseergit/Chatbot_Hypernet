"""
Setup local model directory:
1. Creates models/paraphrase-multilingual-MiniLM-L12-v2/
2. Copies pytorch_model.bin from Downloads
3. Downloads tiny config files from HuggingFace (a few KB each)
4. Updates app config to use local path
"""

import os
import shutil
import urllib.request

SRC = r"C:\Users\ahmad\Downloads\pytorch_model.bin"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "paraphrase-multilingual-MiniLM-L12-v2")
BASE_URL = "https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/resolve/main/"

# Small config files to download (total < 3MB)
CONFIG_FILES = [
    "config.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentence_bert_config.json",
    "modules.json",
    "sentencepiece.bpe.model",
    "tokenizer.json",
]
POOLING_FILES = ["1_Pooling/config.json"]

def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"  Downloading {os.path.basename(dest)}...", end=" ", flush=True)
    urllib.request.urlretrieve(url, dest)
    size = os.path.getsize(dest)
    print(f"OK ({size:,} bytes)")

def main():
    # 1. Create model directory
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"[1/3] Model directory: {MODEL_DIR}")

    # 2. Copy pytorch_model.bin
    dest_bin = os.path.join(MODEL_DIR, "pytorch_model.bin")
    if os.path.exists(dest_bin):
        print(f"[2/3] pytorch_model.bin already exists, skipping copy.")
    elif os.path.exists(SRC):
        print(f"[2/3] Copying pytorch_model.bin ({os.path.getsize(SRC):,} bytes)...")
        shutil.copy2(SRC, dest_bin)
        print("      Copy complete!")
    else:
        print(f"[2/3] ERROR: Source file not found: {SRC}")
        return

    # 3. Download config files
    print("[3/3] Downloading config files...")
    for fname in CONFIG_FILES:
        dest = os.path.join(MODEL_DIR, fname)
        if os.path.exists(dest):
            print(f"  {fname} already exists, skipping.")
        else:
            download(BASE_URL + fname, dest)

    for fname in POOLING_FILES:
        dest = os.path.join(MODEL_DIR, fname)
        if os.path.exists(dest):
            print(f"  {fname} already exists, skipping.")
        else:
            download(BASE_URL + fname, dest)

    print("\n✅ Model ready at:", MODEL_DIR)
    print("\nNow update app_config.py embedding_model to:")
    print(f'    embedding_model: str = r"{MODEL_DIR}"')

if __name__ == "__main__":
    main()
