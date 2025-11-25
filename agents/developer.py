import re
import os
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ProjectState
from tools.file_system import write_file, read_file, get_all_file_paths
from core.llm_factory import get_llm

def parse_and_save_files(ai_response: str):
    if not ai_response:
        return []
    pattern = r"###\s*FILE:\s*([^\n]+)\n(.*?)\n###\s*ENDFILE"
    matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
    created_files = []

    if not matches and len(ai_response.strip()) > 50:
        write_file("raw_response.txt", ai_response)
        return ["raw_response.txt"]

    for filename, content in matches:
        filename = filename.strip()
        content = re.sub(r"^```[a-zA-Z]*\n", "", content, flags=re.MULTILINE)
        content = re.sub(r"\n```$", "", content, flags=re.MULTILINE).strip()
        write_file(filename, content)
        print(f"-> Zapisano: {filename}")
        created_files.append(filename)
    return created_files

def developer_node(state: ProjectState):
    plan = state.get("tech_stack", "")
    feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)
    existing_files = get_all_file_paths()

    model_name = os.getenv("MODEL_CODER", "qwen3-coder:30b")
    llm = get_llm(model_name, temperature=0.0, num_ctx=24000)

    # Kontekst istniejącego kodu
    code_context = ""
    if existing_files:
        print(f"--- Developer: Wczytuję {len(existing_files)} istniejących plików ---")
        for f in existing_files:
            if f.endswith(('.py', '.txt', '.md', '.json', '.html', '.css', '.js')):
                content = read_file(f)
                if content:
                    code_context += f"\n=== {f} ===\n{content}\n" + "="*70 + "\n"
    else:
        code_context = "Brak istniejących plików – nowy projekt."

    # Tryb pracy
    if feedback and "REJECTED" in feedback.upper():
        mode = "NAPRAWA BŁĘDÓW"
        task = f"QA odrzucił kod z powodu:\n{feedback}\nNapraw WSZYSTKIE błędy. Zwracaj PEŁNE pliki."
    else:
        mode = "PIERWSZA WERSJA / ROZWÓJ"
        task = "Wygeneruj kompletną, działającą wersję projektu zgodnie z planem architekta."

    print(f"--- Developer: {mode} (iteracja {iteration + 1}) ---")

    sys_msg = SystemMessage(content="""
Jesteś ekspertem programistą. Zwracaj TYLKO poprawne, działające pliki w formacie:

### FILE: ścieżka/do/pliku.py
pełny kod tutaj
### ENDFILE

ZASADY:
- ZAWSZE podawaj CAŁY plik (bez ... ani pomijania kodu)
- Nie używaj skrótów typu # ... existing code
- Zachowaj istniejące funkcjonalności
- Naprawiaj tylko to, co jest zepsute
""")

    user_msg = HumanMessage(content=f"""
TRYB: {mode}
PLAN ARCHITEKTA:
{plan}

ZADANIE:
{task}

ISTNIEJĄCY KOD:
{code_context}

Wygeneruj lub popraw pliki. Odpowiadaj TYLKO blokami ### FILE: ... ### ENDFILE
""")

    print("--- Wysyłanie do modelu... ---")
    response = llm.invoke([sys_msg, user_msg])
    full_response = response.content
    print(f"-> Otrzymano {len(full_response)} znaków")

    saved = parse_and_save_files(full_response)
    if not saved:
        write_file("developer_error.txt", full_response[:2000])

    generated = {}
    for f in saved:
        content = read_file(f)
        generated[f] = content if content else "# BŁĄD WCZYTANIA"

    return {
        "generated_code": generated,
        "iteration_count": iteration + 1,
        "logs": [f"Developer: zapisano {len(saved)} plików"]
    }