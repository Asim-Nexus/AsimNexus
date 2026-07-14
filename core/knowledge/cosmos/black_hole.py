"""
BlackHole — Intelligent Relevance & Safety Filter
===================================================
Filters RAG chunks using embedding-based semantic similarity.
Only chunks that genuinely relate to the query pass through.
Also applies a "Dharma Veto" — filtering out content that
violates constitutional/ethical boundaries.
"""

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    EMBEDDER_READY = True
except ImportError:
    _model = None
    EMBEDDER_READY = False


# Keywords that trigger the Dharma Veto (safety filter)
_DHARMA_BLOCKED = [
    "हिंसा उक्साउने", "जातीय भेदभाव", "आतंकवाद",
    "बालशोषण", "अश्लील", "घृणा फैलाउने",
    "violence incitement", "terrorism", "child exploitation",
    "hate speech", "discrimination"
]


class BlackHole:
    """Cosmic filter: only relevant, safe knowledge survives the event horizon."""

    def __init__(self, similarity_threshold: float = 0.30):
        self.threshold = similarity_threshold

    # ── Dharma Veto ─────────────────────────────────────────────
    def filter_by_dharma(self, chunks: list) -> list:
        """Remove chunks that contain blocked (unsafe) content."""
        safe = []
        for chunk in chunks:
            text = chunk.get("text", "") if isinstance(chunk, dict) else str(chunk)
            lower = text.lower()
            if not any(kw in lower for kw in _DHARMA_BLOCKED):
                safe.append(chunk)
        return safe

    # ── Semantic Relevance Filter ───────────────────────────────
    def filter_by_relevance(
        self,
        query: str,
        chunks: list,
        threshold: float | None = None,
    ) -> list:
        """Keep only chunks whose cosine similarity to *query* exceeds the threshold."""
        th = threshold if threshold is not None else self.threshold

        if not EMBEDDER_READY or not chunks:
            return chunks

        try:
            # Encode query once
            q_vec = _model.encode([query], normalize_embeddings=True)[0]

            # Encode all chunk texts in a single batch (fast)
            texts = [
                (c.get("text", "") if isinstance(c, dict) else str(c))
                for c in chunks
            ]
            c_vecs = _model.encode(texts, normalize_embeddings=True)

            # Cosine similarities (dot product on L2-normalised vectors)
            sims = c_vecs @ q_vec

            # Keep chunks above threshold, sorted best-first
            scored = sorted(
                zip(chunks, sims),
                key=lambda pair: pair[1],
                reverse=True,
            )
            kept = [chunk for chunk, sim in scored if sim >= th]

            # Always return at least 1 chunk (the best match) if available
            if not kept and scored:
                kept = [scored[0][0]]

            return kept
        except Exception:
            # On any error, pass everything through (fail-open)
            return chunks

    # ── Combined Filter ─────────────────────────────────────────
    def filter(self, query: str, chunks: list, threshold: float | None = None) -> list:
        """Run Dharma + Relevance filter in sequence."""
        safe = self.filter_by_dharma(chunks)
        return self.filter_by_relevance(query, safe, threshold)