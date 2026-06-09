#!/usr/bin/env python3
"""
STATUS: REAL — Phase 1D: Sync & Orchestration
ASIMNEXUS 3-Node Full-Stack E2E Test
======================================
Verifies the entire P2P mesh stack works across 3 localhost nodes:

  1. Start Node A (P2PTransport + KademliaDHT + CRDTStore)
  2. Start Node B (same stack on different ports)
  3. Start Node C (same stack on different ports)
  4. Bootstrap A → B learns about C
  5. CRDT write on A → sync to B via WS → verify B has data
  6. CRDT write on B → sync to C via WS → verify C has data
  7. All 3 nodes converge — each has the same CRDT state

Also validates the create_local_node_set() helper factory.
"""

import os
import sys
import time
import json
import asyncio
import random
import socket
import logging
from typing import Dict, List, Optional, Any, Tuple

import pytest

# ── Silence noisy loggers ────────────────────────────────────────────────
logging.getLogger("AsimNexus.Mesh.P2PIntegration").setLevel(logging.WARNING)
logging.getLogger("AsimNexus.Mesh.P2PTransport").setLevel(logging.WARNING)
logging.getLogger("AsimNexus.Mesh.CrdtSync").setLevel(logging.WARNING)
logging.getLogger("AsimNexus.Mesh.KademliaDHT").setLevel(logging.WARNING)
logging.getLogger("AsimNexus.Mesh.MultiMeshRouter").setLevel(logging.WARNING)

# ── Helper: find free port ───────────────────────────────────────────────

_EPHEMERAL_PORT_MAX = 65535


def _find_free_port(start: int = 22500) -> int:
    """Find a free UDP port by trying random ports near *start*."""
    for _ in range(50):
        port = random.randint(start, min(start + 1000, _EPHEMERAL_PORT_MAX - 1))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return random.randint(30000, 40000)


@pytest.fixture
def event_loop():
    """Provide an event loop for each async test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ═══════════════════════════════════════════════════════════════════════════
# Test: 3-Node Full-Stack CRDT Chain Sync
# ═══════════════════════════════════════════════════════════════════════════

class TestThreeNodeFullStack:
    """
    7-step E2E flow across 3 localhost nodes.

    Topology:
      Node A (127.0.0.1:UDP_A:WS_A)
      Node B (127.0.0.1:UDP_B:WS_B)
      Node C (127.0.0.1:UDP_C:WS_C)

    Chain: A <-> B <-> C   (A and C not directly peered)
    """

    @pytest.mark.asyncio
    async def test_three_node_crdt_chain_sync(self):
        """
        Full 7-step E2E flow:

        1. Start Node A (P2PTransport + KademliaDHT + CRDTStore)
        2. Start Node B (same stack on different ports)
        3. Start Node C (same stack on different ports)
        4. Wire peers in chain: A↔B, B↔C (A and C are NOT directly connected)
        5. CRDT write on A → sync to B via WS → verify B has data
        6. CRDT write on B → sync to C via WS → verify C has data
        7. All 3 nodes converge to same value after full sync
        """
        port_a = _find_free_port(22500)
        port_b = _find_free_port(22600)
        port_c = _find_free_port(22700)

        from mesh.p2p_transport import (
            P2PTransport, P2PMessage, PeerInfo,
            RPCMessageType, WSMessageType,
        )
        from mesh.kademlia_dht import (
            KademliaDHT, NodeID, DHTNode,
        )
        from mesh.crdt_sync import (
            CRDTStore,
        )

        # ── Step 1-3: Create 3 nodes ────────────────────────────────────
        transport_a = P2PTransport("node-A", "127.0.0.1", port_a, port_a + 1)
        transport_b = P2PTransport("node-B", "127.0.0.1", port_b, port_b + 1)
        transport_c = P2PTransport("node-C", "127.0.0.1", port_c, port_c + 1)

        dht_a = KademliaDHT(
            node_id=NodeID.from_string("node-A"),
            port=port_a,
            transport=transport_a,
        )
        dht_b = KademliaDHT(
            node_id=NodeID.from_string("node-B"),
            port=port_b,
            transport=transport_b,
        )
        dht_c = KademliaDHT(
            node_id=NodeID.from_string("node-C"),
            port=port_c,
            transport=transport_c,
        )

        store_a = CRDTStore(node_id="node-A", transport=transport_a)
        store_b = CRDTStore(node_id="node-B", transport=transport_b)
        store_c = CRDTStore(node_id="node-C", transport=transport_c)

        try:
            # Start transports
            await transport_a.start()
            await transport_b.start()
            await transport_c.start()

            # Start DHTs
            await dht_a.start()
            await dht_b.start()
            await dht_c.start()

            # Start CRDT stores
            await store_a.start()
            await store_b.start()
            await store_c.start()

            # ── Step 4: Wire peers in chain ─────────────────────────────
            # A ↔ B (bidirectional)
            dht_a.add_node(DHTNode(
                node_id=NodeID.from_string("node-B"),
                ip_address="127.0.0.1",
                port=port_b,
            ))
            dht_b.add_node(DHTNode(
                node_id=NodeID.from_string("node-A"),
                ip_address="127.0.0.1",
                port=port_a,
            ))
            peer_b = await transport_a.add_peer("node-B", "127.0.0.1", port_b, port_b + 1)
            await transport_b.add_peer("node-A", "127.0.0.1", port_a, port_a + 1)

            # B ↔ C (bidirectional) — A and C NOT directly connected
            dht_b.add_node(DHTNode(
                node_id=NodeID.from_string("node-C"),
                ip_address="127.0.0.1",
                port=port_c,
            ))
            dht_c.add_node(DHTNode(
                node_id=NodeID.from_string("node-B"),
                ip_address="127.0.0.1",
                port=port_b,
            ))
            peer_c = await transport_b.add_peer("node-C", "127.0.0.1", port_c, port_c + 1)
            await transport_c.add_peer("node-B", "127.0.0.1", port_b, port_b + 1)

            # Also let A know about C's DHT entry (so A can discover C indirectly)
            dht_a.add_node(DHTNode(
                node_id=NodeID.from_string("node-C"),
                ip_address="127.0.0.1",
                port=port_c,
            ))
            dht_c.add_node(DHTNode(
                node_id=NodeID.from_string("node-A"),
                ip_address="127.0.0.1",
                port=port_a,
            ))

            # Give WS handshake time to complete
            await asyncio.sleep(0.5)

            # ── Step 5: CRDT write on A → sync to B ────────────────────
            counter_id = "chain-counter"
            counter_a = store_a.create_g_counter(counter_id)
            counter_a.increment("node-A", 42)

            # Push operations from A → B via WS
            pushed_ab = await store_a.push_operations(peer_b)
            assert pushed_ab, "Step 5 FAILED: A could not push operations to B"
            await asyncio.sleep(0.3)

            # Verify B has the counter with value 42
            counter_b = store_b.get_crdt(counter_id)
            assert counter_b is not None, \
                f"Step 5 FAILED: Counter '{counter_id}' not found on B"
            assert counter_b.value() == 42, \
                f"Step 5 FAILED: B expected 42, got {counter_b.value()}"

            # ── Step 6: CRDT write on B → sync to C ────────────────────
            # Increment on B
            counter_b.increment("node-B", 10)

            # Push operations from B → C via WS
            pushed_bc = await store_b.push_operations(peer_c)
            assert pushed_bc, "Step 6 FAILED: B could not push operations to C"
            await asyncio.sleep(0.3)

            # Verify C has the counter with value 52 (42 + 10)
            counter_c = store_c.get_crdt(counter_id)
            assert counter_c is not None, \
                f"Step 6 FAILED: Counter '{counter_id}' not found on C"
            assert counter_c.value() == 52, \
                f"Step 6 FAILED: C expected 52 (42+10), got {counter_c.value()}"

            # ── Step 7: All 3 nodes converge ───────────────────────────
            # Increment on C and push back to B → B pushes to A
            counter_c.increment("node-C", 5)

            # Push C → B
            pushed_cb = await store_c.push_operations(
                await transport_c.get_peer("node-B")
            )
            assert pushed_cb, "Step 7 FAILED: C could not push to B"
            await asyncio.sleep(0.3)

            # Push B → A (forwarding C's operations back to A)
            pushed_ba = await store_b.push_operations(
                await transport_b.get_peer("node-A")
            )
            assert pushed_ba, "Step 7 FAILED: B could not push to A"
            await asyncio.sleep(0.3)

            # All 3 nodes should now have value 57 (42 + 10 + 5)
            for node_name, store, expected in [
                ("A", store_a, 57),
                ("B", store_b, 57),
                ("C", store_c, 57),
            ]:
                c = store.get_crdt(counter_id)
                assert c is not None, \
                    f"Step 7 FAILED: Counter not found on node {node_name}"
                assert c.value() == expected, \
                    f"Step 7 FAILED: Node {node_name} expected {expected}, " \
                    f"got {c.value()}"

        finally:
            await store_a.stop()
            await store_b.stop()
            await store_c.stop()
            await dht_a.stop()
            await dht_b.stop()
            await dht_c.stop()
            await transport_a.stop()
            await transport_b.stop()
            await transport_c.stop()

    @pytest.mark.asyncio
    async def test_three_node_crdt_convergence(self):
        """
        Verify all 3 nodes converge to the same state after independent writes.

        Flow:
        1. All 3 nodes start with same CRDT counter
        2. Each node independently increments the counter
        3. Push operations in a cycle: A→B→C→A→B
        4. All 3 nodes converge to the same value (sum of all increments = 600)
        """
        port_a = _find_free_port(22800)
        port_b = _find_free_port(22900)
        port_c = _find_free_port(23000)

        from mesh.p2p_transport import (
            P2PTransport, PeerInfo,
        )
        from mesh.kademlia_dht import (
            KademliaDHT, NodeID, DHTNode,
        )
        from mesh.crdt_sync import (
            CRDTStore,
        )

        transport_a = P2PTransport("conv-A", "127.0.0.1", port_a, port_a + 1)
        transport_b = P2PTransport("conv-B", "127.0.0.1", port_b, port_b + 1)
        transport_c = P2PTransport("conv-C", "127.0.0.1", port_c, port_c + 1)

        dht_a = KademliaDHT(node_id=NodeID.from_string("conv-A"), port=port_a, transport=transport_a)
        dht_b = KademliaDHT(node_id=NodeID.from_string("conv-B"), port=port_b, transport=transport_b)
        dht_c = KademliaDHT(node_id=NodeID.from_string("conv-C"), port=port_c, transport=transport_c)

        store_a = CRDTStore(node_id="conv-A", transport=transport_a)
        store_b = CRDTStore(node_id="conv-B", transport=transport_b)
        store_c = CRDTStore(node_id="conv-C", transport=transport_c)

        try:
            await transport_a.start()
            await transport_b.start()
            await transport_c.start()
            await dht_a.start()
            await dht_b.start()
            await dht_c.start()
            await store_a.start()
            await store_b.start()
            await store_c.start()

            # Wire A↔B↔C↔A (full cycle)
            for src_t, src_name, src_port, dst_t, dst_name, dst_port in [
                (transport_a, "conv-A", port_a, transport_b, "conv-B", port_b),
                (transport_b, "conv-B", port_b, transport_c, "conv-C", port_c),
                (transport_c, "conv-C", port_c, transport_a, "conv-A", port_a),
            ]:
                dht = dht_a if src_name == "conv-A" else dht_b if src_name == "conv-B" else dht_c
                dht.add_node(DHTNode(
                    node_id=NodeID.from_string(dst_name),
                    ip_address="127.0.0.1",
                    port=dst_port,
                ))
                await src_t.add_peer(dst_name, "127.0.0.1", dst_port, dst_port + 1)

            await asyncio.sleep(0.5)

            # Create same counter on all 3
            counter_id = "converge-counter"
            c_a = store_a.create_g_counter(counter_id)
            c_b = store_b.create_g_counter(counter_id)
            c_c = store_c.create_g_counter(counter_id)

            # Each node increments independently
            c_a.increment("conv-A", 100)
            c_b.increment("conv-B", 200)
            c_c.increment("conv-C", 300)

            # Push A → B
            peer_b = await transport_a.get_peer("conv-B")
            await store_a.push_operations(peer_b)
            await asyncio.sleep(0.3)

            # Push B → C
            peer_c = await transport_b.get_peer("conv-C")
            await store_b.push_operations(peer_c)
            await asyncio.sleep(0.3)

            # Push C → A
            peer_a = await transport_c.get_peer("conv-A")
            await store_c.push_operations(peer_a)
            await asyncio.sleep(0.3)

            # Push A → B (forward C's data to B so all 3 converge)
            peer_b = await transport_a.get_peer("conv-B")
            await store_a.push_operations(peer_b)
            await asyncio.sleep(0.3)

            # Verify all nodes have the same value (100 + 200 + 300 = 600)
            for node_name, store in [("A", store_a), ("B", store_b), ("C", store_c)]:
                counter = store.get_crdt(counter_id)
                assert counter is not None, \
                    f"Counter not found on node {node_name}"
                assert counter.value() == 600, \
                    f"Node {node_name} expected 600, got {counter.value()}"

        finally:
            await store_a.stop()
            await store_b.stop()
            await store_c.stop()
            await dht_a.stop()
            await dht_b.stop()
            await dht_c.stop()
            await transport_a.stop()
            await transport_b.stop()
            await transport_c.stop()

    @pytest.mark.asyncio
    async def test_three_node_lww_register_sync(self):
        """
        LWWRegister sync across 3 nodes — last-writer-wins semantics.

        Flow:
        1. A creates an LWW register with value "A-data"
        2. A pushes to B → B sees "A-data"
        3. B sets register to "B-data" (later timestamp)
        4. B pushes to C → C sees "B-data"
        5. C sets register to "C-data" (latest timestamp)
        6. C pushes back to A → A sees "C-data" (converged)
        """
        port_a = _find_free_port(23100)
        port_b = _find_free_port(23200)
        port_c = _find_free_port(23300)

        from mesh.p2p_transport import P2PTransport
        from mesh.kademlia_dht import KademliaDHT, NodeID, DHTNode
        from mesh.crdt_sync import CRDTStore

        transport_a = P2PTransport("lww-A", "127.0.0.1", port_a, port_a + 1)
        transport_b = P2PTransport("lww-B", "127.0.0.1", port_b, port_b + 1)
        transport_c = P2PTransport("lww-C", "127.0.0.1", port_c, port_c + 1)
        dht_a = KademliaDHT(node_id=NodeID.from_string("lww-A"), port=port_a, transport=transport_a)
        dht_b = KademliaDHT(node_id=NodeID.from_string("lww-B"), port=port_b, transport=transport_b)
        dht_c = KademliaDHT(node_id=NodeID.from_string("lww-C"), port=port_c, transport=transport_c)
        store_a = CRDTStore(node_id="lww-A", transport=transport_a)
        store_b = CRDTStore(node_id="lww-B", transport=transport_b)
        store_c = CRDTStore(node_id="lww-C", transport=transport_c)

        try:
            await transport_a.start()
            await transport_b.start()
            await transport_c.start()
            await dht_a.start()
            await dht_b.start()
            await dht_c.start()
            await store_a.start()
            await store_b.start()
            await store_c.start()

            # Wire: A↔B, B↔C
            dht_a.add_node(DHTNode(node_id=NodeID.from_string("lww-B"), ip_address="127.0.0.1", port=port_b))
            dht_b.add_node(DHTNode(node_id=NodeID.from_string("lww-A"), ip_address="127.0.0.1", port=port_a))
            dht_b.add_node(DHTNode(node_id=NodeID.from_string("lww-C"), ip_address="127.0.0.1", port=port_c))
            dht_c.add_node(DHTNode(node_id=NodeID.from_string("lww-B"), ip_address="127.0.0.1", port=port_b))
            peer_b = await transport_a.add_peer("lww-B", "127.0.0.1", port_b, port_b + 1)
            await transport_b.add_peer("lww-A", "127.0.0.1", port_a, port_a + 1)
            peer_c = await transport_b.add_peer("lww-C", "127.0.0.1", port_c, port_c + 1)
            await transport_c.add_peer("lww-B", "127.0.0.1", port_b, port_b + 1)

            await asyncio.sleep(0.5)

            register_id = "chain-register"

            # Step 1: A creates register
            reg_a = store_a.create_lww_register(register_id)
            reg_a.set("A-data", "lww-A")

            # Step 2: A → B
            pushed = await store_a.push_operations(peer_b)
            assert pushed, "LWW push A→B failed"
            await asyncio.sleep(0.3)

            reg_b = store_b.get_crdt(register_id)
            assert reg_b is not None, "Register not found on B"
            assert reg_b.get() == "A-data", f"B expected 'A-data', got {reg_b.get()}"

            # Step 3: B sets to "B-data" (later timestamp → wins over A)
            reg_b.set("B-data", "lww-B")

            # Step 4: B → C
            pushed = await store_b.push_operations(peer_c)
            assert pushed, "LWW push B→C failed"
            await asyncio.sleep(0.3)

            reg_c = store_c.get_crdt(register_id)
            assert reg_c is not None, "Register not found on C"
            assert reg_c.get() == "B-data", f"C expected 'B-data', got {reg_c.get()}"

            # Step 5: C sets to "C-data" (latest timestamp)
            reg_c.set("C-data", "lww-C")

            # Step 6: C → B → A (chain push back)
            peer_b_from_c = await transport_c.get_peer("lww-B")
            pushed = await store_c.push_operations(peer_b_from_c)
            assert pushed, "LWW push C→B failed"
            await asyncio.sleep(0.3)

            peer_a_from_b = await transport_b.get_peer("lww-A")
            pushed = await store_b.push_operations(peer_a_from_b)
            assert pushed, "LWW push B→A failed"
            await asyncio.sleep(0.3)

            # All nodes converged to "C-data"
            for node_name, store in [("A", store_a), ("B", store_b), ("C", store_c)]:
                reg = store.get_crdt(register_id)
                assert reg is not None, f"Register not found on {node_name}"
                assert reg.get() == "C-data", \
                    f"Node {node_name} expected 'C-data', got {reg.get()}"

        finally:
            await store_a.stop()
            await store_b.stop()
            await store_c.stop()
            await dht_a.stop()
            await dht_b.stop()
            await dht_c.stop()
            await transport_a.stop()
            await transport_b.stop()
            await transport_c.stop()


# ═══════════════════════════════════════════════════════════════════════════
# Test: create_local_node_set() Helper Factory
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateLocalNodeSet:
    """Validate the create_local_node_set() helper function."""

    @pytest.mark.asyncio
    async def test_create_three_nodes(self):
        """create_local_node_set(3) creates 3 pre-wired LocalNode objects."""
        from mesh.p2p_integration import create_local_node_set

        nodes = create_local_node_set(num_nodes=3, base_port=23500)

        assert len(nodes) == 3, f"Expected 3 nodes, got {len(nodes)}"

        for i, node in enumerate(nodes):
            assert node.node_id == f"local-node-{i}"
            assert node.host == "127.0.0.1"
            assert node.port_udp == 23500 + (i * 2)
            assert node.port_ws == 23500 + (i * 2) + 1
            assert node.transport is not None
            assert node.dht is not None
            assert node.crdt is not None
            assert node.integration is not None

        # Verify DHT routing tables are pre-wired
        for i, src in enumerate(nodes):
            for j, dst in enumerate(nodes):
                if i == j:
                    continue
                found = src.dht.find_node(
                    type(dst.dht.node_id).from_string(dst.node_id)
                )
                assert found is not None, \
                    f"Node {i} missing DHT entry for Node {j}"

    @pytest.mark.asyncio
    async def test_create_local_node_set_start_stop(self):
        """LocalNode.start() and .stop() lifecycle works cleanly."""
        from mesh.p2p_integration import create_local_node_set

        nodes = create_local_node_set(num_nodes=2, base_port=23600)

        try:
            # Start all nodes
            for node in nodes:
                await node.start()

            # Verify they started
            for node in nodes:
                assert node.transport._running, \
                    f"{node.node_id} transport not running"
                assert node.integration._running, \
                    f"{node.node_id} integration not running"
        finally:
            # Stop in reverse order
            for node in reversed(nodes):
                await node.stop()

    @pytest.mark.asyncio
    async def test_local_node_set_crdt_sync(self):
        """Two LocalNodes created via helper can sync CRDT data."""
        from mesh.p2p_integration import create_local_node_set

        nodes = create_local_node_set(num_nodes=2, base_port=23700)

        try:
            for node in nodes:
                await node.start()

            # Add transport-level peers (helper pre-wires DHT only)
            await nodes[0].transport.add_peer(
                nodes[1].node_id,
                nodes[1].host,
                nodes[1].port_udp,
                nodes[1].port_ws,
            )
            await nodes[1].transport.add_peer(
                nodes[0].node_id,
                nodes[0].host,
                nodes[0].port_udp,
                nodes[0].port_ws,
            )

            await asyncio.sleep(0.5)

            # Create GCounter on node 0
            counter = nodes[0].crdt.create_g_counter("helper-counter")
            counter.increment(nodes[0].node_id, 99)

            # Push to node 1
            peer_1 = await nodes[0].transport.get_peer(nodes[1].node_id)
            assert peer_1 is not None, "Peer node-1 not found on node-0"

            pushed = await nodes[0].crdt.push_operations(peer_1)
            assert pushed, "Push from node-0 to node-1 failed"
            await asyncio.sleep(0.3)

            # Verify node 1 has the data (counter was created by apply_sync_state during push)
            c1 = nodes[1].crdt.get_crdt("helper-counter")
            assert c1 is not None, "Counter not found on node-1"
            assert c1.value() == 99, \
                f"Node-1 expected 99, got {c1.value()}"

        finally:
            for node in reversed(nodes):
                await node.stop()
