import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client.models import Distance, VectorParams

from core.config import settings
from core.dependencies import (
    get_bm25_index,
    get_qdrant_client,
    get_redis_client,
)
from routers import chat, ingest, sources
from routers import interview

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PlacementBrain API",
    description="Personal AI knowledge base for campus placement preparation",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(sources.router, prefix="/sources", tags=["Sources"])
app.include_router(interview.router, prefix="/interview", tags=["Interview"])


@app.get("/health")
async def health_check():
    """Check connectivity to Qdrant and Redis."""
    qdrant_ok = False
    redis_ok = False

    try:
        client = get_qdrant_client()
        client.get_collections()
        qdrant_ok = True
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")

    try:
        r = get_redis_client()
        r.ping()
        redis_ok = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")

    return {"status": "ok", "qdrant": qdrant_ok, "redis": redis_ok}


from services.db.sqlite_db import init_db

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    # 0. Initialize SQLite Database tables
    init_db()
    
    # 1. Create upload directory
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"Upload directory ensured at {settings.upload_dir}")

    # 2. Initialize Qdrant collection if it doesn't exist
    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if settings.collection_name not in collection_names:
            client.create_collection(
                collection_name=settings.collection_name,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 embedding dimension
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {settings.collection_name}")
        else:
            logger.info(f"Qdrant collection already exists: {settings.collection_name}")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")

    # 3. Warm up BM25 index
    try:
        bm25 = get_bm25_index()
        bm25.build_index()
        logger.info("BM25 index warmed up on startup")
    except Exception as e:
        logger.warning(f"BM25 index warm-up failed (may be empty): {e}")

    logger.info("🧠 PlacementBrain API ready")
