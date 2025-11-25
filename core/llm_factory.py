import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()

# Globalne ustawienia z .env
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN", "")
VERIFY_SSL = os.getenv("OLLAMA_VERIFY_SSL", "False").lower() == "true"

def get_llm(model_name: str, temperature: float = 0.1, num_ctx: int = 8192):
    """
    Tworzy instancję modelu z odpowiednimi parametrami (Timeout, SSL, Context).
    UWAGA: Uproszczona wersja - BEZ dodatkowych model_kwargs które mogą powodować konflikty.
    """
    print(f"🔌 [SYSTEM] Inicjalizuję model...")
    print(f"   -> Adres: {OLLAMA_URL}")
    print(f"   -> Model: {model_name}")
    print(f"   -> Context: {num_ctx} tokenów")
    
    return ChatOllama(
        model=model_name,
        base_url=OLLAMA_URL,
        temperature=temperature,
        num_ctx=num_ctx,
        timeout=300.0,  # 5 minut (jak u kolegi)
        
        client_kwargs={
            "verify": VERIFY_SSL,
            "headers": {"Authorization": f"Bearer {OLLAMA_TOKEN}"} if OLLAMA_TOKEN else {}
        }
    )

# Alias dla kompatybilności z Twoim kodem
def get_chat_model(model_name: str = None, temperature: float = 0.2):
    """
    Wrapper dla kompatybilności z Twoim kodem.
    """
    if not model_name:
        model_name = os.getenv("MODEL_REASONING", "llama3.3:70b")
    
    # Dobierz context na podstawie modelu
    if "qwen" in model_name.lower():
        num_ctx = 24000  # Jak u kolegi dla Qwen
    elif "llama3.3" in model_name.lower():
        num_ctx = 32000
    else:
        num_ctx = 8192
    
    return get_llm(model_name, temperature=temperature, num_ctx=num_ctx)

def get_embeddings_model():
    return OllamaEmbeddings(
        base_url=OLLAMA_URL,
        model=os.getenv("MODEL_EMBEDDINGS", "nomic-embed-text"),
        client_kwargs={
            "verify": VERIFY_SSL,
            "headers": {"Authorization": f"Bearer {OLLAMA_TOKEN}"} if OLLAMA_TOKEN else {}
        }
    )