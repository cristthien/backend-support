"""
Intent-Based RAG Pipeline
Complete pipeline: Intent Detection → Retrieval → Generation
"""
import time
import logging
from typing import Optional, List, Dict, Tuple

from app.query.intent_based_retrieval_engine import intent_engine
from app.query.intent_based_prompt_engine import IntentBasedPromptGenerator, QueryIntent
from app.clients.ollama import ollama_client
from app.clients.openai_client import openai_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class IntentBasedRAGPipeline:
    """
    Complete Intent-Based RAG Pipeline
    
    Flow:
        1. Intent Detection (Preprocess)
        2. Schema-aware Query Expansion
        3. Smart Retrieval (3 strategies)
        4. Reranking (optional)
        5. Intent-aware Answer Generation
    """
    
    def __init__(self):
        self.prompt_generator = IntentBasedPromptGenerator()
    
    async def run(
        self,
        query: str,
        major: Optional[str] = None,
        top_k: int = 10,
        enable_reranking: bool = None,
        enable_query_expansion: bool = None,
        search_mode: str = None
    ) -> Dict:
        """
        Execute complete RAG pipeline with intent-based optimization
        
        Args:
            query: User query text
            major: Optional major filter
            top_k: Number of results to retrieve
            enable_reranking: Override global reranking setting
            enable_query_expansion: Override global expansion setting
            search_mode: Search mode ("vector", "fulltext", "hybrid") - uses config default if None
            
        Returns:
            Dict with keys:
                - answer: Generated answer text
                - sources: List of source sections
                - metadata: Pipeline metadata (intent, timing, etc.)
        """
        start_time = time.time()
        
        # Use config defaults if not specified
        if enable_reranking is None:
            enable_reranking = settings.enable_reranking
        if enable_query_expansion is None:
            enable_query_expansion = settings.enable_query_expansion
        
        logger.info("="*80)
        logger.info("INTENT-BASED RAG PIPELINE")
        logger.info("="*80)
        logger.info(f"Query: '{query}'")
        logger.info(f"Config: major={major}, top_k={top_k}, rerank={enable_reranking}, expand={enable_query_expansion}, search_mode={search_mode}")
        
        # ===== PHASE 1: RETRIEVAL =====
        logger.info("\n[PHASE 1] RETRIEVAL")
        logger.info("-"*80)
        
        retrieval_start = time.time()
        sections, retrieval_metadata = await intent_engine.run(
            query=query,
            major=major,
            enable_reranking=enable_reranking,
            search_mode=search_mode
        )
        retrieval_time = (time.time() - retrieval_start) * 1000
        
        logger.info(f"✓ Retrieved {len(sections)} sections in {retrieval_time:.2f}ms")
        logger.info(f"  Intent: {retrieval_metadata['intent']}")
        logger.info(f"  Strategy: {retrieval_metadata.get('strategy', 'N/A')}")
        
        if not sections:
            logger.warning("No sections retrieved, cannot generate answer")
            return {
                "answer": "Xin lỗi, tôi không tìm thấy thông tin phù hợp để trả lời câu hỏi của bạn.",
                "sources": [],
                "metadata": {
                    **retrieval_metadata,
                    "generation_time_ms": 0,
                    "total_time_ms": (time.time() - start_time) * 1000
                }
            }
        
        # ===== PHASE 2: GENERATION =====
        logger.info("\n[PHASE 2] GENERATION")
        logger.info("-"*80)
        
        generation_start = time.time()
        
        # Get intent from retrieval metadata
        intent_str = retrieval_metadata["intent"]
        intent = QueryIntent(intent_str)
        
        # Generate intent-aware prompt
        prompt = self.prompt_generator.generate_answer_prompt(
            query=query,
            sections=sections,
            intent=intent
        )
        
        logger.info(f"Generating answer with intent: {intent.value}")
        
        # Generate answer using LLM
        # OVERVIEW intent requires OpenAI o4 for better accuracy (mandatory)
        # Other intents use OpenAI if configured (optional)
        use_openai_for_this_intent = (
            intent == QueryIntent.OVERVIEW or 
            (settings.use_openai and settings.openai_api_key)
        )
        
        if use_openai_for_this_intent and settings.openai_api_key:
            answer = await openai_client.generate_answer(prompt)
        else:
            answer = await ollama_client.generate_answer(prompt)
        
        generation_time = (time.time() - generation_start) * 1000
        
        logger.info(f"✓ Generated answer in {generation_time:.2f}ms")
        
        # ===== BUILD RESPONSE =====
        total_time = (time.time() - start_time) * 1000
        
        # Build sources
        sources = []
        for section in sections:
            sources.append({
                "section_id": section.get("section_id"),
                "title": section.get("title"),
                "hierarchy_path": section.get("hierarchy_path"),
                "text_preview": section.get("text", "") ,
                "score": section.get("rerank_score", section.get("score", 0))
            })
        
        # Build complete metadata
        metadata = {
            **retrieval_metadata,
            "generation_time_ms": generation_time,
            "total_time_ms": total_time,
            "num_sources": len(sources),
            "answer_length": len(answer)
        }
        
        logger.info("="*80)
        logger.info(f"✓ PIPELINE COMPLETED in {total_time:.2f}ms")
        logger.info(f"  Retrieval: {retrieval_time:.2f}ms")
        logger.info(f"  Generation: {generation_time:.2f}ms")
        logger.info(f"  Answer: {len(answer)} chars")
        logger.info("="*80)
        
        return {
            "answer": answer,
            "sources": sources,
            "metadata": metadata
        }
    
    async def run_with_streaming(
        self,
        query: str,
        major: Optional[str] = None,
        top_k: int = 10,
        enable_reranking: bool = None,
        enable_query_expansion: bool = None,
        search_mode: str = None
    ):
        """
        Execute pipeline with streaming generation
        
        Args:
            query: User query text
            major: Optional major filter
            top_k: Number of results to retrieve
            enable_reranking: Override global reranking setting
            enable_query_expansion: Override global expansion setting
            search_mode: Search mode ("vector", "fulltext", "hybrid") - uses config default if None
        
        Returns:
            AsyncGenerator that yields:
                - {"type": "metadata", "data": {...}}
                - {"type": "sources", "data": [...]}
                - {"type": "answer_chunk", "data": "ragtext"}
                - {"type": "done"}
        """
        start_time = time.time()
        
        # Use config defaults
        if enable_reranking is None:
            enable_reranking = settings.enable_reranking
        if enable_query_expansion is None:
            enable_query_expansion = settings.enable_query_expansion
        
        # Phase 1: Retrieval
        sections, retrieval_metadata = await intent_engine.run(
            query=query,
            major=major,
            enable_reranking=enable_reranking,
            search_mode=search_mode
        )
        
        # Yield metadata
        yield {
            "type": "metadata",
            "data": retrieval_metadata
        }
        
        if not sections:
            yield {
                "type": "answer_chunk",
                "data": "Xin lỗi, tôi không tìm thấy thông tin phù hợp để trả lời câu hỏi của bạn."
            }
            yield {"type": "done"}
            return
        
        # Yield sources
        sources = []
        for section in sections:
            sources.append({
                "section_id": section.get("section_id"),
                "title": section.get("title"),
                "hierarchy_path": section.get("hierarchy_path"),
                "text_preview": section.get("text", ""),
                "score": section.get("rerank_score", section.get("score", 0))
            })
        
        yield {
            "type": "sources",
            "data": sources
        }
        
        # Phase 2: Generation (streaming)
        intent_str = retrieval_metadata["intent"]
        intent = QueryIntent(intent_str)
        
        prompt = self.prompt_generator.generate_answer_prompt(
            query=query,
            sections=sections,
            intent=intent
        )
        
        # Stream answer chunks
        
        if settings.use_openai and settings.openai_api_key:
            async for chunk in openai_client.generate_answer_stream(prompt):
                yield {
                    "type": "answer_chunk",
                    "data": chunk
                }
        else:
            # Ollama streaming
            async for chunk in ollama_client.generate_answer_stream(prompt):
                yield {
                    "type": "answer_chunk",
                    "data": chunk
                }
        
        # Done
        total_time = (time.time() - start_time) * 1000
        yield {
            "type": "done",
            "data": {
                "total_time_ms": total_time
            }
        }


# Global pipeline instance
rag_pipeline = IntentBasedRAGPipeline()
