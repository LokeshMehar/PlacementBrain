import datetime
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from core.config import settings
from core.dependencies import get_bm25_index, get_embedder, get_vectorstore, get_semantic_cache
from models.schemas import IngestResponse, SourceType
from services.ingestion import dispatcher
from services.ingestion.repo_loader import load_repo

router = APIRouter()


def _stamp_created_at(chunks: list[dict]) -> None:
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for chunk in chunks:
        if "metadata" not in chunk:
            chunk["metadata"] = {}
        chunk["metadata"]["created_at"] = created_at



# Request body for repo ingestion
class RepoRequest(BaseModel):
    repo_url: str


# Request body for text ingestion
class TextRequest(BaseModel):
    text: str
    filename: str
    source_type: str = "text"


# Extension to source type mapping
EXT_MAP = {
    ".pdf": "pdf",
    ".xlsx": "excel",
    ".xls": "excel",
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".java": "code",
    ".cpp": "code",
    ".hpp": "code",
    ".h": "code",
    ".html": "code",
    ".css": "code",
    ".md": "markdown",
    ".txt": "text",
    ".json": "text",
}


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    source_type: str = Form(None),
    embedder=Depends(get_embedder),
    vectorstore=Depends(get_vectorstore),
    bm25=Depends(get_bm25_index),
    cache=Depends(get_semantic_cache),
):
    """Upload and ingest a file into the knowledge base."""
    source_id = str(uuid4())
    filename = file.filename or "unknown"

    # Auto-detect source_type from extension if not provided
    if not source_type:
        ext = os.path.splitext(filename)[1].lower()
        source_type = EXT_MAP.get(ext, "text")

    # Save file to disk
    file_path = os.path.join(settings.upload_dir, f"{source_id}_{filename}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Dispatch to the correct loader
    chunks = dispatcher.dispatch(file_path, source_id, filename, source_type)

    if not chunks:
        return IngestResponse(
            source_id=source_id,
            filename=filename,
            source_type=source_type,
            chunk_count=0,
            status="no_content",
        )

    _stamp_created_at(chunks)

    # Embed all chunks
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_batch(texts)

    # Upsert to vector store
    count = vectorstore.upsert_chunks(chunks, embeddings)

    # Rebuild BM25 index
    bm25.rebuild_after_ingest()

    # Clear semantic cache since context has changed
    cache.clear()

    return IngestResponse(
        source_id=source_id,
        filename=filename,
        source_type=source_type,
        chunk_count=count,
        status="success",
    )


@router.post("/repo", response_model=IngestResponse)
async def ingest_repo(
    body: RepoRequest,
    embedder=Depends(get_embedder),
    vectorstore=Depends(get_vectorstore),
    bm25=Depends(get_bm25_index),
    cache=Depends(get_semantic_cache),
):
    """Clone and ingest a Git repository."""
    source_id = str(uuid4())

    chunks = load_repo(body.repo_url, source_id)

    if not chunks:
        return IngestResponse(
            source_id=source_id,
            filename=body.repo_url,
            source_type="repo",
            chunk_count=0,
            status="no_content",
        )

    _stamp_created_at(chunks)

    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_batch(texts)
    count = vectorstore.upsert_chunks(chunks, embeddings)
    bm25.rebuild_after_ingest()

    # Clear semantic cache since context has changed
    cache.clear()

    return IngestResponse(
        source_id=source_id,
        filename=body.repo_url,
        source_type="repo",
        chunk_count=count,
        status="success",
    )


@router.post("/text", response_model=IngestResponse)
async def ingest_text(
    body: TextRequest,
    embedder=Depends(get_embedder),
    vectorstore=Depends(get_vectorstore),
    bm25=Depends(get_bm25_index),
    cache=Depends(get_semantic_cache),
):
    """Ingest raw text directly."""
    source_id = str(uuid4())

    # Write text to a temp file and process
    file_path = os.path.join(settings.upload_dir, f"{source_id}_{body.filename}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(body.text)

    chunks = dispatcher.dispatch(file_path, source_id, body.filename, body.source_type)

    if not chunks:
        return IngestResponse(
            source_id=source_id,
            filename=body.filename,
            source_type=body.source_type,
            chunk_count=0,
            status="no_content",
        )

    _stamp_created_at(chunks)

    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_batch(texts)
    count = vectorstore.upsert_chunks(chunks, embeddings)
    bm25.rebuild_after_ingest()

    # Clear semantic cache since context has changed
    cache.clear()

    return IngestResponse(
        source_id=source_id,
        filename=body.filename,
        source_type=body.source_type,
        chunk_count=count,
        status="success",
    )
