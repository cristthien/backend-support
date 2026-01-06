"""
Chat CRUD routes - Simplified with lazy creation and Intent-Based RAG
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json

from app.db.session import get_db
from app.schemas.chat import (
    ChatSessionResponse, ChatMessageCreate,
    ChatMessageResponse, ChatWithMessages, ChatSessionListResponse,
    ChatResponse
)
from app.models.user import User
from app.models.chat import MessageRole
from app.repositories import chat_repository
from app.core.security import get_current_active_user
from app.clients.ollama import ollama_client
from app.clients.elasticsearch import es_client
from app.query.intent_based_rag_pipeline import rag_pipeline

router = APIRouter(prefix="/api/chats", tags=["Chats"])
logger = logging.getLogger(__name__)


async def generate_chat_title(message: str) -> str:
    """Use Ollama to generate a short, descriptive chat title from first message"""
    try:
        prompt = f"""Generate a very short title (max 5 words, Vietnamese) for a chat that starts with this message:
"{message[:200]}"

Respond with ONLY the title, no quotes, no explanation."""
        
        title = await ollama_client.generate_answer(prompt)
        title = title.strip().strip('"').strip("'")
        
        # Fallback if title is too long or empty
        if not title or len(title) > 60:
            return message[:50] + "..." if len(message) > 50 else message
        
        return title
    except Exception as e:
        logger.warning(f"Failed to generate title: {e}")
        return message[:50] + "..." if len(message) > 50 else message


@router.get("", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's chat sessions"""
    chats, total = await chat_repository.get_chat_sessions(
        db=db,
        user_id=current_user.id
    )
    
    return ChatSessionListResponse(
        total=total,
        chats=[ChatSessionResponse.from_orm(chat) for chat in chats]
    )


@router.get("/{chat_id}", response_model=ChatWithMessages)
async def get_chat_with_messages(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat session with all messages"""
    chat = await chat_repository.get_chat_by_id(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    messages = await chat_repository.get_chat_messages(db, chat_id)
    
    return ChatWithMessages(
        id=chat.id,
        user_id=chat.user_id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        messages=[ChatMessageResponse.from_orm(msg) for msg in messages]
    )


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete chat session and all its messages"""
    chat = await chat_repository.get_chat_by_id(db, chat_id, current_user.id)
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    await chat_repository.delete_chat_session(db, chat)
    return None


# ============================================================================
# Main Chat Endpoints - Lazy Creation with Intent-Based RAG
# ============================================================================

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def chat_with_rag(
    message: ChatMessageCreate,
    chat_id: Optional[int] = Query(None, description="Chat session ID. If not provided, creates new session."),
    major: Optional[str] = Query(None, description="Filter by major"),
    top_k: int = Query(15, ge=1, le=50),
    enable_reranking: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with Intent-Based RAG assistant (regular response)
    
    - If `chat_id` is provided: continues existing chat session
    - If `chat_id` is NOT provided: creates new session with auto-generated title
    
    Uses Intent-Based RAG pipeline:
    1. Intent Detection (CHUNK_LEVEL / SECTION_LEVEL / HIERARCHICAL)
    2. Schema-aware Query Expansion
    3. Smart Retrieval (strategy based on intent)
    4. Reranking (optional)
    5. Intent-aware Answer Generation
    
    Returns:
        - chat_id: Chat session ID
        - message_id: Assistant message ID
        - answer: Generated answer text
        - sources: List of source sections/chunks
        - metadata: Pipeline metadata including intent, timing, etc.
    """
    # Validate role
    if message.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only 'user' messages can be sent to this endpoint"
        )
    
    # Ensure ES connection
    if not es_client.client:
        await es_client.connect()
    
    # Get or create chat session
    if chat_id:
        # Existing chat - verify ownership
        chat = await chat_repository.get_chat_by_id(db, chat_id, current_user.id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        # New chat - create with auto-generated title
        title = await generate_chat_title(message.content)
        chat = await chat_repository.create_chat_session(
            db=db,
            user_id=current_user.id,
            title=title
        )
        logger.info(f"Created new chat session {chat.id} with title: {title}")
    
    # Save user message
    await chat_repository.add_message(
        db=db,
        chat_id=chat.id,
        role=MessageRole.USER,
        content=message.content
    )
    
    # Run Intent-Based RAG query
    try:
        result = await rag_pipeline.run(
            query=message.content,
            major=major,
            top_k=top_k,
            enable_reranking=enable_reranking,
            enable_query_expansion=True
        )
        
        # Format sources for database storage (include content to avoid re-querying ES)
        db_sources = [
            {
                "id": src.get("section_id"),
                "type": "section",
                "title": src.get("title"),
                "hierarchy_path": src.get("hierarchy_path"),
                "content": src.get("text_preview"),
                "score": src.get("score")
            }
            for src in result["sources"]
        ]
        
        # Save assistant response with sources
        assistant_message = await chat_repository.add_message(
            db=db,
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content=result["answer"],
            sources=db_sources if db_sources else None
        )
        
        return ChatResponse(
            chat_id=chat.id,
            message_id=assistant_message.id,
            answer=result["answer"],
            sources=result["sources"],
            metadata=result["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Chat query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_with_rag_stream(
    message: ChatMessageCreate,
    chat_id: Optional[int] = Query(None, description="Chat session ID. If not provided, creates new session."),
    major: Optional[str] = Query(None, description="Filter by major"),
    top_k: int = Query(15, ge=1, le=50),
    enable_reranking: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with Intent-Based RAG assistant (streaming response)
    
    - If `chat_id` is provided: continues existing chat session
    - If `chat_id` is NOT provided: creates new session with auto-generated title
    
    Returns Server-Sent Events (SSE) stream:
    - {"type": "chat_info", "data": {"chat_id": 123}}
    - {"type": "metadata", "data": {...}}
    - {"type": "sources", "data": [...]}
    - {"type": "answer_chunk", "data": "text"}
    - {"type": "done", "data": {"message_id": 456}}
    """
    # Validate role
    if message.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only 'user' messages can be sent to this endpoint"
        )
    
    # Ensure ES connection
    if not es_client.client:
        await es_client.connect()
    
    # Get or create chat session
    if chat_id:
        chat = await chat_repository.get_chat_by_id(db, chat_id, current_user.id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        title = await generate_chat_title(message.content)
        chat = await chat_repository.create_chat_session(
            db=db,
            user_id=current_user.id,
            title=title
        )
        logger.info(f"Created new chat session {chat.id} with title: {title}")
    
    # Save user message
    await chat_repository.add_message(
        db=db,
        chat_id=chat.id,
        role=MessageRole.USER,
        content=message.content
    )
    
    # Stream generator
    async def stream_generator():
        complete_response = ""
        collected_sources = []
        try:
            # Send chat info first
            yield f"data: {json.dumps({'type': 'chat_info', 'data': {'chat_id': chat.id}}, ensure_ascii=False)}\n\n"
            
            async for chunk in rag_pipeline.run_with_streaming(
                query=message.content,
                major=major,
                top_k=top_k,
                enable_reranking=enable_reranking,
                enable_query_expansion=True
            ):
                # Forward pipeline chunks
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
                # Collect answer chunks
                if chunk.get("type") == "answer_chunk":
                    complete_response += chunk.get("data", "")
                
                # Collect sources
                if chunk.get("type") == "sources":
                    collected_sources = [
                        {
                            "id": src.get("section_id"),
                            "type": "section",
                            "title": src.get("title"),
                            "hierarchy_path": src.get("hierarchy_path"),
                            "content": src.get("text_preview"),  # Full text preview
                            "score": src.get("score")
                        }
                        for src in chunk.get("data", [])
                    ]
            
            # Save complete response with sources
            assistant_message = await chat_repository.add_message(
                db=db,
                chat_id=chat.id,
                role=MessageRole.ASSISTANT,
                content=complete_response,
                sources=collected_sources
            )
            
            # Send done with message_id
            yield f"data: {json.dumps({'type': 'done', 'data': {'message_id': assistant_message.id}}, ensure_ascii=False)}\n\n"
            logger.info(f"Saved streaming response to chat {chat.id} with {len(collected_sources)} sources")
            
        except Exception as e:
            logger.error(f"Streaming chat failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Chat-Id": str(chat.id)
        }
    )
