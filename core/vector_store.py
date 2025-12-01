# core/vector_store.py
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from pathlib import Path
import shutil

CHROMA_PATH = Path("chroma_db")
EMBEDDING_MODEL = "nomic-embed-text"

embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url="http://localhost:11434")

def get_vectorstore():
    if not CHROMA_PATH.exists():
        CHROMA_PATH.mkdir(parents=True)
    return Chroma(persist_directory=str(CHROMA_PATH), embedding_function=embeddings)

def add_project_to_rag(project_name: str, code_dict: dict):
    """Dodaje cały projekt do bazy RAG"""
    texts = []
    metadatas = []
    ids = []
    
    for filename, content in code_dict.items():
        texts.append(content)
        metadatas.append({
            "project": project_name,
            "filename": filename,
            "source": f"{project_name}/{filename}"
        })
        ids.append(f"{project_name}__{filename}")
    
    vectorstore = get_vectorstore()
    vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    print(f"RAG: Dodano projekt '{project_name}' ({len(code_dict)} plików)")

def get_similar_code(query: str, k: int = 6):
    """Zwraca najbardziej podobne istniejące pliki"""
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_score(query, k=k)
    
    formatted = []
    for doc, score in results:
        if score < 0.75:  # filtrujemy szum
            formatted.append({
                "content": doc.page_content,
                "filename": doc.metadata["filename"],
                "project": doc.metadata["project"],
                "score": round(score, 3)
            })
    return formatted