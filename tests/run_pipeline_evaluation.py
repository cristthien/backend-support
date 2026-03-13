"""
Run standard RAG pipeline (pipeline.py) on test queries and save results for evaluation

NOTE: Standard pipeline uses retrieval_engine which does not yet support search_mode.
      For search mode testing, use run_ragas_evaluation.py (intent-based pipeline)
      or run_naive_evaluation.py.

Usage:
    python tests/run_pipeline_evaluation.py               # Run all queries
    python tests/run_pipeline_evaluation.py --overview    # Run only overview intent queries
    python tests/run_pipeline_evaluation.py --structure   # Run only structure intent queries
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

# Available intent types
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
    
    queries = [
        {
            "query": case["original"],
            "expected_intent": case.get("expected_intent"),
            "ground_truth": case.get("ground_truth", ""),
            "major": case.get("major")
        }
        for case in cases
    ]
    
    if intent_filter:
        queries = [q for q in queries if q.get("expected_intent") == intent_filter]
    
    return queries


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Run standard pipeline evaluation with optional intent filtering"
    )
    
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


async def run_pipeline_evaluation(intent_filter=None):
    """Run all queries through standard pipeline and save results"""
    
    from app.query.pipeline import run_query
    from app.clients.elasticsearch import es_client
    
    test_queries = load_test_queries(intent_filter)
    
    if not test_queries:
        logger.error("No queries found for the specified intent filter: %s", intent_filter)
        return []
    
    await es_client.connect()
    
    results = []
    
    logger.info("=" * 80)
    logger.info("RUNNING STANDARD PIPELINE EVALUATION")
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
            # Run standard pipeline
            response = await run_query(
                query=query,
                major=major,
                top_k=10,
                include_sources=True,
                enable_reranking=True,
                enable_query_expansion=True
            )
            
            # Build contexts from sources
            contexts = []
            for source in response.sources:
                contexts.append(source.text_preview or "")
            
            # Build evaluation record
            record = {
                "question": query,
                "answer": response.answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
                "expected_intent": expected_intent,
                "metadata": {
                    "major_used": response.metadata.major_used,
                    "chunks_retrieved": response.metadata.chunks_retrieved,
                    "sections_retrieved": response.metadata.sections_retrieved,
                    "total_time_ms": response.metadata.total_time_ms
                },
                "sources": [
                    {
                        "section_id": s.section_id,
                        "title": s.title,
                        "hierarchy_path": s.hierarchy_path,
                        "text_preview": s.text_preview,
                        "score": s.score
                    }
                    for s in response.sources
                ]
            }
            
            results.append(record)
            
            logger.info("  ✓ Answer: %s...", response.answer[:100])
            logger.info("  ✓ Sources: %d", len(response.sources))
            
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
    
    await es_client.close()
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if intent_filter:
        output_path = output_dir / f"pipeline_evaluation_{intent_filter}_{timestamp}.json"
    else:
        output_path = output_dir / f"pipeline_evaluation_{timestamp}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "pipeline": "standard",
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
    asyncio.run(run_pipeline_evaluation(intent_filter=args.intent_filter))
