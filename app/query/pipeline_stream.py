"""
Streaming RAG Query Pipeline
Handles RAG with streaming response
"""
import time
import logging
from typing import Optional, AsyncGenerator
from collections import defaultdict

from app.clients.elasticsearch import es_client
from app.clients.ollama import ollama_client
from app.clients.openai_client import openai_client
from app.clients.cohere_reranker import cohere_reranker
from app.core.config import settings
from app.query.query_expander import expand_query

logger = logging.getLogger(__name__)


async def run_query_stream(
    query: str,
    major: Optional[str] = None,
    top_k: int = 15,
    enable_reranking: bool = None,
    enable_query_expansion: bool = None
) -> AsyncGenerator[str, None]:
    """
    Execute RAG query pipeline with streaming response
    
    This function performs the same RAG pipeline as run_query but streams
    the answer generation in real-time.
    
    Args:
        query: User query text
        major: Optional major filter
        top_k: Number of chunks to retrieve
        enable_reranking: Override global reranking setting
        enable_query_expansion: Override global expansion setting
        
    Yields:
        Text chunks of the generated answer
    """
    start_time = time.time()
    
    # Use config default if not specified
    if enable_reranking is None:
        enable_reranking = settings.enable_reranking
    if enable_query_expansion is None:
        enable_query_expansion = settings.enable_query_expansion
        
    logger.info(f"Running streaming query: '{query}' | Major: {major}")
    
    try:
        # Step 1: Query Expansion
        search_query = await expand_query(
            original_query=query,
            major=major,
            enable_expansion=enable_query_expansion
        )
        
        if search_query != query:
            logger.info(f"Query expanded: '{query}' -> '{search_query}'")
        
        # Step 2: Generate embedding and search
        query_embedding = await ollama_client.generate_embedding(search_query)
        chunks = await es_client.search_chunks(
            query_embedding=query_embedding,
            major=major,
            top_k=top_k
        )
        
        if not chunks:
            logger.warning("No chunks found for query")
            yield "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn."
            return
        
        # Step 3: Get sections
        section_ids = list(set(chunk["section_id"] for chunk in chunks))
        sections = await es_client.get_sections_by_ids(section_ids)
        
        if not sections:
            logger.warning("No sections found")
            yield "Xin lỗi, tôi không thể truy xuất thông tin chi tiết."
            return
        
        # Step 4: Reranking (if enabled)
        if enable_reranking and settings.cohere_api_key:
            logger.info("Reranking sections with Cohere...")
            try:
                reranked_sections = await cohere_reranker.rerank_sections(
                    query=query,
                    sections=sections,
                    top_n=settings.rerank_top_n
                )
                sections = reranked_sections
            except Exception as e:
                logger.warning(f"Reranking failed, using original sections: {e}")
        else:
            sections = sections[:settings.rerank_top_n]
        
        # Step 5: Build context
        hierarchy_parts = []
        for idx, section in enumerate(sections):
            hierarchy_parts.append(f"Đường dẫn của Context {idx}: {section['hierarchy_path']}\n")
        hierarchy = "\n".join(hierarchy_parts)

        context_parts = []
        for idx, section in enumerate(sections):
            context_parts.append(f"Context {idx}: {section['text']}\n")
        context = "\n".join(context_parts)
        
        # Step 6: Build prompt
        prompt = f"""Bạn là một trợ lý tư vấn tuyển sinh đại học chuyên nghiệp. Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên dựa trên thông tin được cung cấp.

    NGUYÊN TẮC TRẢ LỜI:
    - Chỉ sử dụng thông tin từ CONTEXT được cung cấp bên dưới
    - Trả lời bằng tiếng Việt, rõ ràng và súc tích
    - Nếu thông tin không đủ để trả lời, hãy nói thẳng là "Tôi không có đủ thông tin để trả lời câu hỏi này"
    - Không bịa đặt hoặc suy luận thông tin không có trong CONTEXT
    - Trích dẫn thông tin chính xác từ CONTEXT
    
    Quy trình để trả về được câu trả lời tốt nhất:
    - Dựa theo phần "Đường dẫn" ở mỗi đầu content để hiểu cấu trúc tài liệu dựa trên câu hỏi đặt ra
    - Phân cấp các phần thông tin quan trọng dựa trên câu hỏi để xây dựng câu trả lời
    - Sử dụng ngôn ngữ tự nhiên, thân thiện và chuyên nghiệp để trả lời câu hỏi

    Hãy sử dụng hierarchy bên dưới để hiểu cấu trúc phân cấp của các phần CONTEXT:
    {hierarchy}
    sau đó sử dụng CONTEXT bên dưới để trả lời câu hỏi:
    CONTEXT:
    {context}

    CÂU HỎI: {query}

    TRẢ LỜI:"""
        
        # Step 7: Stream answer generation
        if settings.use_openai and settings.openai_api_key:
            logger.info("Using OpenAI for streaming answer generation")
            async for chunk in openai_client.generate_answer_stream(prompt):
                yield chunk
        else:
            logger.info("Using Ollama for streaming answer generation")
            async for chunk in ollama_client.generate_answer_stream(prompt):
                yield chunk
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"Streaming query completed in {total_time:.2f}ms")
        
    except Exception as e:
        logger.error(f"Streaming query failed: {e}")
        yield f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi: {str(e)}"
