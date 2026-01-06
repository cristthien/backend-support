"""
Test retrieval engine with various queries
"""
import asyncio
import logging
from typing import Optional

from app.query.retrieval_engine import engine as retrieval_engine
from app.clients.elasticsearch import es_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_retrieval_query(
    query: str,
    major: Optional[str] = None,
    top_k: int = 10,
    enable_reranking: bool = None,
    enable_query_expansion: bool = None
):
    """
    Test retrieval engine with a specific query
    
    Args:
        query: User query text
        major: Optional major filter
        top_k: Number of chunks to retrieve
        enable_reranking: Override global reranking setting
        enable_query_expansion: Override global expansion setting
    """
    logger.info("="*80)
    logger.info("TESTING QUERY: %s", query)
    logger.info("Major: %s | Top K: %d | Reranking: %s | Expansion: %s",
                major, top_k, enable_reranking, enable_query_expansion)
    logger.info("="*80)
    
    try:
        # Connect to Elasticsearch
        await es_client.connect()
        
        # Run retrieval engine
        sections = await retrieval_engine.run(
            query=query,
            major=major,
            top_k=top_k,
            enable_reranking=enable_reranking,
            enable_query_expansion=enable_query_expansion
        )
        
        # Print results
        print(f"\n{'='*80}")
        print(f"RESULTS: {len(sections)} sections retrieved")
        print(f"{'='*80}\n")
        
        for i, section in enumerate(sections, 1):
            print(f"{i}. {section.get('title', 'No title')}")
            print(f"   Path: {section.get('hierarchy_path', 'No path')}")
            print(f"   Score: {section.get('rerank_score', section.get('score', 0)):.4f}")
            print(f"   Preview: {section.get('text', '')[:200]}...")
            print()
        
        return sections
        
    finally:
        await es_client.close()


async def run_all_tests():
    """Run multiple test queries"""
    
    test_cases = [
        {
            "name": "Test 1: Overview query with keywords",
            "query": "Ngành Công nghệ thông tin học những gì, các khối kiến thức, CNTT, đại cương, chuyên ngành, cơ sở ngành",
            "major": None,
            "top_k": 10,
            "enable_reranking": True,
            "enable_query_expansion": True
        },
        {
            "name": "Test 2: Specific program question",
            "query": "Chương trình đào tạo ngành CNTT có những khối kiến thức nào?",
            "major": None,
            "top_k": 5,
            "enable_reranking": True,
            "enable_query_expansion": False
        },
        {
            "name": "Test 3: Credits and duration",
            "query": "Ngành công nghệ thông tin học mấy năm và bao nhiêu tín chỉ?",
            "major": None,
            "top_k": 5,
            "enable_reranking": True,
            "enable_query_expansion": True
        },
        {
            "name": "Test 4: Career prospects",
            "query": "Học ngành CNTT ra trường làm gì?",
            "major": None,
            "top_k": 5,
            "enable_reranking": True,
            "enable_query_expansion": True
        },
        {
            "name": "Test 5: Specializations",
            "query": "Ngành công nghệ thông tin có những chuyên ngành nào?",
            "major": None,
            "top_k": 5,
            "enable_reranking": True,
            "enable_query_expansion": True
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n\n{'#'*80}")
        print(f"# {test['name']}")
        print(f"{'#'*80}\n")
        
        await test_retrieval_query(
            query=test['query'],
            major=test.get('major'),
            top_k=test.get('top_k', 10),
            enable_reranking=test.get('enable_reranking'),
            enable_query_expansion=test.get('enable_query_expansion')
        )
        
        # Small delay between tests
        await asyncio.sleep(1)


async def main():
    """Main entry point"""
    # Run single query test
    await test_retrieval_query(
        query="Ngành Công nghệ thông tin học những gì, các khối kiến thức, CNTT, đại cương, chuyên ngành, cơ sở ngành",
        major=None,
        top_k=10,
        enable_reranking=True,
        enable_query_expansion=True
    )
    
    # Uncomment to run all tests
    # await run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
