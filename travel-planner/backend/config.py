"""
Configuration module for the Travel Planner backend.
Uses pydantic-settings for validated, type-safe configuration management.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration management."""

    # API Keys
    gemini_api_key: str = ""
    openai_api_key: Optional[str] = None
    hotel_api_key: Optional[str] = None

    # Paths
    vector_db_path: str = "./vector_db/chroma_data"
    dataset_path: str = "./dataset/processed"

    # Model Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_provider: str = "gemini"
    temperature: float = 0.7
    max_tokens: int = 2048

    # RAG Configuration
    vector_search_k: int = 5
    max_context_length: int = 8000
    similarity_threshold: float = 0.3

    # Execution
    debug: bool = True
    log_level: str = "INFO"
    port: int = 8000

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
