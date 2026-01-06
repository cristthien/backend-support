"""
Test Intent-Based Retrieval Engine - 1 query per intent
Full pipeline test with ES retrieval and JSON logging
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.query.intent_based_retrieval_engine import intent_engine
from app.clients.elasticsearch import es_client


# 1 sample query per intent (9 intents)
SAMPLE_QUERIES = [
    # factual intent
    # {"query": "Môn Dữ Liệu Lớn có bao nhiêu tín chỉ?", "expected_intent": "factual"},
    # {"query": "Tốt nghiệp ngành TTNT cần bao nhiêu tín chỉ?", "expected_intent": "factual"},
    # {"query": "Ngành Công Nghệ Thông Tin học bao nhiêu lâu?", "expected_intent": "factual"},
    # policy intent
    # {"query": "Điều kiện nhận học bổng khích lệ học tập là gì?", "expected_intent": "policy"},
    # {"query": "Quy định về miễn học tiếng anh như thế nào?", "expected_intent": "policy"},
    # overview intent
    # {"query": "Ngành TTNT gồm những mảng chính nào?", "expected_intent": "overview"},
    # {"query": "Chuyên ngành của công nghệ thông tin học những môn nào ", "expected_intent": "overview"},
    # {"query": "Môn hệ quản trị cơ sở dữ liệu học những gì?", "expected_intent": "overview"},
    # outcomes intent
    # {"query": "Ngành Trí Tuệ Nhân Tạo ra làm được role nào?", "expected_intent": "outcomes"},
    # {"query": "Sau khi tốt nghiệp ngành Công Nghệ thông Tin có thể làm được những ngành liên quan tới data không", "expected_intent": "outcomes"},
    # assessment intent
    # {"query": "Môn phân tích dữ liệu kinh doanh điểm cuối kì chiếm bao nhiêu phần trăm", "expected_intent": "assessment"},
    # {"query": "Môn dữ liệu lớn được tính phổ điểm như thế nào?", "expected_intent": "assessment"},
    # prerequisite intent   
    {"query": "Môn tiên quyết của Dữ Liệu Lớn là gì?", "expected_intent": "prerequisite"},
    # compare intent
    # {"query": "So sánh giữa cơ sở dữ liệu và hệ quản trị cơ sở dữ liệu", "expected_intent": "compare"},
    # roadmap intent
    # {"query": "Học kỳ 1 ngành AI học những môn gì?", "expected_intent": "roadmap"},
    # {"query": "Học kỳ 5 ngành trí tuệ nhân tạo học những môn gì?", "expected_intent": "roadmap"},
]


async def run_single_query_test():
    """Test retrieval pipeline with 1 query per intent"""
    
    print("=" * 80)
    print("Intent-Based Retrieval Test - 1 Query Per Intent")
    print("=" * 80)
    
    # Connect to ES
    try:
        await es_client.connect()
        print("✓ Connected to Elasticsearch")
    except Exception as e:
        print(f"✗ Failed to connect to Elasticsearch: {e}")
        print("  Running in intent-detection-only mode...")
        es_connected = False
    else:
        es_connected = True
    
    results = []
    
    for i, item in enumerate(SAMPLE_QUERIES, 1):
        query = item["query"]
        expected = item["expected_intent"]
        
        print(f"\n[{i:02d}] Intent: {expected.upper()}")
        print(f"     Query: {query}")
        
        try:
            # Run full retrieval pipeline
            sections, metadata = await intent_engine.run(
                query=query,
                major=None,
                enable_reranking=True,
            )
            
            actual_intent = metadata.get("intent", "unknown")
            expanded_query = metadata.get("expanded_query", query)
            reasoning = metadata.get("reasoning", "")
            time_ms = metadata.get("time_ms", 0)
            
            intent_match = actual_intent == expected
            marker = "✓" if intent_match else "✗"
            
            print(f"     Detected: {actual_intent} {marker}")
            print(f"     Expanded: {expanded_query[:60]}...")
            print(f"     Time: {time_ms:.2f}ms")
            print(f"     Results: {len(sections)} items")
            
            # Build result entry
            result_entry = {
                "index": i,
                "query": query,
                "expected_intent": expected,
                "actual_intent": actual_intent,
                "intent_match": intent_match,
                "expanded_query": expanded_query,
                "reasoning": reasoning,
                "time_ms": round(time_ms, 2),
                "num_results": len(sections),
                "sections": []
            }
            
            # Add section summaries
            for j, section in enumerate(sections):
                result_entry["sections"].append({
                    "rank": j + 1,
                    "title": section.get("title", "")[:50],
                    "text": section.get("text", ""),
                    "level": section.get("level", 0),
                    "result_type": section.get("result_type", "unknown"),
                    "hierarchy_path": section.get("hierarchy_path", "")[:80],
                })
            
            results.append(result_entry)
            
        except Exception as e:
            print(f"     ERROR: {e}")
            results.append({
                "index": i,
                "query": query,
                "expected_intent": expected,
                "actual_intent": "error",
                "intent_match": False,
                "error": str(e)
            })
    
    # Close ES connection
    if es_connected:
        await es_client.close()
    
    # Summary
    print("\n" + "=" * 80)
    correct = sum(1 for r in results if r.get("intent_match", False))
    total = len(results)
    print(f"INTENT ACCURACY: {correct}/{total} ({100*correct/total:.1f}%)")
    print("=" * 80)
    
    # Save to JSON
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_queries": total,
        "intent_accuracy": f"{correct}/{total} ({100*correct/total:.1f}%)",
        "es_connected": es_connected,
        "results": results
    }
    
    output_path = Path(__file__).parent / "intent_retrieval_log.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(run_single_query_test())
