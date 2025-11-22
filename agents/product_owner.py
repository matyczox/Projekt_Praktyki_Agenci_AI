from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

# Używamy Llamy 70B (Reasoning)
llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.2)

SYSTEM_PROMPT = """
Jesteś Technical Leadem (AI Copilot).
Twoim zadaniem jest analiza pomysłu użytkownika i stworzenie konkretnej SPECYFIKACJI TECHNICZNEJ.

ZASADY:
1. Olej korpo-gadkę i "cele biznesowe".
2. Skup się na TECHNIKALIACH: funkcje, logika, biblioteki.
3. Pisz w punktach. Krótko, zwięźle, technicznie.
4. To ma być instrukcja dla Architekta i Programisty.
5. Nie generuj kodu ani struktur plików.
"""

def product_owner_node(state: ProjectState) -> ProjectState:
    print("\n🧠 Tech Lead: Analizuję zadanie...")
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", f"Zadanie: {state['user_request']}")
    ])
    response = (prompt | llm).invoke({})
    return {
        "requirements": response.content,
        "logs": ["Tech Lead przygotował specyfikację."]
    }