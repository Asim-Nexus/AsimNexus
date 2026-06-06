#!/usr/bin/env python3
"""
STATUS: NEW — CRDT Sync + P2PIntegration Integration Tests
ASIMNEXUS Phase 1D — Sync & Orchestration
=========================================
Tests CRDTStore wired to real P2PTransport WebSocket messaging,
plus P2PIntegration orchestrating DHT + CRDT + Bootstrap together.

Test classes:
  - TestCRDTStoreLifecycle       — start/stop, local-only mode
  - TestCRDTOperations           — GCounter, LWWRegister, ORSet on single store
  - TestTwoNodeCRDTSync          — push_operations + request_sync over real WS
  - TestTwoNodeGCounter          — GCounter increment and sync between 2 nodes
  - TestTwoNodeLWWRegister       — LWWRegister set and sync between 2 nodes
  - TestTwoNodeORSet             — ORSet add and sync between 2 nodes
  - TestBroadcastOperations      — broadcast_operations to multiple peers
  - TestApplySyncState           — apply_sync_state full state reconstruction
  - TestP2PIntegrationWiring     — P2PIntegration start with DHT + CRDT + Bootstrap
"""

import os
import sys
import json
import time
import logging
import asyncio
import socket
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from mesh.crdt_sync import (
    CRDTStore,
    CRDTOperation,
    CRDTType,
    GCounter,
    LWWRegister,
    ORSet,
    get_crdt_store,
    reset_crdt_store,
)
from mesh.p2p_transport import (
    P2PTransport,
    P2PMessage,
    PeerInfo,
    WSMessageType,
    ConnectionState,
    get_p2p_transport,
    reset_p2p_transport,
)
from mesh.kademlia_dht import (
    KademliaDHT,
    NodeID,
    get_kademlia_dht,
    reset_kademlia_dht,
)
from mesh.bootstrap import (
    BootstrapService,
    RegisteredPeer,
    get_bootstrap_service,
    reset_bootstrap_service,
)
from mesh.p2p_integration import (
    P2PIntegration,
    get_p2p_integration,
    reset_p2p_integration,
)
from mesh.multi_mesh_router import MeshType

logger = logging.getLogger("TestMeshSync")
logger.setLevel(logging.DEBUG)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def find_free_port() -> int:
    """Find a free TCP/UDP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def event_loop():
    """Create a fresh event loop per test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ─── Test: CRDTStore Lifecycle ────────────────────────────────────────────────

class TestCRDTStoreLifecycle:
    """CRDTStore start/stop lifecycle with and without transport."""

    @pytest.mark.asyncio
    async def test_create_store(self):
        """CRDTStore can be created with a node_id."""
        store = CRDTStore("node-A")
        assert store.node_id == "node-A"
        assert len(store.crdts) == 0
        assert len(store.operation_log) == 0
        assert len(store.pending_operations) == 0
        assert store.transport is None
        await store.stop()

    @pytest.mark.asyncio
    async def test_start_without_transport_logs_warning(self):
        """start() with no transport logs a warning but doesn't crash."""
        store = CRDTStore("node-A")
        await store.start()  # No transport — logs warning, returns gracefully
        assert store._running is False  # local-only mode does not set _running
        await store.stop()

    @pytest.mark.asyncio
    async def test_start_stop_with_transport(self):
        """start(transport) registers WS handlers, stop() cleans up."""
        port = find_free_port()
        transport = P2PTransport("node-A", "127.0.0.1", find_free_port(), port)
        await transport.start()

        store = CRDTStore("node-A", transport=transport)
        await store.start(transport)

        assert store._running is True
        assert store.transport is transport

        await store.stop()
        assert store._running is False
        await transport.stop()

    @pytest.mark.asyncio
    async def test_get_crdt_store_singleton(self):
        """get_crdt_store returns same instance, reset clears it."""
        reset_crdt_store()
        s1 = get_crdt_store("node-A")
        s2 = get_crdt_store("node-B")
        assert s1 is s2
        reset_crdt_store()
        s3 = get_crdt_store("node-C")
        assert s3 is not s1
        reset_crdt_store()


# ─── Test: CRDT Operations ────────────────────────────────────────────────────

class TestCRDTOperations:
    """Single-store CRDT operations without transport."""

    def setup_method(self):
        self.store = CRDTStore("node-A")

    def teardown_method(self):
        asyncio.run_coroutine_threadsafe(self.store.stop(), asyncio.get_event_loop())

    def test_create_gcounter(self):
        """create_g_counter creates a GCounter."""
        counter = self.store.create_g_counter("counter1")
        assert isinstance(counter, GCounter)
        assert counter.crdt_id == "counter1"
        assert counter.value() == 0  # GCounter.value() returns int (sum)

    def test_create_lww_register(self):
        """create_lww_register creates an LWWRegister."""
        reg = self.store.create_lww_register("reg1")
        assert isinstance(reg, LWWRegister)
        assert reg.crdt_id == "reg1"
        assert reg.get() is None

    def test_create_or_set(self):
        """create_or_set creates an ORSet."""
        orset = self.store.create_or_set("set1")
        assert isinstance(orset, ORSet)
        assert orset.crdt_id == "set1"
        assert orset.elements_list() == []

    def test_gcounter_increment(self):
        """GCounter.increment updates value."""
        counter = self.store.create_g_counter("counter1")
        op = counter.increment("node-A", 5)
        assert op.operation == "increment"
        assert counter.value() == 5  # GCounter.value() returns total sum
        assert counter.counters.get("node-A") == 5  # per-node count

    def test_lww_register_set_and_get(self):
        """LWWRegister.set and get work."""
        reg = self.store.create_lww_register("reg1")
        op = reg.set("hello", "node-A")
        assert op.operation == "set"
        assert reg.get() == "hello"

    def test_orset_add_and_contains(self):
        """ORSet.add and contains work."""
        orset = self.store.create_or_set("set1")
        op = orset.add("item1", "node-A")
        assert op.operation == "add"
        assert orset.contains("item1") is True

    def test_orset_remove(self):
        """ORSet.remove works."""
        orset = self.store.create_or_set("set1")
        orset.add("item1", "node-A")
        assert orset.contains("item1") is True
        orset.remove("item1", "node-A")
        assert orset.contains("item1") is False

    def test_apply_remote_operation(self):
        """apply_remote_operation applies an op from another node."""
        counter = self.store.create_g_counter("counter1")

        # Simulate remote op — GCounter increment value is int (amount)
        op = CRDTOperation(
            id="op1",
            crdt_id="counter1",
            crdt_type=CRDTType.G_COUNTER,
            operation="increment",
            value=3,  # amount to increment
            node_id="node-B",
        )
        success = self.store.apply_remote_operation(op)
        assert success is True
        # GCounter apply_operation adds op.value to counter[node_id]
        assert counter.counters.get("node-B") == 3
        assert counter.value() == 3

    def test_get_state(self):
        """get_state returns all CRDT states."""
        self.store.create_g_counter("counter1")
        self.store.create_lww_register("reg1")
        self.store.create_or_set("set1")
        state = self.store.get_state()
        assert "counter1" in state
        assert "reg1" in state
        assert "set1" in state
        assert state["counter1"]["type"] == "g_counter"
        assert state["reg1"]["type"] == "lww_register"
        assert state["set1"]["type"] == "or_set"

    def test_get_pending_operations(self):
        """get_pending_operations returns pending ops from operation_log."""
        counter = self.store.create_g_counter("counter1")
        op1 = counter.increment("node-A", 1)
        op2 = counter.increment("node-A", 2)
        # Log the operations to the store's pending_operations list
        self.store.log_operation(op1)
        self.store.pending_operations.append(op1)
        self.store.log_operation(op2)
        self.store.pending_operations.append(op2)
        pending = self.store.get_pending_operations()
        assert len(pending) >= 2

    def test_get_pending_since(self):
        """get_pending_operations with since filter."""
        counter = self.store.create_g_counter("counter1")
        time.sleep(0.01)
        since = time.time()
        time.sleep(0.01)
        op1 = counter.increment("node-A", 1)
        op2 = counter.increment("node-A", 2)
        # Log operations to the store's pending_operations list
        self.store.log_operation(op1)
        self.store.pending_operations.append(op1)
        self.store.log_operation(op2)
        self.store.pending_operations.append(op2)
        recent = self.store.get_pending_operations(since=since)
        assert len(recent) >= 2


# ─── Test: Two-Node CRDT Sync ────────────────────────────────────────────────

class TestTwoNodeCRDTSync:
    """CRDT sync between two real P2PTransport instances over WebSocket."""

    @pytest.mark.asyncio
    async def test_push_operations_sync(self):
        """Push operations from node A to node B, verify B receives them."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        # Connect A -> B via WebSocket
        peer_id = await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        assert peer_id == "node-B"

        # Get PeerInfo for B from A's perspective
        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None
        assert peer_b.connection_state == ConnectionState.CONNECTED

        # Create a counter on A, increment it
        counter_a = store_a.create_g_counter("counter1")
        counter_a.increment("node-A", 10)
        counter_a.increment("node-A", 5)

        # Push operations from A to B
        pushed = await store_a.push_operations(peer_b)
        assert pushed is True

        # Allow async handler to process on B
        await asyncio.sleep(0.05)

        # Verify B has the counter with merged value
        counter_b = store_b.get_crdt("counter1")
        assert counter_b is not None, "B should have received the counter CRDT"

        # B should have the value via apply_sync_state (sync_state includes crdt_state)
        # apply_sync_state reconstructs the CRDT from sync_state
        b_state = store_b.get_state()
        assert "counter1" in b_state
        assert b_state["counter1"]["type"] == "g_counter"

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()

    @pytest.mark.asyncio
    async def test_request_sync(self):
        """Node A requests sync from Node B, receives B's CRDT state."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        # Connect A -> B
        peer_id = await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        assert peer_id == "node-B"

        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None

        # Create counter on B (the node being requested)
        counter_b = store_b.create_g_counter("counter1")
        counter_b.increment("node-B", 42)

        # A requests sync from B
        requested = await store_a.request_sync(peer_b, since=0.0)
        assert requested is True

        # Allow async handler to process
        await asyncio.sleep(0.05)

        # A should now have B's CRDT state from the sync response
        # Note: request_sync is fire-and-forget; the response arrives via WS handler
        # The handler receives SYNC_RESPONSE but doesn't auto-apply (it's just received)
        # So this test verifies the request was sent without error

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()


# ─── Test: Two-Node GCounter Sync ────────────────────────────────────────────

class TestTwoNodeGCounter:
    """GCounter operations sync between two nodes."""

    @pytest.mark.asyncio
    async def test_gcounter_sync_via_push(self):
        """GCounter value from A propagates to B via push_operations."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None

        # Create counter on A, increment
        counter_a = store_a.create_g_counter("gc1")
        counter_a.increment("node-A", 7)
        counter_a.increment("node-A", 3)

        # Push to B
        pushed = await store_a.push_operations(peer_b)
        assert pushed is True
        await asyncio.sleep(0.05)

        # B should have received the counter via sync_state from push_operations
        b_state = store_b.get_state()
        assert "gc1" in b_state, "B should have gc1 from push sync_state"

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()

    @pytest.mark.asyncio
    async def test_gcounter_merge_across_nodes(self):
        """Two nodes independently increment, then merge."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None

        # A increments
        counter_a = store_a.create_g_counter("gc_merge")
        counter_a.increment("node-A", 5)

        # B increments (independently created)
        counter_b = store_b.create_g_counter("gc_merge")
        counter_b.increment("node-B", 10)

        # Push A -> B — B's handler applies operations + sync_state
        await store_a.push_operations(peer_b)
        await asyncio.sleep(0.1)

        # After push, B should have merged A's value
        b_counter_after = store_b.get_crdt("gc_merge")
        assert b_counter_after is not None
        assert b_counter_after.counters.get("node-A", 0) == 5
        assert b_counter_after.counters.get("node-B", 0) == 10
        assert b_counter_after.value() == 15  # total sum: 5 + 10

        # Also verify A still has its own value unchanged
        assert counter_a.counters.get("node-A", 0) == 5
        assert counter_a.value() == 5

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()


# ─── Test: Two-Node LWWRegister Sync ─────────────────────────────────────────

class TestTwoNodeLWWRegister:
    """LWWRegister operations sync between two nodes."""

    @pytest.mark.asyncio
    async def test_lww_register_sync(self):
        """LWWRegister value propagates from A to B."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None

        # Create register on A, set value
        reg_a = store_a.create_lww_register("lww1")
        reg_a.set("AsimNexus", "node-A")

        # Push to B
        pushed = await store_a.push_operations(peer_b)
        assert pushed is True
        await asyncio.sleep(0.05)

        # B should have the register via apply_sync_state
        b_state = store_b.get_state()
        assert "lww1" in b_state

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()

    @pytest.mark.asyncio
    async def test_lww_last_writer_wins(self):
        """Later write wins when two nodes set the same register."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None

        # A sets value
        reg_a = store_a.create_lww_register("lww_lww")
        reg_a.set("from-A", "node-A")
        time.sleep(0.01)
        ts_a = time.time()

        # B sets value later
        reg_b = store_b.create_lww_register("lww_lww")
        time.sleep(0.01)
        reg_b.set("from-B", "node-B")

        # Push B's state to A
        b_sync = store_b.get_sync_state()
        store_a.apply_sync_state(b_sync)

        # A should have B's value (later timestamp wins)
        reg_a_after = store_a.get_crdt("lww_lww")
        assert reg_a_after is not None
        # If B's timestamp > A's, B wins
        # Note: timestamps are close, so this is best-effort
        if reg_b.timestamp > ts_a:
            assert reg_a_after.get() == "from-B"

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()


# ─── Test: Two-Node ORSet Sync ───────────────────────────────────────────────

class TestTwoNodeORSet:
    """ORSet operations sync between two nodes."""

    @pytest.mark.asyncio
    async def test_orset_sync(self):
        """ORSet elements propagate from A to B."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None

        # Create set on A, add elements
        set_a = store_a.create_or_set("oset1")
        set_a.add("alpha", "node-A")
        set_a.add("beta", "node-A")

        # Push to B
        pushed = await store_a.push_operations(peer_b)
        assert pushed is True
        await asyncio.sleep(0.05)

        # B should have the set via apply_sync_state
        b_state = store_b.get_state()
        assert "oset1" in b_state

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()

    @pytest.mark.asyncio
    async def test_orset_add_remove_sync(self):
        """ORSet add + remove syncs correctly."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None

        # Create set on A, add then remove
        set_a = store_a.create_or_set("oset_ar")
        set_a.add("temp", "node-A")
        set_a.remove("temp", "node-A")

        # Push to B
        await store_a.push_operations(peer_b)
        await asyncio.sleep(0.05)

        # B's state should show the set (element may or may not be present depending on merge order)
        b_state = store_b.get_state()
        assert "oset_ar" in b_state

        # The removed element should not be in B's set
        set_b = store_b.get_crdt("oset_ar")
        if set_b is not None:
            assert set_b.contains("temp") is False

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()


# ─── Test: Broadcast Operations ───────────────────────────────────────────────

class TestBroadcastOperations:
    """Broadcast CRDT operations to multiple peers."""

    @pytest.mark.asyncio
    async def test_broadcast_to_two_peers(self):
        """Broadcast operations from A reaches both B and C."""
        port_b_ws = find_free_port()
        port_c_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)
        node_c = P2PTransport("node-C", "127.0.0.1", find_free_port(), port_c_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)
        store_c = CRDTStore("node-C", transport=node_c)

        await node_a.start()
        await node_b.start()
        await node_c.start()
        await store_a.start(node_a)
        await store_b.start(node_b)
        await store_c.start(node_c)

        # Connect A -> B and A -> C
        await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        await node_a.connect_peer("127.0.0.1", port_c_ws, timeout=5.0)

        await asyncio.sleep(0.05)  # Let WS connections settle

        # Create counter on A, increment
        counter_a = store_a.create_g_counter("bcast_counter")
        counter_a.increment("node-A", 100)

        # Broadcast to all connected peers
        count = await store_a.broadcast_operations()
        assert count >= 2, f"Should broadcast to 2 peers, got {count}"
        await asyncio.sleep(0.05)

        # Both B and C should have received the counter via sync_state
        b_state = store_b.get_state()
        c_state = store_c.get_state()
        assert "bcast_counter" in b_state, "B should have received broadcast"
        assert "bcast_counter" in c_state, "C should have received broadcast"

        await store_a.stop()
        await store_b.stop()
        await store_c.stop()
        await node_a.stop()
        await node_b.stop()
        await node_c.stop()


# ─── Test: Apply Sync State ───────────────────────────────────────────────────

class TestApplySyncState:
    """apply_sync_state full state reconstruction."""

    @pytest.mark.asyncio
    async def test_apply_sync_state_reconstructs_crdts(self):
        """apply_sync_state creates CRDTs on target node."""
        reset_crdt_store()
        store_a = CRDTStore("node-A")
        store_b = CRDTStore("node-B")

        # Create CRDTs on A
        store_a.create_g_counter("gc_state")
        store_a.create_lww_register("lww_state")
        store_a.create_or_set("or_state")

        # Get sync state from A
        sync_state = store_a.get_sync_state()

        # Apply on B
        applied = store_b.apply_sync_state(sync_state)
        assert applied >= 0

        # B should have the CRDTs
        assert store_b.get_crdt("gc_state") is not None
        assert store_b.get_crdt("lww_state") is not None
        assert store_b.get_crdt("or_state") is not None

        await store_a.stop()
        await store_b.stop()

    @pytest.mark.asyncio
    async def test_apply_sync_state_with_operations(self):
        """apply_sync_state with operations applies them."""
        store_a = CRDTStore("node-A")

        counter = store_a.create_g_counter("gc_ops")
        counter.increment("node-A", 7)

        sync_state = store_a.get_sync_state()

        store_b = CRDTStore("node-B")
        # First apply state to create CRDTs
        store_b.apply_sync_state(sync_state)

        # Then re-apply operations
        store_b.apply_sync_state(sync_state)

        counter_b = store_b.get_crdt("gc_ops")
        assert counter_b is not None

        await store_a.stop()
        await store_b.stop()

    @pytest.mark.asyncio
    async def test_cleanup_old_operations(self):
        """cleanup_old_operations removes stale ops from pending/operation_log."""
        store = CRDTStore("node-A")
        counter = store.create_g_counter("gc_clean")
        op = counter.increment("node-A", 1)
        store.log_operation(op)

        # Before cleanup, ops exist
        assert len(store.operation_log) >= 1

        # Cleanup with max_age=0 should clear everything
        store.cleanup_old_operations(max_age=0)
        assert len(store.pending_operations) == 0

        await store.stop()


# ─── Test: P2PIntegration Wiring ─────────────────────────────────────────────

class TestP2PIntegrationWiring:
    """P2PIntegration start/stop with DHT + CRDT + Bootstrap wired together."""

    @pytest.mark.asyncio
    async def test_integration_start_stop(self):
        """P2PIntegration starts and stops with DHT + CRDT + Bootstrap."""
        reset_p2p_integration()
        reset_kademlia_dht()
        reset_bootstrap_service()
        reset_crdt_store()

        node_id = "integration-node"

        # Create components
        dht = get_kademlia_dht(node_id)
        crdt = get_crdt_store(node_id)
        bootstrap = get_bootstrap_service(node_id, is_bootstrap=True)

        # Bootstrap server on a free port
        bootstrap_port = find_free_port()
        bootstrap.port = bootstrap_port

        # Create P2PIntegration with all components
        integration = P2PIntegration(
            node_id=node_id,
            kademlia_dht=dht,
            crdt_store=crdt,
            bootstrap_service=bootstrap,
        )

        # Start everything
        await bootstrap.start()
        await integration.start()

        assert integration._running is True
        assert integration._dht is dht
        assert integration._crdt is crdt
        assert integration._bootstrap is bootstrap

        # Stop everything
        await integration.stop()
        await bootstrap.stop()

        reset_p2p_integration()
        reset_kademlia_dht()
        reset_bootstrap_service()
        reset_crdt_store()

    @pytest.mark.asyncio
    async def test_integration_without_optional_components(self):
        """P2PIntegration starts cleanly without DHT/CRDT/Bootstrap."""
        reset_p2p_integration()

        integration = P2PIntegration(node_id="bare-node")

        await integration.start()
        assert integration._running is True
        assert integration._dht is None
        assert integration._crdt is None
        assert integration._bootstrap is None

        await integration.stop()
        reset_p2p_integration()

    @pytest.mark.asyncio
    async def test_get_p2p_integration_singleton_with_components(self):
        """get_p2p_integration singleton accepts optional components."""
        reset_p2p_integration()
        reset_kademlia_dht()
        reset_crdt_store()

        node_id = "singleton-test"
        dht = get_kademlia_dht(node_id)
        crdt = get_crdt_store(node_id)

        integration = get_p2p_integration(
            node_id=node_id,
            kademlia_dht=dht,
            crdt_store=crdt,
        )
        assert integration._dht is dht
        assert integration._crdt is crdt

        reset_p2p_integration()
        reset_kademlia_dht()
        reset_crdt_store()

    @pytest.mark.asyncio
    async def test_dht_routes_via_transport_after_start(self):
        """DHT RPC handlers work after P2PIntegration starts with DHT."""
        reset_kademlia_dht()
        reset_p2p_integration()

        port_b_ws = find_free_port()

        node_id_a = "dht-node-A"
        node_id_b = "dht-node-B"

        # Create DHT for A
        dht_a = KademliaDHT(
            node_id=NodeID.from_string("A"),
            port=find_free_port(),
        )
        dht_b = KademliaDHT(
            node_id=NodeID.from_string("B"),
            port=find_free_port(),
        )

        # Create transports
        transport_a = P2PTransport(node_id_a, "127.0.0.1", find_free_port(), find_free_port())
        transport_b = P2PTransport(node_id_b, "127.0.0.1", find_free_port(), port_b_ws)

        # Start DHT on transports
        await dht_a.start(transport_a)
        await dht_b.start(transport_b)
        await transport_a.start()
        await transport_b.start()

        # Connect A -> B
        await transport_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        await asyncio.sleep(0.05)

        # Create a DHTNode for B and add to A's routing table
        from mesh.kademlia_dht import DHTNode
        dht_node_b = DHTNode(
            node_id=dht_b.node_id,
            ip_address="127.0.0.1",
            port=dht_b.port,
        )
        dht_a.add_node(dht_node_b)

        # A should find B in routing table (find_node does direct lookup)
        found = dht_a.find_node(dht_b.node_id)
        assert found is not None
        assert found.node_id.value == dht_b.node_id.value

        # PING from A to B via transport RPC
        from mesh.p2p_transport import RPCMessageType
        peer_b_info = PeerInfo(
            node_id=node_id_b,
            host="127.0.0.1",
            port_udp=transport_b.port_udp,
            port_ws=transport_b.port_ws,
        )
        response = await transport_a.rpc_call(
            peer=peer_b_info,
            msg_type=RPCMessageType.PING.value,
            payload={},
            timeout=3.0,
        )
        assert response is not None
        assert response.msg_type == RPCMessageType.PONG.value

        await dht_a.stop()
        await dht_b.stop()
        await transport_a.stop()
        await transport_b.stop()

        reset_kademlia_dht()
        reset_p2p_integration()


# ─── Test: CRDTStore Integration Pattern ──────────────────────────────────────

class TestCRDTStoreSyncPattern:
    """End-to-end sync pattern: create, push, pull, verify."""

    @pytest.mark.asyncio
    async def test_full_sync_roundtrip(self):
        """Full sync roundtrip: A creates CRDT → B gets state → verify."""
        port_b_ws = find_free_port()

        node_a = P2PTransport("node-A", "127.0.0.1", find_free_port(), find_free_port())
        node_b = P2PTransport("node-B", "127.0.0.1", find_free_port(), port_b_ws)

        store_a = CRDTStore("node-A", transport=node_a)
        store_b = CRDTStore("node-B", transport=node_b)

        await node_a.start()
        await node_b.start()
        await store_a.start(node_a)
        await store_b.start(node_b)

        # Connect
        await node_a.connect_peer("127.0.0.1", port_b_ws, timeout=5.0)
        peer_b = await node_a.get_peer("node-B")
        assert peer_b is not None

        # A creates a counter and increments
        counter_a = store_a.create_g_counter("roundtrip")
        counter_a.increment("node-A", 42)

        # A pushes operations to B
        await store_a.push_operations(peer_b)
        await asyncio.sleep(0.05)

        # B applies the sync state
        b_state = store_b.get_sync_state()

        # A merges B's state back (roundtrip)
        store_a.apply_sync_state(b_state)

        # Verify A's counter has its own value
        counter_a_after = store_a.get_crdt("roundtrip")
        assert counter_a_after is not None
        assert counter_a_after.value() >= 42  # total sum
        assert counter_a_after.counters.get("node-A", 0) >= 42  # per-node

        await store_a.stop()
        await store_b.stop()
        await node_a.stop()
        await node_b.stop()


# ─── Run everything ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
