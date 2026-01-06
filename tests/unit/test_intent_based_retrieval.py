"""
Unit Tests for Intent-Based Retrieval Engine
Tests với các câu hỏi từ RETRIEVAL_OPTIMIZATION_ANALYSIS.md
"""
import asyncio
import pytest
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, List

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.query.intent_based_retrieval_engine import intent_engine
from app.query.intent_based_prompt_engine import QueryIntent
from app.clients.elasticsearch import es_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test cases from RETRIEVAL_OPTIMIZATION_ANALYSIS.md
CHUNK_LEVEL_QUERIES = [
    {
        "query": "Môn EC213 học bao nhiêu tín chỉ?",
        "expected_intent": QueryIntent.CHUNK_LEVEL,
        "expected_keywords": ["số tín chỉ", "thông tin chung", "lý thuyết", "thực hành"],
        "major": None,
        "description": "Simple factual query about course credits"
    },
    {
        "query": "Điều kiện tốt nghiệp ngành CNTT là gì?",
        "expected_intent": QueryIntent.CHUNK_LEVEL,
        "expected_keywords": ["điều kiện tốt nghiệp", "tín chỉ", "yêu cầu"],
        "major": "CNTT",
        "description": "Factual query about graduation requirements"
    },
    {
        "query": "Học kỳ 3 học những môn gì?",
        "expected_intent": QueryIntent.CHUNK_LEVEL,
        "expected_keywords": ["học kỳ 3", "kế hoạch giảng dạy", "môn học"],
        "major": "CNTT",
        "description": "List query about semester courses"
    },
    {
        "query": "IT004 là môn gì?",
        "expected_intent": QueryIntent.CHUNK_LEVEL,
        "expected_keywords": ["IT004", "tên môn", "cơ sở dữ liệu"],
        "major": None,
        "description": "Query about specific course name"
    },
    {
        "query": "Thời gian đào tạo ngành CNTT là bao lâu?",
        "expected_intent": QueryIntent.CHUNK_LEVEL,
        "expected_keywords": ["thời gian đào tạo", "số năm", "học kỳ"],
        "major": "CNTT",
        "description": "Query about program duration"
    }
]

SECTION_LEVEL_QUERIES = [
    {
        "query": "Môn EC213 học những gì?",
        "expected_intent": QueryIntent.SECTION_LEVEL,
        "expected_keywords": ["nội dung môn học", "kế hoạch giảng dạy", "mô tả", "mục tiêu"],
        "major": None,
        "description": "Overview query about course content"
    },
    {
        "query": "Cơ sở ngành của CNTT học những gì?",
        "expected_intent": QueryIntent.SECTION_LEVEL,
        "expected_keywords": ["cơ sở ngành", "nhóm môn học cơ sở ngành", "khối kiến thức chuyên nghiệp"],
        "major": "CNTT",
        "description": "Query about foundation courses"
    },
    {
        "query": "Chuyên ngành Hệ thống thông tin học gì?",
        "expected_intent": QueryIntent.SECTION_LEVEL,
        "expected_keywords": ["chuyên ngành", "hệ thống thông tin", "môn học chuyên ngành"],
        "major": "HTTT",
        "description": "Query about major specialization content"
    },
    {
        "query": "Nội dung môn IT004 gồm những gì?",
        "expected_intent": QueryIntent.SECTION_LEVEL,
        "expected_keywords": ["IT004", "nội dung môn học", "chương"],
        "major": None,
        "description": "Query about detailed course content"
    }
]

HIERARCHICAL_QUERIES = [
    {
        "query": "Ngành Công Nghệ Thông Tin học những gì?",
        "expected_intent": QueryIntent.HIERARCHICAL,
        "expected_keywords": ["các khối kiến thức", "chương trình đào tạo", "cơ sở ngành", "chuyên ngành"],
        "major": "CNTT",
        "description": "Hierarchical query about entire major"
    },
    {
        "query": "Chương trình đào tạo CNTT gồm những gì?",
        "expected_intent": QueryIntent.HIERARCHICAL,
        "expected_keywords": ["chương trình đào tạo", "các khối kiến thức", "cấu trúc"],
        "major": "CNTT",
        "description": "Query about program structure"
    },
    {
        "query": "Các khối kiến thức của ngành TTNT?",
        "expected_intent": QueryIntent.HIERARCHICAL,
        "expected_keywords": ["các khối kiến thức", "đại cương", "chuyên nghiệp", "tốt nghiệp"],
        "major": "TTNT",
        "description": "Query about knowledge blocks"
    }
]


class TestIntentDetection:
    """Test intent detection for different query types"""
    
    @pytest.mark.asyncio
    async def test_chunk_level_intent_detection(self):
        """Test that chunk-level queries are correctly identified"""
        for test_case in CHUNK_LEVEL_QUERIES:
            logger.info(f"\nTesting CHUNK_LEVEL: {test_case['query']}")
            
            from app.query.intent_based_prompt_engine import IntentDetector
            detector = IntentDetector()
            
            result = await detector.detect(test_case["query"])
            
            assert result["intent"] == test_case["expected_intent"], \
                f"Expected {test_case['expected_intent']}, got {result['intent']}"
            
            logger.info(f"✓ Intent: {result['intent'].value}")
            logger.info(f"  Reasoning: {result['reasoning']}")
            logger.info(f"  Keywords: {result['expansion_keywords']}")
    
    @pytest.mark.asyncio
    async def test_section_level_intent_detection(self):
        """Test that section-level queries are correctly identified"""
        for test_case in SECTION_LEVEL_QUERIES:
            logger.info(f"\nTesting SECTION_LEVEL: {test_case['query']}")
            
            from app.query.intent_based_prompt_engine import IntentDetector
            detector = IntentDetector()
            
            result = await detector.detect(test_case["query"])
            
            assert result["intent"] == test_case["expected_intent"], \
                f"Expected {test_case['expected_intent']}, got {result['intent']}"
            
            logger.info(f"✓ Intent: {result['intent'].value}")
            logger.info(f"  Reasoning: {result['reasoning']}")
    
    @pytest.mark.asyncio
    async def test_hierarchical_intent_detection(self):
        """Test that hierarchical queries are correctly identified"""
        for test_case in HIERARCHICAL_QUERIES:
            logger.info(f"\nTesting HIERARCHICAL: {test_case['query']}")
            
            from app.query.intent_based_prompt_engine import IntentDetector
            detector = IntentDetector()
            
            result = await detector.detect(test_case["query"])
            
            assert result["intent"] == test_case["expected_intent"], \
                f"Expected {test_case['expected_intent']}, got {result['intent']}"
            
            logger.info(f"✓ Intent: {result['intent'].value}")
            logger.info(f"  Reasoning: {result['reasoning']}")


class TestQueryExpansion:
    """Test query expansion based on intent"""
    
    @pytest.mark.asyncio
    async def test_chunk_level_expansion(self):
        """Test expansion for chunk-level queries"""
        from app.query.intent_based_prompt_engine import SchemaAwareExpander
        expander = SchemaAwareExpander()
        
        test_case = CHUNK_LEVEL_QUERIES[0]  # "Môn EC213 học bao nhiêu tín chỉ?"
        
        expanded = await expander.expand(
            query=test_case["query"],
            intent=test_case["expected_intent"],
            keywords=["số tín chỉ", "EC213"],
            major=test_case["major"]
        )
        
        logger.info(f"\nOriginal: {test_case['query']}")
        logger.info(f"Expanded: {expanded}")
        
        assert test_case["query"] in expanded, "Original query should be in expanded query"
        assert len(expanded) > len(test_case["query"]), "Expanded query should be longer"
    
    @pytest.mark.asyncio
    async def test_section_level_expansion(self):
        """Test expansion for section-level queries"""
        from app.query.intent_based_prompt_engine import SchemaAwareExpander
        expander = SchemaAwareExpander()
        
        test_case = SECTION_LEVEL_QUERIES[0]  # "Môn EC213 học những gì?"
        
        expanded = await expander.expand(
            query=test_case["query"],
            intent=test_case["expected_intent"],
            keywords=["nội dung", "EC213"],
            major=test_case["major"]
        )
        
        logger.info(f"\nOriginal: {test_case['query']}")
        logger.info(f"Expanded: {expanded}")
        
        assert test_case["query"] in expanded


class TestIntentBasedRetrieval:
    """Test full intent-based retrieval pipeline"""
    
    @pytest.mark.asyncio
    async def test_chunk_level_retrieval(self):
        """Test retrieval for chunk-level queries"""
        await es_client.connect()
        
        try:
            for test_case in CHUNK_LEVEL_QUERIES[:2]:  # Test first 2
                logger.info(f"\n{'='*80}")
                logger.info(f"Testing: {test_case['description']}")
                logger.info(f"Query: {test_case['query']}")
                logger.info(f"{'='*80}")
                
                sections, metadata = await intent_engine.run(
                    query=test_case["query"],
                    major=test_case["major"],
                    top_k=5,
                    enable_reranking=False,
                    enable_query_expansion=True
                )
                
                # Assertions
                assert metadata["intent"] == test_case["expected_intent"].value, \
                    f"Expected intent {test_case['expected_intent'].value}, got {metadata['intent']}"
                
                assert len(sections) > 0, "Should retrieve at least one section"
                
                logger.info(f"\n✓ Retrieved {len(sections)} sections")
                logger.info(f"  Intent: {metadata['intent']}")
                logger.info(f"  Time: {metadata['time_ms']:.2f}ms")
                
                # Print top 3 results
                for i, section in enumerate(sections[:3], 1):
                    logger.info(f"\n  {i}. {section.get('title', 'No title')}")
                    logger.info(f"     Path: {section.get('hierarchy_path', 'N/A')}")
                    logger.info(f"     Score: {section.get('score', 0):.4f}")
        
        finally:
            await es_client.close()
    
    @pytest.mark.asyncio
    async def test_section_level_retrieval(self):
        """Test retrieval for section-level queries"""
        await es_client.connect()
        
        try:
            for test_case in SECTION_LEVEL_QUERIES[:2]:  # Test first 2
                logger.info(f"\n{'='*80}")
                logger.info(f"Testing: {test_case['description']}")
                logger.info(f"Query: {test_case['query']}")
                logger.info(f"{'='*80}")
                
                sections, metadata = await intent_engine.run(
                    query=test_case["query"],
                    major=test_case["major"],
                    top_k=5,
                    enable_reranking=False,
                    enable_query_expansion=True
                )
                
                # Assertions
                assert metadata["intent"] == test_case["expected_intent"].value
                assert len(sections) > 0, "Should retrieve at least one section"
                
                logger.info(f"\n✓ Retrieved {len(sections)} sections")
                logger.info(f"  Intent: {metadata['intent']}")
                logger.info(f"  Time: {metadata['time_ms']:.2f}ms")
                
                # Print results
                for i, section in enumerate(sections[:3], 1):
                    logger.info(f"\n  {i}. {section.get('title', 'No title')}")
                    logger.info(f"     Path: {section.get('hierarchy_path', 'N/A')}")
        
        finally:
            await es_client.close()
    
    @pytest.mark.asyncio
    async def test_hierarchical_retrieval(self):
        """Test retrieval for hierarchical queries"""
        await es_client.connect()
        
        try:
            for test_case in HIERARCHICAL_QUERIES[:2]:  # Test first 2
                logger.info(f"\n{'='*80}")
                logger.info(f"Testing: {test_case['description']}")
                logger.info(f"Query: {test_case['query']}")
                logger.info(f"{'='*80}")
                
                sections, metadata = await intent_engine.run(
                    query=test_case["query"],
                    major=test_case["major"],
                    top_k=5,
                    enable_reranking=False,
                    enable_query_expansion=True
                )
                
                # Assertions
                assert metadata["intent"] == test_case["expected_intent"].value
                assert len(sections) > 0, "Should retrieve at least one section"
                
                # For hierarchical queries, expect multiple sections with hierarchy
                logger.info(f"\n✓ Retrieved {len(sections)} sections (hierarchical)")
                logger.info(f"  Intent: {metadata['intent']}")
                logger.info(f"  Time: {metadata['time_ms']:.2f}ms")
                
                # Print hierarchy structure
                for i, section in enumerate(sections[:5], 1):
                    logger.info(f"\n  {i}. {section.get('title', 'No title')}")
                    logger.info(f"     Level: {section.get('level', 'N/A')}")
                    logger.info(f"     Path: {section.get('hierarchy_path', 'N/A')}")
        
        finally:
            await es_client.close()


class TestRetrievalComparison:
    """Compare old vs new retrieval engine"""
    
    @pytest.mark.asyncio
    async def test_comparison_chunk_query(self):
        """Compare old and new engine on chunk-level query"""
        try:
            from app.query.retrieval_engine import engine as old_engine
        except ImportError:
            pytest.skip("Old engine not available")
            return
        
        await es_client.connect()
        
        try:
            test_query = "Môn EC213 học bao nhiêu tín chỉ?"
            
            # Old engine
            logger.info("\n" + "="*80)
            logger.info("OLD ENGINE (chunk-based)")
            logger.info("="*80)
            old_sections = await old_engine.run(
                query=test_query,
                major=None,
                top_k=5,
                enable_reranking=False,
                enable_query_expansion=False
            )
            
            # New engine
            logger.info("\n" + "="*80)
            logger.info("NEW ENGINE (intent-based)")
            logger.info("="*80)
            new_sections, metadata = await intent_engine.run(
                query=test_query,
                major=None,
                top_k=5,
                enable_reranking=False,
                enable_query_expansion=True
            )
            
            # Comparison
            logger.info(f"\n{'='*80}")
            logger.info("COMPARISON")
            logger.info(f"{'='*80}")
            logger.info(f"Old engine: {len(old_sections)} sections")
            logger.info(f"New engine: {len(new_sections)} sections")
            logger.info(f"Detected intent: {metadata['intent']}")
            logger.info(f"Expanded query: {metadata['expanded_query']}")
            
            # Both should retrieve results
            assert len(old_sections) > 0
            assert len(new_sections) > 0
        
        finally:
            await es_client.close()
    
    @pytest.mark.asyncio
    async def test_comparison_hierarchical_query(self):
        """Compare old and new engine on hierarchical query"""
        try:
            from app.query.retrieval_engine import engine as old_engine
        except ImportError:
            pytest.skip("Old engine not available")
            return
        
        await es_client.connect()
        
        try:
            test_query = "Ngành Công Nghệ Thông Tin học những gì?"
            
            # Old engine
            logger.info("\n" + "="*80)
            logger.info("OLD ENGINE")
            logger.info("="*80)
            old_sections = await old_engine.run(
                query=test_query,
                major="CNTT",
                top_k=10,
                enable_reranking=False,
                enable_query_expansion=False
            )
            
            # New engine
            logger.info("\n" + "="*80)
            logger.info("NEW ENGINE")
            logger.info("="*80)
            new_sections, metadata = await intent_engine.run(
                query=test_query,
                major="CNTT",
                top_k=10,
                enable_reranking=False,
                enable_query_expansion=True
            )
            
            # Comparison
            logger.info(f"\n{'='*80}")
            logger.info("COMPARISON")
            logger.info(f"{'='*80}")
            logger.info(f"Old engine: {len(old_sections)} sections")
            logger.info(f"New engine: {len(new_sections)} sections (hierarchical expansion)")
            logger.info(f"Detected intent: {metadata['intent']}")
            
            # New engine should retrieve more sections due to hierarchy expansion
            logger.info(f"\nExpected: New engine retrieves more sections for overview queries")
            logger.info(f"Result: Old={len(old_sections)}, New={len(new_sections)}")
        
        finally:
            await es_client.close()


# Standalone test runner
async def run_all_tests():
    """Run all tests manually"""
    logger.info("\n" + "="*80)
    logger.info("INTENT-BASED RETRIEVAL ENGINE - UNIT TESTS")
    logger.info("="*80)
    
    # Test 1: Intent Detection
    logger.info("\n\n### TEST SUITE 1: INTENT DETECTION ###")
    test_intent = TestIntentDetection()
    
    logger.info("\n--- Testing CHUNK_LEVEL queries ---")
    await test_intent.test_chunk_level_intent_detection()
    
    logger.info("\n--- Testing SECTION_LEVEL queries ---")
    await test_intent.test_section_level_intent_detection()
    
    logger.info("\n--- Testing HIERARCHICAL queries ---")
    await test_intent.test_hierarchical_intent_detection()
    
    # Test 2: Query Expansion
    logger.info("\n\n### TEST SUITE 2: QUERY EXPANSION ###")
    test_expansion = TestQueryExpansion()
    
    logger.info("\n--- Testing CHUNK_LEVEL expansion ---")
    await test_expansion.test_chunk_level_expansion()
    
    logger.info("\n--- Testing SECTION_LEVEL expansion ---")
    await test_expansion.test_section_level_expansion()
    
    # Test 3: Full Retrieval Pipeline
    logger.info("\n\n### TEST SUITE 3: RETRIEVAL PIPELINE ###")
    test_retrieval = TestIntentBasedRetrieval()
    
    logger.info("\n--- Testing CHUNK_LEVEL retrieval ---")
    await test_retrieval.test_chunk_level_retrieval()
    
    logger.info("\n--- Testing SECTION_LEVEL retrieval ---")
    await test_retrieval.test_section_level_retrieval()
    
    logger.info("\n--- Testing HIERARCHICAL retrieval ---")
    await test_retrieval.test_hierarchical_retrieval()
    
    # Test 4: Comparison with old engine
    logger.info("\n\n### TEST SUITE 4: COMPARISON OLD vs NEW ###")
    test_comparison = TestRetrievalComparison()
    
    logger.info("\n--- Comparing on chunk-level query ---")
    await test_comparison.test_comparison_chunk_query()
    
    logger.info("\n--- Comparing on hierarchical query ---")
    await test_comparison.test_comparison_hierarchical_query()
    
    logger.info("\n\n" + "="*80)
    logger.info("✓ ALL TESTS COMPLETED")
    logger.info("="*80)


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())
