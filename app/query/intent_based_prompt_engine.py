"""
Intent-Based Prompt Engine
Handles intent detection and schema-aware query expansion
"""
import json
import logging
from typing import Optional, List, Dict, Tuple
from enum import Enum

from app.clients.ollama import ollama_client
from app.clients.openai_client import openai_client
from app.core.config import settings
from app.retrieval_engine.intent_detection import QueryIntent

logger = logging.getLogger(__name__)


# Prompt for extracting course name from prerequisite queries
COURSE_EXTRACTION_PROMPT = """Trích xuất TÊN MÔN HỌC từ câu hỏi về môn tiên quyết.

Query: {query}

Chỉ trả về TÊN MÔN HỌC (không giải thích). Nếu không tìm thấy, trả về "UNKNOWN".

Ví dụ:
- "Môn tiên quyết của Dữ Liệu Lớn là gì?" → Dữ Liệu Lớn
- "Điều kiện học môn IS405?" → IS405
- "Học IS336 cần học môn gì trước?" → IS336

Tên môn:"""
SCHEMA_PROGRAM = """
## **Mục tiêu đào tạo** - Định hướng tổng thể của ngành
## **Vị trí và khả năng làm việc sau tốt nghiệp** - Cơ hội nghề nghiệp
## **Quan điểm xây dựng chương trình đào tạo** - 8 chuẩn đầu ra PLO1-PLO8
## **Hình thức và thời gian đào tạo** - Thời gian đào tạo, số tín chỉ, loại hình
## **Điều kiện tốt nghiệp** - Yêu cầu về tín chỉ, điểm, ngoại ngữ
## **Chuẩn đầu ra** - Các chuẩn đầu ra chi tiết (LO1-LO8)
## **Các khối kiến thức** - Tổng quan về cấu trúc chương trình học
### **Khối kiến thức giáo dục đại cương** - Lý luận chính trị, Toán, Ngoại ngữ
### **Khối kiến thức giáo dục chuyên nghiệp**
#### **Nhóm các môn học cơ sở ngành** - Các môn nền tảng bắt buộc
#### **Nhóm các môn học chuyên ngành** - Các môn chuyên sâu theo hướng
### **Khối kiến thức tốt nghiệp** - Khóa luận/Đồ án tốt nghiệp
"""

SCHEMA_SYLLABUS = """
## **THÔNG TIN CHUNG** - Mã môn, tên môn, số tín chỉ (LT/TH), môn tiên quyết, khoa phụ trách
## **MÔ TẢ MÔN HỌC** - Tổng quan về nội dung môn học
## **MỤC TIÊU MÔN HỌC** - Các mục tiêu cần đạt được sau khi học
## **CHUẨN ĐẦU RA MÔN HỌC** - Các chuẩn đầu ra chi tiết (CLO1, CLO2...)
## **NỘI DUNG MÔN HỌC, KẾ HOẠCH GIẢNG DẠY** - Các chương, buổi học, kế hoạch chi tiết
## **PHƯƠNG PHÁP ĐÁNH GIÁ** - Cách thức đánh giá, rubric
## **TÀI LIỆU THAM KHẢO** - Giáo trình, sách, papers, tài liệu tham khảo
"""

# Placeholder patterns that need resolution in ROADMAP results
PLACEHOLDER_PATTERNS = [
    # Các môn patterns
    "các môn học chuyên ngành",
    "các môn cơ sở ngành",
    "các môn tự chọn",
    "các môn học cơ sở ngành",
    "các môn học tự chọn",
    # Nhóm patterns
    "nhóm các môn học chuyên ngành",
    "nhóm các môn học cơ sở ngành",
    # Môn tự chọn patterns (from Học kỳ schedules)
    "môn tự chọn ngành",
    "môn tự chọn liên ngành",
    "môn chuyên ngành",
    "môn học chuyên ngành",
    # Khối kiến thức
    "khối kiến thức tốt nghiệp",
]



class SchemaAwareExpander:
    """
    Schema-aware query expansion based on 5 Retrieval-Focused intent groups
    
    Each intent expands to specific section targets:
    - OVERVIEW: LLM decompose sub-queries (tổng quan ngành/môn)
    - STRUCTURE: Section-level targets (cấu trúc, đánh giá, chuẩn đầu ra, quy định)
    - ROADMAP: KẾ HOẠCH GIẢNG DẠY, Học kỳ
    - FACTUAL: THÔNG TIN CHUNG, TÀI LIỆU THAM KHẢO, Tiên quyết
    - COMPARE: Both entities' sections
    """
    
    # Intent → Section Target mapping (5 intents)
    SECTION_TARGETS = {
        QueryIntent.OVERVIEW: [
            # Program/Major-level (ngành/chương trình) - ưu tiên khối kiến thức
            "Các khối kiến thức của ngành",
            "Hình thức và thời gian đào tạo của ngành",
            "Cơ hội nghề nghiệp của ngành",
            # Syllabus/Course-level (môn học)
            "THÔNG TIN CHUNG của môn",
            "MÔ TẢ MÔN HỌC của môn",
            "NỘI DUNG MÔN HỌC của môn"
        ],
        QueryIntent.STRUCTURE: [
            # Assessment
            "ĐÁNH GIÁ MÔN HỌC", 
            "PHƯƠNG PHÁP ĐÁNH GIÁ",
            "ĐÁNH GIÁ MÔN HỌC CHI TIẾT",
            # Outcomes
            "CHUẨN ĐẦU RA MÔN HỌC",
            "MỤC TIÊU MÔN HỌC",
            "Chuẩn đầu ra",
            "Vị trí và khả năng làm việc sau tốt nghiệp",
            "Cơ hội nghề nghiệp",
            # Policy
            "Quy định đào tạo ngoại ngữ",
            "Học bổng",
            "Điều kiện tốt nghiệp",
            "Chuẩn ngoại ngữ",
            # Structure
            "Các khối kiến thức",
            "Nhóm các môn học cơ sở ngành",
            "Nhóm các môn học chuyên ngành",
            "Các môn học cơ sở ngành",
            "Các môn học chuyên ngành",
            "Các môn học tự chọn ngành",
            "Khối kiến thức tốt nghiệp",
            "Hình thức tốt nghiệp"
        ],
        QueryIntent.ROADMAP: [
            "Kế hoạch giảng dạy",
            "Học kì",
        ],
        QueryIntent.FACTUAL: [
            "THÔNG TIN CHUNG",
            "TÀI LIỆU THAM KHẢO",
            "TÀI LIỆU HỌC TẬP",
            "Môn học trước",
            "Môn tiên quyết"
        ],
        QueryIntent.COMPARE: [
            "THÔNG TIN CHUNG của môn học",
            "MÔ TẢ MÔN HỌC của môn",
            "Mục tiêu đào tạo của môn và ngành học",
            "Các khối kiến thức của ngành học",
            "CHUẨN ĐẦU RA MÔN HỌC",
            "CHUẨN ĐẦU RA của NGÀNH"
        ],
    }
    
    EXPANSION_PROMPT = """Bạn là expert về schema matching cho hệ thống hỏi đáp giáo dục UIT.

        QUERY: {query}
        INTENT: {intent}
        TARGET SECTIONS: {targets}

        === NHIỆM VỤ ===
        Mở rộng query với các từ khóa để tìm đúng section chứa thông tin.

        SCHEMA PROGRAM:
        {schema_program}

        SCHEMA SYLLABUS:
        {schema_syllabus}

        === QUY TẮC ===
        1. Ưu tiên các từ khóa từ TARGET SECTIONS
        2. Thêm tên môn học/ngành nếu có trong query
        3. Thêm synonyms (ví dụ: "tín chỉ" → "TC", "đánh giá" → "assessment")

        Trả về 3-5 từ khóa, cách nhau bởi dấu phẩy:"""
    
    # Prompt for extracting 2 entities from COMPARE queries
    COMPARE_ENTITY_PROMPT = """Trích xuất 2 đối tượng đang được so sánh trong câu hỏi.

        QUERY: {query}

        === QUY TẮC ===
        1. Tìm 2 đối tượng (môn học, ngành, chương trình) được so sánh
        2. Normalize tên viết tắt: TTNT → Trí tuệ nhân tạo, CNTT → Công nghệ thông tin, HTTT → Hệ thống thông tin
        3. Với SO SÁNH MÔN HỌC: thêm prefix "Nội dung môn học" hoặc "Mục tiêu môn học" trước tên môn
        4. Với SO SÁNH NGÀNH: dùng tên ngành trực tiếp
        5. Nếu không tìm được 2 đối tượng rõ ràng, trả về "NONE"

        Ví dụ:
        - "So sánh TTNT và CNTT" → "Ngành Trí tuệ nhân tạo, Ngành Công nghệ thông tin"
        - "HTTT thường khác HTTT tiên tiến gì?" → "Ngành Hệ thống thông tin, Ngành Hệ thống thông tin tiên tiến"
        - "Môn Dữ liệu lớn khác môn kho dữ liệu OLAP gì?" → "Nội dung môn học Dữ liệu lớn, Nội dung môn học Kho dữ liệu OLAP"
        - "So sánh cơ sở dữ liệu và hệ quản trị CSDL" → "Nội dung môn học Cơ sở dữ liệu, Nội dung môn học Hệ quản trị cơ sở dữ liệu"

        Trả về 2 đối tượng, cách nhau bởi dấu phẩy:"""
    
    async def expand(
        self,
        query: str,
        intent: QueryIntent,
        major: Optional[str] = None
    ) -> str:
        """
        Expand query based on intent to target specific sections
        
        Args:
            query: Original query
            intent: Detected intent (one of 9 types)
            keywords: Keywords from intent detection (unused, kept for API compat)
            major: Optional major filter
            
        Returns:
            Expanded query string
        """
        logger.info("Expanding query with intent: %s", intent.value)
        
        # Get target sections for this intent
        targets = self.SECTION_TARGETS.get(intent, [])
        targets_str = ", ".join(targets)
        
        prompt = self.EXPANSION_PROMPT.format(
            query=query,
            intent=intent.value,
            targets=targets_str,
            schema_program=SCHEMA_PROGRAM,
            schema_syllabus=SCHEMA_SYLLABUS
        )
        
        # Generate expansion
        try:
            if settings.use_openai and settings.openai_api_key:
                expansion = await openai_client.generate_answer(prompt)
            else:
                expansion = await ollama_client.generate_answer(prompt)
            
            expansion = expansion.strip()
            
            # Add major context if provided
            major_context = f"ngành {major}" if major else ""
            
            # Build expanded query
            if expansion:
                expanded = f"{query}, {expansion}"
                if major_context:
                    expanded = f"{expanded}, {major_context}"
            else:
                expanded = f"{query}, {major_context}" if major_context else query
            
            logger.info("Expansion result: %s", expansion)
            
            return expanded
            
        except Exception as e:
            logger.warning("Expansion failed: %s, using original query", e)
            return query
    
    def augment_roadmap_query(self, query: str) -> str:
        """
        Augment ROADMAP query with quy định ngoại ngữ keywords
        
        For ROADMAP intent, we also need to retrieve foreign language requirements
        as they are part of the learning roadmap
        """
        # Add quy định ngoại ngữ keywords
        augmentation = "quy định ngoại ngữ, chuẩn tiếng Anh, TOEIC, IELTS"
        return f"{query}, {augmentation}"
    
    async def extract_compare_entities(self, query: str) -> Tuple[str, str]:
        """
        Extract 2 entities from COMPARE query for separate retrieval
        
        Args:
            query: Original compare query
            
        Returns:
            Tuple of (entity1, entity2) or (query, query) if extraction fails
        """
        logger.info("Extracting compare entities from: %s", query)
        
        prompt = self.COMPARE_ENTITY_PROMPT.format(query=query)
        
        try:
            if settings.use_openai and settings.openai_api_key:
                response = await openai_client.generate_answer(prompt)
            else:
                response = await ollama_client.generate_answer(prompt)
            
            response = response.strip()
            
            if "NONE" in response.upper():
                logger.warning("Could not extract 2 entities, using original query")
                return (query, query)
            
            # Parse entities
            parts = [p.strip() for p in response.split(",")]
            
            if len(parts) >= 2:
                entity1, entity2 = parts[0], parts[1]
                logger.info("Extracted entities: '%s' vs '%s'", entity1, entity2)
                return (entity1, entity2)
            else:
                logger.warning("Could not parse entities: %s", response)
                return (query, query)
                
        except Exception as e:
            logger.warning("Entity extraction failed: %s", e)
            return (query, query)


class IntentBasedPromptGenerator:

    """
    Generate prompts for answer generation based on 5 Retrieval-Focused intent groups
    
    - OVERVIEW: Comprehensive summary from multiple sources
    - STRUCTURE: Full section content (assessment, outcomes, policy, cấu trúc)
    - ROADMAP: Timeline/roadmap format by semester
    - FACTUAL: Short 1-2 sentence factual answers (metadata, tiên quyết)
    - COMPARE: Comparison table with criteria
    """
    
    def generate_answer_prompt(
        self,
        query: str,
        sections: List[Dict],
        intent: QueryIntent
    ) -> str:
        """
        Generate answer prompt based on intent (5 types)
        
        Args:
            query: User query
            sections: Retrieved sections/chunks
            intent: Detected query intent (one of 5 types)
            
        Returns:
            Formatted prompt for LLM
        """
        # Map intent to prompt generator (5 intents)
        if intent == QueryIntent.OVERVIEW:
            return self._generate_overview_prompt(query, sections)
        elif intent == QueryIntent.STRUCTURE:
            return self._generate_structure_prompt(query, sections)
        elif intent == QueryIntent.ROADMAP:
            return self._generate_roadmap_prompt(query, sections)
        elif intent == QueryIntent.FACTUAL:
            return self._generate_factual_prompt(query, sections)
        elif intent == QueryIntent.COMPARE:
            return self._generate_compare_prompt(query, sections)
        else:  
            return self._generate_structure_prompt(query, sections)  # Fallback
    
    def _generate_factual_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        FACTUAL: Short 1-2 sentence answers for metadata questions
        
        Used for: mã môn, tín chỉ, giảng viên, tài liệu học tập
        Output: Direct factual answer
        """
        # Build context from sections/chunks
        context_parts = []
        for idx, item in enumerate(sections[:5]):  # Limit to 5
            text = item.get("text", item.get("content", ""))
            if text:
                context_parts.append(f"[{idx+1}]: {text}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""Bạn là trợ lý tư vấn tuyển sinh đại học.

NHIỆM VỤ: Trả lời câu hỏi FACTUAL trong 1-2 CÂU.

QUY TẮC:
- Trả lời NGẮN GỌN, TRỰC TIẾP vào câu hỏi
- Trích dẫn SỐ LIỆU CHÍNH XÁC từ context
- Nếu không có thông tin → nói "Tôi không tìm thấy thông tin này"
- KHÔNG giải thích dài dòng, KHÔNG liệt kê thêm

THÔNG TIN:
{context}

CÂU HỎI: {query}

TRẢ LỜI (1-2 câu):"""
        
        return prompt
    
    def _generate_section_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        SECTION_LEVEL: Optimized for list/overview questions
        
        Input: Sections with hierarchy
        Output: Bullet point list with structure
        """
        # Build hierarchy context
        hierarchy_parts = []
        for idx, section in enumerate(sections[:7]):  # Limit to 7 sections
            path = section.get("hierarchy_path", "N/A")
            hierarchy_parts.append(f"[{idx+1}] {path}")
        hierarchy = "\n".join(hierarchy_parts)
        
        # Build content context
        context_parts = []
        for idx, section in enumerate(sections[:7]):
            text = section.get("text", section.get("content", ""))
            title = section.get("title", "")
            if text:
                context_parts.append(f"--- Section {idx+1}: {title} ---\n{text}")
        context = "\n\n".join(context_parts)
        
        prompt = f"""Bạn là trợ lý tư vấn tuyển sinh đại học.

        NHIỆM VỤ: Trả lời câu hỏi LIỆT KÊ với danh sách có cấu trúc.

        QUY TẮC:
        - Sử dụng BULLET POINTS (•) hoặc NUMBERING (1, 2, 3...)
        - Mỗi item trên 1 dòng riêng
        - Có thể có sub-items nếu cần
        - Trích dẫn thông tin từ CONTEXT, không bịa đặt
        - Nếu không đủ thông tin → nói rõ

        CẤU TRÚC SECTIONS (để hiểu context):
        {hierarchy}

        CONTEXT:
        {context}

        CÂU HỎI: {query}

        TRẢ LỜI (dạng danh sách):"""
        
        return prompt
    
    def _generate_roadmap_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        ROADMAP: Specialized prompt for semester/curriculum questions
        
        Handles:
        - Course listings by semester
        - Placeholder courses (tự chọn, chuyên ngành)
        - Clear formatting with course codes
        """
        # Build context from sections
        context_parts = []
        has_placeholder_section = False
        semester_section = None
        placeholder_sections = []
        
        for idx, section in enumerate(sections[:5]):
            text = section.get("text", section.get("content", ""))
            title = section.get("title", "")
            path = section.get("hierarchy_path", "")
            
            # Detect if this is a semester section or placeholder section
            is_semester = "học kỳ" in path.lower() or "học kì" in path.lower()
            is_placeholder = any(kw in path.lower() for kw in [
                "tự chọn", "chuyên ngành", "cơ sở ngành", "liên ngành"
            ])
            
            if is_semester and not semester_section:
                semester_section = section
            if is_placeholder:
                has_placeholder_section = True
                placeholder_sections.append(section)
            
            if text:
                context_parts.append(f"--- Section {idx+1}: {path or title} ---\n{text}")
        
        context = "\n\n".join(context_parts)
        
        # === CASE 1: Simple semester (no placeholders) ===
        if len(sections) == 1 or not has_placeholder_section:
            prompt = f"""Bạn là trợ lý tư vấn học vụ đại học.

### NHIỆM VỤ:
Trích xuất và liệt kê TẤT CẢ các môn học trong học kỳ được hỏi.

### DỮ LIỆU ĐẦU VÀO:
{context}

### YÊU CẦU:
1. Liệt kê TẤT CẢ các môn học có trong dữ liệu (kể cả GDTC, GDQP, Anh văn)
2. KHÔNG bỏ sót môn nào
3. KHÔNG thêm môn không có trong dữ liệu
4. KHÔNG tự tính toán - chỉ trích xuất thông tin có sẵn

### ĐỊNH DẠNG:
# MÔN HỌC HỌC KỲ [SỐ] - [TÊN NGÀNH]

| Mã MH | Tên môn học | TC | LT | TH |
|-------|-------------|----|----|---|
...

CÂU HỎI: {query}

TRẢ LỜI:"""
        
        # === CASE 2: Semester with placeholders ===
        else:
            prompt = f"""Bạn là trợ lý tư vấn học vụ đại học.

            ### NHIỆM VỤ:
            Liệt kê môn học trong học kỳ được hỏi, BAO GỒM thông tin về các nhóm môn tự chọn/chuyên ngành.

            ### DỮ LIỆU ĐẦU VÀO:
            {context}

            ### QUY TẮC:
            - CHỈ trích xuất thông tin có trong dữ liệu
            - KHÔNG tự tính toán hay suy luận
            - Giữ nguyên các con số từ dữ liệu gốc

            ### CẤU TRÚC TRẢ LỜI:

            ## PHẦN 1: MÔN HỌC TRONG KẾ HOẠCH HỌC KỲ
            Liệt kê các môn có MÃ MÔN cụ thể từ section Học kỳ:
            | Mã MH | Tên môn học | TC | LT | TH |
            |-------|-------------|----|----|---|
            ...

            ## PHẦN 2: CÁC NHÓM MÔN TỰ CHỌN/CHUYÊN NGÀNH
            Với mỗi nhóm (VD: "Môn tự chọn ngành", "Các môn học chuyên ngành (**)"):
            - Tên nhóm môn
            - Yêu cầu tín chỉ (trích từ dữ liệu)
            - Danh sách môn gợi ý:
            | Mã môn | Tên môn | TC |
            |--------|---------|---|
            ...

            CÂU HỎI: {query}

            TRẢ LỜI:"""
        
        return prompt
    
    def _generate_structure_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        STRUCTURE: Full section content for structured information
        
        Used for: đánh giá, chuẩn đầu ra, quy định, policy, khối kiến thức
        Output: Full formatted content from sections
        """
        # Build context from sections (full content)
        context_parts = []
        for idx, section in enumerate(sections[:5]):  # Limit to 5 sections
            text = section.get("text", section.get("content", ""))
            title = section.get("title", "")
            path = section.get("hierarchy_path", "")
            if text:
                context_parts.append(f"--- {path or title} ---\n{text}")
        context = "\n\n".join(context_parts)
        
        prompt = f"""Bạn là trợ lý tư vấn tuyển sinh đại học.

NHIỆM VỤ: Trả lời câu hỏi dựa trên THÔNG TIN ĐẦY ĐỦ từ context.

QUY TẮC:
- Trích xuất và tổng hợp thông tin từ CONTEXT
- Sử dụng BULLET POINTS hoặc BẢNG nếu phù hợp
- Giữ nguyên các CON SỐ, TỈ LỆ, MÃ (A1, CLO, G1...)
- Dựa hoàn toàn vào CONTEXT, không bịa đặt
- Nếu là đánh giá → liệt kê thành phần và trọng số
- Nếu là chuẩn đầu ra → liệt kê CLO/PLO và mô tả
- Nếu là quy định → giải thích rõ ràng điều kiện

CONTEXT:
{context}

CÂU HỎI: {query}

TRẢ LỜI:"""
        
        return prompt
    
    def _generate_assessment_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        ASSESSMENT: Table format for evaluation weights
        
        Used for: cách tính điểm, rubric, A1-A4, trọng số
        Output: Table showing component weights
        """
        # Build context from sections
        context_parts = []
        for idx, section in enumerate(sections[:5]):
            text = section.get("text", section.get("content", ""))
            title = section.get("title", "")
            if text:
                context_parts.append(f"--- {title} ---\n{text}")
        context = "\n\n".join(context_parts)
        
        prompt = f"""Bạn là trợ lý tư vấn tuyển sinh đại học.

NHIỆM VỤ: Trả lời câu hỏi về ĐÁNH GIÁ MÔN HỌC.

QUY TẮC:
- Liệt kê các THÀNH PHẦN ĐÁNH GIÁ (A1, A2, A3, A4...)
- Hiển thị TRỌNG SỐ (%) của mỗi thành phần
- Mô tả ngắn gọn nội dung đánh giá
- Tổng điểm phải = 100%
- Dựa hoàn toàn vào CONTEXT

THÔNG TIN ĐÁNH GIÁ:
{context}

CÂU HỎI: {query}

TRẢ LỜI (format bảng/danh sách):"""
        
        return prompt
    
    def _generate_outcomes_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        OUTCOMES: Bullet list for CLO/PLO skills
        
        Used for: chuẩn đầu ra, học xong làm được gì, CLO, PLO, G1-G4
        Output: Structured skill list
        """
        context_parts = []
        for idx, section in enumerate(sections[:7]):
            text = section.get("text", section.get("content", ""))
            title = section.get("title", "")
            if text:
                context_parts.append(f"--- {title} ---\n{text}")
        context = "\n\n".join(context_parts)
        
        prompt = f"""Bạn là trợ lý tư vấn tuyển sinh đại học.

NHIỆM VỤ: Trả lời câu hỏi về CHUẨN ĐẦU RA môn học.

QUY TẮC:
- Liệt kê các CHUẨN ĐẦU RA (CLO hoặc G1, G2...)
- Mô tả KỸ NĂNG/KIẾN THỨC đạt được
- Sử dụng BULLET POINTS
- Dựa hoàn toàn vào CONTEXT

THÔNG TIN CHUẨN ĐẦU RA:
{context}

CÂU HỎI: {query}

TRẢ LỜI (danh sách kỹ năng):"""
        
        return prompt
    
    def _generate_overview_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        OVERVIEW: Comprehensive detailed answer for general questions
        
        Used for: là gì, học về cái gì, mục tiêu, tổng quan, học những gì, hình thức tốt nghiệp
        Output: Detailed structured answer with explanations
        """
        # Group sections by level
        levels = {}
        for section in sections[:15]:  # Limit to 15 sections
            level = section.get("level", 1)
            if level not in levels:
                levels[level] = []
            levels[level].append(section)
        
        # Build structured context by level - include MORE text for detail
        context_parts = []
        for level in sorted(levels.keys()):
            level_sections = levels[level]
            context_parts.append(f"\n=== CẤP {level} ===")
            for section in level_sections[:5]:  # Max 5 per level
                title = section.get("title", "Untitled")
                text = section.get("text", "")
                path = section.get("hierarchy_path", "")
                context_parts.append(f"• {title}\n  Path: {path}\n  Content: {text}")
        
        context = "\n".join(context_parts)

        
        prompt = f"""
            ### VAI TRÒ:
            Bạn là Trợ lý Tư vấn Tuyển sinh & Đào tạo Đại học chuyên nghiệp. Nhiệm vụ của bạn là cung cấp thông tin chính xác tuyệt đối từ dữ liệu được cung cấp (CONTEXT).

            ### QUY TRÌNH TƯ DUY & XỬ LÝ (BẮT BUỘC TUÂN THỦ):

            1. **BƯỚC 1: ĐỊNH VỊ NGỮ CẢNH (CONTEXT ANCHORING)**
            - Xác định ngay **Ngành học** (VD: CNTT, AI,...) hoặc **Môn học** cụ thể trong câu hỏi.
            - **QUY TẮC SỐNG CÒN:** Chỉ trích xuất thông tin từ các đoạn văn bản có tiêu đề (Header) chứa đúng tên ngành/môn đó. Bỏ qua hoàn toàn các đoạn của ngành khác dù nội dung có vẻ giống nhau (như "Khối kiến thức tốt nghiệp" của các ngành khác nhau).

            2. **BƯỚC 2: PHÂN LOẠI & ÁNH XẠ NGUỒN TIN (INTENT MAPPING)**
            *Đây là bước quan trọng để "nail" đúng câu trả lời:*
            
            - **Trường hợp A: Câu hỏi TỔNG QUAN về Ngành (VD: "Ngành này học gì?", "Cấu trúc chương trình ra sao?")**
                -> **HÀNH ĐỘNG:** Tìm đến các section: **"Các khối kiến thức"**, **"Hình Thức Đào Tạo"**, hoặc **"Mục tiêu đào tạo"**.
                -> **CÁCH TRẢ LỜI:** Tổng hợp theo cấu trúc khung chương trình (Đại cương -> Cơ sở ngành -> Chuyên ngành -> Tốt nghiệp). Không liệt kê chi tiết nội dung từng môn trừ khi được hỏi sâu.

            - **Trường hợp B: Câu hỏi CHI TIẾT về Môn học (VD: "Môn A học gì?", "Nội dung môn B?")**
                -> **HÀNH ĐỘNG:** Tìm đến các section: **"Mô tả môn học"**, **"Nội dung giảng dạy"**, hoặc **"Chuẩn đầu ra môn học"**.
                -> **CÁCH TRẢ LỜI:** Tóm tắt mục tiêu môn học và liệt kê các nội dung chính/kỹ năng đạt được.

            - **Trường hợp C: Câu hỏi DANH SÁCH/SỐ LƯỢNG (VD: "Có bao nhiêu môn...", "Liệt kê các môn...")**
                -> **HÀNH ĐỘNG:** Quét toàn bộ bảng biểu trong phân vùng ngành đã xác định.
                -> **CÁCH TRẢ LỜI:** Đếm chính xác và liệt kê đầy đủ.

            3. **BƯỚC 3: GIẢI MÃ BẢNG BIỂU PHẲNG (TABLE PARSING)**
            - Dữ liệu bảng trong Context là văn bản phẳng. Hãy nhận diện các mẫu lặp lại:
                `STT: [số]... Mã môn: [mã]... Tên môn: [tên]... TC: [số]`
            - Khi trích xuất, luôn trình bày theo định dạng: **Tên môn học** (Mã: [Mã] - [Số] TC).

            ### ĐỊNH DẠNG CÂU TRẢ LỜI:
            - **Cấu trúc:** Rõ ràng, phân cấp (dùng Heading, Bullet points).
            - **Độ chính xác:** Nếu Context không có thông tin cho đúng ngành/môn đó, hãy trả lời: "Tài liệu không chứa thông tin chi tiết về vấn đề này cho [Tên ngành/môn]". KHÔNG suy diễn từ ngành khác.
            - **Văn phong:** Chuyên nghiệp, khách quan, đi thẳng vào trọng tâm.

            ----------------
            ### THÔNG TIN THAM KHẢO (CONTEXT):
            {context}

            ### CÂU HỎI CỦA SINH VIÊN:
            "{query}"

            ### TRẢ LỜI CHI TIẾT:
            """
        logger.info(prompt)

        
        return prompt
    
    def _generate_compare_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        COMPARE: Table-based comparison between two courses/programs
        
        Used for: so sánh, khác nhau, giống nhau, nên chọn
        Output: Comparison table with criteria
        """
        # Build context from sections (may contain info about both entities)
        context_parts = []
        for section in sections[:10]:  # Use more sections for comparison
            text = section.get("text", section.get("content", ""))
            title = section.get("title", "")
            hierarchy = section.get("hierarchy_path", "")
            if text:
                context_parts.append(f"--- {hierarchy or title} ---\n{text[:500]}")
        context = "\n\n".join(context_parts)
        
        prompt = f"""Bạn là trợ lý tư vấn tuyển sinh đại học.

NHIỆM VỤ: SO SÁNH hai môn học hoặc ngành học.

QUY TẮC:
- Trình bày dạng BẢNG SO SÁNH với các tiêu chí rõ ràng
- Các tiêu chí so sánh: Mục tiêu, Số tín chỉ, Nội dung chính, Cơ hội việc làm, v.v.
- Nêu rõ ĐIỂM GIỐNG và ĐIỂM KHÁC
- Kết luận ngắn gọn về đối tượng phù hợp với từng lựa chọn
- Dựa hoàn toàn vào CONTEXT, không bịa đặt

THÔNG TIN:
{context}

CÂU HỎI: {query}

TRẢ LỜI (bảng so sánh):"""
        
        return prompt
    
    def _generate_policy_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        POLICY: Regulation/scholarship explanation
        
        Used for: quy định, học bổng, ngoại ngữ, quy chế, TOEIC, IELTS
        Output: Clear policy explanation with conditions
        """
        # Build context from sections
        context_parts = []
        for idx, section in enumerate(sections[:7]):
            text = section.get("text", section.get("content", ""))
            title = section.get("title", "")
            hierarchy = section.get("hierarchy_path", "")
            if text:
                context_parts.append(f"--- {hierarchy or title} ---\n{text}")
        context = "\n\n".join(context_parts)
        
        prompt = f"""Bạn là trợ lý tư vấn tuyển sinh đại học.

NHIỆM VỤ: Trả lời câu hỏi về QUY ĐỊNH, QUY CHẾ, HỌC BỔNG hoặc YÊU CẦU NGOẠI NGỮ.

QUY TẮC:
- Trình bày RÕ RÀNG các điều kiện, yêu cầu
- Nếu là học bổng: nêu MỨC HỌC BỔNG và ĐIỀU KIỆN
- Nếu là ngoại ngữ: nêu ĐIỂM CHUẨN (TOEIC, IELTS) và các trường hợp MIỄN
- Sử dụng BULLET POINTS cho dễ đọc
- Dựa hoàn toàn vào CONTEXT, không bịa đặt

THÔNG TIN QUY ĐỊNH:
{context}

CÂU HỎI: {query}

TRẢ LỜI (giải thích quy định):"""
        
        return prompt
    
    def _generate_suggestion_prompt(self, query: str, sections: List[Dict]) -> str:
        """
        SUGGESTION: Personalized learning path recommendations
        
        Used for: muốn làm X cần học gì, nên chọn môn nào, định hướng nghề nghiệp
        Output: Personalized recommendations with reasoning
        """
        # Build context from sections (career paths and course info)
        context_parts = []
        for section in sections[:10]:  # Use more sections for comprehensive advice
            text = section.get("text", section.get("content", ""))
            title = section.get("title", "")
            hierarchy = section.get("hierarchy_path", "")
            if text:
                context_parts.append(f"--- {hierarchy or title} ---\n{text[:500]}")
        context = "\n\n".join(context_parts)
        
        prompt = f"""Bạn là trợ lý tư vấn học tập và định hướng nghề nghiệp đại học.

NHIỆM VỤ: GỢI Ý môn học và lộ trình phù hợp với định hướng nghề nghiệp của sinh viên.

QUY TẮC:
- Hiểu rõ mục tiêu nghề nghiệp của sinh viên từ câu hỏi
- Gợi ý CỤ THỂ các môn học nên chọn và lý do
- Đề xuất lộ trình học tập hợp lý (môn nào học trước, môn nào học sau)
- Liên kết giữa môn học và kỹ năng cần thiết cho nghề nghiệp
- Dựa hoàn toàn vào CONTEXT, không bịa đặt tên môn

THÔNG TIN CHƯƠNG TRÌNH:
{context}

CÂU HỎI: {query}

TRẢ LỜI (gợi ý cá nhân hóa):"""
        
        return prompt

