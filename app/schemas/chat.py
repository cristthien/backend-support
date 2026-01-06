"""
Chat Pydantic schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session"""
    title: Optional[str] = "New Chat"


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message"""
    role: str  # "user" or "assistant"
    content: str


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: int
    chat_id: int
    role: str
    content: str
    sources: Optional[List[dict]] = None  # For assistant messages: source references
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatWithMessages(ChatSessionResponse):
    """Schema for chat session with all messages"""
    messages: List[ChatMessageResponse] = []


class ChatSessionListResponse(BaseModel):
    """Schema for list of chat sessions"""
    total: int
    chats: List[ChatSessionResponse]


class ChatResponse(BaseModel):
    """Schema for chat response with RAG results"""
    chat_id: int
    message_id: int
    answer: str
    sources: List[dict] = []
    metadata: Optional[dict] = None
