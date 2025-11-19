import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()

def _get_client_kwargs():
    """
    Konfiguracja klienta HTTP.
    Obsługuje wyłączenie SSL i Tokeny Auth.
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
    Zwraca model ChatOllama z ustawieniami 'Battle-Tested':
    - Timeout 300s (na cold start)
    - Context 8k (na długi kod)
    """
    if not model_name:
        model_name = os.getenv("MODEL_REASONING", "llama3.3:70b")
        
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=model_name,
        
        # --- CRITICAL FIXES OD KOLEGI ---
        temperature=temperature,
        timeout=300.0,    # 5 minut timeoutu (modele 70B wolno wstają)
        num_ctx=8192,     # Większe okno kontekstowe (nie utnie kodu)
        # --------------------------------
        
        client_kwargs=_get_client_kwargs()
    )

def get_embeddings_model():
    """
    Model do RAG z tymi samymi fixami sieciowymi.
    """
    return OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("MODEL_EMBEDDINGS", "embeddinggemma:300m"),
        client_kwargs=_get_client_kwargs()
    )