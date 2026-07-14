#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade vector memory system with env var config
ASIMNEXUS Vector Memory
========================
Local-first semantic memory with embeddings and retrieval.
Supports chat history, user memories, and knowledge base.

Backends:
- CHROMADB (default): ChromaDB persistent client with HNSW ANN indexing
- SENTENCE_TRANSFORMERS: all-MiniLM-L6-v2, 384d, with cache (fallback)
- OPENAI: text-embedding-ada-002, 1536d
- DUMMY: hash-based fallback when sentence-transformers not installed
"""

import os
import logging
import sqlite3
import json
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from collections import OrderedDict

logger = logging.getLogger("AsimNexus.VectorMemory")

# ─── Environment Configuration ────────────────────────────────────────────────
_DEFAULT_DB_PATH = os.getenv("ASIM_VECTOR_DB_PATH", "data/vector_memory.db")
_DEFAULT_EMBEDDING_BACKEND = os.getenv("ASIM_EMBEDDING_BACKEND", "chromadb")
_DEFAULT_PRUNE_DAYS = int(os.getenv("ASIM_VECTOR_PRUNE_DAYS", "90"))
_DEFAULT_KEEP_PER_TYPE = int(os.getenv("ASIM_VECTOR_KEEP_PER_TYPE", "100"))
_DEFAULT_CHROMA_PATH = os.getenv("ASIM_CHROMA_PATH", "data/chromadb")
_DEFAULT_CHROMA_COLLECTION = os.getenv("ASIM_CHROMA_COLLECTION", "asimnexus_memories")
_EMBEDDING_CACHE_SIZE = int(os.getenv("ASIM_EMBEDDING_CACHE_SIZE", "10000"))


class MemoryType(Enum):
    """Types of memories stored in vector memory."""
    CHAT = "chat"           # Conversation messages
    USER_MEMORY = "user"     # User-specific memories
    KNOWLEDGE = "knowledge"  # General knowledge/facts
    LESSON = "lesson"       # Learned lessons from dreaming
    SYSTEM = "system"       # System events and states
    CLONE = "clone"         # Clone-specific memory silo


class EmbeddingBackend(Enum):
    """Embedding generation backends."""
    CHROMADB = "chromadb"                             # ChromaDB with HNSW (default)
    SENTENCE_TRANSFORMERS = "sentence_transformers"  # Local fallback
    OPENAI = "openai"                                 # Cloud fallback
    DUMMY = "dummy"                                  # Testing / fallback


class _EmbeddingCache:
    """LRU cache for embeddings to avoid recomputing for same text."""

    def __init__(self, maxsize: int = _EMBEDDING_CACHE_SIZE):
        self._maxsize = maxsize
        self._cache: OrderedDict = OrderedDict()

    def get(self, text: str) -> Optional[List[float]]:
        if text in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(text)
            return self._cache[text]
        return None

    def put(self, text: str, embedding: List[float]):
        if text in self._cache:
            self._cache.move_to_end(text)
        self._cache[text] = embedding
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def clear(self):
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "usage_pct": round(len(self._cache) / self._maxsize * 100, 1) if self._maxsize else 0
        }


@dataclass
class Memory:
    """Memory entry with embedding."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    memory_type: MemoryType = MemoryType.CHAT
    user_id: str = "anonymous"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0
    last_accessed: Optional[str] = None


@dataclass
class SearchResult:
    """Search result with similarity score."""
    memory: Memory
    similarity: float
    distance: float


class VectorMemory:
    """
    Local-first vector memory system.
    Stores embeddings in ChromaDB (primary) + SQLite metadata (fallback).

    ChromaDB is the default backend with HNSW approximate nearest neighbor indexing.
    Falls back to SQLite full-scan cosine similarity when ChromaDB is unavailable.

    Backward-compatible interface. Callers don't need to change.
    """

    def __init__(self, db_path: str, embedding_backend: EmbeddingBackend = EmbeddingBackend.CHROMADB):
        self.db_path = db_path
        self.embedding_backend = embedding_backend
        self._embedding_dim = self._get_embedding_dimension()
        self._embedding_cache = _EmbeddingCache()
        self._sentence_model = None  # Lazy-loaded SentenceTransformer model
        self._async_embedding_queue: asyncio.Queue = None
        self._async_embedding_task: asyncio.Task = None

        # ChromaDB integration
        self._chroma_client = None
        self._chroma_collection = None
        self._chroma_available = False

        self._init_db()
        # Always attempt ChromaDB init; gracefully falls back if chromadb not installed
        self._init_chromadb()

        logger.info(
            f"🧠 VectorMemory initialized - Backend: {embedding_backend}, "
            f"Dim: {self._embedding_dim}, Cache: {_EMBEDDING_CACHE_SIZE}, "
            f"ChromaDB: {'✅' if self._chroma_available else '❌'}"
        )

    def _get_embedding_dimension(self) -> int:
        """Get embedding dimension based on backend."""
        if self.embedding_backend in (EmbeddingBackend.CHROMADB, EmbeddingBackend.SENTENCE_TRANSFORMERS):
            return 384  # all-MiniLM-L6-v2
        elif self.embedding_backend == EmbeddingBackend.OPENAI:
            return 1536  # text-embedding-ada-002
        else:
            return 128  # Dummy dimension

    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    memory_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            """)

            # Migrate: check if user_id column exists in existing database
            cursor = conn.execute("PRAGMA table_info(memories)")
            columns = [row[1] for row in cursor.fetchall()]
            if columns and "user_id" not in columns:
                logger.info("Migrating vector_memory database: adding user_id column")
                conn.execute("ALTER TABLE memories ADD COLUMN user_id TEXT NOT NULL DEFAULT 'anonymous'")

            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)")

            # Create metadata-only table for ChromaDB mode (stores ChromaDB IDs)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chroma_metadata (
                    memory_id TEXT PRIMARY KEY,
                    chroma_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    FOREIGN KEY (memory_id) REFERENCES memories(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chroma_id ON chroma_metadata(chroma_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chroma_type ON chroma_metadata(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chroma_user ON chroma_metadata(user_id)")

            conn.commit()

    # ── ChromaDB Integration ──────────────────────────────────────────────

    def _init_chromadb(self):
        """Initialize ChromaDB persistent client with HNSW indexing."""
        try:
            import chromadb
            from chromadb.config import Settings

            chroma_path = os.getenv("ASIM_CHROMA_PATH", _DEFAULT_CHROMA_PATH)
            Path(chroma_path).mkdir(parents=True, exist_ok=True)

            self._chroma_client = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )

            collection_name = os.getenv("ASIM_CHROMA_COLLECTION", _DEFAULT_CHROMA_COLLECTION)

            # Check if collection already exists with mismatched dimension
            existing_collections = self._chroma_client.list_collections()
            existing_names = {c.name for c in existing_collections}

            if collection_name in existing_names:
                existing = self._chroma_client.get_collection(name=collection_name)
                # Peek at first record to check dimension
                try:
                    peek = existing.peek()
                    if peek and peek.get("embeddings") and len(peek["embeddings"]) > 0:
                        existing_dim = len(peek["embeddings"][0])
                        if existing_dim != self._embedding_dim:
                            logger.warning(
                                f"⚠️  ChromaDB collection '{collection_name}' has dimension {existing_dim}, "
                                f"expected {self._embedding_dim}. Deleting and recreating."
                            )
                            self._chroma_client.delete_collection(name=collection_name)
                            existing = None
                except Exception:
                    # Collection might be empty, that's fine
                    pass

            # Get or create collection with HNSW configuration
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 100,
                    "hnsw:M": 16,
                    "hnsw:search_ef": 50,
                }
            )

            self._chroma_available = True
            logger.info(f"✅ ChromaDB initialized - path: {chroma_path}, collection: {collection_name}")

        except ImportError:
            logger.warning("⚠️  chromadb not installed, falling back to SQLite-only mode")
            self._chroma_available = False
        except Exception as e:
            logger.warning(f"⚠️  ChromaDB init failed: {e}, falling back to SQLite-only mode")
            self._chroma_available = False

    # ── SentenceTransformer Model (lazy-loaded) ───────────────────────────

    def _get_sentence_model(self):
        """Lazy-load SentenceTransformer model."""
        if self._sentence_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ SentenceTransformer model loaded (all-MiniLM-L6-v2)")
            except ImportError:
                logger.warning("⚠️  sentence-transformers not installed")
                return None
        return self._sentence_model

    # ── Embedding Generation ──────────────────────────────────────────────

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text with caching."""
        # Check cache first
        cached = self._embedding_cache.get(text)
        if cached is not None:
            return cached

        embedding = self._compute_embedding(text)

        # Cache the result
        self._embedding_cache.put(text, embedding)
        return embedding

    def _compute_embedding(self, text: str) -> List[float]:
        """Compute embedding without caching."""
        if self.embedding_backend == EmbeddingBackend.DUMMY:
            result = self._dummy_embedding(text)
            return result

        elif self.embedding_backend in (EmbeddingBackend.SENTENCE_TRANSFORMERS, EmbeddingBackend.CHROMADB):
            model = self._get_sentence_model()
            if model is not None:
                try:
                    return model.encode(text).tolist()
                except Exception as e:
                    logger.warning(f"⚠️  SentenceTransformer encoding failed: {e}, using dummy")
            # Fallback to dummy
            return self._dummy_embedding(text)

        elif self.embedding_backend == EmbeddingBackend.OPENAI:
            try:
                import openai
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return response['data'][0]['embedding']
            except Exception as e:
                logger.warning(f"⚠️  OpenAI embedding failed: {e}, using dummy")
                return self._dummy_embedding(text)

        return [0.0] * self._embedding_dim

    def _dummy_embedding(self, text: str) -> List[float]:
        """Simple hash-based dummy embedding for testing/fallback."""
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        embedding = [float(b) / 255.0 for b in hash_bytes[:self._embedding_dim]]
        if len(embedding) < self._embedding_dim:
            embedding.extend([0.0] * (self._embedding_dim - len(embedding)))
        else:
            embedding = embedding[:self._embedding_dim]
        return embedding

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        Uses SentenceTransformer's built-in batch encoding for efficiency.
        """
        # Check which texts need computing (not in cache)
        uncached_texts = []
        uncached_indices = []
        embeddings = [None] * len(texts)

        for i, text in enumerate(texts):
            cached = self._embedding_cache.get(text)
            if cached is not None:
                embeddings[i] = cached
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        if not uncached_texts:
            return embeddings

        # Compute uncached embeddings in batch
        if self.embedding_backend in (EmbeddingBackend.SENTENCE_TRANSFORMERS, EmbeddingBackend.CHROMADB):
            model = self._get_sentence_model()
            if model is not None:
                try:
                    batch_embeddings = model.encode(uncached_texts).tolist()
                    for idx, emb in zip(uncached_indices, batch_embeddings):
                        embeddings[idx] = emb
                        self._embedding_cache.put(texts[idx], emb)
                    return embeddings
                except Exception:
                    pass

        # Fallback: compute individually
        for idx in uncached_indices:
            emb = self._compute_embedding(texts[idx])
            embeddings[idx] = emb
            self._embedding_cache.put(texts[idx], emb)

        return embeddings

    async def generate_embeddings_async(self, texts: List[str]) -> List[List[float]]:
        """
        Async embedding generation using run_in_executor for thread safety.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_embeddings_batch, texts)

    # ── Serialization ─────────────────────────────────────────────────────

    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """Serialize embedding to bytes for storage."""
        import struct
        return struct.pack(f'{len(embedding)}f', *embedding)

    def _deserialize_embedding(self, data: bytes) -> List[float]:
        """Deserialize embedding from bytes."""
        import struct
        return list(struct.unpack(f'{len(data)//4}f', data))

    # ── CRUD Operations ───────────────────────────────────────────────────

    def add_memory(self, content: str, memory_type: MemoryType = MemoryType.CHAT,
                   user_id: str = "anonymous", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a memory to the vector store.
        Returns the memory ID.
        """
        import secrets
        memory_id = secrets.token_hex(12)

        # Generate embedding
        embedding = self._generate_embedding(content)

        if self._chroma_available:
            return self._chroma_add_memory(memory_id, content, embedding, memory_type, user_id, metadata)
        else:
            return self._sqlite_add_memory(memory_id, content, embedding, memory_type, user_id, metadata)

    def _sqlite_add_memory(self, memory_id: str, content: str, embedding: List[float],
                           memory_type: MemoryType, user_id: str,
                           metadata: Optional[Dict[str, Any]]) -> str:
        """Add memory to SQLite (used by all backends)."""
        embedding_blob = self._serialize_embedding(embedding)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memories (id, content, embedding, memory_type, user_id, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                content,
                embedding_blob,
                memory_type.value,
                user_id,
                json.dumps(metadata or {}),
                datetime.utcnow().isoformat()
            ))
            conn.commit()

        logger.debug(f"✅ Added memory {memory_id} (type: {memory_type.value})")
        return memory_id

    def _chroma_add_memory(self, memory_id: str, content: str, embedding: List[float],
                           memory_type: MemoryType, user_id: str,
                           metadata: Optional[Dict[str, Any]]) -> str:
        """Add memory to ChromaDB + metadata-only SQLite."""
        chroma_id = f"mem_{memory_id}"
        full_metadata = {
            "memory_id": memory_id,
            "memory_type": memory_type.value,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {})
        }

        try:
            # Store in ChromaDB
            self._chroma_collection.add(
                ids=[chroma_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[full_metadata]
            )

            # Store metadata in SQLite (no embedding blob)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO chroma_metadata (memory_id, chroma_id, content, memory_type, user_id, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory_id,
                    chroma_id,
                    content,
                    memory_type.value,
                    user_id,
                    json.dumps(metadata or {}),
                    datetime.utcnow().isoformat()
                ))
                conn.commit()

            logger.debug(f"✅ Added memory to ChromaDB: {memory_id} (type: {memory_type.value})")
            return memory_id

        except Exception as e:
            logger.error(f"❌ ChromaDB add failed: {e}, falling back to SQLite")
            return self._sqlite_add_memory(memory_id, content, embedding, memory_type, user_id, metadata)

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID."""
        if self._chroma_available:
            return self._chroma_get_memory(memory_id)
        else:
            return self._sqlite_get_memory(memory_id)

    def _sqlite_get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?",
                (memory_id,)
            ).fetchone()

            if not row:
                return None

            # Update access count
            conn.execute(
                "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), memory_id)
            )
            conn.commit()

            embedding = self._deserialize_embedding(row['embedding']) if row['embedding'] else None

            return Memory(
                id=row['id'],
                content=row['content'],
                embedding=embedding,
                memory_type=MemoryType(row['memory_type']),
                user_id=row['user_id'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                access_count=row['access_count'],
                last_accessed=row['last_accessed']
            )

    def _chroma_get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory from ChromaDB metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM chroma_metadata WHERE memory_id = ?",
                (memory_id,)
            ).fetchone()

            if not row:
                return None

            # Update access count
            conn.execute(
                "UPDATE chroma_metadata SET access_count = access_count + 1, last_accessed = ? WHERE memory_id = ?",
                (datetime.utcnow().isoformat(), memory_id)
            )
            conn.commit()

            chroma_id = row['chroma_id']

            # Try to get embedding from ChromaDB
            embedding = None
            try:
                result = self._chroma_collection.get(
                    ids=[chroma_id],
                    include=["embeddings"]
                )
                if result and result['embeddings']:
                    embedding = result['embeddings'][0]
            except Exception:
                pass

            return Memory(
                id=row['memory_id'],
                content=row['content'],
                embedding=embedding,
                memory_type=MemoryType(row['memory_type']),
                user_id=row['user_id'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                access_count=row['access_count'],
                last_accessed=row['last_accessed']
            )

    def search(self, query: str, user_id: Optional[str] = None,
               memory_type: Optional[MemoryType] = None,
               limit: int = 10, min_similarity: float = 0.5) -> List[SearchResult]:
        """
        Semantic search for memories.
        Returns list of SearchResult with similarity scores.

        When ChromaDB is available, uses HNSW approximate nearest neighbor
        for fast search. Otherwise, uses full scan with cosine similarity.
        """
        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        if self._chroma_available:
            return self._chroma_search(query_embedding, query, user_id, memory_type, limit, min_similarity)
        else:
            return self._sqlite_search(query_embedding, user_id, memory_type, limit, min_similarity)

    def _sqlite_search(self, query_embedding: List[float],
                       user_id: Optional[str] = None,
                       memory_type: Optional[MemoryType] = None,
                       limit: int = 10, min_similarity: float = 0.5) -> List[SearchResult]:
        """Full-scan cosine similarity search over SQLite records."""
        sql = "SELECT * FROM memories WHERE 1=1"
        params = []

        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type.value)

        sql += " ORDER BY created_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()

        results = []
        for row in rows:
            embedding = self._deserialize_embedding(row['embedding']) if row['embedding'] else None
            if not embedding:
                continue

            similarity = self._cosine_similarity(query_embedding, embedding)

            if similarity >= min_similarity:
                memory = Memory(
                    id=row['id'],
                    content=row['content'],
                    embedding=embedding,
                    memory_type=MemoryType(row['memory_type']),
                    user_id=row['user_id'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=row['created_at'],
                    access_count=row['access_count'],
                    last_accessed=row['last_accessed']
                )

                # Update access count
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                        (datetime.utcnow().isoformat(), row['id'])
                    )
                    conn.commit()

                results.append(SearchResult(
                    memory=memory,
                    similarity=similarity,
                    distance=1.0 - similarity
                ))

        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:limit]

    def _chroma_search(self, query_embedding: List[float], query: str,
                       user_id: Optional[str] = None,
                       memory_type: Optional[MemoryType] = None,
                       limit: int = 10, min_similarity: float = 0.5) -> List[SearchResult]:
        """Approximate nearest neighbor search via ChromaDB HNSW index."""
        try:
            # Build where filter
            where_filter = {}
            if user_id:
                where_filter["user_id"] = user_id
            if memory_type:
                where_filter["memory_type"] = memory_type.value

            n_results = min(limit * 3, 100)  # Get more for post-filtering

            results = self._chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances", "embeddings"]
            )

            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, chroma_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1.0 - distance  # ChromaDB returns cosine distance

                    if similarity < min_similarity:
                        continue

                    metadata = results["metadatas"][0][i]
                    memory_id = metadata.get("memory_id", chroma_id.replace("mem_", ""))
                    content = results["documents"][0][i]
                    emb = results["embeddings"][0][i] if results.get("embeddings") else None

                    memory = Memory(
                        id=memory_id,
                        content=content,
                        embedding=emb,
                        memory_type=MemoryType(metadata.get("memory_type", "chat")),
                        user_id=metadata.get("user_id", "anonymous"),
                        metadata={k: v for k, v in metadata.items()
                                   if k not in ("memory_id", "memory_type", "user_id", "created_at")},
                        created_at=metadata.get("created_at", datetime.utcnow().isoformat())
                    )

                    # Update access count in metadata table
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(
                            "UPDATE chroma_metadata SET access_count = access_count + 1, last_accessed = ? WHERE memory_id = ?",
                            (datetime.utcnow().isoformat(), memory_id)
                        )
                        conn.commit()

                    search_results.append(SearchResult(
                        memory=memory,
                        similarity=similarity,
                        distance=distance
                    ))

            search_results.sort(key=lambda x: x.similarity, reverse=True)
            return search_results[:limit]

        except Exception as e:
            logger.error(f"❌ ChromaDB search failed: {e}, falling back to SQLite search")
            return self._sqlite_search(query_embedding, user_id, memory_type, limit, min_similarity)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(y * y for y in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def get_user_memories(self, user_id: str, memory_type: Optional[MemoryType] = None,
                          limit: int = 50) -> List[Memory]:
        """Get all memories for a user."""
        if self._chroma_available:
            return self._chroma_get_user_memories(user_id, memory_type, limit)
        else:
            return self._sqlite_get_user_memories(user_id, memory_type, limit)

    def _sqlite_get_user_memories(self, user_id: str, memory_type: Optional[MemoryType] = None,
                                  limit: int = 50) -> List[Memory]:
        """Get user memories from SQLite."""
        sql = "SELECT * FROM memories WHERE user_id = ?"
        params = [user_id]

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type.value)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()

        memories = []
        for row in rows:
            embedding = self._deserialize_embedding(row['embedding']) if row['embedding'] else None
            memories.append(Memory(
                id=row['id'],
                content=row['content'],
                embedding=embedding,
                memory_type=MemoryType(row['memory_type']),
                user_id=row['user_id'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                access_count=row['access_count'],
                last_accessed=row['last_accessed']
            ))

        return memories

    def _chroma_get_user_memories(self, user_id: str, memory_type: Optional[MemoryType] = None,
                                  limit: int = 50) -> List[Memory]:
        """Get user memories from ChromaDB metadata SQLite table."""
        sql = "SELECT * FROM chroma_metadata WHERE user_id = ?"
        params = [user_id]

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type.value)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()

        memories = []
        for row in rows:
            memories.append(Memory(
                id=row['memory_id'],
                content=row['content'],
                embedding=None,
                memory_type=MemoryType(row['memory_type']),
                user_id=row['user_id'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                access_count=row['access_count'],
                last_accessed=row['last_accessed']
            ))

        return memories

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        if self._chroma_available:
            return self._chroma_delete_memory(memory_id)
        else:
            return self._sqlite_delete_memory(memory_id)

    def _sqlite_delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _chroma_delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from ChromaDB + metadata SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT chroma_id FROM chroma_metadata WHERE memory_id = ?",
                    (memory_id,)
                ).fetchone()

                if not row:
                    return False

                chroma_id = row[0]

                # Delete from ChromaDB
                self._chroma_collection.delete(ids=[chroma_id])

                # Delete from metadata table
                conn.execute("DELETE FROM chroma_metadata WHERE memory_id = ?", (memory_id,))
                conn.commit()

            logger.debug(f"🗑️ Deleted memory from ChromaDB: {memory_id}")
            return True

        except Exception as e:
            logger.error(f"❌ ChromaDB delete failed: {e}, trying SQLite fallback")
            return self._sqlite_delete_memory(memory_id)

    def update_memory(self, memory_id: str, content: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a memory's content and/or metadata.
        Regenerates embedding if content changes.
        """
        try:
            if self._chroma_available:
                return self._chroma_update_memory(memory_id, content, metadata)
            else:
                return self._sqlite_update_memory(memory_id, content, metadata)
        except Exception as e:
            logger.error(f"❌ Update failed for memory {memory_id}: {e}")
            return False

    def _sqlite_update_memory(self, memory_id: str, content: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update a memory in SQLite."""
        existing = self._sqlite_get_memory(memory_id)
        if not existing:
            return False

        with sqlite3.connect(self.db_path) as conn:
            if content is not None and content != existing.content:
                embedding = self._generate_embedding(content)
                embedding_blob = self._serialize_embedding(embedding)
                conn.execute(
                    "UPDATE memories SET content = ?, embedding = ? WHERE id = ?",
                    (content, embedding_blob, memory_id)
                )

            if metadata is not None:
                merged = {**existing.metadata, **metadata}
                conn.execute(
                    "UPDATE memories SET metadata = ? WHERE id = ?",
                    (json.dumps(merged), memory_id)
                )

            conn.commit()
        return True

    def _chroma_update_memory(self, memory_id: str, content: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update a memory in ChromaDB + metadata SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM chroma_metadata WHERE memory_id = ?",
                (memory_id,)
            ).fetchone()

            if not row:
                return False

            chroma_id = row['chroma_id']
            current_content = row['content']
            current_metadata = json.loads(row['metadata']) if row['metadata'] else {}

        try:
            new_content = content if content is not None else current_content
            new_metadata = {**current_metadata, **(metadata or {})}

            if content is not None and content != current_content:
                embedding = self._generate_embedding(new_content)
                self._chroma_collection.update(
                    ids=[chroma_id],
                    embeddings=[embedding],
                    documents=[new_content],
                    metadatas=[{
                        "memory_id": memory_id,
                        "memory_type": row['memory_type'],
                        "user_id": row['user_id'],
                        "created_at": row['created_at'],
                        **new_metadata
                    }]
                )
            else:
                self._chroma_collection.update(
                    ids=[chroma_id],
                    metadatas=[{
                        "memory_id": memory_id,
                        "memory_type": row['memory_type'],
                        "user_id": row['user_id'],
                        "created_at": row['created_at'],
                        **new_metadata
                    }]
                )

            # Update SQLite metadata
            with sqlite3.connect(self.db_path) as conn:
                if content is not None:
                    conn.execute(
                        "UPDATE chroma_metadata SET content = ?, metadata = ? WHERE memory_id = ?",
                        (new_content, json.dumps(new_metadata), memory_id)
                    )
                else:
                    conn.execute(
                        "UPDATE chroma_metadata SET metadata = ? WHERE memory_id = ?",
                        (json.dumps(new_metadata), memory_id)
                    )
                conn.commit()

            return True

        except Exception as e:
            logger.error(f"❌ ChromaDB update failed: {e}")
            return False

    # ── Stats & Pruning ───────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        stats = {
            "embedding_backend": self.embedding_backend.value,
            "embedding_dimension": self._embedding_dim,
            "cache": self._embedding_cache.stats,
            "chromadb_available": self._chroma_available
        }

        if self._chroma_available:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute("SELECT COUNT(*) FROM chroma_metadata").fetchone()[0]

                by_type = {}
                for mt in MemoryType:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM chroma_metadata WHERE memory_type = ?",
                        (mt.value,)
                    ).fetchone()[0]
                    by_type[mt.value] = count

                by_user = {}
                rows = conn.execute("""
                    SELECT user_id, COUNT(*) as count
                    FROM chroma_metadata
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 10
                """).fetchall()
                for user_id, count in rows:
                    by_user[user_id] = count

                try:
                    chroma_count = self._chroma_collection.count()
                except Exception:
                    chroma_count = total

                stats.update({
                    "total_memories": total,
                    "chroma_collection_count": chroma_count,
                    "by_type": by_type,
                    "by_user": by_user,
                    "storage_size_bytes": self._get_storage_size()
                })
        else:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

                by_type = {}
                for mt in MemoryType:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM memories WHERE memory_type = ?",
                        (mt.value,)
                    ).fetchone()[0]
                    by_type[mt.value] = count

                by_user = {}
                rows = conn.execute("""
                    SELECT user_id, COUNT(*) as count
                    FROM memories
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 10
                """).fetchall()
                for user_id, count in rows:
                    by_user[user_id] = count

                stats.update({
                    "total_memories": total,
                    "by_type": by_type,
                    "by_user": by_user,
                    "storage_size_bytes": self._get_storage_size()
                })

        return stats

    def _get_storage_size(self) -> int:
        """Get total storage size in bytes."""
        size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
        if self._chroma_available:
            chroma_path = Path(os.getenv("ASIM_CHROMA_PATH", _DEFAULT_CHROMA_PATH))
            if chroma_path.exists():
                for f in chroma_path.rglob("*"):
                    if f.is_file():
                        size += f.stat().st_size
        return size

    def prune_old_memories(self, days: Optional[int] = None, keep_per_type: Optional[int] = None) -> int:
        """
        Prune old memories to save space.
        Keeps the most recent N memories per type.
        Returns number of memories deleted.
        """
        if days is None:
            days = _DEFAULT_PRUNE_DAYS
        if keep_per_type is None:
            keep_per_type = _DEFAULT_KEEP_PER_TYPE

        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        if self._chroma_available:
            return self._chroma_prune(cutoff, keep_per_type)
        else:
            return self._sqlite_prune(cutoff, keep_per_type)

    def _sqlite_prune(self, cutoff: str, keep_per_type: int) -> int:
        """Prune old memories from SQLite."""
        deleted = 0
        for mt in MemoryType:
            with sqlite3.connect(self.db_path) as conn:
                keep_ids = conn.execute("""
                    SELECT id FROM memories
                    WHERE memory_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (mt.value, keep_per_type)).fetchall()
                keep_ids = [row[0] for row in keep_ids]

                if keep_ids:
                    placeholders = ','.join('?' * len(keep_ids))
                    cursor = conn.execute(f"""
                        DELETE FROM memories
                        WHERE memory_type = ?
                        AND created_at < ?
                        AND id NOT IN ({placeholders})
                    """, [mt.value, cutoff] + keep_ids)
                    deleted += cursor.rowcount
                else:
                    cursor = conn.execute("""
                        DELETE FROM memories
                        WHERE memory_type = ? AND created_at < ?
                    """, (mt.value, cutoff))
                    deleted += cursor.rowcount

                conn.commit()

        logger.info(f"🗑️  Pruned {deleted} old memories from SQLite")
        return deleted

    def _chroma_prune(self, cutoff: str, keep_per_type: int) -> int:
        """Prune old memories from ChromaDB + metadata table."""
        deleted = 0
        for mt in MemoryType:
            with sqlite3.connect(self.db_path) as conn:
                # Get IDs to keep
                keep_rows = conn.execute("""
                    SELECT memory_id, chroma_id FROM chroma_metadata
                    WHERE memory_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (mt.value, keep_per_type)).fetchall()
                keep_ids = {row[0] for row in keep_rows}
                keep_chroma_ids = {row[1] for row in keep_rows}

                # Get all old memories of this type
                old_rows = conn.execute("""
                    SELECT memory_id, chroma_id FROM chroma_metadata
                    WHERE memory_type = ? AND created_at < ?
                """, (mt.value, cutoff)).fetchall()

                to_delete = []
                to_delete_chroma = []
                for row in old_rows:
                    if row[0] not in keep_ids:
                        to_delete.append(row[0])
                        to_delete_chroma.append(row[1])

                if to_delete:
                    # Delete from ChromaDB
                    try:
                        self._chroma_collection.delete(ids=to_delete_chroma)
                    except Exception as e:
                        logger.warning(f"⚠️  ChromaDB batch delete failed: {e}")

                    # Delete from metadata table
                    placeholders = ','.join('?' * len(to_delete))
                    cursor = conn.execute(f"""
                        DELETE FROM chroma_metadata
                        WHERE memory_id IN ({placeholders})
                    """, to_delete)
                    deleted += cursor.rowcount
                    conn.commit()

        logger.info(f"🗑️  Pruned {deleted} old memories from ChromaDB")
        return deleted

    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("🧹 Embedding cache cleared")

    # ── Migration ──────────────────────────────────────────────────────────

    def migrate_from_sqlite(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Migrate existing SQLite embeddings to ChromaDB.
        Copies all memories from the SQLite 'memories' table into ChromaDB
        and the 'chroma_metadata' table. Does NOT delete the original data.

        Returns a summary dict with counts of migrated/skipped/failed records.
        """
        if not self._chroma_available:
            logger.warning("⚠️  ChromaDB not available, cannot migrate")
            return {"migrated": 0, "skipped": 0, "failed": 0, "error": "ChromaDB not available"}

        migrated = 0
        skipped = 0
        failed = 0

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

            if total == 0:
                logger.info("📭 No SQLite memories to migrate")
                return {"migrated": 0, "skipped": 0, "failed": 0, "total": 0}

            # Check which memory_ids already exist in chroma_metadata
            existing = set(
                row[0] for row in conn.execute("SELECT memory_id FROM chroma_metadata").fetchall()
            )

            offset = 0
            while offset < total:
                rows = conn.execute(
                    "SELECT * FROM memories ORDER BY created_at ASC LIMIT ? OFFSET ?",
                    (batch_size, offset)
                ).fetchall()

                for row in rows:
                    memory_id = row["id"]
                    if memory_id in existing:
                        skipped += 1
                        continue

                    try:
                        embedding_blob = row["embedding"]
                        if not embedding_blob:
                            skipped += 1
                            continue

                        embedding = self._deserialize_embedding(embedding_blob)
                        content = row["content"]
                        memory_type = row["memory_type"]
                        user_id = row["user_id"]
                        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                        created_at = row["created_at"]

                        # Add to ChromaDB
                        chroma_id = f"mem_{memory_id}"
                        full_metadata = {
                            "memory_id": memory_id,
                            "memory_type": memory_type,
                            "user_id": user_id,
                            "created_at": created_at,
                            **metadata
                        }

                        self._chroma_collection.add(
                            ids=[chroma_id],
                            embeddings=[embedding],
                            documents=[content],
                            metadatas=[full_metadata]
                        )

                        # Add to chroma_metadata table
                        conn.execute("""
                            INSERT INTO chroma_metadata
                                (memory_id, chroma_id, content, memory_type, user_id, metadata, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            memory_id, chroma_id, content, memory_type, user_id,
                            json.dumps(metadata), created_at
                        ))

                        migrated += 1

                    except Exception as e:
                        logger.warning(f"⚠️  Migration failed for memory {memory_id}: {e}")
                        failed += 1

                conn.commit()
                offset += batch_size
                logger.info(f"🔄 Migration progress: {offset}/{total}")

        logger.info(
            f"✅ Migration complete - migrated: {migrated}, "
            f"skipped: {skipped}, failed: {failed}"
        )
        return {
            "migrated": migrated,
            "skipped": skipped,
            "failed": failed,
            "total": total
        }


# Global vector memory instance
_vector_memory: Optional[VectorMemory] = None


def get_vector_memory(db_path: Optional[str] = None,
                     embedding_backend: Optional[EmbeddingBackend] = None) -> VectorMemory:
    """Get or create global vector memory instance."""
    global _vector_memory
    if db_path is None:
        db_path = _DEFAULT_DB_PATH
    if embedding_backend is None:
        embedding_backend = EmbeddingBackend(_DEFAULT_EMBEDDING_BACKEND)
    if _vector_memory is None:
        _vector_memory = VectorMemory(db_path, embedding_backend)
    return _vector_memory


def reset_vector_memory():
    """Reset global vector memory instance (for testing)."""
    global _vector_memory
    _vector_memory = None
