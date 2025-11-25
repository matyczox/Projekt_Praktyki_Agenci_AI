from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

# QA używa modelu rezonowania (lub codera, jeśli wolisz)
llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

QA_SYSTEM_PROMPT = """
Jesteś QA Engineerem. Twoim zadaniem jest audyt kodu.
Oceń dostarczony kod pod kątem błędów logicznych, składniowych i bezpieczeństwa.

ZASADY:
1. Jeśli kod wygląda na działający i kompletny -> Odpisz TYLKO słowem: 'APPROVED'.
2. Jeśli są błędy -> Odpisz: 'REJECTED: <krótki opis co poprawić>'.
"""

def qa_node(state: ProjectState) -> ProjectState:
    print("\n🕵️‍♂️ QA: Rozpoczynam sprawdzanie...")
    code_dict = state.get("generated_code", {})
    
    if not code_dict:
        return {
            "qa_status": "REJECTED", 
            "qa_feedback": "Brak kodu do sprawdzenia!", 
            "logs": ["QA: Pusto"]
        }

    # 1. Auto-Check Składni (Python)
    for filename, content in code_dict.items():
        if filename.endswith(".py"):
            try:
                compile(content, filename, 'exec')
            except SyntaxError as e:
                error_msg = f"BŁĄD SKŁADNI w {filename}: {e}"
                print(f"❌ QA (Auto): {error_msg}")
                return {
                    "qa_status": "REJECTED",
                    "qa_feedback": f"Kod się nie kompiluje. {error_msg}",
                    "iteration_count": state.get("iteration_count", 0) + 1,
                    "logs": [f"QA Auto-Reject: {filename}"]
                }

    # 2. Analiza AI
    # Łączymy kod w jeden ciąg
    full_code = "\n".join([f"--- {k} ---\n{v}" for k, v in code_dict.items()])
    
    # --- POPRAWKA TUTAJ ---
    # Definiujemy szablon z placeholderem {code}
    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        ("user", "Sprawdź poniższy kod:\n\n{code}") 
    ])
    
    print("🕵️‍♂️ QA: Składnia OK. Analizuję logikę modelem AI...")
    
    # Przekazujemy kod jako zmienną w .invoke()
    # To chroni przed błędami z klamrami {} wewnątrz kodu gry
    response = (prompt | llm).invoke({"code": full_code})
    
    # Decyzja
    decision_text = response.content.strip()
    status = "APPROVED" if "APPROVED" in decision_text else "REJECTED"
    
    print(f"🕵️‍♂️ QA Decyzja: {status}")
    
    return {
        "qa_status": status,
        "qa_feedback": decision_text,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "logs": [f"QA: {status}"]
    }