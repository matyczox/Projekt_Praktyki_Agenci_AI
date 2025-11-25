from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

QA_SYSTEM_PROMPT = """
Jesteś bardzo surowym QA Engineerem.

ZASADY:
1. Jeśli kod jest kompletny, działający, bezpieczny i ma README + requirements.txt → odpowiedz TYLKO: APPROVED
2. Jeśli cokolwiek jest źle (brak pliku, błąd logiczny, zły format, brak main loop, crash przy uruchomieniu itp.) → odpowiedz:
REJECTED: <krótki, konkretny opis błędu i który plik>

Przykłady:
REJECTED: Brak pliku main.py
REJECTED: Wąż nie rośnie po zjedzeniu jedzenia (snake_game.py)
REJECTED: Brak obsługi klawiszy strzałek
"""

def qa_node(state: ProjectState) -> ProjectState:
    print("\nQA: Sprawdzam kod...")
    code_dict = state.get("generated_code", {})

    if not code_dict:
        return {"qa_status": "REJECTED", "qa_feedback": "Brak wygenerowanego kodu!"}

    # Sprawdzenie składni Pythona
    for filename, content in code_dict.items():
        if filename.endswith(".py"):
            try:
                compile(content, filename, 'exec')
            except SyntaxError as e:
                return {"qa_status": "REJECTED", "qa_feedback": f"Błąd składni w {filename}: {e}"}

    full_code = "\n".join([f"--- {k} ---\n{v}" for k, v in code_dict.items()])

    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        ("user", "Sprawdź kod:\n\n{code}")
    ])

    print("QA: Analiza logiki przez LLM...")
    response = (prompt | llm).invoke({"code": full_code})
    decision = response.content.strip()

    status = "APPROVED" if "APPROVED" in decision.upper() else "REJECTED"
    print(f"QA Decyzja: {status}")

    return {
        "qa_status": status,
        "qa_feedback": decision,
        "iteration_count": state.get("iteration_count", 0) + 1
    }