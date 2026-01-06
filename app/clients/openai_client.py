"""
OpenAI GPT-4o-mini integration for LLM generation
"""
from openai import AsyncOpenAI
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client wrapper for GPT-4o-mini"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (if None, will use from settings)
        """
        self.api_key = api_key or settings.openai_api_key
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info(f"Initialized OpenAI client - Model: {settings.openai_model}")
    
    async def generate_answer(self, prompt: str, temperature: Optional[float] = None) -> str:
        """
        Generate answer using GPT-4o-mini
        
        Args:
            prompt: Input prompt with query and context
            temperature: Override default temperature (0.0-2.0)
            
        Returns:
            Generated answer text
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            temp = temperature if temperature is not None else settings.openai_temperature
            
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là trợ lý tư vấn tuyển sinh đại học chuyên nghiệp."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temp,
                max_tokens=settings.openai_max_tokens
            )
            
            answer = response.choices[0].message.content
            logger.info(f"Generated answer with OpenAI (tokens: {response.usage.total_tokens})")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer with OpenAI: {e}")
            raise
    
    async def generate_answer_stream(self, prompt: str, temperature: Optional[float] = None):
        """
        Generate answer with streaming using GPT-4o
        
        Args:
            prompt: Input prompt with query and context
            temperature: Override default temperature (0.0-2.0)
            
        Yields:
            Text chunks as they are generated
        """
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            temp = temperature if temperature is not None else settings.openai_temperature
            
            stream = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là trợ lý tư vấn tuyển sinh đại học chuyên nghiệp."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temp,
                max_tokens=settings.openai_max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Failed to generate streaming answer with OpenAI: {e}")
            raise


# Global OpenAI client instance
openai_client = OpenAIClient()
