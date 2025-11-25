import chainlit as cl
from langgraph.graph import StateGraph, END
from core.state import ProjectState
from agents.product_owner import product_owner_node
from agents.architect import architect_node
from agents.developer import developer_node
from agents.qa import qa_node
import shutil
import os
from core.rag import init_rag  # RAG inicjalizacja

WORKSPACE_DIR = "./output_projects"

def clear_workspace():
    """Usuwa wszystko z output_projects przy każdym nowym czacie"""
    if os.path.exists(WORKSPACE_DIR):
        print(f"🧹 Czyszczę folder {WORKSPACE_DIR} przed nowym projektem...")
        shutil.rmtree(WORKSPACE_DIR)
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    # Opcjonalnie: utwórz .gitkeep
    open(os.path.join(WORKSPACE_DIR, ".gitkeep"), "a").close()

def should_continue(state: ProjectState):
    if state["qa_status"] == "APPROVED" or state["iteration_count"] >= 5:
        return "end"
    return "fix"

def build_graph():
    workflow = StateGraph(ProjectState)
    workflow.add_node("product_owner", product_owner_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("qa_engineer", qa_node)
    
    workflow.set_entry_point("product_owner")
    workflow.add_edge("product_owner", "architect")
    workflow.add_edge("architect", "developer")
    workflow.add_edge("developer", "qa_engineer")
    
    workflow.add_conditional_edges(
        "qa_engineer", should_continue, {"fix": "developer", "end": END}
    )
    return workflow.compile()

@cl.on_chat_start
async def start():
    clear_workspace()
    cl.user_session.set("app", build_graph())
    await cl.Message(content="🚀 AgileFlow z RAG gotowy! Co budujemy?").send()

@cl.on_message
async def main(message: cl.Message):
    app = cl.user_session.get("app")
    clear_workspace()
    
    # RAG: Indeksuj wiedzę projektu (user_request na start)
    initial_docs = [message.content]  # Dodaj requirements/tech_stack w workflow
    vectorstore = init_rag(initial_docs)
    
    state = {
        "user_request": message.content, 
        "iteration_count": 0, 
        "generated_code": {}, 
        "logs": [],
        "vectorstore": vectorstore  # Przekazuj RAG do agentów
    }
    
    msg = cl.Message(content="")
    await msg.send()
    
    async for output in app.astream(state):
        for key, value in output.items():
            if key == "product_owner":
                # Dodaj requirements do RAG (aktualizacja w locie)
                state["vectorstore"] = init_rag(initial_docs + [value['requirements']])
                await cl.Message(author="Product Owner", content=value['requirements']).send()
            elif key == "architect":
                # Dodaj tech_stack do RAG
                state["vectorstore"] = init_rag(initial_docs + [value['requirements'], value['tech_stack']])
                await cl.Message(author="Architekt", content=value['tech_stack']).send()
            elif key == "developer":
                files = list(value['generated_code'].keys())
                await cl.Message(author="Developer", content=f"Utworzono pliki: {files} (z RAG)").send()
            elif key == "qa_engineer":
                await cl.Message(author="QA", content=f"Status: {value['qa_status']}\n{value['qa_feedback']}").send()
                
                # Opcjonalna interakcja: Zatwierdź REJECTED?
                if value['qa_status'] == "REJECTED":
                    confirm = await cl.AskUserMessage(content="Zatwierdzasz iterację naprawy? (yes/no)").send()
                    if confirm.content.lower() == "no":
                        await cl.Message(content="Anulowano iterację.").send()
                        return
    
    await cl.Message(content="✅ Proces zakończony. Projekt w `output_projects/`, RAG w `./chroma_db/`").send()