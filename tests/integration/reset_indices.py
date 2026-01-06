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

async def main(reset: bool = False):
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




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Document Ingestion Integration Test")
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset ES indices and clear PostgreSQL documents before ingestion"
    )
    args = parser.parse_args()
    asyncio.run(main(reset=args.reset))
