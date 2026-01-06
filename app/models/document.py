"""
Document model for storing user documents
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """Document model for user documents with markdown content for RAG ingestion"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False, default="program")  # program, syllabus, etc.
    academic_year = Column(String(20), nullable=True)  # e.g. "2024-2025"
    body = Column(Text, nullable=False)  # Markdown content for RAG ingestion
    
    # Relationships
    # user = relationship("User", back_populates="documents")
