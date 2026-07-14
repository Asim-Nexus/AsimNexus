#!/usr/bin/env python3
"""
STATUS: NEW — Gap 7 Implementation
ASIMNEXUS Offline-First Sync Engine
====================================
Queue-based sync engine with CRDT-based conflict resolution.
Handles intermittent connectivity with priority-based sync ordering.

Extends existing mesh infrastructure:
  - [`mesh/crdt_sync.py`](crdt_sync.py) — CRDT types and store for conflict-free replication
  - [`mesh/node_registry.py`](node_registry.py) — Peer selection for sync
  - [`mesh/p2p_transport.py`](p2p_transport.py) — Transport for sync data transfer
  - [`mesh/multi_mesh_router.py`](multi_mesh_router.py) — Mesh-type aware sync routing
  - [`core/routing/hybrid_router.py`](../core/routing/hybrid_router.py) — Sync triggers mesh-type switching
"""

import os
import time
import json
import logging
import threading
import uuid
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime
from queue import PriorityQueue
from pathlib import Path

logger = logging.getLogger("AsimNexus.Mesh.OfflineSync")

# ─── Environment Configuration ────────────────────────────────────────────────
_SYNC_DB_PATH = os.getenv("ASIM_SYNC_DB_PATH", "data/offline_sync.jsonl")
_SYNC_INTERVAL_SEC = int(os.getenv("ASIM_SYNC_INTERVAL", "15"))
_SYNC_BATCH_SIZE = int(os.getenv("ASIM_SYNC_BATCH_SIZE", "50"))
_SYNC_MAX_RETRIES = int(os.getenv("ASIM_SYNC_MAX_RETRIES", "5"))
_SYNC_RETRY_BACKOFF_SEC = int(os.getenv("ASIM_SYNC_RETRY_BACKOFF", "30"))
# Test mode — reduces sync interval for faster test execution
_ASIM_TEST_MODE = os.getenv("ASIM_TEST_MODE", "0") == "1"
if _ASIM_TEST_MODE:
    _SYNC_INTERVAL_SEC = 1

# ─── Circuit Breaker Configuration ────────────────────────────────────────────
_CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("ASIM_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
_CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(os.getenv("ASIM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30"))
_CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS = int(os.getenv("ASIM_CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS", "3"))


class CircuitState(Enum):
    """Circuit Breaker state machine states (DDIA Chapter 4: Reliability)."""
    CLOSED = "CLOSED"          # Normal operation — requests pass through
    OPEN = "OPEN"              # Failure threshold exceeded — requests fail fast
    HALF_OPEN = "HALF_OPEN"    # Testing recovery — limited requests allowed


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.
    
    State machine: CLOSED → OPEN → HALF_OPEN → CLOSED (or back to OPEN)
    
    Prevents cascading failures by failing fast when a peer is down,
    and uses recovery timeout + probe requests to detect recovery.
    
    Reference: DDIA Chapter 4 (Reliability), Google SRE Book.
    """

    def __init__(self, name: str = "default",
                 failure_threshold: int = _CIRCUIT_BREAKER_FAILURE_THRESHOLD,
                 recovery_timeout: float = _CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
                 half_open_max_requests: int = _CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_requests = half_open_max_requests
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        self.half_open_requests = 0
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        """
        Check if execution is allowed based on current state.
        
        Returns:
            True if the operation can proceed, False to fail fast.
        """
        with self._lock:
            now = time.time()
            
            if self.state == CircuitState.CLOSED:
                return True
                
            elif self.state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if now - self.last_state_change > self.recovery_timeout:
                    self._change_state(CircuitState.HALF_OPEN)
                    self.half_open_requests = 0
                    logger.info(f"[CIRCUIT_BREAKER:{self.name}] OPEN → HALF_OPEN — probing recovery")
                    return True
                return False  # Fail fast
                
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited probe requests
                if self.half_open_requests < self.half_open_max_requests:
                    self.half_open_requests += 1
                    return True
                return False  # Too many probes in flight
                
        return True

    def record_success(self):
        """Record a successful execution."""
        with self._lock:
            self.failure_count = 0
            self.success_count += 1
            if self.state == CircuitState.HALF_OPEN:
                self._change_state(CircuitState.CLOSED)
                logger.info(f"[CIRCUIT_BREAKER:{self.name}] HALF_OPEN → CLOSED — recovery confirmed")

    def record_failure(self):
        """Record a failed execution."""
        with self._lock:
            self.failure_count += 1
            if self.state == CircuitState.HALF_OPEN:
                # Probe failed — back to OPEN
                self._change_state(CircuitState.OPEN)
                logger.warning(f"[CIRCUIT_BREAKER:{self.name}] HALF_OPEN → OPEN — probe failed")
            elif self.failure_count >= self.failure_threshold:
                self._change_state(CircuitState.OPEN)
                logger.warning(
                    f"[CIRCUIT_BREAKER:{self.name}] CLOSED → OPEN — "
                    f"{self.failure_count} consecutive failures"
                )

    def _change_state(self, new_state: CircuitState):
        """Transition to a new state."""
        self.state = new_state
        self.last_state_change = time.time()
        self.half_open_requests = 0

    def get_state(self) -> Dict[str, Any]:
        """Get current breaker state for monitoring."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "last_state_change": self.last_state_change,
                "seconds_in_current_state": time.time() - self.last_state_change,
            }


def calculate_exp_backoff(attempt: int, base_sec: float = 2.0, max_sec: float = 60.0) -> float:
    """
    Exponential backoff with jitter (DDIA Chapter 4).
    
    Formula: min(max_sec, base * 2^attempt) * (0.5 + random(0, 0.5))
    
    This prevents thundering herd problem when multiple clients
    retry simultaneously after a failure.
    """
    temp = min(max_sec, base_sec * (2 ** attempt))
    jitter = 0.5 + random.random() * 0.5  # 50-100% of the base value
    return temp * jitter


class SyncPriority(Enum):
    """Priority tiers for sync operations. Lower number = higher priority."""
    CRITICAL = 0    # Identity, contracts, consent — sync immediately
    HIGH = 1        # Recent messages, active task state
    MEDIUM = 2      # Chat history, memories
    LOW = 3         # Media files, old data


class SyncOperationStatus(Enum):
    """Status of a sync operation in the queue."""
    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"
    SKIPPED = "skipped"


class ResolutionStrategy(Enum):
    """Conflict resolution strategies."""
    LAST_WRITER_WINS = "last_writer_wins"   # Default CRDT strategy
    MANUAL = "manual"                        # Requires user intervention
    LOCAL_PREFERRED = "local_preferred"      # Local changes take precedence
    REMOTE_PREFERRED = "remote_preferred"    # Remote changes take precedence
    MERGE = "merge"                          # Merge both (for compatible ops)


@dataclass
class SyncOperation:
    """
    A single sync operation in the queue.

    Attributes:
        id: Unique operation ID.
        crdt_id: The CRDT document/object being modified.
        operation: Type of operation ("add", "remove", "set", etc.).
        key: Optional key within the CRDT.
        value: Optional value for the operation.
        priority: Sync priority (CRITICAL=0, HIGH=1, MEDIUM=2, LOW=3).
        status: Current status of the operation.
        created_at: Timestamp when operation was queued.
        synced_at: Timestamp when operation was successfully synced.
        retry_count: Number of sync attempts.
        node_id: The node that created this operation.
        error: Last error message, if any.
    """
    id: str
    crdt_id: str
    operation: str
    key: Optional[str] = None
    value: Optional[Any] = None
    priority: SyncPriority = SyncPriority.MEDIUM
    status: SyncOperationStatus = SyncOperationStatus.PENDING
    created_at: float = field(default_factory=time.time)
    synced_at: Optional[float] = None
    retry_count: int = 0
    node_id: Optional[str] = None
    error: Optional[str] = None

    def __lt__(self, other: "SyncOperation") -> bool:
        """For PriorityQueue ordering: lower priority number = higher priority."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "crdt_id": self.crdt_id,
            "operation": self.operation,
            "key": self.key,
            "value": self.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "synced_at": self.synced_at,
            "retry_count": self.retry_count,
            "node_id": self.node_id,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncOperation":
        data = dict(data)
        if "priority" in data and isinstance(data["priority"], int):
            data["priority"] = SyncPriority(data["priority"])
        if "status" in data and isinstance(data["status"], str):
            data["status"] = SyncOperationStatus(data["status"])
        return cls(**data)


@dataclass
class SyncConflict:
    """
    Record of a sync conflict requiring attention.

    Attributes:
        id: Unique conflict ID.
        crdt_id: The CRDT document with the conflict.
        local_operation: The local operation.
        remote_operation: The remote operation (from peer).
        resolution: The chosen resolution strategy.
        resolved: Whether the conflict has been resolved.
        resolved_at: When the conflict was resolved.
        resolved_by: "auto", "manual", or node ID.
    """
    id: str
    crdt_id: str
    local_operation: SyncOperation
    remote_operation: SyncOperation
    resolution: ResolutionStrategy = ResolutionStrategy.LAST_WRITER_WINS
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolved_by: str = "auto"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "crdt_id": self.crdt_id,
            "local_operation": self.local_operation.to_dict(),
            "remote_operation": self.remote_operation.to_dict(),
            "resolution": self.resolution.value,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at,
        }


@dataclass
class SyncStatus:
    """
    Current sync status report.

    Attributes:
        pending_count: Operations waiting to be synced.
        in_flight_count: Operations currently being synced.
        synced_count: Operations successfully synced.
        failed_count: Operations that failed.
        conflict_count: Operations with conflicts.
        last_sync_time: Timestamp of last successful sync.
        is_online: Whether connectivity is currently available.
        total_operations: Total operations tracked.
    """
    pending_count: int = 0
    in_flight_count: int = 0
    synced_count: int = 0
    failed_count: int = 0
    conflict_count: int = 0
    last_sync_time: Optional[float] = None
    is_online: bool = False
    total_operations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pending_count": self.pending_count,
            "in_flight_count": self.in_flight_count,
            "synced_count": self.synced_count,
            "failed_count": self.failed_count,
            "conflict_count": self.conflict_count,
            "last_sync_time": self.last_sync_time,
            "is_online": self.is_online,
            "total_operations": self.total_operations,
        }


# ─── Peer Info (lightweight, avoids circular import with node_registry) ───────

@dataclass
class SyncPeer:
    """
    Represents a peer available for sync.

    Attributes:
        node_id: Unique peer identifier.
        hostname: Peer hostname or IP.
        port: Connection port.
        trust_level: Trust score 0.0–1.0.
        latency_ms: Observed latency.
        last_seen: Last successful contact timestamp.
        version: Peer's sync protocol version.
    """
    node_id: str
    hostname: str = "localhost"
    port: int = 0
    trust_level: float = 0.5
    latency_ms: float = 100.0
    last_seen: Optional[float] = None
    version: str = "1.0.0"


class OfflineSyncEngine:
    """
    Offline-first sync engine with CRDT-based conflict resolution.

    Handles intermittent connectivity with queue-based sync.
    Operations are queued locally and synced in priority order when
    connectivity is restored.

    Key methods:
        [`enqueue_operation()`](:280) — queue an operation (works offline)
        [`sync_loop()`](:310) — background sync loop
        [`sync_now()`](:370) — trigger immediate sync
        [`get_sync_status()`](:400) — current sync health
        [`select_sync_peer()`](:420) — best peer selection
        [`process_conflict()`](:470) — conflict resolution
        [`get_conflicts()`](:530) — pending conflicts
        [`resolve_conflict()`](:550) — manual conflict resolution
    """

    def __init__(self, crdt_store: Any = None):
        self._lock = threading.RLock()
        self._crdt_store = crdt_store  # CRDTStore instance from crdt_sync.py
        self._queue: "PriorityQueue[SyncOperation]" = PriorityQueue()
        self._operations: Dict[str, SyncOperation] = {}  # All tracked ops
        self._conflicts: Dict[str, SyncConflict] = {}
        self._is_online: bool = False
        self._last_sync_time: Optional[float] = None
        self._connectivity_checkers: List[Callable[[], bool]] = []
        self._sync_handlers: List[Callable[[List[SyncOperation]], bool]] = []
        self._sync_thread: Optional[threading.Thread] = None
        self._stop_sync: threading.Event = threading.Event()
        self._node_id: str = os.getenv("ASIM_NODE_ID", f"node_{uuid.uuid4().hex[:8]}")
        self._synced_ids: Set[str] = set()

        # ─── Circuit Breaker (DDIA Chapter 4: Reliability) ────────────────────
        # Prevents cascading failures by failing fast when sync failures
        # exceed threshold. State machine: CLOSED → OPEN → HALF_OPEN → CLOSED
        self._circuit_breaker = CircuitBreaker(
            name=f"sync-{self._node_id}",
            failure_threshold=_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=_CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
            half_open_max_requests=_CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS,
        )

        # Load any persisted operations from disk
        self._load_from_db()
        logger.info(
            f"📡 OfflineSyncEngine initialized — node={self._node_id}, "
            f"pending={self._count_by_status(SyncOperationStatus.PENDING)}, "
            f"circuit_breaker={self._circuit_breaker.state.value}"
        )

    # ─── Core API ────────────────────────────────────────────────────────────

    def enqueue_operation(self, crdt_id: str, operation: str,
                          key: Optional[str] = None,
                          value: Optional[Any] = None,
                          priority: SyncPriority = SyncPriority.MEDIUM) -> SyncOperation:
        """
        Queue an operation for sync. Works offline — the operation is stored
        locally and synced when connectivity is restored.

        Args:
            crdt_id: The CRDT document/object to modify.
            operation: Operation type ("add", "remove", "set", etc.).
            key: Optional key within the CRDT.
            value: Optional value to set.
            priority: Sync priority.

        Returns:
            The created SyncOperation.
        """
        op = SyncOperation(
            id=str(uuid.uuid4()),
            crdt_id=crdt_id,
            operation=operation,
            key=key,
            value=value,
            priority=priority,
            node_id=self._node_id,
        )
        with self._lock:
            self._operations[op.id] = op
            self._queue.put(op)
            self._persist_operation(op)

        logger.debug(
            f"📥 Enqueued [{op.id[:8]}] {crdt_id}.{operation} "
            f"(priority={priority.name}, offline={not self._is_online})"
        )
        return op

    def enqueue_batch(self, operations: List[Dict[str, Any]]) -> List[SyncOperation]:
        """
        Queue multiple operations at once.

        Args:
            operations: List of dicts with keys: crdt_id, operation, key, value, priority.

        Returns:
            List of created SyncOperations.
        """
        results = []
        for op_data in operations:
            op = self.enqueue_operation(
                crdt_id=op_data["crdt_id"],
                operation=op_data["operation"],
                key=op_data.get("key"),
                value=op_data.get("value"),
                priority=SyncPriority(op_data.get("priority", SyncPriority.MEDIUM.value)),
            )
            results.append(op)
        return results

    def start_sync_loop(self) -> None:
        """
        Start the background sync loop.

        Runs in a daemon thread, checking connectivity and syncing at
        [`_SYNC_INTERVAL_SEC`](:26) intervals.
        """
        if self._sync_thread and self._sync_thread.is_alive():
            logger.warning("Sync loop already running")
            return

        self._stop_sync.clear()
        self._sync_thread = threading.Thread(
            target=self._sync_loop,
            daemon=True,
            name="offline-sync",
        )
        self._sync_thread.start()
        logger.info("▶️ Sync loop started")

    def stop_sync_loop(self) -> None:
        """Stop the background sync loop."""
        self._stop_sync.set()
        if self._sync_thread:
            self._sync_thread.join(timeout=5)
        logger.info("⏹️ Sync loop stopped")

    def _sync_loop(self) -> None:
        """Background loop: check connectivity, sync pending operations."""
        while not self._stop_sync.is_set():
            try:
                self._check_connectivity()
                if self._is_online:
                    self._process_pending()
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
            self._stop_sync.wait(_SYNC_INTERVAL_SEC)

    def sync_now(self) -> SyncStatus:
        """
        Trigger an immediate sync attempt.

        Returns:
            Current SyncStatus after the sync attempt.
        """
        self._check_connectivity()
        if self._is_online:
            self._process_pending()
        return self.get_sync_status()

    # ─── Connectivity ────────────────────────────────────────────────────────

    def register_connectivity_checker(self, checker: Callable[[], bool]) -> None:
        """
        Register a function that returns True when the network is reachable.

        Multiple checkers can be registered; ALL must return True for
        is_online to be True.
        """
        with self._lock:
            self._connectivity_checkers.append(checker)

    def register_sync_handler(self, handler: Callable[[List[SyncOperation]], bool]) -> None:
        """
        Register a handler that sends a batch of operations to a peer.

        The handler receives a list of SyncOperation objects to sync.
        It should return True if all were successfully sent.
        """
        with self._lock:
            self._sync_handlers.append(handler)

    def set_online(self, online: bool) -> None:
        """Manually set online/offline status (for testing)."""
        with self._lock:
            self._is_online = online
            if online:
                self._last_sync_time = time.time()

    def _check_connectivity(self) -> None:
        """Run registered connectivity checkers."""
        with self._lock:
            if not self._connectivity_checkers:
                # Default: assume we're online if we have handlers registered
                self._is_online = True
                return

            all_connected = all(
                checker() for checker in self._connectivity_checkers
            )
            was_offline = not self._is_online
            self._is_online = all_connected

            if was_offline and self._is_online:
                logger.info("🔗 Connectivity restored — resuming sync")
            elif not was_offline and not self._is_online:
                logger.info("🔌 Connectivity lost — queuing operations")

    # ─── Sync Processing ─────────────────────────────────────────────────────

    def _process_pending(self) -> None:
        """
        Process pending operations in priority order.

        Uses Circuit Breaker (DDIA Chapter 4) to prevent cascading failures.
        Uses exponential backoff with jitter for retry timing.

        Batches operations by priority and sends them via registered handlers.
        """
        # ─── Circuit Breaker Check ────────────────────────────────────────────
        # Fail fast if circuit is OPEN — prevents cascading failures
        if not self._circuit_breaker.can_execute():
            logger.warning(
                f"⛔ Circuit breaker OPEN — failing fast. "
                f"State: {self._circuit_breaker.state.value}"
            )
            return

        with self._lock:
            if not self._sync_handlers:
                logger.debug("No sync handlers registered — skipping sync")
                return

            # Collect pending operations up to batch size
            batch: List[SyncOperation] = []
            temp_queue: "PriorityQueue[SyncOperation]" = PriorityQueue()

            while not self._queue.empty() and len(batch) < _SYNC_BATCH_SIZE:
                op = self._queue.get_nowait()
                if op.status == SyncOperationStatus.SYNCED:
                    continue
                if op.id in self._synced_ids:
                    continue
                if op.retry_count >= _SYNC_MAX_RETRIES:
                    op.status = SyncOperationStatus.FAILED
                    op.error = f"Max retries ({_SYNC_MAX_RETRIES}) exceeded"
                    self._persist_operation(op)
                    continue

                # ─── Exponential Backoff Check ────────────────────────────────
                # Skip operations that haven't waited long enough for retry
                if op.retry_count > 0:
                    backoff_sec = calculate_exp_backoff(op.retry_count - 1)
                    elapsed = time.time() - (op.synced_at or op.created_at)
                    if elapsed < backoff_sec:
                        # Not yet time to retry — put back in queue
                        temp_queue.put(op)
                        continue

                op.status = SyncOperationStatus.IN_FLIGHT
                batch.append(op)
                # NOTE: Do NOT put batch ops on temp_queue — they will be
                # re-added only if the handler fails (see below). This
                # prevents duplicate queue entries on retry.

            # Put remaining (non-batch) ops back into the queue
            while not self._queue.empty():
                temp_queue.put(self._queue.get_nowait())
            self._queue = temp_queue

        if not batch:
            return

        # Send batch through registered handlers (outside lock)
        success = False
        for handler in self._sync_handlers:
            try:
                if handler(batch):
                    success = True
                    break
            except Exception as e:
                logger.error(f"Sync handler error: {e}")

        # Update status based on result
        with self._lock:
            now = time.time()
            for op in batch:
                if success:
                    op.status = SyncOperationStatus.SYNCED
                    op.synced_at = now
                    self._synced_ids.add(op.id)
                    # Record success in circuit breaker
                    self._circuit_breaker.record_success()
                else:
                    op.retry_count += 1
                    op.status = SyncOperationStatus.PENDING
                    backoff = calculate_exp_backoff(op.retry_count - 1)
                    op.error = (
                        f"Sync failed (attempt {op.retry_count}, "
                        f"next retry in {backoff:.1f}s)"
                    )
                    # Record failure in circuit breaker
                    self._circuit_breaker.record_failure()
                    # Put back in queue for retry
                    self._queue.put(op)

                self._persist_operation(op)

            if success:
                self._last_sync_time = now
                logger.info(
                    f"✅ Synced {len(batch)} operations — "
                    f"pending={self._count_by_status(SyncOperationStatus.PENDING)}, "
                    f"synced={self._count_by_status(SyncOperationStatus.SYNCED)}, "
                    f"circuit={self._circuit_breaker.state.value}"
                )

    # ─── Peer Selection ──────────────────────────────────────────────────────

    def select_sync_peer(self, available_peers: List[SyncPeer],
                         strategy: str = "best_effort") -> Optional[SyncPeer]:
        """
        Select the best peer for sync.

        Strategies:
            - "best_effort": highest trust + lowest latency
            - "fastest": lowest latency only
            - "most_reliable": highest trust only
            - "random": random selection

        Args:
            available_peers: List of peers to choose from.
            strategy: Selection strategy.

        Returns:
            The selected SyncPeer, or None if no peers available.
        """
        if not available_peers:
            return None

        if strategy == "random":
            import random
            return random.choice(available_peers)

        if strategy == "fastest":
            return min(available_peers, key=lambda p: p.latency_ms)

        if strategy == "most_reliable":
            return max(available_peers, key=lambda p: p.trust_level)

        # Default: best_effort — combined score: trust - (latency / 1000)
        def score(peer: SyncPeer) -> float:
            return peer.trust_level - (peer.latency_ms / 1000.0)

        return max(available_peers, key=score)

    # ─── Conflict Resolution ─────────────────────────────────────────────────

    def process_conflict(self, local_op: SyncOperation,
                         remote_op: SyncOperation) -> ResolutionStrategy:
        """
        Resolve a conflict between local and remote operations.

        CRDTs auto-resolve most conflicts mathematically. This method
        handles edge cases that need strategy selection.

        Args:
            local_op: The local operation.
            remote_op: The remote operation (from peer).

        Returns:
            The appropriate ResolutionStrategy.
        """
        # Same operation type — CRDT handles it
        if local_op.operation == remote_op.operation:
            return ResolutionStrategy.LAST_WRITER_WINS

        # Different operations on the same key — merge or manual
        if local_op.key == remote_op.key:
            if local_op.operation in ("add", "set") and remote_op.operation in ("add", "set"):
                return ResolutionStrategy.MERGE
            if local_op.operation == "remove" or remote_op.operation == "remove":
                return ResolutionStrategy.MANUAL

        # Default: last writer wins (CRDT safe)
        return ResolutionStrategy.LAST_WRITER_WINS

    def record_conflict(self, local_op: SyncOperation,
                        remote_op: SyncOperation,
                        resolution: ResolutionStrategy) -> SyncConflict:
        """Record a sync conflict for tracking and potential manual resolution."""
        conflict = SyncConflict(
            id=str(uuid.uuid4()),
            crdt_id=local_op.crdt_id,
            local_operation=local_op,
            remote_operation=remote_op,
            resolution=resolution,
        )

        with self._lock:
            self._conflicts[conflict.id] = conflict
            local_op.status = SyncOperationStatus.CONFLICT
            self._persist_operation(local_op)
            self._persist_conflict(conflict)

        logger.warning(
            f"⚔️ Conflict detected [{conflict.id[:8]}] {local_op.crdt_id}: "
            f"resolution={resolution.value}"
        )
        return conflict

    def resolve_conflict(self, conflict_id: str,
                         resolution: ResolutionStrategy,
                         resolved_by: str = "manual") -> bool:
        """
        Manually resolve a sync conflict.

        Args:
            conflict_id: The conflict to resolve.
            resolution: Chosen resolution strategy.
            resolved_by: Who resolved it ("manual", "auto", or node ID).

        Returns:
            True if conflict was found and resolved.
        """
        with self._lock:
            conflict = self._conflicts.get(conflict_id)
            if not conflict:
                return False

            conflict.resolution = resolution
            conflict.resolved = True
            conflict.resolved_at = time.time()
            conflict.resolved_by = resolved_by

            # Update the local operation status
            conflict.local_operation.status = SyncOperationStatus.SYNCED
            self._persist_operation(conflict.local_operation)
            self._persist_conflict(conflict)

            logger.info(
                f"✅ Conflict resolved [{conflict_id[:8]}] "
                f"resolution={resolution.value} by {resolved_by}"
            )
            return True

    def get_conflicts(self, unresolved_only: bool = True) -> List[SyncConflict]:
        """Get all tracked conflicts, optionally filtered to unresolved only."""
        with self._lock:
            conflicts = list(self._conflicts.values())
            if unresolved_only:
                conflicts = [c for c in conflicts if not c.resolved]
            return conflicts

    # ─── Status & Queries ────────────────────────────────────────────────────

    def get_sync_status(self) -> SyncStatus:
        """Get current sync status report."""
        with self._lock:
            pending = self._count_by_status(SyncOperationStatus.PENDING)
            in_flight = self._count_by_status(SyncOperationStatus.IN_FLIGHT)
            synced = self._count_by_status(SyncOperationStatus.SYNCED)
            failed = self._count_by_status(SyncOperationStatus.FAILED)
            conflict = self._count_by_status(SyncOperationStatus.CONFLICT)
            unresolved_conflicts = sum(
                1 for c in self._conflicts.values() if not c.resolved
            )

            return SyncStatus(
                pending_count=pending,
                in_flight_count=in_flight,
                synced_count=synced,
                failed_count=failed,
                conflict_count=conflict + unresolved_conflicts,
                last_sync_time=self._last_sync_time,
                is_online=self._is_online,
                total_operations=len(self._operations),
            )

    def get_pending_operations(self, priority: Optional[SyncPriority] = None) -> List[SyncOperation]:
        """Get pending operations, optionally filtered by priority."""
        with self._lock:
            ops = [
                op for op in self._operations.values()
                if op.status == SyncOperationStatus.PENDING
            ]
            if priority:
                ops = [op for op in ops if op.priority == priority]
            return sorted(ops, key=lambda o: (o.priority.value, o.created_at))

    def get_operation(self, op_id: str) -> Optional[SyncOperation]:
        """Get a specific operation by ID."""
        with self._lock:
            return self._operations.get(op_id)

    def clear_synced(self) -> int:
        """Remove all successfully synced operations from tracking. Returns count."""
        with self._lock:
            synced_ids = [
                op_id for op_id, op in self._operations.items()
                if op.status == SyncOperationStatus.SYNCED
            ]
            for op_id in synced_ids:
                del self._operations[op_id]
            self._synced_ids.clear()
            return len(synced_ids)

    def get_circuit_breaker_state(self) -> Dict[str, Any]:
        """Get circuit breaker state for monitoring (DDIA Chapter 4)."""
        return self._circuit_breaker.get_state()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive sync engine statistics."""
        with self._lock:
            return {
                "is_online": self._is_online,
                "last_sync_time": self._last_sync_time,
                "total_operations": len(self._operations),
                "node_id": self._node_id,
                "connectivity_checkers": len(self._connectivity_checkers),
                "sync_handlers": len(self._sync_handlers),
                "unresolved_conflicts": sum(
                    1 for c in self._conflicts.values() if not c.resolved
                ),
                "total_conflicts": len(self._conflicts),
                "status": self.get_sync_status().to_dict(),
                "circuit_breaker": self._circuit_breaker.get_state(),
            }

    # ─── Internal Helpers ────────────────────────────────────────────────────

    def _count_by_status(self, status: SyncOperationStatus) -> int:
        return sum(
            1 for op in self._operations.values() if op.status == status
        )

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _persist_operation(self, op: SyncOperation) -> None:
        """Append operation state to JSONL audit trail."""
        try:
            os.makedirs(os.path.dirname(_SYNC_DB_PATH), exist_ok=True)
            with open(_SYNC_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(op.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist sync operation: {e}")

    def _persist_conflict(self, conflict: SyncConflict) -> None:
        """Append conflict record to JSONL audit trail."""
        try:
            conflict_path = _SYNC_DB_PATH.replace(".jsonl", "_conflicts.jsonl")
            os.makedirs(os.path.dirname(conflict_path), exist_ok=True)
            with open(conflict_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(conflict.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist sync conflict: {e}")

    def _load_from_db(self) -> None:
        """Load operations from persistent storage on startup."""
        try:
            path = Path(_SYNC_DB_PATH)
            if not path.exists():
                return

            latest_ops: Dict[str, SyncOperation] = {}
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        op = SyncOperation.from_dict(data)
                        # Keep the latest state for each operation
                        latest_ops[op.id] = op
                    except (json.JSONDecodeError, KeyError):
                        continue

            # Re-populate in-memory state
            for op_id, op in latest_ops.items():
                self._operations[op_id] = op
                if op.status == SyncOperationStatus.SYNCED:
                    self._synced_ids.add(op_id)
                elif op.status == SyncOperationStatus.PENDING:
                    self._queue.put(op)

            logger.info(
                f"📂 Loaded {len(latest_ops)} sync operations from DB "
                f"({self._count_by_status(SyncOperationStatus.PENDING)} pending)"
            )
        except Exception as e:
            logger.warning(f"Failed to load sync operations from DB: {e}")

        # Load conflicts
        try:
            conflict_path = Path(_SYNC_DB_PATH.replace(".jsonl", "_conflicts.jsonl"))
            if conflict_path.exists():
                with open(conflict_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            conflict = SyncConflict(
                                id=data["id"],
                                crdt_id=data["crdt_id"],
                                local_operation=SyncOperation.from_dict(data["local_operation"]),
                                remote_operation=SyncOperation.from_dict(data["remote_operation"]),
                                resolution=ResolutionStrategy(data.get("resolution", "last_writer_wins")),
                                resolved=data.get("resolved", False),
                                resolved_at=data.get("resolved_at"),
                                resolved_by=data.get("resolved_by", "auto"),
                                created_at=data.get("created_at", time.time()),
                            )
                            self._conflicts[conflict.id] = conflict
                        except (json.JSONDecodeError, KeyError) as e:
                            continue
        except Exception as e:
            logger.warning(f"Failed to load sync conflicts: {e}")


# ─── Singleton Factory ────────────────────────────────────────────────────────

_offline_sync_engine_instance: Optional[OfflineSyncEngine] = None
_offline_sync_engine_lock = threading.Lock()


def get_offline_sync_engine(crdt_store: Any = None) -> OfflineSyncEngine:
    """
    Get or create the singleton OfflineSyncEngine instance.

    Args:
        crdt_store: Optional CRDTStore instance. Only used on first creation.

    Usage:
        ```python
        engine = get_offline_sync_engine()
        op = engine.enqueue_operation("chat_msg_001", "add", ...)
        status = engine.sync_now()
        ```
    """
    global _offline_sync_engine_instance
    if _offline_sync_engine_instance is None:
        with _offline_sync_engine_lock:
            if _offline_sync_engine_instance is None:
                _offline_sync_engine_instance = OfflineSyncEngine(crdt_store=crdt_store)
    return _offline_sync_engine_instance


def reset_offline_sync_engine() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _offline_sync_engine_instance
    with _offline_sync_engine_lock:
        if _offline_sync_engine_instance:
            _offline_sync_engine_instance.stop_sync_loop()
        _offline_sync_engine_instance = None
    # Remove persisted DB so a fresh singleton starts clean
    try:
        from pathlib import Path
        p = Path(_SYNC_DB_PATH)
        if p.exists():
            p.unlink()
        conflict_path = Path(_SYNC_DB_PATH.replace(".jsonl", "_conflicts.jsonl"))
        if conflict_path.exists():
            conflict_path.unlink()
    except Exception:
        pass


# ─── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
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
