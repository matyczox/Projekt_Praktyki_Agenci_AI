from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState

llm = get_chat_model(temperature=0.3)

PO_SYSTEM_PROMPT = """
Jesteś Product Ownerem. Stwórz Backlog na podstawie pomysłu użytkownika.
Zawrzyj: Cel biznesowy, User Stories, Kryteria Akceptacji.
Nie pisz kodu.
"""

def product_owner_node(state: ProjectState) -> ProjectState:
    print("\n🎩 Product Owner: Startuję...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", PO_SYSTEM_PROMPT),
        ("user", state["user_request"])
    ])
    
    chain = prompt | llm
    
    print(f"🎩 Product Owner: Wysyłam zapytanie do modelu... (To może chwilę potrwać)")
    response = chain.invoke({})
    print("🎩 Product Owner: Otrzymałem odpowiedź!")
    
    return {
        "requirements": response.content,
        "logs": ["Product Owner stworzył backlog."]
    }