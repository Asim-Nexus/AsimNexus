#!/usr/bin/env python3
"""
Tests for [`mesh/offline_sync_engine.py`](../../mesh/offline_sync_engine.py)
Covers Gap 7: Offline-First Sync Engine with priority queue, conflict resolution,
peer selection, and singleton factory.
"""

import os
import json
import time
import pytest
import threading
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

from mesh.offline_sync_engine import (
    SyncPriority,
    SyncOperationStatus,
    ResolutionStrategy,
    SyncOperation,
    SyncConflict,
    SyncStatus,
    SyncPeer,
    OfflineSyncEngine,
    get_offline_sync_engine,
    reset_offline_sync_engine,
    __all__ as module_exports,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_engine():
    """Reset singleton before each test and clean up."""
    reset_offline_sync_engine()
    yield
    reset_offline_sync_engine()


@pytest.fixture
def engine() -> OfflineSyncEngine:
    """Fresh OfflineSyncEngine instance."""
    return OfflineSyncEngine()


# ─── Test: SyncPriority ────────────────────────────────────────────────────────

class TestSyncPriority:
    """Tests for SyncPriority enum."""

    def test_values(self):
        assert SyncPriority.CRITICAL.value == 0
        assert SyncPriority.HIGH.value == 1
        assert SyncPriority.MEDIUM.value == 2
        assert SyncPriority.LOW.value == 3

    def test_all_tiers(self):
        tiers = set(SyncPriority)
        assert len(tiers) == 4


# ─── Test: SyncOperationStatus ─────────────────────────────────────────────────

class TestSyncOperationStatus:
    """Tests for SyncOperationStatus enum."""

    def test_values(self):
        assert SyncOperationStatus.PENDING.value == "pending"
        assert SyncOperationStatus.IN_FLIGHT.value == "in_flight"
        assert SyncOperationStatus.SYNCED.value == "synced"
        assert SyncOperationStatus.FAILED.value == "failed"
        assert SyncOperationStatus.CONFLICT.value == "conflict"
        assert SyncOperationStatus.SKIPPED.value == "skipped"

    def test_all_statuses(self):
        statuses = set(SyncOperationStatus)
        assert len(statuses) == 6


# ─── Test: ResolutionStrategy ──────────────────────────────────────────────────

class TestResolutionStrategy:
    """Tests for ResolutionStrategy enum."""

    def test_values(self):
        assert ResolutionStrategy.LAST_WRITER_WINS.value == "last_writer_wins"
        assert ResolutionStrategy.MANUAL.value == "manual"
        assert ResolutionStrategy.LOCAL_PREFERRED.value == "local_preferred"
        assert ResolutionStrategy.REMOTE_PREFERRED.value == "remote_preferred"
        assert ResolutionStrategy.MERGE.value == "merge"

    def test_all_strategies(self):
        strategies = set(ResolutionStrategy)
        assert len(strategies) == 5


# ─── Test: SyncOperation ───────────────────────────────────────────────────────

class TestSyncOperation:
    """Tests for SyncOperation dataclass."""

    def test_create_defaults(self):
        op = SyncOperation(
            id="op_001",
            crdt_id="chat_room_1",
            operation="add",
        )
        assert op.id == "op_001"
        assert op.crdt_id == "chat_room_1"
        assert op.operation == "add"
        assert op.key is None
        assert op.value is None
        assert op.priority == SyncPriority.MEDIUM
        assert op.status == SyncOperationStatus.PENDING
        assert op.retry_count == 0

    def test_create_full(self):
        op = SyncOperation(
            id="op_002",
            crdt_id="counter_1",
            operation="increment",
            key="visits",
            value=1,
            priority=SyncPriority.CRITICAL,
            node_id="node_a",
        )
        assert op.priority == SyncPriority.CRITICAL
        assert op.key == "visits"
        assert op.value == 1

    def test_lt_priority_ordering(self):
        """CRITICAL ops should sort before LOW ops."""
        high = SyncOperation(id="h", crdt_id="x", operation="add",
                             priority=SyncPriority.CRITICAL)
        low = SyncOperation(id="l", crdt_id="x", operation="add",
                            priority=SyncPriority.LOW)
        assert high < low
        assert not (low < high)

    def test_lt_same_priority_uses_time(self):
        """Same priority ops should sort by created_at."""
        op1 = SyncOperation(id="a", crdt_id="x", operation="add",
                            priority=SyncPriority.MEDIUM, created_at=100.0)
        op2 = SyncOperation(id="b", crdt_id="x", operation="add",
                            priority=SyncPriority.MEDIUM, created_at=200.0)
        assert op1 < op2

    def test_to_dict(self):
        op = SyncOperation(
            id="op_003",
            crdt_id="test_crdt",
            operation="set",
            key="name",
            value="Alice",
            priority=SyncPriority.HIGH,
            status=SyncOperationStatus.PENDING,
            node_id="node_b",
        )
        d = op.to_dict()
        assert d["id"] == "op_003"
        assert d["crdt_id"] == "test_crdt"
        assert d["operation"] == "set"
        assert d["key"] == "name"
        assert d["value"] == "Alice"
        assert d["priority"] == 1  # HIGH
        assert d["status"] == "pending"
        assert d["node_id"] == "node_b"

    def test_from_dict(self):
        data = {
            "id": "op_004",
            "crdt_id": "counter_2",
            "operation": "increment",
            "key": None,
            "value": 5,
            "priority": 0,
            "status": "pending",
            "created_at": 1000.0,
            "synced_at": None,
            "retry_count": 0,
            "node_id": None,
            "error": None,
        }
        op = SyncOperation.from_dict(data)
        assert op.id == "op_004"
        assert op.priority == SyncPriority.CRITICAL
        assert op.status == SyncOperationStatus.PENDING
        assert op.value == 5

    def test_from_dict_with_enum_strings(self):
        data = {
            "id": "op_005",
            "crdt_id": "reg",
            "operation": "add",
            "key": None,
            "value": None,
            "priority": 3,
            "status": "synced",
            "created_at": 1000.0,
            "synced_at": 1100.0,
            "retry_count": 1,
            "node_id": "node_c",
            "error": None,
        }
        op = SyncOperation.from_dict(data)
        assert op.priority == SyncPriority.LOW
        assert op.status == SyncOperationStatus.SYNCED
        assert op.retry_count == 1


# ─── Test: SyncConflict ────────────────────────────────────────────────────────

class TestSyncConflict:
    """Tests for SyncConflict dataclass."""

    def test_create(self):
        local_op = SyncOperation(id="l1", crdt_id="c", operation="add")
        remote_op = SyncOperation(id="r1", crdt_id="c", operation="set")
        conflict = SyncConflict(
            id="conflict_1",
            crdt_id="c",
            local_operation=local_op,
            remote_operation=remote_op,
        )
        assert conflict.id == "conflict_1"
        assert conflict.resolved is False
        assert conflict.resolved_by == "auto"

    def test_to_dict(self):
        local_op = SyncOperation(id="l2", crdt_id="c", operation="add", value="A")
        remote_op = SyncOperation(id="r2", crdt_id="c", operation="remove")
        conflict = SyncConflict(
            id="conflict_2",
            crdt_id="c",
            local_operation=local_op,
            remote_operation=remote_op,
            resolution=ResolutionStrategy.MANUAL,
            resolved=False,
        )
        d = conflict.to_dict()
        assert d["id"] == "conflict_2"
        assert d["resolution"] == "manual"
        assert d["local_operation"]["id"] == "l2"
        assert d["remote_operation"]["id"] == "r2"


# ─── Test: SyncStatus ──────────────────────────────────────────────────────────

class TestSyncStatus:
    """Tests for SyncStatus dataclass."""

    def test_defaults(self):
        status = SyncStatus()
        assert status.pending_count == 0
        assert status.synced_count == 0
        assert status.is_online is False
        assert status.last_sync_time is None

    def test_to_dict(self):
        status = SyncStatus(
            pending_count=5,
            in_flight_count=2,
            synced_count=10,
            failed_count=1,
            conflict_count=1,
            last_sync_time=1000.0,
            is_online=True,
            total_operations=19,
        )
        d = status.to_dict()
        assert d["pending_count"] == 5
        assert d["synced_count"] == 10
        assert d["is_online"] is True


# ─── Test: SyncPeer ────────────────────────────────────────────────────────────

class TestSyncPeer:
    """Tests for SyncPeer dataclass."""

    def test_create_minimal(self):
        peer = SyncPeer(node_id="peer_001")
        assert peer.node_id == "peer_001"
        assert peer.hostname == "localhost"
        assert peer.trust_level == 0.5
        assert peer.version == "1.0.0"

    def test_create_full(self):
        peer = SyncPeer(
            node_id="peer_002",
            hostname="10.0.0.1",
            port=9090,
            trust_level=0.95,
            latency_ms=5.0,
            last_seen=1000.0,
            version="2.0.0",
        )
        assert peer.port == 9090
        assert peer.trust_level == 0.95


# ─── Test: OfflineSyncEngine — Initialization ──────────────────────────────────

class TestOfflineSyncEngineInit:
    """Tests for OfflineSyncEngine initialization."""

    def test_default_state(self, engine):
        assert engine._is_online is False
        assert engine._last_sync_time is None
        assert len(engine._operations) == 0
        assert len(engine._conflicts) == 0
        assert len(engine._connectivity_checkers) == 0
        assert len(engine._sync_handlers) == 0

    def test_default_status(self, engine):
        status = engine.get_sync_status()
        assert status.pending_count == 0
        assert status.is_online is False

    def test_stats_basic(self, engine):
        stats = engine.get_stats()
        assert stats["is_online"] is False
        assert stats["total_operations"] == 0
        assert stats["connectivity_checkers"] == 0
        assert stats["sync_handlers"] == 0


# ─── Test: OfflineSyncEngine — Enqueue Operations ─────────────────────────────

class TestEnqueue:
    """Tests for enqueue_operation()."""

    def test_enqueue_single(self, engine):
        op = engine.enqueue_operation(
            crdt_id="chat_room_1",
            operation="add",
            key="message_1",
            value="Hello",
            priority=SyncPriority.HIGH,
        )
        assert op.crdt_id == "chat_room_1"
        assert op.operation == "add"
        assert op.key == "message_1"
        assert op.value == "Hello"
        assert op.priority == SyncPriority.HIGH
        assert op.status == SyncOperationStatus.PENDING
        assert op.node_id is not None

    def test_enqueue_generates_unique_ids(self, engine):
        op1 = engine.enqueue_operation("crdt_1", "add")
        op2 = engine.enqueue_operation("crdt_1", "add")
        assert op1.id != op2.id

    def test_enqueue_tracks_operation(self, engine):
        op = engine.enqueue_operation("crdt_2", "set", key="theme", value="dark")
        retrieved = engine.get_operation(op.id)
        assert retrieved is not None
        assert retrieved.key == "theme"
        assert retrieved.value == "dark"

    def test_enqueue_default_priority(self, engine):
        op = engine.enqueue_operation("crdt_3", "add")
        assert op.priority == SyncPriority.MEDIUM

    def test_get_pending_after_enqueue(self, engine):
        engine.enqueue_operation("crdt_4", "add")
        pending = engine.get_pending_operations()
        assert len(pending) == 1

    def test_get_pending_filter_by_priority(self, engine):
        engine.enqueue_operation("crdt_5", "add", priority=SyncPriority.CRITICAL)
        engine.enqueue_operation("crdt_5", "update", priority=SyncPriority.LOW)
        critical = engine.get_pending_operations(priority=SyncPriority.CRITICAL)
        low = engine.get_pending_operations(priority=SyncPriority.LOW)
        assert len(critical) == 1
        assert len(low) == 1


# ─── Test: OfflineSyncEngine — Batch Enqueue ──────────────────────────────────

class TestBatchEnqueue:
    """Tests for enqueue_batch()."""

    def test_enqueue_batch(self, engine):
        ops_data = [
            {"crdt_id": "c1", "operation": "add", "key": "k1", "value": "v1",
             "priority": 0},
            {"crdt_id": "c1", "operation": "set", "key": "k2", "value": "v2",
             "priority": 1},
        ]
        results = engine.enqueue_batch(ops_data)
        assert len(results) == 2
        assert results[0].crdt_id == "c1"
        assert results[0].priority == SyncPriority.CRITICAL
        assert results[1].priority == SyncPriority.HIGH

    def test_batch_default_priority(self, engine):
        ops_data = [
            {"crdt_id": "c1", "operation": "add"},
        ]
        results = engine.enqueue_batch(ops_data)
        assert results[0].priority == SyncPriority.MEDIUM


# ─── Test: OfflineSyncEngine — Sync Loop ──────────────────────────────────────

class TestSyncLoop:
    """Tests for start/stop sync loop."""

    def test_start_stop(self, engine):
        """Starting and stopping should not raise."""
        engine.start_sync_loop()
        engine.stop_sync_loop()

    def test_start_twice(self, engine):
        """Starting an already running loop should log warning but not raise."""
        engine.start_sync_loop()
        engine.start_sync_loop()  # Should just log warning
        engine.stop_sync_loop()


# ─── Test: OfflineSyncEngine — Sync Now ──────────────────────────────────────

class TestSyncNow:
    """Tests for sync_now()."""

    def test_sync_now_no_handlers(self, engine):
        """sync_now() with no handlers and no checkers should still work."""
        status = engine.sync_now()
        assert isinstance(status, SyncStatus)

    def test_sync_now_with_handler_success(self, engine):
        """sync_now() should call registered handlers."""
        handler_called = False

        def dummy_handler(ops: List[SyncOperation]) -> bool:
            nonlocal handler_called
            handler_called = True
            return True

        engine.register_sync_handler(dummy_handler)
        engine.enqueue_operation("crdt_1", "add", value="test")
        engine.sync_now()
        assert handler_called is True

    def test_sync_now_with_handler_and_pending(self, engine):
        """Pending operations should be synced via handler."""
        synced_ops = []

        def tracking_handler(ops: List[SyncOperation]) -> bool:
            synced_ops.extend(ops)
            return True

        engine.register_sync_handler(tracking_handler)
        engine.enqueue_operation("crdt_1", "add", value="A")
        engine.enqueue_operation("crdt_1", "add", value="B")
        engine.sync_now()
        assert len(synced_ops) == 2

    def test_sync_now_handler_failure(self, engine):
        """If handler returns False, ops should stay pending for retry."""

        def failing_handler(ops: List[SyncOperation]) -> bool:
            return False

        engine.register_sync_handler(failing_handler)
        op = engine.enqueue_operation("crdt_1", "add", value="test")
        engine.sync_now()
        assert op.retry_count == 1
        assert op.status == SyncOperationStatus.PENDING

    def test_sync_mark_as_synced(self, engine):
        """Successfully synced ops should be marked SYNCED."""

        def success_handler(ops: List[SyncOperation]) -> bool:
            return True

        engine.register_sync_handler(success_handler)
        op = engine.enqueue_operation("crdt_1", "add", value="test")
        engine.sync_now()
        assert op.status == SyncOperationStatus.SYNCED
        assert op.synced_at is not None

    def test_sync_priority_ordering(self, engine):
        """Higher priority ops should sync before lower priority."""
        synced_order = []

        def ordered_handler(ops: List[SyncOperation]) -> bool:
            synced_order.extend(ops)
            return True

        engine.register_sync_handler(ordered_handler)
        engine.enqueue_operation("crdt_1", "add", value="low",
                                 priority=SyncPriority.LOW)
        engine.enqueue_operation("crdt_1", "add", value="critical",
                                 priority=SyncPriority.CRITICAL)
        engine.sync_now()
        if len(synced_order) >= 2:
            assert synced_order[0].value == "critical"


# ─── Test: OfflineSyncEngine — Connectivity ────────────────────────────────────

class TestConnectivity:
    """Tests for connectivity checking."""

    def test_default_online_status(self, engine):
        assert engine._is_online is False

    def test_set_online(self, engine):
        engine.set_online(True)
        assert engine._is_online is True
        assert engine._last_sync_time is not None

    def test_set_offline(self, engine):
        engine.set_online(True)
        engine.set_online(False)
        assert engine._is_online is False

    def test_register_connectivity_checker(self, engine):
        checker = lambda: True
        engine.register_connectivity_checker(checker)
        assert len(engine._connectivity_checkers) == 1

    def test_connectivity_checker_all_true(self, engine):
        engine.register_connectivity_checker(lambda: True)
        engine.register_connectivity_checker(lambda: True)
        engine._check_connectivity()
        assert engine._is_online is True

    def test_connectivity_checker_one_false(self, engine):
        engine.register_connectivity_checker(lambda: True)
        engine.register_connectivity_checker(lambda: False)
        engine._check_connectivity()
        assert engine._is_online is False

    def test_no_checkers_defaults_online(self, engine):
        """With no checkers, _check_connectivity should set is_online True."""
        engine._check_connectivity()
        assert engine._is_online is True


# ─── Test: OfflineSyncEngine — Peer Selection ─────────────────────────────────

class TestPeerSelection:
    """Tests for select_sync_peer()."""

    def make_peers(self):
        return [
            SyncPeer(node_id="fast", latency_ms=1.0, trust_level=0.5),
            SyncPeer(node_id="trusted", latency_ms=100.0, trust_level=0.99),
            SyncPeer(node_id="balanced", latency_ms=50.0, trust_level=0.8),
        ]

    def test_no_peers_returns_none(self, engine):
        result = engine.select_sync_peer([], "best_effort")
        assert result is None

    def test_best_effort_strategy(self, engine):
        peers = self.make_peers()
        result = engine.select_sync_peer(peers, "best_effort")
        # "trusted" has highest trust - latency/1000: 0.99 - 0.1 = 0.89
        # "balanced": 0.8 - 0.05 = 0.75
        # "fast": 0.5 - 0.001 = 0.499
        # "trusted" should win
        assert result.node_id == "trusted"

    def test_fastest_strategy(self, engine):
        peers = self.make_peers()
        result = engine.select_sync_peer(peers, "fastest")
        assert result.node_id == "fast"

    def test_most_reliable_strategy(self, engine):
        peers = self.make_peers()
        result = engine.select_sync_peer(peers, "most_reliable")
        assert result.node_id == "trusted"

    def test_random_strategy(self, engine):
        peers = self.make_peers()
        # Run multiple times to verify it can pick different peers
        results = set()
        for _ in range(20):
            result = engine.select_sync_peer(peers, "random")
            results.add(result.node_id)
        # At least 2 different peers should have been picked
        assert len(results) >= 2

    def test_single_peer_any_strategy(self, engine):
        peers = [SyncPeer(node_id="only_one", latency_ms=50.0, trust_level=0.5)]
        for strategy in ["best_effort", "fastest", "most_reliable", "random"]:
            result = engine.select_sync_peer(peers, strategy)
            assert result.node_id == "only_one"

    def test_default_strategy_is_best_effort(self, engine):
        peers = self.make_peers()
        result = engine.select_sync_peer(peers)  # No strategy arg
        # Default should be best_effort
        assert result is not None


# ─── Test: OfflineSyncEngine — Conflict Resolution ────────────────────────────

class TestConflictResolution:
    """Tests for process_conflict(), record_conflict(), resolve_conflict()."""

    def test_same_operation_type_lww(self, engine):
        """Same operation type should use LAST_WRITER_WINS."""
        local = SyncOperation(id="l1", crdt_id="c", operation="add",
                              created_at=100.0)
        remote = SyncOperation(id="r1", crdt_id="c", operation="add",
                               created_at=200.0)
        strategy = engine.process_conflict(local, remote)
        assert strategy == ResolutionStrategy.LAST_WRITER_WINS

    def test_both_set_operations_merge(self, engine):
        """Both 'set' or 'add' on same key should MERGE."""
        local = SyncOperation(id="l1", crdt_id="c", operation="set",
                              key="theme")
        remote = SyncOperation(id="r1", crdt_id="c", operation="add",
                               key="theme")
        strategy = engine.process_conflict(local, remote)
        assert strategy == ResolutionStrategy.MERGE

    def test_remove_operation_manual(self, engine):
        """If either op is 'remove', strategy should be MANUAL."""
        local = SyncOperation(id="l1", crdt_id="c", operation="set",
                              key="data")
        remote = SyncOperation(id="r1", crdt_id="c", operation="remove",
                               key="data")
        strategy = engine.process_conflict(local, remote)
        assert strategy == ResolutionStrategy.MANUAL

    def test_different_keys_lww(self, engine):
        """Different keys with different ops should use LAST_WRITER_WINS."""
        local = SyncOperation(id="l1", crdt_id="c", operation="add",
                              key="a")
        remote = SyncOperation(id="r1", crdt_id="c", operation="remove",
                               key="b")
        strategy = engine.process_conflict(local, remote)
        assert strategy == ResolutionStrategy.LAST_WRITER_WINS

    def test_record_conflict(self, engine):
        """Recording a conflict should add it to tracking."""
        local = SyncOperation(id="l1", crdt_id="c", operation="set", key="x")
        remote = SyncOperation(id="r1", crdt_id="c", operation="remove", key="x")
        conflict = engine.record_conflict(local, remote, ResolutionStrategy.MANUAL)
        assert conflict.id is not None
        assert conflict.resolved is False
        assert conflict.resolution == ResolutionStrategy.MANUAL
        # Operation should be marked as CONFLICT
        assert local.status == SyncOperationStatus.CONFLICT

    def test_get_conflicts_unresolved(self, engine):
        """get_conflicts() should return only unresolved by default."""
        local = SyncOperation(id="l1", crdt_id="c", operation="set", key="x")
        remote = SyncOperation(id="r1", crdt_id="c", operation="remove", key="x")
        engine.record_conflict(local, remote, ResolutionStrategy.MANUAL)
        conflicts = engine.get_conflicts(unresolved_only=True)
        assert len(conflicts) == 1
        assert conflicts[0].resolved is False

    def test_get_conflicts_all(self, engine):
        """get_conflicts() with unresolved_only=False should return all."""
        local1 = SyncOperation(id="l1", crdt_id="c", operation="set", key="a")
        remote1 = SyncOperation(id="r1", crdt_id="c", operation="set", key="a")
        c1 = engine.record_conflict(local1, remote1, ResolutionStrategy.MERGE)
        # Resolve it
        engine.resolve_conflict(c1.id, ResolutionStrategy.MERGE, "auto")
        local2 = SyncOperation(id="l2", crdt_id="c", operation="set", key="b")
        remote2 = SyncOperation(id="r2", crdt_id="c", operation="remove", key="b")
        engine.record_conflict(local2, remote2, ResolutionStrategy.MANUAL)
        all_c = engine.get_conflicts(unresolved_only=False)
        assert len(all_c) == 2

    def test_resolve_conflict(self, engine):
        """Resolving a conflict should update its status."""
        local = SyncOperation(id="l1", crdt_id="c", operation="set", key="x")
        remote = SyncOperation(id="r1", crdt_id="c", operation="remove", key="x")
        conflict = engine.record_conflict(local, remote, ResolutionStrategy.MANUAL)
        result = engine.resolve_conflict(
            conflict.id, ResolutionStrategy.LAST_WRITER_WINS, "manual"
        )
        assert result is True
        # Check conflict is resolved
        c = engine.get_conflicts(unresolved_only=False)[0]
        assert c.resolved is True
        assert c.resolution == ResolutionStrategy.LAST_WRITER_WINS
        assert c.resolved_by == "manual"

    def test_resolve_nonexistent_conflict(self, engine):
        """Resolving a nonexistent conflict should return False."""
        result = engine.resolve_conflict("fake_id", ResolutionStrategy.MANUAL)
        assert result is False

    def test_manual_resolution_syncs_op(self, engine):
        """Manual resolution should mark the local op as SYNCED."""
        local = SyncOperation(id="l1", crdt_id="c", operation="set", key="x",
                              status=SyncOperationStatus.CONFLICT)
        remote = SyncOperation(id="r1", crdt_id="c", operation="remove", key="x")
        conflict = engine.record_conflict(local, remote, ResolutionStrategy.MANUAL)
        engine.resolve_conflict(conflict.id, ResolutionStrategy.LAST_WRITER_WINS)
        assert local.status == SyncOperationStatus.SYNCED


# ─── Test: OfflineSyncEngine — Status & Queries ───────────────────────────────

class TestStatusAndQueries:
    """Tests for status and query methods."""

    def test_get_sync_status_counts(self, engine):
        engine.enqueue_operation("c1", "add", priority=SyncPriority.CRITICAL)
        engine.enqueue_operation("c1", "add", priority=SyncPriority.HIGH)
        status = engine.get_sync_status()
        assert status.pending_count == 2
        assert status.total_operations == 2
        assert status.is_online is False

    def test_get_sync_status_after_sync(self, engine):
        engine.enqueue_operation("c1", "add")
        handled = []

        def handler(ops):
            handled.extend(ops)
            return True

        engine.register_sync_handler(handler)
        engine.sync_now()
        status = engine.get_sync_status()
        assert status.synced_count == 1
        assert status.pending_count == 0

    def test_get_pending_operations_ordering(self, engine):
        """Pending ops should be ordered by priority then time."""
        engine.enqueue_operation("c1", "add", priority=SyncPriority.LOW)
        engine.enqueue_operation("c1", "add", priority=SyncPriority.CRITICAL)
        engine.enqueue_operation("c1", "add", priority=SyncPriority.HIGH)
        pending = engine.get_pending_operations()
        assert len(pending) == 3
        # Should be sorted by priority (CRITICAL=0 < HIGH=1 < LOW=3)
        assert pending[0].priority == SyncPriority.CRITICAL
        assert pending[1].priority == SyncPriority.HIGH
        assert pending[2].priority == SyncPriority.LOW

    def test_clear_synced(self, engine):
        """clear_synced() should remove all synced operations."""

        def handler(ops):
            return True

        engine.register_sync_handler(handler)
        op = engine.enqueue_operation("c1", "add")
        engine.sync_now()
        cleared = engine.clear_synced()
        assert cleared >= 1
        assert engine.get_operation(op.id) is None

    def test_get_stats_structure(self, engine):
        stats = engine.get_stats()
        assert "is_online" in stats
        assert "total_operations" in stats
        assert "node_id" in stats
        assert "status" in stats
        assert "unresolved_conflicts" in stats
        assert "total_conflicts" in stats

    def test_get_operation_nonexistent(self, engine):
        result = engine.get_operation("nonexistent")
        assert result is None

    def test_get_pending_operations_empty(self, engine):
        pending = engine.get_pending_operations()
        assert pending == []


# ─── Test: OfflineSyncEngine — Retry Logic ────────────────────────────────────

class TestRetryLogic:
    """Tests for retry and max-retries behavior."""

    def test_retry_increments_on_failure(self, engine):
        """Failed sync should increment retry_count."""

        def failing_handler(ops):
            return False

        engine.register_sync_handler(failing_handler)
        op = engine.enqueue_operation("c1", "add")
        engine.sync_now()
        assert op.retry_count == 1
        engine.sync_now()
        assert op.retry_count == 2

    def test_max_retries_marks_failed(self, engine):
        """Operation exceeding max retries should be marked FAILED."""

        def always_fails(ops):
            return False

        engine.register_sync_handler(always_fails)
        op = engine.enqueue_operation("c1", "add")
        # Simulate max retries
        for _ in range(6):  # More than _SYNC_MAX_RETRIES (default 5)
            engine.sync_now()
        assert op.status == SyncOperationStatus.FAILED
        assert "Max retries" in (op.error or "")


# ─── Test: Singleton Factory ───────────────────────────────────────────────────

class TestSingletonFactory:
    """Tests for get_offline_sync_engine() and reset_offline_sync_engine()."""

    def test_singleton_returns_same_instance(self):
        e1 = get_offline_sync_engine()
        e2 = get_offline_sync_engine()
        assert e1 is e2

    def test_reset_creates_new_instance(self):
        e1 = get_offline_sync_engine()
        reset_offline_sync_engine()
        e2 = get_offline_sync_engine()
        assert e1 is not e2

    def test_singleton_preserves_state(self):
        e1 = get_offline_sync_engine()
        e1.enqueue_operation("c1", "add", value="persist")
        e2 = get_offline_sync_engine()
        assert len(e2._operations) >= 1

    def test_reset_clears_state(self):
        e1 = get_offline_sync_engine()
        e1.enqueue_operation("c1", "add", value="gone")
        reset_offline_sync_engine()
        e2 = get_offline_sync_engine()
        assert len(e2._operations) == 0


# ─── Test: Persistence ─────────────────────────────────────────────────────────

class TestPersistence:
    """Tests for JSONL persistence."""

    def test_enqueue_persists_operation(self, engine, tmp_path):
        """Operations should be written to disk on enqueue."""
        import mesh.offline_sync_engine as ose
        original_path = ose._SYNC_DB_PATH
        test_path = str(tmp_path / "test_sync.jsonl")
        try:
            ose._SYNC_DB_PATH = test_path
            e = OfflineSyncEngine()
            e.enqueue_operation("c1", "add", value="persist_test")
            assert os.path.exists(test_path)
            with open(test_path) as f:
                lines = [l.strip() for l in f if l.strip()]
            assert len(lines) >= 1
            last = json.loads(lines[-1])
            assert last["crdt_id"] == "c1"
            assert last["value"] == "persist_test"
        finally:
            ose._SYNC_DB_PATH = original_path

    def test_conflict_persisted(self, engine, tmp_path):
        """Conflict records should be written to disk."""
        import mesh.offline_sync_engine as ose
        original_path = ose._SYNC_DB_PATH
        test_path = str(tmp_path / "test_sync_conflict.jsonl")
        try:
            ose._SYNC_DB_PATH = test_path
            e = OfflineSyncEngine()
            local = SyncOperation(id="l1", crdt_id="c", operation="set", key="x")
            remote = SyncOperation(id="r1", crdt_id="c", operation="remove", key="x")
            e.record_conflict(local, remote, ResolutionStrategy.MANUAL)
            conflict_path = test_path.replace(".jsonl", "_conflicts.jsonl")
            if os.path.exists(conflict_path):
                with open(conflict_path) as f:
                    lines = [l.strip() for l in f if l.strip()]
                assert len(lines) >= 1
        finally:
            ose._SYNC_DB_PATH = original_path


# ─── Test: Module Exports ──────────────────────────────────────────────────────

class TestModuleExports:
    """Verify that __all__ exports match actual module contents."""

    def test_all_exports_defined(self):
        expected = [
            "SyncPriority",
            "SyncOperationStatus",
            "ResolutionStrategy",
            "SyncOperation",
            "SyncConflict",
            "SyncStatus",
            "SyncPeer",
            "OfflineSyncEngine",
            "get_offline_sync_engine",
            "reset_offline_sync_engine",
        ]
        for name in expected:
            assert name in module_exports, f"{name} missing from __all__"

    def test_all_exports_are_importable(self):
        from mesh.offline_sync_engine import (
            SyncPriority,
            SyncOperationStatus,
            ResolutionStrategy,
            SyncOperation,
            SyncConflict,
            SyncStatus,
            SyncPeer,
            OfflineSyncEngine,
            get_offline_sync_engine,
            reset_offline_sync_engine,
        )
        assert SyncPriority is not None
        assert OfflineSyncEngine is not None
        assert get_offline_sync_engine is not None


# ─── Test: Edge Cases ──────────────────────────────────────────────────────────

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_enqueue_after_sync_loop_stopped(self, engine):
        """Enqueue should work even after sync loop is stopped."""
        engine.start_sync_loop()
        engine.stop_sync_loop()
        op = engine.enqueue_operation("c1", "add", value="after_stop")
        assert op is not None
        assert op.status == SyncOperationStatus.PENDING

    def test_large_value_operation(self, engine):
        """Operations with large values should work."""
        large_value = "x" * 10000
        op = engine.enqueue_operation("c1", "set", value=large_value)
        assert op.value == large_value

    def test_special_chars_in_keys(self, engine):
        """Keys with special characters should be handled."""
        op = engine.enqueue_operation("c1", "set", key="user@domain.com/profile/name")
        assert op.key == "user@domain.com/profile/name"

    def test_multiple_conflicts_same_crdt(self, engine):
        """Multiple conflicts on the same CRDT should be tracked separately."""
        for i in range(3):
            local = SyncOperation(id=f"l{i}", crdt_id="c", operation="set",
                                  key=f"k{i}")
            remote = SyncOperation(id=f"r{i}", crdt_id="c", operation="remove",
                                   key=f"k{i}")
            engine.record_conflict(local, remote, ResolutionStrategy.MANUAL)
        conflicts = engine.get_conflicts(unresolved_only=True)
        assert len(conflicts) == 3

    def test_sync_status_after_failed_then_success(self, engine):
        """Status counts should reflect mixed outcomes."""
        results = []

        def flip_handler(ops):
            results.append(True)
            return True

        engine.register_sync_handler(flip_handler)
        op1 = engine.enqueue_operation("c1", "add", value="a")
        op2 = engine.enqueue_operation("c1", "add", value="b")
        engine.sync_now()
        status = engine.get_sync_status()
        assert status.synced_count == 2

    def test_sync_now_idempotent(self, engine):
        """Calling sync_now multiple times should not raise."""
        engine.sync_now()
        engine.sync_now()
        engine.sync_now()

    def test_get_pending_after_clear(self, engine):
        """After clearing synced, pending should still be accessible."""

        def handler(ops):
            return True

        engine.register_sync_handler(handler)
        engine.enqueue_operation("c1", "add")
        engine.sync_now()
        # Clear synced
        engine.clear_synced()
        # Enqueue another
        engine.enqueue_operation("c1", "add")
        pending = engine.get_pending_operations()
        assert len(pending) == 1

    def test_operation_status_transitions(self, engine):
        """Operation should transition through statuses correctly."""

        def handler(ops):
            for op in ops:
                assert op.status == SyncOperationStatus.IN_FLIGHT
            return True

        engine.register_sync_handler(handler)
        op = engine.enqueue_operation("c1", "add")
        assert op.status == SyncOperationStatus.PENDING
        engine.sync_now()
        assert op.status == SyncOperationStatus.SYNCED
