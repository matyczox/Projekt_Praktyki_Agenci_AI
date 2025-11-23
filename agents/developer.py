from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from pathlib import Path
import json
import re
import os

llm = get_chat_model(os.getenv("MODEL_REASONING", "qwen3-coder:30b"), temperature=0.2)

DEVELOPER_SYSTEM_PROMPT = """
Jesteś Senior Full-Stack Developerem (Polyglot).
Generujesz KOMPLETNY, DZIAŁAJĄCY kod dla każdego pliku z listy Architekta.

ZASADY UNIWERSALNE:
1. Generuj KOD dla KAŻDEGO pliku z listy (zero pomijania).
2. Każdy plik MUSI być kompletny i gotowy do uruchomienia.
3. Format odpowiedzi - dla każdego pliku osobny blok:

--- filename.ext ---
```language
[kod tutaj]
```

4. NIE POMIŃ żadnego pliku. Jeśli lista ma 5 plików → wygeneruj 5 bloków.

ZASADY DLA PYTHONA:
- Importy na górze
- Jeśli to main.py → dodaj if __name__ == "__main__":
- Używaj typehints gdzie możliwe
- Dodaj docstringi do funkcji

ZASADY DLA JAVASCRIPT/NODE:
- Używaj const/let (NIE var)
- Dodaj "use strict" na początku
- Jeśli to moduł → eksportuj funkcje (module.exports lub export)
- Obsłuż błędy (try/catch gdzie potrzeba)

ZASADY DLA HTML:
- Pełna struktura: <!DOCTYPE html>, <head>, <body>
- Jeśli są style → wstaw <link> do pliku CSS
- Jeśli jest JS → wstaw <script src="...">

ZASADY DLA CSS:
- Resetuj podstawowe style (box-sizing, margin)
- Używaj semantycznych nazw klas
- Dodaj komentarze dla sekcji

KRYTYCZNE:
- Jeśli QA odrzuciło kod → przeczytaj feedback i napraw DOKŁADNIE to co napisali
- NIE generuj placeholder'ów typu "TODO" ani "# implementacja tutaj"
- Każdy plik musi być production-ready
"""

def save_file_direct(filename: str, code_content: str):
    """
    Bezpośredni zapis pliku (bez LangChain tool).
    """
    PROJECT_ROOT = Path("output_projects")
    try:
        full_path = (PROJECT_ROOT / filename).resolve()
        root_path = PROJECT_ROOT.resolve()
        
        if not str(full_path).startswith(str(root_path)):
            print(f"❌ SECURITY ERROR: {filename}")
            return False
        
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code_content)
        
        return True
    except Exception as e:
        print(f"❌ Błąd zapisu {filename}: {e}")
        return False

def parse_code_blocks(text: str) -> dict:
    """
    Ekstrahuje pliki z odpowiedzi LLM w formacie:
    --- filename ---
    ```language
    kod
    ```
    """
    code_dict = {}
    
    # Regex: wyciąga nazwę pliku i kod z bloku
    pattern = r'---\s*([^\n]+?)\s*---\s*```(?:\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for filename, code in matches:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
            
    return code_dict

def extract_file_list(tech_stack_response: str) -> list:
    """
    Wyciąga listę plików z JSON-a na końcu odpowiedzi Architekta.
    """
    try:
        # Szukamy bloku JSON na końcu tekstu
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', tech_stack_response, re.DOTALL)
        if json_match:
            file_list = json.loads(json_match.group(1))
            return file_list
    except Exception as e:
        print(f"⚠️ Nie udało się sparsować listy plików: {e}")
    
    return []

def developer_node(state: ProjectState) -> ProjectState:
    print("\n💻 Developer: Rozpoczynam kodowanie...")
    
    # 1. Pobieramy listę plików od Architekta
    file_list = extract_file_list(state.get("tech_stack", ""))
    
    if not file_list:
        print("⚠️ Architekt nie dostarczył listy plików! Próbuję działać bez niej...")
        file_list_str = "Architekt nie dostarczył jasnej listy - wygeneruj pliki samodzielnie na podstawie specyfikacji."
    else:
        print(f"📋 Developer otrzymał listę: {file_list}")
        file_list_str = "\n".join([f"- {f}" for f in file_list])
    
    # 2. Jeśli to poprawka po QA → dodajemy feedback
    qa_feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)
    
    if iteration > 0 and qa_feedback:
        context = f"""
=== POPRAWKA (Iteracja {iteration}) ===
QA odrzuciło kod z powodu:
{qa_feedback}

NAPRAW DOKŁADNIE TO CO WSKAZALI POWYŻEJ.
"""
    else:
        context = "=== PIERWSZA IMPLEMENTACJA ==="
    
    # 3. Budujemy prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", DEVELOPER_SYSTEM_PROMPT),
        ("user", f"""
{context}

SPECYFIKACJA:
{state.get('requirements', '')}

STRUKTURA PROJEKTU:
{state.get('tech_stack', '')}

LISTA PLIKÓW DO WYGENEROWANIA:
{file_list_str}

Wygeneruj KOMPLETNY kod dla każdego pliku.
Użyj formatu:
--- filename ---
```language
kod
```
""")
    ])
    
    print("💻 Developer: Wysyłam zapytanie do LLM...")
    response = (prompt | llm).invoke({})
    
    # 4. Parsujemy odpowiedź
    generated_code = parse_code_blocks(response.content)
    
    print(f"💻 Developer: Wygenerowano {len(generated_code)} plików")
    
    # 5. Sprawdzamy czy wszystkie pliki z listy zostały wygenerowane
    if file_list:
        missing = [f for f in file_list if f not in generated_code]
        if missing:
            print(f"⚠️ BRAKUJĄCE PLIKI: {missing}")
    
    # 6. Zapisujemy pliki na dysk
    for filename, code in generated_code.items():
        if save_file_direct(filename, code):
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename} - nie zapisano")
    
    return {
        "generated_code": generated_code,
        "logs": [f"Developer wygenerował {len(generated_code)} plików."]
    }