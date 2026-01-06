"""
Ingestion API endpoints"""
from fastapi import APIRouter, HTTPException, status
import logging

from app.models.ingestion import IngestRequest, IngestResponse, IndexStats
from app.ingestion.pipeline import ingest_data
from app.clients.elasticsearch import es_client

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Ingest data from simple-output.json
    
    - Extracts major from H1 heading
    - Generates embeddings
    - Indexes to Elasticsearch
    """
    try:
        stats = await ingest_data(request.file_path)
        
        return IngestResponse(
            status="success",
            major=stats["major"],
            sections_indexed=stats["sections_indexed"],
            chunks_indexed=stats["chunks_indexed"],
            sections_failed=stats["sections_failed"],
            chunks_failed=stats["chunks_failed"]
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {request.file_path}"
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get("/status", response_model=IndexStats)
async def get_status():
    """Get current index statistics"""
    try:
        stats = await es_client.get_index_stats()
        return IndexStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.delete("/clear")
async def clear_indices():
    """Clear all indices (for re-ingestion)"""
    try:
        await es_client.delete_indices()
        await es_client.create_indices()
        return {"status": "success", "message": "Indices cleared and recreated"}
    except Exception as e:
        logger.error(f"Failed to clear indices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear indices: {str(e)}"
        )
