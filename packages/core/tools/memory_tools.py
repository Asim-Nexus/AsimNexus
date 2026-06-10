#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Memory Tools for Agent System

Tool functions for agent memory operations: search, store, and recall.
Uses the AsimNexus memory infrastructure (vector DB + key-value store).

Each function has a TOOL_DEFINITION dict for OpenAI-compatible function calling,
proper error handling, and structured JSON-serializable return values.

Security: These are SENSITIVE-level tools (read/write user data).
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.Tools.Memory")

# ─── Constants ─────────────────────────────────────────────────────────────────

_DEFAULT_MEMORY_LIMIT = 10
_DEFAULT_RECALL_LIMIT = 20
_MAX_MEMORY_VALUE_LENGTH = 10000
_MEMORY_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "agent_memory.jsonl"
)


# ─── Helper ────────────────────────────────────────────────────────────────────

def _safe_result(success: bool, data: Any = None,
                 error: Optional[str] = None, **extra) -> Dict:
    """Build a standardized result dict."""
    result = {"success": success, "error": error}
    if data is not None:
        result["data"] = data
    result.update(extra)
    return result


def _get_memory_file_path(user_id: str) -> str:
    """Get the memory file path for a specific user."""
    mem_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "memories"
    )
    os.makedirs(mem_dir, exist_ok=True)
    return os.path.join(mem_dir, f"{user_id}.jsonl")


def _load_memories(user_id: str, limit: int = 100) -> List[Dict]:
    """Load memories for a user from the JSONL file."""
    path = _get_memory_file_path(user_id)
    memories = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            memories.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Failed to load memories from {path}: {e}")
    return memories[-limit:]  # Return most recent


def _save_memory(user_id: str, memory: Dict):
    """Append a memory to the user's JSONL file."""
    path = _get_memory_file_path(user_id)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory) + "\n")
    except Exception as e:
        logger.error(f"Failed to save memory to {path}: {e}")
        raise


# ─── TOOL: memory_search ───────────────────────────────────────────────────────

TOOL_DEFINITION_MEMORY_SEARCH = {
    "name": "memory_search",
    "description": "Search vector memory for semantically similar content. Returns relevant memories matching the query.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query describing what to find in memories."
            },
            "user_id": {
                "type": "string",
                "description": "User ID to search memories for."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results (default: 10, max: 50).",
                "default": 10
            }
        },
        "required": ["query", "user_id"]
    }
}


def memory_search(query: str, user_id: str, limit: int = _DEFAULT_MEMORY_LIMIT) -> Dict[str, Any]:
    """Search vector memory for semantically similar content.

    Uses ChromaDB if available, falls back to keyword search on JSONL file.

    Args:
        query: Search query.
        user_id: User ID to scope search.
        limit: Max results (max 50).

    Returns:
        Dict with keys: success, results (list of {id, key, value, score, timestamp})
    """
    logger.info(f"Memory search: user={user_id}, query='{query[:100]}', limit={limit}")

    limit = min(max(1, limit), 50)
    results = []

    # Try ChromaDB vector search first
    try:
        import chromadb
        from chromadb.config import Settings

        chroma_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "chromadb"
        )

        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )

        collection_name = f"memory_{user_id}"
        try:
            collection = client.get_collection(name=collection_name)
            search_results = collection.query(
                query_texts=[query],
                n_results=limit,
            )

            if search_results and search_results.get("ids") and len(search_results["ids"]) > 0:
                for i in range(len(search_results["ids"][0])):
                    results.append({
                        "id": search_results["ids"][0][i],
                        "key": "",
                        "value": search_results["documents"][0][i] if search_results.get("documents") else "",
                        "score": search_results["distances"][0][i] if search_results.get("distances") else 0,
                        "timestamp": "",
                    })
                logger.info(f"ChromaDB returned {len(results)} results")
                return _safe_result(
                    success=True,
                    data={
                        "results": results,
                        "source": "chromadb",
                        "total": len(results),
                    }
                )
        except Exception as e:
            logger.debug(f"ChromaDB collection query failed: {e}")

    except ImportError:
        logger.debug("chromadb not available, falling back to keyword search")

    # Fallback: keyword search on JSONL
    query_lower = query.lower()
    query_terms = set(query_lower.split())

    memories = _load_memories(user_id, limit=500)
    scored = []

    for mem in memories:
        text = f"{mem.get('key', '')} {mem.get('value', '')}".lower()
        # Simple keyword overlap scoring
        mem_terms = set(text.split())
        overlap = len(query_terms & mem_terms)
        if overlap > 0:
            scored.append({
                "id": mem.get("id", ""),
                "key": mem.get("key", ""),
                "value": mem.get("value", ""),
                "score": overlap / max(len(query_terms), 1),
                "timestamp": mem.get("timestamp", ""),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    results = scored[:limit]

    return _safe_result(
        success=True,
        data={
            "results": results,
            "source": "keyword",
            "total": len(results),
        }
    )


# ─── TOOL: memory_store ────────────────────────────────────────────────────────

TOOL_DEFINITION_MEMORY_STORE = {
    "name": "memory_store",
    "description": "Store a key-value pair in agent memory for future recall.",
    "parameters": {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Memory key (used for lookup and categorization)."
            },
            "value": {
                "type": "string",
                "description": "Memory content to store."
            },
            "user_id": {
                "type": "string",
                "description": "User ID to associate the memory with."
            }
        },
        "required": ["key", "value", "user_id"]
    }
}


def memory_store(key: str, value: str, user_id: str) -> Dict[str, Any]:
    """Store a key-value pair in agent memory.

    Stores to both JSONL persistent file and ChromaDB vector store (if available).

    Args:
        key: Memory key.
        value: Memory value/content.
        user_id: User ID.

    Returns:
        Dict with keys: success, id, stored_at
    """
    logger.info(f"Memory store: user={user_id}, key='{key}'")

    if len(value) > _MAX_MEMORY_VALUE_LENGTH:
        value = value[:_MAX_MEMORY_VALUE_LENGTH]
        logger.warning(f"Memory value truncated to {_MAX_MEMORY_VALUE_LENGTH} chars")

    memory_id = f"mem_{user_id}_{int(time.time())}_{hash(key) % 10000}"
    timestamp = datetime.utcnow().isoformat()

    memory_entry = {
        "id": memory_id,
        "key": key,
        "value": value,
        "user_id": user_id,
        "timestamp": timestamp,
    }

    # Save to JSONL
    try:
        _save_memory(user_id, memory_entry)
        logger.info(f"Memory saved to JSONL: {memory_id}")
    except Exception as e:
        return _safe_result(False, error=f"Failed to save memory: {e}")

    # Also store in ChromaDB if available
    try:
        import chromadb
        from chromadb.config import Settings

        chroma_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "chromadb"
        )

        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )

        collection_name = f"memory_{user_id}"
        try:
            collection = client.get_or_create_collection(name=collection_name)
            collection.add(
                documents=[value],
                metadatas=[{"key": key, "user_id": user_id, "timestamp": timestamp}],
                ids=[memory_id],
            )
            logger.info(f"Memory stored in ChromaDB: {memory_id}")
        except Exception as e:
            logger.debug(f"ChromaDB store failed (non-fatal): {e}")

    except ImportError:
        logger.debug("chromadb not available, memory stored to JSONL only")

    return _safe_result(
        success=True,
        data={
            "id": memory_id,
            "key": key,
            "stored_at": timestamp,
        }
    )


# ─── TOOL: memory_recall ───────────────────────────────────────────────────────

TOOL_DEFINITION_MEMORY_RECALL = {
    "name": "memory_recall",
    "description": "Recall recent memories for a user. Returns the most recent memories chronologically.",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User ID to recall memories for."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of recent memories (default: 20, max: 100).",
                "default": 20
            }
        },
        "required": ["user_id"]
    }
}


def memory_recall(user_id: str, limit: int = _DEFAULT_RECALL_LIMIT) -> Dict[str, Any]:
    """Recall recent memories for a user.

    Args:
        user_id: User ID.
        limit: Max number of recent memories (max 100).

    Returns:
        Dict with keys: success, memories (list of {id, key, value, timestamp})
    """
    logger.info(f"Memory recall: user={user_id}, limit={limit}")

    limit = min(max(1, limit), 100)

    try:
        memories = _load_memories(user_id, limit=limit)

        # Sort by timestamp descending (most recent first)
        memories.sort(key=lambda m: m.get("timestamp", ""), reverse=True)

        # Return requested number
        results = memories[:limit]

        logger.info(f"Recalled {len(results)} memories for user {user_id}")
        return _safe_result(
            success=True,
            data={
                "memories": results,
                "total": len(results),
            }
        )

    except Exception as e:
        logger.error(f"Failed to recall memories for user {user_id}: {e}")
        return _safe_result(False, error=str(e))
