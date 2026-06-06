#!/usr/bin/env python3
"""
AsimNexus Storage — Vector Data Migrator.

Migrates existing vector/embedding data into VectorStore collections.
Reads from vectormemory.py's SQLite metadata + ChromaDB collections,
and from JSONL files for re-indexing.

Phase 4 of the 4-layer storage architecture.
"""

import os
import re
import json
import glob
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("AsimNexus.VectorMigrator")

# ─── Forward Reference (avoid circular imports at module level) ───────────────
# VectorStore is imported lazily inside methods to avoid circular deps.

# Default paths used by vectormemory.py
_DEFAULT_VECTOR_DB = os.getenv("ASIM_VECTOR_DB_PATH", "data/vector_memory.db")
_DEFAULT_CHROMA_PATH = os.getenv("ASIM_CHROMA_PATH", "data/chromadb")
_DEFAULT_CHROMA_COLLECTION = os.getenv("ASIM_CHROMA_COLLECTION", "asimnexus_memories")


class VectorDataMigrator:
    """
    Migrates existing vector/embedding data into VectorStore.

    Reads from vectormemory.py's SQLite metadata + ChromaDB collections,
    and from JSONL files, re-indexing into the consolidated 4-collection VectorStore.
    """

    def __init__(self, store):
        """
        Args:
            store: An initialized VectorStore instance.
        """
        self._store = store

    # ── Content-based Collection Router ───────────────────────────────────

    @staticmethod
    def _infer_collection(content: str, metadata: Optional[Dict] = None) -> str:
        """
        Infer the target VectorStore collection from content and metadata.

        Heuristics:
        - If metadata has 'memory_type' == 'clone' → clone_silos
        - If metadata has 'source' == 'rag_pipeline' or 'doc_id' → retrieval
        - If content looks like a conversation/session → agent_context
        - Otherwise → semantic_memory
        """
        meta = metadata or {}

        # Direct mapping from vectormemory memory_type
        memory_type = meta.get("memory_type", meta.get("type", ""))
        if memory_type == "clone":
            return "clone_silos"
        if memory_type == "knowledge":
            return "retrieval"
        if memory_type == "chat":
            return "agent_context"

        # Source-based routing
        source = meta.get("source", "")
        if source == "rag_pipeline" or "doc_id" in meta:
            return "retrieval"

        # Content heuristics for agent context
        if content:
            content_lower = content.lower()
            # Short conversational turns likely belong to agent_context
            if len(content.split()) < 50 and any(
                marker in content_lower
                for marker in ["user said", "agent:", "human:", "assistant:", "you:"]
            ):
                return "agent_context"
            # Clone-specific keywords
            if any(kw in content_lower for kw in ["clone", "silo", "isolated"]):
                return "clone_silos"

        # Default: semantic memory (long-term knowledge)
        return "semantic_memory"

    # ── Migration from vectormemory.py SQLite + ChromaDB ──────────────────

    async def migrate_from_vectormemory(
        self,
        vector_db_path: Optional[str] = None,
        chroma_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reads existing ChromaDB collections and SQLite metadata,
        re-indexes into VectorStore collections.

        Args:
            vector_db_path: Path to vectormemory's SQLite database.
                            Default: data/vector_memory.db
            chroma_path: Path to vectormemory's ChromaDB persistent client data.
                         Default: data/chromadb

        Returns:
            Dict with keys: "total", "collections" (per-collection counts), "errors"
        """
        vdb_path = vector_db_path or _DEFAULT_VECTOR_DB
        cpath = chroma_path or _DEFAULT_CHROMA_PATH

        result: Dict[str, Any] = {
            "source": "vectormemory",
            "total": 0,
            "collections": {},
            "errors": [],
            "collections_detail": [],
        }

        # Strategy 1: Read from existing ChromaDB collection directly
        chroma_count = await self._migrate_from_chromadb(cpath, result)

        # Strategy 2: Read from SQLite metadata (catches items not in ChromaDB)
        sqlite_count = await self._migrate_from_sqlite(vdb_path, result)

        # Strategy 3: Scan the SQLite main memories table directly
        sqlite_memories_count = await self._migrate_from_sqlite_memories(vdb_path, result)

        result["total"] = chroma_count + sqlite_count + sqlite_memories_count
        logger.info(
            f"✅ VectorMemory migration complete — "
            f"total={result['total']}, collections={result['collections']}, "
            f"errors={len(result['errors'])}"
        )
        return result

    async def _migrate_from_chromadb(
        self, chroma_path: str, result: Dict[str, Any]
    ) -> int:
        """Migrate from existing ChromaDB persistent client data."""
        count = 0
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            logger.warning("⚠️  chromadb not installed — skipping ChromaDB migration")
            return 0

        chroma_dir = Path(chroma_path)
        if not chroma_dir.exists():
            logger.info(f"ℹ️  No ChromaDB data at {chroma_path} — skipping")
            return 0

        try:
            client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False, allow_reset=False),
            )

            # List all existing collections
            collections = client.list_collections()
            if not collections:
                logger.info("ℹ️  No collections found in existing ChromaDB")
                return 0

            for collection in collections:
                col_name = collection.name
                try:
                    all_data = collection.get(include=["documents", "metadatas", "embeddings"])
                    if not all_data or not all_data["ids"]:
                        continue

                    for i, cid in enumerate(all_data["ids"]):
                        try:
                            content = all_data["documents"][i] if all_data.get("documents") else ""
                            meta = (
                                all_data["metadatas"][i]
                                if all_data.get("metadatas")
                                else {}
                            )
                            embedding = (
                                all_data["embeddings"][i]
                                if all_data.get("embeddings")
                                else []
                            )

                            # Infer target collection
                            target_col = self._infer_collection(content, meta)

                            stored = await self._store.store(
                                collection=target_col,
                                id=cid,
                                embedding=embedding,
                                metadata=meta,
                                content=content,
                            )
                            if stored:
                                count += 1
                                result["collections"][target_col] = (
                                    result["collections"].get(target_col, 0) + 1
                                )
                            else:
                                result["errors"].append(
                                    f"Failed to store {cid} from ChromaDB collection {col_name}"
                                )
                        except Exception as e:
                            result["errors"].append(
                                f"Item error in ChromaDB collection {col_name}, id {cid}: {e}"
                            )

                    logger.info(
                        f"  → Migrated {count} items from ChromaDB collection '{col_name}'"
                    )

                except Exception as e:
                    logger.warning(f"⚠️  Error reading ChromaDB collection '{col_name}': {e}")
                    result["errors"].append(f"ChromaDB collection '{col_name}': {e}")

        except Exception as e:
            logger.warning(f"⚠️  ChromaDB migration error: {e}")
            result["errors"].append(f"ChromaDB client error: {e}")

        return count

    async def _migrate_from_sqlite(
        self, vector_db_path: str, result: Dict[str, Any]
    ) -> int:
        """Migrate from vectormemory's chroma_metadata SQLite table."""
        count = 0
        db_path = Path(vector_db_path)
        if not db_path.exists():
            logger.info(f"ℹ️  No vector memory DB at {vector_db_path} — skipping SQLite metadata")
            return 0

        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row

                # Check if chroma_metadata table exists
                table_check = conn.execute(
                    "SELECT name FROM sqlite_master WHERE name='chroma_metadata'"
                ).fetchone()
                if not table_check:
                    logger.info("ℹ️  No chroma_metadata table found in vector memory DB")
                    return 0

                rows = conn.execute(
                    "SELECT * FROM chroma_metadata ORDER BY created_at ASC"
                ).fetchall()

                for row in rows:
                    try:
                        memory_id = row["memory_id"]
                        chroma_id = row["chroma_id"]
                        content = row["content"] or ""
                        memory_type = row["memory_type"]
                        user_id = row["user_id"]
                        metadata_str = row["metadata"]
                        metadata = json.loads(metadata_str) if metadata_str else {}
                        created_at = row["created_at"]

                        # Enrich metadata
                        metadata["memory_id"] = memory_id
                        metadata["chroma_id"] = chroma_id
                        metadata["memory_type"] = memory_type
                        metadata["user_id"] = user_id
                        metadata["created_at"] = created_at
                        metadata["source"] = "vectormemory_migration"

                        # Infer target collection
                        target_col = self._infer_collection(content, metadata)

                        # Generate embedding for this content
                        stored = await self._store.store_text(
                            collection=target_col,
                            id=memory_id,
                            text=content,
                            metadata=metadata,
                        )
                        if stored:
                            count += 1
                            result["collections"][target_col] = (
                                result["collections"].get(target_col, 0) + 1
                            )
                        else:
                            result["errors"].append(
                                f"Failed to store {memory_id} from chroma_metadata"
                            )
                    except Exception as e:
                        result["errors"].append(
                            f"Row error in chroma_metadata: {e}"
                        )

                logger.info(f"  → Migrated {count} items from chroma_metadata SQLite table")

        except Exception as e:
            logger.warning(f"⚠️  SQLite chroma_metadata migration error: {e}")
            result["errors"].append(f"SQLite chroma_metadata error: {e}")

        return count

    async def _migrate_from_sqlite_memories(
        self, vector_db_path: str, result: Dict[str, Any]
    ) -> int:
        """Migrate from vectormemory's main memories SQLite table."""
        count = 0
        db_path = Path(vector_db_path)
        if not db_path.exists():
            return 0

        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row

                # Check if memories table exists
                table_check = conn.execute(
                    "SELECT name FROM sqlite_master WHERE name='memories'"
                ).fetchone()
                if not table_check:
                    return 0

                rows = conn.execute(
                    "SELECT * FROM memories ORDER BY created_at ASC"
                ).fetchall()

                for row in rows:
                    try:
                        memory_id = row["id"]
                        content = row["content"] or ""
                        memory_type = row["memory_type"]
                        user_id = row["user_id"]
                        metadata_str = row["metadata"]
                        metadata = json.loads(metadata_str) if metadata_str else {}
                        created_at = row["created_at"]

                        # Enrich metadata
                        metadata["memory_id"] = memory_id
                        metadata["memory_type"] = memory_type
                        metadata["user_id"] = user_id
                        metadata["created_at"] = created_at
                        metadata["source"] = "vectormemory_migration"

                        # Infer target collection
                        target_col = self._infer_collection(content, metadata)

                        # Generate embedding for this content
                        stored = await self._store.store_text(
                            collection=target_col,
                            id=memory_id,
                            text=content,
                            metadata=metadata,
                        )
                        if stored:
                            count += 1
                            result["collections"][target_col] = (
                                result["collections"].get(target_col, 0) + 1
                            )
                        else:
                            result["errors"].append(
                                f"Failed to store {memory_id} from memories table"
                            )
                    except Exception as e:
                        result["errors"].append(
                            f"Row error in memories table: {e}"
                        )

                logger.info(f"  → Migrated {count} items from memories SQLite table")

        except Exception as e:
            logger.warning(f"⚠️  SQLite memories migration error: {e}")
            result["errors"].append(f"SQLite memories error: {e}")

        return count

    # ── JSONL Migration ──────────────────────────────────────────────────

    async def migrate_from_jsonl(
        self, glob_pattern: str = "data/**/*.jsonl"
    ) -> Dict[str, Any]:
        """
        Reads JSONL files, generates embeddings, stores in appropriate collection
        based on content analysis.

        Args:
            glob_pattern: Glob pattern for JSONL files to process.
                          Default: data/**/*.jsonl

        Returns:
            Dict with keys: "total", "files_processed", "collections", "errors"
        """
        result: Dict[str, Any] = {
            "source": "jsonl",
            "total": 0,
            "files_processed": 0,
            "collections": {},
            "errors": [],
        }

        jsonl_files = glob.glob(glob_pattern, recursive=True)
        if not jsonl_files:
            logger.info(f"ℹ️  No JSONL files matching '{glob_pattern}'")
            return result

        for filepath in sorted(jsonl_files):
            try:
                file_count = await self._migrate_single_jsonl(filepath, result)
                if file_count > 0:
                    result["files_processed"] += 1
                    logger.info(f"  → File '{filepath}': {file_count} items migrated")
            except Exception as e:
                logger.warning(f"⚠️  Error processing JSONL file '{filepath}': {e}")
                result["errors"].append(f"File '{filepath}': {e}")

        logger.info(
            f"✅ JSONL migration complete — "
            f"files={result['files_processed']}, total={result['total']}, "
            f"collections={result['collections']}, errors={len(result['errors'])}"
        )
        return result

    async def _migrate_single_jsonl(
        self, filepath: str, result: Dict[str, Any]
    ) -> int:
        """Migrate a single JSONL file into VectorStore."""
        count = 0
        file_key = Path(filepath).stem

        with open(filepath, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    result["errors"].append(
                        f"JSON parse error in {filepath} at line {line_idx}"
                    )
                    continue

                try:
                    # Extract content and metadata from the record
                    content = (
                        record.get("content")
                        or record.get("message")
                        or record.get("text")
                        or record.get("data")
                        or json.dumps(record)
                    )
                    if isinstance(content, (dict, list)):
                        content = json.dumps(content)

                    record_id = record.get(
                        "id",
                        record.get("memory_id", f"{file_key}_line{line_idx}"),
                    )
                    metadata = {
                        k: v
                        for k, v in record.items()
                        if k not in ("content", "message", "text", "data", "embedding")
                    }
                    metadata["source_file"] = filepath
                    metadata["source"] = "jsonl_migration"

                    # Infer target collection
                    target_col = self._infer_collection(content, metadata)

                    # If record has pre-computed embedding, use it
                    if "embedding" in record and isinstance(record["embedding"], list):
                        stored = await self._store.store(
                            collection=target_col,
                            id=record_id,
                            embedding=record["embedding"],
                            metadata=metadata,
                            content=content,
                        )
                    else:
                        stored = await self._store.store_text(
                            collection=target_col,
                            id=record_id,
                            text=content,
                            metadata=metadata,
                        )

                    if stored:
                        count += 1
                        result["collections"][target_col] = (
                            result["collections"].get(target_col, 0) + 1
                        )
                    else:
                        result["errors"].append(
                            f"Failed to store record {record_id} from {filepath}:{line_idx}"
                        )

                except Exception as e:
                    result["errors"].append(
                        f"Record error in {filepath} at line {line_idx}: {e}"
                    )

        result["total"] += count
        return count

    # ── Run All Migrations ────────────────────────────────────────────────

    async def migrate_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Runs all migration strategies.

        Returns:
            Dict[str, Dict[str, Any]] — keys are migration source names, values
            are the per-source result dicts.
        """
        results: Dict[str, Dict[str, Any]] = {}

        logger.info("🔄 Starting full vector data migration...")

        # 1. Migrate from existing vectormemory (ChromaDB + SQLite)
        try:
            vm_result = await self.migrate_from_vectormemory()
            results["vectormemory"] = vm_result
            logger.info(
                f"  ✓ vectormemory: {vm_result.get('total', 0)} items migrated"
            )
        except Exception as e:
            logger.error(f"❌ vectormemory migration failed: {e}")
            results["vectormemory"] = {"error": str(e), "total": 0}

        # 2. Migrate from JSONL files
        try:
            jsonl_result = await self.migrate_from_jsonl()
            results["jsonl"] = jsonl_result
            logger.info(
                f"  ✓ jsonl: {jsonl_result.get('total', 0)} items from "
                f"{jsonl_result.get('files_processed', 0)} files"
            )
        except Exception as e:
            logger.error(f"❌ jsonl migration failed: {e}")
            results["jsonl"] = {"error": str(e), "total": 0}

        # Summary
        total = sum(
            r.get("total", 0) for r in results.values() if isinstance(r, dict)
        )
        errors = sum(
            len(r.get("errors", [])) for r in results.values() if isinstance(r, dict)
        )
        logger.info(
            f"✅ Full migration complete — total={total}, errors={errors}"
        )

        return results
