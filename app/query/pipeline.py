"""
RAG Query Pipeline
Orchestrates 3 engines: Retrieval → Prompt → Generation
"""
import time
import logging
from typing import Optional

from app.models.query import QueryResponse, QueryMetadata
from app.query.retrieval_engine import engine as retrieval_engine
from app.query.prompt_engine import prompt_engine
from app.query.generation_engine import generation_engine
from app.query.source_builder import build_sources

logger = logging.getLogger(__name__)


async def run_query(
    query: str,
    major: Optional[str] = None,
    top_k: int = 10,
    include_sources: bool = True,
    enable_reranking: bool = None,
    enable_query_expansion: bool = None
) -> QueryResponse:
    """
    Execute RAG query pipeline using 3 engines
    
    Architecture:
        1. RETRIEVAL ENGINE: Always returns sections (expanded + reranked)
        2. PROMPT ENGINE: Build prompt from sections
        3. GENERATION ENGINE: LLM answer generation
    
    Args:
        query: User query text
        major: Optional major filter
        top_k: Number of chunks to retrieve
        include_sources: Whether to include source sections
        enable_reranking: Override global reranking setting
        enable_query_expansion: Override global expansion setting
        
    Returns:
        QueryResponse with answer, sources, and metadata
    """
    start_time = time.time()
    
    logger.info(
        "Pipeline START: query='%s' | major=%s | top_k=%d",
        query, major, top_k
    )
    
    # ===== ENGINE 1: RETRIEVAL =====
    logger.info("ENGINE 1: Retrieval")
    sections = await retrieval_engine.run(
        query=query,
        major=major,
        top_k=top_k,
        enable_reranking=enable_reranking,
        enable_query_expansion=enable_query_expansion
    )
    
    # Handle no results
    if not sections:
        return QueryResponse(
            answer="Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn.",
            sources=[],
            chunks=[],
            metadata=QueryMetadata(
                major_used=major,
                chunks_retrieved=0,
                sections_retrieved=0,
                total_time_ms=(time.time() - start_time) * 1000
            )
        )
    
    logger.info("Retrieved %d sections", len(sections))
    
    # ===== ENGINE 2: PROMPT =====
    logger.info("ENGINE 2: Prompt Building")
    prompt = prompt_engine.generate_prompt(
        query=query,
        sections=sections  
    )
    
    # ===== ENGINE 3: GENERATION =====
    logger.info("ENGINE 3: Answer Generation")
    answer = await generation_engine.generate(prompt)
    
    # ===== BUILD RESPONSE =====
    source_infos = build_sources(sections, []) if include_sources else []
    
    total_time = (time.time() - start_time) * 1000
    logger.info("Pipeline COMPLETE in %.2fms", total_time)
    
    return QueryResponse(
        answer=answer,
        sources=source_infos,
        chunks=[],  # Chunks not exposed in response
        metadata=QueryMetadata(
            major_used=major,
            chunks_retrieved=0,
            sections_retrieved=len(sections),
            total_time_ms=total_time
        )
    )
