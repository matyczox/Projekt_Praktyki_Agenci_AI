# config.py
"""
Scentralizowana konfiguracja projektu AgileFlow.
Wszystkie ustawienia w jednym miejscu z walidacją typów.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Główna klasa konfiguracyjna projektu."""
    
    # === Ollama ===
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="URL serwera Ollama"
    )
    ollama_verify_ssl: bool = Field(default=True)
    ollama_token: Optional[str] = Field(default=None)
    ollama_timeout: float = Field(default=600.0)
    
    # === Modele LLM ===
    model_reasoning: str = Field(
        default="qwen2.5-coder:14b",
        description="Model do rozumowania i generowania kodu"
    )
    model_embeddings: str = Field(
        default="nomic-embed-text",
        description="Model do embeddingów"
    )
    
    # === Parametry LLM ===
    llm_num_ctx: int = Field(default=8192, description="Rozmiar kontekstu")
    llm_num_predict: int = Field(default=8192, description="Max tokenów w odpowiedzi")
    llm_temperature_default: float = Field(default=0.2)
    
    # === Ścieżki ===
    output_dir: Path = Field(default=Path("output_projects"))
    chroma_db_path: Path = Field(default=Path("chroma_db"))
    
    # === Limity ===
    max_iterations: int = Field(default=10, description="Max pętli dev-QA")
    rag_top_k: int = Field(default=6, description="Ile wyników z RAG")
    rag_score_threshold: float = Field(default=0.75, description="Próg podobieństwa")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignoruj nieznane zmienne środowiskowe


# Singleton - jedna instancja dla całej aplikacji
settings = Settings()
