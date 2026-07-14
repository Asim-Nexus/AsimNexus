"""
AsimNexus — Embeddings Service
===============================
Wrapper around sentence-transformers for generating text embeddings.
Falls back to a simple hash-based embedding if sentence-transformers is unavailable.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed — using fallback embeddings")


class EmbeddingsService:
    """
    Generates text embeddings using sentence-transformers.
    Falls back to a simple deterministic embedding for testing.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self._model = SentenceTransformer(model_name)
                logger.info("EmbeddingsService loaded model: %s", model_name)
            except Exception as exc:
                logger.warning("Failed to load model %s: %s", model_name, exc)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if self._model is not None:
            embeddings = self._model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        return [self._fallback_embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        return self.embed([text])[0]

    def get_embedding(self, text: str) -> List[float]:
        """Alias for embed_query — generate embedding for a single text."""
        return self.embed_query(text)

    def _fallback_embed(self, text: str) -> List[float]:
        """Simple deterministic fallback embedding based on character codes."""
        import hashlib
        # Create a 384-dimensional deterministic embedding
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Expand to 384 dims using repeated hashing
        result = []
        for i in range(384):
            h = hashlib.sha256(hash_bytes + str(i).encode()).digest()
            val = int.from_bytes(h[:4], "big") / 2**32
            result.append(val)
        return result
