import chainlit as cl
from langgraph.graph import StateGraph, END
from core.state import ProjectState
from agents.product_owner import product_owner_node
from agents.architect import architect_node
from agents.developer import developer_node
from agents.qa import qa_node
import shutil
from pathlib import Path  # ← dodane


MAX_ITERATIONS = 10


# NOWA FUNKCJA: Czyści output_projects przy każdym nowym projekcie
def clear_output_projects():
    """
    Usuwa cały folder output_projects i tworzy go od nowa.
    Dzięki temu każdy nowy projekt zaczyna na czysto – zero śmieci z poprzednich runów.
    """
    folder = Path("output_projects")
    if folder.exists() and folder.is_dir():
        shutil.rmtree(folder)
        print("Usunięto stary folder output_projects")
    folder.mkdir(exist_ok=True)
    print("Utworzono nowy, czysty folder output_projects")


def should_continue(state: ProjectState):
    if state.get("qa_status") == "APPROVED":
        return "end"
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        print(f"Limit {MAX_ITERATIONS} iteracji osiągnięty.")
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
    cl.user_session.set("app", build_graph())
    await cl.Message(content="**AgileFlow Pro Ready!** Co robimy?").send()


@cl.on_message
async def main(message: cl.Message):
    # CZYSZCZENIE FOLDERU PRZED KAŻDYM NOWYM PROJEKTEM
    clear_output_projects()

    app = cl.user_session.get("app")
    state = {
        "user_request": message.content,
        "iteration_count": 0,
        "generated_code": {},
        "qa_feedback": "",
        "qa_status": "",
        "logs": []
    }

    # TaskList – ładny progress bar
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

                files = list(value['generated_code'].keys())
                elements = [
                    cl.Text(
                        name=f,
                        content=c,
                        language="python" if f.endswith((".py", ".pyi")) else
                                 "javascript" if f.endswith(".js") else
                                 "html" if f.endswith(".html") else
                                 "css" if f.endswith(".css") else
                                 "markdown" if f.endswith(".md") else
                                 "json" if f.endswith(".json") else "text",
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
                    await cl.Message(author="QA", content="**APPROVED** – Kod przeszedł testy!").send()
                else:
                    task_qa.status = cl.TaskStatus.FAILED
                    task_dev.status = cl.TaskStatus.RUNNING
                    await task_list.send()
                    await cl.Message(
                        author="QA",
                        content=f"**REJECTED**\n{value['qa_feedback']}"
                    ).send()

    # ZIP na koniec + DODANIE DO RAG
    project_name = state["user_request"][:60].replace(" ", "_").replace('"', '').strip()
    zip_path = shutil.make_archive(f"projekt_{project_name}", 'zip', "output_projects")

    await cl.Message(
        content="**Projekt gotowy!**",
        elements=[cl.File(name=f"{project_name}.zip", path=zip_path, display="inline")]
    ).send()

    # <<< KLUCZOWY RAG >>>
    if state.get("qa_status") == "APPROVED" and state.get("generated_code"):
        from core.vector_store import add_project_to_rag
        add_project_to_rag(project_name, state["generated_code"])
        await cl.Message(content=f"RAG: Projekt \"{project_name}\" zapisany do pamięci długoterminowej").send()