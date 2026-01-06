"""
Data ingestion pipeline with H1-based major extraction
"""
import asyncio
import json
from typing import List, Dict, Any
from pathlib import Path
import logging

from app.core.config import settings
from app.clients.ollama import ollama_client
from app.clients.elasticsearch import es_client

logger = logging.getLogger(__name__)


def extract_major_from_sections(sections: List[Dict]) -> str:
    """
    Extract major from first H1 heading (level=1)
    
    Args:
        sections: List of section dictionaries
        
    Returns:
        Major name from H1 heading or 'UNKNOWN'
        
    Examples:
        H1: "Ngành Công Nghệ Thông Tin" → "Ngành Công Nghệ Thông Tin"
    """
    for section in sections:
        if section.get('level') == 1:
            major = section.get('title', 'UNKNOWN')
            logger.info("Extracted major from H1: %s", major)
            return major
    
    logger.warning("No H1 heading found, using UNKNOWN")
    return 'UNKNOWN'


async def process_sections(
    sections: List[Dict],
    major: str,
) -> List[Dict[str, Any]]:
    """
    Process sections: add major field and generate embeddings SEQUENTIALLY
    
    Args:
        sections: Raw sections from simple-output.json
        major: Major name extracted from H1
        batch_size: Not used anymore - kept for compatibility
        
    Returns:
        Processed sections with embeddings and major field
    """
    processed_sections = []
    
    total = len(sections)
    for i, section in enumerate(sections, 1):
        logger.info("Generating embedding for section %d/%d: %s...", i, total, section['title'][:50])
        
        # Retry logic for embedding
        max_retries = 3
        for attempt in range(max_retries):
            try:
                embedding = await ollama_client.generate_embedding(section['title'])
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("Retry %d/%d for section %d", attempt + 1, max_retries, i)
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    logger.error("Failed after %d retries: %s", max_retries, e)
                    raise
        
        section_data = {
            **section,
            'major': major,
            'embedding': embedding
        }
        processed_sections.append(section_data)
    
    logger.info("Processed %d sections", len(processed_sections))
    return processed_sections


async def process_chunks(
    chunks: List[Dict],
    major: str,
) -> List[Dict[str, Any]]:
    """
    Process chunks: add major field and generate embeddings SEQUENTIALLY
    
    Args:
        chunks: Raw chunks from simple-output.json
        major: Major name extracted from H1
        batch_size: Not used anymore - kept for compatibility
        
    Returns:
        Processed chunks with embeddings and major field
    """
    processed_chunks = []
    
    # Process ONE BY ONE to avoid Ollama overload
    total = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        logger.info("Generating embedding for chunk %d/%d", i, total)
        
        # Retry logic for embedding
        max_retries = 3
        for attempt in range(max_retries):
            try:
                embedding = await ollama_client.generate_embedding(chunk['text'])
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("Retry %d/%d for chunk %d", attempt + 1, max_retries, i)
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    logger.error("Failed after %d retries: %s", max_retries, e)
                    raise
        
        chunk_data = {
            **chunk,
            'major': major,
            'embedding': embedding
        }
        processed_chunks.append(chunk_data)
    
    logger.info("Processed %d chunks", len(processed_chunks))
    return processed_chunks


async def ingest_data(file_path: str):
    """
    Main ingestion pipeline
    
    Args:
        file_path: Path to simple-output.json file
        
    Flow:
        1. Load simple-output.json
        2. Extract major from H1 heading
        3. Generate embeddings for sections and chunks
        4. Bulk index to Elasticsearch
    """
    logger.info("Starting ingestion from %s", file_path)
    
    # 1. Load data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sections = data.get('sections', [])
    chunks = data.get('chunks', [])
    
    logger.info("Loaded %d sections and %d chunks", len(sections), len(chunks))
    
    # 2. Extract major from H1
    major = extract_major_from_sections(sections)
    
    # 3. Process sections with embeddings
    processed_sections = await process_sections(
        sections,
        major,
    )
    
    # 4. Process chunks with embeddings
    processed_chunks = await process_chunks(
        chunks,
        major,
    )
    
    # 5. Index to Elasticsearch
    logger.info("Indexing sections to Elasticsearch...")
    sections_success, sections_failed = await es_client.bulk_index_sections(processed_sections)
    
    logger.info("Indexing chunks to Elasticsearch...")
    chunks_success, chunks_failed = await es_client.bulk_index_chunks(processed_chunks)
    
    # 6. Return statistics
    stats = {
        "major": major,
        "sections_indexed": sections_success,
        "sections_failed": len(sections_failed),
        "chunks_indexed": chunks_success,
        "chunks_failed": len(chunks_failed)
    }
    
    logger.info("Ingestion complete: %s", stats)
    return stats


