"""
Naive RAG Query Pipeline
Simple RAG without query expansion, reranking, or section expansion.
Used for benchmarking against standard and intent-based pipelines.
"""
import time
import logging
from typing import Optional, List, Dict

from app.models.query import QueryResponse, QueryMetadata, SourceInfo
from app.clients.elasticsearch import es_client, SearchMode
from app.clients.ollama import ollama_client
from app.query.generation_engine import generation_engine

logger = logging.getLogger(__name__)


def build_naive_prompt(query: str, chunks: List[Dict]) -> str:
    """
    Build simple prompt from chunks (no hierarchy context)
    
    Args:
        query: User query
        chunks: Retrieved chunks
        
    Returns:
        Simple prompt string
    """
    # Build context from chunks
    context_parts = []
    for idx, chunk in enumerate(chunks):
        text = chunk.get('text', '')
        context_parts.append(f"[{idx + 1}] {text}")
    
    context = "\n\n".join(context_parts)
    
    # Simple prompt template
    prompt = f"""Bạn là một trợ lý tư vấn tuyển sinh đại học. Trả lời câu hỏi dựa trên thông tin được cung cấp.

NGUYÊN TẮC:
- Chỉ sử dụng thông tin từ CONTEXT bên dưới
- Trả lời bằng tiếng Việt, rõ ràng và súc tích
- Nếu không đủ thông tin, hãy nói "Tôi không có đủ thông tin để trả lời"
- Không bịa đặt thông tin

CONTEXT:
{context}

CÂU HỎI: {query}

TRẢ LỜI:"""
    
    return prompt


def build_naive_sources(chunks: List[Dict]) -> List[SourceInfo]:
    """
    Build source information from chunks
    
    Args:
        chunks: Retrieved chunks
        
    Returns:
        List of SourceInfo objects
    """
    sources = []
    seen_sections = set()
    
    for chunk in chunks:
        section_id = chunk.get('section_id', '')
        if section_id in seen_sections:
            continue
        seen_sections.add(section_id)
        
        source = SourceInfo(
            section_id=section_id,
            title=chunk.get('title', 'Unknown'),
            hierarchy_path=chunk.get('hierarchy_path', ''),
            text_preview=chunk.get('text', '')[:200],
            score=chunk.get('score', 0.0)
        )
        sources.append(source)
    
    return sources


async def run_naive_query(
    query: str,
    major: Optional[str] = None,
    top_k: int = 10,
    include_sources: bool = True,
    search_mode: Optional[str] = None
) -> QueryResponse:
    """
    Execute Naive RAG query pipeline
    
    Flow: Query → Embedding → Chunk Search → Simple Prompt → LLM Answer
    
    NO query expansion, NO reranking, NO section expansion
    
    Args:
        query: User query text
        major: Optional major filter
        top_k: Number of chunks to retrieve
        include_sources: Whether to include source info
        search_mode: Search mode ("vector", "fulltext", "hybrid") - uses config default if None
        
    Returns:
        QueryResponse with answer, sources, and metadata
    """
    start_time = time.time()
    
    logger.info(
        "Naive Pipeline START: query='%s' | major=%s | top_k=%d | search_mode=%s",
        query, major, top_k, search_mode or "default"
    )
    
    # ===== STEP 1: Generate Embedding =====
    logger.info("STEP 1: Generating embedding")
    query_embedding = await ollama_client.generate_embedding(query)
    
    # ===== STEP 2: Search Chunks =====
    logger.info("STEP 2: Searching chunks")
    
    # Use unified search if search_mode specified, otherwise use vector search
    if search_mode:
        mode_enum = SearchMode(search_mode)
        chunks = await es_client.search_chunks_unified(
            query=query,
            query_embedding=query_embedding,
            major=major,
            top_k=top_k,
            search_mode=mode_enum
        )
    else:
        chunks = await es_client.search_chunks(
            query_embedding=query_embedding,
            major=major,
            top_k=top_k
        )
    
    # Handle no results
    if not chunks:
        logger.warning("No chunks found for query")
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
    
    logger.info("Retrieved %d chunks", len(chunks))
    
    # ===== STEP 3: Build Prompt =====
    logger.info("STEP 3: Building prompt")
    prompt = build_naive_prompt(query=query, chunks=chunks)
    
    # ===== STEP 4: Generate Answer =====
    logger.info("STEP 4: Generating answer")
    answer = await generation_engine.generate(prompt)
    
    # ===== BUILD RESPONSE =====
    source_infos = build_naive_sources(chunks) if include_sources else []
    
    total_time = (time.time() - start_time) * 1000
    logger.info("Naive Pipeline COMPLETE in %.2fms", total_time)
    
    return QueryResponse(
        answer=answer,
        sources=source_infos,
        chunks=[],  # Chunks not exposed in response
        metadata=QueryMetadata(
            major_used=major,
            chunks_retrieved=len(chunks),
            sections_retrieved=len(source_infos),
            total_time_ms=total_time
        )
    )
