from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

QA_SYSTEM_PROMPT = """
Jesteś QA Engineerem. Oceń kod pod kątem logiki i bezpieczeństwa.
Jeśli kod wygląda dobrze, odpisz tylko 'APPROVED'.
Jeśli są błędy, odpisz 'REJECTED: <opis co poprawić>'.
"""

def qa_node(state: ProjectState) -> ProjectState:
    print("\n🕵️‍♂️ QA: Rozpoczynam sprawdzanie...")
    code_dict = state.get("generated_code", {})
    
    if not code_dict:
        return {"qa_status": "REJECTED", "qa_feedback": "Brak kodu!", "logs": ["QA: Pusto"]}

    # --- NOWOŚĆ: AUTOMATYCZNY TEST SKŁADNI (LINTING) ---
    # Zanim zapytamy AI, sprawdzamy czy kod w ogóle jest poprawnym Pythonem.
    for filename, content in code_dict.items():
        if filename.endswith(".py"):
            try:
                # Próbujemy skompilować kod. Jak jest błąd, Python rzuci wyjątek.
                compile(content, filename, 'exec')
            except SyntaxError as e:
                error_msg = f"BŁĄD SKŁADNI (SyntaxError) w pliku {filename}: {e}"
                print(f"🕵️‍♂️ QA (Auto-Check): ❌ {error_msg}")
                return {
                    "qa_status": "REJECTED",
                    "qa_feedback": f"KRYTYCZNY BŁĄD: Kod nie działa. {error_msg}. Popraw to natychmiast.",
                    "iteration_count": state.get("iteration_count", 0) + 1,
                    "logs": [f"QA Auto-Reject: {filename}"]
                }
    # ----------------------------------------------------

    full_code = "\n".join([f"--- {k} ---\n{v}" for k, v in code_dict.items()])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        ("user", f"Kod do sprawdzenia:\n{full_code}")
    ])
    
    print("🕵️‍♂️ QA: Składnia OK. Analizuję logikę modelem AI...")
    response = (prompt | llm).invoke({})
    
    status = "APPROVED" if "APPROVED" in response.content else "REJECTED"
    print(f"🕵️‍♂️ QA Decyzja: {status}")
    
    return {
        "qa_status": status,
        "qa_feedback": response.content,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "logs": [f"QA: {status}"]
    }