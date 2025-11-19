import chainlit as cl
from langgraph.graph import StateGraph, END
from core.state import ProjectState

# Importujemy naszych agentów
from agents.product_owner import product_owner_node
from agents.architect import architect_node
from agents.developer import developer_node
from agents.qa import qa_node

# --- LOGIKA GRAFU (Taka sama jak w main.py) ---

def should_continue(state: ProjectState):
    """Decyduje czy wracamy do Deva czy kończymy."""
    status = state.get("qa_status", "REJECTED")
    iteration = state.get("iteration_count", 0)
    
    if status == "APPROVED" or iteration >= 3:
        return "end"
    else:
        return "fix"

def build_graph():
    """Buduje maszynę stanów."""
    workflow = StateGraph(ProjectState)
    
    # Węzły
    workflow.add_node("product_owner", product_owner_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("qa_engineer", qa_node)
    
    # Krawędzie
    workflow.set_entry_point("product_owner")
    workflow.add_edge("product_owner", "architect")
    workflow.add_edge("architect", "developer")
    workflow.add_edge("developer", "qa_engineer")
    
    workflow.add_conditional_edges(
        "qa_engineer",
        should_continue,
        {
            "fix": "developer",
            "end": END
        }
    )
    
    return workflow.compile()

# --- INTERFEJS CHAINLIT ---

@cl.on_chat_start
async def start():
    """To się uruchamia, gdy otwierasz stronę."""
    
    # Budujemy graf i zapisujemy go w sesji użytkownika
    app = build_graph()
    cl.user_session.set("app", app)
    
    await cl.Message(
        content="👋 **Witaj w AgileFlow!**\n\nJestem Twoim managerem AI. Opisz, jaką aplikację mam stworzyć, a mój zespół (PO, Architekt, Dev, QA) zajmie się resztą.",
        author="Agile Manager"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """To się uruchamia, gdy wyślesz wiadomość."""
    
    app = cl.user_session.get("app")
    
    # Stan początkowy
    initial_state = {
        "user_request": message.content,
        "iteration_count": 0,
        "generated_code": {},
        "logs": []
    }
    
    # Informacja o starcie
    msg = cl.Message(content="", author="System")
    await msg.send()
    
    # Uruchamiamy graf w trybie strumieniowania (async)
    # Dzięki temu widzimy postęp krok po kroku
    async for output in app.astream(initial_state):
        
        # Sprawdzamy, który agent właśnie skończył pracę
        for key, value in output.items():
            
            if key == "product_owner":
                await cl.Message(
                    content=f"### 🎩 Product Owner\n\n{value.get('requirements')}", 
                    author="Product Owner"
                ).send()
                
            elif key == "architect":
                await cl.Message(
                    content=f"### 📐 Architekt\n\n{value.get('tech_stack')}", 
                    author="Architekt"
                ).send()
                
            elif key == "developer":
                # Wyciągamy nazwy plików, które stworzył
                code_files = value.get("generated_code", {}).keys()
                file_list = ", ".join(code_files) if code_files else "Brak zmian w plikach"
                
                await cl.Message(
                    content=f"### 👨‍💻 Developer\n\nZaimplementowałem/Poprawiłem pliki:\n`{file_list}`\n\n*(Pliki zapisane w folderze output_projects)*", 
                    author="Developer"
                ).send()

            elif key == "qa_engineer":
                status = value.get("qa_status")
                feedback = value.get("qa_feedback")
                
                icon = "✅" if status == "APPROVED" else "❌"
                
                await cl.Message(
                    content=f"### 🐞 QA Engineer\n\n**Status:** {icon} {status}\n\n**Raport:**\n{feedback}", 
                    author="QA Engineer"
                ).send()

    # Koniec procesu
    await cl.Message(
        content="🚀 **Proces zakończony!** Sprawdź folder `output_projects` na dysku.", 
        author="Agile Manager"
    ).send()