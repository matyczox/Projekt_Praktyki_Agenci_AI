# app.py
import chainlit as cl
from langgraph.graph import StateGraph, END
from core.state import ProjectState
from agents.product_owner import product_owner_node
from agents.architect import architect_node
from agents.developer import developer_node
from agents.qa import qa_node
import shutil
import os
from core.rag import init_rag


WORKSPACE_DIR = "./output_projects"


def clear_workspace():
    """Czyści folder z projektami przy każdym nowym czacie"""
    if os.path.exists(WORKSPACE_DIR):
        print(f"Czyszczę folder {WORKSPACE_DIR} przed nowym projektem...")
        shutil.rmtree(WORKSPACE_DIR)
    os.makedirs(WORKSPACE_DIR, exist_ok=True)


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
    workflow.add_conditional_edges("qa_engineer", should_continue, {"fix": "developer", "end": END})
    return workflow.compile()


@cl.on_chat_start
async def start():
    clear_workspace()
    cl.user_session.set("app", build_graph())
    await cl.Message(content="AgileFlow z RAG gotowy! Co budujemy?").send()


@cl.on_message
async def main(message: cl.Message):
    app = cl.user_session.get("app")
    clear_workspace()

    # Inicjalizacja RAG – na start indeksujemy tylko prośbę użytkownika
    user_request = message.content
    vectorstore = init_rag([user_request])

    state = {
        "user_request": user_request,
        "iteration_count": 0,
        "generated_code": {},
        "logs": [],
        "vectorstore": vectorstore,  # przekazujemy RAG do wszystkich agentów
        "requirements": "",
        "tech_stack": ""
    }

    msg = cl.Message(content="")
    await msg.send()

    async for output in app.astream(state):
        for key, value in output.items():
            if key == "product_owner":
                state["requirements"] = value.get("requirements", "")
                # Aktualizujemy RAG – dodajemy backlog
                vectorstore = init_rag([user_request, state["requirements"]])
                state["vectorstore"] = vectorstore
                await cl.Message(author="Product Owner", content=state["requirements"]).send()

            elif key == "architect":
                state["tech_stack"] = value.get("tech_stack", "")
                # Aktualizujemy RAG – dodajemy plan techniczny
                vectorstore = init_rag([user_request, state["requirements"], state["tech_stack"]])
                state["vectorstore"] = vectorstore
                await cl.Message(author="Architekt", content=state["tech_stack"]).send()

            elif key == "developer":
                files = list(value["generated_code"].keys())
                await cl.Message(
                    author="Developer (Qwen3-coder)",
                    content=f"Utworzył / poprawił {len(files)} plików:\n" + "\n".join(f"• {f}" for f in files)
                ).send()

            elif key == "qa_engineer":
                status = value["qa_status"]
                feedback = value["qa_feedback"]
                await cl.Message(
                    author="QA Engineer",
                    content=f"**{status}**\n\n{feedback}"
                ).send()

                # Opcjonalna interakcja – możesz wyłączyć
                if status == "REJECTED":
                    confirm_msg = await cl.AskUserMessage(content="Naprawić kod? (tak/nie)").send()
                    if "nie" in confirm_msg.content.lower():
                        await cl.Message(content="Anulowano dalsze iteracje.").send()
                        return

    await cl.Message(content="Projekt gotowy!\n\nSprawdź folder: `./output_projects`").send()