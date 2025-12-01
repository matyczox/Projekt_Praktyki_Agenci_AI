# agents/architect.py
from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from core.vector_store import get_similar_code

llm = get_chat_model(temperature=0.1)

ARCHITECT_SYSTEM_PROMPT = """
Jesteś Głównym Architektem Systemów IT. Twoim zadaniem jest zaprojektowanie struktury plików od zera.

ZASADY (OBOWIĄZKOWE):
1. Zawsze sprawdzasz, czy w pamięci RAG są podobne projekty – jeśli tak, wykorzystujesz je jako inspirację.
2. Krótko opisujesz przeznaczenie każdego pliku (1-2 zdania).
3. Na samym końcu odpowiedzi podajesz TYLKO czysty blok JSON z samymi nazwami plików.
4. Nie generujesz kodu źródłowego.
5. Blok JSON musi wyglądać dokładnie tak (żadnych komentarzy, spacji na początku, dodatkowego tekstu po bloku):

```json
["main.py", "snake.py", "food.py", "game.py", "README.md"]
```

Przykładowa poprawna odpowiedź:
Projekt: Klasyczna gra Snake w Pythonie z biblioteką pygame.
Pliki:

main.py – punkt wejścia, główna pętla gry i inicjalizacja
snake.py – klasa Snake zarządzająca pozycją i ruchem węża
food.py – klasa Food i losowanie pozycji jabłka
game.py – logika gry, kolizje, punktacja, restart
README.md – instrukcja uruchomienia i opis projektu

JSON["main.py", "snake.py", "food.py", "game.py", "README.md"]
"""

def architect_node(state: ProjectState) -> ProjectState:
    print("\nArchitekt: Projektuję strukturę...")

    # RAG – wyszukiwanie podobnych projektów
    query = state["user_request"] + "\n" + state.get("requirements", "")
    similar = get_similar_code(query, k=8)

    rag_context = ""
    if similar:
        rag_context = "\n\nISTNIEJĄCE PODOBNE PROJEKTY (użyj jako inspiracja):\n"
        for item in similar[:5]:
            rag_context += f"\n=== {item['project']} / {item['filename']} ===\n{item['content'][:1500]}\n"

    user_prompt = f"""Specyfikacja techniczna od Tech Leada:
{state.get('requirements', 'Brak specyfikacji')}
{rag_context}
Na podstawie powyższego zaprojektuj strukturę plików.
Podaj krótki opis projektu, listę plików z opisami i na samym końcu dokładnie jeden czysty blok JSON z listą nazw plików."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", ARCHITECT_SYSTEM_PROMPT),
        ("user", user_prompt)
    ])

    response = (prompt | llm).invoke({})

    print("Architekt: Struktura gotowa")

    return {
        "tech_stack": response.content,
        "logs": ["Architekt zaprojektował strukturę z wykorzystaniem RAG"]
    }