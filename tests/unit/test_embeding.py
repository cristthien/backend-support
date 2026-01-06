"""
Test embedding search với top_k = 10
Kiểm tra khả năng tìm kiếm vector embedding cho các câu hỏi tiếng Việt
"""
import asyncio
import logging
import json
from typing import Optional
import csv 

from app.clients.elasticsearch import es_client
from app.clients.ollama import ollama_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_embedding_search(
    query: str,
    major: Optional[str] = None,
    top_k: int = 10
):
    """
    Test embedding search với một câu hỏi cụ thể
    
    Args:
        query: Câu hỏi người dùng
        major: Bộ lọc ngành (optional)
        top_k: Số kết quả trả về
    """
    logger.info("=" * 80)
    logger.info("TESTING QUERY: %s", query)
    logger.info("Major: %s | Top K: %d", major, top_k)
    logger.info("=" * 80)
    
    try:
        # Connect to Elasticsearch
        await es_client.connect()
        
        # Generate embedding for the query
        logger.info("Generating embedding for query...")
        query_embedding = await ollama_client.generate_embedding(query)
        logger.info("Embedding generated with dimension: %d", len(query_embedding))
        
        # Search sections using vector similarity
        logger.info("Searching sections with top_k=%d...", top_k)
        sections = await es_client.search_chunks(
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        # Print results
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")
        print(f"RESULTS: {len(sections)} sections retrieved")
        print(f"{'='*80}\n")
        
        for section in sections:
           section.pop("embedding", None)
        return sections
        
    finally:
        await es_client.close()


async def run_all_embedding_tests():
    """Run all embedding search tests với các câu hỏi đã cho"""
    
    test_questions = [
        {
            "name": "Test 1: Học CNTT học những gì",
            "query": "Học Công Nghệ Thông Tin thì học những gì?",
            "major": None,
            "top_k": 10
        },
        {
            "name": "Test 2: Data Engineering trong ngành CNTT",
            "query": "Sau này muốn học Data Engineering, mà t đang học ngành công nghệ thông tin thì t học những môn nào?",
            "major": None,
            "top_k": 10
        },
        {
            "name": "Test 3: Làm Data Engineering học môn nào",
            "query": "T muốn làm Data Engineering thì nên học những môn nào?",
            "major": None,
            "top_k": 10
        },
        {
            "name": "Test 4: So sánh HTTT tiên tiến và chính quy",
            "query": "Hệ Thống thống tin tiên tiến khác gì với hệ thống thông tin chính quy.",
            "major": None,
            "top_k": 10
        },
        {
            "name": "Test 5: Học vượt như thế nào",
            "query": "Sinh viên học vượt thì nên học như thế nào?",
            "major": None,
            "top_k": 10
        }
    ]
    
    all_results = []
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n\n{'#'*80}")
        print(f"# {test['name']}")
        print(f"{'#'*80}\n")
        
        results = await test_embedding_search(
            query=test['query'],
            top_k=test.get('top_k', 10)
        )
        
        all_results.append({
            "test_name": test['name'],
            "query": test['query'],
            "num_results": len(results),
            "results": results
        })
        
        # Small delay between tests
        await asyncio.sleep(1)

    # Save results to JSON file
    with open("test_results.json", "w", encoding="utf-8-sig") as f:
        json.dump(all_results, f, indent=4, ensure_ascii=False)
    
    # Save results to CSV file
    with open("test_results.csv", "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["test_name", "query", "text"])
        for result in all_results:
            for chunk in result["results"]:
                writer.writerow([result["test_name"], result["query"], chunk["text"]])

    # Print summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for result in all_results:
        print(f"✓ {result['test_name']}: {result['num_results']} results")
    
    return all_results


async def main():
    """Main entry point"""
    # Run all embedding tests
    await run_all_embedding_tests()


if __name__ == "__main__":
    asyncio.run(main())
