"""
Source Builder: Builds SourceInfo from sections and chunks
"""
import logging
from typing import List, Dict
from app.models.query import SourceInfo

logger = logging.getLogger(__name__)


def build_sources(sections: List[Dict], chunks: List[Dict]) -> List[SourceInfo]:
    """
    Build source information from sections and chunks
    
    Args:
        sections: Retrieved sections
        chunks: Retrieved chunks
        
    Returns:
        List of SourceInfo objects sorted by score
    """
    sources = []
    
    for section in sections:
        # Get best chunk score for this section
        section_chunk_scores = [
            chunk["score"]
            for chunk in chunks
            if chunk["section_id"] == section["section_id"]
        ] if chunks else []
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
    
    logger.info("Built %d sources", len(sources))
    return sources
