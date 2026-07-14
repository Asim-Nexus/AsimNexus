#!/usr/bin/env python3
"""
STATUS: REAL — Offline Sync Engine Tests
AsimNexus Offline Sync Testing
=============================
Tests for CRDT-based offline synchronization.
"""

import pytest

def test_sync_priority_enum():
    """Test sync priority enum."""
    from core.mesh.offline_sync_engine import SyncPriority
    assert SyncPriority.CRITICAL.value == 0
    assert SyncPriority.HIGH.value == 1

def test_sync_operation():
    """Test sync operation creation."""
    from core.mesh.offline_sync_engine import SyncOperation, SyncPriority
    op = SyncOperation(
        id="test_001",
        crdt_id="test_crdt",
        operation="add"
    )
    assert op.id == "test_001"
    assert op.status.value == "pending"

def test_sync_status():
    """Test sync status data class."""
    from core.mesh.offline_sync_engine import SyncStatus
    status = SyncStatus()
    assert status.pending_count >= 0

def test_offline_sync_engine():
    """Test offline sync engine initialization."""
    from core.mesh.offline_sync_engine import OfflineSyncEngine
    engine = OfflineSyncEngine()
    status = engine.get_sync_status()
    assert hasattr(status, "is_online")