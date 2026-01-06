"""
Document CRUD routes with Elasticsearch ingestion integration
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse, 
    DocumentListResponse, DocumentIngestionResult,
    MockIngestionRequest, MockIngestionResponse
)
from app.models.user import User
from app.models.document import Document
from app.repositories import document_repository
from app.core.security import get_current_active_user
from app.services.document_ingestion_service import document_ingestion_service
from app.clients.elasticsearch import es_client
from app.utils.chunker import MarkdownStructureChunker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/docs", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc: DocumentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new document and ingest it into Elasticsearch
    
    The document will be saved to PostgreSQL immediately, and ingestion
    (chunking + embeddings) will be processed in the background.
    """
    # Save to PostgreSQL
    document = await document_repository.create_document(
        db=db,
        user_id=current_user.id,
        title=doc.title,
        body=doc.body,
        doc_type=doc.type,
        academic_year=doc.academic_year
    )
    
    # Add ingestion to background tasks
    background_tasks.add_task(
        document_ingestion_service.ingest_document,
        doc_id=document.id,
        title=document.title,
        body=document.body,
        doc_type=document.type,
        academic_year=document.academic_year
    )
    
    logger.info("Document %d created, ingestion queued", document.id)
    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents with pagination (public endpoint)
    
    No authentication required.
    """
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id)).select_from(Document)
    )
    total = count_result.scalar()
    
    # Get documents
    result = await db.execute(
        select(Document)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    
    return DocumentListResponse(
        total=total,
        skip=skip,
        limit=limit,
        documents=[DocumentResponse.model_validate(doc) for doc in documents]
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific document by ID (public endpoint)
    
    No authentication required.
    """
    
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.put("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: int,
    doc_update: DocumentUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a document and re-ingest into Elasticsearch (public endpoint)
    
    No authentication required.
    When content changes, the document will be re-ingested (deleted + ingested again).
    """
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update in PostgreSQL
    updated_doc = await document_repository.update_document(
        db=db,
        doc=document,
        title=doc_update.title,
        body=doc_update.body,
        doc_type=doc_update.type,
        academic_year=doc_update.academic_year
    )
    
    # Re-ingest in background
    background_tasks.add_task(
        document_ingestion_service.reingest_document,
        doc_id=updated_doc.id,
        title=updated_doc.title,
        body=updated_doc.body,
        doc_type=updated_doc.type,
        academic_year=updated_doc.academic_year
    )
    
    logger.info("Document %d updated, re-ingestion queued", doc_id)
    return DocumentResponse.model_validate(updated_doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document from PostgreSQL and Elasticsearch (public endpoint)
    
    No authentication required. Hard delete.
    """
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from Elasticsearch first
    await document_ingestion_service.delete_document(doc_id)
    
    # Delete from PostgreSQL
    await document_repository.delete_document(db, document)
    
    logger.info("Document %d deleted from PostgreSQL and Elasticsearch", doc_id)
    return None


@router.post("/{doc_id}/reingest", response_model=Dict[str, Any])
async def reingest_document(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Re-ingest a document into Elasticsearch without updating its content
    
    Use this to rebuild the search index for a document.
    """
    document = await document_repository.get_document_by_id(db, doc_id, current_user.id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Re-ingest synchronously
    result = await document_ingestion_service.reingest_document(
        doc_id=document.id,
        title=document.title,
        body=document.body,
        doc_type=document.type,
        academic_year=document.academic_year
    )
    
    return result


# ============================================================================
# Public endpoints (no authentication required)
# ============================================================================

@router.get("/public/{doc_id}", response_model=DocumentResponse)
async def get_document_public(
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a document's full content by ID (public endpoint)
    
    No authentication required. Allows users to read full document content.
    """
    
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.get("/{doc_id}/sections", response_model=List[Dict[str, Any]])
async def get_document_sections(
    doc_id: int,
    level: Optional[int] = Query(None, description="Filter by heading level (1=H1, 2=H2, etc.)")
):
    """
    Get sections for a document from Elasticsearch
    
    No authentication required.
    Use `level` parameter to filter by heading level (e.g., level=2 for H2 sections).
    """
    sections = await es_client.get_sections_by_doc_id(doc_id, level)
    
    # Remove embedding from response (too large)
    for section in sections:
        section.pop('embedding', None)
    
    return sections


@router.get("/{doc_id}/chunks", response_model=List[Dict[str, Any]])
async def get_document_chunks(doc_id: int):
    """
    Get chunks for a document from Elasticsearch
    
    No authentication required.
    """
    chunks = await es_client.get_chunks_by_doc_id(doc_id)
    
    # Remove embedding from response (too large)
    for chunk in chunks:
        chunk.pop('embedding', None)
    
    return chunks


# ============================================================================
# Mock/Preview endpoints (for testing and development)
# ============================================================================

@router.post("/mock-ingest", response_model=MockIngestionResponse)
async def mock_ingest_document(request: MockIngestionRequest):
    """
    Mock document ingestion - returns parsed sections and chunks without saving
    
    This endpoint is useful for:
    - Previewing how a markdown document will be chunked
    - Testing ingestion without affecting the database or Elasticsearch
    - Generating JSON mock data for testing
    
    Table types (keypair/standard) are detected automatically using LLM.
    Falls back to heuristics if LLM fails.
    
    No authentication required.
    """
    chunker = MarkdownStructureChunker()
    
    # Use async method with LLM-based table type detection
    result = await chunker.chunk_markdown(
        text=request.body,
        metadata={'source': 'mock_ingest', 'doc_type': request.doc_type}
    )
    
    sections = result['sections']
    chunks = result['chunks']
    
    # Extract major from first H1 heading (if exists)
    major = request.title
    
    # Add mock doc_id and other metadata to sections
    processed_sections = []
    for section in sections:
        section_metadata = {
            **section.get('metadata', {}),
            'doc_id': 'mock',
            'major': major,
            'academic_year': request.academic_year,
            'doc_type': request.doc_type,
        }
        processed_sections.append({
            **{k: v for k, v in section.items() if k != 'metadata'},
            'metadata': section_metadata
        })
    
    # Add mock doc_id and other metadata to chunks
    processed_chunks = []
    for chunk in chunks:
        chunk_metadata = {
            **chunk.get('metadata', {}),
            'doc_id': 'mock',
            'major': major,
            'academic_year': request.academic_year,
            'doc_type': request.doc_type,
        }
        processed_chunks.append({
            **{k: v for k, v in chunk.items() if k != 'metadata'},
            'metadata': chunk_metadata
        })
    
    return MockIngestionResponse(
        title=request.title,
        doc_type=request.doc_type,
        academic_year=request.academic_year,
        sections=processed_sections,
        chunks=processed_chunks,
        total_sections=len(processed_sections),
        total_chunks=len(processed_chunks)
    )

