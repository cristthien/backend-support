"""
Elasticsearch index mappings for sections and chunks
"""


from app.core.config import settings

SECTIONS_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},  # Link to PostgreSQL document
            "section_id": {"type": "keyword"},
            "parent_section_id": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "text": {
                "type": "text",
                "analyzer": "standard"
            },
            "hierarchy_path": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "level": {"type": "integer"},
            "major": {"type": "keyword"},
            "source": {"type": "keyword"},
            "embedding": {
                "type": "dense_vector",
                "dims": settings.ollama_embedding_model_dim,
                "index": True,
                "similarity": "cosine"
            },
            "tables": {
                "type": "object",
                "enabled": False  # Store but don't index (already in searchable_text)
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}

CHUNKS_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},  # Link to PostgreSQL document
            "chunk_id": {"type": "keyword"},
            "section_id": {"type": "keyword"},
            "text": {
                "type": "text",
                "analyzer": "standard"
            },
            "major": {"type": "keyword"},
            "source": {"type": "keyword"},
            "parent_section_id": {"type": "keyword"},
            "embedding": {
                "type": "dense_vector",
                "dims": settings.ollama_embedding_model_dim,
                "index": True,
                "similarity": "cosine"
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}
