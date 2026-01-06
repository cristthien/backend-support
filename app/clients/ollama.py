"""
Ollama integration using Langchain Ollama for embeddings and chat
"""
from langchain_ollama import OllamaEmbeddings, ChatOllama
from typing import List
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama client wrapper using Langchain"""
    
    def __init__(self):
        # Initialize embedding model (BGE-M3)
        # Note: Ollama Langchain uses OLLAMA_HOST env variable or defaults to localhost:11434
        self.embedding_model = OllamaEmbeddings(
            model=settings.ollama_embedding_model
        )
        
        # Initialize LLM (Gemma3:4b)
        self.llm = ChatOllama(
            model=settings.ollama_llm_model,
            temperature=settings.ollama_temperature
        )

        
        logger.info(f"Initialized Ollama client - Embedding: {settings.ollama_embedding_model}, LLM: {settings.ollama_llm_model}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using BGE-M3
        
        Args:
            text: Input text to embed
            
        Returns:
            List of 1024 floats (embedding vector)
        """
        try:
            embedding = await self.embedding_model.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = await self.embedding_model.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    async def generate_answer(self, prompt: str) -> str:
        """
        Generate answer using Gemma3:4b
        
        Args:
            prompt: Input prompt with query and context
            
        Returns:
            Generated answer text
        """
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise
    
    async def generate_answer_stream(self, prompt: str):
        """
        Generate answer with streaming using Gemma3:4b
        
        Args:
            prompt: Input prompt with query and context
            
        Yields:
            Text chunks as they are generated
        """
        try:
            async for chunk in self.llm.astream(prompt):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Failed to generate streaming answer: {e}")
            raise


# Global Ollama client instance
ollama_client = OllamaClient()
