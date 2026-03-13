"""
History Contextualizer Service
Resolves references and contextualizes queries using chat history
"""
import logging
from typing import List, Optional
from dataclasses import dataclass

from app.clients.ollama import ollama_client

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Simple chat message structure"""
    role: str  # "user" or "assistant"
    content: str


CONTEXTUALIZE_PROMPT = """Bạn là một assistant giúp viết lại câu hỏi để có thể hiểu được mà không cần đọc lịch sử chat.

LỊCH SỬ CHAT:
{history}

CÂU HỎI MỚI NHẤT: {question}

NHIỆM VỤ:
1. Nếu câu hỏi mới có tham chiếu mơ hồ (như "nó", "cái đó", "môn này", "ngành này"), hãy thay thế bằng tên cụ thể từ lịch sử
2. Nếu câu hỏi đã đầy đủ ý nghĩa, giữ nguyên
3. Chỉ trả về câu hỏi đã viết lại, không giải thích

VÍ DỤ:
- Lịch sử: "Môn IS336 học gì?" -> "Môn IS336 dạy về..."
- Câu hỏi: "Nó có bao nhiêu tín chỉ?"
- Viết lại: "Môn IS336 có bao nhiêu tín chỉ?"

CÂU HỎI VIẾT LẠI:"""


class HistoryContextualizer:
    """
    Resolve references and contextualize queries using chat history.
    
    Uses LLM to rewrite queries that contain references ("nó", "cái đó", etc.)
    to standalone queries that can be understood without history.
    """
    
    def __init__(self):
        self.prompt_template = CONTEXTUALIZE_PROMPT
    
    def _format_history(self, messages: List[ChatMessage], max_messages: int = 5) -> str:
        """Format chat history for prompt"""
        # Take last N messages
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        history_lines = []
        for msg in recent_messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            # Truncate long messages
            content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
            history_lines.append(f"{role_label}: {content}")
        
        return "\n".join(history_lines)
    
    def _needs_contextualization(self, query: str) -> bool:
        """Quick check if query likely needs contextualization"""
        # Vietnamese pronouns and references that need context
        reference_patterns = [
            "nó", "cái đó", "cái này", "môn này", "môn đó", "ngành này", "ngành đó",
            "ở trên", "vừa nói", "như trên", "điều đó", "thứ đó", "chúng",
            "còn gì nữa", "tiếp theo", "thêm về"
        ]
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in reference_patterns)
    
    async def contextualize(
        self,
        query: str,
        history: List[ChatMessage],
        max_history: int = 5
    ) -> str:
        """
        Contextualize query using chat history.
        
        Args:
            query: Current user query
            history: List of previous messages
            max_history: Max messages to use for context
            
        Returns:
            Contextualized query (or original if no context needed)
        """
        # No history = no contextualization needed
        if not history:
            logger.debug("No history, returning original query")
            return query
        
        # Quick check for references
        if not self._needs_contextualization(query):
            logger.debug("Query doesn't need contextualization: %s", query[:50])
            return query
        
        # Build prompt
        formatted_history = self._format_history(history, max_history)
        prompt = self.prompt_template.format(
            history=formatted_history,
            question=query
        )
        
        try:
            # Use LLM to rewrite
            contextualized = await ollama_client.generate_answer(prompt)
            contextualized = contextualized.strip()
            
            # Validate response
            if not contextualized or len(contextualized) < 3:
                logger.warning("Invalid contextualization result, using original")
                return query
            
            logger.info(
                "Contextualized query: '%s' -> '%s'",
                query[:50], contextualized[:50]
            )
            return contextualized
            
        except Exception as e:
            logger.error("Contextualization failed: %s", e)
            return query  # Fallback to original


# Global instance
history_contextualizer = HistoryContextualizer()
