"""
Unit tests for SchemaAwareExpander
Tests query expansion based on intent using queries from tests/query.json
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.query.intent_based_prompt_engine import SchemaAwareExpander
from app.retrieval_engine.intent_detection import QueryIntent, detect_intent

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_test_queries() -> list:
    """Load test queries from tests/query.json"""
    query_file = Path(__file__).parent.parent / "query.json"
    with open(query_file, 'r', encoding='utf-8') as f:
        return json.load(f)


async def test_schema_aware_expansion():
    """Test SchemaAwareExpander with all queries from query.json"""
    
    # Load test queries
    test_queries = load_test_queries()
    logger.info(f"Loaded {len(test_queries)} test queries")
    
    # Initialize expander
    expander = SchemaAwareExpander()
    
    # Group queries by intent
    intent_groups = {}
    for q in test_queries:
        intent = q["expected_intent"]
        if intent not in intent_groups:
            intent_groups[intent] = []
        intent_groups[intent].append(q["original"])
    
    logger.info("=" * 70)
    logger.info("SCHEMA-AWARE EXPANSION TEST")
    logger.info("=" * 70)
    
    results = []
    
    # Test each intent group
    for intent_name, queries in intent_groups.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"INTENT: {intent_name.upper()} ({len(queries)} queries)")
        logger.info("="*60)
        
        # Map string to enum
        intent_map = {
            "factual": QueryIntent.FACTUAL,
            "overview": QueryIntent.OVERVIEW,
            "roadmap": QueryIntent.ROADMAP,
            "compare": QueryIntent.COMPARE,
            "structure": QueryIntent.STRUCTURE,
        }
        intent_enum = intent_map.get(intent_name, QueryIntent.STRUCTURE)
        
        # Test first 3 queries per intent
        for i, query in enumerate(queries[:3]):
            logger.info(f"\n[{i+1}] Original: '{query}'")
            
            try:
                expanded = await expander.expand(query, intent_enum)
                logger.info(f"    Expanded: '{expanded}'")
                
                results.append({
                    "query": query,
                    "intent": intent_name,
                    "expanded": expanded,
                    "success": True
                })
            except Exception as e:
                logger.error(f"    Error: {e}")
                results.append({
                    "query": query,
                    "intent": intent_name,
                    "error": str(e),
                    "success": False
                })
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Total queries tested: {len(results)}")
    logger.info(f"Successful expansions: {success_count}/{len(results)}")
    
    # Show sample expansions
    logger.info("\n--- Sample Expansions ---")
    for intent_name in intent_groups.keys():
        intent_results = [r for r in results if r["intent"] == intent_name and r["success"]]
        if intent_results:
            sample = intent_results[0]
            logger.info(f"\n[{intent_name.upper()}]")
            logger.info(f"  Query: {sample['query'][:50]}...")
            logger.info(f"  Expanded: {sample['expanded'][:80]}...")
    
    return results


async def test_expansion_quality():
    """Test that expansions contain relevant keywords for each intent"""
    
    expander = SchemaAwareExpander()
    
    # Test cases with expected keywords
    test_cases = [
        {
            "query": "Ngành CNTT học những gì?",
            "intent": QueryIntent.OVERVIEW,
            "expected_keywords": ["Mục tiêu đào tạo", "khối kiến thức", "MÔ TẢ"]
        },
        {
            "query": "Học kỳ 1 ngành AI học những môn gì?",
            "intent": QueryIntent.ROADMAP,
            "expected_keywords": ["KẾ HOẠCH GIẢNG DẠY", "Học kỳ", "Học kì"]
        },
        {
            "query": "Môn tiên quyết của Dữ Liệu Lớn là gì?",
            "intent": QueryIntent.FACTUAL,
            "expected_keywords": ["THÔNG TIN CHUNG", "tiên quyết", "Môn học trước"]
        },
        {
            "query": "Điểm đánh giá môn Cơ sở dữ liệu như thế nào?",
            "intent": QueryIntent.STRUCTURE,
            "expected_keywords": ["ĐÁNH GIÁ", "CHUẨN ĐẦU RA"]
        },
    ]
    
    logger.info("\n" + "=" * 70)
    logger.info("EXPANSION QUALITY TEST")
    logger.info("=" * 70)
    
    for tc in test_cases:
        logger.info(f"\nIntent: {tc['intent'].value}")
        logger.info(f"Query: {tc['query']}")
        
        expanded = await expander.expand(tc['query'], tc['intent'])
        logger.info(f"Expanded: {expanded}")
        
        # Check if any expected keyword is present
        found_keywords = [kw for kw in tc['expected_keywords'] 
                        if kw.lower() in expanded.lower()]
        
        if found_keywords:
            logger.info(f"✓ Found keywords: {found_keywords}")
        else:
            logger.warning(f"✗ No expected keywords found. Expected: {tc['expected_keywords']}")


if __name__ == "__main__":
    logger.info("Starting SchemaAwareExpander tests...")
    
    # Run tests
    asyncio.run(test_schema_aware_expansion())
    asyncio.run(test_expansion_quality())
    
    logger.info("\n✓ Tests completed")
