"""
Run full RAG pipeline on test queries and save results for RAGAS evaluation

5 Retrieval-Focused Intents:
- OVERVIEW: Tổng quan ngành/môn (LLM decompose)
- STRUCTURE: Cấu trúc, đánh giá, chuẩn đầu ra, policy (section search)
- ROADMAP: Lộ trình học kỳ/năm (semester filter)
- FACTUAL: Metadata, tiên quyết (chunk exact match)
- COMPARE: So sánh 2 đối tượng (split entity merge)

Usage:
    python tests/run_ragas_evaluation.py               # Run all queries
    python tests/run_ragas_evaluation.py --overview    # Run only overview intent queries
    python tests/run_ragas_evaluation.py --structure   # Run only structure intent queries
    python tests/run_ragas_evaluation.py --roadmap     # Run only roadmap intent queries
    python tests/run_ragas_evaluation.py --factual     # Run only factual intent queries
    python tests/run_ragas_evaluation.py --compare     # Run only compare intent queries
"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Available intent types (5 Retrieval-Focused Intents)
INTENT_TYPES = ["overview", "structure", "roadmap", "factual", "compare"]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_queries(intent_filter=None):
    """Load test queries from query.json, optionally filtered by intent type"""
    query_file = Path(__file__).parent / "query.json"
    with open(query_file, "r", encoding="utf-8") as f:
        cases = json.load(f)
    
    # Transform to match expected format
    queries = [
        {
            "query": case["original"],
            "expected_intent": case.get("expected_intent"),
            "ground_truth": case.get("ground_truth", ""),
            "major": case.get("major")
        }
        for case in cases
    ]
    
    # Filter by intent if specified
    if intent_filter:
        queries = [q for q in queries if q.get("expected_intent") == intent_filter]
    
    return queries


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Run RAG pipeline evaluation with optional intent filtering"
    )
    
    # Add mutually exclusive group for intent filters
    intent_group = parser.add_mutually_exclusive_group()
    for intent in INTENT_TYPES:
        intent_group.add_argument(
            f"--{intent}",
            action="store_const",
            const=intent,
            dest="intent_filter",
            help=f"Run only {intent} intent queries"
        )
    
    return parser.parse_args()


async def run_ragas_evaluation(intent_filter=None):
    """Run all queries through RAG pipeline and save results"""
    
    # Import after to avoid circular imports
    from app.query.intent_based_rag_pipeline import rag_pipeline
    from app.clients.elasticsearch import es_client
    
    # Load queries with optional filter
    test_queries = load_test_queries(intent_filter)
    
    if not test_queries:
        logger.error("No queries found for the specified intent filter: %s", intent_filter)
        return []
    
    # Connect to Elasticsearch
    await es_client.connect()
    
    results = []
    
    logger.info("=" * 80)
    logger.info("RUNNING RAG PIPELINE FOR RAGAS EVALUATION")
    if intent_filter:
        logger.info("Intent filter: %s", intent_filter)
    logger.info("Total queries: %d", len(test_queries))
    logger.info("=" * 80)
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        major = test_case.get("major")
        ground_truth = test_case.get("ground_truth", "")
        expected_intent = test_case.get("expected_intent", "")
        
        logger.info("\n[%d/%d] Processing: %s...", i, len(test_queries), query[:60])
        
        try:
            # Run RAG pipeline
            result = await rag_pipeline.run(
                query=query,
                major=major,
                top_k=10,
                enable_reranking=False,
                enable_query_expansion=True
            )
            
            # Build contexts from sources
            contexts = []
            for source in result["sources"]:
                contexts.append(source.get("text_preview", ""))
            
            # Build RAGAS-compatible record
            ragas_record = {
                "question": query,
                "answer": result["answer"],
                "contexts": contexts,
                "ground_truth": ground_truth,
                "expected_intent": expected_intent,
                "metadata": {
                    "intent": result["metadata"].get("intent"),
                    "expanded_query": result["metadata"].get("expanded_query"),
                    "num_sources": result["metadata"].get("num_sources"),
                    "total_time_ms": result["metadata"].get("total_time_ms"),
                    "major": major
                },
                "sources": result["sources"]
            }
            
            results.append(ragas_record)
            
            logger.info("  ✓ Answer: %s...", result['answer'][:100])
            logger.info("  ✓ Sources: %d", len(result['sources']))
            logger.info("  ✓ Intent: %s", result['metadata'].get('intent'))
            
        except Exception as e:
            logger.error("  ✗ Error: %s", e)
            results.append({
                "question": query,
                "answer": f"ERROR: {str(e)}",
                "contexts": [],
                "ground_truth": ground_truth,
                "expected_intent": expected_intent,
                "metadata": {"error": str(e)},
                "sources": []
            })
    
    # Close ES connection
    await es_client.close()
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results with timestamp and intent filter in filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if intent_filter:
        output_path = output_dir / f"ragas_evaluation_{intent_filter}_{timestamp}.json"
    else:
        output_path = output_dir / f"ragas_evaluation_{timestamp}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "intent_filter": intent_filter,
            "total_queries": len(test_queries),
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    logger.info("\n%s", "=" * 80)
    logger.info("✓ Results saved to: %s", output_path)
    logger.info("  Total queries: %d", len(results))
    logger.info("%s", "=" * 80)
    
    return results


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_ragas_evaluation(intent_filter=args.intent_filter))

