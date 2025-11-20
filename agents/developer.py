from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os
import json
import re

llm = get_chat_model(os.getenv("MODEL_CODER", "qwen3-coder:30b"), temperature=0.2)

FILE_LIST_PROMPT = """
Jesteś Tech Leadem. Zwróć JSON z listą plików do utworzenia na podstawie planu.
Przykład: ["main.py", "utils.py"]
Plan: {plan}
"""

MD_OPEN = "```python"
MD_CLOSE = "```"

CODE_GEN_PROMPT = f"""
Jesteś Developerem. Napisz kod pliku: {{filename}}.
Kod MUSI być w bloku markdown:
{MD_OPEN}
...kod...
{MD_CLOSE}
Plan: {{plan}}
Feedback QA: {{feedback}}
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
    
    chain_files = ChatPromptTemplate.from_messages([("system", FILE_LIST_PROMPT.format(plan=tech_stack))]) | llm
    files = extract_json_list(chain_files.invoke({}).content)
    
    if not files: files = ["main.py"]
    print(f"📋 Developer Zadania: {files}")
    
    generated = {}
    logs = []
    
    for filename in files:
        print(f"   🔨 Piszę kod: {filename}...")
        
        chain_code = ChatPromptTemplate.from_messages([
            ("system", CODE_GEN_PROMPT.format(filename=filename, plan=tech_stack, feedback=qa_feedback))
        ]) | llm
        
        raw_resp = chain_code.invoke({}).content
        
        # --- DEBUG LOG ---
        print(f"      🔴 [DEBUG RAW]: {raw_resp[:50].replace(chr(10), ' ')}...")
        
        final_code = clean_code_content(raw_resp)
        save_msg = save_file.invoke({"filename": filename, "code_content": final_code})
        
        print(f"      💾 {save_msg}")
        generated[filename] = final_code
        logs.append(f"{filename}: {save_msg}")

    return {"generated_code": generated, "logs": logs}