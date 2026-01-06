"""
Integration Tests for Intent-Based RAG Pipeline
End-to-end tests: Query → Intent → Retrieval → Generation → Answer
"""
import asyncio
import pytest
import logging
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.query.intent_based_rag_pipeline import rag_pipeline
from app.clients.elasticsearch import es_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Integration test cases
INTEGRATION_TEST_CASES = [
    {
        "name": "CHUNK-1: Factual query - Số tín chỉ",
        "query": "Môn EC213 học bao nhiêu tín chỉ?",
        "major": None,
        "expected_intent": "chunk_level",
        "expected_in_answer": ["tín chỉ", "EC213"],
        "description": "Should return specific number of credits"
    },
    {
        "name": "CHUNK-2: Factual query - Điều kiện tốt nghiệp",
        "query": "Điều kiện tốt nghiệp ngành CNTT là gì?",
        "major": "CNTT",
        "expected_intent": "chunk_level",
        "expected_in_answer": ["125", "tín chỉ"],
        "description": "Should return graduation requirements"
    },
    {
        "name": "SECTION-1: Overview query - Nội dung môn học",
        "query": "Môn EC213 học những gì?",
        "major": None,
        "expected_intent": "section_level",
        "expected_in_answer": ["CRM", "khách hàng"],
        "description": "Should provide course overview"
    },
    {
        "name": "SECTION-2: Overview query - Cơ sở ngành",
        "query": "Cơ sở ngành của CNTT học những gì?",
        "major": "CNTT",
        "expected_intent": "section_level",
        "expected_in_answer": ["lập trình", "cơ sở dữ liệu"],
        "description": "Should list foundation courses"
    },
    {
        "name": "HIERARCHICAL-1: Major overview",
        "query": "Ngành Công Nghệ Thông Tin học những gì?",
        "major": "CNTT",
        "expected_intent": "hierarchical",
        "expected_in_answer": ["khối kiến thức", "đại cương", "chuyên nghiệp"],
        "description": "Should provide structured major overview"
    },
    {
        "name": "HIERARCHICAL-2: Program structure",
        "query": "Chương trình đào tạo CNTT gồm những gì?",
        "major": "CNTT",
        "expected_intent": "hierarchical",
        "expected_in_answer": ["chương trình", "tín chỉ"],
        "description": "Should describe program structure"
    }
]


class TestIntegrationRAGPipeline:
    """Integration tests for complete RAG pipeline"""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_chunk_query(self):
        """Test complete pipeline with chunk-level query"""
        await es_client.connect()
        
        try:
            test_case = INTEGRATION_TEST_CASES[0]  # "Môn EC213 học bao nhiêu tín chỉ?"
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing: {test_case['name']}")
            logger.info(f"Query: {test_case['query']}")
            logger.info(f"{'='*80}")
            
            result = await rag_pipeline.run(
                query=test_case["query"],
                major=test_case["major"],
                top_k=5,
                enable_reranking=False,
                enable_query_expansion=True
            )
            
            # Assertions
            assert "answer" in result
            assert "sources" in result
            assert "metadata" in result
            
            # Check intent
            assert result["metadata"]["intent"] == test_case["expected_intent"]
            
            # Check answer quality
            answer = result["answer"].lower()
            for keyword in test_case["expected_in_answer"]:
                assert keyword.lower() in answer, f"Expected '{keyword}' in answer"
            
            # Check sources
            assert len(result["sources"]) > 0, "Should have at least one source"
            
            logger.info(f"\n✓ Answer generated: {len(result['answer'])} chars")
            logger.info(f"  Intent: {result['metadata']['intent']}")
            logger.info(f"  Sources: {len(result['sources'])}")
            logger.info(f"  Time: {result['metadata']['total_time_ms']:.2f}ms")
            logger.info(f"\n  Answer preview: {result['answer'][:200]}...")
            
        finally:
            await es_client.close()
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_section_query(self):
        """Test complete pipeline with section-level query"""
        await es_client.connect()
        
        try:
            test_case = INTEGRATION_TEST_CASES[2]  # "Môn EC213 học những gì?"
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing: {test_case['name']}")
            logger.info(f"Query: {test_case['query']}")
            logger.info(f"{'='*80}")
            
            result = await rag_pipeline.run(
                query=test_case["query"],
                major=test_case["major"],
                top_k=5,
                enable_reranking=False,
                enable_query_expansion=True
            )
            
            # Assertions
            assert result["metadata"]["intent"] == test_case["expected_intent"]
            
            answer = result["answer"].lower()
            for keyword in test_case["expected_in_answer"]:
                assert keyword.lower() in answer, f"Expected '{keyword}' in answer"
            
            # Section queries should have more comprehensive answers
            assert len(result["answer"]) > 200, "Section query should have detailed answer"
            
            logger.info(f"\n✓ Answer generated: {len(result['answer'])} chars")
            logger.info(f"  Intent: {result['metadata']['intent']}")
            logger.info(f"  Sources: {len(result['sources'])}")
            logger.info(f"\n  Answer preview: {result['answer'][:300]}...")
            
        finally:
            await es_client.close()
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_hierarchical_query(self):
        """Test complete pipeline with hierarchical query"""
        await es_client.connect()
        
        try:
            test_case = INTEGRATION_TEST_CASES[4]  # "Ngành CNTT học những gì?"
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing: {test_case['name']}")
            logger.info(f"Query: {test_case['query']}")
            logger.info(f"{'='*80}")
            
            result = await rag_pipeline.run(
                query=test_case["query"],
                major=test_case["major"],
                top_k=10,  # More results for hierarchical
                enable_reranking=False,
                enable_query_expansion=True
            )
            
            # Assertions
            assert result["metadata"]["intent"] == test_case["expected_intent"]
            
            answer = result["answer"].lower()
            for keyword in test_case["expected_in_answer"]:
                assert keyword.lower() in answer, f"Expected '{keyword}' in answer"
            
            # Hierarchical queries should retrieve more sources
            assert len(result["sources"]) >= 3, "Hierarchical should have multiple sources"
            
            # Answer should be comprehensive
            assert len(result["answer"]) > 300, "Hierarchical query should have detailed answer"
            
            logger.info(f"\n✓ Answer generated: {len(result['answer'])} chars")
            logger.info(f"  Intent: {result['metadata']['intent']}")
            logger.info(f"  Sources: {len(result['sources'])}")
            logger.info(f"\n  Answer preview: {result['answer'][:400]}...")
            
        finally:
            await es_client.close()
    
    @pytest.mark.asyncio
    async def test_pipeline_with_no_results(self):
        """Test pipeline behavior when no results found"""
        await es_client.connect()
        
        try:
            result = await rag_pipeline.run(
                query="Môn XXXXXXX học những gì?",  # Non-existent course
                major=None,
                top_k=5
            )
            
            # Should still return a response
            assert "answer" in result
            assert "không tìm thấy" in result["answer"].lower() or "không có" in result["answer"].lower()
            assert len(result["sources"]) == 0
            
            logger.info(f"\n✓ Handled no-results case gracefully")
            
        finally:
            await es_client.close()


class TestIntegrationAllQueries:
    """Run all integration test cases"""
    
    @pytest.mark.asyncio
    async def test_all_integration_cases(self):
        """Run all integration test cases and collect metrics"""
        await es_client.connect()
        
        results_summary = []
        
        try:
            for test_case in INTEGRATION_TEST_CASES:
                logger.info(f"\n\n{'█'*80}")
                logger.info(f"TEST: {test_case['name']}")
                logger.info(f"{'█'*80}")
                
                try:
                    result = await rag_pipeline.run(
                        query=test_case["query"],
                        major=test_case["major"],
                        top_k=10,
                        enable_reranking=False,
                        enable_query_expansion=True
                    )
                    
                    # Check intent
                    intent_match = result["metadata"]["intent"] == test_case["expected_intent"]
                    
                    # Check answer quality
                    answer = result["answer"].lower()
                    keywords_found = sum(
                        1 for kw in test_case["expected_in_answer"] 
                        if kw.lower() in answer
                    )
                    keywords_ratio = keywords_found / len(test_case["expected_in_answer"])
                    
                    results_summary.append({
                        "name": test_case["name"],
                        "query": test_case["query"],
                        "expected_intent": test_case["expected_intent"],
                        "actual_intent": result["metadata"]["intent"],
                        "intent_match": intent_match,
                        "keywords_found": keywords_found,
                        "keywords_total": len(test_case["expected_in_answer"]),
                        "keywords_ratio": keywords_ratio,
                        "num_sources": len(result["sources"]),
                        "answer_length": len(result["answer"]),
                        "total_time_ms": result["metadata"]["total_time_ms"],
                        "success": intent_match and keywords_ratio >= 0.5
                    })
                    
                    logger.info(f"\n✓ Completed")
                    logger.info(f"  Intent: {result['metadata']['intent']} ({'✓' if intent_match else '✗'})")
                    logger.info(f"  Keywords: {keywords_found}/{len(test_case['expected_in_answer'])}")
                    logger.info(f"  Answer: {len(result['answer'])} chars")
                    logger.info(f"  Time: {result['metadata']['total_time_ms']:.2f}ms")
                    
                    # Print answer preview
                    logger.info(f"\n  Answer preview:")
                    logger.info(f"  {result['answer'][:300]}...")
                    
                except Exception as e:
                    logger.error(f"✗ Test failed: {e}")
                    results_summary.append({
                        "name": test_case["name"],
                        "query": test_case["query"],
                        "success": False,
                        "error": str(e)
                    })
                
                # Wait between tests
                await asyncio.sleep(1)
            
            # Print summary
            logger.info(f"\n\n{'='*80}")
            logger.info("INTEGRATION TEST SUMMARY")
            logger.info(f"{'='*80}")
            
            for result in results_summary:
                status = "✓" if result.get("success", False) else "✗"
                logger.info(f"\n{status} {result['name']}")
                logger.info(f"  Query: {result['query']}")
                
                if "error" in result:
                    logger.info(f"  Error: {result['error']}")
                else:
                    logger.info(f"  Intent: {result['expected_intent']} → {result['actual_intent']} ({'✓' if result['intent_match'] else '✗'})")
                    logger.info(f"  Keywords: {result['keywords_found']}/{result['keywords_total']} ({result['keywords_ratio']*100:.0f}%)")
                    logger.info(f"  Sources: {result['num_sources']}")
                    logger.info(f"  Answer: {result['answer_length']} chars")
                    logger.info(f"  Time: {result['total_time_ms']:.2f}ms")
            
            # Calculate metrics
            total = len(results_summary)
            successful = sum(1 for r in results_summary if r.get("success", False))
            success_rate = (successful / total) * 100
            
            intent_correct = sum(1 for r in results_summary if r.get("intent_match", False))
            intent_accuracy = (intent_correct / total) * 100
            
            avg_time = sum(r.get("total_time_ms", 0) for r in results_summary) / total
            
            logger.info(f"\n{'='*80}")
            logger.info("METRICS")
            logger.info(f"{'='*80}")
            logger.info(f"Success Rate: {successful}/{total} ({success_rate:.1f}%)")
            logger.info(f"Intent Accuracy: {intent_correct}/{total} ({intent_accuracy:.1f}%)")
            logger.info(f"Avg Time: {avg_time:.2f}ms")
            logger.info(f"{'='*80}")
            
            # Assert minimum quality
            assert success_rate >= 80, f"Success rate {success_rate:.1f}% below 80% threshold"
            assert intent_accuracy >= 80, f"Intent accuracy {intent_accuracy:.1f}% below 80% threshold"
            
        finally:
            await es_client.close()


# Standalone runner
async def run_all_integration_tests():
    """Run all integration tests manually"""
    logger.info("\n" + "="*80)
    logger.info("INTENT-BASED RAG PIPELINE - INTEGRATION TESTS")
    logger.info("="*80)
    
    test_runner = TestIntegrationAllQueries()
    await test_runner.test_all_integration_cases()
    
    logger.info("\n\n" + "="*80)
    logger.info("✓ ALL INTEGRATION TESTS COMPLETED")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(run_all_integration_tests())
