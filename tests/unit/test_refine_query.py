"""
Test suite for Query Refinement Module

Tests:
1. normalize_query - lowercase conversion
2. expand_abbreviations - Vietnamese education term expansion
3. refine_query_sync - full synchronous pipeline (no LLM)
4. All testcase queries from testcase_queries.txt
5. Intent detection after refinement with JSON log
"""
import sys
import os
import asyncio
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.retrieval_engine.refine_query import (
    normalize_query,
    expand_abbreviations,
    refine_query_sync,
    refine_query,
    ABBREVIATION_MAP,
)
from app.query.intent_based_prompt_engine import IntentDetector, SchemaAwareExpander, QueryIntent


def test_normalize_query():
    """Test lowercase normalization."""
    print("\n=== Test: normalize_query ===")
    
    test_cases = [
        ("Ngành TTNT học những gì?", "ngành ttnt học những gì?"),
        ("CNTT và HTTT", "cntt và httt"),
        ("Deep Learning ở đâu?", "deep learning ở đâu?"),
    ]
    
    for original, expected in test_cases:
        result = normalize_query(original)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{original}' -> '{result}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print("  All normalize_query tests passed!")


def test_expand_abbreviations():
    """Test abbreviation expansion."""
    print("\n=== Test: expand_abbreviations ===")
    
    test_cases = [
        ("Ngành TTNT học những gì?", "Ngành Trí tuệ nhân tạo học những gì?"),
        ("CNTT và HTTT", "Công nghệ thông tin và Hệ thống thông tin"),
        ("Sinh viên KTMT cần gì?", "Sinh viên Kỹ thuật máy tính cần gì?"),
        ("KLTN ngành KHDL", "Khóa luận tốt nghiệp ngành Khoa học dữ liệu"),
        ("AI và CSDL", "Trí tuệ nhân tạo và Cơ sở dữ liệu"),
    ]
    
    for original, expected in test_cases:
        result = expand_abbreviations(original)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{original}'")
        print(f"      -> '{result}'")
        if result != expected:
            print(f"      Expected: '{expected}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print("  All expand_abbreviations tests passed!")


def test_refine_query_sync():
    """Test synchronous refinement (lowercase + abbreviation expansion)."""
    print("\n=== Test: refine_query_sync ===")
    
    test_cases = [
        ("Ngành TTNT học những gì?", "ngành trí tuệ nhân tạo học những gì?"),
        ("CNTT và HTTT", "công nghệ thông tin và hệ thống thông tin"),
        ("Điều kiện làm KLTN CNTT?", "điều kiện làm khóa luận tốt nghiệp công nghệ thông tin?"),
    ]
    
    for original, expected in test_cases:
        result = refine_query_sync(original)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{original}'")
        print(f"      -> '{result}'")
        if result != expected:
            print(f"      Expected: '{expected}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print("  All refine_query_sync tests passed!")


def test_all_testcase_queries():
    """Test all queries from testcase_queries.txt."""
    print("\n=== Test: All Testcase Queries (Sync) ===")
    
    # Load testcase queries
    testcase_file = os.path.join(os.path.dirname(__file__), "testcase_queries.txt")
    
    with open(testcase_file, "r", encoding="utf-8") as f:
        queries = [line.strip().strip('"') for line in f if line.strip()]
    
    print(f"  Loaded {len(queries)} queries from testcase_queries.txt\n")
    
    for i, query in enumerate(queries, 1):
        refined = refine_query_sync(query)
        print(f"  [{i:02d}] Original: {query}")
        print(f"       Refined:  {refined}")
        print()
    
    print(f"  Processed {len(queries)} queries successfully!")


async def test_refine_and_detect_intent():
    """
    Test refine + intent detection pipeline with JSON log output.
    
    Pipeline:
    1. Load expected results from expect_results.json
    2. Refine each query (expand abbreviations + normalize)
    3. Detect intent using IntentDetector
    4. Compare expected vs actual intent
    5. Save results to JSON log file
    """
    print("\n=== Test: Refine + Intent Detection (with Expected) ===")
    
    # Load expected results
    expect_file = os.path.join(os.path.dirname(__file__), "expect_results.json")
    
    with open(expect_file, "r", encoding="utf-8") as f:
        expected_data = json.load(f)
    
    print(f"  Loaded {len(expected_data)} expected results\n")
    
    # Initialize intent detector
    detector = IntentDetector()
    
    # Process all queries
    results = []
    intent_counts = {}
    correct = 0
    wrong = 0
    
    for i, item in enumerate(expected_data, 1):
        query = item["original"]
        expected_intent = item["expected_intent"]
        
        # Step 1: Refine query
        refined = refine_query_sync(query)
        
        # Step 2: Detect intent
        try:
            intent_result = await detector.detect(refined)
            intent_obj = intent_result["intent"]
            actual_intent = intent_obj.value
        except Exception as e:
            actual_intent = f"error: {str(e)}"
        
        # Step 3: Compare
        is_match = actual_intent == expected_intent
        if is_match:
            correct += 1
            status = "✓"
        else:
            wrong += 1
            status = "✗"
        
        # Count intents
        intent_counts[actual_intent] = intent_counts.get(actual_intent, 0) + 1
        
        # Store result
        results.append({
            "id": i,
            "original": query,
            "refined": refined,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "match": is_match
        })
        
        # Print progress
        if is_match:
            print(f"  [{i:02d}] {status} {actual_intent:12s} | {query[:50]}...")
        else:
            print(f"  [{i:02d}] {status} {actual_intent:12s} (expected: {expected_intent}) | {query[:40]}...")
    
    # Summary
    total = len(expected_data)
    accuracy = correct / total * 100
    
    print(f"\n=== Accuracy: {correct}/{total} ({accuracy:.1f}%) ===")
    
    print(f"\n=== Intent Distribution (Actual) ===")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {intent.upper():12s}: {count:3d} ({pct:.1f}%)")
    
    # Show mismatches
    mismatches = [r for r in results if not r["match"]]
    if mismatches:
        print(f"\n=== Mismatches ({len(mismatches)}) ===")
        for m in mismatches[:10]:  # Show first 10
            print(f"  [{m['id']:02d}] {m['original'][:50]}")
            print(f"       Expected: {m['expected_intent']}, Got: {m['actual_intent']}")
    
    # Save to JSON log
    output_dir = os.path.dirname(__file__)
    log_file = os.path.join(output_dir, "refine_intent_log.json")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": total,
        "correct": correct,
        "wrong": wrong,
        "accuracy": accuracy,
        "intent_distribution": intent_counts,
        "results": results
    }
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Results saved to: {log_file}")
    
    return results



async def test_refine_query_with_llm():
    """Test full refinement pipeline with LLM (async)."""
    print("\n=== Test: refine_query with LLM ===")
    
    test_queries = [
        "Ngành TTNT học những gì?",
        "Điều kiện làm KLTN CNTT là gì?",
        "So sánh HTTT thường và HTTT tiên tiến",
    ]
    
    for query in test_queries:
        print(f"\n  Original: {query}")
        try:
            refined = await refine_query(query, use_llm=True)
            print(f"  Refined:  {refined}")
        except Exception as e:
            print(f"  Error:    {e}")
    
    print("\n  LLM refinement test completed!")


def run_sync_tests():
    """Run all synchronous tests."""
    print("=" * 60)
    print("Query Refinement Module - Test Suite")
    print("=" * 60)
    
    test_normalize_query()
    test_expand_abbreviations()
    test_refine_query_sync()
    test_all_testcase_queries()
    
    print("\n" + "=" * 60)
    print("All synchronous tests passed!")
    print("=" * 60)


def run_async_tests():
    """Run async tests with LLM."""
    print("\n" + "=" * 60)
    print("Running LLM Refinement Tests (requires Ollama)")
    print("=" * 60)
    
    asyncio.run(test_refine_query_with_llm())


def run_intent_tests():
    """Run refine + intent detection tests."""
    print("\n" + "=" * 60)
    print("Running Refine + Intent Detection Tests")
    print("=" * 60)
    
    asyncio.run(test_refine_and_detect_intent())


async def test_expand_with_schema():
    """
    Test SchemaAwareExpander - expand query based on intent.
    
    Pipeline:
    1. Load expected results from expect_results.json
    2. Refine query
    3. Detect intent
    4. Expand query using SchemaAwareExpander
    5. Save results to JSON log
    """
    print("\n=== Test: Refine + Intent + Expand ===")
    
    # Load expected results
    expect_file = os.path.join(os.path.dirname(__file__), "expect_results.json")
    
    with open(expect_file, "r", encoding="utf-8") as f:
        expected_data = json.load(f)
    
    print(f"  Loaded {len(expected_data)} queries\n")
    
    # Initialize components
    detector = IntentDetector()
    expander = SchemaAwareExpander()
    
    # Process queries
    results = []
    
    for i, item in enumerate(expected_data, 1):
        query = item["original"]
        
        # Step 1: Refine query
        refined = refine_query_sync(query)
        
        # Step 2: Detect intent
        try:
            intent_result = await detector.detect(refined)
            intent = intent_result["intent"]
            intent_str = intent.value
        except Exception as e:
            intent = QueryIntent.OVERVIEW
            intent_str = f"error: {str(e)}"
        
        # Step 3: Expand query
        try:
            expanded = await expander.expand(refined, intent)
        except Exception as e:
            expanded = f"error: {str(e)}"
        
        # Store result
        results.append({
            "id": i,
            "original": query,
            "refined": refined,
            "intent": intent_str,
            "expanded": expanded
        })
        
        # Print progress
        print(f"  [{i:02d}] {intent_str:12s} | {query[:40]}...")
        print(f"       Expanded: {expanded[:60]}...")
        print()
    
    # Save to JSON log
    output_dir = os.path.dirname(__file__)
    log_file = os.path.join(output_dir, "expand_log.json")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": len(expected_data),
        "results": results
    }
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Results saved to: {log_file}")
    
    return results


def run_expand_tests():
    """Run expand tests."""
    print("\n" + "=" * 60)
    print("Running Expand Tests (SchemaAwareExpander)")
    print("=" * 60)
    
    asyncio.run(test_expand_with_schema())


async def test_full_pipeline():
    """
    Test FULL pipeline: Refine → Detect Intent → Expand
    
    Pipeline:
    1. Load expected results from expect_results.json
    2. Refine each query (expand abbreviations + normalize)
    3. Detect intent using IntentDetector
    4. Expand query using SchemaAwareExpander
    5. Save all results to JSON log file
    """
    print("\n=== Test: FULL Pipeline (Refine → Detect → Expand) ===")
    
    # Load expected results
    expect_file = os.path.join(os.path.dirname(__file__), "expect_results.json")
    
    with open(expect_file, "r", encoding="utf-8") as f:
        expected_data = json.load(f)
    
    print(f"  Loaded {len(expected_data)} queries\n")
    
    # Initialize components
    detector = IntentDetector()
    expander = SchemaAwareExpander()
    
    # Process all queries
    results = []
    intent_counts = {}
    correct = 0
    wrong = 0
    
    for i, item in enumerate(expected_data, 1):
        query = item["original"]
        expected_intent = item["expected_intent"]
        
        # === Step 1: REFINE ===
        refined = refine_query_sync(query)
        
        # === Step 2: DETECT INTENT ===
        try:
            intent_result = await detector.detect(refined)
            intent_obj = intent_result["intent"]
            actual_intent = intent_obj.value
        except Exception as e:
            intent_obj = QueryIntent.OVERVIEW
            actual_intent = f"error: {str(e)}"
        
        # Check intent match
        is_match = actual_intent == expected_intent
        if is_match:
            correct += 1
            status = "✓"
        else:
            wrong += 1
            status = "✗"
        
        # Count intents
        intent_counts[actual_intent] = intent_counts.get(actual_intent, 0) + 1
        
        # === Step 3: EXPAND ===
        try:
            expanded = await expander.expand(refined, intent_obj)
        except Exception as e:
            expanded = f"error: {str(e)}"
        
        # Store result
        results.append({
            "id": i,
            "original": query,
            "refined": refined,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "intent_match": is_match,
            "expanded": expanded
        })
        
        # Print progress
        if is_match:
            print(f"  [{i:02d}] {status} {actual_intent:12s} | {query[:45]}...")
        else:
            print(f"  [{i:02d}] {status} {actual_intent:12s} (expected: {expected_intent}) | {query[:35]}...")
        print(f"       Refined:  {refined[:60]}...")
        print(f"       Expanded: {expanded[:60]}...")
        print()
    
    # Summary
    total = len(expected_data)
    accuracy = correct / total * 100
    
    print("=" * 60)
    print(f"=== ACCURACY: {correct}/{total} ({accuracy:.1f}%) ===")
    print("=" * 60)
    
    print(f"\n=== Intent Distribution (Actual) ===")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {intent.upper():12s}: {count:3d} ({pct:.1f}%)")
    
    # Show mismatches
    mismatches = [r for r in results if not r["intent_match"]]
    if mismatches:
        print(f"\n=== Mismatches ({len(mismatches)}) ===")
        for m in mismatches[:10]:
            print(f"  [{m['id']:02d}] {m['original'][:50]}")
            print(f"       Expected: {m['expected_intent']}, Got: {m['actual_intent']}")
    
    # Save to JSON log
    output_dir = os.path.dirname(__file__)
    log_file = os.path.join(output_dir, "full_pipeline_log.json")
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "test_name": "Full Pipeline (Refine → Detect → Expand)",
        "total_queries": total,
        "correct": correct,
        "wrong": wrong,
        "accuracy": accuracy,
        "intent_distribution": intent_counts,
        "results": results
    }
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Results saved to: {log_file}")
    
    return results


def run_full_pipeline_tests():
    """Run full pipeline tests (refine + detect + expand)."""
    print("\n" + "=" * 60)
    print("Running FULL Pipeline Tests (Refine → Detect → Expand)")
    print("=" * 60)
    
    asyncio.run(test_full_pipeline())


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-llm", action="store_true", help="Run LLM refinement tests")
    parser.add_argument("--with-intent", action="store_true", help="Run intent detection tests")
    parser.add_argument("--intent-only", action="store_true", help="Run only intent detection tests")
    parser.add_argument("--expand-only", action="store_true", help="Run only expand tests")
    parser.add_argument("--full-only", action="store_true", help="Run full pipeline (refine+detect+expand)")
    args = parser.parse_args()
    
    if args.intent_only:
        # Run only intent tests
        run_intent_tests()
    elif args.expand_only:
        # Run only expand tests
        run_expand_tests()
    elif args.full_only:
        # Run full pipeline tests
        run_full_pipeline_tests()
    else:
        # Run synchronous tests first
        run_sync_tests()
        
        # Optional: LLM tests
        if args.with_llm:
            run_async_tests()
        
        # Optional: Intent tests
        if args.with_intent:
            run_intent_tests()
