from sentence_transformers import SentenceTransformer

from core.config import settings


class Embedder:
    """Wrapper around SentenceTransformer for embedding text."""

    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string and return as a list of floats."""
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return as a list of float lists."""
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, query: str) -> list[float]:
        """Embed a query string — same as embed_text, kept separate for clarity."""
        return self.embed_text(query)
