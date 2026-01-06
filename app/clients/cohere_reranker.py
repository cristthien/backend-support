"""
Cohere Reranker client for multilingual reranking
"""
import cohere
from typing import List, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CohereReranker:
    """Cohere reranker for improving retrieval quality"""
    
    def __init__(self):
        self.client = cohere.ClientV2(api_key=settings.cohere_api_key)
        self.model = settings.cohere_rerank_model
        logger.info(f"Initialized Cohere reranker: {self.model}")
    
    async def rerank_sections(
        self,
        query: str,
        sections: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank sections based on relevance to query
        
        Args:
            query: User query text
            sections: List of section dictionaries with 'text' field
            top_n: Number of top results to return
            
        Returns:
            Reranked list of sections with updated scores
        """
        if not sections:
            return []
        
        # Prepare documents for reranking
        documents = []
        for section in sections:
            # Combine title and text for better reranking
            doc_text = f"{section['title']}\n\n{section['text'][:1000]}"  # Limit text length
            documents.append(doc_text)
        
        logger.info(f"Reranking {len(documents)} sections with query: '{query[:50]}...'")
        
        try:
            # Call Cohere rerank API
            response = self.client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=min(top_n, len(documents)),
                return_documents=False  # We already have the documents
            )
            
            # Map reranked results back to original sections
            reranked_sections = []
            for result in response.results:
                idx = result.index
                section = sections[idx].copy()
                section['rerank_score'] = result.relevance_score
                reranked_sections.append(section)
            
            logger.info(f"Reranking complete: top score = {reranked_sections[0]['rerank_score']:.4f}")
            return reranked_sections
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}, returning original sections")
            # Fallback to original sections if reranking fails
            return sections[:top_n]
    
    async def rerank_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks based on relevance to query
        
        Args:
            query: User query text
            chunks: List of chunk dictionaries with 'text' field
            top_n: Number of top results to return
            
        Returns:
            Reranked list of chunks with updated scores
        """
        if not chunks:
            return []
        
        # Prepare documents for reranking
        documents = []
        for chunk in chunks:
            # Use chunk text directly, limit to 1000 characters for efficiency
            doc_text = chunk.get('text', '')[:1000]
            documents.append(doc_text)
        
        logger.info(f"Reranking {len(documents)} chunks with query: '{query[:50]}...'")
        
        try:
            # Call Cohere rerank API
            response = self.client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=min(top_n, len(documents)),
                return_documents=False  # We already have the documents
            )
            
            # Map reranked results back to original chunks
            reranked_chunks = []
            for result in response.results:
                idx = result.index
                chunk = chunks[idx].copy()
                chunk['rerank_score'] = result.relevance_score
                reranked_chunks.append(chunk)
            
            logger.info(f"Reranking complete: top score = {reranked_chunks[0]['rerank_score']:.4f}")
            return reranked_chunks
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}, returning original chunks")
            # Fallback to original chunks if reranking fails
            return chunks[:top_n]


# Global reranker instance
cohere_reranker = CohereReranker()
