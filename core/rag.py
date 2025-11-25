from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.llm_factory import get_embeddings_model
import os
import shutil

# Ścieżka do persistent ChromaDB (plikowa, bez serwera)
PERSIST_DIR = "./chroma_db"

def init_rag(docs: list[str]):
    """
    Inicjalizuje ChromaDB z dokumentami projektu (user_request, requirements, tech_stack).
    Czyści poprzednią DB dla nowego projektu.
    """
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)  # Czyść na nowy projekt
        print("🧹 Czyszczę poprzednią ChromaDB dla nowego projektu")
    
    os.makedirs(PERSIST_DIR, exist_ok=True)
    
    # Podziel dokumenty na chunki
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.create_documents([Document(page_content=doc) for doc in docs])
    
    # Stwórz vectorstore
    vectorstore = Chroma.from_documents(
        documents=split_docs,
        embedding=get_embeddings_model(),
        persist_directory=PERSIST_DIR
    )
    vectorstore.persist()
    print(f"📚 RAG zainicjalizowany: zaindeksowano {len(split_docs)} chunków w {PERSIST_DIR}")
    return vectorstore

def retrieve_context(query: str, vectorstore):
    """
    Pobiera relewantny kontekst (top 3 chunki) dla agenta.
    """
    if not vectorstore:
        return "Brak kontekstu RAG."
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    relevant_docs = retriever.get_relevant_documents(query)
    context = "\n--- RAG KONTEKST ---\n" + "\n".join([doc.page_content for doc in relevant_docs])
    print(f"🔍 RAG: Pobrano {len(relevant_docs)} relewantnych chunków dla query: {query[:50]}...")
    return context