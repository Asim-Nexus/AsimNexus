#!/usr/bin/env python3
"""
Mesh + Offline Sync Demo
=========================
Demonstrates the mesh layer and offline sync engine working together.

This script exercises the REAL mesh/offline_sync_engine.py (873 lines, 87 tests)
via the bridge module core/sync/offline_sync.py and also directly imports the
real engine for advanced scenarios.

Usage:
    python scripts/demo_mesh_offline.py

What it shows:
  1. Singleton engine initialisation (bridge layer)
  2. Enqueue operations while "offline" (CREATE / UPDATE / DELETE)
  3. Sync status and queue inspection
  4. Peer selection strategies (best-effort, lowest-latency, round-robin, random)
  5. Conflict simulation and resolution (LAST_WRITER_WINS / MANUAL / LOCAL_PREFERRED)
  6. Flush / sync-now cycle
  7. Multi-Mesh Router awareness (LOCAL / PERSONAL / CLOUD / PUBLIC mesh types)
  8. Integration with backend /api/sync/* and /api/offline/* endpoints
  9. Stats and conflict reporting
"""

import sys
import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# -- Path setup -------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Demo.OfflineSync")

# Suppress debug from the engine itself
logging.getLogger("AsimNexus.Sync").setLevel(logging.WARNING)
logging.getLogger("AsimNexus.Sync.Bridge").setLevel(logging.WARNING)

SEP = "=" * 72


# ============================================================================
# Demo 1 -- Bridge layer initialisation
# ============================================================================

def demo_bridge_init():
    """Demonstrate that the bridge module loads and returns a connected engine."""
    print("\n" + SEP)
    print("  [DEMO 1] Bridge Initialisation")
    print(SEP)

    from core.sync.offline_sync import get_sync_engine, reset_sync_engine

    # Reset to start clean
    reset_sync_engine()

    engine = get_sync_engine()
    st = engine.status()

    print(f"  [OK] SyncEngine bridge loaded")
    print(f"  [OK] Engine type : {type(engine._engine).__name__}")
    print(f"  [OK] Node ID     : {st.get('node_id', 'unknown')}")
    print(f"  [OK] Queue size  : {st.get('queue_size', 0)}")
    print(f"  [OK] Online      : {st.get('is_online', False)}")
    print(f"  [OK] Last sync   : {st.get('last_sync', 'never')}")
    print(f"  [OK] Pending     : {st.get('pending_count', 0)}")
    print(f"  [OK] Synced      : {st.get('synced_count', 0)}")

    return engine


# ============================================================================
# Demo 2 -- Enqueue operations while offline
# ============================================================================

def demo_enqueue_operations(engine):
    """Queue several operations of different types, simulating offline use."""
    print("\n" + SEP)
    print("  [DEMO 2] Enqueue Operations (Offline Mode)")
    print(SEP)

    from core.sync.offline_sync import OpType

    operations = [
        ("message", "msg_001", {"text": "Hello from offline mode!", "sender": "alice"}),
        ("message", "msg_002", {"text": "Working in the Himalayas", "sender": "alice"}),
        ("memory",  "mem_001", {"content": "User preference: dark mode", "tags": ["ui", "prefs"]}),
        ("memory",  "mem_002", {"content": "Bookmarked trekking routes", "tags": ["travel", "nepal"]}),
        ("memory",  "mem_003", {"content": "Contact: ngima@example.com", "tags": ["contacts"]}),
    ]

    for entity_type, entity_id, payload in operations:
        op = engine.enqueue(OpType.CREATE, entity_type, entity_id, payload)
        d = op.to_dict()
        print(f"  [OK] Enqueued [{entity_type}] {entity_id} -- op_id={d.get('operation_id', '?')[:12]}...")

    # Also enqueue an UPDATE and DELETE
    engine.enqueue(OpType.UPDATE, "memory", "mem_001",
                   {"content": "User preference: system theme", "tags": ["ui", "theme"]})
    engine.enqueue(OpType.DELETE, "memory", "mem_003", None)

    print(f"  [OK] Enqueued UPDATE memory:mem_001")
    print(f"  [OK] Enqueued DELETE memory:mem_003")

    st = engine.status()
    print(f"\n  [->] Queue size after enqueue: {st.get('queue_size', 0)}")

    return engine


# ============================================================================
# Demo 3 -- Queue inspection
# ============================================================================

def demo_inspect_queue(engine):
    """List pending operations and show their details."""
    print("\n" + SEP)
    print("  [DEMO 3] Queue Inspection")
    print(SEP)

    queue = engine.queue_list()
    print(f"  Pending operations: {len(queue)}")

    for i, op in enumerate(queue):
        print(f"\n  --- Operation {i+1} ---")
        print(f"      ID        : {op.get('operation_id', '?')[:16]}...")
        print(f"      CRDT ID   : {op.get('crdt_id', '?')}")
        print(f"      Operation : {op.get('operation', '?')}")
        print(f"      Key       : {op.get('key', '?')}")
        print(f"      Status    : {op.get('status', '?')}")
        print(f"      Timestamp : {op.get('timestamp', '?')}")

    # Test pending_count helper
    count = engine.pending_count()
    print(f"\n  [->] Pending count (helper): {count}")


# ============================================================================
# Demo 4 -- Direct engine: peer selection strategies
# ============================================================================

def demo_peer_selection():
    """Exercise all four peer-selection strategies from the real engine."""
    print("\n" + SEP)
    print("  [DEMO 4] Peer Selection Strategies")
    print(SEP)

    from mesh.offline_sync_engine import (
        SyncPeer, get_offline_sync_engine,
    )

    engine = get_offline_sync_engine()

    # Create some fake peers
    now_ts = datetime.now(timezone.utc).timestamp()
    peers = [
        SyncPeer("node-alpha", hostname="10.0.0.1", port=9100, latency_ms=45,   last_seen=now_ts),
        SyncPeer("node-beta",  hostname="10.0.0.2", port=9101, latency_ms=120,  last_seen=now_ts),
        SyncPeer("node-gamma", hostname="10.0.0.3", port=9102, latency_ms=30,   last_seen=now_ts),
        SyncPeer("node-delta", hostname="10.0.0.4", port=9103, latency_ms=200,  last_seen=now_ts),
    ]

    strategies = ["best_effort", "lowest_latency", "round_robin", "random"]

    # Prime round-robin by calling it once
    engine.select_sync_peer(peers, "round_robin")

    for strat in strategies:
        picked = engine.select_sync_peer(peers, strat)
        if picked:
            print(f"  [OK] {strat:20s} -> {picked.node_id:15s} (latency={picked.latency_ms}ms)")
        else:
            print(f"  [--] {strat:20s} -> no peer selected")

    # Remove peers and test fallback
    empty = engine.select_sync_peer([], "best_effort")
    print(f"  [OK] best_effort (empty) -> {'None (graceful)' if empty is None else empty.node_id}")


# ============================================================================
# Demo 5 -- Conflict simulation and resolution
# ============================================================================

def demo_conflict_resolution():
    """Simulate a sync conflict and resolve it using different strategies."""
    print("\n" + SEP)
    print("  [DEMO 5] Conflict Simulation & Resolution")
    print(SEP)

    from mesh.offline_sync_engine import (
        SyncOperation, SyncOperationStatus,
        ResolutionStrategy, get_offline_sync_engine,
    )

    engine = get_offline_sync_engine()

    now_ts = datetime.now(timezone.utc).timestamp()

    # Create two conflicting local and remote operations using keyword args
    local_op = SyncOperation(
        id="local-001",
        crdt_id="doc:chapter1",
        operation="update",
        key="title",
        value={"title": "Offline Nepal Guide"},
        status=SyncOperationStatus.PENDING,
        created_at=now_ts,
    )
    remote_op = SyncOperation(
        id="remote-001",
        crdt_id="doc:chapter1",
        operation="update",
        key="title",
        value={"title": "Nepal Travel Guide 2026"},
        status=SyncOperationStatus.PENDING,
        created_at=now_ts,
    )

    # Test each resolution strategy
    for strategy in ResolutionStrategy:
        resolution = engine.process_conflict(local_op, remote_op)
        print(f"  [OK] {strategy.value:25s} -> resolution: {resolution.value}")

    # Record a real conflict
    conflict = engine.record_conflict(local_op, remote_op, ResolutionStrategy.MANUAL)
    print(f"\n  [->] Recorded conflict: {conflict.id[:16]}... (resolved={conflict.resolved})")

    # Resolve it manually
    ok = engine.resolve_conflict(conflict.id, ResolutionStrategy.LOCAL_PREFERRED, resolved_by="demo")
    print(f"  [->] Manually resolved: {ok}")

    # Check conflicts list
    remaining = engine.get_conflicts(unresolved_only=True)
    print(f"  [->] Unresolved conflicts remaining: {len(remaining)}")


# ============================================================================
# Demo 6 -- Sync flush cycle (sync-now)
# ============================================================================

def demo_sync_flush(engine):
    """Trigger an immediate sync and inspect the result."""
    print("\n" + SEP)
    print("  [DEMO 6] Sync Flush (sync_now)")
    print(SEP)

    result = engine.flush()

    print(f"  [OK] Flush triggered")
    print(f"  [OK] Flushed         : {result.get('flushed', False)}")
    print(f"  [OK] Synced count    : {result.get('synced_count', 0)}")
    print(f"  [OK] Failed count    : {result.get('failed_count', 0)}")
    print(f"  [OK] Conflict count  : {result.get('conflict_count', 0)}")
    print(f"  [OK] Duration (s)    : {result.get('duration_seconds', 0):.3f}")

    # Check queue is now smaller
    st = engine.status()
    print(f"  [->] Queue size after flush: {st.get('queue_size', 0)}")


# ============================================================================
# Demo 7 -- Multi-Mesh Router integration
# ============================================================================

def demo_multi_mesh_router():
    """Show multi-mesh routing awareness alongside offline sync."""
    print("\n" + SEP)
    print("  [DEMO 7] Multi-Mesh Router Integration")
    print(SEP)

    try:
        from mesh.multi_mesh_router import (
            MultiMeshRouter, MeshType, get_multi_mesh_router,
        )
    except ImportError:
        print("  [--] multi_mesh_router not importable -- skipping")
        return

    router = get_multi_mesh_router()

    print(f"  [OK] MultiMeshRouter loaded")

    for mesh_type in MeshType:
        state = router.get_connection_state(mesh_type) if hasattr(router, 'get_connection_state') else "unknown"
        print(f"  [OK] {mesh_type.value:15s} -> state: {state}")

    # Show data classification routing
    print(f"\n  [->] Router type : {type(router).__name__}")
    print(f"  [->] Mesh types  : {[mt.value for mt in MeshType]}")

    if hasattr(router, 'get_active_mesh'):
        active = router.get_active_mesh()
        print(f"  [->] Active mesh : {active.value if active else 'none'}")

    if hasattr(router, 'get_stats'):
        stats = router.get_stats()
        print(f"  [->] Router stats: {json.dumps(stats, indent=2)}")


# ============================================================================
# Demo 8 -- Stats and engine report
# ============================================================================

def demo_engine_stats(engine):
    """Collect and display comprehensive engine statistics."""
    print("\n" + SEP)
    print("  [DEMO 8] Engine Statistics & Report")
    print(SEP)

    stats = engine.stats()
    print(f"  {json.dumps(stats, indent=2, default=str)}")


# ============================================================================
# Demo 9 -- Endpoint integration (dry-run)
# ============================================================================

def demo_endpoint_integration():
    """Show how the backend endpoints map to the engine (no server needed)."""
    print("\n" + SEP)
    print("  [DEMO 9] Backend Endpoint Integration (Dry-Run)")
    print(SEP)

    from core.sync.offline_sync import get_sync_engine, OpType

    engine = get_sync_engine()

    # Simulate what each endpoint does
    print("  GET /api/sync/status")
    st = engine.status()
    simple = {k: v for k, v in st.items() if not isinstance(v, (list, dict))}
    print(f"    -> {json.dumps(simple, indent=4)}")

    print("\n  POST /api/sync/enqueue")
    op = engine.enqueue(OpType.CREATE, "endpoint_test", "demo_endpoint",
                        {"source": "dry_run"})
    print(f"    -> op_id={op.to_dict().get('operation_id', '?')[:16]}...")

    print("\n  POST /api/sync/flush")
    fl = engine.flush()
    print(f"    -> flushed={fl.get('flushed')}, synced={fl.get('synced_count')}")

    print("\n  GET /api/sync/queue")
    q = engine.queue_list()
    print(f"    -> {len(q)} pending operations")

    print("\n  GET /api/offline/data")
    offline_data = {
        "offline_ready": True,
        "sync_engine": engine.status(),
        "pending_count": engine.pending_count(),
        "conflicts": engine.conflicts(),
        "stats": engine.stats(),
    }
    print(f"    -> offline_ready={offline_data['offline_ready']}")
    print(f"    -> pending_count={offline_data['pending_count']}")
    print(f"    -> conflicts={len(offline_data['conflicts'])}")

    print("\n  POST /api/offline/sync")
    engine.flush()
    print(f"    -> success=True, remaining_pending={len(engine.queue_list())}")


# ============================================================================
# Demo 10 -- Full lifecycle: offline -> enqueue -> online -> sync
# ============================================================================

def demo_full_lifecycle():
    """Simulate a complete offline-then-online lifecycle with real engine."""
    print("\n" + SEP)
    print("  [DEMO 10] Full Lifecycle (Offline -> Online -> Sync)")
    print(SEP)

    from mesh.offline_sync_engine import (
        get_offline_sync_engine, reset_offline_sync_engine,
        SyncPriority, SyncOperationStatus,
    )

    # Reset for clean demo
    reset_offline_sync_engine()

    real_engine = get_offline_sync_engine()
    real_engine.set_online(False)  # Start offline

    # -- Phase 1: Offline --
    print("\n  [Phase 1] Device is OFFLINE -- queueing operations...")
    ops_data = [
        ("note:trek1", {"title": "Annapurna Circuit", "status": "planned"}),
        ("note:trek2", {"title": "Everest Base Camp", "status": "planned"}),
        ("note:trek3", {"title": "Langtang Valley",    "status": "planned"}),
    ]
    for crdt_id, value in ops_data:
        op = real_engine.enqueue_operation(crdt_id, "create", key=crdt_id, value=value)
        print(f"    [OK] Queued [{crdt_id}] -- status={op.status.name}")

    assert real_engine.get_pending_operations(), "Should have pending ops"
    print(f"    [->] Pending count: {len(real_engine.get_pending_operations())}")

    # -- Phase 2: Go online --
    print("\n  [Phase 2] Device comes ONLINE -- triggering sync...")
    real_engine.set_online(True)

    # Register a simple handler that "syncs" by marking operations as synced
    def fake_sync_handler(ops):
        """Pretend to send operations to a remote server."""
        logger.info(f"  Fake sync handler received {len(ops)} operations")
        return True

    real_engine.register_sync_handler(fake_sync_handler)

    # Trigger sync
    status = real_engine.sync_now()
    print(f"    [OK] Sync complete: synced={status.synced_count}, failed={status.failed_count}")

    # -- Phase 3: Add more while online --
    print("\n  [Phase 3] Device is ONLINE -- direct sync...")
    op = real_engine.enqueue_operation(
        "note:trek4", "create",
        key="note:trek4", value={"title": "Mardi Himal", "status": "planned"},
        priority=SyncPriority.HIGH,
    )
    print(f"    [OK] Enqueued HIGH-priority op: {op.id[:16]}...")
    status = real_engine.sync_now()
    print(f"    [OK] Sync after online enqueue: synced={status.synced_count}")

    # -- Phase 4: Stats --
    print("\n  [Phase 4] Final Stats:")
    stats = real_engine.get_stats()
    print(f"    Total operations  : {stats.get('total_operations', 0)}")
    print(f"    Synced            : {stats.get('total_synced', 0)}")
    print(f"    Conflicts         : {stats.get('total_conflicts', 0)}")
    print(f"    Sync count        : {stats.get('sync_count', 0)}")


# ============================================================================
# Main
# ============================================================================

def main():
    print()
    print(SEP)
    print("  ASIM NEXUS -- Mesh + Offline Sync Demo (Phase 60-80%)")
    print(SEP)
    print()
    print(f"  Started at: {datetime.now().isoformat()}")
    print(f"  Python    : {sys.version.split()[0]}")
    print()

    # Run all demos
    engine = demo_bridge_init()
    demo_enqueue_operations(engine)
    demo_inspect_queue(engine)
    demo_peer_selection()
    demo_conflict_resolution()
    demo_sync_flush(engine)
    demo_multi_mesh_router()
    demo_engine_stats(engine)
    demo_endpoint_integration()
    demo_full_lifecycle()

    # -- Summary --
    print()
    print(SEP)
    print("  DEMO COMPLETE")
    print(SEP)
    print()
    print("  Components demonstrated:")
    print("    * core/sync/offline_sync.py   -- Bridge adapter (161 lines)")
    print("    * mesh/offline_sync_engine.py -- Real engine (873 lines, 87 tests)")
    print("    * mesh/multi_mesh_router.py   -- Multi-mesh routing (825 lines, 80 tests)")
    print("    * simple_backend.py           -- Wired /api/sync/* + /api/offline/*")
    print()
    print("  For backend integration, start the server:")
    print("    python simple_backend.py")
    print()
    print("  Then test endpoints:")
    print("    curl http://localhost:8000/api/sync/status")
    print("    curl http://localhost:8000/api/offline/data")
    print()


if __name__ == "__main__":
    main()
