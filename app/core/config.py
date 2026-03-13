"""
Centralized configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Elasticsearch Configuration
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_sections_index: str = "sections"
    elasticsearch_chunks_index: str = "chunks"
    
    # Ollama Configuration (for backward compatibility and when using Ollama provider)
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "bge-m3"  # Kept for backward compatibility
    ollama_embedding_model_dim: int = 1024  # Kept for backward compatibility
    ollama_llm_model: str = "gemma3:4b"
    ollama_temperature: float = 0.5
    
    # Cohere Reranker Configuration
    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-multilingual-v3.0"
    rerank_top_n: int = 5
    enable_reranking: bool = False
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"  
    openai_temperature: float = 0.3
    openai_max_tokens: int = 2000
    use_openai: bool = True
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    top_k_chunks: int = 10
    top_k_sections: int = 5
    batch_size: int = 10
    
    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Query Expansion Configuration
    enable_query_expansion: bool = True
    
    # Search Mode Configuration
    search_mode: str = "vector"  # "vector", "fulltext", "hybrid"
    hybrid_vector_weight: float = 0.7
    hybrid_text_weight: float = 0.3
    
    # History Context Configuration
    enable_history_context: bool = True
    history_context_window: int = 5  # Number of messages to use for context
    
    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "rag_user"
    postgres_password: str = "rag_password"
    postgres_db: str = "rag_auth_db"
    
    # JWT Authentication
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Google OAuth Configuration
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"
    
    # Email Configuration (for OTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "RAG Backend"
    
    # OTP Configuration
    otp_expire_minutes: int = 10
    otp_length: int = 6
    
    # Frontend URL
    frontend_url: str = "http://localhost:3000"
    
    @property
    def elasticsearch_url(self) -> str:
        """Construct Elasticsearch URL"""
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL async database URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

