from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os
import json
import re
import time
import chainlit as cl

# Qwen 32B Coder
llm = get_chat_model(os.getenv("MODEL_CODER", "qwen2.5-coder:32b"), temperature=0.2)

MD_QUOTE = "```"

IGNORED_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp3", ".wav", ".ogg", ".flac",
    ".ttf", ".otf", ".woff", ".woff2",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dll", ".so", ".bin"
)

FILE_LIST_PROMPT = """
Jesteś Tech Leadem.
Przeanalizuj plan Architekta i zwróć listę plików do utworzenia.
Zwróć TYLKO surową listę JSON, np.: ["main.py", "game.py"]

Plan Architekta:
{plan}
"""

CODE_GEN_PROMPT = """
Jesteś Senior Developerem (Expert Python).
Napisz PEŁNY, DZIAŁAJĄCY kod dla pliku: {filename}.

KONTEKST PROJEKTU (Inne pliki):
{existing_files}

{feedback_section}

WYTYCZNE:
1. Kod musi być gotowy do uruchomienia.
2. Użyj bloku markdown (np. ```python).
3. PAMIĘTAJ O IMPORTACH (zgodnych z listą plików).
4. Nie pisz komentarzy typu "Oto kod", tylko sam kod.

Plan Architekta:
{plan}
"""

def extract_json_list(text):
    """
    Super-bezpieczne parsowanie listy plików (wg zaleceń Claude).
    """
    print(f"🔍 Parsowanie listy plików...")
    try:
        # 1. Markdown JSON
        match = re.search(r"```json\s*(\[.*?\])\s*```", text, re.DOTALL | re.IGNORECASE)
        if match: return json.loads(match.group(1))

        # 2. Surowa lista [...]
        match = re.search(r'(\[.*?\])', text, re.DOTALL)
        if match: return json.loads(match.group(1))

        # 3. Cały tekst
        return json.loads(text)
    except:
        print(f"⚠️ Błąd JSON. Fallback na regex...")
        # Fallback: Regex wyciągający nazwy plików z tekstu
        files = re.findall(r'["\']([a-zA-Z0-9_\-./]+\.[a-z]{2,5})["\']', text)
        unique = list(set([f for f in files if not f.endswith('.json')]))
        return unique if unique else ["main.py"]

def clean_code_content(text):
    """Wyciąga kod z markdowna."""
    match = re.search(r"```(?:\w+)?\s*(.*?)```", text, re.DOTALL)
    if match and match.group(1).strip():
        return match.group(1).strip()
    return text.replace("```", "").strip()

async def developer_node(state: ProjectState) -> ProjectState:
    tech_stack = state.get("tech_stack", "")
    iteration = state.get("iteration_count", 0)
    qa_feedback = state.get("qa_feedback", "")
    
    # Pobieramy kod z poprzednich iteracji (State)
    generated_code = state.get("generated_code", {})

    print(f"\n👨‍💻 Developer: Iteracja {iteration}...")
    
    # 1. Lista plików
    chain_files = ChatPromptTemplate.from_messages([("system", FILE_LIST_PROMPT)]) | llm
    response_files = chain_files.invoke({"plan": tech_stack})
    files = extract_json_list(response_files.content)
    
    # Jeśli QA wskazał konkretne pliki w feedbacku, regenerujemy tylko je (PRO!)
    # Szukamy nazw plików w feedbacku QA (np. "Błąd w main.py")
    files_to_regen = []
    if iteration > 0 and qa_feedback:
        for f in files:
            if f in qa_feedback:
                files_to_regen.append(f)
        
        if not files_to_regen:
            print("⚠️ QA nie wskazał konkretnych plików, regeneruję wszystko dla pewności.")
            files_to_regen = files
        else:
            print(f"♻️ Regeneruję tylko poprawki: {files_to_regen}")
    else:
        files_to_regen = files

    print(f"📋 Zadania: {files_to_regen}")
    
    logs = []
    start_time = time.time()
    total_files = len(files_to_regen)
    
    # UI Message
    status_msg = cl.Message(content=f"🚀 **Developer pisze kod...**")
    await status_msg.send()

    # 2. Generowanie kodu
    for i, filename in enumerate(files_to_regen):
        if filename.lower().endswith(IGNORED_EXTENSIONS):
            continue

        # UI Update
        elapsed = time.time() - start_time
        eta = f"{(elapsed / (i+1)) * (total_files - i - 1):.1f}s" if i > 0 else "..."
        status_msg.content = f"### 👨‍💻 Piszę kod...\n**Plik:** `{filename}` ({i+1}/{total_files})\n**ETA:** {eta}"
        await status_msg.update()

        print(f"   🔨 Piszę kod: {filename} ...")
        
        # Budujemy kontekst (pokaż Developerowi kod innych plików)
        context_str = ""
        for fname, content in generated_code.items():
            if fname != filename:
                context_str += f"\n--- PLIK: {fname} ---\n{content[:1000]}...\n" # Skrót żeby nie zapchać pamięci

        feedback_msg = ""
        if iteration > 0 and qa_feedback:
            feedback_msg = f"⚠️ POPRAWKI QA:\n{qa_feedback}\nNAPRAW TE BŁĘDY."

        prompt_code = ChatPromptTemplate.from_messages([("system", CODE_GEN_PROMPT)])
        chain_code = prompt_code | llm
        
        response_code = chain_code.invoke({
            "filename": filename,
            "plan": tech_stack,
            "feedback_section": feedback_msg,
            "existing_files": context_str
        })
        
        final_code = clean_code_content(response_code.content)
        save_file.invoke({"filename": filename, "code_content": final_code})
        
        # Aktualizujemy stan (nadpisujemy stary kod nowym)
        generated_code[filename] = final_code
        logs.append(f"{filename}: OK")

    status_msg.content = f"✅ **Developer zakończył.** Zaktualizowano {len(files_to_regen)} plików."
    await status_msg.update()

    return {"generated_code": generated_code, "logs": logs}