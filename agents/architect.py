from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState

llm = get_chat_model(temperature=0.1)

ARCHITECT_SYSTEM_PROMPT = """
Jesteś Architektem. Zaprojektuj stack technologiczny i listę plików.
Projekt musi być w Pythonie.
"""

def architect_node(state: ProjectState) -> ProjectState:
    print("\n📐 Architekt: Projektuję...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", ARCHITECT_SYSTEM_PROMPT),
        ("user", f"Wymagania:\n{state.get('requirements')}")
    ])
    
    print("📐 Architekt: Generuję plan...")
    response = (prompt | llm).invoke({})
    
    return {
        "tech_stack": response.content,
        "logs": ["Architekt stworzył strukturę."]
    }