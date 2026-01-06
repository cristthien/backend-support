"""
Query Expansion Module
Detects query intent and expands with relevant keywords for better retrieval
"""
import logging
from typing import Optional
from app.clients.ollama import ollama_client
from app.core.config import settings
from langchain_ollama import ChatOllama


logger = logging.getLogger(__name__)


SCHEMA_PROGRAM = """
## **Mục tiêu đào tạo** - Định hướng tổng thể của ngành
## **Cơ hội nghề nghiệp** - Các vị trí có thể làm sau tốt nghiệp
## **Quan điểm xây dựng chương trình đào tạo** - 8 chuẩn đầu ra PLO1-PLO8
## **Hình thức và thời gian đào tạo** - Thời gian đào tạo, số tín chỉ, loại hình
## **Điều kiện tốt nghiệp** - Yêu cầu về tín chỉ, điểm, ngoại ngữ
## **Các khối kiến thức**- Tổng quan về cấu trúc chương trình học
### **Khối kiến thức giáo dục đại cương** 
### **Khối kiến thức giáo dục chuyên nghiệp** 
#### **Nhóm các môn học cơ sở ngành** 
#### **Nhóm các môn học chuyên ngành**
### **Khối kiến thức tốt nghiệp** 
## **Kế hoạch giảng dạy mẫu** - Lộ trình chi tiết từng học kỳ
### **Học kì 1-8** - Nhóm các môn học được đề xuất theo học kỳ
"""

SCHEMA_SYLLABUS = """
## THÔNG TIN CHUNG - Mã môn, tên môn, số tín chỉ (LT/TH), Môn tiên quyết, khoa phụ trách
## MÔ TẢ MÔN HỌC (Course description) - Tổng quan về nội dung môn học
## MỤC TIÊU MÔN HỌC (Course goals)
## CHUẨN ĐẦU RA MÔN HỌC (Course learning outcomes) - Các chuẩn đầu ra chi tiết
## NỘI DUNG MÔN HỌC, KẾ HOẠCH GIẢNG DẠY - Các chương, buổi học
## TÀI LIỆU THAM KHẢO - Giáo trình, sách, paper, tài liệu tham khảo
"""

EXPANSION_GENERATION_PROMPT = """
Bạn là chuyên gia phân tích câu hỏi về giáo dục đại học.

NHIỆM VỤ: Dựa vào câu hỏi và schema, hãy tạo ra các từ khóa mở rộng để tìm kiếm chính xác hơn.

SCHEMA CHƯƠNG TRÌNH ĐÀO TẠO:
{schema_program}

SCHEMA MÔN HỌC:
{schema_syllabus}

3 MỨC ĐỘ MỞ RỘNG:

1. OVERVIEW (Tổng quan ngành học):
   - Câu hỏi: "Ngành CNTT học gì?", "Ngành CNTT có mấy mảng chính?"
   - Cần: các khối kiến thức trong chương trình đào tạo 
   - Trả về: "các khối kiến thức, đại cương, chuyên nghiệp, tốt nghiệp"

2. SECTION (Nội dung một phần cụ thể):
   - Câu hỏi: "Cơ sở ngành học gì?", "Học kỳ 3 học gì?", "Điều kiện tốt nghiệp?", 
   - Cần: Section/phần được hỏi + các sections liên quan
   - Trả về: Tên section cụ thể + related sections

3. DETAIL (Chi tiết):
    - Nếu hỏi về MÔN HỌC : expand theo schema môn học
    Ví dụ: "Môn Cơ sở dữ liệu học gì?" → "thông tin chung, mô tả môn học, kế hoạch giảng dạy, mục tiêu"
   - Nếu hỏi về CHƯƠNG TRÌNH: expand theo schema chương trình
     Ví dụ: "Thời gian đào tạo?" → "hình thức và thời gian đào tạo"

HƯỚNG DẪN TRẢ LỜI:
- Chỉ trả về CÁC TỪ KHÓA cách nhau bởi dấu phẩy
- Không giải thích, không thêm chữ khác
- Từ khóa phải là tên sections trong schema HOẶC khái niệm liên quan
- Tối đa 5 từ khóa

CÂU HỎI: {query}

TRẢ LỜI (chỉ từ khóa, cách nhau bởi dấu phẩy):"""

async def expand_query(
    original_query: str,
    major: Optional[str] = None,
    enable_expansion: bool = True
) -> str:
    """
    Smart query expansion using LLM to analyze schema and query
    
    3 LEVELS of expansion:
    1. OVERVIEW: "Ngành CNTT học gì?" → expand to "các khối kiến thức, ..."
    2. SECTION: "Cơ sở ngành học gì?" → expand to specific section names
    3. DETAIL: "Môn IT004 học gì?" → expand based on syllabus schema
    
    Flow:
    1. Detect intent: CHUNK or SECTION
    2. If SECTION, use LLM to generate schema-aware expansion keywords
    3. Return expanded query for Elasticsearch
    
    Args:
        original_query: User query text
        enable_expansion: Whether to enable expansion (from config)
        
    Returns:
        Expanded query string with smart keywords
    """
    if not enable_expansion:
        logger.info("Query expansion disabled")
        return original_query
    
    
    # Generate smart expansion keywords using LLM (invoke is synchronous)
    response = await ollama_client.generate_answer(EXPANSION_GENERATION_PROMPT.format(
        schema_program=SCHEMA_PROGRAM,
        schema_syllabus=SCHEMA_SYLLABUS,
        query=original_query
    ))  
    
    # Extract content from AIMessage
    expansion_terms = response.strip()
    
    if not expansion_terms:
        logger.warning("Empty expansion generated, using original query")
        return original_query
    
    # Add major context if provided
    major_context = f" ngành {major}" if major else ""
    
    # Build expanded query
    expanded = f"{original_query}, {expansion_terms}"
    
    logger.info("Smart expanded query: '%s' -> '%s'", original_query, expanded)
    
    return expanded
