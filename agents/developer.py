from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os
import json
import re

# ============================================
# KRYTYCZNE: Wyłącz streaming dla stabilności
# ============================================
llm = get_chat_model(
    os.getenv("MODEL_CODER", "llama3.3:70b"), 
    temperature=0.2
)

# Wymuś non-streaming mode (może pomóc jeśli streaming ma problemy)
llm.streaming = False

# --- PROMPTY ---

FILE_LIST_PROMPT = """
Jesteś Tech Leadem. Zwróć JSON z listą plików do utworzenia.
Format: ["main.py", "utils.py", "requirements.txt", "README.md"]

Plan:
{plan}

Odpowiedź (tylko JSON, nic więcej):
"""

CODE_GEN_PROMPT = """
TASK: Write complete Python code for file: {filename}

REQUIREMENTS:
{plan}

PREVIOUS ISSUES (FIX THESE):
{feedback}

RULES:
- Write ONLY executable Python code
- NO markdown (no ```python```)
- NO explanations
- Start with imports
- Include error handling
- Make it production-ready

BEGIN CODE FOR {filename}:
"""

def extract_json_list(text):
    """Wyciąga listę plików z odpowiedzi modelu"""
    try:
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match: 
            return json.loads(match.group(1))
        
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match: 
            return json.loads(match.group())
        
        return json.loads(text)
    except Exception as e:
        print(f"⚠️  Błąd parsowania listy plików: {e}")
        return ["main.py", "README.md"]

def developer_node(state: ProjectState) -> ProjectState:
    tech_stack = state.get("tech_stack", "")
    qa_feedback = state.get("qa_feedback", "Pierwsza iteracja.")
    iteration = state.get("iteration_count", 0)

    print(f"\n👨‍💻 Developer [Iteracja {iteration}]: Rozpoczynam pracę...")
    
    # === KROK 1: Lista plików ===
    print("   📋 Pobieram listę plików...")
    prompt_files = ChatPromptTemplate.from_messages([
        ("system", FILE_LIST_PROMPT)
    ])
    
    response_files = (prompt_files | llm).invoke({"plan": tech_stack})
    files = extract_json_list(response_files.content)
    
    if not files:
        files = ["main.py", "README.md"]
    
    print(f"   ✅ Zadania: {', '.join(files)}")
    
    generated = {}
    logs = []
    
    # === KROK 2: Generuj kod ===
    for idx, filename in enumerate(files, 1):
        print(f"\n   [{idx}/{len(files)}] 🔨 Generuję: {filename}")
        
        prompt_code = ChatPromptTemplate.from_messages([
            ("system", CODE_GEN_PROMPT)
        ])
        
        print(f"      ⏳ Czekam na odpowiedź modelu...")
        
        response_code = (prompt_code | llm).invoke({
            "filename": filename,
            "plan": tech_stack,
            "feedback": qa_feedback
        })
        
        raw_content = response_code.content
        
        # ============================================
        # DIAGNOSTYKA
        # ============================================
        print(f"      📊 Statystyki odpowiedzi:")
        print(f"         • Długość: {len(raw_content)} znaków")
        print(f"         • Typ: {type(raw_content)}")
        print(f"         • Puste: {not raw_content or not raw_content.strip()}")
        
        if raw_content and len(raw_content.strip()) > 0:
            # Pokaż podgląd
            lines = raw_content.split('\n')
            print(f"         • Liczba linii: {len(lines)}")
            print(f"         • Pierwsza linia: {lines[0][:50]}")
            
            # Zapisz kod
            save_msg = save_file.invoke({
                "filename": filename, 
                "code_content": raw_content
            })
            print(f"      {save_msg}")
            
            generated[filename] = raw_content
            logs.append(f"{filename}: OK ({len(raw_content)} znaków)")
        else:
            # Model zwrócił puste
            error_msg = f"# BŁĄD: Brak odpowiedzi od modelu\n# Plik: {filename}\n# Sprawdź Ollama\npass\n"
            
            save_file.invoke({
                "filename": filename, 
                "code_content": error_msg
            })
            
            print(f"      ❌ Model nie wygenerował kodu!")
            generated[filename] = error_msg
            logs.append(f"{filename}: FAILED (pusty)")

    print(f"\n✅ Developer zakończył. Plików: {len(generated)}")
    
    return {
        "generated_code": generated, 
        "logs": logs
    }