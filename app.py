import chainlit as cl
from langgraph.graph import StateGraph, END
from core.state import ProjectState
from agents.product_owner import product_owner_node
from agents.architect import architect_node
from agents.developer import developer_node
from agents.qa import qa_node
import shutil

MAX_ITERATIONS = 10

def should_continue(state: ProjectState):
    if state["qa_status"] == "APPROVED": return "end"
    if state["iteration_count"] >= MAX_ITERATIONS:
        print(f"⚠️ Limit {MAX_ITERATIONS} iteracji osiągnięty.")
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
    cl.user_session.set("app", build_graph())
    await cl.Message(content="🚀 **AgileFlow Pro Ready!** Co robimy?").send()

@cl.on_message
async def main(message: cl.Message):
    app = cl.user_session.get("app")
    state = {"user_request": message.content, "iteration_count": 0, "generated_code": {}, "qa_feedback": "", "logs": []}
    
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
                await cl.Message(author="Tech Lead", content=f"**Spec:**\n{value['requirements']}").send()
            elif key == "architect":
                task_arch.status = cl.TaskStatus.DONE
                task_dev.status = cl.TaskStatus.RUNNING
                await task_list.send()
                await cl.Message(author="Architekt", content=f"**Plan:**\n{value['tech_stack']}").send()
            elif key == "developer":
                task_dev.status = cl.TaskStatus.DONE
                task_qa.status = cl.TaskStatus.RUNNING
                await task_list.send()
                
                files = list(value['generated_code'].keys())
                elements = [cl.Text(name=f, content=c, language="python", display="inline") for f, c in value['generated_code'].items()]
                await cl.Message(author="Coder", content=f"🔨 Pliki ({len(files)}):", elements=elements).send()
            elif key == "qa_engineer":
                if value['qa_status'] == "APPROVED":
                    task_qa.status = cl.TaskStatus.DONE
                    task_list.status = "Done"
                    await task_list.send()
                    await cl.Message(author="QA", content="✅ **APPROVED**").send()
                else:
                    task_qa.status = cl.TaskStatus.FAILED
                    task_dev.status = cl.TaskStatus.RUNNING
                    await task_list.send()
                    await cl.Message(author="QA", content=f"❌ **REJECTED:**\n{value['qa_feedback']}").send()

    shutil.make_archive("projekt", 'zip', "output_projects")
    await cl.Message(content="🎁 **ZIP:**", elements=[cl.File(name="projekt.zip", path="projekt.zip", display="inline")]).send()