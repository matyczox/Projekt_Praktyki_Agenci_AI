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
    UNIWERSALNE parsowanie - obsługuje WSZYSTKIE formaty:
    1. --- filename ---
    2. ### filename
    3. ## filename
    4. **filename**
    5. Filename:
    """
    code_dict = {}
    
    # STRATEGIA 1: Format --- filename ---
    pattern1 = r'---\s*([^\n]+?)\s*---\s*```(?:\w+)?\n(.*?)```'
    matches1 = re.findall(pattern1, text, re.DOTALL)
    
    for filename, code in matches1:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
    
    # Jeśli znaleziono coś - wracamy
    if code_dict:
        print(f"✅ Parsowanie: Format '--- filename ---' → {len(code_dict)} plików")
        return code_dict
    
    # STRATEGIA 2: Format ### filename lub ## filename
    # Qwen często używa markdownowych nagłówków
    pattern2 = r'#{2,3}\s+([^\n]+?)\s*\n+```(?:\w+)?\n(.*?)```'
    matches2 = re.findall(pattern2, text, re.DOTALL)
    
    for filename, code in matches2:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
    
    if code_dict:
        print(f"✅ Parsowanie: Format '### filename' → {len(code_dict)} plików")
        return code_dict
    
    # STRATEGIA 3: Format **filename** (bold)
    pattern3 = r'\*\*([^\*]+?)\*\*\s*\n+```(?:\w+)?\n(.*?)```'
    matches3 = re.findall(pattern3, text, re.DOTALL)
    
    for filename, code in matches3:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
    
    if code_dict:
        print(f"✅ Parsowanie: Format '**filename**' → {len(code_dict)} plików")
        return code_dict
    
    # STRATEGIA 4: Filename: (dwukropek)
    pattern4 = r'([a-zA-Z0-9_\-\.\/]+\.[a-z]+):\s*\n+```(?:\w+)?\n(.*?)```'
    matches4 = re.findall(pattern4, text, re.DOTALL | re.IGNORECASE)
    
    for filename, code in matches4:
        filename = filename.strip()
        code = code.strip()
        if filename and code:
            code_dict[filename] = code
    
    if code_dict:
        print(f"✅ Parsowanie: Format 'filename:' → {len(code_dict)} plików")
        return code_dict
    
    # STRATEGIA 5 (OSTATNIA DESKA RATUNKU): Wszystkie bloki kodu + próba zgadnięcia nazwy
    # Jeśli nic nie zadziałało - wyciągamy wszystkie bloki ```
    pattern5 = r'```(?:\w+)?\n(.*?)```'
    all_blocks = re.findall(pattern5, text, re.DOTALL)
    
    if all_blocks:
        print(f"⚠️ Fallback: Znaleziono {len(all_blocks)} bloków kodu bez nazw - próbuję zgadnąć...")
        
        # Próbujemy znaleźć nazwy plików w tekście przed blokami
        lines = text.split('\n')
        for i, block in enumerate(all_blocks):
            # Szukamy nazwy pliku w 5 liniach przed blokiem
            block_start = text.find('```' + block[:50])
            text_before = text[:block_start]
            lines_before = text_before.split('\n')[-5:]
            
            # Szukamy czegoś co wygląda jak nazwa pliku
            for line in reversed(lines_before):
                # Regex na nazwę pliku (np. main.py, index.html)
                file_match = re.search(r'([a-zA-Z0-9_\-]+\.[a-z]+)', line)
                if file_match:
                    filename = file_match.group(1)
                    code_dict[filename] = block.strip()
                    print(f"  ✅ Zgadłem: {filename}")
                    break
            else:
                # Jeśli nie znaleziono - używamy generycznej nazwy
                ext = ".py" if "def " in block or "import " in block else ".txt"
                filename = f"file_{i+1}{ext}"
                code_dict[filename] = block.strip()
                print(f"  ⚠️ Generyczna nazwa: {filename}")
        
        return code_dict
    
    # Jeśli NAPRAWDĘ nic nie znaleziono
    print("❌ BŁĄD PARSOWANIA: Nie znaleziono żadnego kodu!")
    print("📄 Pierwsze 500 znaków odpowiedzi:")
    print(text[:500])
    return {}

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
    
    # 4. Parsujemy odpowiedź (NOWA FUNKCJA!)
    generated_code = parse_code_blocks(response.content)
    
    if not generated_code:
        print("❌ KRYTYCZNY BŁĄD: Parser nie wyciągnął żadnego kodu!")
        print("📄 Zapisuję surową odpowiedź do debug.txt...")
        with open("debug_llm_response.txt", "w", encoding="utf-8") as f:
            f.write(response.content)
        print("✅ Sprawdź plik debug_llm_response.txt")
    
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