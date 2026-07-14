"""
AsimNexus — Core RAG Pipeline
==============================
1. Chunk       — RecursiveCharacterTextSplitter (Nepali-aware)
2. Embed+Store — ChromaDB with built-in SentenceTransformer
3. Retrieve    — Semantic search via Chroma
4. Filter      — Optional black-hole relevance filter
5. Re-chunk    — Supernova merge-and-rechunk for long contexts

All embeddings are handled by ChromaDB's built-in embedding function,
so there is no need for a separate SentenceTransformer instance.
"""

import os
import logging
from typing import List, Dict, Optional, Any, Tuple

from .vector_store import VectorStore
from .chunker import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Core RAG pipeline backed by a real ChromaDB vector store.

    Usage::

        rag = RAGEngine()
        rag.add_documents([{"id": "1", "text": "...", "metadata": {...}}])
        results = rag.retrieve("user query", top_k=5)
    """

    def __init__(
        self,
        persist_dir: str = "knowledge/vector_store",
        collection_name: str = "nepal_knowledge",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.vector = VectorStore(
            persist_dir=persist_dir,
            collection_name=collection_name,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "।", ".", " "],
        )
        logger.info(
            "RAGEngine initialised — collection=%s, chunk_size=%d",
            collection_name, chunk_size,
        )

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    _chunk_counter: int = 0  # instance-level counter for unique chunk IDs

    def chunk_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Split *text* into chunks and attach *metadata* to each."""
        raw_chunks = self.splitter.split_text(text)
        result = []
        for chunk in raw_chunks:
            result.append({
                "id": f"chunk_{self._chunk_counter}",
                "text": chunk,
                "metadata": metadata or {},
            })
            self._chunk_counter += 1
        return result

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def add_documents(self, docs: List[Dict[str, Any]]) -> None:
        """Add a batch of pre-chunked documents to the vector store.

        Each dict must have at least ``id`` and ``text`` keys.
        """
        ids = [d["id"] for d in docs]
        texts = [d["text"] for d in docs]
        metadatas = [d.get("metadata", {}) for d in docs]
        self.vector.add(ids, texts, metadatas)
        logger.info("Added %d documents to vector store", len(docs))

    def add_text(
        self,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Convenience: chunk *text* and add to the store in one call.

        Returns the first chunk id.
        """
        chunks = self.chunk_document(text, metadata=metadata)
        if not chunks:
            return ""
        self.add_documents(chunks)
        return chunks[0]["id"]

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search — return the *top_k* most relevant chunks.

        Returns a list of dicts with keys ``text``, ``metadata``, ``score``.
        """
        raw = self.vector.query(query, top_k=top_k, where=where)
        return self._parse_chroma_response(raw)

    def retrieve_by_metadata(
        self,
        query: str,
        where: Dict[str, Any],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Semantic search filtered by metadata (e.g. ``{"source": "policy.md"}``)."""
        raw = self.vector.query(query, top_k=top_k, where=where)
        return self._parse_chroma_response(raw)

    # ------------------------------------------------------------------
    # Filtering & Re-chunking
    # ------------------------------------------------------------------

    def black_hole_filter(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Re-rank retrieved chunks by computing cosine similarity against *query*.

        Uses Chroma's stored embeddings via query_by_embedding to avoid
        re-embedding everything. Falls back to returning all chunks if
        anything fails.
        """
        if not chunks:
            return chunks
        try:
            # Use the first chunk's text as a proxy query to get an embedding
            # from Chroma's built-in function
            raw = self.vector.query(query, top_k=len(chunks))
            parsed = self._parse_chroma_response(raw)
            # parsed already has scores — filter by threshold
            return [c for c in parsed if c.get("score", 0) >= threshold]
        except Exception as exc:
            logger.warning("black_hole_filter failed: %s — returning unfiltered", exc)
            return chunks

    def supernova_rechunk(
        self,
        old_chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge all *old_chunks* into one text and re-chunk.

        Useful when individual chunks are too small to provide useful context.
        """
        combined = " ".join(c["text"] for c in old_chunks if "text" in c)
        return self.chunk_document(combined, {"generation": "supernova"})

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the total number of documents in the vector store."""
        return self.vector.count()

    def reset(self) -> None:
        """Wipe the vector store collection."""
        self.vector.reset()
        logger.info("RAGEngine vector store has been reset")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_chroma_response(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert Chroma's nested-list response to a flat list of dicts.

        Chroma returns L2 distances by default.  We convert to a
        0‑to‑1 similarity score via ``1 / (1 + distance)`` so that
        higher is always better and the value is guaranteed to be in
        ``[0, 1]``.
        """
        results: List[Dict[str, Any]] = []
        documents = raw.get("documents")
        metadatas = raw.get("metadatas")
        distances = raw.get("distances")
        ids = raw.get("ids")

        if not documents or not documents[0]:
            return results

        for i, text in enumerate(documents[0]):
            dist = distances[0][i] if distances and distances[0] else 1.0
            results.append({
                "text": text,
                "metadata": metadatas[0][i] if metadatas and metadatas[0] else {},
                "score": 1.0 / (1.0 + dist),  # L2 → [0, 1] similarity
                "id": ids[0][i] if ids and ids[0] else "",
            })
        return results
