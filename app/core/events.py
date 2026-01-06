"""
Application lifecycle event handlers
"""
import logging
from app.core.config import settings
from app.clients.elasticsearch import es_client

logger = logging.getLogger(__name__)


async def startup_handler() -> None:
    """
    Execute startup tasks
    
    - Connect to Elasticsearch
    - Create indices if they don't exist
    - Initialize other external services
    """
    logger.info("Starting RAG backend...")
    
    # Connect to Elasticsearch
    logger.info(f"Connecting to Elasticsearch at {settings.elasticsearch_url}")
    await es_client.connect()
    
    # Create indices if they don't exist
    logger.info("Ensuring Elasticsearch indices exist...")
    await es_client.create_indices(recreate=False)
    
    logger.info("✅ RAG backend ready")


async def shutdown_handler() -> None:
    """
    Execute shutdown tasks
    
    - Close Elasticsearch connections
    - Cleanup resources
    """
    logger.info("Shutting down RAG backend...")
    
    # Close Elasticsearch connection
    await es_client.close()
    
    logger.info("✅ RAG backend stopped")
