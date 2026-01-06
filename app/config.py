"""
Centralized configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Elasticsearch Configuration
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_sections_index: str = "sections"
    elasticsearch_chunks_index: str = "chunks"
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "bge-m3"
    ollama_embedding_model_dim: int = 1024
    ollama_llm_model: str = "gemma3:4b"
    ollama_temperature: float = 0.3
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    top_k_chunks: int = 10
    top_k_sections: int = 5
    batch_size: int = 10
    
    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    @property
    def elasticsearch_url(self) -> str:
        """Construct Elasticsearch URL"""
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
