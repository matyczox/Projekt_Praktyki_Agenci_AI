# agents/qa.py
"""
Agent QA Engineer.
Audytuje kod pod kątem kompletności i poprawności.
"""

import re
from typing import Dict, Any, Optional
from agents.base import BaseAgent
from core.state import ProjectState
from prompts import QA_PROMPT
from config import settings


class QAAgent(BaseAgent):
    """
    QA Engineer - audytuje kod pod kątem jakości.
    Wykonuje automatyczne checky składni + AI review logiki.
    """
    
    @property
    def name(self) -> str:
        return "QA"
    
    @property
    def system_prompt(self) -> str:
        return QA_PROMPT
    
    def __init__(self):
        super().__init__(
            model_name=settings.model_reasoning,
            temperature=0.1
        )
    
    def _check_python_syntax(self, filename: str, content: str) -> Optional[str]:
        """Sprawdza składnię Pythona."""
        try:
            compile(content, filename, 'exec')
            return None
        except SyntaxError as e:
            return f"Błąd składni Python w {filename}: {e.msg} (linia {e.lineno})"
    
    def _check_javascript_syntax(self, filename: str, content: str) -> Optional[str]:
        """Podstawowe sprawdzenie JavaScript."""
        # Sprawdź czy nie ma var
        if re.search(r'\bvar\s+\w+', content):
            return f"W {filename} użyto 'var' zamiast 'const'/'let' (bad practice)"
        
        # Sprawdź balans klamer
        if content.count('{') != content.count('}'):
            return f"W {filename} niezbalansowane nawiasy klamrowe"
        
        return None
    
    def _check_html_syntax(self, filename: str, content: str) -> Optional[str]:
        """Podstawowe sprawdzenie HTML."""
        if not re.search(r'<!DOCTYPE html>', content, re.IGNORECASE):
            return f"W {filename} brakuje <!DOCTYPE html>"
        
        if '<html' not in content or '</html>' not in content:
            return f"W {filename} brakuje tagów <html>"
        
        return None
    
    def _check_css_syntax(self, filename: str, content: str) -> Optional[str]:
        """Podstawowe sprawdzenie CSS."""
        if content.count('{') != content.count('}'):
            return f"W {filename} niezbalansowane nawiasy klamrowe"
        
        return None
    
    def quick_syntax_check(self, filename: str, content: str) -> Optional[str]:
        """
        Szybkie sprawdzenie składni dla różnych języków.
        
        Args:
            filename: Nazwa pliku
            content: Zawartość pliku
        
        Returns:
            Opis błędu lub None jeśli OK
        """
        if filename.endswith(".py"):
            return self._check_python_syntax(filename, content)
        elif filename.endswith(".js"):
            return self._check_javascript_syntax(filename, content)
        elif filename.endswith(".html"):
            return self._check_html_syntax(filename, content)
        elif filename.endswith(".css"):
            return self._check_css_syntax(filename, content)
        
        return None
    
    def process(self, state: ProjectState) -> Dict[str, Any]:
        """
        Audytuje wygenerowany kod.
        
        Args:
            state: Stan z generated_code
        
        Returns:
            Dict z qa_status, qa_feedback, iteration_count, logs
        """
        code_dict = state.get("generated_code", {})
        iteration = state.get("iteration_count", 0)
        
        if not code_dict:
            self.logger.warning("Brak kodu do sprawdzenia!")
            return {
                "qa_status": "REJECTED",
                "qa_feedback": "Developer nie wygenerował żadnego kodu!",
                "iteration_count": iteration + 1,
                "logs": ["QA: Brak kodu do sprawdzenia"]
            }
        
        # ETAP 1: Automatyczne sprawdzenie składni
        self.logger.info(f"Sprawdzam składnię ({len(code_dict)} plików)...")
        
        for filename, content in code_dict.items():
            syntax_error = self.quick_syntax_check(filename, content)
            if syntax_error:
                self.logger.warning(f"Auto-reject: {syntax_error}")
                return {
                    "qa_status": "REJECTED",
                    "qa_feedback": syntax_error,
                    "iteration_count": iteration + 1,
                    "logs": [f"QA Auto-Reject: {filename}"]
                }
        
        self.logger.info("Składnia OK, przechodzę do analizy AI...")
        
        # ETAP 2: AI review (logika, kompletność)
        full_code = "\n\n".join([f"=== {k} ===\n{v}" for k, v in code_dict.items()])
        
        user_message = f"Sprawdź poniższy kod:\n\n{full_code}"
        
        response = self.invoke(user_message)
        
        if response is None:
            return {
                "qa_status": "REJECTED",
                "qa_feedback": "Błąd analizy AI",
                "iteration_count": iteration + 1,
                "logs": ["QA: Błąd wywołania AI"]
            }
        
        # Parsuj decyzję
        decision = response.content.strip()
        status = "APPROVED" if "APPROVED" in decision else "REJECTED"
        
        if status == "APPROVED":
            self.logger.info("APPROVED - Kod jest OK!")
        else:
            self.logger.warning(f"REJECTED: {decision[:100]}...")
        
        return {
            "qa_status": status,
            "qa_feedback": decision,
            "iteration_count": iteration + 1,
            "logs": [f"QA: {status}"]
        }


# Instancja dla LangGraph node
_agent = QAAgent()


def qa_node(state: ProjectState) -> Dict[str, Any]:
    """Node function dla LangGraph."""
    return _agent(state)