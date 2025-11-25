# core/rag.py
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.llm_factory import get_embeddings_model
import os
import shutil

PERSIST_DIR = "./chroma_db"

def _ensure_string(content) -> str:
    """Bezpiecznie wyciąga tekst z stringa albo Document"""
    if isinstance(content, str):
        return content
    if isinstance(content, Document):
        return content.page_content
    return str(content)  # ostateczny fallback

def init_rag(docs):
    """
    Przyjmuje listę stringów LUB obiektów Document – działa zawsze.
    Czyści poprzednią bazę przy każdym nowym projekcie.
    """
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)
        print("Czyszczę poprzednią ChromaDB")

    os.makedirs(PERSIST_DIR, exist_ok=True)

    # Konwertujemy wszystko na stringi
    texts = [_ensure_string(doc) for doc in docs if _ensure_string(doc).strip()]

    if not texts:
        print("Brak tekstów do zaindeksowania w RAG")
        return None

    # Tworzymy dokumenty LangChain
    documents = [Document(page_content=text) for text in texts]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=get_embeddings_model(),
        persist_directory=PERSIST_DIR
    )
    vectorstore.persist()
    print(f"RAG zainicjalizowany – zaindeksowano {len(splits)} chunków")

    return vectorstore

def retrieve_context(query: str, vectorstore):
    if not vectorstore or not query.strip():
        return "Brak kontekstu RAG."

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    relevant = retriever.get_relevant_documents(query)
    context = "\n".join([doc.page_content for doc in relevant])
    print(f"RAG zwrócił {len(relevant)} chunków")
    return f"\n--- RAG KONTEKST ---\n{context}\n--- KONIEC RAG ---\n"