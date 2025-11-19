from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os
import json
import re

# Używamy modelu KODUJĄCEGO
llm = get_chat_model(os.getenv("MODEL_CODER", "qwen3-coder:30b"), temperature=0.2)

# --- PROMPT LISTA PLIKÓW ---
FILE_LIST_PROMPT = """
Jesteś Tech Leadem. Przeanalizuj plan architekta i wylistuj WSZYSTKIE pliki, które trzeba stworzyć.
Zwróć TYLKO surową listę plików w formacie JSON (lista stringów).

Przykład:
["main.py", "requirements.txt", "src/utils.py"]

Plan Architekta:
{plan}
"""

# --- PROMPT KOD ---
# Triki, żeby czat nie ucinał kodu przy kopiowaniu:
MD_OPEN = "```python"
MD_CLOSE = "```"

CODE_GEN_PROMPT = f"""
Jesteś Senior Python Developerem.
Napisz kod pliku: "{{filename}}".

PLAN:
{{plan}}

UWAGI QA:
{{feedback}}

WYMAGANIA KRYTYCZNE:
1. Kod MUSI być w bloku markdown:
{MD_OPEN}
...treść kodu...
{MD_CLOSE}
2. Kod musi być kompletny.

Napisz teraz kod dla: {{filename}}
"""

def extract_json_list(text):
    try:
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match: return json.loads(match.group(1))
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match: return json.loads(match.group())
        return json.loads(text)
    except:
        return []

def clean_code_content(text):
    """
    Pancerne czyszczenie.
    Jeśli regex nic nie znajdzie, zwraca CAŁY tekst (z dopiskiem), 
    żeby plik nie był pusty i żebyś widział w nim, co poszło nie tak.
    """
    # 1. Próba Regex (szuka treści między ``` a ```)
    # (?:\w+)? - opcjonalnie słowo np. python
    # \s* - dowolna ilość białych znaków (spacja lub enter)
    pattern = r"```(?:\w+)?\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        content = match.group(1).strip()
        if content:
            return content

    # 2. Fallback - jeśli regex nie zadziałał, próbujemy ręcznie wyczyścić
    cleaned = text.replace("```python", "").replace("```", "").strip()
    
    if cleaned:
        return cleaned
        
    # 3. OSTATECZNY FALLBACK - Jeśli po czyszczeniu jest pusto, zwróć oryginał
    return "# DEBUG: REGEX NIE ZNALAZŁ KODU. OTO SUROWA ODPOWIEDŹ:\n\n" + text

def developer_node(state: ProjectState) -> ProjectState:
    tech_stack = state.get("tech_stack", "")
    qa_feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)

    print(f"\n👨‍💻 Developer: Iteracja {iteration}...")
    
    # 1. Lista plików
    prompt_files = ChatPromptTemplate.from_messages([
        ("system", FILE_LIST_PROMPT.format(plan=tech_stack))
    ])
    chain_files = prompt_files | llm
    response_files = chain_files.invoke({})
    files_to_create = extract_json_list(response_files.content)
    
    if not files_to_create:
        files_to_create = ["main.py"]

    print(f"📋 Zadania: {files_to_create}")
    
    generated_files = {}
    logs = []
    
    # 2. Generowanie
    for filename in files_to_create:
        print(f"   🔨 Piszę: {filename}...")
        
        # Używamy f-stringa ostrożnie, bo prompt ma już klamry
        prompt_code = ChatPromptTemplate.from_messages([
            ("system", CODE_GEN_PROMPT.format(
                filename=filename, 
                plan=tech_stack,
                feedback=qa_feedback
            ))
        ])
        
        chain_code = prompt_code | llm
        response_code = chain_code.invoke({})
        raw_content = response_code.content
        
        # --- SEKCJA DEBUGOWANIA ---
        # Pokaż w terminalu co naprawdę dał model (pierwsze 100 znaków)
        clean_preview = raw_content[:100].replace('\n', ' ')
        print(f"      🔴 [DEBUG RAW]: {clean_preview}...") 
        
        code_content = clean_code_content(raw_content)
        
        # Zapis
        save_msg = save_file.invoke({"filename": filename, "code_content": code_content})
        
        status_icon = "✅" if "Zapisano" in save_msg else "❌"
        print(f"      {status_icon} {filename} (Rozmiar: {len(code_content)} znaków)")
        
        generated_files[filename] = code_content
        logs.append(f"{status_icon} {filename}")

    return {
        "generated_code": generated_files,
        "logs": logs
    }