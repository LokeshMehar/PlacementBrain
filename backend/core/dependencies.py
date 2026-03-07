import functools

import redis
from langchain_groq import ChatGroq
from qdrant_client import QdrantClient

from core.config import settings
from services.rag.embedder import Embedder
from services.rag.vectorstore import VectorStore
from services.rag.bm25_index import BM25Index
from services.cache.semantic_cache import SemanticCache
from services.agent.tools import ToolFactory
from services.agent.agent import PlacementAgent


@functools.lru_cache()
def get_qdrant_client() -> QdrantClient:
    """Singleton Qdrant client."""
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


@functools.lru_cache()
def get_redis_client() -> redis.Redis:
    """Singleton Redis client."""
    return redis.from_url(settings.redis_url, decode_responses=True)


@functools.lru_cache()
def get_embedder() -> Embedder:
    """Singleton Embedder instance."""
    return Embedder()


@functools.lru_cache()
def get_vectorstore() -> VectorStore:
    """Singleton VectorStore backed by Qdrant."""
    client = get_qdrant_client()
    return VectorStore(client=client, collection_name=settings.collection_name)


@functools.lru_cache()
def get_bm25_index() -> BM25Index:
    """Singleton BM25 index — built from Qdrant on first call."""
    vs = get_vectorstore()
    index = BM25Index(vectorstore=vs)
    return index


@functools.lru_cache()
def get_semantic_cache() -> SemanticCache:
    """Singleton semantic cache backed by Redis."""
    return SemanticCache(
        redis_client=get_redis_client(),
        embedder=get_embedder(),
    )


@functools.lru_cache()
def get_llm() -> ChatGroq:
    """Singleton Groq LLM."""
    return ChatGroq(
        api_key=settings.groq_api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=4096,
        streaming=True,
    )


@functools.lru_cache()
def get_tool_factory() -> ToolFactory:
    """Singleton ToolFactory with all dependencies wired."""
    return ToolFactory(
        embedder=get_embedder(),
        vectorstore=get_vectorstore(),
        bm25=get_bm25_index(),
        llm=get_llm(),
    )


@functools.lru_cache()
def get_agent() -> PlacementAgent:
    """Singleton PlacementAgent with tools and memory."""
    factory = get_tool_factory()
    return PlacementAgent(
        llm=get_llm(),
        tools=factory.get_tools(),
        redis_client=get_redis_client(),
    )
