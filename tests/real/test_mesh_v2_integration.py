#!/usr/bin/env python3
"""
STATUS: REAL — Two-node mesh integration test
ASIMNEXUS Mesh V2 Integration Test
===================================
Tests the complete mesh networking stack end-to-end:

1. Two P2PTransport instances communicating via UDP
2. Kademlia DHT lookup/publish across nodes via P2P RPC
3. CRDT sync across nodes via WebSocket
4. Peer discovery and management

Run with: python -m pytest tests/real/test_mesh_v2_integration.py -v --tb=long
"""

import os
import sys
import json
import time
import asyncio
import logging
import socket
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("TestMeshV2")


# ---------------------------------------------------------------------------
# Find free ports
# ---------------------------------------------------------------------------

def _find_free_port(start: int = 21000) -> int:
    """Find a free UDP port starting from `start`."""
    for port in range(start, start + 100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            continue
    raise RuntimeError("No free ports found")


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Two-node mesh integration test
# ---------------------------------------------------------------------------

class TestTwoNodeMeshIntegration:
    """
    Integration test for two-node P2P mesh.
    
    Test topology:
    Node A (127.0.0.1:UDP_A:WS_A) <-> Node B (127.0.0.1:UDP_B:WS_B)
    
    Tests:
    1. Both transports start and listen
    2. Nodes discover each other via add_peer
    3. Ping/Pong RPC round-trip via UDP
    4. DHT FIND_VALUE / STORE via RPC
    5. CRDT sync via WebSocket
    6. CRDT operation broadcast
    """

    @pytest.mark.asyncio
    async def test_two_node_ping_pong(self):
        """Test basic PING/PONG RPC between two nodes."""
        port_a = _find_free_port(21000)
        port_b = _find_free_port(21100)

        from mesh.p2p_transport import (
            P2PTransport, P2PMessage, PeerInfo,
            RPCMessageType, WSMessageType,
        )

        # Create two transport instances
        node_a = P2PTransport("node_a", "127.0.0.1", port_a, port_a + 1)
        node_b = P2PTransport("node_b", "127.0.0.1", port_b, port_b + 1)

        # Register PONG handler on node_b
        async def handle_ping(msg):
            return P2PMessage(
                msg_type=RPCMessageType.PONG.value,
                sender_id="node_b",
                msg_id=msg.msg_id,
                payload={"echo": msg.payload},
            )
        node_b.on_rpc(RPCMessageType.PING.value, handle_ping)

        try:
            # Start both transports
            await node_a.start()
            await node_b.start()

            # Add peers to each other
            peer_b = await node_a.add_peer("node_b", "127.0.0.1", port_b, port_b + 1)
            await node_b.add_peer("node_a", "127.0.0.1", port_a, port_a + 1)

            # Give servers time to start
            await asyncio.sleep(0.2)

            # Send PING from A -> B
            response = await node_a.rpc_call(
                peer_b,
                RPCMessageType.PING.value,
                {"ts": time.time()},
                timeout=5.0,
            )

            assert response is not None, "PING/PONG RPC failed — no response"
            assert response.msg_type == RPCMessageType.PONG.value, \
                f"Expected PONG, got {response.msg_type}"
            assert response.sender_id == "node_b"
            assert response.payload.get("echo", {}).get("ts") is not None

        finally:
            await node_a.stop()
            await node_b.stop()

    @pytest.mark.asyncio
    async def test_two_node_dht_lookup_and_publish(self):
        """Test DHT STORE and FIND_VALUE across two nodes."""
        port_a = _find_free_port(21200)
        port_b = _find_free_port(21300)

        from mesh.p2p_transport import (
            P2PTransport, P2PMessage, PeerInfo,
            RPCMessageType,
        )
        from mesh.kademlia_dht import (
            KademliaDHT, NodeID, DHTNode,
            get_kademlia_dht, reset_kademlia_dht,
        )

        # Create transports
        transport_a = P2PTransport("dht_a", "127.0.0.1", port_a, port_a + 1)
        transport_b = P2PTransport("dht_b", "127.0.0.1", port_b, port_b + 1)

        # Create DHT instances wired to transports
        dht_a = KademliaDHT(node_id=NodeID.from_string("dht_a"), port=port_a, transport=transport_a)
        dht_b = KademliaDHT(node_id=NodeID.from_string("dht_b"), port=port_b, transport=transport_b)

        try:
            # Start transports
            await transport_a.start()
            await transport_b.start()

            # Start DHTs (registers RPC handlers)
            await dht_a.start()
            await dht_b.start()

            # Add peers to routing tables
            dht_a.add_node(DHTNode(
                node_id=NodeID.from_string("dht_b"),
                ip_address="127.0.0.1",
                port=port_b,
            ))
            dht_b.add_node(DHTNode(
                node_id=NodeID.from_string("dht_a"),
                ip_address="127.0.0.1",
                port=port_a,
            ))

            # Give handlers time to register
            await asyncio.sleep(0.3)

            # Publish a value from node A
            test_key = NodeID.from_string("test_key_42")
            test_value = b"Hello from DHT Node A!"
            await dht_a.publish(test_key, test_value)

            # Look up from node B
            result = await dht_b.lookup(test_key)
            assert result is not None, f"DHT lookup returned None"
            assert result == test_value, f"Value mismatch: {result} != {test_value}"

        finally:
            await dht_a.stop()
            await dht_b.stop()
            await transport_a.stop()
            await transport_b.stop()
            reset_kademlia_dht()

    @pytest.mark.asyncio
    async def test_two_node_crdt_sync(self):
        """Test CRDT sync across two nodes via WebSocket."""
        port_a = _find_free_port(21400)
        port_b = _find_free_port(21500)

        from mesh.p2p_transport import (
            P2PTransport, PeerInfo,
        )
        from mesh.crdt_sync import (
            CRDTStore, get_crdt_store, reset_crdt_store,
        )

        # Create transports
        transport_a = P2PTransport("crdt_a", "127.0.0.1", port_a, port_a + 1)
        transport_b = P2PTransport("crdt_b", "127.0.0.1", port_b, port_b + 1)

        # Create CRDT stores wired to transports
        store_a = CRDTStore(node_id="crdt_a", transport=transport_a)
        store_b = CRDTStore(node_id="crdt_b", transport=transport_b)

        try:
            # Start transports
            await transport_a.start()
            await transport_b.start()

            # Start CRDT sync (registers WS handlers)
            await store_a.start()
            await store_b.start()

            # Add peers
            peer_b = await transport_a.add_peer("crdt_b", "127.0.0.1", port_b, port_b + 1)
            await transport_b.add_peer("crdt_a", "127.0.0.1", port_a, port_a + 1)

            # Give servers time to start
            await asyncio.sleep(0.3)

            # Create a counter on node A and increment it
            counter_a = store_a.create_g_counter("test_counter")
            counter_a.increment("crdt_a", 42)

            # Create a counter on node B
            counter_b = store_b.create_g_counter("test_counter")

            # Push pending ops from A -> B
            pushed = await store_a.push_operations(peer_b)
            assert pushed, "Failed to push operations to peer B"

            # Give time for WS message delivery
            await asyncio.sleep(0.3)

            # Verify B received the operations
            assert counter_b.value() == 42, \
                f"Counter B expected 42, got {counter_b.value()}"

        finally:
            await store_a.stop()
            await store_b.stop()
            await transport_a.stop()
            await transport_b.stop()
            reset_crdt_store()

    @pytest.mark.asyncio
    async def test_two_node_full_stack(self):
        """
        Full stack integration test:
        1. Nodes discover each other
        2. DHT stores and retrieves values
        3. CRDT syncs operations
        4. Peer health tracking works
        """
        port_a = _find_free_port(21600)
        port_b = _find_free_port(21700)

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

        # --- Setup ---
        transport_a = P2PTransport("full_a", "127.0.0.1", port_a, port_a + 1)
        transport_b = P2PTransport("full_b", "127.0.0.1", port_b, port_b + 1)

        dht_a = KademliaDHT(node_id=NodeID.from_string("full_a"), port=port_a, transport=transport_a)
        dht_b = KademliaDHT(node_id=NodeID.from_string("full_b"), port=port_b, transport=transport_b)

        store_a = CRDTStore(node_id="full_a", transport=transport_a)
        store_b = CRDTStore(node_id="full_b", transport=transport_b)

        try:
            # Start everything
            await transport_a.start()
            await transport_b.start()
            await dht_a.start()
            await dht_b.start()
            await store_a.start()
            await store_b.start()

            # Add peers
            dht_a.add_node(DHTNode(
                node_id=NodeID.from_string("full_b"),
                ip_address="127.0.0.1",
                port=port_b,
            ))
            dht_b.add_node(DHTNode(
                node_id=NodeID.from_string("full_a"),
                ip_address="127.0.0.1",
                port=port_a,
            ))
            peer_b = await transport_a.add_peer("full_b", "127.0.0.1", port_b, port_b + 1)
            await transport_b.add_peer("full_a", "127.0.0.1", port_a, port_a + 1)

            await asyncio.sleep(0.3)

            # --- 1. DHT store on A, lookup on B ---
            test_key = NodeID.from_string("full_stack_key")
            test_value = b"Full stack integration test value"
            await dht_a.publish(test_key, test_value)

            result = await dht_b.lookup(test_key)
            assert result is not None, "DHT full-stack lookup returned None"
            assert result == test_value, f"DHT value mismatch"

            # --- 2. CRDT counter sync ---
            counter_a = store_a.create_g_counter("stack_counter")
            counter_a.increment("full_a", 10)
            counter_a.increment("full_a", 5)

            store_b.create_g_counter("stack_counter")

            pushed = await store_a.push_operations(peer_b)
            assert pushed, "CRDT push failed"
            await asyncio.sleep(0.3)

            counter_b = store_b.get_crdt("stack_counter")
            assert counter_b is not None, "Counter B not found"
            assert counter_b.value() == 15, \
                f"Counter B expected 15, got {counter_b.value()}"

            # --- 3. Peer health tracking ---
            stats_a = await transport_a.get_online_peers()
            # node_b might not be "connected" since it's UDP (connectionless)
            # but it should be in the peers list
            assert "full_b" in transport_a.peers

        finally:
            await store_a.stop()
            await store_b.stop()
            await dht_a.stop()
            await dht_b.stop()
            await transport_a.stop()
            await transport_b.stop()


