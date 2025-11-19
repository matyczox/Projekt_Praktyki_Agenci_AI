from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState

# Architekt musi być mądry, więc też używamy modelu Reasoning (Llama 3.3)
llm = get_chat_model(temperature=0.1)

ARCHITECT_SYSTEM_PROMPT = """
Jesteś Głównym Architektem Systemu (Solution Architect).
Twoim zadaniem jest zaprojektować rozwiązanie techniczne na podstawie wymagań biznesowych.

Twoja odpowiedź MUSI zawierać:
1. **Stack Technologiczny**: Język, frameworki, baza danych.
2. **Struktura Projektu**: Lista plików i folderów, które należy utworzyć.
3. **Plan Implementacji**: Krótka instrukcja dla programisty, od czego zacząć.

PAMIĘTAJ:
- Projekt musi być w Pythonie.
- Strukturę plików przedstaw jako listę wypunktowaną.
- Nie pisz jeszcze pełnego kodu, tylko nazwy plików i co mają robić.
"""

def architect_node(state: ProjectState) -> ProjectState:
    print("\n📐 Architekt: Projektuję strukturę systemu...")
    
    # Pobieramy wymagania ze stanu (to co wypluł wcześniej PO)
    requirements = state.get("requirements", "Brak wymagań.")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ARCHITECT_SYSTEM_PROMPT),
        ("user", f"Oto wymagania od Product Ownera:\n\n{requirements}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({})
    
    print("✅ Architekt: Plan techniczny gotowy.")
    
    # Zapisujemy plan do stanu, żeby Developer mógł go przeczytać
    return {
        "tech_stack": response.content,
        "logs": ["Architekt stworzył strukturę plików."]
    }