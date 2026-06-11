#!/usr/bin/env python3
"""
Bridge module: [`mesh/offline_sync_engine.py`](../../mesh/offline_sync_engine.py)
================================================================================

Provides the `get_sync_engine()` / `OpType` / `SyncEngine` API that
the backend [`simple_backend.py`](../../simple_backend.py) imports for
`/api/sync/*` endpoints.

This is an **adapter layer** — the real implementation lives in
[`mesh/offline_sync_engine.py`](../../mesh/offline_sync_engine.py) (873 lines,
87 tests). This module simply re-exports and adapts the singleton factory
to match what the backend expects.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any

from mesh.offline_sync_engine import (
    OfflineSyncEngine as _RealEngine,
    SyncOperation as _RealOperation,
    SyncPriority as _RealPriority,
    SyncOperationStatus as _RealStatus,
    get_offline_sync_engine as _get_real_engine,
    reset_offline_sync_engine as _reset_real_engine,
)

logger = logging.getLogger("AsimNexus.Sync.Bridge")


# ─── OpType (enum expected by backend endpoints) ───────────────────────────────

class OpType(Enum):
    """Operation types matching the legacy backend API."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


# ─── SyncEngine (adapter wrapping OfflineSyncEngine) ──────────────────────────

class SyncEngine:
    """
    Adapter that wraps [`OfflineSyncEngine`](:160) to provide the
    `.status()`, `.enqueue()`, `.flush()`, `.queue_list()` interface
    expected by [`simple_backend.py`](../../simple_backend.py) endpoints.
    """

    def __init__(self):
        self._engine: _RealEngine = _get_real_engine()
        self._engine.start_sync_loop()
        logger.info("SyncEngine bridge initialized — wrapped OfflineSyncEngine")

    # ── Public API ──────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return sync engine status as a plain dict."""
        s = self._engine.get_sync_status()
        d = s.to_dict()
        d["node_id"] = self._engine._node_id
        d["queue_size"] = (
            self._engine._count_by_status(_RealStatus.PENDING)
            + self._engine._count_by_status(_RealStatus.IN_FLIGHT)
        )
        return d

    def enqueue(self, op_type: OpType, entity_type: str,
                entity_id: str, payload: Optional[Dict] = None) -> "_SyncOp":
        """
        Enqueue an operation for sync.

        Args:
            op_type: Type of operation (CREATE / UPDATE / DELETE).
            entity_type: The entity kind (e.g. "message", "memory").
            entity_id: The entity identifier.
            payload: Optional data payload.

        Returns:
            A SyncOp wrapper with .to_dict().
        """
        crdt_id = f"{entity_type}:{entity_id}"
        op = self._engine.enqueue_operation(
            crdt_id=crdt_id,
            operation=op_type.value,
            key=entity_id,
            value=payload,
            priority=_RealPriority.MEDIUM,
        )
        return _SyncOp(op)

    def flush(self) -> Dict[str, Any]:
        """Trigger immediate sync and return status."""
        s = self._engine.sync_now()
        d = s.to_dict()
        d["flushed"] = True
        return d

    def queue_list(self) -> List[Dict[str, Any]]:
        """Return pending operations as dicts."""
        ops = self._engine.get_pending_operations()
        return [o.to_dict() for o in ops]

    # ── Additional helpers (not required by backend but useful) ────────────

    def pending_count(self) -> int:
        """Number of operations waiting to sync."""
        return self._engine._count_by_status(_RealStatus.PENDING)

    def conflicts(self) -> List[Dict[str, Any]]:
        """Return unresolved conflicts as dicts."""
        return [c.to_dict() for c in self._engine.get_conflicts(unresolved_only=True)]

    def stats(self) -> Dict[str, Any]:
        """Comprehensive engine statistics."""
        return self._engine.get_stats()


# ─── SyncOp (wrapper with to_dict) ────────────────────────────────────────────

class _SyncOp:
    """Wrapper returned by enqueue(), provides .to_dict()."""

    def __init__(self, op: _RealOperation):
        self._op = op

    def to_dict(self) -> Dict[str, Any]:
        return self._op.to_dict()


# ─── Singleton Factory ────────────────────────────────────────────────────────

_sync_engine_instance: Optional[SyncEngine] = None


def get_sync_engine() -> SyncEngine:
    """Get or create the singleton SyncEngine adapter."""
    global _sync_engine_instance
    if _sync_engine_instance is None:
        _sync_engine_instance = SyncEngine()
    return _sync_engine_instance


def reset_sync_engine() -> None:
    """Reset the singleton (for testing)."""
    global _sync_engine_instance
    if _sync_engine_instance:
        _sync_engine_instance._engine.stop_sync_loop()
    _sync_engine_instance = None
    _reset_real_engine()


# ─── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
    "OpType",
    "SyncEngine",
    "get_sync_engine",
    "reset_sync_engine",
]
