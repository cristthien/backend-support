"""
Query API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import logging
import json

from app.models.query import QueryRequest, QueryResponse
from app.query.pipeline import run_query
from app.query.intent_based_rag_pipeline import rag_pipeline
from app.clients.elasticsearch import es_client

router = APIRouter(prefix="/api/query", tags=["query"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Execute RAG query (legacy endpoint)
    
    - Generates query embedding
    - Searches chunks with optional major filter
    - Expands to full sections
    - Reranks sections using Cohere (optional)
    - Generates answer with context
    """
    try:
        response = await run_query(
            query=request.query,
            major=request.major,
            top_k=request.top_k,
            include_sources=request.include_sources,
            enable_reranking=request.enable_reranking
        )
        return response
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/intent")
async def query_intent_based(request: QueryRequest):
    """
    Execute Intent-Based RAG query (recommended)
    
    Flow:
    1. Intent Detection (CHUNK_LEVEL / SECTION_LEVEL / HIERARCHICAL)
    2. Schema-aware Query Expansion
    3. Smart Retrieval (strategy based on intent)
    4. Reranking (optional)
    5. Intent-aware Answer Generation
    
    Returns:
        - answer: Generated answer text
        - sources: List of source sections/chunks
        - metadata: Pipeline metadata including intent, timing, etc.
    """
    try:
        # Ensure ES connection
        if not es_client.client:
            await es_client.connect()
        
        result = await rag_pipeline.run(
            query=request.query,
            major=request.major,
            top_k=request.top_k,
            enable_reranking=request.enable_reranking,
            enable_query_expansion=True  # Always enable for intent-based
        )
        
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "metadata": result["metadata"]
        }
    except Exception as e:
        logger.error(f"Intent-based query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/intent/stream")
async def query_intent_based_stream(request: QueryRequest):
    """
    Execute Intent-Based RAG query with streaming response
    
    Returns Server-Sent Events (SSE) stream:
    - {"type": "metadata", "data": {...}}
    - {"type": "sources", "data": [...]}
    - {"type": "answer_chunk", "data": "text"}
    - {"type": "done", "data": {...}}
    """
    async def stream_generator():
        try:
            # Ensure ES connection
            if not es_client.client:
                await es_client.connect()
            
            async for chunk in rag_pipeline.run_with_streaming(
                query=request.query,
                major=request.major,
                top_k=request.top_k,
                enable_reranking=request.enable_reranking,
                enable_query_expansion=True
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            logger.error(f"Stream query failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )