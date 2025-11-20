from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
import os

llm = get_chat_model(os.getenv("MODEL_REASONING", "llama3.3:70b"), temperature=0.1)

QA_SYSTEM_PROMPT = """
Jesteś QA Engineerem. Oceń kod.
Odpisz 'APPROVED' jeśli działa.
Odpisz 'REJECTED: <powód>' jeśli są błędy.
"""

def qa_node(state: ProjectState) -> ProjectState:
    print("\n🕵️‍♂️ QA: Sprawdzam kod...")
    code_dict = state.get("generated_code", {})
    
    if not code_dict:
        return {"qa_status": "REJECTED", "qa_feedback": "Brak kodu!", "logs": ["QA Pusto"]}

    full_code = "\n".join([f"--- {k} ---\n{v}" for k, v in code_dict.items()])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", QA_SYSTEM_PROMPT),
        ("user", f"Kod:\n{full_code}")
    ])
    
    print("🕵️‍♂️ QA: Analizuję...")
    response = (prompt | llm).invoke({})
    status = "APPROVED" if "APPROVED" in response.content else "REJECTED"
    
    print(f"🕵️‍♂️ QA Decyzja: {status}")
    
    return {
        "qa_status": status,
        "qa_feedback": response.content,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "logs": [f"QA: {status}"]
    }