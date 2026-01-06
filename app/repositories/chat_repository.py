"""
Chat repository for database operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.chat import ChatSession, ChatMessage, MessageRole
from typing import List, Optional


async def create_chat_session(
    db: AsyncSession,
    user_id: int,
    title: str
) -> ChatSession:
    """Create a new chat session"""
    chat = ChatSession(
        user_id=user_id,
        title=title
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def get_chat_sessions(db: AsyncSession, user_id: int) -> tuple[List[ChatSession], int]:
    """Get user's chat sessions"""
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user_id)
    )
    total = count_result.scalar()
    
    # Get chat sessions
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    chats = result.scalars().all()
    
    return chats, total


async def get_chat_by_id(db: AsyncSession, chat_id: int, user_id: int) -> Optional[ChatSession]:
    """Get chat session by ID (ensures user owns it)"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == chat_id)
        .where(ChatSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_chat_with_messages(
    db: AsyncSession,
    chat_id: int,
    user_id: int
) -> Optional[ChatSession]:
    """Get chat session with all messages"""
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == chat_id)
        .where(ChatSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def add_message(
    db: AsyncSession,
    chat_id: int,
    role: MessageRole,
    content: str,
    sources: Optional[List[dict]] = None
) -> ChatMessage:
    """
    Add a message to chat session
    
    Args:
        sources: For assistant messages, list of source references.
                 Format: [{"id": "...", "type": "section|chunk", "title": "...", "score": 0.95}, ...]
    """
    message = ChatMessage(
        chat_id=chat_id,
        role=role,
        content=content,
        sources=sources
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_chat_messages(db: AsyncSession, chat_id: int) -> List[ChatMessage]:
    """Get all messages in a chat session"""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return result.scalars().all()


async def delete_chat_session(db: AsyncSession, chat: ChatSession) -> None:
    """Delete chat session and all its messages"""
    await db.delete(chat)
    await db.commit()
