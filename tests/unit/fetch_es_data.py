"""
Fetch chunks and sections from Elasticsearch and export to JSON

Usage:
    .venv/bin/python tests/unit/fetch_es_data.py                    # Fetch all
    .venv/bin/python tests/unit/fetch_es_data.py --doc-id 1         # Fetch for specific doc
    .venv/bin/python tests/unit/fetch_es_data.py --stats-only       # Just show stats
"""
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/admin/Documents/School/backend-support')

from app.clients.elasticsearch import es_client

OUTPUT_DIR = Path('/Users/admin/Documents/School/backend-support/tests/unit/output')


async def fetch_all_sections():
    """Fetch all sections from Elasticsearch"""
    response = await es_client.client.search(
        index=es_client.sections_index,
        body={
            "query": {"match_all": {}},
            "size": 10000,
            "sort": [{"level": "asc"}]
        }
    )
    sections = [hit["_source"] for hit in response["hits"]["hits"]]
    return sections


async def fetch_all_chunks():
    """Fetch all chunks from Elasticsearch"""
    response = await es_client.client.search(
        index=es_client.chunks_index,
        body={
            "query": {"match_all": {}},
            "size": 10000
        }
    )
    chunks = [hit["_source"] for hit in response["hits"]["hits"]]
    return chunks


async def main(doc_id: int = None, stats_only: bool = False):
    """Main function to fetch and export ES data"""
    print("=" * 60)
    print("Elasticsearch Data Fetcher")
    print("=" * 60)
    
    # Connect to Elasticsearch
    print("\n📡 Connecting to Elasticsearch...")
    await es_client.connect()
    
    # Get index stats
    stats = await es_client.get_index_stats()
    print(f"   Sections index: {stats['sections']} documents")
    print(f"   Chunks index: {stats['chunks']} documents")
    
    if stats_only:
        print("\n✅ Stats only mode - done!")
        await es_client.close()
        return
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Fetch data
    if doc_id:
        print(f"\n📥 Fetching data for doc_id={doc_id}...")
        sections = await es_client.get_sections_by_doc_id(doc_id)
        chunks = await es_client.get_chunks_by_doc_id(doc_id)
        suffix = f"_doc{doc_id}"
    else:
        print("\n📥 Fetching ALL data...")
        sections = await fetch_all_sections()
        chunks = await fetch_all_chunks()
        suffix = "_all"
    
    print(f"   Retrieved {len(sections)} sections")
    print(f"   Retrieved {len(chunks)} chunks")
    
    # Remove embeddings (too large for JSON)
    for section in sections:
        section.pop('embedding', None)
    for chunk in chunks:
        chunk.pop('embedding', None)
    
    # Export sections
    sections_file = OUTPUT_DIR / f'es_sections{suffix}.json'
    with open(sections_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'doc_id': doc_id,
            'total_count': len(sections),
            'sections': sections
        }, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved sections to: {sections_file}")
    
    # Export chunks
    chunks_file = OUTPUT_DIR / f'es_chunks{suffix}.json'
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'doc_id': doc_id,
            'total_count': len(chunks),
            'chunks': chunks
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved chunks to: {chunks_file}")
    
    # Print sample data
    print("\n" + "=" * 60)
    print("📊 Sample Sections (first 3)")
    print("=" * 60)
    for i, section in enumerate(sections[:3], 1):
        title = section.get('title', 'N/A')
        level = section.get('level', 'N/A')
        text_len = len(section.get('text', ''))
        tables = len(section.get('tables', []))
        major = section.get('metadata', {}).get('major', 'N/A')
        print(f"{i}. [H{level}] {title[:50]}...")
        print(f"   Major: {major}")
        print(f"   Text: {text_len} chars, Tables: {tables}")
        print()
    
    print("=" * 60)
    print("📦 Sample Chunks (first 3)")
    print("=" * 60)
    for i, chunk in enumerate(chunks[:3], 1):
        text = chunk.get('text', '')[:100].replace('\n', ' ')
        chunk_id = chunk.get('chunk_id', 'N/A')
        section_id = chunk.get('section_id', 'N/A')
        print(f"{i}. ID: {chunk_id}")
        print(f"   Section: {section_id}")
        print(f"   Text: {text}...")
        print()
    
    # Close connection
    await es_client.close()
    
    print("=" * 60)
    print("✅ Done!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch chunks and sections from Elasticsearch")
    parser.add_argument(
        "--doc-id",
        type=int,
        default=None,
        help="Specific document ID to fetch (default: fetch all)"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show index statistics, don't fetch data"
    )
    args = parser.parse_args()
    
    asyncio.run(main(doc_id=args.doc_id, stats_only=args.stats_only))
