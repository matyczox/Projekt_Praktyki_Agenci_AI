from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState

llm = get_chat_model(temperature=0.1)

# --- ZMIANA: Dodaliśmy instrukcje o README i requirements ---
ARCHITECT_SYSTEM_PROMPT = """
Jesteś Głównym Architektem Systemu.
Twoim zadaniem jest zaprojektować rozwiązanie techniczne na podstawie wymagań.

WYMAGANIA KRYTYCZNE:
1. Stack technologiczny: Python.
2. ZAWSZE uwzględnij plik 'requirements.txt' z listą bibliotek (np. pygame, pandas).
3. ZAWSZE uwzględnij plik 'README.md' z instrukcją, jak zainstalować zależności i uruchomić program.
4. Rozbij kod na sensowne moduły, jeśli projekt jest duży.

Twoja odpowiedź to plan dla Developera.
"""

def architect_node(state: ProjectState) -> ProjectState:
    print("\n📐 Architekt: Projektuję strukturę systemu...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ARCHITECT_SYSTEM_PROMPT),
        ("user", f"Wymagania od PO:\n{state.get('requirements')}")
    ])
    
    print("📐 Architekt: Generuję plan techniczny...")
    response = (prompt | llm).invoke({})
    
    return {
        "tech_stack": response.content,
        "logs": ["Architekt stworzył strukturę z dokumentacją."]
    }