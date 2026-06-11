"""
AsimNexus Sync Bridge
=====================
Provides the offline_sync module's public API via core.sync namespace.

Exports:
    OpType       — Enum: CREATE, UPDATE, DELETE
    SyncEngine   — Sync engine wrapper (enqueue, flush, status, stats)
    get_sync_engine  — Singleton factory
    reset_sync_engine — Reset singleton (for testing)
"""

from core.sync.offline_sync import OpType, SyncEngine, get_sync_engine, reset_sync_engine

__all__ = ["OpType", "SyncEngine", "get_sync_engine", "reset_sync_engine"]
