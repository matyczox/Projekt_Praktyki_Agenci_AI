from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

ARCHITECT_SYSTEM_PROMPT = """
Jesteś Głównym Architektem Systemów IT.
Projektujesz strukturę plików dla projektu.

ZASADY:
1. Zaplanuj sensowny podział na pliki (główny plik, logika, konfiguracja, UI).
2. KRÓTKO opisz przeznaczenie każdego pliku (1-2 zdania).
3. NIE generuj kodu - tylko plan struktury.
4. W liście JSON uwzględnij TYLKO pliki tekstowe (.py, .js, .html, .css, .md, .txt, .json).
5. NIE dodawaj do JSON obrazków (.png, .jpg) ani dźwięków (.wav, .mp3).

STRUKTURA ODPOWIEDZI:
1. Krótki opis projektu (2-3 zdania)
2. Lista plików z opisem każdego
3. Na końcu: JSON z nazwami plików

PRZYKŁAD:

Projekt: Prosta gra w kółko i krzyżyk w przeglądarce.

Pliki:
- index.html - Główny plik HTML, struktura UI
- game.js - Logika gry (stan planszy, sprawdzanie wygranej)
- styles.css - Stylowanie planszy i UI
- README.md - Instrukcja uruchomienia

```json
[
  "index.html",
  "game.js",
  "styles.css",
  "README.md"
]
```

KRYTYCZNE: JSON MUSI być na końcu odpowiedzi, w bloku ```json```.
"""

def architect_node(state: ProjectState) -> ProjectState:
    print("\n📐 Architekt: Projektuję strukturę...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ARCHITECT_SYSTEM_PROMPT),
        ("user", f"Zaprojektuj strukturę plików dla:\n\n{state.get('requirements')}")
    ])
    
    response = (prompt | llm).invoke({})
    
    print("📐 Architekt: Struktura gotowa")
    
    return {
        "tech_stack": response.content,
        "logs": ["Architekt zaprojektował strukturę."]
    }