import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()

def _get_client_kwargs():
    """
    Konfiguracja klienta HTTP.
    """
    kwargs = {}
    
    # 1. SSL Fix
    verify_ssl = os.getenv("OLLAMA_VERIFY_SSL", "True").lower() == "true"
    kwargs["verify"] = verify_ssl
    
    # 2. Auth Token Fix
    token = os.getenv("OLLAMA_TOKEN")
    if token and token.strip():
        kwargs["headers"] = {"Authorization": f"Bearer {token}"}
        
    return kwargs

def get_chat_model(model_name: str = None, temperature: float = 0.2):
    """
    Zwraca model ChatOllama z logowaniem DEBUGOWANIA.
    """
    # Jeśli nie podano modelu, bierzemy z .env, a jak tam nie ma - bezpieczny fallback na mniejszy model
    if not model_name:
        model_name = os.getenv("MODEL_REASONING", "qwen3-coder:30b")
        
    # --- TU JEST KLUCZOWA ZMIANA ---
    # Wypisujemy w terminalu co się dzieje.
    print(f"🔌 [SYSTEM] Inicjalizuję połączenie z Ollama...")
    print(f"   -> Adres: {os.getenv('OLLAMA_BASE_URL')}")
    print(f"   -> Model: {model_name}")
    # -------------------------------

    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=model_name,
        temperature=temperature,
        
        # Fixy sieciowe
        timeout=300.0,    
        num_ctx=8192,
        client_kwargs=_get_client_kwargs()
    )

def get_embeddings_model():
    return OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("MODEL_EMBEDDINGS", "nomic-embed-text"),
        client_kwargs=_get_client_kwargs()
    )