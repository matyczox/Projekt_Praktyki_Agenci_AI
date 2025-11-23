from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os
import re

llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

QA_SYSTEM_PROMPT = """
Jesteś Senior QA Engineerem (Polyglot).
Audytujesz kod pod kątem kompletności i poprawności.

ZASADY OCENY:
1. Czy wszystkie pliki są kompletne? (Nie ma TODO, placeholder'ów)
2. Czy importy/include są poprawne?
3. Czy logika ma sens?
4. Czy pliki są ze sobą spójne? (np. HTML linkuje do CSS/JS)

ODPOWIEDŹ:
- Jeśli OK → 'APPROVED'
- Jeśli błędy → 'REJECTED: [konkretny problem w konkretnym pliku]'

Przykład dobrego REJECTED:
"REJECTED: W pliku main.py brakuje importu 'random'. W game.html niepoprawna ścieżka do game.js (jest 'game.js' a powinno być 'static/game.js')."
"""

def quick_syntax_check(filename: str, content: str) -> str:
    """
    Szybkie sprawdzenie podstawowych błędów składni.
    Zwraca None jeśli OK, albo opis błędu.
    """
    # Python
    if filename.endswith(".py"):
        try:
            compile(content, filename, 'exec')
        except SyntaxError as e:
            return f"Błąd składni Python w {filename}: {e.msg} (linia {e.lineno})"
    
    # JavaScript/Node.js - podstawowe checky
    if filename.endswith(".js"):
        # Sprawdź czy nie ma var (powinno być const/let)
        if re.search(r'\bvar\s+\w+', content):
            return f"W {filename} użyto 'var' zamiast 'const'/'let' (bad practice)"
        
        # Sprawdź balans klamer
        if content.count('{') != content.count('}'):
            return f"W {filename} niezbalansowane nawiasy klamrowe"
    
    # HTML
    if filename.endswith(".html"):
        if not re.search(r'<!DOCTYPE html>', content, re.IGNORECASE):
            return f"W {filename} brakuje <!DOCTYPE html>"
        
        if not '<html' in content or not '</html>' in content:
            return f"W {filename} brakuje tagów <html>"
    
    # CSS
    if filename.endswith(".css"):
        if content.count('{') != content.count('}'):
            return f"W {filename} niezbalansowane nawiasy klamrowe"
    
    return None

def qa_node(state: ProjectState) -> ProjectState:
    print("\n🕵️‍♂️ QA: Rozpoczynam audyt...")
    code_dict = state.get("generated_code", {})
    
    if not code_dict:
        return {
            "qa_status": "REJECTED",
            "qa_feedback": "Developer nie wygenerował żadnego kodu!",
            "logs": ["QA: Brak kodu do sprawdzenia"]
        }
    
    # ETAP 1: Auto-check składni
    print(f"🕵️‍♂️ QA: Sprawdzam składnię ({len(code_dict)} plików)...")
    for filename, content in code_dict.items():
        syntax_error = quick_syntax_check(filename, content)
        if syntax_error:
            print(f"❌ {syntax_error}")
            return {
                "qa_status": "REJECTED",
                "qa_feedback": syntax_error,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "logs": [f"QA Auto-Reject: {filename}"]
            }
    
    print("✅ QA: Składnia OK, przechodzę do analizy AI...")
    
    # ETAP 2: AI review (logika, kompletność)
    full_code = "\n\n".join([f"=== {k} ===\n{v}" for k, v in code_dict.items()])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        ("user", "Sprawdź poniższy kod:\n\n{code_to_check}")
    ])
    
    response = (prompt | llm).invoke({"code_to_check": full_code})
    
    # Parsujemy decyzję
    decision = response.content.strip()
    status = "APPROVED" if "APPROVED" in decision else "REJECTED"
    
    if status == "APPROVED":
        print("✅ QA: APPROVED - Kod jest OK!")
    else:
        print(f"❌ QA: REJECTED")
        print(f"   Powód: {decision}")
    
    return {
        "qa_status": status,
        "qa_feedback": decision,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "logs": [f"QA: {status}"]
    }