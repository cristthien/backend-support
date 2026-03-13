"""
Query API endpoints - Unified RAG query with search_mode and pipeline_mode
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import logging
import json

from app.models.query import QueryRequest
from app.query.intent_based_rag_pipeline import rag_pipeline
from app.query.naive_pipeline import run_naive_query
from app.clients.elasticsearch import es_client

router = APIRouter(prefix="/api/query", tags=["query"])
logger = logging.getLogger(__name__)


@router.post("/")
async def query(request: QueryRequest):
    """
    Execute RAG query with configurable pipeline and search mode
    
    Request body fields:
    - `query`: User query text (required)
    - `major`: Optional major filter
    - `top_k`: Number of results (default: 15)
    - `enable_reranking`: Enable/disable reranking
    - `search_mode`: "vector", "fulltext", or "hybrid" (default: vector)
    - `pipeline_mode`: "naive" or "intent" (default: intent)
    
    Pipeline modes:
    - **intent**: Intent-Based RAG with smart retrieval strategies
    - **naive**: Simple RAG (no query expansion, no reranking, no section expansion)
    
    Search modes:
    - **vector**: Dense vector search (kNN)
    - **fulltext**: BM25 text search
    - **hybrid**: Combined vector + fulltext with RRF
    
    Returns:
        - answer: Generated answer text
        - sources: List of source sections/chunks
        - metadata: Pipeline metadata including intent, timing, etc.
    """
    # Extract parameters
    search_mode = request.search_mode or "vector"
    pipeline_mode = request.pipeline_mode or "intent"
    
    try:
        # Ensure ES connection
        if not es_client.client:
            await es_client.connect()
        
        if pipeline_mode == "naive":
            response = await run_naive_query(
                query=request.query,
                major=request.major,
                top_k=request.top_k,
                include_sources=True,
                search_mode=search_mode
            )
            return {
                "answer": response.answer,
                "sources": [
                    {
                        "section_id": src.section_id,
                        "title": src.title,
                        "hierarchy_path": src.hierarchy_path,
                        "text_preview": src.text_preview,
                        "score": src.score
                    }
                    for src in response.sources
                ],
                "metadata": {
                    "pipeline": "naive",
                    "search_mode": search_mode,
                    "major": response.metadata.major_used,
                    "chunks_retrieved": response.metadata.chunks_retrieved,
                    "sections_retrieved": response.metadata.sections_retrieved,
                    "total_time_ms": response.metadata.total_time_ms
                }
            }
        else:
            result = await rag_pipeline.run(
                query=request.query,
                major=request.major,
                top_k=request.top_k,
                enable_reranking=request.enable_reranking,
                enable_query_expansion=True,
                search_mode=search_mode
            )
            return {
                "answer": result["answer"],
                "sources": result["sources"],
                "metadata": result["metadata"]
            }
            
    except Exception as e:
        logger.error("Query failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/stream")
async def query_stream(request: QueryRequest):
    """
    Execute RAG query with streaming response
    
    Request body fields:
    - `query`: User query text (required)
    - `major`: Optional major filter
    - `top_k`: Number of results (default: 15)
    - `enable_reranking`: Enable/disable reranking
    - `search_mode`: "vector", "fulltext", or "hybrid"
    
    Note: Streaming only supports intent pipeline (pipeline_mode is ignored).
    
    Returns Server-Sent Events (SSE) stream:
    - {"type": "metadata", "data": {...}}
    - {"type": "sources", "data": [...]}
    - {"type": "answer_chunk", "data": "text"}
    - {"type": "done", "data": {...}}
    """
    search_mode = request.search_mode or "vector"
    
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
                enable_query_expansion=True,
                search_mode=search_mode
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            logger.error("Stream query failed: %s", e, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )