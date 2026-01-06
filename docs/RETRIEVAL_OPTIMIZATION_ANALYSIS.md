# Phân Tích Hệ Thống và Kế Hoạch Tối Ưu Retrieval Engine

## 1. DEEP DIVE: 2 LOẠI SCHEMA DATA

### 1.1. Schema Program (Chương trình đào tạo - VD: CNTT.json)

#### **Cấu trúc phân cấp (Hierarchical Structure)**

```
Level 1: Ngành (Major)
    └─ Level 2: Các phần chính (Main Sections)
        ├─ Mục tiêu đào tạo
        ├─ Vị trí và khả năng làm việc sau tốt nghiệp
        ├─ Quan điểm xây dựng chương trình đào tạo
        ├─ Hình thức và thời gian đào tạo
        ├─ Điều kiện tốt nghiệp
        ├─ Chuẩn đầu ra (PLO1-PLO8)
        └─ Các khối kiến thức ⭐
            ├─ Level 3: Khối kiến thức giáo dục đại cương
            │   └─ Level 4: Nhóm môn (Lý luận chính trị, Toán-Tin học, Ngoại ngữ...)
            │       └─ Chunks: Danh sách môn học chi tiết
            ├─ Level 3: Khối kiến thức giáo dục chuyên nghiệp ⭐⭐
            │   ├─ Level 4: Nhóm các môn học cơ sở ngành ⭐⭐⭐
            │   │   └─ Chunks: Danh sách môn học cơ sở (IT001, IT002...)
            │   └─ Level 4: Nhóm các môn học chuyên ngành
            │       └─ Chunks: Danh sách môn học chuyên ngành
            └─ Level 3: Khối kiến thức tốt nghiệp
        └─ Kế hoạch giảng dạy mẫu
            ├─ Level 3: Học kì 1
            ├─ Level 3: Học kì 2
            ├─ ...
            └─ Level 3: Học kì 8
```

#### **Đặc điểm quan trọng:**

1. **Sections (19-26 sections)**: Các phần lớn, mang thông tin khái niệm, tổng quan
   - Ví dụ: "Mục tiêu đào tạo", "Điều kiện tốt nghiệp", "Chuẩn đầu ra"
2. **Chunks (50-71 chunks)**: Các phần nhỏ, mang thông tin chi tiết cụ thể

   - Ví dụ: Danh sách môn học trong từng học kỳ, bảng điểm, danh sách môn cơ sở ngành

3. **Mối quan hệ Section-Chunk**:

   - 1 Section có thể có nhiều chunks
   - Chunks được "chunked" từ sections lớn để dễ retrieval
   - `section_id` trong chunk trỏ đến section cha

4. **Hierarchy Path**:
   ```
   "Ngành Công Nghệ Thông Tin > Các khối kiến thức > Khối kiến thức giáo dục chuyên nghiệp > Nhóm các môn học cơ sở ngành"
   ```

---

### 1.2. Schema Syllabus (Đề cương môn học - VD: EC213.json)

#### **Cấu trúc phân cấp**

```
Level 1: Mã môn -- Tên môn học (VD: EC213 -- QUẢN TRỊ QUAN HỆ...)
    ├─ Level 2: THÔNG TIN CHUNG (General information)
    │   └─ Chunks: Bảng thông tin (số tín chỉ, giảng viên, môn tiên quyết...)
    ├─ Level 2: MÔ TẢ MÔN HỌC (Course description)
    │   └─ Chunks: Mô tả tổng quan nội dung môn học
    ├─ Level 2: MỤC TIÊU MÔN HỌC (Course goals)
    │   └─ Chunks: Các mục tiêu cần đạt được
    ├─ Level 2: CHUẨN ĐẦU RA MÔN HỌC (Course learning outcomes)
    │   └─ Chunks: CLO1, CLO2, CLO3... (chi tiết từng chuẩn)
    ├─ Level 2: NỘI DUNG MÔN HỌC, KẾ HOẠCH GIẢNG DẠY ⭐⭐⭐
    │   ├─ Level 3: Tuần 1 - Chương 1...
    │   ├─ Level 3: Tuần 2 - Chương 2...
    │   └─ ...
    │       └─ Chunks: Nội dung từng tuần chi tiết
    └─ Level 2: TÀI LIỆU THAM KHẢO
        └─ Chunks: Danh sách sách, giáo trình, papers
```

#### **Đặc điểm quan trọng:**

1. **Sections (15-19 sections)**: Các phần chính của đề cương

   - Mỗi section tương ứng 1 phần trong cấu trúc chuẩn

2. **Chunks (40-51 chunks)**: Nội dung chi tiết

   - Chia nhỏ từ sections dài (VD: Kế hoạch giảng dạy)
   - Bảng thông tin (tables)

3. **Tables**: Được index trong `searchable_text`
   - Bảng thông tin chung (tín chỉ, giảng viên)
   - Bảng rubric đánh giá
   - Bảng kế hoạch giảng dạy

---

## 2. VÍ DỤ MINH HOẠ: INTENT-BASED RETRIEVAL

### 2.1. CHUNK-LEVEL (Câu hỏi về thông tin đơn giản, cụ thể)

#### Ví dụ 1: "Môn EC213 học bao nhiêu tín chỉ?"

```
✅ CHUNK LEVEL ĐỦ

Intent: DETAIL_FACT
Query expansion: "EC213, số tín chỉ, thông tin chung, lý thuyết, thực hành"

Retrieved chunks:
- Chunk từ section "THÔNG TIN CHUNG"
  Text: "...Số tín chỉ: | Lý thuyết: 2 | Thực hành: 1..."

Answer: "Môn EC213 có 3 tín chỉ (2 lý thuyết + 1 thực hành)"
```

#### Ví dụ 2: "Điều kiện tốt nghiệp ngành CNTT là gì?"

```
✅ CHUNK LEVEL ĐỦ

Intent: DETAIL_FACT
Query expansion: "điều kiện tốt nghiệp, tín chỉ, yêu cầu"

Retrieved chunks:
- Chunk từ section "Điều kiện tốt nghiệp"
  Text: "Sinh viên đã tích lũy tối thiểu 125 tín chỉ (bao gồm 12 tín chỉ Anh văn)..."

Answer: "Điều kiện tốt nghiệp: tối thiểu 125 tín chỉ (bao gồm 12 tín chỉ Anh văn)..."
```

#### Ví dụ 3: "Học kỳ 3 học những môn gì?"

```
✅ CHUNK LEVEL ĐỦ

Intent: DETAIL_LIST
Query expansion: "học kỳ 3, kế hoạch giảng dạy, môn học"

Retrieved chunks:
- Chunk từ section "Học kì 3"
  Text: "...IT002 - Lập trình hướng đối tượng (4TC)
        IT003 - Cấu trúc dữ liệu và giải thuật (4TC)..."

Answer: "Học kỳ 3 có các môn: IT002, IT003, IT004..."
```

---

### 2.2. SECTION-LEVEL (Câu hỏi cần ngữ cảnh rộng hơn)

#### Ví dụ 4: "Môn EC213 học những gì?"

```
❌ CHUNK LEVEL KHÔNG ĐỦ
✅ SECTION LEVEL CẦN THIẾT

Intent: COURSE_CONTENT_OVERVIEW
Query expansion: "EC213, nội dung môn học, kế hoạch giảng dạy, mô tả, mục tiêu"

Tại sao cần SECTION?
- Cần "MÔ TẢ MÔN HỌC" → overview tổng quan
- Cần "NỘI DUNG MÔN HỌC" → các chương/tuần học
- Cần "MỤC TIÊU" → học để làm gì

Retrieved sections:
1. Section "MÔ TẢ MÔN HỌC"
   - "Cung cấp kiến thức về cách thức kết nối với khách hàng và nhà cung cấp..."

2. Section "NỘI DUNG MÔN HỌC, KẾ HOẠCH GIẢNG DẠY"
   - Tuần 1: Tổng quan về CRM
   - Tuần 2: Mối quan hệ khách hàng
   - Tuần 3-7: Thu hút, giữ chân, phát triển khách hàng...

Answer: "Môn EC213 học về CRM & SRM, bao gồm:
- Tổng quan về quản trị quan hệ khách hàng
- Kỹ thuật thu hút và giữ chân khách hàng
- Cơ sở dữ liệu khách hàng
- Quản trị nhà cung cấp..."
```

#### Ví dụ 5: "Cơ sở ngành của CNTT học những gì?"

```
❌ CHUNK LEVEL KHÔNG ĐỦ
✅ SECTION LEVEL CẦN THIẾT

Intent: KNOWLEDGE_BLOCK_CONTENT
Query expansion: "cơ sở ngành, nhóm môn học cơ sở ngành, khối kiến thức chuyên nghiệp"

Tại sao cần SECTION?
- Cần section "Nhóm các môn học cơ sở ngành" → full context
- Có thể cần section cha "Khối kiến thức giáo dục chuyên nghiệp" → định nghĩa
- Cần cả bảng danh sách môn học + mô tả

Retrieved sections:
1. Section "Các khối kiến thức" (parent)
   - Giới thiệu cấu trúc: Đại cương 45TC, Chuyên nghiệp 70TC, Tốt nghiệp 10TC

2. Section "Khối kiến thức giáo dục chuyên nghiệp" (parent)
   - Cơ sở ngành: 44TC
   - Chuyên ngành: ≥26TC

3. Section "Nhóm các môn học cơ sở ngành" ⭐⭐⭐
   - IT001: Nhập môn lập trình (4TC, 3LT, 1TH)
   - IT002: Lập trình hướng đối tượng (4TC, 3LT, 1TH)
   - IT003: Cấu trúc dữ liệu và giải thuật (4TC, 3LT, 1TH)
   - IT004: Cơ sở dữ liệu (4TC, 3LT, 1TH)
   - ... (full list)

Answer: "Cơ sở ngành CNTT gồm 44 tín chỉ, bao gồm các môn:
- Lập trình: IT001, IT002, IT006
- Cơ sở dữ liệu: IT004
- Cấu trúc dữ liệu: IT003
- Mạng máy tính: IT007
- ..."
```

#### Ví dụ 6: "Ngành Công Nghệ Thông Tin học những gì?"

```
❌ CHUNK LEVEL HOÀN TOÀN KHÔNG ĐỦ
✅ SECTION LEVEL - MULTIPLE PARENTS CẦN THIẾT

Intent: MAJOR_OVERVIEW
Query expansion: "ngành công nghệ thông tin, các khối kiến thức, chương trình đào tạo, cơ sở ngành, chuyên ngành"

Tại sao cần MULTIPLE SECTIONS với HIERARCHY?
- Cần "Các khối kiến thức" → entry point, big picture
- Cần expand đến các khối con:
  ├─ "Khối kiến thức giáo dục đại cương"
  ├─ "Khối kiến thức giáo dục chuyên nghiệp" ⭐
  │   ├─ "Nhóm các môn học cơ sở ngành" ⭐⭐
  │   └─ "Nhóm các môn học chuyên ngành" ⭐⭐
  └─ "Khối kiến thức tốt nghiệp"

Strategy: HIERARCHICAL EXPANSION
1. Tìm section gốc: "Các khối kiến thức"
2. Expand xuống children:
   - Lấy tất cả sections có hierarchy_path bắt đầu bằng "Ngành Công Nghệ Thông Tin > Các khối kiến thức"
3. Prioritize level 3 & 4 sections (chi tiết hơn)

Retrieved sections (theo hierarchy):
1. "Các khối kiến thức" (level 2) - OVERVIEW
   └─ "3 khối: Đại cương 45TC, Chuyên nghiệp 70TC, Tốt nghiệp 10TC"

2. "Khối kiến thức giáo dục đại cương" (level 3)
   └─ "Lý luận chính trị 13TC, Toán-Tin 18TC, Ngoại ngữ 12TC..."

3. "Khối kiến thức giáo dục chuyên nghiệp" (level 3)
   ├─ "Nhóm các môn học cơ sở ngành" (level 4)
   │   └─ Danh sách đầy đủ: IT001, IT002, IT003...
   └─ "Nhóm các môn học chuyên ngành" (level 4)
       └─ Danh sách môn chuyên ngành: IS207, IS402...

4. "Khối kiến thức tốt nghiệp" (level 3)
   └─ "Khóa luận hoặc Đồ án tốt nghiệp..."

Answer: "Ngành CNTT học 3 khối kiến thức chính:

1. **Đại cương (45TC)**: Lý luận chính trị, Toán, Tin học, Ngoại ngữ
2. **Chuyên nghiệp (70TC)**:
   - Cơ sở ngành (44TC): Lập trình, Cấu trúc dữ liệu, Cơ sở dữ liệu, Mạng...
   - Chuyên ngành (≥26TC): Hệ thống thông tin, Web, Mobile, AI...
3. **Tốt nghiệp (10TC)**: Khóa luận hoặc Đồ án"
```

---

### 2.3. HYBRID-LEVEL (Cần cả chunks và sections)

#### Ví dụ 7: "IT004 là môn gì và học ở học kỳ nào?"

```
✅ HYBRID: CHUNK + SECTION

Intent: COURSE_INFO_AND_PLAN
Query expansion: "IT004, tên môn, số tín chỉ, kế hoạch giảng dạy, học kỳ"

Cần 2 loại thông tin:
1. CHUNK: "IT004 là môn gì?" → tên môn, số TC
2. SECTION: "Học kỳ nào?" → cần xem kế hoạch giảng dạy

Retrieved:
- Chunk từ "Nhóm môn học cơ sở ngành"
  "IT004: Cơ sở dữ liệu (4TC, 3LT, 1TH)"

- Section "Học kì 3"
  "...IT004 - Cơ sở dữ liệu..."

Answer: "IT004 là môn Cơ sở dữ liệu (4TC), học ở học kỳ 3"
```

---

## 3. PHÂN TÍCH: KHI NÀO DÙNG CHUNK vs SECTION?

### 3.1. Bảng quyết định

| **Query Intent**    | **Level**       | **Lý do**                            | **Ví dụ**                 |
| ------------------- | --------------- | ------------------------------------ | ------------------------- |
| **SIMPLE_FACT**     | Chunk           | Thông tin đơn giản, 1 giá trị cụ thể | "Môn X học bao nhiêu TC?" |
| **DETAIL_LIST**     | Chunk           | Danh sách ngắn trong 1 context       | "Học kỳ 3 học gì?"        |
| **COURSE_CONTENT**  | Section         | Cần tổng quan + chi tiết môn học     | "Môn EC213 học những gì?" |
| **KNOWLEDGE_BLOCK** | Section         | Cần nhóm môn học + mô tả             | "Cơ sở ngành học gì?"     |
| **MAJOR_OVERVIEW**  | Section (Multi) | Cần big picture + hierarchy          | "Ngành CNTT học gì?"      |
| **CONDITION**       | Chunk           | Điều kiện cụ thể                     | "Điều kiện tốt nghiệp?"   |
| **HYBRID**          | Both            | Cần kết hợp 2 loại thông tin         | "IT004 học kỳ nào?"       |

### 3.2. Quy tắc phân loại Intent

#### **CHUNK-LEVEL Indicators:**

- Từ khóa: "bao nhiêu", "mấy", "là gì", "khi nào"
- Hỏi về 1 giá trị: tín chỉ, thời gian, điều kiện
- Hỏi về danh sách trong 1 ngữ cảnh nhỏ

#### **SECTION-LEVEL Indicators:**

- Từ khóa: "những gì", "bao gồm", "gồm có", "nội dung"
- Hỏi về nhóm/khối kiến thức: "cơ sở ngành", "chuyên ngành"
- Hỏi về tổng quan: "ngành X học gì", "môn Y về gì"
- Câu hỏi mở, cần giải thích chi tiết

#### **HIERARCHICAL EXPANSION Indicators:**

- Hỏi về ngành/chương trình: "Ngành CNTT..."
- Từ khóa hierarchy: "các khối kiến thức", "chương trình đào tạo"
- Cần trả về cấu trúc phân cấp

---

## 4. KẾ HOẠCH TỐI ỨU RETRIEVAL ENGINE

### 4.1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RETRIEVAL ENGINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [PREPROCESS]                                                │
│  ├─ Query Analysis & Intent Detection ⭐ NEW                │
│  │  ├─ Classify: CHUNK_LEVEL vs SECTION_LEVEL               │
│  │  └─ Detect hierarchy needs                               │
│  ├─ Schema-aware Query Expansion                            │
│  │  ├─ Program schema context                               │
│  │  └─ Syllabus schema context                              │
│  └─ Generate embeddings                                      │
│                                                               │
│  [CORE RETRIEVAL] ⭐ OPTIMIZE                                │
│  ├─ Smart Retrieval Strategy                                │
│  │  ├─ If CHUNK_LEVEL → retrieve chunks only                │
│  │  ├─ If SECTION_LEVEL → retrieve sections directly        │
│  │  └─ If HIERARCHICAL → retrieve + expand hierarchy        │
│  ├─ Elasticsearch Query                                      │
│  │  ├─ Query chunks index OR sections index                 │
│  │  └─ Apply major filter                                   │
│  └─ Hierarchy Expansion (if needed)                         │
│     ├─ Get parent sections                                   │
│     └─ Get child sections                                    │
│                                                               │
│  [POSTPROCESS]                                               │
│  ├─ Rerank with Cohere (optional)                           │
│  ├─ Deduplicate sections                                    │
│  └─ Sort by relevance score                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2. Preprocess: Intent Detection & Query Expansion

#### **4.2.1. Intent Classifier Prompt (NEW)**

```python
INTENT_DETECTION_PROMPT = """
Phân tích câu hỏi và xác định intent để tối ưu retrieval.

QUERY: {query}

INTENT TYPES:

1. **CHUNK_LEVEL**: Câu hỏi đơn giản về thông tin cụ thể
   - Indicators: "bao nhiêu tín chỉ", "mấy TC", "khi nào", "học kỳ nào"
   - Examples:
     * "EC213 học bao nhiêu tín chỉ?"
     * "Điều kiện tốt nghiệp là gì?"
     * "Học kỳ 3 học những môn gì?"

2. **SECTION_LEVEL**: Câu hỏi cần overview/context rộng
   - Indicators: "học những gì", "nội dung", "bao gồm"
   - Examples:
     * "Môn EC213 học những gì?"
     * "Cơ sở ngành CNTT gồm những môn nào?"

3. **HIERARCHICAL**: Câu hỏi cần cấu trúc phân cấp
   - Indicators: hỏi về ngành, chương trình đào tạo, khối kiến thức
   - Examples:
     * "Ngành CNTT học những gì?"
     * "Chương trình đào tạo TTNT gồm những gì?"

PHÂN TÍCH:
- Intent: [CHUNK_LEVEL | SECTION_LEVEL | HIERARCHICAL]
- Reasoning: [Giải thích ngắn gọn]
- Expansion keywords: [từ khóa để expand query]

Chỉ trả về JSON:
{
  "intent": "...",
  "reasoning": "...",
  "expansion_keywords": ["...", "..."]
}
"""
```

#### **4.2.2. Schema-aware Expansion (ENHANCED)**

```python
async def expand_query_with_intent(
    query: str,
    intent: str,  # NEW: based on detected intent
    major: Optional[str] = None
) -> str:
    """
    Expand query based on detected intent and schema
    """

    if intent == "CHUNK_LEVEL":
        # Minimal expansion, focus on specific keywords
        expansion = await llm_generate(
            f"Extract specific keywords for: {query}"
        )

    elif intent == "SECTION_LEVEL":
        # Expand with section-level schema terms
        expansion = await llm_generate(
            f"""Query: {query}
            Schema context: {SCHEMA_PROGRAM + SCHEMA_SYLLABUS}
            Generate section-level keywords to find overview content.
            """
        )

    elif intent == "HIERARCHICAL":
        # Expand with hierarchy keywords
        expansion = await llm_generate(
            f"""Query: {query}
            Detect hierarchy keywords: khối kiến thức, chương trình, ngành
            Generate keywords for hierarchical search.
            """
        )

    return f"{query}, {expansion}"
```

### 4.3. Core Retrieval: Smart Strategy (NEW)

```python
async def core_retrieval_smart(
    self,
    query: str,
    query_embedding: List[float],
    intent: str,  # NEW
    major: Optional[str],
    top_k: int = 10
) -> List[Dict]:
    """
    Smart retrieval based on detected intent

    CHUNK_LEVEL → retrieve chunks only
    SECTION_LEVEL → retrieve sections directly
    HIERARCHICAL → retrieve + expand hierarchy
    """

    if intent == "CHUNK_LEVEL":
        # Strategy 1: Chunks only
        logger.info("CHUNK_LEVEL: Retrieving chunks only")

        chunks = await es_client.search_chunks(
            query_embedding=query_embedding,
            major=major,
            top_k=top_k
        )

        # Extract sections from chunks
        section_ids = [chunk["section_id"] for chunk in chunks]
        sections = await es_client.get_sections_by_ids(section_ids)

        return sections

    elif intent == "SECTION_LEVEL":
        # Strategy 2: Search sections directly
        logger.info("SECTION_LEVEL: Searching sections directly")

        sections = await es_client.search_sections(
            query_embedding=query_embedding,
            major=major,
            top_k=top_k
        )

        return sections

    elif intent == "HIERARCHICAL":
        # Strategy 3: Hierarchical expansion
        logger.info("HIERARCHICAL: Expanding hierarchy")

        # Step 1: Find entry-point sections
        sections = await es_client.search_sections(
            query_embedding=query_embedding,
            major=major,
            top_k=5  # Fewer entry points
        )

        # Step 2: Expand hierarchy
        expanded_sections = []
        for section in sections:
            # Get children
            children = await es_client.get_child_sections(
                parent_id=section["section_id"]
            )
            expanded_sections.extend(children)

            # Get parent if needed
            if section["parent_section_id"]:
                parent = await es_client.get_section_by_id(
                    section["parent_section_id"]
                )
                expanded_sections.append(parent)

        # Combine and deduplicate
        all_sections = sections + expanded_sections
        unique_sections = deduplicate_by_id(all_sections)

        return unique_sections
```

### 4.4. Elasticsearch: Add Section Search (NEW)

```python
# In app/clients/elasticsearch.py

async def search_sections(
    self,
    query_embedding: List[float],
    major: Optional[str] = None,
    top_k: int = 10
) -> List[Dict]:
    """
    Search sections index directly using vector similarity
    """

    query = {
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": top_k * 3
        }
    }

    if major:
        query["knn"]["filter"] = {"term": {"major": major}}

    response = await self.es.search(
        index=self.sections_index,
        body=query,
        size=top_k
    )

    results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        source["score"] = hit["_score"]
        results.append(source)

    return results


async def get_child_sections(
    self,
    parent_id: str
) -> List[Dict]:
    """
    Get all child sections of a parent section
    """

    query = {
        "query": {
            "term": {"parent_section_id": parent_id}
        }
    }

    response = await self.es.search(
        index=self.sections_index,
        body=query,
        size=100  # Assume max 100 children
    )

    return [hit["_source"] for hit in response["hits"]["hits"]]


async def get_sections_by_hierarchy_prefix(
    self,
    hierarchy_prefix: str
) -> List[Dict]:
    """
    Get all sections with hierarchy path starting with prefix

    Example:
      hierarchy_prefix = "Ngành Công Nghệ Thông Tin > Các khối kiến thức"
      → returns all sections under "Các khối kiến thức"
    """

    query = {
        "query": {
            "prefix": {
                "hierarchy_path.keyword": hierarchy_prefix
            }
        }
    }

    response = await self.es.search(
        index=self.sections_index,
        body=query,
        size=50
    )

    return [hit["_source"] for hit in response["hits"]["hits"]]
```

### 4.5. Updated Retrieval Engine Flow

```python
async def run(
    self,
    query: str,
    major: Optional[str] = None,
    top_k: int = 10,
    enable_reranking: bool = None,
    enable_query_expansion: bool = None
) -> List[Dict]:
    """
    Execute smart retrieval pipeline with intent detection
    """

    # ===== PREPROCESS =====
    # Step 1: Detect intent
    intent_result = await self.detect_intent(query)
    intent = intent_result["intent"]
    reasoning = intent_result["reasoning"]

    logger.info(f"Detected intent: {intent} - {reasoning}")

    # Step 2: Expand query based on intent
    expanded_query = await expand_query_with_intent(
        query=query,
        intent=intent,
        major=major
    )

    # Step 3: Generate embedding
    query_embedding = await ollama_client.generate_embedding(expanded_query)

    # ===== CORE RETRIEVAL =====
    sections = await self.core_retrieval_smart(
        query=query,
        query_embedding=query_embedding,
        intent=intent,
        major=major,
        top_k=top_k
    )

    if not sections:
        return []

    # ===== POSTPROCESS =====
    sections = await self.postprocess(
        sections=sections,
        query=query,
        enable_reranking=enable_reranking
    )

    return sections
```

---

## 5. IMPLEMENTATION ROADMAP

### Phase 1: Intent Detection (Week 1)

- [ ] Implement `detect_intent()` với LLM prompt
- [ ] Test với dataset câu hỏi mẫu
- [ ] Tune prompt để accuracy > 90%

### Phase 2: Schema-aware Expansion (Week 1-2)

- [ ] Enhance `expand_query_with_intent()`
- [ ] Thêm logic expansion khác nhau cho từng intent
- [ ] A/B test so với baseline

### Phase 3: Core Retrieval Strategy (Week 2)

- [ ] Implement `search_sections()` trong Elasticsearch client
- [ ] Implement `get_child_sections()` và `get_sections_by_hierarchy_prefix()`
- [ ] Implement `core_retrieval_smart()` với 3 strategies

### Phase 4: Hierarchy Expansion (Week 2-3)

- [ ] Logic expand parent/children sections
- [ ] Deduplication và ranking
- [ ] Test với câu hỏi hierarchical

### Phase 5: Testing & Evaluation (Week 3-4)

- [ ] Tạo test dataset (50-100 câu hỏi)
- [ ] Đánh giá metrics:
  - Precision@K
  - Recall@K
  - MRR (Mean Reciprocal Rank)
- [ ] So sánh với baseline (current system)

### Phase 6: Production Optimization (Week 4)

- [ ] Caching cho intent detection
- [ ] Optimize Elasticsearch queries
- [ ] Monitor performance & latency

---

## 6. EXPECTED IMPROVEMENTS

### 6.1. Accuracy

- **Baseline**: 65-70% relevant results in top 5
- **Target**: 85-90% relevant results in top 5

### 6.2. Latency

- **Intent detection**: +100-200ms
- **Smart retrieval**: -50ms (skip chunk→section conversion)
- **Net impact**: ~+100ms acceptable for better quality

### 6.3. User Experience

- Câu hỏi overview → full context sections
- Câu hỏi đơn giản → fast, precise chunks
- Câu hỏi hierarchy → structured, comprehensive answer

---

## 7. VÍ DỤ KẾT QUẢ MONG ĐỢI

### Before (Current):

```
Query: "Ngành CNTT học những gì?"

Retrieved (chunks từ nhiều sections lẻ tẻ):
1. Chunk: "IT001 - Nhập môn lập trình (4TC)"
2. Chunk: "Điều kiện tốt nghiệp: 125TC"
3. Chunk: "SS007 - Triết học Mác-Lênin"
...

→ Không có big picture, chỉ có thông tin lẻ tẻ
```

### After (Optimized):

```
Query: "Ngành CNTT học những gì?"

Intent: HIERARCHICAL
Expansion: "các khối kiến thức, chương trình đào tạo, đại cương, chuyên nghiệp, tốt nghiệp"

Retrieved (hierarchical sections):
1. Section "Các khối kiến thức" (level 2)
   → Overview: 3 khối chính

2. Section "Khối kiến thức giáo dục đại cương" (level 3)
   → 45TC: Chính trị, Toán, Ngoại ngữ

3. Section "Khối kiến thức giáo dục chuyên nghiệp" (level 3)
   ├─ Section "Nhóm môn học cơ sở ngành" (level 4)
   │  → Full list: IT001, IT002, IT003...
   └─ Section "Nhóm môn học chuyên ngành" (level 4)
      → Full list: IS207, IS402...

4. Section "Khối kiến thức tốt nghiệp" (level 3)
   → Khóa luận/Đồ án

→ Có cấu trúc phân cấp rõ ràng, đầy đủ thông tin
```

---

## CONCLUSION

Hệ thống hiện tại: **Always chunks → extract sections**
Hệ thống tối ưu: **Intent-based → smart strategy**

Key innovations:

1. ✅ Intent detection để chọn strategy
2. ✅ Search sections directly khi cần
3. ✅ Hierarchical expansion cho câu hỏi overview
4. ✅ Schema-aware expansion theo intent

Expected outcome: **+20-25% accuracy** với acceptable latency overhead.
