from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os
import json
import re

# Używamy modelu KODUJĄCEGO
llm = get_chat_model(os.getenv("MODEL_CODER", "qwen3-coder:30b"), temperature=0.2)

# --- KROK 1: EKSTRAKCJA LISTY PLIKÓW ---
FILE_LIST_PROMPT = """
Jesteś Tech Leadem. Przeanalizuj plan architekta i wylistuj WSZYSTKIE pliki, które trzeba stworzyć.
Zwróć TYLKO surową listę plików w formacie JSON (lista stringów).
Nie dodawaj żadnych komentarzy. Tylko JSON.

Przykład:
["main.py", "requirements.txt", "src/utils.py"]

Plan Architekta:
{plan}
"""

# --- KROK 2: GENEROWANIE KODU DLA POJEDYNCZEGO PLIKU ---
CODE_GEN_PROMPT = """
Jesteś Senior Python Developerem.
Twoim zadaniem jest napisać zawartość pliku: "{filename}".

Kontekst projektu (Plan Architekta):
{plan}

WYMAGANIA:
1. Zwróć TYLKO kod tego jednego pliku.
2. Nie używaj markdowna (```python). Czysty tekst.
3. Kod musi być kompletny (z importami).

Napisz teraz kod dla: {filename}
"""

def extract_json_list(text):
    """Pomocnicza funkcja do wyciągania JSONa z odpowiedzi modelu"""
    try:
        # Szukamy czegoś co wygląda jak lista ["..."]
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except:
        return []

def developer_node(state: ProjectState) -> ProjectState:
    tech_stack = state.get("tech_stack", "")
    
    # Sprawdzamy, czy to iteracja z poprawkami (QA)
    qa_feedback = state.get("qa_feedback", "")
    if qa_feedback:
        print(f"\n👨‍💻 Developer: Wdzięczam poprawki QA...")
        # Tutaj uproszczona logika dla poprawek - prosimy o poprawienie wszystkiego naraz
        # (W pełnej wersji można by też iterować, ale przy poprawkach kontekst jest kluczowy)
        # ... (zostawiamy starą logikę dla poprawek lub po prostu nadpisujemy kluczowe pliki)
        pass 

    print(f"\n👨‍💻 Developer: Analizuję listę plików do utworzenia...")
    
    # 1. Wyciągamy listę plików
    prompt_files = ChatPromptTemplate.from_messages([
        ("system", FILE_LIST_PROMPT.format(plan=tech_stack))
    ])
    chain_files = prompt_files | llm
    response_files = chain_files.invoke({})
    
    files_to_create = extract_json_list(response_files.content)
    
    if not files_to_create:
        print("⚠️ Developer nie znalazł plików w planie. Próbuję zgadnąć main.py...")
        files_to_create = ["main.py"]

    print(f"📋 Lista zadań: {files_to_create}")
    
    generated_files = {}
    logs = []
    
    # 2. PĘTLA GENEROWANIA (Plik po pliku)
    for filename in files_to_create:
        print(f"   🔨 Piszę kod: {filename}...")
        
        prompt_code = ChatPromptTemplate.from_messages([
            ("system", CODE_GEN_PROMPT.format(filename=filename, plan=tech_stack))
        ])
        chain_code = prompt_code | llm
        response_code = chain_code.invoke({})
        
        # Czyszczenie kodu z ewentualnych znaczników markdown
        code_content = response_code.content.replace("```python", "").replace("```", "").strip()
        
        # 3. Zapis na dysk (Używamy narzędzia bezpośrednio)
        save_msg = save_file.invoke({"filename": filename, "code_content": code_content})
        print(f"      💾 {save_msg}")
        
        generated_files[filename] = code_content
        logs.append(f"Utworzono: {filename}")

    return {
        "generated_code": generated_files,
        "logs": logs
    }