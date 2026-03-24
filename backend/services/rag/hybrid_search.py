from services.rag.embedder import Embedder
from services.rag.vectorstore import VectorStore
from services.rag.bm25_index import BM25Index


def hybrid_search(
    query: str,
    embedder: Embedder,
    vectorstore: VectorStore,
    bm25: BM25Index,
    top_k: int = 6,
    source_type_filter: list[str] = None,
) -> list[dict]:
    """
    Perform hybrid search combining semantic (vector) and BM25 (keyword) results
    using Reciprocal Rank Fusion (RRF).
    """
    # Get semantic results
    query_embedding = embedder.embed_query(query)
    semantic_results = vectorstore.search(
        query_embedding=query_embedding,
        top_k=20,
        source_type_filter=source_type_filter,
    )

    # Get BM25 results
    bm25_results = bm25.search(query, top_k=20, source_type_filter=source_type_filter)

    # Reciprocal Rank Fusion
    # Use first 100 chars of text as deduplication key
    rrf_scores: dict[str, dict] = {}
    k = 60  # RRF constant

    for rank, result in enumerate(semantic_results):
        key = result["text"][:100]
        if key not in rrf_scores:
            rrf_scores[key] = {
                "text": result["text"],
                "combined_score": 0.0,
                "metadata": result["metadata"],
                "sources": [],
            }
        rrf_scores[key]["combined_score"] += 1.0 / (rank + k)
        if "semantic" not in rrf_scores[key]["sources"]:
            rrf_scores[key]["sources"].append("semantic")

    for rank, result in enumerate(bm25_results):
        key = result["text"][:100]
        if key not in rrf_scores:
            rrf_scores[key] = {
                "text": result["text"],
                "combined_score": 0.0,
                "metadata": result["metadata"],
                "sources": [],
            }
        rrf_scores[key]["combined_score"] += 1.0 / (rank + k)
        if "bm25" not in rrf_scores[key]["sources"]:
            rrf_scores[key]["sources"].append("bm25")

    # Sort by combined RRF score and return top_k
    sorted_results = sorted(
        rrf_scores.values(),
        key=lambda x: x["combined_score"],
        reverse=True,
    )

    return sorted_results[:top_k]
