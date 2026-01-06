"""
Unit test for OVERVIEW intent with CNTT program queries
Tests 3 specific queries about Công nghệ thông tin:
1. Các khối kiến thức
2. Hình thức và thời gian học
3. Nghề nghiệp
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.query.intent_based_retrieval_engine import IntentBasedRetrievalEngine
from app.clients.elasticsearch import es_client

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


TEST_QUERIES = [
    {
        "query": "Các khối kiến thức công nghệ thông tin",
        "expected_sections": ["Tỷ lệ các khối kiến thức", "Các khối kiến thức", "Khối kiến thức"]
    },
    {
        "query": "Hình thức và thời gian học công nghệ thông tin",
        "expected_sections": ["Hình thức và thời gian đào tạo", "Thời gian đào tạo"]
    },
    {
        "query": "Nghề nghiệp của công nghệ thông tin",
        "expected_sections": ["Cơ hội nghề nghiệp", "Vị trí và khả năng làm việc sau tốt nghiệp"]
    },
    {
        "query": "Thông tin chung của môn Hoạch định doanh nghiệp",
        "expected_sections": ["Tỷ lệ các khối kiến thức", "Các khối kiến thức", "Khối kiến thức"]
    },
    {
        "query": "Mô tả chung của môn Hoạch định doanh nghiệp",
        "expected_sections": ["Hình thức và thời gian đào tạo", "Thời gian đào tạo"]
    },
    {
        "query": "Kế hoạch giảng dạy của môn Hoạch định doanh nghiệp",
        "expected_sections": ["Cơ hội nghề nghiệp", "Vị trí và khả năng làm việc sau tốt nghiệp"]
    }
]


async def test_cntt_overview_queries():
    """Test OVERVIEW retrieval for CNTT program queries"""
    
    await es_client.connect()
    engine = IntentBasedRetrievalEngine()
    
    logger.info("=" * 70)
    logger.info("CNTT OVERVIEW RETRIEVAL TEST")
    logger.info("=" * 70)
    
    results = []
    
    for i, tc in enumerate(TEST_QUERIES, 1):
        query = tc["query"]
        expected = tc["expected_sections"]
        
        logger.info(f"\n[Test {i}] Query: '{query}'")
        logger.info(f"Expected sections: {expected}")
        
        try:
            # Run retrieval
            sections, intent = await engine.retrieve(query, major=None, enable_reranking=True)
            
            logger.info(f"Intent: {intent.value}")
            logger.info(f"Retrieved {len(sections)} sections:")
            
            # Check results
            found_expected = False
            for j, section in enumerate(sections[:5]):
                title = section.get("title", "N/A")
                path = section.get("hierarchy_path", "N/A")
                logger.info(f"  [{j+1}] {title}")
                logger.info(f"      Path: {path}")
                
                # Check if any expected section is found
                for exp in expected:
                    if exp.lower() in title.lower() or exp.lower() in path.lower():
                        found_expected = True
            
            if found_expected:
                logger.info(f"✓ PASS: Found expected section(s)")
            else:
                logger.warning(f"✗ FAIL: No expected sections found")
            
            results.append({
                "query": query,
                "intent": intent.value,
                "num_sections": len(sections),
                "found_expected": found_expected,
                "sections": [s.get("title") for s in sections[:5]]
            })
            
        except Exception as e:
            logger.error(f"Error: {e}")
            results.append({
                "query": query,
                "error": str(e),
                "found_expected": False
            })
    
    await es_client.close()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for r in results if r.get("found_expected", False))
    logger.info(f"Passed: {passed}/{len(results)}")
    
    for r in results:
        status = "✓" if r.get("found_expected") else "✗"
        logger.info(f"{status} {r['query'][:40]}...")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_cntt_overview_queries())
