"""
Elasticsearch client wrapper with connection management and indexing utilities
"""
from elasticsearch import AsyncElasticsearch, helpers
from typing import List, Dict, Any, Optional
import logging

from app.core.config import settings
from app.schemas.elasticsearch import SECTIONS_INDEX_MAPPING, CHUNKS_INDEX_MAPPING

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearch client with connection management and index operations"""
    
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None
        self.sections_index = settings.elasticsearch_sections_index
        self.chunks_index = settings.elasticsearch_chunks_index
    
    async def connect(self):
        """Initialize Elasticsearch connection"""
        self.client = AsyncElasticsearch(
            hosts=[settings.elasticsearch_url],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        # Verify connection
        try:
            info = await self.client.info()
            logger.info(f"Connected to Elasticsearch {info['version']['number']}")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise
    
    async def close(self):
        """Close Elasticsearch connection"""
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch connection closed")
    
    async def create_indices(self, recreate: bool = False):
        """Create sections and chunks indices"""
        if recreate:
            await self.delete_indices()
        
        # Create sections index
        if not await self.client.indices.exists(index=self.sections_index):
            await self.client.indices.create(
                index=self.sections_index,
                body=SECTIONS_INDEX_MAPPING
            )
            logger.info(f"Created index: {self.sections_index}")
        else:
            logger.info(f"Index already exists: {self.sections_index}")
        
        # Create chunks index
        if not await self.client.indices.exists(index=self.chunks_index):
            await self.client.indices.create(
                index=self.chunks_index,
                body=CHUNKS_INDEX_MAPPING
            )
            logger.info(f"Created index: {self.chunks_index}")
        else:
            logger.info(f"Index already exists: {self.chunks_index}")
    
    async def delete_indices(self):
        """Delete sections and chunks indices"""
        for index in [self.sections_index, self.chunks_index]:
            if await self.client.indices.exists(index=index):
                await self.client.indices.delete(index=index)
                logger.info(f"Deleted index: {index}")
    
    async def bulk_index_sections(self, sections: List[Dict[str, Any]]):
        """Bulk index sections with doc_id mapping"""
        actions = [
            {
                "_index": self.sections_index,
                "_id": section["section_id"], 
                "_source": section
            }
            for section in sections
        ]
        
        success, failed = await helpers.async_bulk(
            self.client,
            actions,
            raise_on_error=False,
            stats_only=False
        )
        
        logger.info(f"Indexed {success} sections, {len(failed)} failed")
        return success, failed
    
    async def bulk_index_chunks(self, chunks: List[Dict[str, Any]]):
        """Bulk index chunks with doc_id mapping"""
        actions = [
            {
                "_index": self.chunks_index,
                "_id": chunk["chunk_id"],  # Use chunk_id as doc _id
                "_source": chunk
            }
            for chunk in chunks
        ]
        
        success, failed = await helpers.async_bulk(
            self.client,
            actions,
            raise_on_error=False,
            stats_only=False
        )
        
        logger.info(f"Indexed {success} chunks, {len(failed)} failed")
        return success, failed
    
    async def search_chunks(
        self,
        query_embedding: List[float],
        major: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search chunks using vector similarity with optional major filter
        
        Args:
            query_embedding: Query vector (1024 dims)
            major: Optional major filter (e.g., "Ngành Công Nghệ Thông Tin")
            top_k: Number of results to return
            
        Returns:
            List of chunk results with scores
        """
        # Build knn query
        knn_query = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": 100
        }
        
        # Add major filter to knn if specified
        if major:
            knn_query["filter"] = {"term": {"metadata.major": major}}
        
        query = {"knn": knn_query}
        
        response = await self.client.search(
            index=self.chunks_index,
            body=query,
            size=top_k
        )
        
        results = []
        for hit in response["hits"]["hits"]:
            result = hit["_source"]
            result["score"] = hit["_score"]
            results.append(result)
        
        return results
    
    async def get_sections_by_ids(self, section_ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieve full sections by their IDs"""
        if not section_ids:
            return []
        
        response = await self.client.mget(
            index=self.sections_index,
            body={"ids": section_ids}
        )
        
        sections = []
        for doc in response["docs"]:
            if doc["found"]:
                sections.append(doc["_source"])
        
        return sections
    
    async def search_sections(
        self,
        query_embedding: List[float],
        major: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search sections directly using vector similarity
        NEW: For intent-based retrieval
        
        Args:
            query_embedding: Query vector (1024 dims)
            major: Optional major filter
            top_k: Number of results to return
            
        Returns:
            List of section results with scores
        """
        # Build knn query
        knn_query = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": top_k * 3
        }
        
        # Add major filter if specified
        if major:
            knn_query["filter"] = {"term": {"metadata.major": major}}
        
        query = {"knn": knn_query}
        
        response = await self.client.search(
            index=self.sections_index,
            body=query,
            size=top_k
        )
        
        results = []
        for hit in response["hits"]["hits"]:
            result = hit["_source"]
            result["score"] = hit["_score"]
            results.append(result)
        
        logger.info(f"Section search returned {len(results)} results")
        return results
    
    async def get_section_by_id(self, section_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single section by ID
        NEW: For hierarchy expansion
        
        Args:
            section_id: Section ID to retrieve
            
        Returns:
            Section document or None if not found
        """
        try:
            response = await self.client.get(
                index=self.sections_index,
                id=section_id
            )
            return response["_source"] if response["found"] else None
        except Exception as e:
            logger.warning(f"Section {section_id} not found: {e}")
            return None
    
    async def get_child_sections(
        self,
        parent_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all child sections of a parent section
        NEW: For hierarchical expansion
        
        Args:
            parent_id: Parent section ID
            
        Returns:
            List of child sections
        """
        if not parent_id:
            return []
        
        query = {
            "query": {
                "term": {"parent_section_id": parent_id}
            },
            "size": 100  # Max children per parent
        }
        
        response = await self.client.search(
            index=self.sections_index,
            body=query
        )
        
        children = [hit["_source"] for hit in response["hits"]["hits"]]
        logger.info(f"Found {len(children)} children for parent {parent_id}")
        
        return children
    
    async def get_sections_by_hierarchy_prefix(
        self,
        hierarchy_prefix: str,
        major: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all sections with hierarchy path starting with prefix
        NEW: For hierarchical expansion
        
        Example:
            hierarchy_prefix = "Ngành Công Nghệ Thông Tin > Các khối kiến thức"
            → returns all sections under "Các khối kiến thức"
        
        Args:
            hierarchy_prefix: Hierarchy path prefix to match
            major: Optional major filter
            
        Returns:
            List of matching sections
        """
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "prefix": {
                                "hierarchy_path.keyword": hierarchy_prefix
                            }
                        }
                    ]
                }
            },
            "size": 100
        }
        
        # Add major filter if specified
        if major:
            query_body["query"]["bool"]["filter"] = [
                {"term": {"metadata.major": major}}
            ]
        
        response = await self.client.search(
            index=self.sections_index,
            body=query_body
        )
        
        sections = [hit["_source"] for hit in response["hits"]["hits"]]
        logger.info(f"Found {len(sections)} sections with prefix '{hierarchy_prefix}'")
        
        return sections
    
    async def get_sections_by_level(
        self,
        level: int,
        major: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all sections at a specific hierarchy level
        NEW: For hierarchical analysis
        
        Args:
            level: Hierarchy level (1, 2, 3, 4, etc.)
            major: Optional major filter
            
        Returns:
            List of sections at specified level
        """
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"level": level}}
                    ]
                }
            },
            "size": 100
        }
        
        # Add major filter if specified
        if major:
            query_body["query"]["bool"]["filter"] = [
                {"term": {"metadata.major": major}}
            ]
        
        response = await self.client.search(
            index=self.sections_index,
            body=query_body
        )
        
        sections = [hit["_source"] for hit in response["hits"]["hits"]]
        logger.info(f"Found {len(sections)} sections at level {level}")
        
        return sections
    
    async def get_index_stats(self) -> Dict[str, int]:
        """Get count statistics for indices"""
        sections_count = await self.client.count(index=self.sections_index)
        chunks_count = await self.client.count(index=self.chunks_index)
        
        return {
            "sections": sections_count["count"],
            "chunks": chunks_count["count"]
        }
    
    # =========================================================================
    # Document-based operations (for API integration)
    # =========================================================================
    
    async def delete_sections_by_doc_id(self, doc_id: int) -> int:
        """
        Delete all sections belonging to a document
        
        Args:
            doc_id: PostgreSQL document ID
            
        Returns:
            Number of deleted sections
        """
        response = await self.client.delete_by_query(
            index=self.sections_index,
            body={
                "query": {
                    "term": {"metadata.doc_id": str(doc_id)}
                }
            },
            refresh=True
        )
        deleted = response.get("deleted", 0)
        logger.info(f"Deleted {deleted} sections for doc_id={doc_id}")
        return deleted
    
    async def delete_chunks_by_doc_id(self, doc_id: int) -> int:
        """
        Delete all chunks belonging to a document
        
        Args:
            doc_id: PostgreSQL document ID
            
        Returns:
            Number of deleted chunks
        """
        response = await self.client.delete_by_query(
            index=self.chunks_index,
            body={
                "query": {
                    "term": {"metadata.doc_id": str(doc_id)}
                }
            },
            refresh=True
        )
        deleted = response.get("deleted", 0)
        logger.info(f"Deleted {deleted} chunks for doc_id={doc_id}")
        return deleted
    
    async def delete_document_from_es(self, doc_id: int) -> Dict[str, int]:
        """
        Delete all sections and chunks for a document
        
        Args:
            doc_id: PostgreSQL document ID
            
        Returns:
            Dict with counts of deleted sections and chunks
        """
        sections_deleted = await self.delete_sections_by_doc_id(doc_id)
        chunks_deleted = await self.delete_chunks_by_doc_id(doc_id)
        
        logger.info(f"Deleted document {doc_id} from ES: {sections_deleted} sections, {chunks_deleted} chunks")
        
        return {
            "sections_deleted": sections_deleted,
            "chunks_deleted": chunks_deleted
        }
    
    async def get_sections_by_doc_id(
        self,
        doc_id: int,
        level: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all sections for a document, optionally filtered by level
        
        Args:
            doc_id: PostgreSQL document ID
            level: Optional heading level filter (1=H1, 2=H2, etc.)
            
        Returns:
            List of sections
        """
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"metadata.doc_id": str(doc_id)}}
                    ]
                }
            },
            "size": 1000,
            "sort": [{"level": "asc"}]
        }
        
        # Add level filter if specified
        if level is not None:
            query_body["query"]["bool"]["must"].append(
                {"term": {"level": level}}
            )
        
        response = await self.client.search(
            index=self.sections_index,
            body=query_body
        )
        
        sections = [hit["_source"] for hit in response["hits"]["hits"]]
        logger.info(f"Found {len(sections)} sections for doc_id={doc_id}" + (f" at level {level}" if level else ""))
        
        return sections
    
    async def get_chunks_by_doc_id(self, doc_id: int) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document
        
        Args:
            doc_id: PostgreSQL document ID
            
        Returns:
            List of chunks
        """
        response = await self.client.search(
            index=self.chunks_index,
            body={
                "query": {
                    "term": {"metadata.doc_id": str(doc_id)}
                },
                "size": 1000
            }
        )
        
        chunks = [hit["_source"] for hit in response["hits"]["hits"]]
        logger.info(f"Found {len(chunks)} chunks for doc_id={doc_id}")
        
        return chunks


# Global client instance
es_client = ElasticsearchClient()

