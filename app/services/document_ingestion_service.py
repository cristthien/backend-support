"""
Document Ingestion Service - Handles chunking, embedding, and ES indexing for documents
"""
import logging
from typing import Dict, List, Optional

from app.clients.elasticsearch import es_client
from app.clients.ollama import ollama_client
from app.utils.chunker import MarkdownStructureChunker

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """
    Service for ingesting documents into Elasticsearch
    
    Handles:
    - Markdown chunking into sections + chunks
    - Embedding generation via Ollama
    - Bulk indexing to Elasticsearch
    - Document deletion and re-ingestion
    """
    
    def __init__(self):
        self.chunker = MarkdownStructureChunker()
    
    async def ingest_document(
        self,
        doc_id: int,
        title: str,
        body: str,
        doc_type: str = "program",
        academic_year: Optional[str] = None
    ) -> Dict:
        """
        Ingest a document into Elasticsearch
        
        Args:
            doc_id: PostgreSQL document ID
            title: Document title
            body: Markdown content
            doc_type: Document type (program, syllabus, etc.)
            academic_year: Academic year (e.g. "2024-2025")
            
        Returns:
            Dict with ingestion statistics
        """
        logger.info(f"Starting ingestion for document {doc_id}: {title}")
        
        # Chunk markdown content (async for LLM-based table detection)
        result = await self.chunker.chunk_markdown(
            text=body,
            metadata={'source': f"doc_{doc_id}", 'doc_type': doc_type}
        )
        
        sections = result['sections']
        chunks = result['chunks']
        
        logger.info(f"Created {len(sections)} sections and {len(chunks)} chunks")
        
        # Extract major from first H1 heading (if exists)
        major = title  # Default to document title
        for section in sections:
            if section.get('level') == 1:
                major = section.get('title', title)
                break
        
        # Generate embeddings and add doc_id to each section
        processed_sections = []
        for i, section in enumerate(sections, 1):
            try:
                title_text = section.get('title', '')
                embedding = await ollama_client.generate_embedding(title_text)
                
                # Merge document-level fields into metadata
                section_metadata = {
                    **section.get('metadata', {}),
                    'doc_id': str(doc_id),
                    'major': major,
                    'academic_year': academic_year,
                    'doc_type': doc_type,
                }
                
                section_data = {
                    **{k: v for k, v in section.items() if k != 'metadata'},
                    'metadata': section_metadata,
                    'embedding': embedding
                }
                processed_sections.append(section_data)
                
                if i % 10 == 0:
                    logger.info(f"Processed {i}/{len(sections)} sections")
                    
            except Exception as e:
                logger.error(f"Failed to process section {i}: {e}")
                raise
        
        # Generate embeddings and add doc_id to each chunk
        processed_chunks = []
        for i, chunk in enumerate(chunks, 1):
            try:
                chunk_text = chunk.get('text', '')
                embedding = await ollama_client.generate_embedding(chunk_text)
                
                # Merge document-level fields into metadata
                chunk_metadata = {
                    **chunk.get('metadata', {}),
                    'doc_id': str(doc_id),
                    'major': major,
                    'academic_year': academic_year,
                    'doc_type': doc_type,
                }
                
                chunk_data = {
                    **{k: v for k, v in chunk.items() if k != 'metadata'},
                    'metadata': chunk_metadata,
                    'embedding': embedding
                }
                processed_chunks.append(chunk_data)
                
                if i % 20 == 0:
                    logger.info(f"Processed {i}/{len(chunks)} chunks")
                    
            except Exception as e:
                logger.error(f"Failed to process chunk {i}: {e}")
                raise
        
        # Bulk index to Elasticsearch
        logger.info(f"Indexing {len(processed_sections)} sections...")
        sections_success, sections_failed = await es_client.bulk_index_sections(processed_sections)
        
        logger.info(f"Indexing {len(processed_chunks)} chunks...")
        chunks_success, chunks_failed = await es_client.bulk_index_chunks(processed_chunks)
        
        result = {
            "doc_id": doc_id,
            "sections_indexed": sections_success,
            "chunks_indexed": chunks_success,
            "sections_failed": len(sections_failed) if sections_failed else 0,
            "chunks_failed": len(chunks_failed) if chunks_failed else 0
        }
        
        logger.info(f"Ingestion complete for document {doc_id}: {result}")
        return result
    
    async def delete_document(self, doc_id: int) -> Dict[str, int]:
        """
        Delete all sections and chunks for a document from Elasticsearch
        
        Args:
            doc_id: PostgreSQL document ID
            
        Returns:
            Dict with deletion counts
        """
        logger.info(f"Deleting document {doc_id} from Elasticsearch")
        return await es_client.delete_document_from_es(doc_id)
    
    async def reingest_document(
        self,
        doc_id: int,
        title: str,
        body: str,
        doc_type: str = "program",
        academic_year: Optional[str] = None
    ) -> Dict:
        """
        Re-ingest a document (delete existing + ingest new)
        
        Args:
            doc_id: PostgreSQL document ID
            title: Document title
            body: Markdown content
            doc_type: Document type
            academic_year: Academic year
            
        Returns:
            Dict with re-ingestion statistics
        """
        logger.info(f"Re-ingesting document {doc_id}")
        
        # Delete existing
        delete_result = await self.delete_document(doc_id)
        
        # Ingest new
        ingest_result = await self.ingest_document(
            doc_id=doc_id,
            title=title,
            body=body,
            doc_type=doc_type,
            academic_year=academic_year
        )
        
        return {
            **ingest_result,
            "previous_sections_deleted": delete_result["sections_deleted"],
            "previous_chunks_deleted": delete_result["chunks_deleted"]
        }
    
    async def get_document_sections(
        self,
        doc_id: int,
        level: Optional[int] = None
    ) -> List[Dict]:
        """
        Get sections for a document
        
        Args:
            doc_id: PostgreSQL document ID
            level: Optional heading level filter (2 = H2 sections)
            
        Returns:
            List of section dictionaries
        """
        return await es_client.get_sections_by_doc_id(doc_id, level)
    
    async def get_document_chunks(self, doc_id: int) -> List[Dict]:
        """
        Get chunks for a document
        
        Args:
            doc_id: PostgreSQL document ID
            
        Returns:
            List of chunk dictionaries
        """
        return await es_client.get_chunks_by_doc_id(doc_id)


# Global service instance
document_ingestion_service = DocumentIngestionService()
