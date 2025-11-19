from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState

# 1. Pobieramy model "Reasoning" (ten mądrzejszy, Llama 3.3 70b)
llm = get_chat_model(temperature=0.3)

# 2. Definiujemy "Osobowość" agenta (System Prompt)
# To tutaj dzieje się magia - każemy mu być konkretnym.
PO_SYSTEM_PROMPT = """
Jesteś doświadczonym Product Ownerem w zespole Agile.
Twój cel: Przeanalizować pomysł użytkownika i stworzyć profesjonalną specyfikację (Backlog).

Twoja odpowiedź MUSI zawierać:
1. **Cel Biznesowy**: Jedno zdanie, co budujemy.
2. **User Stories**: Lista funkcjonalności w formacie "Jako użytkownik chcę..., aby...".
3. **Kryteria Akceptacji**: Co musi działać, żeby uznać zadanie za skończone.

NIE PISZ KODU. Skup się na logice biznesowej i wymaganiach.
Pisz zwięźle, punktuj, używaj Markdown.
"""

def product_owner_node(state: ProjectState) -> ProjectState:
    """
    Funkcja, która jest 'Węzłem' (Node) w naszym grafie.
    Przyjmuje stan, myśli, i zwraca zaktualizowany stan.
    """
    print("\n🎩 Product Owner: Analizuję wymagania...")
    
    # Tworzymy prompt: System Prompt + Prośba użytkownika ze stanu
    prompt = ChatPromptTemplate.from_messages([
        ("system", PO_SYSTEM_PROMPT),
        ("user", state["user_request"])
    ])
    
    # Łączymy Prompt z Modelem
    chain = prompt | llm
    
    # Uruchamiamy (Invoke)
    response = chain.invoke({})
    
    print("✅ Product Owner: Specyfikacja gotowa.")
    
    # Zwracamy TYLKO to, co się zmieniło (wymagania i logi)
    return {
        "requirements": response.content,
        "logs": ["Product Owner stworzył backlog."]
    }