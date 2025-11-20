import chainlit as cl
from langgraph.graph import StateGraph, END
from core.state import ProjectState
from agents.product_owner import product_owner_node
from agents.architect import architect_node
from agents.developer import developer_node
from agents.qa import qa_node

def should_continue(state: ProjectState):
    if state["qa_status"] == "APPROVED" or state["iteration_count"] >= 3:
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
    cl.user_session.set("app", build_graph())
    await cl.Message(content="🚀 AgileFlow Gotowy! Co budujemy?").send()

@cl.on_message
async def main(message: cl.Message):
    app = cl.user_session.get("app")
    state = {"user_request": message.content, "iteration_count": 0, "generated_code": {}, "logs": []}
    
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
                await cl.Message(author="Developer", content=f"Utworzono pliki: {files}").send()
            elif key == "qa_engineer":
                await cl.Message(author="QA", content=f"Status: {value['qa_status']}\n{value['qa_feedback']}").send()
                
    await cl.Message(content="✅ Proces zakończony.").send()