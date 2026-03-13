"""
Pydantic models for query request/response
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class QueryRequest(BaseModel):
    """RAG query request"""
    query: str = Field(..., description="User query text")
    major: Optional[str] = Field(None, description="Optional major filter (e.g., 'Ngành Công Nghệ Thông Tin')")
    top_k: int = Field(15, description="Number of chunks to retrieve", ge=1, le=50)
    include_sources: bool = Field(True, description="Whether to include source sections in response")
    enable_reranking: Optional[bool] = Field(None, description="Enable Cohere reranking (None = use config default)")
    search_mode: Optional[Literal["vector", "fulltext", "hybrid"]] = Field(None, description="Search mode: vector, fulltext, or hybrid")
    pipeline_mode: Optional[Literal["naive", "intent"]] = Field("intent", description="Pipeline mode: naive or intent")


class SourceInfo(BaseModel):
    """Information about a source section"""
    section_id: str
    title: str
    hierarchy_path: str
    text_preview: str = Field(..., description="First 200 chars of section text")
    score: Optional[float] = None


class QueryMetadata(BaseModel):
    """Query metadata and timing info"""
    major_used: Optional[str]
    chunks_retrieved: int
    sections_retrieved: int
    total_time_ms: Optional[float] = None


class QueryResponse(BaseModel):
    """RAG query response"""
    answer: str
    sources: List[SourceInfo] = []
    chunks: List[Dict[str, Any]] = []
    metadata: QueryMetadata
