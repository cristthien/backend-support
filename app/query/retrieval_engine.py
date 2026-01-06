"""
Retrieval Engine: Preprocess → Core → Postprocess Architecture
Handles the full RAG retrieval flow with intent-based query expansion
"""
import time
import logging
from typing import Optional, List, Dict, Tuple

from app.clients.elasticsearch import es_client
from app.clients.ollama import ollama_client
from app.clients.openai_client import openai_client
from app.clients.cohere_reranker import cohere_reranker
from app.models.query import QueryResponse, SourceInfo, QueryMetadata
from app.core.config import settings
from app.query.query_expander import expand_query

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """
    Retrieval Engine implementing preprocess-core-postprocess pattern
    
    Flow:
        PREPROCESS: Expand query based on intent
        CORE: Retrieve chunks → Extract sections
        POSTPROCESS: Rerank sections → Generate answer
    """
    
    async def preprocess(
        self,
        query: str,
        major: Optional[str],
        enable_expansion: bool
    ) -> str:
        """
        PREPROCESS: Expand query using LLM-based smart expansion
        
        Args:
            query: Original user query
            major: Optional major filter
            enable_expansion: Whether to enable query expansion
            
        Returns:
            Expanded query string
        """
        logger.info("PREPROCESS: Expanding query")
        
        if not enable_expansion:
            logger.info("Expansion disabled")
            return query
        
        # Expand query using smart expansion
        expanded_query = await expand_query(
            original_query=query,
            major=major,
            enable_expansion=enable_expansion
        )
        
        logger.info("Query expanded: '%s' → '%s'", query, expanded_query)
        return expanded_query
    
    async def core_retrieval(
        self,
        query_embedding: List[float],
        major: Optional[str],
        top_k: int,
    ) -> List[Dict]:
        """
        CORE: Retrieve sections from chunks
        
        Strategy: Always retrieve chunks → Extract sections → Expand
        
        Args:
            query_embedding: Embedding vector for the query
            major: Optional major filter
            top_k: Number of chunks to retrieve
            
        Returns:
            List of sections
        """
        logger.info("CORE: Retrieving sections")
        
        # Step 1: Search top-k chunks
        chunks = await es_client.search_chunks(
            query_embedding=query_embedding,
            major=major,
            top_k=top_k
        )
        
        if not chunks:
            logger.warning("No chunks found for query")
            return []
        for chunk in chunks: 
            logger.info("Retrieved chunk: %s", chunk['text'])

        # Step 2: Extract and retrieve full sections
        section_ids = list(dict.fromkeys(
            chunk["section_id"] for chunk in chunks
        ))

        logger.info("Extracted %s unique section IDs", section_ids)
        
        sources = await es_client.get_sections_by_ids(section_ids)
        
        if not sources:
            logger.warning("No sections found for section IDs")
            return []
        
        logger.info("Retrieved %d initial sections", len(sources))
        
        return sources
    
    async def postprocess(
        self,
        sections: List[Dict],
        query: str,
        enable_reranking: bool
    ) -> List[Dict]:
        """
        POSTPROCESS: Optionally rerank sections using Cohere
        
        Args:
            sections: List of retrieved sections
            query: Original user query (for reranking)
            enable_reranking: Whether to enable reranking
            
        Returns:
            Reranked (or top-N) sections
        """
        logger.info("POSTPROCESS: Reranking sections")
        
        if enable_reranking and settings.cohere_api_key:
            logger.info("Reranking %d sections with Cohere...", len(sections))
            try:
                reranked_sections = await cohere_reranker.rerank_sections(
                    query=query,
                    sections=sections,
                    top_n=settings.rerank_top_n
                )
                logger.info("Reranking complete: using top %d sections", len(reranked_sections))
                return reranked_sections
                
            except Exception as e:
                logger.warning("Reranking failed, using original sections: %s", e)
                return sections[:settings.rerank_top_n]
        else:
            if enable_reranking:
                logger.warning("Reranking enabled but Cohere API key not configured")
            # Return top-N sections without reranking
            logger.info("not rerank")
            return sections[:settings.rerank_top_n]
    
    async def generate_answer(
        self,
        query: str,
        sections: List[Dict]
    ) -> str:
        """
        Generate answer using LLM with retrieved sections as context
        
        Args:
            query: Original user query
            sections: Retrieved and reranked sections
            
        Returns:
            Generated answer text
        """
        logger.info("Generating answer with %d sections", len(sections))
        
        # Build hierarchy context
        hierarchy_parts = []
        for idx, section in enumerate(sections):
            hierarchy_parts.append(f"Đường dẫn của Context {idx}: {section['hierarchy_path']}\n")
        hierarchy = "\n".join(hierarchy_parts)
        
        # Build content context
        context_parts = []
        for idx, section in enumerate(sections):
            context_parts.append(f"Context {idx}: {section['text']}\n")
        context = "\n".join(context_parts)
        
        # Build prompt
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

Sau đó sử dụng CONTEXT bên dưới để trả lời câu hỏi:
CONTEXT:
{context}

CÂU HỎI: {query}

TRẢ LỜI:"""
        
        # Generate answer
        if settings.use_openai and settings.openai_api_key:
            logger.info("Using OpenAI GPT-4o for answer generation")
            answer = await openai_client.generate_answer(prompt)
        else:
            logger.info("Using Ollama for answer generation")
            answer = await ollama_client.generate_answer(prompt)
        
        return answer
    
    def build_sources(
        self,
        sections: List[Dict],
        chunks: List[Dict]
    ) -> List[SourceInfo]:
        """
        Build source information from sections and chunks
        
        Args:
            sections: Retrieved sections
            chunks: Retrieved chunks
            
        Returns:
            List of SourceInfo objects
        """
        sources = []
        
        for section in sections:
            # Get best chunk score for this section
            section_chunk_scores = [
                chunk["score"]
                for chunk in chunks
                if chunk["section_id"] == section["section_id"]
            ]
            best_chunk_score = max(section_chunk_scores) if section_chunk_scores else 0.0
            
            # Use rerank score if available, otherwise use chunk score
            score = section.get('rerank_score', best_chunk_score)
            
            source = SourceInfo(
                section_id=section["section_id"],
                title=section["title"],
                hierarchy_path=section["hierarchy_path"],
                text_preview=section["text"],
                score=score
            )
            sources.append(source)
        
        # Sort by score (highest first)
        sources.sort(key=lambda x: x.score, reverse=True)
        
        return sources
    
    async def run(
        self,
        query: str,
        major: Optional[str] = None,
        top_k: int = 10,
        enable_reranking: bool = None,
        enable_query_expansion: bool = None
    ) -> List[Dict]:
        """
        Execute retrieval pipeline: Always returns sections
        
        Args:
            query: User query text
            major: Optional major filter  
            top_k: Number of chunks to retrieve
            enable_reranking: Override global reranking setting
            enable_query_expansion: Override global expansion setting
            
        Returns:
            List of sections
        """
        start_time = time.time()
        
        # Use config defaults if not specified
        if enable_reranking is None:
            enable_reranking = settings.enable_reranking
        if enable_query_expansion is None:
            enable_query_expansion = settings.enable_query_expansion
        
        logger.info(
            "Retrieval Engine: query='%s' | major=%s | top_k=%d | rerank=%s | expand=%s",
            query, major, top_k, enable_reranking, enable_query_expansion
        )
        
        # ===== PREPROCESS =====
        expanded_query = await self.preprocess(
            query=query,
            major=major,
            enable_expansion=enable_query_expansion
        )
        
        # Generate embedding from expanded query
        query_embedding = await ollama_client.generate_embedding(expanded_query)
        
        # ===== CORE RETRIEVAL =====
        sources = await self.core_retrieval(
            query_embedding=query_embedding,
            major=major,
            top_k=top_k
        )
        
        if not sources:
            logger.warning("No results retrieved")
            total_time = (time.time() - start_time) * 1000
            logger.info("Retrieval completed in %.2fms (no results)", total_time)
            return []
        
        # ===== POSTPROCESS =====
        sources = await self.postprocess(
            sections=sources,
            query=query,
            enable_reranking=enable_reranking
        )
        
        total_time = (time.time() - start_time) * 1000
        logger.info("Retrieval completed in %.2fms: %d sections", 
                   total_time, len(sources))
        
        return sources


# Global instance
engine = RetrievalEngine()
