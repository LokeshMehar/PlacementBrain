import uuid
from collections import defaultdict

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)


class VectorStore:
    """Qdrant-backed vector store for PlacementBrain."""

    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name

    def upsert_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> int:
        """Upsert chunks with their embeddings into Qdrant in batches of 100."""
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            payload = {**chunk["metadata"], "text": chunk["text"]}
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload=payload,
                )
            )

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=self.collection_name, points=batch)

        return len(points)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        source_type_filter: list[str] = None,
    ) -> list[dict]:
        """Search for similar vectors with optional source_type filtering."""
        search_filter = None
        if source_type_filter:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="source_type",
                        match=MatchAny(any=source_type_filter),
                    )
                ]
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=search_filter,
            limit=top_k,
        )

        output = []
        for hit in response.points:
            payload = dict(hit.payload or {})
            text = payload.pop("text", "")
            output.append({
                "text": text,
                "score": hit.score,
                "metadata": payload,
            })

        return output

    def delete_by_source_id(self, source_id: str) -> int:
        """Delete all points matching a source_id."""
        # First count how many exist
        count_result = self.client.count(
            collection_name=self.collection_name,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key="source_id",
                        match=MatchValue(value=source_id),
                    )
                ]
            ),
        )
        count = count_result.count

        # Delete them
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="source_id",
                            match=MatchValue(value=source_id),
                        )
                    ]
                )
            ),
        )

        return count

    def list_sources(self) -> list[dict]:
        """List all unique sources with their chunk counts."""
        sources = defaultdict(lambda: {"chunk_count": 0})
        offset = None

        while True:
            results, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            if not results:
                break

            for point in results:
                payload = point.payload or {}
                sid = payload.get("source_id", "unknown")
                if sid not in sources:
                    sources[sid] = {
                        "source_id": sid,
                        "filename": payload.get("filename", "unknown"),
                        "source_type": payload.get("source_type", "text"),
                        "chunk_count": 0,
                        "created_at": payload.get("created_at", ""),
                    }
                sources[sid]["chunk_count"] += 1

            offset = next_offset
            if offset is None:
                break

        return list(sources.values())

    def get_chunks_by_source_id(self, source_id: str) -> list[dict]:
        """Get all chunks for a given source_id."""
        results, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="source_id",
                        match=MatchValue(value=source_id),
                    )
                ]
            ),
            limit=10000,
            with_payload=True,
            with_vectors=False,
        )

        chunks = []
        for point in results:
            payload = point.payload or {}
            chunks.append({
                "id": str(point.id),
                "text": payload.get("text", ""),
                "metadata": {k: v for k, v in payload.items() if k != "text"},
            })

        return chunks
