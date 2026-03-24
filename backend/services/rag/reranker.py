"""
Reranker module — placeholder for future cross-encoder reranking.

Currently the hybrid_search module uses RRF for result fusion.
A cross-encoder reranker (e.g., cross-encoder/ms-marco-MiniLM-L-6-v2) can be
added here to further improve retrieval quality if needed.
"""


def rerank(query: str, results: list[dict], top_k: int = 6) -> list[dict]:
    """
    Pass-through reranker. Currently returns results as-is.
    Replace with cross-encoder reranking for production use.
    """
    return results[:top_k]
