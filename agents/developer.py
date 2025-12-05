# agents/developer.py
"""
Agent Developer.
Generuje kompletny kod dla każdego pliku z listy Architekta.
"""

from typing import Dict, Any, List
from agents.base import BaseAgent
from core.state import ProjectState
from prompts import DEVELOPER_PROMPT
from services.file_service import file_service
from utils.parsers import parse_code_blocks, extract_file_list
from config import settings


class DeveloperAgent(BaseAgent):
    """
    Developer - generuje kompletny, działający kod.
    Obsługuje zarówno pierwszą implementację jak i poprawki po QA.
    """
    
    @property
    def name(self) -> str:
        return "Developer"
    
    @property
    def system_prompt(self) -> str:
        return DEVELOPER_PROMPT
    
    def __init__(self):
        super().__init__(
            model_name=settings.model_reasoning,
            temperature=0.2
        )
    
    def _build_file_list_str(self, file_list: List[str]) -> str:
        """Formatuje listę plików do promptu."""
        if not file_list:
            return "Architekt nie dostarczył jasnej listy - wygeneruj pliki samodzielnie na podstawie specyfikacji."
        return "\n".join([f"- {f}" for f in file_list])
    
    def _build_context(self, state: ProjectState) -> str:
        """Buduje kontekst dla LLM (pierwsza implementacja vs poprawka)."""
        iteration = state.get("iteration_count", 0)
        qa_feedback = state.get("qa_feedback", "")
        
        if iteration > 0 and qa_feedback:
            return f"""
=== POPRAWKA (Iteracja {iteration}) ===
QA odrzuciło kod z powodu:
{qa_feedback}

NAPRAW DOKŁADNIE TO CO WSKAZALI POWYŻEJ.
"""
        return "=== PIERWSZA IMPLEMENTACJA ==="
    
    def _check_missing_files(self, file_list: List[str], generated: Dict[str, str]) -> List[str]:
        """Sprawdza czy wszystkie pliki zostały wygenerowane."""
        if not file_list:
            return []
        return [f for f in file_list if f not in generated]
    
    def process(self, state: ProjectState) -> Dict[str, Any]:
        """
        Generuje kod dla wszystkich plików z listy Architekta.
        
        Args:
            state: Stan z tech_stack, requirements, qa_feedback
        
        Returns:
            Dict z generated_code i logs
        """
        # Pobierz listę plików od Architekta
        tech_stack = state.get("tech_stack", "")
        file_list = extract_file_list(tech_stack)
        
        if file_list:
            self.logger.info(f"Lista plików: {file_list}")
        else:
            self.logger.warning("Architekt nie dostarczył listy plików")
        
        # Buduj prompt
        context = self._build_context(state)
        file_list_str = self._build_file_list_str(file_list)
        
        user_message = f"""
{context}

SPECYFIKACJA:
{state.get('requirements', '')}

STRUKTURA PROJEKTU:
{tech_stack}

LISTA PLIKÓW DO WYGENEROWANIA:
{file_list_str}

Wygeneruj KOMPLETNY kod dla każdego pliku.
Użyj formatu:
--- filename ---
```language
kod
```
"""
        
        # Wywołaj LLM
        response = self.invoke(user_message)
        
        if response is None:
            return {
                "generated_code": {},
                "logs": ["Developer: Błąd generowania kodu"]
            }
        
        # Parsuj odpowiedź
        generated_code = parse_code_blocks(response.content)
        
        if not generated_code:
            self.logger.error("Parser nie wyciągnął żadnego kodu!")
            # Zapisz debug do pliku
            try:
                with open("debug_llm_response.txt", "w", encoding="utf-8") as f:
                    f.write(response.content)
                self.logger.info("Zapisano debug do debug_llm_response.txt")
            except Exception:
                pass
            
            return {
                "generated_code": {},
                "logs": ["Developer: Błąd parsowania odpowiedzi LLM"]
            }
        
        self.logger.info(f"Wygenerowano {len(generated_code)} plików")
        
        # Sprawdź brakujące pliki
        missing = self._check_missing_files(file_list, generated_code)
        if missing:
            self.logger.warning(f"Brakujące pliki: {missing}")
        
        # Zapisz pliki na dysk
        save_results = file_service.save_files(generated_code)
        
        saved_count = sum(save_results.values())
        failed = [f for f, ok in save_results.items() if not ok]
        
        if failed:
            self.logger.warning(f"Nie zapisano: {failed}")
        
        return {
            "generated_code": generated_code,
            "logs": [f"Developer wygenerował {len(generated_code)} plików, zapisano {saved_count}."]
        }


# Instancja dla LangGraph node
_agent = DeveloperAgent()


def developer_node(state: ProjectState) -> Dict[str, Any]:
    """Node function dla LangGraph."""
    return _agent(state)