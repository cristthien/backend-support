"""
Test Intent-Based Retrieval Engine with first 10 queries from expect_results
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.query.intent_based_retrieval_engine import intent_engine
from app.clients.elasticsearch import es_client


async def test_retrieval_pipeline():
    """Test the intent-based retrieval pipeline with first 10 queries"""
    
    # Load test queries
    with open(Path(__file__).parent / "expect_results.json") as f:
        all_queries = json.load(f)
    
    # Take first 10 queries
    test_queries = all_queries[:10]
    
    print("=" * 80)
    print("Testing Intent-Based Retrieval Engine")
    print("=" * 80)
    
    # Connect to ES
    await es_client.connect()
    
    results = []
    
    for i, item in enumerate(test_queries, 1):
        query = item["original"]
        expected_intent = item["expected_intent"]
        
        print(f"\n[{i:02d}] Query: {query}")
        print(f"     Expected: {expected_intent}")
        
        try:
            # Run retrieval
            sections, metadata = await intent_engine.run(
                query=query,
                major=None,
                top_k=5,
                enable_reranking=False,  # Skip reranking for testing
                enable_query_expansion=True
            )
            
            actual_intent = metadata.get("intent", "unknown")
            strategy_used = metadata.get("strategy", "unknown")
            num_results = len(sections)
            
            # Check intent match
            intent_match = actual_intent == expected_intent
            marker = "✓" if intent_match else "✗"
            
            print(f"     Actual:   {actual_intent} {marker}")
            print(f"     Strategy: {strategy_used if 'strategy' in metadata else 'N/A'}")
            print(f"     Results:  {num_results} items")
            
            if sections:
                # Show first result
                first = sections[0]
                result_type = first.get("result_type", "unknown")
                level = first.get("level", "?")
                title = first.get("title", first.get("hierarchy_path", ""))[:50]
                print(f"     First:    [{result_type}] L{level} - {title}...")
            
            results.append({
                "query": query,
                "expected": expected_intent,
                "actual": actual_intent,
                "match": intent_match,
                "num_results": num_results
            })
            
        except Exception as e:
            print(f"     ERROR: {e}")
            results.append({
                "query": query,
                "expected": expected_intent,
                "actual": "error",
                "match": False,
                "error": str(e)
            })
    
    # Close ES connection
    await es_client.close()
    
    # Summary
    print("\n" + "=" * 80)
    correct = sum(1 for r in results if r["match"])
    total = len(results)
    print(f"SUMMARY: {correct}/{total} ({100*correct/total:.1f}%) intent matches")
    print("=" * 80)
    
    # Show failures
    failures = [r for r in results if not r["match"]]
    if failures:
        print("\nFailed queries:")
        for r in failures:
            print(f"  - {r['query']}")
            print(f"    Expected: {r['expected']}, Got: {r['actual']}")


if __name__ == "__main__":
    asyncio.run(test_retrieval_pipeline())
