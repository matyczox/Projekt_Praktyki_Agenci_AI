# core/state.py
"""
Definicja stanu projektu dla LangGraph.
"""

import operator
from typing import Annotated, List, Dict
from typing_extensions import TypedDict


class ProjectState(TypedDict):
    """
    Stan projektu przepływający przez workflow LangGraph.
    
    Atrybuty:
        user_request: Oryginalne żądanie użytkownika
        requirements: Specyfikacja techniczna od Product Ownera
        tech_stack: Plan architektury od Architekta (z listą plików)
        generated_code: Słownik {filename: content} wygenerowanego kodu
        qa_feedback: Feedback od QA (jeśli REJECTED)
        qa_status: Status QA - "APPROVED" lub "REJECTED"
        iteration_count: Licznik pętli developer-QA
        logs: Lista logów z całego procesu (akumulowana)
    """
    user_request: str
    requirements: str
    tech_stack: str
    generated_code: Dict[str, str]
    qa_feedback: str
    qa_status: str
    iteration_count: int
    logs: Annotated[List[str], operator.add]


def create_initial_state(user_request: str) -> ProjectState:
    """
    Tworzy początkowy stan projektu.
    
    Args:
        user_request: Żądanie użytkownika
    
    Returns:
        Zainicjalizowany ProjectState
    """
    return {
        "user_request": user_request,
        "requirements": "",
        "tech_stack": "",
        "generated_code": {},
        "qa_feedback": "",
        "qa_status": "",
        "iteration_count": 0,
        "logs": []
    }