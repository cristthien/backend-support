"""
Generation Engine: Handles LLM-based answer generation
"""
import logging
from app.clients.ollama import ollama_client
from app.clients.openai_client import openai_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class GenerationEngine:
    """
    Generation Engine: Generates answers using LLM
    
    Responsibilities:
    - Select appropriate LLM (OpenAI or Ollama)
    - Generate answer from prompt
    - Handle generation errors
    """
    
    async def generate(self, prompt: str) -> str:
        """
        Generate answer using configured LLM
        
        Args:
            prompt: Complete prompt string
            
        Returns:
            Generated answer text
        """
        logger.info("Generating answer using LLM: %s", prompt)
        
        try:
            if settings.use_openai and settings.openai_api_key:
                logger.info("Using OpenAI GPT-4o for answer generation")
                answer = await openai_client.generate_answer(prompt)
            else:
                logger.info("Using Ollama for answer generation")
                answer = await ollama_client.generate_answer(prompt)
            
            logger.info("Answer generated successfully (length: %d chars)", len(answer))
            return answer
            
        except Exception as e:
            logger.error("Error generating answer: %s", e)
            return "Xin lỗi, đã xảy ra lỗi khi tạo câu trả lời. Vui lòng thử lại."


# Global instance
generation_engine = GenerationEngine()
