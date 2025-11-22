from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

# Używamy modelu REASONING (Llama 70B z Vast.ai) - najlepszy audytor
llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

QA_SYSTEM_PROMPT = """
Jesteś QA Engineerem (Polyglot).
Twoim zadaniem jest ocena kodu i znalezienie błędów.

ZASADY:
1. Sprawdź czy kod jest kompletny.
2. Sprawdź importy i logikę.
3. Jeśli kod wygląda poprawnie -> Odpisz 'APPROVED'.
4. Jeśli są błędy -> Odpisz 'REJECTED: <krótki opis co poprawić>'.
"""

def qa_node(state: ProjectState) -> ProjectState:
    print("\n🕵️‍♂️ QA: Rozpoczynam audyt kodu (Llama 70B)...")
    code_dict = state.get("generated_code", {})
    
    if not code_dict:
        return {"qa_status": "REJECTED", "qa_feedback": "Brak kodu!", "logs": ["QA: Pusto"]}

    # 1. AUTO-CHECK (Tylko dla Pythona - wyłapuje błędy składni od razu)
    for filename, content in code_dict.items():
        if filename.endswith(".py"):
            try:
                compile(content, filename, 'exec')
            except SyntaxError as e:
                error_msg = f"BŁĄD SKŁADNI (Python) w {filename}: {e}"
                print(f"🕵️‍♂️ QA (Auto-Check): ❌ {error_msg}")
                return {
                    "qa_status": "REJECTED",
                    "qa_feedback": f"Popraw błąd składni w {filename}: {error_msg}",
                    "iteration_count": state.get("iteration_count", 0) + 1,
                    "logs": [f"QA Auto-Reject: {filename}"]
                }

    # 2. ANALIZA AI (Logika biznesowa)
    # Łączymy kod w jeden tekst
    full_code = "\n".join([f"--- {k} ---\n{v}" for k, v in code_dict.items()])
    
    # --- FIX NA BŁĄD 'Invalid variable name' ---
    # Definiujemy prompt z placeholderem {code_to_check}
    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        ("user", "Kod do sprawdzenia:\n{code_to_check}")
    ])
    
    print(f"🕵️‍♂️ QA: Analizuję logikę ({len(code_dict)} plików)...")
    
    # Przekazujemy kod jako wartość zmiennej. 
    # Dzięki temu LangChain NIE będzie próbował analizować klamer wewnątrz full_code.
    response = (prompt | llm).invoke({"code_to_check": full_code})
    
    status = "APPROVED" if "APPROVED" in response.content else "REJECTED"
    print(f"🕵️‍♂️ QA Decyzja: {status}")
    
    return {
        "qa_status": status,
        "qa_feedback": response.content,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "logs": [f"QA: {status}"]
    }