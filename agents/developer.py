from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os
import json
import re

llm = get_chat_model(os.getenv("MODEL_CODER", "qwen3-coder:30b"), temperature=0.2)

# --- PROMPTY ---

FILE_LIST_PROMPT = """
Jesteś Tech Leadem. Zwróć JSON z listą plików do utworzenia na podstawie planu.
Przykład: ["main.py", "utils.py", "requirements.txt", "README.md"]

WAŻNE: ZAWSZE uwzględnij requirements.txt i README.md jeśli projekt używa bibliotek.

Plan Architekta:
{plan}
"""

CODE_GEN_PROMPT = """
You are a Python code generator.

Write complete, working code for file: {filename}

Requirements: {plan}

QA feedback: {feedback}

Write the code now (no explanations, no markdown blocks, just pure code):
"""

def extract_json_list(text):
    """Wyciąga listę plików z odpowiedzi modelu"""
    try:
        # Próba 1: JSON w bloku markdown
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match: 
            return json.loads(match.group(1))
        
        # Próba 2: Surowy JSON
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match: 
            return json.loads(match.group())
        
        # Próba 3: Bezpośredni parse
        return json.loads(text)
    except Exception as e:
        print(f"⚠️  Błąd parsowania listy plików: {e}")
        print(f"Raw response: {text[:200]}")
        return ["main.py"]

def developer_node(state: ProjectState) -> ProjectState:
    tech_stack = state.get("tech_stack", "")
    qa_feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)

    print(f"\n👨‍💻 Developer: Iteracja {iteration}. Pobieram listę plików...")
    
    # === KROK 1: Pobierz listę plików ===
    prompt_files = ChatPromptTemplate.from_messages([
        ("system", FILE_LIST_PROMPT)
    ])
    chain_files = prompt_files | llm
    response_files = chain_files.invoke({"plan": tech_stack})
    
    files = extract_json_list(response_files.content)
    
    if not files or len(files) == 0:
        files = ["main.py"]
    
    print(f"📋 Developer Zadania: {files}")
    
    generated = {}
    logs = []
    
    # === KROK 2: Generuj kod dla każdego pliku ===
    for filename in files:
        print(f"\n   🔨 Piszę kod: {filename}...")
        
        prompt_code = ChatPromptTemplate.from_messages([
            ("system", CODE_GEN_PROMPT)
        ])
        
        chain_code = prompt_code | llm
        response_code = chain_code.invoke({
            "filename": filename,
            "plan": tech_stack,
            "feedback": qa_feedback
        })
        
        # ============================================
        # RAW DUMP MODE - ZERO PARSOWANIA
        # ============================================
        raw_content = response_code.content
        
        print(f"      📏 Model zwrócił: {len(raw_content)} znaków")
        print(f"      👀 Pierwsze 200 znaków:")
        print(f"         {raw_content[:200].replace(chr(10), '↵')}")
        
        # Sprawdź czy model w ogóle coś zwrócił
        if not raw_content or len(raw_content.strip()) == 0:
            print(f"      ❌ BŁĄD: Model zwrócił pusty string dla {filename}!")
            raw_content = f"# BŁĄD: Model nie wygenerował kodu dla {filename}\n# Sprawdź logi Ollama"
        
        # Zapisujemy DOKŁADNIE to co model zwrócił
        save_msg = save_file.invoke({
            "filename": filename, 
            "code_content": raw_content
        })
        
        print(f"      💾 {save_msg}")
        
        generated[filename] = raw_content
        logs.append(f"{filename}: {len(raw_content)} znaków")

    print(f"\n✅ Developer zakończył pracę. Wygenerowano {len(generated)} plików.")
    
    return {
        "generated_code": generated, 
        "logs": logs
    }