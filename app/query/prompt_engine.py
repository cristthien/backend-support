"""
Prompt Engine: Builds context and prompts from retrieved sections
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Prompt Engine: Transforms retrieved sections into structured prompts
    
    Responsibilities:
    - Build hierarchy context from sections
    - Build content context from sections
    - Generate final prompt for LLM
    """
    
    def build_hierarchy_context(self, sections: List[Dict]) -> str:
        """
        Build hierarchy context showing document structure
        
        Args:
            sections: List of retrieved sections
            
        Returns:
            Formatted hierarchy string
        """
        hierarchy_parts = []
        for idx, section in enumerate(sections):
            hierarchy_path = section.get('hierarchy_path', 'Unknown')
            hierarchy_parts.append(f"Đường dẫn của Context {idx}: {hierarchy_path}\n")
        
        return "\n".join(hierarchy_parts)
    
    def build_content_context(self, sections: List[Dict]) -> str:
        """
        Build content context from section texts
        
        Args:
            sections: List of retrieved sections
            
        Returns:
            Formatted content string
        """
        context_parts = []
        for idx, section in enumerate(sections):
            text = section.get('text', '')
            context_parts.append(f"Context {idx}: {text}\n")
        
        return "\n".join(context_parts)
    
    def generate_prompt(
        self,
        query: str,
        sections: List[Dict]
    ) -> str:
        """
        Generate complete RAG prompt
        
        Args:
            query: User query
            sections: Retrieved and reranked sections
            
        Returns:
            Complete prompt string for LLM
        """
        logger.info("Building prompt from %d sections", len(sections))
        
        # Build contexts
        hierarchy = self.build_hierarchy_context(sections)
        content = self.build_content_context(sections)
        
        # Build final prompt
        prompt = f"""Bạn là một trợ lý tư vấn tuyển sinh đại học chuyên nghiệp. Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên dựa trên thông tin được cung cấp.

NGUYÊN TẮC TRẢ LỜI:
- Chỉ sử dụng thông tin từ CONTEXT được cung cấp bên dưới
- Trả lời bằng tiếng Việt, rõ ràng và súc tích
- Nếu thông tin không đủ để trả lời, hãy nói thẳng là "Tôi không có đủ thông tin để trả lời câu hỏi này"
- Không bịa đặt hoặc suy luận thông tin không có trong CONTEXT
- Trích dẫn thông tin chính xác từ CONTEXT

Quy trình để trả về được câu trả lời tốt nhất:
- Dựa theo phần "Đường dẫn" ở mỗi đầu content để hiểu cấu trúc tài liệu dựa trên câu hỏi đặt ra
- Phân cấp các phần thông tin quan trọng dựa trên câu hỏi để xây dựng câu trả lời
- Sử dụng ngôn ngữ tự nhiên, thân thiện và chuyên nghiệp để trả lời câu hỏi

Hãy sử dụng hierarchy bên dưới để hiểu cấu trúc phân cấp của các phần CONTEXT:
{hierarchy}

Sau đó sử dụng CONTEXT bên dưới để trả lời câu hỏi:
CONTEXT:
{content}

CÂU HỎI: {query}

TRẢ LỜI:"""
        
        logger.info("Prompt generated successfully")
        return prompt


# Global instance
prompt_engine = PromptEngine()
