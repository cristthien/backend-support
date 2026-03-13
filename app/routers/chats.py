"""
Chat CRUD routes - Simplified with lazy creation and Intent-Based RAG
"""
from typing import Optional, Literal
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
from app.core.config import settings
from app.clients.ollama import ollama_client
from app.clients.elasticsearch import es_client
from app.query.intent_based_rag_pipeline import rag_pipeline
from app.query.naive_pipeline import run_naive_query
from app.services.history_contextualizer import history_contextualizer, ChatMessage

# Type aliases for search and pipeline modes
SearchModeType = Literal["vector", "fulltext", "hybrid"]
PipelineModeType = Literal["naive", "intent"]

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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with RAG assistant (regular response)
    
    Request body fields:
    - `chat_id`: Chat session ID. If not provided, creates new session.
    - `major`: Optional major filter
    - `top_k`: Number of results (default: 15)
    - `enable_reranking`: Enable/disable reranking
    - `search_mode`: "vector", "fulltext", or "hybrid"
    - `pipeline_mode`: "naive" or "intent" (default: intent)
    - `role`: Must be "user"
    - `content`: Message content
    
    Pipeline modes:
    - **intent**: Intent-Based RAG with smart retrieval strategies
    - **naive**: Simple RAG (no query expansion, no reranking, no section expansion)
    
    Search modes:
    - **vector**: Dense vector search (kNN)
    - **fulltext**: BM25 text search
    - **hybrid**: Combined vector + fulltext with RRF
    
    Returns:
        - chat_id: Chat session ID
        - message_id: Assistant message ID
        - answer: Generated answer text
        - sources: List of source sections/chunks
        - metadata: Pipeline metadata including intent, timing, etc.
    """
    # Extract parameters from body
    chat_id = message.chat_id
    major = message.major
    top_k = message.top_k or 15
    enable_reranking = message.enable_reranking
    search_mode = message.search_mode or "vector"
    pipeline_mode = message.pipeline_mode or "intent"
    
    # Ensure ES connection
    if not es_client.client:
        await es_client.connect()
    
    # Get or create chat session + load history for context
    chat_history = []
    if chat_id:
        # Existing chat - verify ownership
        chat = await chat_repository.get_chat_by_id(db, chat_id, current_user.id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        # Load chat history for context
        if settings.enable_history_context:
            db_messages = await chat_repository.get_chat_messages(db, chat_id)
            chat_history = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in db_messages
            ]
    else:
        # New chat - create with auto-generated title
        title = await generate_chat_title(message.content)
        chat = await chat_repository.create_chat_session(
            db=db,
            user_id=current_user.id,
            title=title
        )
        logger.info("Created new chat session %d with title: %s", chat.id, title)
    
    # Save user message
    await chat_repository.add_message(
        db=db,
        chat_id=chat.id,
        role=MessageRole.USER,
        content=message.content
    )
    
    # Contextualize query using history (resolve references like "nó", "cái đó")
    if chat_history and settings.enable_history_context:
        contextualized_query = await history_contextualizer.contextualize(
            query=message.content,
            history=chat_history,
            max_history=settings.history_context_window
        )
    else:
        contextualized_query = message.content
    
    # Run RAG query based on pipeline_mode
    try:
        if pipeline_mode == "naive":
            response = await run_naive_query(
                query=contextualized_query,
                major=major,
                top_k=top_k,
                include_sources=True,
                search_mode=search_mode
            )
            result = {
                "answer": response.answer,
                "sources": [
                    {
                        "section_id": src.section_id,
                        "title": src.title,
                        "hierarchy_path": src.hierarchy_path,
                        "text_preview": src.text_preview,
                        "score": src.score
                    }
                    for src in response.sources
                ],
                "metadata": {
                    "pipeline": "naive",
                    "search_mode": search_mode or "vector",
                    "major": response.metadata.major_used,
                    "chunks_retrieved": response.metadata.chunks_retrieved,
                    "sections_retrieved": response.metadata.sections_retrieved,
                    "total_time_ms": response.metadata.total_time_ms
                }
            }
        else:
            result = await rag_pipeline.run(
                query=contextualized_query,
                major=major,
                top_k=top_k,
                enable_reranking=enable_reranking,
                enable_query_expansion=True,
                search_mode=search_mode
            )
        
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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with Intent-Based RAG assistant (streaming response)
    
    Request body fields:
    - `chat_id`: Chat session ID. If not provided, creates new session.
    - `major`: Optional major filter
    - `top_k`: Number of results (default: 15)
    - `enable_reranking`: Enable/disable reranking
    - `search_mode`: "vector", "fulltext", or "hybrid"
    - `role`: Must be "user"
    - `content`: Message content
    
    Note: Streaming only supports intent pipeline (pipeline_mode is ignored).
    
    Search modes:
    - **vector**: Dense vector search (kNN)
    - **fulltext**: BM25 text search
    - **hybrid**: Combined vector + fulltext with RRF
    
    Returns Server-Sent Events (SSE) stream:
    - {"type": "chat_info", "data": {"chat_id": 123}}
    - {"type": "metadata", "data": {...}}
    - {"type": "sources", "data": [...]}
    - {"type": "answer_chunk", "data": "text"}
    - {"type": "done", "data": {"message_id": 456}}
    """
    # Extract parameters from body
    chat_id = message.chat_id
    major = message.major
    top_k = message.top_k or 15
    enable_reranking = message.enable_reranking
    search_mode = message.search_mode or "vector"
    logger.info("Chat streaming with RAG: chat_id=%s, search_mode=%s", chat_id, search_mode)
    
    # Ensure ES connection
    if not es_client.client:
        await es_client.connect()
    
    # Get or create chat session + load history for context
    chat_history = []
    if chat_id:
        chat = await chat_repository.get_chat_by_id(db, chat_id, current_user.id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        # Load chat history for context
        if settings.enable_history_context:
            db_messages = await chat_repository.get_chat_messages(db, chat_id)
            chat_history = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in db_messages
            ]
    else:
        title = await generate_chat_title(message.content)
        chat = await chat_repository.create_chat_session(
            db=db,
            user_id=current_user.id,
            title=title
        )
        logger.info("Created new chat session %d with title: %s", chat.id, title)
    
    # Save user message
    await chat_repository.add_message(
        db=db,
        chat_id=chat.id,
        role=MessageRole.USER,
        content=message.content
    )
    
    # Contextualize query using history
    if chat_history and settings.enable_history_context:
        contextualized_query = await history_contextualizer.contextualize(
            query=message.content,
            history=chat_history,
            max_history=settings.history_context_window
        )
    else:
        contextualized_query = message.content
    
    # Stream generator
    async def stream_generator():
        complete_response = ""
        collected_sources = []
        try:
            # Send chat info first
            yield f"data: {json.dumps({'type': 'chat_info', 'data': {'chat_id': chat.id}}, ensure_ascii=False)}\n\n"
            
            async for chunk in rag_pipeline.run_with_streaming(
                query=contextualized_query,
                major=major,
                top_k=top_k,
                enable_reranking=enable_reranking,
                enable_query_expansion=True,
                search_mode=search_mode
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
