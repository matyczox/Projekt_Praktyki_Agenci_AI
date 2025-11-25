# agents/developer.py
import re
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ProjectState
from tools.file_system import write_file, read_file, get_all_file_paths
from core.llm_factory import get_coder_model  # ← tylko Qwen3-coder:30b
from core.rag import retrieve_context


def parse_and_save_files(ai_response: str):
    """Parsuje odpowiedź AI i zapisuje pliki w formacie ### FILE: ... ### ENDFILE"""
    if not ai_response:
        return []

    pattern = r"###\s*FILE:\s*([^\n]+)\n(.*?)\n###\s*ENDFILE"
    matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
    saved_files = []

    # Fallback – jeśli model nie użył formatu
    if not matches and len(ai_response.strip()) > 100:
        write_file("raw_developer_response.txt", ai_response)
        saved_files.append("raw_developer_response.txt")
        return saved_files

    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()

        # Usuń ewentualne bloki ```python / ```
        content = re.sub(r"^```[a-zA-Z]*\n", "", content, flags=re.MULTILINE)
        content = re.sub(r"\n```$", "", content, flags=re.MULTILINE)

        write_file(filename, content)
        print(f"Developer zapisano plik: {filename}")
        saved_files.append(filename)

    return saved_files


def developer_node(state: ProjectState):
    """
    Najlepszy Developer na świecie:
    - tylko qwen3-coder:30b
    - 200k kontekstu
    - RAG z wymagań i planu
    - perfekcyjne naprawy kodu
    """
    plan = state.get("tech_stack", "Brak planu.")
    feedback = state.get("qa_feedback", "")
    iteration = state.get("iteration_count", 0)
    vectorstore = state.get("vectorstore")

    # RAG – klucz do idealnych napraw
    rag_query = f"Jak zrealizować: {plan[:150]}... (z uwzględnieniem feedbacku QA)"
    rag_context = retrieve_context(rag_query, vectorstore)

    # Wczytaj cały istniejący kod
    code_context = ""
    existing_files = get_all_file_paths()
    if existing_files:
        print(f"Developer: Analizuję {len(existing_files)} istniejących plików + RAG")
        for file_path in existing_files:
            if file_path.endswith(('.py', '.cs', '.ts', '.js', '.html', '.css', '.json', '.md', '.csproj', '.angular-cli.json')):
                content = read_file(file_path)
                if content:
                    code_context += f"\n=== {file_path} ===\n{content}\n{'='*60}\n"
    else:
        code_context = "Brak istniejących plików – nowy projekt."

    # Tryb pracy
    if feedback and "REJECT" in feedback.upper():
        mode = "NAPRAWA BŁĘDÓW"
        task = f"""
QA odrzucił kod z powodu:
{feedback}

Twoim zadaniem jest naprawić WSZYSTKIE błędy.
Użyj kontekstu RAG poniżej – zawiera wymagania i plan projektu.
"""
    else:
        mode = "TWORZENIE / ROZWÓJ"
        task = "Wygeneruj kompletną, działającą wersję projektu zgodnie z planem architekta."

    print(f"Developer: {mode} (iteracja {iteration + 1})")

    # Qwen3-coder:30b – pełna moc
    llm = get_coder_model(temperature=0.0)  # ← 200k tokenów, zero ograniczeń

    # System prompt – perfekcjonista
    system_prompt = SystemMessage(content="""
Jesteś Senior Fullstack Developerem z 15-letnim doświadczeniem.
Twoja specjalność: perfekcyjne, działające od razu aplikacje w Pythonie, .NET, Angularze, React itd.

ZASADY ŻELAZNE:
- Zawsze zwracaj PEŁNĄ zawartość edytowanych plików
- NIGDY nie używaj // ... ani # ... – to psuje projekt
- Przy naprawie zmieniaj TYLKO to, co jest zepsute
- Zachowaj wszystkie istniejące nazwy klas, metod, zmiennych
- Używaj RAG kontekstu do przypomnienia wymagań użytkownika
- Format odpowiedzi: tylko bloki ### FILE: ... ### ENDFILE
""")

    user_prompt = HumanMessage(content=f"""
TRYB: {mode}

PLAN ARCHITEKTA:
{plan}

ZADANIE:
{task}

RAG KONTEKST (wymagania + plan):
{rag_context}

ISTNIEJĄCY KOD PROJEKTU:
{code_context}

Twoja kolej: przeanalizuj, a potem zwróć poprawione lub nowe pliki w formacie ### FILE: ...
""")

    print("Developer: Wysyłam zadanie do Qwen3-coder:30b (to może potrwać 20–60 sekund)...")
    try:
        response = llm.invoke([system_prompt, user_prompt])
        full_response = response.content
        print(f"Developer: Otrzymano odpowiedź ({len(full_response):,} znaków)")
    except Exception as e:
        full_response = f"Błąd modelu: {e}"
        print(full_response)

    # Zapisujemy pliki
    saved_files = parse_and_save_files(full_response)

    # Bezpiecznik – jeśli nic nie zwrócił
    if not saved_files and existing_files:
        saved_files = existing_files

    # Wczytujemy z powrotem do state
    generated_code = {}
    for file in saved_files:
        content = read_file(file)
        generated_code[file] = content if content else "# BŁĄD ODCZYTU PLIKU"

    return {
        "generated_code": generated_code,
        "iteration_count": iteration + 1,
        "logs": [f"Developer (Qwen3): zapisano {len(saved_files)} plików"],
        "vectorstore": vectorstore  # przekazujemy RAG dalej
    }