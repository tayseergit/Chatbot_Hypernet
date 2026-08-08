from sentence_transformers import SentenceTransformer

# List of models to download
models = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # This is the default one
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "intfloat/multilingual-e5-base",
]

print("Starting model downloads. This may take a while depending on your internet connection...\n")

for model_name in models:
    print(f"Downloading: {model_name}")
    # Instantiating the SentenceTransformer automatically triggers the download
    # if the model is not already cached locally.
    SentenceTransformer(model_name)
    print(f"Successfully downloaded and cached: {model_name}\n")

print("All models have been downloaded! You can now freely switch between them in app_config.py.")
