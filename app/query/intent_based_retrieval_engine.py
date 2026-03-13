"""
Intent-Based Retrieval Engine (Simplified)
Optimized retrieval with smart strategy based on query intent detection
"""
import logging
import re
import json
from typing import Optional, List, Dict, Tuple
from enum import Enum

from app.clients.elasticsearch import es_client, SearchMode
from app.clients.ollama import ollama_client
from app.clients.cohere_reranker import cohere_reranker
from app.query.intent_based_prompt_engine import (
    SchemaAwareExpander,
    PLACEHOLDER_PATTERNS
)
from app.retrieval_engine.intent_detection import detect_intent, QueryIntent
from app.retrieval_engine.refine_query import refine_query
from app.core.config import settings

logger = logging.getLogger(__name__)



class IntentBasedRetrievalEngine:
    """
    Simplified Intent-Based Retrieval Engine
    
    Flow:
        PREPROCESS: Detect intent + Refine query (no expansion)
        CORE: Smart retrieval based on intent
        POSTPROCESS: Rerank → Deduplicate
    """
    
    def __init__(self):
        self.query_expander = SchemaAwareExpander()
        self._search_mode = None  # Will use config default if None
    
    def _get_search_mode(self) -> SearchMode:
        """Get current search mode, defaulting to config setting"""
        if self._search_mode is None:
            return SearchMode(settings.search_mode)
        return self._search_mode
    
    async def _search_chunks(
        self,
        query: str,
        query_embedding: List[float],
        major: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Internal wrapper for chunk search using current search mode
        """
        return await es_client.search_chunks_unified(
            query=query,
            query_embedding=query_embedding,
            major=major,
            top_k=top_k,
            search_mode=self._get_search_mode()
        )
    
    # ==================== PREPROCESS ====================
    
    async def preprocess(
        self,
        query: str,
        major: Optional[str] = None,
    ) -> Tuple[QueryIntent, str]:
        """
        PREPROCESS: Detect intent and refine query (no expansion)
        
        Returns:
            Tuple of (detected_intent, refined_query)
        """
        logger.info("=" * 60)
        logger.info("PREPROCESS: Intent Detection & Query Refinement")
        logger.info("=" * 60)
        
        # Step 1: Refine query (normalize + expand abbreviations)
        refined_query = await refine_query(query, use_llm=False)
        logger.info("Refined: '%s' → '%s'", query, refined_query)
        
        # Step 2: Detect intent
        intent = await detect_intent(refined_query)
        logger.info("Intent: %s", intent.value)
        
        return intent, refined_query
    
    # ==================== CORE RETRIEVAL ====================
    
    async def core_retrieval(
        self,
        query: str,
        refined_query: str,
        query_embedding: List[float],
        intent: QueryIntent,
        major: Optional[str] = None,
    ) -> List[Dict]:
        """
        CORE: Smart retrieval strategy selection based on intent
        """
        logger.info("=" * 60)
        logger.info("CORE RETRIEVAL: Intent=%s", intent.value)
        logger.info("=" * 60)
        
        if intent == QueryIntent.OVERVIEW:
            return await self._retrieve_overview(query, refined_query, query_embedding, major)
        
        elif intent == QueryIntent.STRUCTURE:
            return await self._retrieve_structure(query_embedding, refined_query, major)
        
        elif intent == QueryIntent.COMPARE:
            return await self._retrieve_compare(query, query_embedding, major)
        
        elif intent == QueryIntent.FACTUAL:
            return await self._retrieve_factual(query_embedding, refined_query, major)
        
        elif intent == QueryIntent.ROADMAP:
            return await self._retrieve_roadmap(refined_query, query_embedding, major)
        
        else:
            # Fallback to structure
            logger.warning("Unknown intent %s, using STRUCTURE", intent)
            return await self._retrieve_structure(query_embedding, refined_query, major)
    
    # ==================== OVERVIEW ====================
    
    async def _retrieve_overview(
        self,
        query: str,
        refined_query: str,
        query_embedding: List[float],
        major: Optional[str]
    ) -> List[Dict]:
        """
        OVERVIEW: Decompose into sub-queries based on target type
        - MAJOR: các khối kiến thức, hình thức thời gian, cơ hội nghề nghiệp
        - COURSE: thông tin chung, mô tả môn học, kế hoạch giảng dạy
        """
        logger.info("Strategy: OVERVIEW_DECOMPOSE")
        
        # Detect type and extract entity
        target_type, entity = await self._detect_overview_target(query)
        logger.info("  Type: %s, Entity: '%s'", target_type, entity)
        
        # Build sub-queries based on type
        if target_type == "MAJOR":
            sub_queries = [
                f"Các khối kiến thức của ngành {entity}",
                f"Hình thức và thời gian học của ngành {entity}",
                f"Cơ hội nghề nghiệp của ngành {entity}"
            ]
        else:  # COURSE
            sub_queries = [
                f"Thông tin chung của môn {entity}",
                f"Mô tả chung của môn {entity}",
                f"Kế hoạch giảng dạy của môn {entity}"
            ]
        
        logger.info("  Sub-queries: %s", sub_queries)
        
        all_sections = []
        for sub_query in sub_queries:
            query_embedding = await ollama_client.generate_embedding(sub_query)
            chunks = await self._search_chunks(
                query=sub_query,
                query_embedding=query_embedding,
                major=major,
                top_k=15
            )

            if chunks:
                section_ids = list(dict.fromkeys(
                    chunk["section_id"] for chunk in chunks
                ))
                sections = await es_client.get_sections_by_ids(section_ids)
                sections = [section for section in sections if section.get("level") == 2]
                all_sections.extend(sections[:3])
        
        all_sections = self._deduplicate_sections(all_sections)
        logger.info("✓ OVERVIEW: %d sections from %d sub-queries", len(all_sections), len(sub_queries))
        return all_sections[:5]
    
    async def _detect_overview_target(self, query: str) -> Tuple[str, str]:
        """Use LLM to detect if query is about MAJOR (ngành) or COURSE (môn) and extract entity name"""
        
        prompt = """Phân tích câu hỏi sau để xác định:
        1. Loại đối tượng: MAJOR (ngành/chương trình đào tạo) hoặc COURSE (môn học)
        2. Tên đối tượng cụ thể

        QUERY: {query}

        Quy tắc:
        - Nếu hỏi về "ngành", "chương trình", "chuyên ngành" → MAJOR
        - Nếu hỏi về "môn", "môn học", "học phần" → COURSE
        - Normalize tên: CNTT → Công nghệ thông tin, TTNT → Trí tuệ nhân tạo, HTTT → Hệ thống thông tin

        Trả về ĐÚNG FORMAT (không giải thích):
        TYPE: [MAJOR hoặc COURSE]
        ENTITY: [tên đối tượng]

        Ví dụ:
        - "Ngành CNTT học những gì?" → TYPE: MAJOR, ENTITY: Công nghệ thông tin
        - "Môn Hoạch định nguồn lực học gì?" → TYPE: COURSE, ENTITY: Hoạch định nguồn lực doanh nghiệp
        """
        
        try:
            response = await ollama_client.generate_answer(prompt.format(query=query))
            
            # Parse response
            target_type = "MAJOR"
            entity = query
            
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith("TYPE:"):
                    type_val = line.replace("TYPE:", "").strip()
                    if "COURSE" in type_val.upper():
                        target_type = "COURSE"
                    else:
                        target_type = "MAJOR"
                elif line.startswith("ENTITY:"):
                    entity = line.replace("ENTITY:", "").strip()
            
            logger.info("LLM detected: type=%s, entity='%s'", target_type, entity)
            return target_type, entity
            
        except Exception as e:
            logger.warning("LLM detection failed: %s, using fallback", e)
            # Fallback to simple keyword detection
            if "môn" in query.lower():
                return "COURSE", query
            return "MAJOR", query
    
    
    # ==================== STRUCTURE ====================``
    
    async def _retrieve_structure(
        self,
        query_embedding: List[float],
        refined_query: str,
        major: Optional[str]
    ) -> List[Dict]:
        """
        STRUCTURE: Section-level search with expansion
        """
        logger.info("Strategy: STRUCTURE (section expanded)")
        
        # Search chunks
        chunks = await self._search_chunks(
            query=refined_query,
            query_embedding=query_embedding,
            major=major,
            top_k=15
        )
        
        if not chunks:
            return []
        
        # Rerank chunks
        chunks = await cohere_reranker.rerank_chunks(
            query=refined_query,
            chunks=chunks,
            top_n=10
        )
        
        # Extract section IDs and get sections
        section_ids = list(dict.fromkeys(
            c["section_id"] for c in chunks if c.get("section_id")
        ))
        
        sections = await es_client.get_sections_by_ids(section_ids)
        logger.info("✓ STRUCTURE: %d sections", len(sections))
        return sections[:5]
    
    # ==================== COMPARE ====================
    
    async def _retrieve_compare(
        self,
        query: str,
        query_embedding: List[float],
        major: Optional[str]
    ) -> List[Dict]:
        """
        COMPARE: Extract 2 entities, retrieve for each, merge interleaved
        """
        logger.info("Strategy: COMPARE_SPLIT")
        
        # Extract entities
        entity1, entity2 = await self.query_expander.extract_compare_entities(query)
        
        logger.info("  Entity 1: '%s'", entity1)
        logger.info("  Entity 2: '%s'", entity2)
    
        
        # Retrieve for entity 1
        expanded_entity1 = await self.query_expander.expand(entity1, QueryIntent.COMPARE)
        emb1 = await ollama_client.generate_embedding(expanded_entity1)
        chunks1 = await self._search_chunks(query=expanded_entity1, query_embedding=emb1, major=major, top_k=10)
        chunks1 = await cohere_reranker.rerank_chunks(entity1, chunks1, top_n=5)
        ids1 = list(dict.fromkeys(c.get("section_id") for c in chunks1 if c.get("section_id")))
        sections1 = await es_client.get_sections_by_ids(ids1[:4])
        
        # Retrieve for entity 2
        expanded_entity2 = await self.query_expander.expand(entity2, QueryIntent.COMPARE)
        emb2 = await ollama_client.generate_embedding(expanded_entity2)
        chunks2 = await self._search_chunks(query=expanded_entity2, query_embedding=emb2, major=major, top_k=10)
        chunks2 = await cohere_reranker.rerank_chunks(entity2, chunks2, top_n=5)
        ids2 = list(dict.fromkeys(c.get("section_id") for c in chunks2 if c.get("section_id")))
        sections2 = await es_client.get_sections_by_ids(ids2[:4])
        
        # Merge interleaved
        merged = []
        max_len = max(len(sections1), len(sections2))
        for i in range(max_len):
            if i < len(sections1):
                s = sections1[i].copy()
                s["compare_entity"] = "entity1"
                merged.append(s)
            if i < len(sections2):
                s = sections2[i].copy()
                s["compare_entity"] = "entity2"
                merged.append(s)
        
        unique = self._deduplicate_sections(merged)
        logger.info("✓ COMPARE: %d sections (E1: %d, E2: %d)", len(unique), len(sections1), len(sections2))
        return unique[:8]
    
    # ==================== FACTUAL ====================
    
    async def _retrieve_factual(
        self,
        query_embedding: List[float],
        refined_query: str,
        major: Optional[str]
    ) -> List[Dict]:
        """
        FACTUAL: Chunk exact match with reranking
        """
        logger.info("Strategy: FACTUAL (chunk rerank)")
        
        chunks = await self._search_chunks(
            query=refined_query,
            query_embedding=query_embedding,
            major=major,
            top_k=20
        )
        
        if not chunks:
            return []
        
        # Rerank for precision
        chunks = await cohere_reranker.rerank_chunks(
            query=refined_query,
            chunks=chunks,
            top_n=5
        )
        
        # Return chunks directly (not sections)
        results = []
        for chunk in chunks:
            results.append({
                "text": chunk.get("content", chunk.get("text", "")),
                "section_id": chunk.get("section_id", ""),
                "hierarchy_path": chunk.get("hierarchy_path", ""),
                "score": chunk.get("score", 0.0),
                "result_type": "chunk"
            })
        
        logger.info("✓ FACTUAL: %d chunks", len(results))
        return results
    
    # ==================== ROADMAP ====================
    
    async def _retrieve_roadmap(
        self,
        refined_query: str,
        query_embedding: List[float],
        major: Optional[str]
    ) -> List[Dict]:
        """
        ROADMAP: Seed & Expand approach
        
        Flow:
        1. SEED: Find the most relevant section (e.g. "Học kỳ 6 ngành TTNT")
        2. EXPAND: Use LLM to identify what additional info is needed
        3. RETRIEVE: Get additional sections based on expansion
        """
        logger.info("Strategy: ROADMAP_SEED_EXPAND")

        expanded_query = await self.query_expander.expand(query= refined_query, intent=QueryIntent.ROADMAP)
        logger.info("Expanded query: %s", expanded_query)
        query_embedding = await ollama_client.generate_embedding(expanded_query)
        chunks = await self._search_chunks(
            query=expanded_query,
            query_embedding=query_embedding,
            major=major,
            top_k=10
        )
        
        if not chunks:
            return []

        section_ids = list(dict.fromkeys(
            c["section_id"] for c in chunks if c.get("section_id")
        ))
        all_sections = await es_client.get_sections_by_ids(section_ids)
        
        for i, s in enumerate(all_sections):
            logger.info("  Candidate %d: %s", i, s.get("hierarchy_path", ""))
        
        seed_section = await self._select_best_section(query = refined_query, sections=all_sections)
        if not seed_section:
            seed_section = all_sections[0] if all_sections else None
        
        if not seed_section:
            return []
            
        logger.info("  SEED: %s", seed_section.get("hierarchy_path", "")[:60])

        expansion_queries = await self._analyze_for_expansion(refined_query, seed_section)
        logger.info("  Expansion queries: %s", expansion_queries)
        result_sections = [seed_section]
        
        for exp_query in expansion_queries[:3]: 
            emb = await ollama_client.generate_embedding(exp_query)
            add_chunks = await self._search_chunks(
                query=exp_query,
                query_embedding=emb,
                major=major,
                top_k=3
            )
            if add_chunks:
                add_ids = [c["section_id"] for c in add_chunks if c.get("section_id")]
                add_sections = await es_client.get_sections_by_ids(add_ids[:2])
                result_sections.extend(add_sections)
        
        unique = self._deduplicate_sections(result_sections)
        logger.info("✓ ROADMAP_SEED_EXPAND: 1 seed + %d expanded = %d total", 
                    len(unique) - 1, len(unique))
        return unique[:6]

    async def _select_best_section(
        self, query: str, sections: List[Dict]
    ) -> Optional[Dict]:
        """Select best section using hybrid approach: rule extraction + LLM decision"""
        
        if len(sections) <= 1:
            return sections[0] if sections else None
        
        # Build section options with index
        options = []
        for i, s in enumerate(sections[:8]):
            path = s.get("hierarchy_path", "")
            options.append(f"{i}: {path}")
        
        prompt = f"""NHIỆM VỤ: Chọn ĐÚNG section chứa thông tin học kỳ.

        CÂU HỎI: {query}

        DANH SÁCH SECTIONS:
        {chr(10).join(options)}

        === BƯỚC 1: TRÍCH XUẤT TỪ CÂU HỎI ===
        Xác định:
        - HỌC KỲ: Số mấy? (1, 2, 3, 4, 5, 6, 7, 8)
        - NGÀNH: Tên ngành? (normalize: AI/TTNT → "Trí Tuệ Nhân Tạo", CNTT → "Công Nghệ Thông Tin", HTTT → "Hệ Thống Thông Tin")

        === BƯỚC 2: SO KHỚP VỚI SECTIONS ===
        Tìm section có path CHỨA CẢ HAI:
        1. Tên ngành (hoặc viết tắt)
        2. "Học kỳ X" hoặc "Học kì X" với X = số học kỳ

        === BƯỚC 3: XÁC NHẬN ===
        Kiểm tra path của section đã chọn:
        - Có chứa đúng tên ngành? ✓/✗
        - Có chứa đúng số học kỳ? ✓/✗

        VÍ DỤ:
        - Câu hỏi: "Học kỳ 5 ngành AI" → Tìm path chứa "Trí Tuệ" + "Học kỳ 5"
        - Câu hỏi: "HK3 CNTT" → Tìm path chứa "Công Nghệ Thông Tin" + "Học kỳ 3"

        TRẢ LỜI (chỉ 1 dòng):
        BEST: [số index]"""

        try:
            response = await ollama_client.generate_answer(prompt)
            
            if "BEST:" in response:
                match = re.search(r'BEST:\s*(\d+)', response)
                if match:
                    idx = int(match.group(1))
                    if idx < len(sections):
                        return sections[idx]
            
        except Exception as e:
            logger.warning("LLM select failed: %s", e)
            return sections[0] if sections else None
    
    async def _analyze_for_expansion(
        self, query: str, seed_section: Dict
    ) -> List[str]:
        """
        OPTIMIZED: Regex-first placeholder detection
        Only triggers expansion if placeholders found in seed text
        """
        seed_text = seed_section.get("text", "")
        seed_path = seed_section.get("hierarchy_path", "").split('>')
        major_name = seed_path[0].strip() if seed_path else ""
        
        # === STEP 1: REGEX PLACEHOLDER DETECTION ===
        # These patterns indicate courses that need expansion
        PLACEHOLDER_PATTERNS = [
            r"môn\s+tự\s+chọn\s+ngành",
            r"môn\s+tự\s+chọn\s+liên\s+ngành", 
            r"môn\s+cơ\s+sở\s+ngành",
            r"môn\s+học\s+tự\s+chọn",
            r"môn\s+chuyên\s+ngành",
            r"các\s+môn\s+học\s+chuyên\s+ngành",
            r"các\s+môn\s+học\s+cơ\s+sở\s+ngành",
            r"\(\*\*\)",  # Pattern like "Các môn học chuyên ngành (**)"
        ]
        
        seed_text_lower = seed_text.lower()
        found_placeholders = []
        
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, seed_text_lower):
                found_placeholders.append(pattern)
        
        # === EARLY EXIT: No placeholders found ===
        if not found_placeholders:
            logger.info("  ✓ No placeholders detected - skipping expansion")
            return []
        
        logger.info("  Found placeholders: %s", found_placeholders[:3])
        logger.info("  Major name: %s", major_name)
        
        # === STEP 2: GENERATE EXPANSION QUERIES (no LLM needed) ===
        expansion_queries = []
        
        # Map detected patterns to expansion queries
        if re.search(r"tự\s+chọn\s+ngành", seed_text_lower):
            expansion_queries.append(f"Các môn học tự chọn ngành {major_name}")
            
        if re.search(r"tự\s+chọn\s+liên\s+ngành", seed_text_lower):
            expansion_queries.append(f"Các môn học tự chọn liên ngành {major_name}")
            
        if re.search(r"cơ\s+sở\s+ngành", seed_text_lower):
            expansion_queries.append(f"Các môn học cơ sở ngành {major_name}")
            
        if re.search(r"chuyên\s+ngành|\(\*\*\)", seed_text_lower):
            expansion_queries.append(f"Các môn học chuyên ngành {major_name}")
        
        logger.info("  Expansion queries: %s", expansion_queries)
        return expansion_queries[:3]

    # ==================== POSTPROCESS ====================
    
    async def postprocess(
        self,
        sections: List[Dict],
        query: str,
        enable_reranking: bool = True,
        intent: QueryIntent = None
    ) -> List[Dict]:
        """
        POSTPROCESS: Optional reranking and deduplication
        """
        if not sections:
            return []
        
        logger.info("=" * 60)
        logger.info("POSTPROCESS: %d sections", len(sections))
        logger.info("=" * 60)
        
        # Deduplicate
        unique_sections = self._deduplicate_sections(sections)
        
        # Rerank if enabled and not already reranked
        if enable_reranking and intent not in [QueryIntent.FACTUAL, QueryIntent.COMPARE]:
            try:
                unique_sections = await cohere_reranker.rerank_sections(
                    query=query,
                    sections=unique_sections,
                    top_n=min(len(unique_sections), 10)
                )
            except Exception as e:
                logger.warning("Reranking failed: %s", e)
        
        logger.info("✓ POSTPROCESS: %d final sections", len(unique_sections))
        return unique_sections
    
    # ==================== UTILITIES ====================
    
    def _deduplicate_sections(self, sections: List[Dict]) -> List[Dict]:
        """Remove duplicate sections by section_id"""
        seen = set()
        unique = []
        for s in sections:
            sid = s.get("section_id", "")
            if sid and sid not in seen:
                seen.add(sid)
                unique.append(s)
            elif not sid:
                unique.append(s)
        return unique
    
    # ==================== FULL PIPELINE ====================
    
    async def retrieve(
        self,
        query: str,
        major: Optional[str] = None,
        enable_reranking: bool = True,
        search_mode: Optional[str] = None
    ) -> Tuple[List[Dict], QueryIntent]:
        """
        Full retrieval pipeline: preprocess → core → postprocess
        
        Args:
            query: User query text
            major: Optional major filter
            enable_reranking: Whether to enable reranking
            search_mode: Search mode ("vector", "fulltext", "hybrid") - uses config default if None
            
        Returns:
            Tuple of (sections, detected_intent)
        """
        # Set search mode for this retrieval
        if search_mode is not None:
            self._search_mode = SearchMode(search_mode)
        else:
            self._search_mode = None  # Use config default
        
        # Preprocess
        intent, refined_query = await self.preprocess(query, major)
        
        # Generate embedding
        query_embedding = await ollama_client.generate_embedding(refined_query)
        
        # Core retrieval
        sections = await self.core_retrieval(
            query=query,
            refined_query=refined_query,
            query_embedding=query_embedding,
            intent=intent,
            major=major
        )

        
        # Postprocess
        sections = await self.postprocess(
            sections=sections,
            query=query,
            enable_reranking=enable_reranking,
            intent=intent
        )
        
        return sections, intent
    
    async def run(
        self,
        query: str,
        major: Optional[str] = None,
        enable_reranking: bool = True,
        search_mode: Optional[str] = None
    ) -> Tuple[List[Dict], Dict]:
        """
        Run retrieval pipeline (compatible with existing code)
        
        Args:
            query: User query text
            major: Optional major filter
            enable_reranking: Whether to enable reranking
            search_mode: Search mode ("vector", "fulltext", "hybrid") - uses config default if None
            
        Returns:
            Tuple of (sections, metadata_dict)
        """
        import time
        start_time = time.time()
        
        # Execute pipeline
        sections, intent = await self.retrieve(query, major, enable_reranking, search_mode)
        
        # Build metadata
        retrieval_time = (time.time() - start_time) * 1000
        actual_search_mode = self._get_search_mode().value
        metadata = {
            "intent": intent.value,
            "strategy": f"{intent.value}_strategy",
            "search_mode": actual_search_mode,
            "retrieval_time_ms": retrieval_time,
            "num_sections": len(sections),
            "major": major
        }
        
        return sections, metadata


# Export singleton instance
intent_engine = IntentBasedRetrievalEngine()


