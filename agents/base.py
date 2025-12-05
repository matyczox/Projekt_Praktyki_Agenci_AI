# agents/base.py
"""
Klasa bazowa dla wszystkich agentów.
Wspólna logika: inicjalizacja LLM, budowanie promptów, obsługa błędów.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from services.llm_service import llm_service
from core.state import ProjectState
from utils.logger import get_agent_logger


class BaseAgent(ABC):
    """
    Abstrakcyjna klasa bazowa dla agentów AgileFlow.
    
    Każdy agent musi zaimplementować:
    - name: nazwa agenta
    - system_prompt: prompt systemowy
    - process(): logika przetwarzania
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Inicjalizuje agenta z modelem LLM.
        
        Args:
            model_name: Nazwa modelu (domyślnie z config)
            temperature: Temperatura generowania
        """
        self.logger = get_agent_logger(self.name)
        self._model_name = model_name
        self._temperature = temperature
        self._llm = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nazwa agenta (do logowania)."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Prompt systemowy agenta."""
        pass
    
    @property
    def llm(self):
        """Lazy-loaded instancja LLM."""
        if self._llm is None:
            self._llm = llm_service.get_chat_model(
                model_name=self._model_name,
                temperature=self._temperature
            )
        return self._llm
    
    def build_messages(self, user_message: str) -> List[BaseMessage]:
        """
        Tworzy listę wiadomości do LLM.
        Używa bezpośrednich Message obiektów zamiast template,
        żeby uniknąć problemów z {} w kodzie.
        
        Args:
            user_message: Wiadomość użytkownika
        
        Returns:
            Lista wiadomości
        """
        return [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_message)
        ]
    
    def invoke(self, user_message: str) -> Optional[BaseMessage]:
        """
        Wywołuje LLM z obsługą błędów.
        
        Args:
            user_message: Wiadomość do LLM
        
        Returns:
            Odpowiedź LLM lub None
        """
        self.logger.info("Rozpoczynam przetwarzanie...")
        
        try:
            messages = self.build_messages(user_message)
            response = self.llm.invoke(messages)
            
            # Loguj użycie tokenów jeśli dostępne
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                input_tokens = metadata.get("prompt_eval_count", "?")
                output_tokens = metadata.get("eval_count", "?")
                self.logger.debug(f"Tokeny: input={input_tokens}, output={output_tokens}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Błąd wywołania LLM: {e}")
            raise
    
    @abstractmethod
    def process(self, state: ProjectState) -> Dict[str, Any]:
        """
        Przetwarza stan i zwraca aktualizacje.
        
        Args:
            state: Aktualny stan projektu
        
        Returns:
            Słownik z aktualizacjami stanu
        """
        pass
    
    def __call__(self, state: ProjectState) -> Dict[str, Any]:
        """
        Pozwala używać agenta jako node w LangGraph.
        
        Args:
            state: Stan projektu
        
        Returns:
            Aktualizacje stanu
        """
        return self.process(state)
