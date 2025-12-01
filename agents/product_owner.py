# agents/product_owner.py
from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

llm = get_chat_model(os.getenv("MODEL_REASONING", "qwen2.5-coder:14b"), temperature=0.2)

SYSTEM_PROMPT = """
Jesteś Technical Leadem (AI Copilot).
Twoim JEDYNYM zadaniem jest przełożyć pomysł użytkownika na CZYSTĄ, TECHNICZNĄ SPECYFIKACJĘ.

ZASADY ABSOLUTNE:
- Piszesz TYLKO specyfikację techniczną (funkcje, biblioteki, logika, wymagania).
- NIGDY nie piszesz o strukturze plików, nazwach modułów, architekturze projektu.
- NIGDY nie sugerujesz "main.py", "game.py", "snake.py" itp.
- NIGDY nie piszesz sekcji "Architektura", "Moduły", "Plan projektu".
- Nie generujesz JSON-a z listą plików.
- Nie wspominasz o README.md.

DOZWOLONE sekcje:
- Cele funkcjonalne
- Wymagane biblioteki
- Opis mechanik gry
- Sterowanie
- Warunki końca gry
- Punktacja
- Inne czysto techniczne rzeczy

PRZYKŁAD POPRAWNEJ ODPOWIEDZI:

Gra Snake w Pythonie z użyciem pygame.

Funkcjonalności:
- Wąż porusza się po siatce, sterowany strzałkami
- Zjada jabłka → rośnie i dostaje punkty
- Kolizja z granicą lub sobą → koniec gry
- Punktacja wyświetlana na ekranie
- Możliwość restartu po przegranej

Wymagane biblioteki:
- pygame
- random

Mechanika:
- Plansza 600x600 px, siatka 20x20 pól
- Wąż zaczyna z długością 3, prędkość rośnie co 10 punktów
- Jabłko pojawia się losowo po zjedzeniu
"""

def product_owner_node(state: ProjectState) -> ProjectState:
    print("\nTech Lead: Analizuję zadanie...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", f"Zadanie użytkownika:\n{state['user_request']}")
    ])
    
    response = (prompt | llm).invoke({})
    
    print("TOKENS → Input:", response.response_metadata.get("prompt_eval_count", "?"), 
          "| Output:", response.response_metadata.get("eval_count", "?"))
    
    return {
        "requirements": response.content.strip(),
        "logs": ["Tech Lead przygotował czystą specyfikację."]
    }