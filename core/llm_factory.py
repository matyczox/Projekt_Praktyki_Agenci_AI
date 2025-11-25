import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN", "")
VERIFY_SSL = os.getenv("OLLAMA_VERIFY_SSL", "False").lower() == "true"

def get_llm(model_name: str, temperature: float = 0.1):
    """
    Automatycznie dobiera maksymalny kontekst w zależności od modelu.
    """
    if "qwen" in model_name.lower() and "coder" in model_name.lower():
        num_ctx = 200000   # Qwen3-coder łyka wszystko
        print(f"Qwen3-coder:30b → 200 000 tokenów (kodowanie full power!)")
    elif "llama3.3" in model_name.lower():
        num_ctx = 128000   # Llama3.3 oficjalnie 128k
        print(f"Llama3.3:70b → 128 000 tokenów (reasoning)")
    else:
        num_ctx = 32768
    
    return ChatOllama(
        model=model_name,
        base_url=OLLAMA_URL,
        temperature=temperature,
        num_ctx=num_ctx,
        timeout=900.0,
        client_kwargs={
            "verify": VERIFY_SSL,
            "headers": {"Authorization": f"Bearer {OLLAMA_TOKEN}"} if OLLAMA_TOKEN else {}
        }
    )

# Dla reszty agentów (PO, Architekt, QA) – zawsze Llama
def get_chat_model(temperature: float = 0.2):
    model = os.getenv("MODEL_REASONING", "llama3.3:70b")
    return get_llm(model, temperature)

# Dla Developera – zawsze Qwen
def get_coder_model(temperature: float = 0.0):
    model = os.getenv("MODEL_CODER", "qwen3-coder:30b")
    return get_llm(model, temperature)

def get_embeddings_model():
    model = os.getenv("MODEL_EMBEDDINGS", "nomic-embed-text")
    return OllamaEmbeddings(
        base_url=OLLAMA_URL,
        model=model,
        client_kwargs={
            "verify": VERIFY_SSL,
            "headers": {"Authorization": f"Bearer {OLLAMA_TOKEN}"} if OLLAMA_TOKEN else {}
        }
    )