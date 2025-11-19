from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os
import json
import re

# Używamy modelu KODUJĄCEGO zdefiniowanego w .env
llm = get_chat_model(os.getenv("MODEL_CODER", "qwen3-coder:30b"), temperature=0.2)

# --- KROK 1: PROMPT DO LISTY PLIKÓW ---
FILE_LIST_PROMPT = """
Jesteś Tech Leadem. Przeanalizuj plan architekta i wylistuj WSZYSTKIE pliki, które trzeba stworzyć.
Zwróć TYLKO surową listę plików w formacie JSON (lista stringów).
Nie dodawaj żadnych komentarzy ani wstępów. Tylko czysty JSON.

Przykład poprawnej odpowiedzi:
["main.py", "requirements.txt", "src/utils.py"]

Plan Architekta:
{plan}
"""

# --- KROK 2: PROMPT DO GENEROWANIA KODU ---

# Definiujemy przykład osobno, żeby nie psuł kopiowania w czacie
EXAMPLE_BLOCK = "```python\nprint('Hello World')\n```"

CODE_GEN_PROMPT = """
Jesteś Senior Python Developerem.
Twoim zadaniem jest napisać zawartość pliku: "{filename}".

PLAN ARCHITEKTA:
{plan}

UWAGI OD QA (Jeśli są, musisz je uwzględnić i poprawić kod):
{feedback}

WYMAGANIA:
1. Zwróć TYLKO kod tego jednego pliku.
2. Kod musi być otoczony znacznikami markdown, np:
""" + EXAMPLE_BLOCK + """
3. Kod musi być kompletny (zawierać wszystkie importy).
4. Nie ucinaj kodu w połowie.

Napisz teraz kompletny kod dla pliku: {filename}
"""

def extract_json_list(text):
    """
    Bezpieczne wyciąganie listy plików z odpowiedzi modelu.
    Radzi sobie z blokami json i czystym tekstem.
    """
    try:
        # 1. Najpierw szukamy bloku kodu json w markdown
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        
        # 2. Jeśli nie ma markdowna, szukamy po prostu nawiasów kwadratowych
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
            
        # 3. Próba bezpośredniego parsowania
        return json.loads(text)
    except Exception:
        return []

def clean_code_content(text):
    """
    Krytyczna funkcja: Wyciąga czysty kod spomiędzy znaczników markdown.
    Ignoruje gadaninę modelu przed i po kodzie.
    """
    # Regex szukający treści między ``` (opcjonalnie python/bash itp) a ```
    pattern = r"```(?:\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        # Fallback: Jeśli model zapomniał markdowna, ale dał kod,
        # próbujemy oczyścić go z popularnych zwrotów.
        clean_text = text.replace("```python", "").replace("```", "").strip()
        return clean_text

def developer_node(state: ProjectState) -> ProjectState:
    tech_stack = state.get("tech_stack", "")
    
    # Pobieramy feedback od QA (jeśli to kolejna iteracja)
    qa_feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)

    print(f"\n👨‍💻 Developer: Rozpoczynam pracę (Iteracja {iteration})...")
    
    if qa_feedback:
        print(f"   ⚠️ Otrzymałem uwagi od QA. Wdrażam poprawki...")

    # 1. Generowanie listy plików
    prompt_files = ChatPromptTemplate.from_messages([
        ("system", FILE_LIST_PROMPT.format(plan=tech_stack))
    ])
    chain_files = prompt_files | llm
    response_files = chain_files.invoke({})
    
    files_to_create = extract_json_list(response_files.content)
    
    # Zabezpieczenie przed pustą listą
    if not files_to_create:
        print("⚠️ Developer nie znalazł listy plików. Tworzę domyślny main.py.")
        files_to_create = ["main.py"]

    print(f"📋 Lista zadań: {files_to_create}")
    
    generated_files = {}
    logs = []
    
    # 2. Pętla generowania kodu dla każdego pliku
    for filename in files_to_create:
        print(f"   🔨 Piszę kod: {filename}...")
        
        # Wstrzykujemy feedback do promptu
        prompt_code = ChatPromptTemplate.from_messages([
            ("system", CODE_GEN_PROMPT.format(
                filename=filename, 
                plan=tech_stack,
                feedback=qa_feedback if qa_feedback else "Brak uwag, to pierwsza wersja."
            ))
        ])
        
        chain_code = prompt_code | llm
        response_code = chain_code.invoke({})
        
        # Wyciągamy czysty kod regexem
        code_content = clean_code_content(response_code.content)
        
        # Zapisujemy na dysk używając narzędzia
        save_msg = save_file.invoke({"filename": filename, "code_content": code_content})
        
        # Logowanie
        if "Zapisano" in save_msg:
            print(f"      💾 Zapisano.")
        else:
            print(f"      ❌ Błąd zapisu: {save_msg}")
            
        generated_files[filename] = code_content
        logs.append(f"Utworzono/Zaktualizowano: {filename}")

    return {
        "generated_code": generated_files,
        "logs": logs
    }