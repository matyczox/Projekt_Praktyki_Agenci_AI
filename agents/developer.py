import re
import os
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import ProjectState
from tools.file_system import write_file, read_file, get_all_file_paths
from core.llm_factory import get_llm
from core.rag import retrieve_context  # RAG integracja

def parse_and_save_files(ai_response: str):
    """Parsuje odpowiedź AI i zapisuje pliki."""
    if not ai_response: 
        return []

    # Regex szuka bloków: ### FILE: nazwa ... ### ENDFILE
    pattern = r"###\s*FILE:\s*([^\n]+)\n(.*?)\n###\s*ENDFILE"
    matches = re.findall(pattern, ai_response, re.DOTALL | re.IGNORECASE)
    created_files = []
    
    # Fallback
    if not matches and len(ai_response.strip()) > 50:
        write_file("raw_code.txt", ai_response)
        return ["raw_code.txt"]

    for filename, content in matches:
        filename = filename.strip()
        content = content.strip()
        
        # Usuwanie śmieci (markdown, komentarze)
        content = re.sub(r"^```[a-zA-Z]*\n", "", content)
        content = re.sub(r"\n```$", "", content)
        
        write_file(filename, content)
        print(f"-> Zaktualizowano plik: {filename}")
        created_files.append(filename)
        
    return created_files

def developer_node(state: ProjectState):
    """
    Developer node – z RAG dla lepszego kontekstu.
    """
    plan = state.get("tech_stack", "Brak planu.")
    feedback = state.get("qa_feedback", "")
    current_revisions = state.get("iteration_count", 0)
    vectorstore = state.get("vectorstore")  # RAG z state
    
    # RAG: Pobierz relewantny kontekst (np. z wymagań)
    rag_query = f"Napraw lub zbuduj kod dla: {plan[:100]}..."  # Krótki query
    rag_context = retrieve_context(rag_query, vectorstore)
    
    existing_files = get_all_file_paths()
    code_context = ""
    
    if existing_files:
        print(f"--- PROGRAMISTA: ANALIZA {len(existing_files)} PLIKÓW + RAG ---")
        for fname in existing_files:
            # Ignorujemy pliki binarne/systemowe, czytamy tylko kod
            if fname.endswith(('.py', '.js', '.html', '.css', '.cs', '.json', '.md', '.txt')):
                content = read_file(fname)
                if content:  # Tylko jeśli plik ma zawartość
                    code_context += f"\n=== PLIK ISTNIEJĄCY: {fname} ===\n{content}\n" + "="*40 + "\n"
    else:
        code_context = "BRAK PLIKÓW (Nowy projekt)."

    # Konfiguracja modelu
    model_name = os.getenv("MODEL_CODER", "llama3.3:70b")
    
    # WAŻNE: Używamy get_llm (jak kolega), nie get_chat_model
    # Bardzo duży kontekst, żeby zmieścił cały stary kod + nowy kod + RAG
    llm = get_llm(model_name, temperature=0.0, num_ctx=24000)

    # ============================================
    # 2. PRZYGOTOWANIE INSTRUKCJI
    # ============================================
    if feedback and "REJECT" in str(feedback).upper():
        mode = "TRYB NAPRAWY (DEBUGGING) z RAG"
        task_desc = f"Tester zgłosił błędy:\n{feedback}\nTwoim zadaniem jest je naprawić. Użyj RAG kontekstu: {rag_context}"
        current_revisions += 1
    elif existing_files:
        mode = "TRYB ROZWOJU (REFACTORING) z RAG"
        task_desc = f"Kontynuuj rozwój projektu zgodnie z planem architekta. Użyj RAG kontekstu: {rag_context}"
    else:
        mode = "TRYB TWORZENIA (GREENFIELD) z RAG"
        task_desc = f"Zbuduj pierwszą działającą wersję projektu zgodnie z planem. Użyj RAG kontekstu: {rag_context}"

    print(f"--- PROGRAMISTA: {mode} ---")

    # 3. SYSTEM PROMPT (jak u kolegi) – z osobowością perfekcjonisty
    # ============================================
    sys_msg = SystemMessage(content=f"""
Jesteś Expert Software Engineerem-perfekcjonistą specjalizującym się w refaktoryzacji.
Twoim celem jest dostarczenie DZIAŁAJĄCEGO, KOMPLETNEGO kodu. Używasz RAG do lepszego zrozumienia wymagań.

--- ZASADY EDYCJI PLIKÓW (KRYTYCZNE) ---
1. Jeśli edytujesz plik, musisz zwrócić jego PEŁNĄ, NOWĄ ZAWARTOŚĆ.
2. ABSOLUTNY ZAKAZ używania skrótów: `// ... reszta kodu`, `# ... existing code`. TO PSUJE PLIK.
3. Musisz zachować istniejące funkcjonalności, chyba że plan każe je usunąć.
4. Upewnij się, że nowe funkcje (np. nowa klasa) są faktycznie WYWOŁYWANE w głównym kodzie (np. w game loop).

--- FORMAT ODPOWIEDZI ---
Krok 1: ANALIZA (Jako komentarz). Napisz krótko: co zmienisz, w którym miejscu. Uwzględnij RAG.
Krok 2: KOD. Użyj znaczników:

### FILE: sciezka/plik.ext
PEŁNY_KOD_PLIKU
### ENDFILE
""")

    # 4. USER PROMPT (konkretne dane)
    # ============================================
    user_msg = HumanMessage(content=f"""
TRYB PRACY: {mode}

PLAN ARCHITEKTA (CO ZROBIĆ):
{plan}

ZADANIE SZCZEGÓŁOWE:
{task_desc}

AKTUALNY KOD PROJEKTU (KONTEKST):
{code_context}

Rozpocznij od analizy zmian (z RAG), a potem wygeneruj PEŁNE pliki.
""")
    
    # 5. WYWOŁANIE MODELU (jak u kolegi!)
    # ============================================
    full_response = ""
    try:
        print("--- WYSYŁANIE DO AI (To może chwilę potrwać)... ---")
        
        # KLUCZOWE: Używamy listy [SystemMessage, HumanMessage]
        response_obj = llm.invoke([sys_msg, user_msg])
        full_response = response_obj.content
        
        print(f"-> Otrzymano {len(full_response)} znaków.")
        
    except Exception as e:
        err = f"BŁĄD LLM: {e}"
        print(err)
        write_file("error_log.txt", err)

    # 6. PARSOWANIE I ZAPIS
    # ============================================
    saved_files = parse_and_save_files(full_response)
    
    # Jeśli Coder nic nie zwrócił, a mieliśmy pliki
    if not saved_files and existing_files:
        saved_files = existing_files
    elif not saved_files:
        error_content = f"Brak kodu. Odpowiedź AI:\n{full_response[:500]}"
        write_file("error_report.txt", error_content)
        saved_files.append("error_report.txt")

    # 7. WCZYTAJ PLIKI Z POWROTEM DO STATE
    # ============================================
    generated = {}
    for fname in saved_files:
        content = read_file(fname)
        if content:
            generated[fname] = content
        else:
            print(f"⚠️  Nie można wczytać {fname}")
            generated[fname] = f"# Błąd wczytania\npass\n"

    return {
        "generated_code": generated,
        "logs": [f"Zaktualizowano pliki: {saved_files} (z RAG)"],
        "iteration_count": current_revisions,
        "feedback": None,
        "vectorstore": vectorstore  # Przekazuj RAG dalej
    }