# agents/product_owner.py
"""
Agent Product Owner (Tech Lead).
Tworzy specyfikację techniczną na podstawie pomysłu użytkownika.
"""

from typing import Dict, Any
from agents.base import BaseAgent
from core.state import ProjectState
from prompts import PRODUCT_OWNER_PROMPT
from config import settings


class ProductOwnerAgent(BaseAgent):
    """
    Tech Lead - przekłada pomysł użytkownika na specyfikację techniczną.
    Nie zajmuje się architekturą ani strukturą plików.
    """
    
    @property
    def name(self) -> str:
        return "ProductOwner"
    
    @property
    def system_prompt(self) -> str:
        return PRODUCT_OWNER_PROMPT
    
    def __init__(self):
        super().__init__(
            model_name=settings.model_reasoning,
            temperature=0.2
        )
    
    def process(self, state: ProjectState) -> Dict[str, Any]:
        """
        Przetwarza request użytkownika i generuje specyfikację.
        
        Args:
            state: Stan z user_request
        
        Returns:
            Dict z requirements i logs
        """
        user_request = state.get("user_request", "")
        
        if not user_request:
            self.logger.warning("Brak user_request w stanie!")
            return {
                "requirements": "",
                "logs": ["Tech Lead: Brak zadania od użytkownika"]
            }
        
        user_message = f"Zadanie użytkownika:\n{user_request}"
        
        response = self.invoke(user_message)
        
        if response is None:
            return {
                "requirements": "",
                "logs": ["Tech Lead: Błąd generowania specyfikacji"]
            }
        
        self.logger.info("Specyfikacja gotowa")
        
        return {
            "requirements": response.content.strip(),
            "logs": ["Tech Lead przygotował czystą specyfikację."]
        }


# Instancja dla LangGraph node
_agent = ProductOwnerAgent()


def product_owner_node(state: ProjectState) -> Dict[str, Any]:
    """Node function dla LangGraph."""
    return _agent(state)