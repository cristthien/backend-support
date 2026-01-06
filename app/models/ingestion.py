"""
Ingestion-related Pydantic models
"""
from pydantic import BaseModel


class IngestRequest(BaseModel):
    """Request to ingest data from file"""
    file_path: str


class IngestResponse(BaseModel):
    """Ingestion response with statistics"""
    status: str
    major: str
    sections_indexed: int
    chunks_indexed: int
    sections_failed: int
    chunks_failed: int


class IndexStats(BaseModel):
    """Index statistics"""
    sections: int
    chunks: int
