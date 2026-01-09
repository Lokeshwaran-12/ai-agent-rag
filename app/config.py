"""
Configuration management for the AI Agent RAG System.
Loads environment variables and provides centralized configuration.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure OpenAI Configuration - Chat Model
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: str = "gpt-4"
    azure_openai_api_version: str = "2024-02-15-preview"
    
    # Azure OpenAI Configuration - Embedding Model (can be separate deployment)
    azure_openai_embedding_endpoint: Optional[str] = None  # Falls back to azure_openai_endpoint if not set
    azure_openai_embedding_api_key: Optional[str] = None  # Falls back to azure_openai_api_key if not set
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"
    
    # OpenAI Configuration (fallback)
    openai_api_key: Optional[str] = None
    
    # Azure AI Search Configuration
    azure_search_endpoint: Optional[str] = None
    azure_search_api_key: Optional[str] = None
    azure_search_index_name: str = "documents-index"
    
    # Application Settings
    app_name: str = "AI Agent RAG System"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # RAG Settings
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 500
    chunk_overlap: int = 100
    top_k_results: int = 7
    
    # Agent Settings
    max_iterations: int = 5
    temperature: float = 0.7
    max_tokens: int = 1000
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
