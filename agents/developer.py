from langchain_core.prompts import ChatPromptTemplate
from core.llm_factory import get_chat_model
from core.state import ProjectState
from tools.file_system import save_file
import os

llm = get_chat_model(os.getenv("MODEL_CODER", "qwen3-coder:30b"), temperature=0.1)
llm_with_tools = llm.bind_tools([save_file])

DEV_SYSTEM_PROMPT = """
Jesteś Senior Python Developerem.
Masz zaimplementować projekt lub wprowadzić poprawki zgłoszone przez QA.

Masz dostęp do narzędzia 'save_file'.
Jeśli to pierwsza iteracja: Napisz kod od zera wg planu.
Jeśli to poprawka (QA Feedback): Popraw TYLKO wskazane błędy i nadpisz pliki używając 'save_file'.

PAMIĘTAJ: ZAWSZE używaj narzędzia 'save_file' do zapisu wyników pracy.
"""

def developer_node(state: ProjectState) -> ProjectState:
    iteration = state.get("iteration_count", 0)
    qa_feedback = state.get("qa_feedback", "")
    
    if iteration > 0 and qa_feedback:
        print(f"\n👨‍💻 Developer: Wdzięczam poprawki (Iteracja {iteration})...")
        user_msg = f"QA odrzucił poprzedni kod. Powód:\n{qa_feedback}\n\nPopraw kod i zapisz go ponownie."
    else:
        print("\n👨‍💻 Developer: Piszę kod od zera...")
        user_msg = f"Plan techniczny:\n{state.get('tech_stack')}\n\nZacznij implementację."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", DEV_SYSTEM_PROMPT),
        ("user", user_msg)
    ])
    
    chain = prompt | llm_with_tools
    response = chain.invoke({})
    
    logs = []
    generated_files = {}
    
    if response.tool_calls:
        print(f"🔨 Developer aktualizuje {len(response.tool_calls)} plików...")
        for tool_call in response.tool_calls:
            args = tool_call["args"]
            filename = args.get("filename")
            content = args.get("code_content")
            
            save_file.invoke(args) # Fizyczny zapis
            
            logs.append(f"Zapisano/Zaktualizowano: {filename}")
            generated_files[filename] = content
    else:
        logs.append("Developer nie wykonał zmian w plikach.")

    # Aktualizujemy stan o nowy kod (lub nadpisujemy stary)
    current_code = state.get("generated_code", {})
    current_code.update(generated_files)

    return {
        "generated_code": current_code,
        "logs": logs
    }