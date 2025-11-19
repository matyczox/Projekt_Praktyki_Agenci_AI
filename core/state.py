import operator
from typing import Annotated, List, TypedDict, Dict

class ProjectState(TypedDict):
    # --- Input ---
    user_request: str
    
    # --- PO & Architekt ---
    requirements: str
    tech_stack: str
    
    # --- Kod ---
    # Słownik: { "main.py": "print('hello')" }
    generated_code: Dict[str, str]
    
    # --- QA & Pętla ---
    qa_feedback: str        # Co QA myśli o kodzie (np. "Brakuje obsługi błędów")
    qa_status: str          # "APPROVED" lub "REJECTED"
    iteration_count: int    # Licznik pętli (żeby nie poprawiali w nieskończoność)
    
    # --- Logi ---
    logs: Annotated[List[str], operator.add]