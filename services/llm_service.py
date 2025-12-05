# services/llm_service.py
"""
Serwis LLM - ujednolicony dostęp do modeli Ollama.
Obsługuje błędy, retry, timeout i logowanie.
"""

from typing import Optional, Dict, Any
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.messages import BaseMessage
from config import settings
from utils.logger import get_service_logger

logger = get_service_logger("llm")


class LLMService:
    """
    Centralny serwis do zarządzania modelami LLM.
    Zapewnia spójną konfigurację i obsługę błędów.
    """
    
    def __init__(self):
        self._models_cache: Dict[str, ChatOllama] = {}
        self._embeddings: Optional[OllamaEmbeddings] = None
    
    def _get_client_kwargs(self) -> Dict[str, Any]:
        """Konfiguracja klienta HTTP dla Ollama."""
        kwargs = {"verify": settings.ollama_verify_ssl}
        
        if settings.ollama_token:
            kwargs["headers"] = {"Authorization": f"Bearer {settings.ollama_token}"}
        
        return kwargs
    
    def get_chat_model(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> ChatOllama:
        """
        Zwraca model ChatOllama z cache'owaniem.
        
        Args:
            model_name: Nazwa modelu (domyślnie z config)
            temperature: Temperatura generowania (domyślnie z config)
        
        Returns:
            Skonfigurowana instancja ChatOllama
        """
        model_name = model_name or settings.model_reasoning
        temperature = temperature if temperature is not None else settings.llm_temperature_default
        
        cache_key = f"{model_name}_{temperature}"
        
        if cache_key not in self._models_cache:
            logger.info(f"Inicjalizuję model: {model_name} (temp={temperature})")
            logger.debug(f"URL: {settings.ollama_base_url}")
            
            self._models_cache[cache_key] = ChatOllama(
                base_url=settings.ollama_base_url,
                model=model_name,
                temperature=temperature,
                timeout=settings.ollama_timeout,
                num_ctx=settings.llm_num_ctx,
                num_predict=settings.llm_num_predict,
                client_kwargs=self._get_client_kwargs()
            )
        
        return self._models_cache[cache_key]
    
    def get_embeddings(self) -> OllamaEmbeddings:
        """
        Zwraca model embeddingów (singleton).
        
        Returns:
            Skonfigurowana instancja OllamaEmbeddings
        """
        if self._embeddings is None:
            logger.info(f"Inicjalizuję embeddings: {settings.model_embeddings}")
            
            self._embeddings = OllamaEmbeddings(
                base_url=settings.ollama_base_url,
                model=settings.model_embeddings,
                client_kwargs=self._get_client_kwargs()
            )
        
        return self._embeddings
    
    def invoke_with_retry(
        self,
        model: ChatOllama,
        messages: list,
        max_retries: int = 2
    ) -> Optional[BaseMessage]:
        """
        Wywołuje model z obsługą błędów i retry.
        
        Args:
            model: Model ChatOllama
            messages: Lista wiadomości
            max_retries: Maksymalna liczba prób
        
        Returns:
            Odpowiedź modelu lub None przy błędzie
        """
        for attempt in range(max_retries + 1):
            try:
                return model.invoke(messages)
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Błąd LLM (próba {attempt + 1}/{max_retries + 1}): {e}")
                else:
                    logger.error(f"LLM zwrócił błąd po {max_retries + 1} próbach: {e}")
                    raise
        
        return None


# Singleton dla całej aplikacji
llm_service = LLMService()
