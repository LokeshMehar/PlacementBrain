import hashlib
import json

import numpy as np
import redis


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class SemanticCache:
    """Redis-backed semantic cache for LLM responses, partitioned by chat_id."""

    def __init__(
        self,
        redis_client: redis.Redis,
        embedder,
        similarity_threshold: float = 0.97,
        ttl_seconds: int = 3600,
    ):
        self.redis_client = redis_client
        self.embedder = embedder
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds

    def _exact_cache_key(self, chat_id: str, query: str) -> str:
        """Generate a 1-to-1 exact string cache key for a specific chat."""
        query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]
        return f"exactcache:{chat_id}:{query_hash}"

    def _sem_cache_key(self, chat_id: str, embedding: list[float]) -> str:
        """Generate a semantic cache key for a specific chat."""
        hash_str = hashlib.sha256(str(embedding).encode()).hexdigest()[:16]
        return f"semcache:{chat_id}:{hash_str}"

    def get(self, chat_id: str, query: str) -> str | None:
        """
        Check if an exact match or semantically similar query in this session has been cached.
        Returns the cached response if found, None otherwise.
        """
        # 1. Exact string match first (O(1) lookup, bypassing embedding generation)
        exact_key = self._exact_cache_key(chat_id, query)
        exact_data = self.redis_client.get(exact_key)
        if exact_data:
            return exact_data

        # 2. Semantic lookup
        query_embedding = self.embedder.embed_query(query)

        # Scan only semantic keys matching the current chat session context
        pattern = f"semcache:{chat_id}:*"
        for key in self.redis_client.scan_iter(match=pattern):
            try:
                cached_data = self.redis_client.get(key)
                if cached_data is None:
                    continue

                entry = json.loads(cached_data)
                cached_embedding = entry.get("embedding", [])
                similarity = cosine_similarity(query_embedding, cached_embedding)

                if similarity > self.similarity_threshold:
                    return entry.get("response")
            except (json.JSONDecodeError, KeyError):
                continue

        return None

    def set(self, chat_id: str, query: str, response: str) -> None:
        """Cache a query-response pair with both exact and semantic keys."""
        # 1. Set exact string cache
        exact_key = self._exact_cache_key(chat_id, query)
        self.redis_client.setex(exact_key, self.ttl_seconds, response)

        # 2. Set semantic cache
        embedding = self.embedder.embed_query(query)
        sem_key = self._sem_cache_key(chat_id, embedding)
        entry = json.dumps({
            "embedding": embedding,
            "response": response,
        })
        self.redis_client.setex(sem_key, self.ttl_seconds, entry)

    def clear(self) -> int:
        """Delete all semantic and exact cache entries. Returns count deleted."""
        keys = list(self.redis_client.scan_iter(match="semcache:*")) + list(self.redis_client.scan_iter(match="exactcache:*"))
        if keys:
            return self.redis_client.delete(*keys)
        return 0
