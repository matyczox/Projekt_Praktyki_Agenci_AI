# app.py
"""
AgileFlow Pro - główna aplikacja Chainlit.
Orkiestracja workflow agentów przez LangGraph.
"""

import shutil
from pathlib import Path

import chainlit as cl
from langgraph.graph import StateGraph, END

from config import settings
from core.state import ProjectState, create_initial_state
from agents import product_owner_node, architect_node, developer_node, qa_node
from services.file_service import file_service
from services.vector_store_service import add_project_to_rag
from utils.logger import get_logger

logger = get_logger("app")


def should_continue(state: ProjectState) -> str:
    """
    Decyduje czy kontynuować pętlę dev-QA.
    
    Returns:
        "end" - jeśli APPROVED lub limit iteracji
        "fix" - jeśli trzeba poprawić kod
    """
    if state.get("qa_status") == "APPROVED":
        return "end"
    
    if state.get("iteration_count", 0) >= settings.max_iterations:
        logger.warning(f"Limit {settings.max_iterations} iteracji osiągnięty")
        return "end"
    
    return "fix"


def build_graph() -> StateGraph:
    """
    Buduje graf workflow AgileFlow.
    
    Flow:
        product_owner -> architect -> developer -> qa_engineer
                                            ^            |
                                            |--- fix <---|
    
    Returns:
        Skompilowany graf LangGraph
    """
    workflow = StateGraph(ProjectState)
    
    # Dodaj nodes
    workflow.add_node("product_owner", product_owner_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("qa_engineer", qa_node)
    
    # Ustaw przepływ
    workflow.set_entry_point("product_owner")
    workflow.add_edge("product_owner", "architect")
    workflow.add_edge("architect", "developer")
    workflow.add_edge("developer", "qa_engineer")
    
    # Warunkowa pętla QA -> Developer
    workflow.add_conditional_edges(
        "qa_engineer",
        should_continue,
        {"fix": "developer", "end": END}
    )
    
    return workflow.compile()


@cl.on_chat_start
async def start():
    """Inicjalizacja sesji Chainlit."""
    cl.user_session.set("app", build_graph())
    logger.info("Sesja rozpoczęta")
    await cl.Message(content="**AgileFlow Pro Ready!** Co robimy?").send()


@cl.on_message
async def main(message: cl.Message):
    """Główna obsługa wiadomości użytkownika."""
    
    # Czyść folder output przed nowym projektem
    file_service.clear_output()
    
    app = cl.user_session.get("app")
    state = create_initial_state(message.content)
    
    # TaskList - progress bar w UI
    task_list = cl.TaskList()
    task_list.status = "Running"
    
    task_po = cl.Task(title="Tech Lead", status=cl.TaskStatus.RUNNING)
    task_arch = cl.Task(title="Architekt", status=cl.TaskStatus.READY)
    task_dev = cl.Task(title="Coder", status=cl.TaskStatus.READY)
    task_qa = cl.Task(title="QA", status=cl.TaskStatus.READY)
    
    await task_list.add_task(task_po)
    await task_list.add_task(task_arch)
    await task_list.add_task(task_dev)
    await task_list.add_task(task_qa)
    await task_list.send()
    
    msg = cl.Message(content="")
    await msg.send()
    
    # Streamuj wykonanie workflow
    async for output in app.astream(state):
        for key, value in output.items():
            
            if key == "product_owner":
                task_po.status = cl.TaskStatus.DONE
                task_arch.status = cl.TaskStatus.RUNNING
                await task_list.send()
                await cl.Message(
                    author="Tech Lead",
                    content=f"**Specyfikacja:**\n{value['requirements']}"
                ).send()
            
            elif key == "architect":
                task_arch.status = cl.TaskStatus.DONE
                task_dev.status = cl.TaskStatus.RUNNING
                await task_list.send()
                await cl.Message(
                    author="Architekt",
                    content=f"**Plan projektu:**\n{value['tech_stack']}"
                ).send()
            
            elif key == "developer":
                task_dev.status = cl.TaskStatus.DONE
                task_qa.status = cl.TaskStatus.RUNNING
                await task_list.send()
                
                # Wyświetl wygenerowane pliki
                files = list(value['generated_code'].keys())
                elements = [
                    cl.Text(
                        name=f,
                        content=c,
                        language=_get_language(f),
                        display="inline"
                    )
                    for f, c in value['generated_code'].items()
                ]
                await cl.Message(
                    author="Coder",
                    content=f"Pliki ({len(files)}):",
                    elements=elements
                ).send()
            
            elif key == "qa_engineer":
                if value['qa_status'] == "APPROVED":
                    task_qa.status = cl.TaskStatus.DONE
                    task_list.status = "Done"
                    await task_list.send()
                    await cl.Message(
                        author="QA",
                        content="**APPROVED** – Kod przeszedł testy!"
                    ).send()
                else:
                    task_qa.status = cl.TaskStatus.FAILED
                    task_dev.status = cl.TaskStatus.RUNNING
                    await task_list.send()
                    await cl.Message(
                        author="QA",
                        content=f"**REJECTED**\n{value['qa_feedback']}"
                    ).send()
    
    # ZIP na koniec
    project_name = _sanitize_project_name(state["user_request"])
    zip_path = shutil.make_archive(f"projekt_{project_name}", 'zip', "output_projects")
    
    await cl.Message(
        content="**Projekt gotowy!**",
        elements=[cl.File(name=f"{project_name}.zip", path=zip_path, display="inline")]
    ).send()
    
    # Zapisz do RAG jeśli APPROVED
    if state.get("qa_status") == "APPROVED" and state.get("generated_code"):
        add_project_to_rag(project_name, state["generated_code"])
        await cl.Message(
            content=f"RAG: Projekt \"{project_name}\" zapisany do pamięci długoterminowej"
        ).send()
    
    logger.info(f"Projekt '{project_name}' zakończony")


def _get_language(filename: str) -> str:
    """Mapuje rozszerzenie pliku na język dla Chainlit."""
    ext_map = {
        ".py": "python",
        ".pyi": "python",
        ".js": "javascript",
        ".html": "html",
        ".css": "css",
        ".md": "markdown",
        ".json": "json",
    }
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang
    return "text"


def _sanitize_project_name(user_request: str) -> str:
    """Czyści nazwę projektu z user_request."""
    name = user_request[:60]
    name = name.replace(" ", "_").replace('"', '').replace("'", "")
    return name.strip()