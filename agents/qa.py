from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

# QA potrzebuje modelu "Reasoning" (Llama 3.3), żeby znaleźć błędy logiczne
llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

QA_SYSTEM_PROMPT = """
Jesteś surowym QA Engineerem (Testerem).
Twoim zadaniem jest sprawdzić kod wygenerowany przez Developera pod kątem:
1. Zgodności z planem Architekta.
2. Błędów składniowych i logicznych.
3. Bezpieczeństwa i dobrych praktyk (Clean Code).

Jeśli kod jest dobry: Odpisz tylko "APPROVED".
Jeśli kod ma błędy: Odpisz "REJECTED: [Krótki opis co poprawić]".

NIE POPRAWIAJ KODU. Tylko zgłoś błędy.
"""

def qa_node(state: ProjectState) -> ProjectState:
    print("\n🕵️‍♂️ QA: Sprawdzam jakość kodu...")
    
    # Pobieramy kod ze stanu
    code_dict = state.get("generated_code", {})
    tech_stack = state.get("tech_stack", "")
    
    if not code_dict:
        return {
            "qa_status": "REJECTED",
            "qa_feedback": "Brak kodu do sprawdzenia!",
            "logs": ["QA: Pusto. Odrzucam."]
        }

    # Sklejamy kod w jeden tekst dla LLM
    full_code_preview = ""
    for filename, content in code_dict.items():
        full_code_preview += f"\n--- PLIK: {filename} ---\n{content}\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        ("user", f"Plan Architekta: {tech_stack}\n\nWygenerowany Kod:\n{full_code_preview}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({})
    
    result = response.content
    status = "APPROVED" if "APPROVED" in result else "REJECTED"
    
    print(f"🕵️‍♂️ QA Decyzja: {status}")
    if status == "REJECTED":
        print(f"   Powód: {result}")

    return {
        "qa_status": status,
        "qa_feedback": result, # Tu jest opis błędu dla Developera
        "iteration_count": state.get("iteration_count", 0) + 1,
        "logs": [f"QA zakończył sprawdzanie. Status: {status}"]
    }