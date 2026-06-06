#!/usr/bin/env python3
"""
AsimNexus Vector DB — Consolidated Vector Store Wrapper.

Provides a 4-collection ChromaDB layer with full graceful degradation:
  ChromaDB → SQLite (stored embeddings as JSON blobs) → In-memory dict

Phase 4 of the 4-layer storage architecture.
"""

import os
import json
import math
import time
import logging
import hashlib
import asyncio
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("AsimNexus.VectorStore")

# ─── Constants ────────────────────────────────────────────────────────────────

_DEFAULT_CHROMADB_PATH = os.getenv("ASIM_VECTOR_DB_PATH", "data/chromadb")
_DEFAULT_FALLBACK_DB = os.getenv("ASIM_VECTOR_FALLBACK_PATH", "data/storage/vector_fallback.db")

# 4 named collections with metadata
COLLECTIONS = {
    "semantic_memory": {
        "description": "Long-term knowledge storage",
        "dim": 384,
        "ttl_hours": None,  # No TTL
    },
    "agent_context": {
        "description": "Agent conversation/session context",
        "dim": 384,
        "ttl_hours": 24,
    },
    "retrieval": {
        "description": "RAG document retrieval index",
        "dim": 384,
        "ttl_hours": None,  # No TTL
    },
    "clone_silos": {
        "description": "Per-clone isolated memory silos",
        "dim": 384,
        "ttl_hours": 168,  # 7 days
    },
}

_EMBEDDING_CACHE_SIZE = int(os.getenv("ASIM_EMBEDDING_CACHE_SIZE", "10000"))


# ─── Internal Helpers ─────────────────────────────────────────────────────────

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _dummy_embedding(text: str, dim: int = 384) -> List[float]:
    """Hash-based dummy embedding for fallback."""
    h = hashlib.sha256(text.encode()).digest()
    return [float(b) / 255.0 for b in h[:dim]] + [0.0] * max(0, dim - len(h))


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _expires_iso(ttl_hours: Optional[int]) -> Optional[str]:
    if ttl_hours is None:
        return None
    return (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat()


def _is_expired(expires_at: Optional[str]) -> bool:
    if expires_at is None:
        return False
    try:
        return datetime.utcnow() > datetime.fromisoformat(expires_at)
    except (ValueError, TypeError):
        return False


# ─── In-Memory Fallback Store ─────────────────────────────────────────────────

class _InMemoryStore:
    """
    Thread-safe in-memory vector store.
    Structure: {collection_name: {id: {embedding, metadata, content, created_at, expires_at}}}
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._data: Dict[str, Dict[str, Dict[str, Any]]] = {}

    async def _ensure_collection(self, collection: str):
        if collection not in self._data:
            self._data[collection] = {}

    async def store(self, collection: str, item_id: str, embedding: List[float],
                    metadata: Optional[Dict] = None, content: Optional[str] = None,
                    expires_at: Optional[str] = None) -> bool:
        async with self._lock:
            await self._ensure_collection(collection)
            self._data[collection][item_id] = {
                "embedding": embedding,
                "metadata": metadata or {},
                "content": content or "",
                "created_at": _now_iso(),
                "expires_at": expires_at,
            }
        return True

    async def get(self, collection: str, item_id: str) -> Optional[Dict]:
        async with self._lock:
            col = self._data.get(collection, {})
            entry = col.get(item_id)
            if entry is None:
                return None
            if _is_expired(entry.get("expires_at")):
                del col[item_id]
                return None
            return {
                "id": item_id,
                "score": 1.0,
                "metadata": entry["metadata"],
                "content": entry["content"],
                "embedding": entry["embedding"],
            }

    async def search(self, collection: str, query_vector: List[float],
                     top_k: int = 10, filter: Optional[Dict] = None) -> List[Dict]:
        async with self._lock:
            col = self._data.get(collection, {})
            scored = []
            for item_id, entry in list(col.items()):
                if _is_expired(entry.get("expires_at")):
                    del col[item_id]
                    continue
                if filter and not self._match_filter(entry["metadata"], filter):
                    continue
                sim = _cosine_similarity(query_vector, entry["embedding"])
                scored.append({
                    "id": item_id,
                    "score": sim,
                    "metadata": entry["metadata"],
                    "content": entry["content"],
                })
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:top_k]

    async def delete(self, collection: str, item_id: str) -> bool:
        async with self._lock:
            col = self._data.get(collection, {})
            if item_id in col:
                del col[item_id]
                return True
            return False

    async def list_ids(self, collection: str) -> List[str]:
        async with self._lock:
            col = self._data.get(collection, {})
            # Filter expired
            active = []
            for item_id, entry in list(col.items()):
                if _is_expired(entry.get("expires_at")):
                    del col[item_id]
                else:
                    active.append(item_id)
            return active

    async def count(self, collection: str) -> int:
        async with self._lock:
            col = self._data.get(collection, {})
            # Filter expired
            active_count = 0
            for item_id, entry in list(col.items()):
                if _is_expired(entry.get("expires_at")):
                    del col[item_id]
                else:
                    active_count += 1
            return active_count

    async def cleanup_expired(self) -> int:
        removed = 0
        async with self._lock:
            for collection, items in self._data.items():
                expired_ids = [
                    item_id for item_id, entry in items.items()
                    if _is_expired(entry.get("expires_at"))
                ]
                for item_id in expired_ids:
                    del items[item_id]
                    removed += 1
        return removed

    async def all_collections(self) -> List[str]:
        async with self._lock:
            return list(self._data.keys())

    def _match_filter(self, metadata: Dict, filter: Dict) -> bool:
        for k, v in filter.items():
            if metadata.get(k) != v:
                return False
        return True


# ─── SQLite Fallback Store ────────────────────────────────────────────────────

class _SQLiteVectorStore:
    """
    SQLite-based vector store using JSON blobs for embeddings.
    Table: vector_embeddings(id, collection, vector_json, metadata_json, content, created_at, expires_at)
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._init_db()

    def _init_db(self):
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_embeddings (
                    id TEXT NOT NULL,
                    collection TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    metadata_json TEXT DEFAULT '{}',
                    content TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    PRIMARY KEY (id, collection)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ve_collection
                ON vector_embeddings(collection)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ve_expires
                ON vector_embeddings(expires_at)
            """)
            conn.commit()

    async def store(self, collection: str, item_id: str, embedding: List[float],
                    metadata: Optional[Dict] = None, content: Optional[str] = None,
                    expires_at: Optional[str] = None) -> bool:
        loop = asyncio.get_event_loop()
        try:
            def _run():
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute(
                        """INSERT OR REPLACE INTO vector_embeddings
                           (id, collection, vector_json, metadata_json, content, created_at, expires_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            item_id, collection,
                            json.dumps(embedding),
                            json.dumps(metadata or {}),
                            content or "",
                            _now_iso(),
                            expires_at,
                        ),
                    )
                    conn.commit()
            await loop.run_in_executor(self._executor, _run)
            return True
        except Exception as e:
            logger.warning(f"⚠️  SQLite store failed: {e}")
            return False

    async def get(self, collection: str, item_id: str) -> Optional[Dict]:
        loop = asyncio.get_event_loop()

        def _run():
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM vector_embeddings WHERE id = ? AND collection = ?",
                    (item_id, collection),
                ).fetchone()
                return dict(row) if row else None

        try:
            row = await loop.run_in_executor(self._executor, _run)
            if row is None:
                return None
            if _is_expired(row.get("expires_at")):
                await self.delete(collection, item_id)
                return None
            embedding = json.loads(row["vector_json"])
            return {
                "id": row["id"],
                "score": 1.0,
                "metadata": json.loads(row["metadata_json"]),
                "content": row["content"],
                "embedding": embedding,
            }
        except Exception as e:
            logger.warning(f"⚠️  SQLite get failed: {e}")
            return None

    async def search(self, collection: str, query_vector: List[float],
                     top_k: int = 10, filter: Optional[Dict] = None) -> List[Dict]:
        loop = asyncio.get_event_loop()

        def _run():
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM vector_embeddings WHERE collection = ?",
                    (collection,),
                ).fetchall()
            return [dict(r) for r in rows]

        try:
            rows = await loop.run_in_executor(self._executor, _run)
        except Exception as e:
            logger.warning(f"⚠️  SQLite search query failed: {e}")
            return []

        scored = []
        for row in rows:
            if _is_expired(row.get("expires_at")):
                await self.delete(collection, row["id"])
                continue
            metadata = json.loads(row["metadata_json"])
            if filter and not self._match_filter(metadata, filter):
                continue
            try:
                embedding = json.loads(row["vector_json"])
                sim = _cosine_similarity(query_vector, embedding)
                scored.append({
                    "id": row["id"],
                    "score": sim,
                    "metadata": metadata,
                    "content": row["content"],
                })
            except (json.JSONDecodeError, KeyError):
                continue

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    async def delete(self, collection: str, item_id: str) -> bool:
        loop = asyncio.get_event_loop()

        def _run():
            with sqlite3.connect(self._db_path) as conn:
                cur = conn.execute(
                    "DELETE FROM vector_embeddings WHERE id = ? AND collection = ?",
                    (item_id, collection),
                )
                conn.commit()
                return cur.rowcount > 0

        try:
            return await loop.run_in_executor(self._executor, _run)
        except Exception:
            return False

    async def list_ids(self, collection: str) -> List[str]:
        loop = asyncio.get_event_loop()

        def _run():
            with sqlite3.connect(self._db_path) as conn:
                rows = conn.execute(
                    "SELECT id FROM vector_embeddings WHERE collection = ?",
                    (collection,),
                ).fetchall()
                return [r[0] for r in rows]

        try:
            return await loop.run_in_executor(self._executor, _run)
        except Exception:
            return []

    async def count(self, collection: str) -> int:
        loop = asyncio.get_event_loop()

        def _run():
            with sqlite3.connect(self._db_path) as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM vector_embeddings WHERE collection = ?",
                    (collection,),
                ).fetchone()
                return row[0] if row else 0

        try:
            return await loop.run_in_executor(self._executor, _run)
        except Exception:
            return 0

    async def cleanup_expired(self) -> int:
        loop = asyncio.get_event_loop()

        def _run():
            with sqlite3.connect(self._db_path) as conn:
                cur = conn.execute(
                    "DELETE FROM vector_embeddings WHERE expires_at IS NOT NULL AND expires_at < ?",
                    (_now_iso(),),
                )
                conn.commit()
                return cur.rowcount

        try:
            return await loop.run_in_executor(self._executor, _run)
        except Exception:
            return 0

    async def all_collections(self) -> List[str]:
        loop = asyncio.get_event_loop()

        def _run():
            with sqlite3.connect(self._db_path) as conn:
                rows = conn.execute(
                    "SELECT DISTINCT collection FROM vector_embeddings"
                ).fetchall()
                return [r[0] for r in rows]

        try:
            return await loop.run_in_executor(self._executor, _run)
        except Exception:
            return []

    def _match_filter(self, metadata: Dict, filter: Dict) -> bool:
        for k, v in filter.items():
            if metadata.get(k) != v:
                return False
        return True


# ─── Main VectorStore Class ───────────────────────────────────────────────────

class VectorStore:
    """
    Consolidated Vector DB layer for AsimNexus.

    Wraps ChromaDB with multi-collection support, TTL management,
    and automatic fallback to SQLite + in-memory.

    Fallback chain: ChromaDB → SQLite (stored embeddings) → In-memory dict
    """

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def __init__(self, chromadb_path: Optional[str] = None):
        self._chromadb_path = chromadb_path or os.getenv(
            "ASIM_VECTOR_DB_PATH", _DEFAULT_CHROMADB_PATH
        )
        self._fallback_db_path = os.getenv(
            "ASIM_VECTOR_FALLBACK_PATH", _DEFAULT_FALLBACK_DB
        )

        # Backend state
        self._mode: str = "in_memory"  # chromadb | sqlite | in_memory
        self._connected: bool = False
        self._chroma_client = None
        self._chroma_collections: Dict[str, Any] = {}
        self._chroma_available = False
        self._sqlite_store: Optional[_SQLiteVectorStore] = None
        self._memory_store: Optional[_InMemoryStore] = None

        # Embedding state
        self._sentence_model = None
        self._embedding_cache: OrderedDict = OrderedDict()
        self._executor = ThreadPoolExecutor(max_workers=4)

        # TTL configuration per collection
        self._collection_ttl: Dict[str, Optional[int]] = {
            name: info["ttl_hours"] for name, info in COLLECTIONS.items()
        }

        logger.info(
            f"🧠 VectorStore initialized — chromadb_path={self._chromadb_path}, "
            f"fallback={self._fallback_db_path}"
        )

    async def connect(self) -> bool:
        """
        Connect to ChromaDB persistent client. Create default collections.
        Fall back to SQLite at data/storage/vector_fallback.db, then in-memory dict.
        """
        # Attempt ChromaDB first
        if await self._try_chromadb():
            self._mode = "chromadb"
            self._connected = True
            logger.info("✅ VectorStore connected — mode=chromadb")
            return True

        # Fallback: SQLite
        try:
            self._sqlite_store = _SQLiteVectorStore(self._fallback_db_path)
            # Create default collections (no-op for SQLite, just ensure table exists)
            self._mode = "sqlite"
            self._connected = True
            logger.info(f"✅ VectorStore connected — mode=sqlite (path={self._fallback_db_path})")
            return True
        except Exception as e:
            logger.warning(f"⚠️  SQLite fallback init failed: {e}")

        # Final fallback: in-memory
        self._memory_store = _InMemoryStore()
        self._mode = "in_memory"
        self._connected = True
        logger.info("✅ VectorStore connected — mode=in_memory")
        return True

    async def close(self):
        """Close client and release resources."""
        self._chroma_client = None
        self._chroma_collections.clear()
        self._chroma_available = False
        self._sqlite_store = None
        self._memory_store = None
        self._connected = False
        self._embedding_cache.clear()
        logger.info("🔒 VectorStore closed")

    async def _try_chromadb(self) -> bool:
        """Try to initialize ChromaDB with multi-collection support."""
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            logger.warning("⚠️  chromadb not installed")
            return False

        try:
            Path(self._chromadb_path).mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(
                path=self._chromadb_path,
                settings=Settings(anonymized_telemetry=False, allow_reset=False),
            )

            # Create/get all 4 collections with HNSW index
            for col_name, col_info in COLLECTIONS.items():
                collection = self._chroma_client.get_or_create_collection(
                    name=col_name,
                    metadata={
                        "hnsw:space": "cosine",
                        "hnsw:construction_ef": 100,
                        "hnsw:M": 16,
                        "hnsw:search_ef": 50,
                        "description": col_info["description"],
                        "dim": col_info["dim"],
                    },
                )
                self._chroma_collections[col_name] = collection

            self._chroma_available = True
            logger.info(
                f"✅ ChromaDB initialized — path={self._chromadb_path}, "
                f"collections={list(self._chroma_collections.keys())}"
            )
            return True

        except Exception as e:
            logger.warning(f"⚠️  ChromaDB init failed: {e}")
            self._chroma_client = None
            self._chroma_collections.clear()
            self._chroma_available = False
            return False

    def _get_chroma_collection(self, collection: str):
        """Get a ChromaDB collection by name, or None."""
        return self._chroma_collections.get(collection)

    # ── Embedding ─────────────────────────────────────────────────────────

    def _get_sentence_model(self):
        """Lazy-load SentenceTransformer model."""
        if self._sentence_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("✅ SentenceTransformer model loaded (all-MiniLM-L6-v2)")
            except ImportError:
                logger.warning("⚠️  sentence-transformers not installed")
                return None
        return self._sentence_model

    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        if text in self._embedding_cache:
            self._embedding_cache.move_to_end(text)
            return self._embedding_cache[text]
        return None

    def _put_in_cache(self, text: str, embedding: List[float]):
        self._embedding_cache[text] = embedding
        self._embedding_cache.move_to_end(text)
        if len(self._embedding_cache) > _EMBEDDING_CACHE_SIZE:
            self._embedding_cache.popitem(last=False)

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text with caching."""
        cached = self._get_from_cache(text)
        if cached is not None:
            return cached

        model = self._get_sentence_model()
        if model is not None:
            try:
                embedding = model.encode(text).tolist()
                self._put_in_cache(text, embedding)
                return embedding
            except Exception as e:
                logger.warning(f"⚠️  SentenceTransformer encoding failed: {e}")

        # Dummy fallback
        embedding = _dummy_embedding(text, 384)
        self._put_in_cache(text, embedding)
        return embedding

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        model = self._get_sentence_model()
        if model is not None:
            try:
                embeddings = model.encode(texts).tolist()
                for t, e in zip(texts, embeddings):
                    self._put_in_cache(t, e)
                return embeddings
            except Exception:
                pass
        # Fallback: individual
        return [self._generate_embedding(t) for t in texts]

    async def _generate_embedding_async(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._generate_embedding, text)

    # ── Collection & TTL helpers ──────────────────────────────────────────

    def _validate_collection(self, collection: str) -> bool:
        """Check if collection name is valid."""
        return collection in COLLECTIONS

    def _get_expires_at(self, collection: str) -> Optional[str]:
        ttl = self._collection_ttl.get(collection)
        return _expires_iso(ttl)

    # ── Core Store Methods ────────────────────────────────────────────────

    async def store(
        self,
        collection: str,
        id: str,
        embedding: List[float],
        metadata: Optional[Dict] = None,
        content: Optional[str] = None,
    ) -> bool:
        """
        Store embedding + metadata in specified collection.
        Returns True on success.
        """
        if not self._validate_collection(collection):
            logger.warning(f"⚠️  Unknown collection: {collection}")
            return False

        expires_at = self._get_expires_at(collection)

        if self._mode == "chromadb" and self._chroma_available:
            return await self._chroma_store(collection, id, embedding, metadata, content, expires_at)
        elif self._mode == "sqlite" and self._sqlite_store:
            return await self._sqlite_store.store(collection, id, embedding, metadata, content, expires_at)
        elif self._memory_store:
            return await self._memory_store.store(collection, id, embedding, metadata, content, expires_at)
        return False

    async def _chroma_store(
        self,
        collection: str,
        id: str,
        embedding: List[float],
        metadata: Optional[Dict],
        content: Optional[str],
        expires_at: Optional[str],
    ) -> bool:
        col = self._get_chroma_collection(collection)
        if col is None:
            return False
        loop = asyncio.get_event_loop()

        def _run():
            try:
                meta = dict(metadata or {})
                meta["_id"] = id
                if expires_at:
                    meta["_expires_at"] = expires_at
                col.add(
                    ids=[id],
                    embeddings=[embedding],
                    documents=[content or ""],
                    metadatas=[meta],
                )
                return True
            except Exception as e:
                logger.warning(f"⚠️  ChromaDB store failed: {e}")
                return False

        return await loop.run_in_executor(self._executor, _run)

    async def store_text(
        self,
        collection: str,
        id: str,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Generate embedding from text using SentenceTransformer and store.
        """
        embedding = await self._generate_embedding_async(text)
        return await self.store(collection, id, embedding, metadata, content=text)

    async def store_batch(self, collection: str, items: List[Dict]) -> int:
        """
        Batch store multiple items.
        Each item dict: {"id": str, "embedding": List[float], "metadata": Dict, "content": str}
        Returns number of successfully stored items.
        """
        success = 0
        for item in items:
            ok = await self.store(
                collection=collection,
                id=item["id"],
                embedding=item.get("embedding", []),
                metadata=item.get("metadata"),
                content=item.get("content"),
            )
            if ok:
                success += 1
        return success

    # ── Search Methods ────────────────────────────────────────────────────

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Vector similarity search in collection.
        Returns [{"id": str, "score": float, "metadata": Dict, "content": str}]
        """
        if not self._validate_collection(collection):
            return []

        if self._mode == "chromadb" and self._chroma_available:
            return await self._chroma_search(collection, query_vector, top_k, filter)
        elif self._mode == "sqlite" and self._sqlite_store:
            return await self._sqlite_store.search(collection, query_vector, top_k, filter)
        elif self._memory_store:
            return await self._memory_store.search(collection, query_vector, top_k, filter)
        return []

    async def _chroma_search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict] = None,
    ) -> List[Dict]:
        col = self._get_chroma_collection(collection)
        if col is None:
            return []
        loop = asyncio.get_event_loop()

        def _run():
            try:
                where_filter = None
                if filter:
                    where_filter = {k: v for k, v in filter.items()}

                results = col.query(
                    query_embeddings=[query_vector],
                    n_results=top_k,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"],
                )

                output = []
                if results["ids"] and results["ids"][0]:
                    for i, cid in enumerate(results["ids"][0]):
                        distance = results["distances"][0][i]
                        score = 1.0 - distance  # cosine distance → similarity
                        meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                        content = results["documents"][0][i] if results.get("documents") else ""

                        # Skip expired
                        expires_at = meta.pop("_expires_at", None) if meta else None
                        if _is_expired(expires_at):
                            continue

                        output.append({
                            "id": cid,
                            "score": score,
                            "metadata": meta or {},
                            "content": content or "",
                        })
                return output
            except Exception as e:
                logger.warning(f"⚠️  ChromaDB search failed: {e}")
                return []

        return await loop.run_in_executor(self._executor, _run)

    async def search_text(
        self,
        collection: str,
        query: str,
        top_k: int = 10,
        filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Generate query embedding and search.
        """
        query_vector = await self._generate_embedding_async(query)
        return await self.search(collection, query_vector, top_k, filter)

    async def hybrid_search(
        self,
        collection: str,
        query: str,
        top_k: int = 10,
        alpha: float = 0.7,
    ) -> List[Dict]:
        """
        Combined vector + keyword search using Reciprocal Rank Fusion (RRF).

        Args:
            collection: Collection name.
            query: The search query text.
            top_k: Number of results to return.
            alpha: Weight for vector similarity (0.0 = keyword only, 1.0 = vector only).

        Returns:
            List of dicts with id, score, metadata, content.
        """
        if alpha >= 1.0:
            # Pure vector search
            return await self.search_text(collection, query, top_k)

        # Vector search (get more for re-ranking)
        vector_results = await self.search_text(collection, query, top_k=top_k * 3)

        if alpha <= 0.0 or not vector_results:
            return vector_results[:top_k]

        # BM25-style keyword scoring
        query_terms = set(query.lower().split())
        keyword_scores: Dict[str, float] = {}
        for res in vector_results:
            content = (res.get("content") or "").lower()
            matches = sum(1 for t in query_terms if t in content)
            keyword_scores[res["id"]] = matches / max(len(query_terms), 1)

        # RRF merge
        rrf_constant = 60.0
        merged_scores: Dict[str, float] = {}

        # Rank-based scoring from vector results
        for rank, res in enumerate(vector_results):
            rid = res["id"]
            vector_rrf = 1.0 / (rrf_constant + rank + 1)
            keyword_rrf = keyword_scores.get(rid, 0.0)
            merged_scores[rid] = alpha * vector_rrf + (1 - alpha) * keyword_rrf

        # Build final results
        result_map = {r["id"]: r for r in vector_results}
        sorted_ids = sorted(merged_scores.keys(), key=lambda x: merged_scores[x], reverse=True)

        output = []
        for rid in sorted_ids[:top_k]:
            entry = dict(result_map[rid])
            entry["score"] = merged_scores[rid]
            output.append(entry)

        return output

    # ── CRUD Methods ──────────────────────────────────────────────────────

    async def delete(self, collection: str, id: str) -> bool:
        """Delete from collection."""
        if not self._validate_collection(collection):
            return False

        if self._mode == "chromadb" and self._chroma_available:
            return await self._chroma_delete(collection, id)
        elif self._mode == "sqlite" and self._sqlite_store:
            return await self._sqlite_store.delete(collection, id)
        elif self._memory_store:
            return await self._memory_store.delete(collection, id)
        return False

    async def _chroma_delete(self, collection: str, id: str) -> bool:
        col = self._get_chroma_collection(collection)
        if col is None:
            return False
        loop = asyncio.get_event_loop()

        def _run():
            try:
                col.delete(ids=[id])
                return True
            except Exception as e:
                logger.warning(f"⚠️  ChromaDB delete failed: {e}")
                return False

        return await loop.run_in_executor(self._executor, _run)

    async def get(self, collection: str, id: str) -> Optional[Dict]:
        """Get by ID. Returns {"id", "score", "metadata", "content"} or None."""
        if not self._validate_collection(collection):
            return None

        if self._mode == "chromadb" and self._chroma_available:
            return await self._chroma_get(collection, id)
        elif self._mode == "sqlite" and self._sqlite_store:
            return await self._sqlite_store.get(collection, id)
        elif self._memory_store:
            return await self._memory_store.get(collection, id)
        return None

    async def _chroma_get(self, collection: str, id: str) -> Optional[Dict]:
        col = self._get_chroma_collection(collection)
        if col is None:
            return None
        loop = asyncio.get_event_loop()

        def _run():
            try:
                result = col.get(ids=[id], include=["documents", "metadatas", "embeddings"])
                if not result or not result["ids"]:
                    return None
                meta = result["metadatas"][0] if result.get("metadatas") else {}
                content = result["documents"][0] if result.get("documents") else ""

                # Skip expired
                expires_at = meta.pop("_expires_at", None) if meta else None
                if _is_expired(expires_at):
                    try:
                        col.delete(ids=[id])
                    except Exception:
                        pass
                    return None

                return {
                    "id": id,
                    "score": 1.0,
                    "metadata": meta or {},
                    "content": content or "",
                }
            except Exception as e:
                logger.warning(f"⚠️  ChromaDB get failed: {e}")
                return None

        return await loop.run_in_executor(self._executor, _run)

    # ── Collection Management ─────────────────────────────────────────────

    async def list_collections(self) -> List[str]:
        """List all available collections."""
        if self._mode == "chromadb" and self._chroma_available:
            return list(self._chroma_collections.keys())
        elif self._mode == "sqlite" and self._sqlite_store:
            stored = await self._sqlite_store.all_collections()
            # Always include known collections
            return list(set(list(COLLECTIONS.keys()) + stored))
        elif self._memory_store:
            stored = await self._memory_store.all_collections()
            return list(set(list(COLLECTIONS.keys()) + stored))
        return list(COLLECTIONS.keys())

    async def get_stats(self, collection: Optional[str] = None) -> Dict[str, Any]:
        """Get collection stats: count, dimension, avg embedding norm."""
        stats = {
            "mode": self._mode,
            "connected": self._connected,
            "cache_size": len(self._embedding_cache),
        }

        target_collections = [collection] if collection else list(COLLECTIONS.keys())

        for col_name in target_collections:
            col_info = COLLECTIONS.get(col_name, {})
            col_stats = {
                "dim": col_info.get("dim", 384),
                "ttl_hours": col_info.get("ttl_hours"),
                "count": 0,
            }

            try:
                if self._mode == "chromadb" and self._chroma_available:
                    chroma_col = self._get_chroma_collection(col_name)
                    if chroma_col:
                        col_stats["count"] = chroma_col.count()
                elif self._mode == "sqlite" and self._sqlite_store:
                    col_stats["count"] = await self._sqlite_store.count(col_name)
                elif self._memory_store:
                    col_stats["count"] = await self._memory_store.count(col_name)
            except Exception as e:
                logger.warning(f"⚠️  Error getting count for {col_name}: {e}")

            stats[col_name] = col_stats

        return stats

    async def health(self) -> Dict[str, Any]:
        """Health check for the vector store."""
        start = time.monotonic()
        total_vectors = 0

        try:
            for col_name in COLLECTIONS:
                try:
                    if self._mode == "chromadb" and self._chroma_available:
                        chroma_col = self._get_chroma_collection(col_name)
                        if chroma_col:
                            total_vectors += chroma_col.count()
                    elif self._mode == "sqlite" and self._sqlite_store:
                        total_vectors += await self._sqlite_store.count(col_name)
                    elif self._memory_store:
                        total_vectors += await self._memory_store.count(col_name)
                except Exception:
                    pass
        except Exception:
            pass

        latency = (time.monotonic() - start) * 1000.0  # ms

        return {
            "connected": self._connected,
            "mode": self._mode,
            "collections": len(COLLECTIONS),
            "total_vectors": total_vectors,
            "latency_ms": round(latency, 2),
        }

    async def cleanup_expired(self) -> Dict[str, int]:
        """
        Remove expired entries from TTL-limited collections.
        Returns {collection_name: count_removed}.
        """
        result: Dict[str, int] = {}

        if self._mode == "chromadb" and self._chroma_available:
            for col_name, col_info in COLLECTIONS.items():
                if col_info.get("ttl_hours") is None:
                    result[col_name] = 0
                    continue
                col = self._get_chroma_collection(col_name)
                if col is None:
                    result[col_name] = 0
                    continue

                loop = asyncio.get_event_loop()

                def _run_cleanup(c=col, cn=col_name):
                    removed = 0
                    try:
                        # Get all IDs with expiration metadata
                        all_items = c.get(include=["metadatas"])
                        if not all_items or not all_items["ids"]:
                            return 0
                        expired_ids = []
                        for i, cid in enumerate(all_items["ids"]):
                            meta = all_items["metadatas"][i] if all_items.get("metadatas") else {}
                            expires_at = meta.get("_expires_at")
                            if _is_expired(expires_at):
                                expired_ids.append(cid)
                        if expired_ids:
                            c.delete(ids=expired_ids)
                            removed = len(expired_ids)
                    except Exception as e:
                        logger.warning(f"⚠️  ChromaDB cleanup for {cn} failed: {e}")
                    return removed

                count = await loop.run_in_executor(self._executor, _run_cleanup)
                result[col_name] = count

        elif self._mode == "sqlite" and self._sqlite_store:
            total = await self._sqlite_store.cleanup_expired()
            # Approximate per-collection breakdown
            for col_name in COLLECTIONS:
                if self._collection_ttl.get(col_name) is not None:
                    result[col_name] = total // sum(
                        1 for c in COLLECTIONS if self._collection_ttl.get(c) is not None
                    )
                else:
                    result[col_name] = 0

        elif self._memory_store:
            total = await self._memory_store.cleanup_expired()
            for col_name in COLLECTIONS:
                if self._collection_ttl.get(col_name) is not None:
                    result[col_name] = total // sum(
                        1 for c in COLLECTIONS if self._collection_ttl.get(c) is not None
                    )
                else:
                    result[col_name] = 0

        else:
            for col_name in COLLECTIONS:
                result[col_name] = 0

        logger.info(f"🧹 cleanup_expired: {result}")
        return result
