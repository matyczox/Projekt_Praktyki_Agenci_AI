# agents/architect.py
"""
Agent Architekt.
Projektuje strukturę plików projektu z wykorzystaniem RAG.
"""

from typing import Dict, Any
from agents.base import BaseAgent
from core.state import ProjectState
from prompts import ARCHITECT_PROMPT
from services.vector_store_service import vector_store_service
from config import settings


class ArchitectAgent(BaseAgent):
    """
    Architekt - projektuje strukturę plików projektu.
    Korzysta z RAG do wyszukiwania podobnych projektów jako inspiracji.
    """
    
    @property
    def name(self) -> str:
        return "Architect"
    
    @property
    def system_prompt(self) -> str:
        return ARCHITECT_PROMPT
    
    def __init__(self):
        super().__init__(
            model_name=settings.model_reasoning,
            temperature=0.1
        )
    
    def _build_rag_context(self, query: str) -> str:
        """
        Buduje kontekst RAG z podobnych projektów.
        
        Args:
            query: Zapytanie do wyszukiwania
        
        Returns:
            Sformatowany kontekst lub pusty string
        """
        similar = vector_store_service.search_similar(query, k=8)
        
        if not similar:
            self.logger.debug("Brak podobnych projektów w RAG")
            return ""
        
        context = "\n\nISTNIEJĄCE PODOBNE PROJEKTY (użyj jako inspiracja):\n"
        
        for item in similar[:5]:
            content_preview = item['content'][:1500]
            context += f"\n=== {item['project']} / {item['filename']} ===\n{content_preview}\n"
        
        self.logger.info(f"Znaleziono {len(similar)} podobnych projektów w RAG")
        return context
    
    def process(self, state: ProjectState) -> Dict[str, Any]:
        """
        Projektuje strukturę plików na podstawie specyfikacji.
        
        Args:
            state: Stan z requirements
        
        Returns:
            Dict z tech_stack i logs
        """
        requirements = state.get("requirements", "")
        user_request = state.get("user_request", "")
        
        # Buduj zapytanie RAG
        rag_query = f"{user_request}\n{requirements}"
        rag_context = self._build_rag_context(rag_query)
        
        user_message = f"""Specyfikacja techniczna od Tech Leada:
{requirements if requirements else 'Brak specyfikacji'}
{rag_context}
Na podstawie powyższego zaprojektuj strukturę plików.
Podaj krótki opis projektu, listę plików z opisami i na samym końcu dokładnie jeden czysty blok JSON z listą nazw plików."""
        
        response = self.invoke(user_message)
        
        if response is None:
            return {
                "tech_stack": "",
                "logs": ["Architekt: Błąd projektowania struktury"]
            }
        
        self.logger.info("Struktura projektu gotowa")
        
        return {
            "tech_stack": response.content,
            "logs": ["Architekt zaprojektował strukturę z wykorzystaniem RAG"]
        }


# Instancja dla LangGraph node
_agent = ArchitectAgent()


def architect_node(state: ProjectState) -> Dict[str, Any]:
    """Node function dla LangGraph."""
    return _agent(state)