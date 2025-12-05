# services/vector_store_service.py
"""
Serwis RAG - zarządzanie bazą wektorową ChromaDB.
Ulepszone chunkowanie, wyszukiwanie i filtrowanie.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_community.vectorstores import Chroma
from config import settings
from services.llm_service import llm_service
from utils.logger import get_service_logger

logger = get_service_logger("vectorstore")


class VectorStoreService:
    """
    Serwis do zarządzania bazą wektorową ChromaDB.
    Obsługuje dodawanie projektów i wyszukiwanie podobieństw.
    """
    
    def __init__(self):
        self._vectorstore: Optional[Chroma] = None
        self._ensure_db_path()
    
    def _ensure_db_path(self) -> None:
        """Tworzy folder bazy danych jeśli nie istnieje."""
        if not settings.chroma_db_path.exists():
            settings.chroma_db_path.mkdir(parents=True)
            logger.info(f"Utworzono folder bazy: {settings.chroma_db_path}")
    
    def get_vectorstore(self) -> Chroma:
        """
        Zwraca instancję ChromaDB (singleton).
        
        Returns:
            Skonfigurowana instancja Chroma
        """
        if self._vectorstore is None:
            logger.info("Inicjalizuję ChromaDB...")
            embeddings = llm_service.get_embeddings()
            
            self._vectorstore = Chroma(
                persist_directory=str(settings.chroma_db_path),
                embedding_function=embeddings
            )
            logger.info("ChromaDB gotowe")
        
        return self._vectorstore
    
    def _chunk_code(self, content: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
        """
        Dzieli kod na chunki dla lepszego wyszukiwania.
        
        Args:
            content: Treść pliku
            chunk_size: Rozmiar chunka w znakach
            overlap: Nakładanie się chunków
        
        Returns:
            Lista chunków
        """
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Szukamy końca linii żeby nie ciąć w środku
            if end < len(content):
                newline_pos = content.rfind('\n', start, end)
                if newline_pos > start:
                    end = newline_pos + 1
            
            chunks.append(content[start:end])
            start = end - overlap
        
        return chunks
    
    def add_project(self, project_name: str, code_dict: Dict[str, str]) -> int:
        """
        Dodaje cały projekt do bazy RAG z chunkowaniem.
        
        Args:
            project_name: Nazwa projektu
            code_dict: Słownik {filename: content}
        
        Returns:
            Liczba dodanych chunków
        """
        texts = []
        metadatas = []
        ids = []
        
        for filename, content in code_dict.items():
            chunks = self._chunk_code(content)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{project_name}__{filename}__chunk{i}"
                
                texts.append(chunk)
                metadatas.append({
                    "project": project_name,
                    "filename": filename,
                    "source": f"{project_name}/{filename}",
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
                ids.append(chunk_id)
        
        if texts:
            vectorstore = self.get_vectorstore()
            vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
            logger.info(f"Dodano projekt '{project_name}': {len(code_dict)} plików, {len(texts)} chunków")
        
        return len(texts)
    
    def search_similar(
        self,
        query: str,
        k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Wyszukuje podobne fragmenty kodu.
        
        Args:
            query: Zapytanie tekstowe
            k: Liczba wyników (domyślnie z config)
            score_threshold: Próg podobieństwa (domyślnie z config)
        
        Returns:
            Lista wyników z metadanymi
        """
        k = k or settings.rag_top_k
        score_threshold = score_threshold or settings.rag_score_threshold
        
        vectorstore = self.get_vectorstore()
        
        try:
            results = vectorstore.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Błąd wyszukiwania w ChromaDB: {e}")
            return []
        
        formatted = []
        for doc, score in results:
            # ChromaDB używa L2 distance - mniejsze = lepsze
            # Filtrujemy wyniki powyżej progu
            if score < score_threshold:
                formatted.append({
                    "content": doc.page_content,
                    "filename": doc.metadata.get("filename", "unknown"),
                    "project": doc.metadata.get("project", "unknown"),
                    "score": round(score, 3),
                    "chunk_index": doc.metadata.get("chunk_index", 0)
                })
        
        logger.debug(f"Znaleziono {len(formatted)} wyników dla zapytania")
        return formatted
    
    def get_project_files(self, project_name: str) -> List[str]:
        """
        Zwraca listę plików dla danego projektu.
        
        Args:
            project_name: Nazwa projektu
        
        Returns:
            Lista nazw plików
        """
        vectorstore = self.get_vectorstore()
        
        try:
            # Pobierz wszystkie dokumenty z metadanymi
            results = vectorstore.similarity_search(
                f"project:{project_name}",
                k=100,
                filter={"project": project_name}
            )
            
            filenames = set()
            for doc in results:
                if "filename" in doc.metadata:
                    filenames.add(doc.metadata["filename"])
            
            return list(filenames)
        except Exception as e:
            logger.warning(f"Nie można pobrać plików projektu: {e}")
            return []


# Singleton
vector_store_service = VectorStoreService()


# === Funkcje pomocnicze dla kompatybilności wstecznej ===

def add_project_to_rag(project_name: str, code_dict: Dict[str, str]) -> int:
    """Wrapper dla kompatybilności z istniejącym kodem."""
    return vector_store_service.add_project(project_name, code_dict)


def get_similar_code(query: str, k: int = 6) -> List[Dict[str, Any]]:
    """Wrapper dla kompatybilności z istniejącym kodem."""
    return vector_store_service.search_similar(query, k=k)
