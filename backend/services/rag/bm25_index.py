import logging

import numpy as np
from rank_bm25 import BM25Okapi

from services.rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


class BM25Index:
    """In-memory BM25 index built from the Qdrant corpus."""

    def __init__(self, vectorstore: VectorStore):
        self.vectorstore = vectorstore
        self.index: BM25Okapi | None = None
        self.documents: list[dict] = []
        self.tokenized_corpus: list[list[str]] = []

    def build_index(self) -> None:
        """Scroll all points from Qdrant and build BM25 index."""
        logger.info("Building BM25 index from Qdrant corpus...")
        self.documents = []
        offset = None

        while True:
            results, next_offset = self.vectorstore.client.scroll(
                collection_name=self.vectorstore.collection_name,
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            if not results:
                break

            for point in results:
                payload = point.payload or {}
                text = payload.get("text", "")
                if text.strip():
                    self.documents.append({
                        "id": str(point.id),
                        "text": text,
                        "metadata": {k: v for k, v in payload.items() if k != "text"},
                    })

            offset = next_offset
            if offset is None:
                break

        if self.documents:
            self.tokenized_corpus = [doc["text"].lower().split() for doc in self.documents]
            self.index = BM25Okapi(self.tokenized_corpus)
            logger.info(f"BM25 index built with {len(self.documents)} documents")
        else:
            self.index = None
            logger.info("BM25 index: no documents found")

    def search(self, query: str, top_k: int = 10, source_type_filter: list[str] = None) -> list[dict]:
        """Search the BM25 index for matching documents."""
        if self.index is None or not self.documents:
            return []

        tokenized_query = query.lower().split()
        scores = self.index.get_scores(tokenized_query)

        # Get sorted indices in descending order
        sorted_indices = np.argsort(scores)[::-1]

        results = []
        for idx in sorted_indices:
            if len(results) >= top_k:
                break
            if scores[idx] > 0:
                doc = self.documents[idx]
                if source_type_filter and doc["metadata"].get("source_type") not in source_type_filter:
                    continue
                results.append({
                    "text": doc["text"],
                    "score": float(scores[idx]),
                    "metadata": doc["metadata"],
                })

        return results

    def rebuild_after_ingest(self) -> None:
        """Rebuild the index after new documents are ingested."""
        self.build_index()
