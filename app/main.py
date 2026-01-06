"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.events import startup_handler, shutdown_handler
from app.core.logging import setup_logging
from app.clients.elasticsearch import es_client
from app.routers import ingestion, query, auth, documents, chats, parse

# Configure logging
setup_logging(level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await startup_handler()
    
    yield
    
    # Shutdown
    await shutdown_handler()


# Create FastAPI app
app = FastAPI(
    title="RAG Backend API",
    description="RAG backend for educational program information with major-aware retrieval",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chats.router)
app.include_router(ingestion.router)
app.include_router(query.router)
app.include_router(parse.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Backend API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "auth": {
                "email_otp_request": "/api/auth/email/request-otp",
                "email_otp_verify": "/api/auth/email/verify-otp",
                "google_auth": "/api/auth/google",
                "current_user": "/api/auth/me"
            },
            "documents": "/api/docs",
            "chats": "/api/chats",
            "ingestion": "/api/ingest",
            "query": "/api/query",
            "parse": "/api/parse"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check Elasticsearch connection
        stats = await es_client.get_index_stats()
        
        return {
            "status": "healthy",
            "elasticsearch": "connected",
            "indices": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
