"""Document Ingestion Integration Test

This test:
1. Optionally resets ES indices and clears PostgreSQL documents
2. Reads all markdown files from data/raw/program, data/raw/syllabus, and data/raw/policy
3. Creates documents in PostgreSQL with user_id = 1
4. Ingests them via DocumentIngestionService (chunking + embedding + ES indexing)
5. Exports results to 3 JSON files:
   - test_output_sections.json: All sections from ES
   - test_output_chunks.json: All chunks from ES
   - test_output_docs.json: All documents from PostgreSQL

Usage:
    .venv/bin/python tests/integration/test_document_ingestion.py              # Ingestion only
    .venv/bin/python tests/integration/test_document_ingestion.py --reset      # Reset + Ingestion
"""
import argparse
import asyncio
import json
import logging
import sys
import re
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/admin/Documents/School/backend-support')

from app.db.session import AsyncSessionLocal
from app.repositories import document_repository
from app.services.document_ingestion_service import document_ingestion_service
from app.clients.elasticsearch import es_client
from sqlalchemy import select, text
from app.models.document import Document
from app.models.user import User 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

USER_ID = 1
OUTPUT_DIR = Path('/Users/admin/Documents/School/backend-support/tests/integration/output')
PROGRAM_DIR = Path('/Users/admin/Documents/School/backend-support/data/raw/program')
SYLLABUS_DIR = Path('/Users/admin/Documents/School/backend-support/data/raw/syllabus')
POLICY_DIR = Path('/Users/admin/Documents/School/backend-support/data/raw/policy')
ACADEMIC_YEAR = 'K20'


def extract_title_from_markdown(content: str, filename: str) -> str:
    """Extract title from markdown H1 heading or use filename"""
    # Try to find H1 heading
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        # Clean up markdown formatting
        title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)
        title = re.sub(r'\*(.+?)\*', r'\1', title)
        title = title.replace('--', '-').strip()
        return title
    
    # Fall back to filename without extension
    return filename.replace('.md', '').strip()


def get_all_test_files() -> list:
    """Scan program, syllabus, and policy directories for all .md files"""
    test_files = []
    
    # Scan program directory
    for md_file in sorted(PROGRAM_DIR.glob('*.md')):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        test_files.append({
            'path': md_file,
            'title': extract_title_from_markdown(content, md_file.name),
            'type': 'program',
            'academic_year': ACADEMIC_YEAR
        })
    
    # Scan syllabus directory
    for md_file in sorted(SYLLABUS_DIR.glob('*.md')):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        test_files.append({
            'path': md_file,
            'title': extract_title_from_markdown(content, md_file.name),
            'type': 'syllabus',
            'academic_year': ACADEMIC_YEAR
        })
    
    # Scan policy directory
    for md_file in sorted(POLICY_DIR.glob('*.md')):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        test_files.append({
            'path': md_file,
            'title': extract_title_from_markdown(content, md_file.name),
            'type': 'policy',
            'academic_year': ACADEMIC_YEAR
        })
    
    return test_files


# Get all files dynamically
TEST_FILES = get_all_test_files()


async def create_documents_in_db():
    """Create documents in PostgreSQL"""
    logger.info("=" * 60)
    logger.info("Step 1: Creating documents in PostgreSQL")
    logger.info("=" * 60)
    
    created_docs = []
    
    async with AsyncSessionLocal() as db:
        for file_info in TEST_FILES:
            # Read file content
            with open(file_info['path'], 'r', encoding='utf-8') as f:
                body = f.read()
            
            logger.info(f"Creating document: {file_info['title']}")
            logger.info(f"  - File: {file_info['path'].name}")
            logger.info(f"  - Type: {file_info['type']}")
            logger.info(f"  - Body length: {len(body)} chars")
            
            # Create document
            doc = await document_repository.create_document(
                db=db,
                user_id=USER_ID,
                title=file_info['title'],
                body=body,
                doc_type=file_info['type'],
                academic_year=file_info['academic_year']
            )
            
            logger.info(f"  ✅ Created document ID: {doc.id}")
            created_docs.append({
                'id': doc.id,
                'title': doc.title,
                'body': body,
                'type': doc.type,
                'academic_year': doc.academic_year
            })
    
    return created_docs


async def ingest_documents(docs: list):
    """Ingest documents into Elasticsearch"""
    logger.info("\n" + "=" * 60)
    logger.info("Step 2: Ingesting documents into Elasticsearch")
    logger.info("=" * 60)
    
    # Connect to Elasticsearch
    logger.info("Connecting to Elasticsearch...")
    await es_client.connect()
    
    ingestion_results = []
    
    for doc in docs:
        logger.info(f"\nIngesting document {doc['id']}: {doc['title']}")
        
        try:
            result = await document_ingestion_service.ingest_document(
                doc_id=doc['id'],
                title=doc['title'],
                body=doc['body'],
                doc_type=doc['type'],
                academic_year=doc['academic_year']
            )
            
            logger.info(f"  ✅ Ingestion complete:")
            logger.info(f"     - Sections indexed: {result['sections_indexed']}")
            logger.info(f"     - Chunks indexed: {result['chunks_indexed']}")
            logger.info(f"     - Sections failed: {result['sections_failed']}")
            logger.info(f"     - Chunks failed: {result['chunks_failed']}")
            
            ingestion_results.append(result)
            
        except Exception as e:
            logger.error(f"  ❌ Failed to ingest document {doc['id']}: {e}")
            raise
    
    return ingestion_results


async def export_to_json(doc_ids: list):
    """Export sections, chunks, and docs to JSON files"""
    logger.info("\n" + "=" * 60)
    logger.info("Step 3: Exporting data to JSON files")
    logger.info("=" * 60)
    
    # Create output directory if not exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Collect all sections and chunks from ES
    all_sections = []
    all_chunks = []
    
    for doc_id in doc_ids:
        logger.info(f"\nFetching ES data for document {doc_id}...")
        
        # Get sections
        sections = await es_client.get_sections_by_doc_id(doc_id)
        for section in sections:
            section.pop('embedding', None)  # Remove embedding (too large)
        all_sections.extend(sections)
        logger.info(f"  - Retrieved {len(sections)} sections")
        
        # Get chunks
        chunks = await es_client.get_chunks_by_doc_id(doc_id)
        for chunk in chunks:
            chunk.pop('embedding', None)  # Remove embedding (too large)
        all_chunks.extend(chunks)
        logger.info(f"  - Retrieved {len(chunks)} chunks")
    
    # Get all documents from PostgreSQL
    logger.info("\nFetching all documents from PostgreSQL...")
    all_docs = []
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document))
        documents = result.scalars().all()
        
        for doc in documents:
            all_docs.append({
                'id': doc.id,
                'user_id': doc.user_id,
                'title': doc.title,
                'type': doc.type,
                'academic_year': doc.academic_year,
                'body': doc.body[:500] + '...' if len(doc.body) > 500 else doc.body,  
                'body_length': len(doc.body),
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'updated_at': doc.updated_at.isoformat() if doc.updated_at else None
            })
    
    logger.info(f"  - Retrieved {len(all_docs)} documents from DB")
    
    # Write JSON files
    sections_file = OUTPUT_DIR / 'test_output_sections.json'
    chunks_file = OUTPUT_DIR / 'test_output_chunks.json'
    docs_file = OUTPUT_DIR / 'test_output_docs.json'
    
    # Export sections
    with open(sections_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_count': len(all_sections),
            'sections': all_sections
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"\n✅ Exported {len(all_sections)} sections to: {sections_file}")
    
    # Export chunks
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_count': len(all_chunks),
            'chunks': all_chunks
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Exported {len(all_chunks)} chunks to: {chunks_file}")
    
    # Export docs
    with open(docs_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_count': len(all_docs),
            'documents': all_docs
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Exported {len(all_docs)} documents to: {docs_file}")
    
    return {
        'sections_file': str(sections_file),
        'chunks_file': str(chunks_file),
        'docs_file': str(docs_file),
        'sections_count': len(all_sections),
        'chunks_count': len(all_chunks),
        'docs_count': len(all_docs)
    }


async def reset_all():
    """Reset ES indices and clear PostgreSQL documents"""
    logger.info("=" * 60)
    logger.info("RESET: Clearing all data before ingestion")
    logger.info("=" * 60)
    
    # Connect to ES
    await es_client.connect()
    
    # Reset ES indices
    logger.info("\n🗑️  Deleting old ES indices...")
    await es_client.delete_indices()
    
    logger.info("✨ Creating new ES indices...")
    await es_client.create_indices()
    
    stats = await es_client.get_index_stats()
    logger.info(f"✅ ES Indices ready: Sections={stats['sections']}, Chunks={stats['chunks']}")
    
    await es_client.close()
    
    # Clear PostgreSQL documents
    logger.info("\n🗑️  Clearing PostgreSQL documents...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("DELETE FROM documents"))
        deleted_count = result.rowcount
        await db.execute(text("ALTER SEQUENCE documents_id_seq RESTART WITH 1"))
        await db.commit()
    
    logger.info(f"✅ Deleted {deleted_count} documents, reset ID sequence to 1")
    logger.info("=" * 60 + "\n")


async def main(reset: bool = False):
    """Main test function"""
    
    # Reset if requested
    if reset:
        await reset_all()
    
    logger.info("=" * 60)
    logger.info("Document Ingestion Integration Test")
    logger.info("=" * 60)
    logger.info(f"Test files: {len(TEST_FILES)} files")
    logger.info(f"User ID: {USER_ID}")
    
    try:
        # Step 1: Create documents in PostgreSQL
        created_docs = await create_documents_in_db()
        doc_ids = [doc['id'] for doc in created_docs]
        
        # Step 2: Ingest into Elasticsearch
        await ingest_documents(created_docs)
        
        # Step 3: Export to JSON
        export_result = await export_to_json(doc_ids)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST COMPLETE - SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Documents created: {len(created_docs)}")
        logger.info(f"Document IDs: {doc_ids}")
        logger.info(f"\nOutput files:")
        logger.info(f"  - Sections ({export_result['sections_count']}): {export_result['sections_file']}")
        logger.info(f"  - Chunks ({export_result['chunks_count']}): {export_result['chunks_file']}")
        logger.info(f"  - Docs ({export_result['docs_count']}): {export_result['docs_file']}")
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        # Close ES connection
        await es_client.close()
        logger.info("\n✅ Elasticsearch connection closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Document Ingestion Integration Test")
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset ES indices and clear PostgreSQL documents before ingestion"
    )
    args = parser.parse_args()
    asyncio.run(main(reset=args.reset))
