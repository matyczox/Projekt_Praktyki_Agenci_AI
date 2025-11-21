from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os
import json
import re

llm = get_chat_model(os.getenv("MODEL_CODER", "qwen3-coder:30b"), temperature=0.2)

# --- ZMIENNE POMOCNICZE (Żeby czat nie ucinał kodu) ---
MD_OPEN = "```" + "python"
MD_CLOSE = "```"

# --- PROMPTY ---
# Używamy standardowych klamr { }, LangChain podstawi tu wartości bezpiecznie.

FILE_LIST_PROMPT = """
Jesteś Tech Leadem. Zwróć JSON z listą plików do utworzenia na podstawie planu.
Przykład: ["main.py", "utils.py"]

Plan Architekta:
{plan}
"""

CODE_GEN_PROMPT = """
Jesteś Developerem. Napisz kod pliku: {filename}.

WYMAGANIA:
1. Kod MUSI być w bloku markdown:
""" + MD_OPEN + """
...kod...
""" + MD_CLOSE + """
2. Nie pisz wstępów.
3. Kod musi być kompletny.

Plan Architekta:
{plan}

Feedback QA:
{feedback}
"""

def extract_json_list(text):
    try:
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match: return json.loads(match.group(1))
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match: return json.loads(match.group())
        return json.loads(text)
    except:
        return ["main.py"]

def clean_code_content(text):
    # Regex łapiący treść między ```
    match = re.search(r"```(?:\w+)?\s*(.*?)```", text, re.DOTALL)
    if match and match.group(1).strip():
        return match.group(1).strip()
    
    # Fallback ręczny
    clean = text.replace("```python", "").replace("```", "").strip()
    if clean: return clean
    
    return f"# DEBUG: BRAK KODU W ODPOWIEDZI.\n# RAW:\n{text}"

def developer_node(state: ProjectState) -> ProjectState:
    tech_stack = state.get("tech_stack", "")
    qa_feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)

    print(f"\n👨‍💻 Developer: Iteracja {iteration}. Pobieram listę plików...")
    
    # --- FIX 1: Bezpieczne przekazywanie planu ---
    # Nie używamy .format(), tylko przekazujemy słownik do invoke
    prompt_files = ChatPromptTemplate.from_messages([
        ("system", FILE_LIST_PROMPT)
    ])
    chain_files = prompt_files | llm
    response_files = chain_files.invoke({"plan": tech_stack})
    
    files = extract_json_list(response_files.content)
    
    if not files: files = ["main.py"]
    print(f"📋 Developer Zadania: {files}")
    
    generated = {}
    logs = []
    
    # --- FIX 2: Bezpieczne przekazywanie zmiennych do generatora ---
    for filename in files:
        print(f"   🔨 Piszę kod: {filename}...")
        
        prompt_code = ChatPromptTemplate.from_messages([
            ("system", CODE_GEN_PROMPT)
        ])
        
        chain_code = prompt_code | llm
        
        # LangChain sam bezpiecznie podstawi te wartości, 
        # ignorując klamry wewnątrz treści zmiennych (tech_stack)
        response_code = chain_code.invoke({
            "filename": filename,
            "plan": tech_stack,
            "feedback": qa_feedback
        })
        
        raw_resp = response_code.content
        
        # --- DEBUG LOG ---
        print(f"      🔴 [DEBUG RAW]: {raw_resp[:50].replace(chr(10), ' ')}...")
        
        final_code = clean_code_content(raw_resp)
        save_msg = save_file.invoke({"filename": filename, "code_content": final_code})
        
        print(f"      💾 {save_msg}")
        generated[filename] = final_code
        logs.append(f"{filename}: {save_msg}")

    return {"generated_code": generated, "logs": logs}