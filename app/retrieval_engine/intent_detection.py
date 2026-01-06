import logging
import json
from enum import Enum

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """5 Retrieval-Focused Intent Groups for UIT Q&A System"""
    OVERVIEW = "overview"
    STRUCTURE = "structure"
    ROADMAP = "roadmap"
    FACTUAL = "factual"
    COMPARE = "compare"


INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Phân loại câu hỏi vào 1 trong 5 nhóm. ƯU TIÊN kiểm tra theo THỨ TỰ:

1. **compare** - So sánh 2 đối tượng RÕ RÀNG
   - Phải có 2 tên riêng (ngành A và ngành B, môn X và môn Y)
   - Keywords: "khác gì", "so sánh", "khác nhau"

2. **roadmap** - Hỏi về lộ trình HỌC KỲ hoặc NĂM cụ thể
   - PHẢI có "học kỳ/kỳ/kì + SỐ" hoặc "năm + SỐ"
   - VD: "Học kỳ 1 học gì?", "Năm 3 học những môn gì?"
   - LƯU Ý: "kì mấy" hỏi về SỐ → factual

3. **overview** - Hỏi TỔNG QUAN ngành hoặc môn học
   - Hỏi chung về nội dung: "ngành X học gì", "môn Y dạy gì"
   - KHÔNG áp dụng cho: khối kiến thức, nghề nghiệp, cơ hội việc làm

4. **factual** - Hỏi THÔNG TIN CỤ THỂ, câu trả lời ngắn
   - Số liệu: "bao nhiêu tín chỉ", "mấy tín chỉ"
   - Có/Không: "có cần", "được không"
   - Tiên quyết: "môn tiên quyết"
   - KHÔNG áp dụng cho: TOEIC tốt nghiệp, điều kiện tốt nghiệp → structure

5. **structure** - TẤT CẢ còn lại (default)
   - Quy định: học bổng, TOEIC, bảo lưu, chuyển ngành, điều kiện tốt nghiệp
   - Đánh giá: rubric, cách tính điểm, chuẩn đầu ra CLO/G1-G4
   - Khối kiến thức: "khối kiến thức đại cương", "khối kiến thức chuyên nghiệp"
   - Nghề nghiệp: "làm nghề gì", "ra trường làm gì", "cơ hội việc làm"
   - Quy trình: "làm sao", "như thế nào"

Trả về JSON: {{"intent": "<factual|overview|roadmap|compare|structure>"}}"""),
    ("human", "{query}")
])


def _get_llm():
    """Get LLM configured for JSON output"""
    if settings.use_openai and settings.openai_api_key:
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
    else:
        return ChatOllama(
            model=settings.ollama_llm_model,
            temperature=0,
            format="json"
        )


def _parse_intent(response: str) -> QueryIntent:
    """Parse JSON response to QueryIntent"""
    try:
        data = json.loads(response.strip())
        intent_str = data.get("intent", "structure").lower().strip()
        
        intent_map = {
            "factual": QueryIntent.FACTUAL,
            "overview": QueryIntent.OVERVIEW,
            "roadmap": QueryIntent.ROADMAP,
            "compare": QueryIntent.COMPARE,
            "structure": QueryIntent.STRUCTURE,
            "policy": QueryIntent.STRUCTURE,  # Map policy → structure
        }
        return intent_map.get(intent_str, QueryIntent.STRUCTURE)
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        logger.warning("Failed to parse intent response: %s, error: %s", response, e)
        return QueryIntent.STRUCTURE


async def detect_intent(query: str) -> QueryIntent:
    """
    Detect intent from user query using LangChain with JSON mode
    
    Args:
        query: User query text
        
    Returns:
        QueryIntent enum value
    """
    try:
        llm = _get_llm()
        chain = INTENT_PROMPT | llm | StrOutputParser()
        
        response = await chain.ainvoke({"query": query})
        intent = _parse_intent(response)
        
        logger.info("Detected intent: %s for query: '%s'", intent.value, query[:50])
        return intent
        
    except Exception as e:
        logger.warning("Intent detection failed: %s, defaulting to FACTUAL", e)
        return QueryIntent.FACTUAL



