from fastapi import APIRouter, Depends

from core.dependencies import get_vectorstore
from models.schemas import DeleteResponse

router = APIRouter()


@router.get("")
async def list_sources(vectorstore=Depends(get_vectorstore)):
    """List all ingested sources with chunk counts."""
    sources = vectorstore.list_sources()
    return sources


@router.delete("/{source_id}", response_model=DeleteResponse)
async def delete_source(source_id: str, vectorstore=Depends(get_vectorstore)):
    """Delete a source and all its chunks."""
    count = vectorstore.delete_by_source_id(source_id)
    return DeleteResponse(
        success=True,
        message=f"Deleted {count} chunks for source {source_id}",
    )


@router.get("/{source_id}/chunks")
async def get_source_chunks(source_id: str, vectorstore=Depends(get_vectorstore)):
    """Get all chunks for a specific source — useful for debugging."""
    chunks = vectorstore.get_chunks_by_source_id(source_id)
    return {"source_id": source_id, "chunk_count": len(chunks), "chunks": chunks}
