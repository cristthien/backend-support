"""
Document Pydantic schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class DocumentBase(BaseModel):
    """Base document schema"""
    title: str
    type: str = "program"  # program, syllabus, etc.
    academic_year: Optional[str] = None  
    body: str  # Markdown content


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    title: Optional[str] = None
    type: Optional[str] = None
    academic_year: Optional[str] = None
    body: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents with pagination"""
    total: int
    skip: int
    limit: int
    documents: List[DocumentResponse]


class DocumentIngestionResult(BaseModel):
    """Schema for document ingestion result"""
    doc_id: int
    sections_indexed: int
    chunks_indexed: int
    sections_failed: int
    chunks_failed: int


class MockIngestionRequest(BaseModel):
    """Schema for mock ingestion request - preview chunking without saving"""
    title: str = "Untitled Document"
    body: str  # Markdown content
    doc_type: str = "program"
    academic_year: Optional[str] = None


class MockIngestionResponse(BaseModel):
    """Schema for mock ingestion response - sections and chunks without embeddings"""
    title: str
    doc_type: str
    academic_year: Optional[str]
    sections: List[dict]
    chunks: List[dict]
    total_sections: int
    total_chunks: int

