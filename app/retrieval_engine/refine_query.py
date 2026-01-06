"""
Query Refinement Module

This module provides functions to refine user queries for better retrieval:
1. Lowercase normalization
2. Abbreviation expansion for Vietnamese education terms
3. LLM-based query refinement using Ollama
"""
import re
import logging
from typing import Optional

from app.clients.ollama import ollama_client

logger = logging.getLogger(__name__)

# Vietnamese education abbreviation mappings (abbreviation -> full name)
ABBREVIATION_MAP = {
    "KHMT": "Khoa học máy tính",
    "KTPM": "Kỹ thuật phần mềm",
    "KTMT": "Kỹ thuật máy tính",
    "HTTT": "Hệ thống thông tin",
    "CNTT": "Công nghệ thông tin",
    "ATTT": "An toàn thông tin",
    "MMT&TT": "Mạng máy tính và Truyền thông dữ liệu",
    "TMĐT": "Thương mại điện tử",
    "KHDL": "Khoa học dữ liệu",
    "TTNT": "Trí tuệ nhân tạo",
    "TKVM": "Thiết kế vi mạch",
    "TTĐPT": "Truyền thông đa phương tiện",
    "CSDL": "Cơ sở dữ liệu",
    "DE": "Data Engineering",
    # Additional common abbreviations
    "AI": "Trí tuệ nhân tạo",
    "KLTN": "Khóa luận tốt nghiệp",
    "TN": "tốt nghiệp",
    "HK": "Học kỳ",
    "PLO": "Program Learning Outcome",
}


def normalize_query(query: str) -> str:
    """
    Normalize query by converting to lowercase.
    
    Args:
        query: User input query
        
    Returns:
        Lowercased query string
    """
    return query.lower()


def expand_abbreviations(query: str) -> str:
    """
    Expand common Vietnamese education abbreviations to full names.
    Uses word-boundary matching to avoid partial replacements.
    
    Args:
        query: User input query (can be any case)
        
    Returns:
        Query with abbreviations expanded to full names
    """
    result = query
    
    # Sort by length (longest first) to handle overlapping abbreviations
    sorted_abbrevs = sorted(ABBREVIATION_MAP.keys(), key=len, reverse=True)
    
    for abbrev in sorted_abbrevs:
        full_name = ABBREVIATION_MAP[abbrev]
        # For short abbreviations (2 chars), use case-sensitive matching
        # to avoid false positives (e.g., "ai" meaning "who" in Vietnamese)
        if len(abbrev) <= 2:
            pattern = re.compile(r'\b' + re.escape(abbrev) + r'\b')
        else:
            pattern = re.compile(r'\b' + re.escape(abbrev) + r'\b', re.IGNORECASE)
        result = pattern.sub(full_name, result)
    
    return result


LLM_REFINE_PROMPT = """Bạn là trợ lý tinh chỉnh câu hỏi. Nhiệm vụ của bạn là viết lại câu hỏi để tối ưu cho việc tìm kiếm thông tin về chương trình đào tạo đại học.

Quy tắc:
1. GIỮ NGUYÊN ý định gốc của câu hỏi
2. Mở rộng các tham chiếu ngầm (ví dụ: "môn đó" -> tên môn cụ thể nếu biết)
3. Làm rõ câu hỏi cho ngữ cảnh giáo dục đại học
4. KHÔNG thêm thông tin không có trong câu hỏi gốc
5. Trả về CHỈ câu hỏi đã tinh chỉnh, không giải thích

Câu hỏi gốc: {query}

Câu hỏi đã tinh chỉnh:"""


async def refine_query_with_llm(query: str) -> str:
    """
    Refine query using Ollama LLM for better semantic search.
    
    Args:
        query: User input query (after normalization and abbreviation expansion)
        
    Returns:
        LLM-refined query string
    """
    try:
        prompt = LLM_REFINE_PROMPT.format(query=query)
        refined = await ollama_client.generate_answer(prompt)
        
        # Clean up the response
        refined = refined.strip()
        
        # If LLM returns empty or very short response, return original
        if len(refined) < 5:
            logger.warning(f"LLM returned short response, using original query")
            return query
            
        logger.info(f"Refined query: '{query}' -> '{refined}'")
        return refined
        
    except Exception as e:
        logger.error(f"LLM refinement failed: {e}, using original query")
        return query


async def refine_query(query: str, use_llm: bool = True) -> str:
    """
    Main pipeline to refine a user query.
    
    Steps:
    1. Lowercase normalization
    2. Abbreviation expansion
    3. (Optional) LLM refinement
    
    Args:
        query: User input query
        use_llm: Whether to apply LLM refinement (default: True)
        
    Returns:
        Refined query string
    """
    # Step 1: Expand abbreviations first (preserves case from mapping)
    result = expand_abbreviations(query)
    
    # Step 2: Normalize (lowercase)
    result = normalize_query(result)
    
    # Step 3: LLM refinement (optional)
    if use_llm:
        result = await refine_query_with_llm(result)
    
    return result


def refine_query_sync(query: str) -> str:
    """
    Synchronous version of refine_query without LLM.
    Useful for testing abbreviation expansion only.
    
    Args:
        query: User input query
        
    Returns:
        Refined query (abbreviations expanded + lowercase)
    """
    # First expand abbreviations, then lowercase
    result = expand_abbreviations(query)
    result = normalize_query(result)
    return result
