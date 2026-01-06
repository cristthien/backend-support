"""
Chat models for storing chat sessions and messages
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
import enum


class MessageRole(str, enum.Enum):
    """Message role types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base, TimestampMixin):
    """Chat session model"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    
    # Relationships
    # messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")


class ChatMessage(Base, TimestampMixin):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Sources from RAG retrieval (for assistant messages)
    # Format: [{"id": "...", "type": "section|chunk", "title": "...", "score": 0.95}, ...]
    sources = Column(JSON, nullable=True, default=None)
    
    # Relationships
    # chat_session = relationship("ChatSession", back_populates="messages")

