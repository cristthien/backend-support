"""
Token counter utilities for tracking prompt sizes
"""
import tiktoken
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TokenCounter:
    """Token counter using tiktoken (OpenAI's tokenizer)"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize token counter
        
        Args:
            model: Model name for encoding (gpt-4o-mini, gpt-4, gpt-3.5-turbo)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
            self.model = model
            logger.info(f"Initialized token counter for model: {model}")
        except KeyError:
            # Fallback to cl100k_base encoding (used by GPT-4 and GPT-3.5-turbo)
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.model = "cl100k_base"
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Failed to count tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 chars for English, ≈ 1.5 chars for Vietnamese)
            return len(text) // 2
    
    def count_prompt_tokens(self, system_prompt: str, user_prompt: str) -> Dict[str, int]:
        """
        Count tokens for a complete chat prompt
        
        Args:
            system_prompt: System message
            user_prompt: User message
            
        Returns:
            Dictionary with token counts
        """
        system_tokens = self.count_tokens(system_prompt)
        user_tokens = self.count_tokens(user_prompt)
        
        # Add overhead for chat format (approximate)
        # Each message has ~4 tokens overhead: <|im_start|>role\n...<|im_end|>
        overhead = 8  # 4 tokens per message * 2 messages
        
        total = system_tokens + user_tokens + overhead
        
        return {
            "system_tokens": system_tokens,
            "user_tokens": user_tokens,
            "overhead_tokens": overhead,
            "total_tokens": total
        }
    
    def analyze_prompt(self, prompt: str, query: str, context: str) -> Dict[str, int]:
        """
        Analyze token distribution in RAG prompt
        
        Args:
            prompt: Full prompt text
            query: Query text
            context: Context text
            
        Returns:
            Detailed token breakdown
        """
        # Count individual components
        prompt_tokens = self.count_tokens(prompt)
        query_tokens = self.count_tokens(query)
        context_tokens = self.count_tokens(context)
        
        # Instruction is the rest (prompt - context - query)
        # Approximate by counting the template text
        instruction_template = """Bạn là một trợ lý tư vấn tuyển sinh đại học chuyên nghiệp. Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên dựa trên thông tin được cung cấp.

NGUYÊN TẮC TRẢ LỜI:
- Chỉ sử dụng thông tin từ CONTEXT được cung cấp bên dưới
- Trả lời bằng tiếng Việt, rõ ràng và súc tích
- Nếu thông tin không đủ để trả lời, hãy nói thẳng là "Tôi không có đủ thông tin để trả lời câu hỏi này"
- Không bịa đặt hoặc suy luận thông tin không có trong CONTEXT
- Trích dẫn thông tin chính xác từ CONTEXT

QUY TRÌNH TRẢ LỜI TỐI ƯU:
- Context được tổ chức theo cấu trúc phân cấp (parent-child sections)
- Sections lồng nhau thể hiện mối quan hệ phụ thuộc (## là parent, ### là child)
- Sử dụng biểu tượng 📍 và đường dẫn để hiểu vị trí của thông tin trong tài liệu
- Phân tích cấu trúc để nắm bắt mối quan hệ giữa các phần
- Ưu tiên thông tin từ sections ở đầu (được xếp hạng cao nhất)
- Tổng hợp thông tin từ parent và child sections để có câu trả lời đầy đủ
- Sử dụng ngôn ngữ tự nhiên, thân thiện và chuyên nghiệp

CONTEXT (có cấu trúc phân cấp):

CÂU HỎI: 

TRẢ LỜI:"""
        instruction_tokens = self.count_tokens(instruction_template)
        
        return {
            "total_prompt_tokens": prompt_tokens,
            "instruction_tokens": instruction_tokens,
            "context_tokens": context_tokens,
            "query_tokens": query_tokens,
            "context_percentage": round(context_tokens / prompt_tokens * 100, 1) if prompt_tokens > 0 else 0,
            "instruction_percentage": round(instruction_tokens / prompt_tokens * 100, 1) if prompt_tokens > 0 else 0,
        }
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> Dict[str, float]:
        """
        Estimate API cost for token usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name
            
        Returns:
            Cost breakdown in USD
        """
        # Pricing as of Dec 2024 (per 1M tokens)
        pricing = {
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        }
        
        prices = pricing.get(model, pricing["gpt-4o-mini"])
        
        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "model": model
        }


# Global token counter instance
token_counter = TokenCounter()
