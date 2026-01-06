"""
Unit test for Intent Detection
Tests the IntentDetector class with query.json test cases
"""
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_queries():
    """Load test queries from query.json"""
    query_file = Path(__file__).parent.parent / "query.json"
    with open(query_file, "r", encoding="utf-8") as f:
        return json.load(f)


async def test_intent_detection():
    """Test intent detection accuracy on all queries"""
    from app.retrieval_engine.intent_detection import detect_intent
    
    test_cases = load_test_queries()
    
    results = []
    correct = 0
    total = len(test_cases)
    
    # Group results by intent
    intent_stats = {
        "overview": {"correct": 0, "total": 0, "errors": []},
        "structure": {"correct": 0, "total": 0, "errors": []},
        "roadmap": {"correct": 0, "total": 0, "errors": []},
        "factual": {"correct": 0, "total": 0, "errors": []},
        "compare": {"correct": 0, "total": 0, "errors": []},
        "policy": {"correct": 0, "total": 0, "errors": []}
    }
    
    logger.info("=" * 70)
    logger.info("INTENT DETECTION TEST")
    logger.info("=" * 70)
    logger.info(f"Total test cases: {total}")
    logger.info("-" * 70)
    
    for idx, case in enumerate(test_cases):
        query = case["original"]
        expected = case["expected_intent"]
        
        # Detect intent - now returns QueryIntent directly
        intent = await detect_intent(query)
        predicted = intent.value
        is_correct = predicted == expected
        
        # Update stats
        if expected not in intent_stats:
            intent_stats[expected] = {"correct": 0, "total": 0, "errors": []}
        intent_stats[expected]["total"] += 1
        if is_correct:
            correct += 1
            intent_stats[expected]["correct"] += 1
        else:
            intent_stats[expected]["errors"].append({
                "query": query,
                "predicted": predicted
            })
        
        # Log result
        status = "✓" if is_correct else "✗"
        logger.info(f"[{idx+1}/{total}] {status} '{query[:50]}...'")
        if not is_correct:
            logger.info(f"       Expected: {expected}, Got: {predicted}")
        
        results.append({
            "query": query,
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct
        })
    
    # Summary
    accuracy = correct / total * 100
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Overall Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    logger.info("")
    
    # Per-intent breakdown
    logger.info("Per-Intent Accuracy:")
    for intent, stats in intent_stats.items():
        if stats["total"] > 0:
            acc = stats["correct"] / stats["total"] * 100
            logger.info(f"  {intent.upper()}: {stats['correct']}/{stats['total']} ({acc:.1f}%)")
            if stats["errors"]:
                for err in stats["errors"]:
                    logger.info(f"    ✗ '{err['query'][:40]}...' → {err['predicted']}")
    
    # Save output
    output = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "per_intent": {
            intent: {
                "total": stats["total"],
                "correct": stats["correct"],
                "accuracy": stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0,
                "errors": stats["errors"]
            }
            for intent, stats in intent_stats.items()
        },
        "results": results
    }
    
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"intent_detection_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    logger.info("")
    logger.info(f"Results saved to: {output_file}")
    
    return output


if __name__ == "__main__":
    result = asyncio.run(test_intent_detection())
    
    # Exit with error code if accuracy < 80%
    if result["accuracy"] < 80:
        logger.warning(f"Accuracy below 80%: {result['accuracy']:.1f}%")
        sys.exit(1)
    else:
        logger.info(f"Test passed with {result['accuracy']:.1f}% accuracy")
        sys.exit(0)
