from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

ARCHITECT_SYSTEM_PROMPT = """
Jesteś Głównym Architektem Systemów IT.
Zaprojektuj strukturę plików dla projektu.

ZASADY KRYTYCZNE:
1. Zaplanuj sensowny podział na pliki (logika, widoki, config).
2. KRÓTKO opisz przeznaczenie każdego pliku.
3. ABSOLUTNY ZAKAZ generowania kodu implementacyjnego.
4. W liście JSON uwzględnij TYLKO pliki tekstowe (.py, .js, .html, .css, .md, .txt).
5. NIE WPISUJ do JSONa obrazków (.png) ani dźwięków (.wav).
6. Na samym końcu odpowiedzi MUSISZ wygenerować blok JSON z listą plików.

PRZYKŁAD FORMATU KOŃCOWEGO:
...opis...
```json
[
  "main.py",
  "game_logic.py",
  "requirements.txt"
]
```
"""

def architect_node(state: ProjectState) -> ProjectState:
    print("\n📐 Architekt: Projektuję strukturę...")
    prompt = ChatPromptTemplate.from_messages([
        ("system", ARCHITECT_SYSTEM_PROMPT),
        ("user", f"Wymagania:\n{state.get('requirements')}")
    ])
    response = (prompt | llm).invoke({})
    return {
        "tech_stack": response.content,
        "logs": ["Architekt zaprojektował strukturę."]
    }