"""
Test script for querying the RAG system
Usage: .venv/bin/python test_query.py
"""
import asyncio
import sys
import logging
import json

# Add parent directory to path
sys.path.insert(0, '/Users/admin/Documents/School/backend-support')

from app.core.config import settings
from app.clients.elasticsearch import es_client
from app.query.pipeline import run_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_query(query: str, major: str = None):
    """Test a single query"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Query: {query}")
    if major:
        logger.info(f"Major filter: {major}")
    logger.info(f"{'='*60}\n")
    
    try:
        response = await run_query(
            query=query,
            major=major,
            top_k=10,
            enable_reranking= False,
            include_sources=True
        )
        
        # Print answer
        logger.info("📝 ANSWER:")
        logger.info(f"{response.answer}\n")
        
        # Print sources
        if response.sources:
            logger.info("📚 SOURCES:")
            for i, source in enumerate(response.sources, 1):
                logger.info(f"\n  {i}. {source.title}")
                logger.info(f"     Path: {source.hierarchy_path}")
                logger.info(f"     Score: {source.score:.4f}")
                logger.info(f"     Preview: {source.text_preview[:100]}...")
        
        # Print metadata
        logger.info(f"\n📊 METADATA:")
        logger.info(f"  - Major used: {response.metadata.major_used}")
        logger.info(f"  - Chunks retrieved: {response.metadata.chunks_retrieved}")
        logger.info(f"  - Sections retrieved: {response.metadata.sections_retrieved}")
        logger.info(f"  - Total time: {response.metadata.total_time_ms:.2f}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run test queries"""
    
    # Connect to Elasticsearch
    logger.info("Connecting to Elasticsearch...")
    await es_client.connect()
    
    # Test queries
    queries = [
        {
            "query": "Dữ liệu lớn học mấy tín chỉ",
        },
    ]
    
    for i, test_case in enumerate(queries, 1):
        logger.info(f"\n\n{'#'*70}")
        logger.info(f"# TEST CASE {i}")
        logger.info(f"{'#'*70}")
        
        await test_query(
            query=test_case["query"],
        )
        
        await asyncio.sleep(1)  # Small delay between queries
    
    # Close connection
    await es_client.close()
    logger.info("\n\n✅ All tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
