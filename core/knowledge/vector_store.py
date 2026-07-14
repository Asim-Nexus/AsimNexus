"""
AsimNexus — ChromaDB-backed Vector Store
=========================================
Provides a simple interface for storing and querying text embeddings
via ChromaDB with an in-memory fallback.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    logger.warning("chromadb not installed — using in-memory fallback")


class VectorStore:
    """
    ChromaDB-backed vector store with automatic in-memory fallback.

    Usage::

        store = VectorStore()
        store.add(ids=["1"], texts=["Hello"], metadatas=[{"source": "test"}])
        results = store.query("Hello", top_k=5)
    """

    def __init__(
        self,
        persist_dir: str = "knowledge/vector_store",
        collection_name: str = "nepal_knowledge",
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embed_model = "all-MiniLM-L6-v2"
        self._lock = threading.Lock()
        self._chroma_collection = None
        self._fallback_store: Optional[Dict[str, Any]] = None
        self._init_store()

    def _init_store(self) -> None:
        """Initialise the underlying store (ChromaDB or fallback)."""
        if HAS_CHROMADB:
            try:
                client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                self._chroma_collection = client.get_or_create_collection(
                    name=self.collection_name,
                )
                logger.info(
                    "VectorStore initialised — collection=%s, backend=chromadb",
                    self.collection_name,
                )
                return
            except Exception as exc:
                logger.warning(
                    "ChromaDB init failed (%s) — falling back to in-memory", exc,
                )
        self._init_fallback()

    def _init_fallback(self) -> None:
        """Initialise the in-memory fallback store."""
        self._fallback_store = {
            "ids": [],
            "texts": [],
            "metadatas": [],
        }
        logger.info(
            "VectorStore initialised — collection=%s, backend=memory",
            self.collection_name,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add documents to the store."""
        if not ids or not texts:
            return
        if metadatas is None:
            metadatas = [{}] * len(ids)

        # ChromaDB requires non-empty metadata dicts; ensure each has at least one key
        chroma_metadatas = [
            (m if m else {"source": "unknown"}) for m in metadatas
        ]

        if self._chroma_collection is not None:
            try:
                self._chroma_collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=chroma_metadatas,
                )
                return
            except Exception as exc:
                logger.warning("ChromaDB add failed (%s) — falling back", exc)
                self._init_fallback()

        if self._fallback_store is not None:
            with self._lock:
                self._fallback_store["ids"].extend(ids)
                self._fallback_store["texts"].extend(texts)
                self._fallback_store["metadatas"].extend(metadatas or [])

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add texts and return their IDs (legacy interface)."""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        self.add(ids=ids, texts=texts, metadatas=metadatas)
        return ids

    def query(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query the store and return results.

        Returns a dict with keys: ``documents``, ``metadatas``, ``distances``, ``ids``.
        """
        if self._chroma_collection is not None:
            try:
                where_filter = where or {}
                results = self._chroma_collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where=where_filter if where_filter else None,
                )
                return {
                    "documents": results.get("documents", [[]]),
                    "metadatas": results.get("metadatas", [[]]),
                    "distances": results.get("distances", [[]]),
                    "ids": results.get("ids", [[]]),
                }
            except Exception as exc:
                logger.warning("ChromaDB query failed (%s) — falling back", exc)
                self._init_fallback()

        if self._fallback_store is not None:
            with self._lock:
                texts = self._fallback_store["texts"]
                # Simple keyword matching fallback
                query_lower = query.lower()
                matched_texts = []
                matched_metadatas = []
                matched_ids = []
                matched_distances = []
                for i, text in enumerate(texts):
                    if query_lower in text.lower():
                        matched_texts.append(text)
                        matched_metadatas.append(
                            self._fallback_store["metadatas"][i]
                            if i < len(self._fallback_store["metadatas"])
                            else {}
                        )
                        matched_ids.append(
                            self._fallback_store["ids"][i]
                            if i < len(self._fallback_store["ids"])
                            else ""
                        )
                        matched_distances.append(0.5)
                return {
                    "documents": [matched_texts[:top_k]],
                    "metadatas": [matched_metadatas[:top_k]],
                    "distances": [matched_distances[:top_k]],
                    "ids": [matched_ids[:top_k]],
                }

        return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    def similarity_search(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Alias for query that returns a list of dicts (legacy)."""
        result = self.query(query, top_k=k)
        docs = []
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        for i in range(len(documents)):
            docs.append({
                "text": documents[i],
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "score": 1.0 / (1.0 + distances[i]) if distances else 1.0,
                "id": ids[i] if i < len(ids) else "",
            })
        return docs

    def update(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Update existing documents."""
        if self._chroma_collection is not None:
            try:
                self._chroma_collection.update(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                )
                return
            except Exception as exc:
                logger.warning("ChromaDB update failed (%s)", exc)

        # Fallback: delete and re-add
        self.delete(ids)
        self.add(ids=ids, texts=texts, metadatas=metadatas)

    def delete(self, ids: List[str]) -> None:
        """Delete documents by IDs."""
        if self._chroma_collection is not None:
            try:
                self._chroma_collection.delete(ids=ids)
                return
            except Exception as exc:
                logger.warning("ChromaDB delete failed (%s)", exc)

        if self._fallback_store is not None:
            with self._lock:
                for doc_id in ids:
                    if doc_id in self._fallback_store["ids"]:
                        idx = self._fallback_store["ids"].index(doc_id)
                        self._fallback_store["ids"].pop(idx)
                        self._fallback_store["texts"].pop(idx)
                        self._fallback_store["metadatas"].pop(idx)

    def peek(self, limit: int = 10) -> Dict[str, Any]:
        """Peek at documents in the store."""
        if self._chroma_collection is not None:
            try:
                results = self._chroma_collection.peek(limit=limit)
                return {
                    "documents": results.get("documents", []),
                    "metadatas": results.get("metadatas", []),
                    "ids": results.get("ids", []),
                }
            except Exception as exc:
                logger.warning("ChromaDB peek failed (%s)", exc)

        if self._fallback_store is not None:
            with self._lock:
                count = min(limit, len(self._fallback_store["texts"]))
                return {
                    "documents": self._fallback_store["texts"][:count],
                    "metadatas": self._fallback_store["metadatas"][:count],
                    "ids": self._fallback_store["ids"][:count],
                }

        return {"documents": [], "metadatas": [], "ids": []}

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        if self._chroma_collection is not None:
            try:
                # Delete all documents by passing all current IDs
                all_ids = self._chroma_collection.get()["ids"]
                if all_ids:
                    self._chroma_collection.delete(ids=all_ids)
                self._chroma_collection = None
            except Exception as exc:
                logger.warning("ChromaDB delete_collection failed (%s)", exc)
        self._fallback_store = None

    def count(self) -> int:
        """Return the number of documents in the store."""
        if self._chroma_collection is not None:
            try:
                return self._chroma_collection.count()
            except Exception:
                pass
        if self._fallback_store is not None:
            with self._lock:
                return len(self._fallback_store["texts"])
        return 0

    def reset(self) -> None:
        """Reset the store (delete and re-initialise)."""
        self.delete_collection()
        self._init_store()
