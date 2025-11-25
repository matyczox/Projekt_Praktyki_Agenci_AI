import chainlit as cl
from langgraph.graph import StateGraph, END
from core.state import ProjectState
from agents.product_owner import product_owner_node
from agents.architect import architect_node
from agents.developer import developer_node
from agents.qa import qa_node
import shutil
import os

WORKSPACE_DIR = "./output_projects"

def clear_workspace():
    """Czyści folder output_projects przed każdym nowym projektem"""
    if os.path.exists(WORKSPACE_DIR):
        print(f"🧹 Czyszczę folder {WORKSPACE_DIR} przed nowym projektem...")
        shutil.rmtree(WORKSPACE_DIR)
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    open(os.path.join(WORKSPACE_DIR, ".gitkeep"), "a").close()

def should_continue(state: ProjectState):
    if state.get("qa_status") == "APPROVED":
        return "end"
    if state.get("iteration_count", 0) >= 5:
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
        "qa_engineer",
        should_continue,
        {"fix": "developer", "end": END}
    )
    return workflow.compile()

@cl.on_chat_start
async def start():
    clear_workspace()  # Kluczowe: czyści stare projekty
    cl.user_session.set("app", build_graph())
    await cl.Message(content="AgileFlow Gotowy! Co budujemy?").send()

@cl.on_message
async def main(message: cl.Message):
    app = cl.user_session.get("app")
    clear_workspace()  # Dodatkowe bezpieczeństwo

    state = {
        "user_request": message.content,
        "iteration_count": 0,
        "generated_code": {},
        "logs": []
    }

    msg = cl.Message(content="")
    await msg.send()

    async for output in app.astream(state):
        for key, value in output.items():
            if key == "product_owner":
                await cl.Message(author="Product Owner", content=value['requirements']).send()
            elif key == "architect":
                await cl.Message(author="Architekt", content=value['tech_stack']).send()
            elif key == "developer":
                files = list(value['generated_code'].keys())
                await cl.Message(author="Developer", content=f"Utworzono pliki:\n{', '.join(files)}").send()
            elif key == "qa_engineer":
                status = value['qa_status']
                feedback = value['qa_feedback']
                await cl.Message(author="QA Engineer", content=f"**{status}**\n\n{feedback}").send()

    await cl.Message(content="Proces zakończony!\nProjekt gotowy w folderze `output_projects/`").send()