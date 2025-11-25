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
    Zwraca model ChatOllama z DUŻYM context window.
    """
    if not model_name:
        model_name = os.getenv("MODEL_REASONING", "llama3.3:70b")
        
    print(f"🔌 [SYSTEM] Inicjalizuję połączenie z Ollama...")
    print(f"   -> Adres: {os.getenv('OLLAMA_BASE_URL')}")
    print(f"   -> Model: {model_name}")

    # Dobierz context automatycznie na podstawie modelu
    if "qwen" in model_name.lower():
        ctx_size = 24576  # 24k dla Qwen
    elif "llama3.3" in model_name.lower():
        ctx_size = 32768  # 32k dla Llama 3.3
    elif "codellama" in model_name.lower():
        ctx_size = 16384  # 16k dla CodeLlama
    else:
        ctx_size = 8192   # Fallback
    
    print(f"   -> Context: {ctx_size} tokenów")

    # ============================================
    # SPECJALNE OPCJE DLA QWEN (FIX EMPTY OUTPUT)
    # ============================================
    model_kwargs = {}
    
    if "qwen" in model_name.lower():
        # Qwen potrzebuje tych parametrów żeby generować więcej
        model_kwargs = {
            "top_p": 0.9,           # Diversity sampling
            "top_k": 40,            # Rozważ top 40 tokenów
            "repeat_penalty": 1.1,  # Nie powtarzaj się
            "num_predict": 2048,    # Generuj minimum 2048 tokenów (był default 128!)
        }
        print(f"   -> Tryb: Qwen Extended Generation")
        print(f"   -> Min tokens: 2048")
    # ============================================

    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        model=model_name,
        temperature=temperature,
        
        # Zwiększony timeout dla dużych modeli
        timeout=600.0,
        
        # Context window
        num_ctx=ctx_size,
        
        # Dodatkowe parametry modelu
        **model_kwargs,
        
        client_kwargs=_get_client_kwargs()
    )

def get_embeddings_model():
    return OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        model=os.getenv("MODEL_EMBEDDINGS", "nomic-embed-text"),
        client_kwargs=_get_client_kwargs()
    )