"""
STATUS: REAL — Unit tests for P2P transport layer
ASIMNEXUS P2P Transport Tests
==============================
Tests for p2p_transport.py, kademlia_dht.py RPC integration,
crdt_sync.py WebSocket integration, and nat_traversal.py.
"""

import unittest
import sys
import os
import json
import time
import struct
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from p2p_transport import (
    P2PMessage, PeerInfo, P2PTransport,
    RPCMessageType, WSMessageType,
    P2P_MAGIC, P2P_VERSION,
    ConnectionState,
    get_p2p_transport, reset_p2p_transport,
)


# ---------------------------------------------------------------------------
# P2PMessage serialization tests
# ---------------------------------------------------------------------------

class TestP2PMessage(unittest.TestCase):
    """Test P2PMessage binary serialization/deserialization."""

    def setUp(self):
        self.msg = P2PMessage(
            msg_type=RPCMessageType.PING.value,
            sender_id="test_node",
            msg_id="msg_001",
            payload={"hello": "world"},
            timestamp=1000.0,
            ttl=3,
        )

    def test_to_bytes_contains_magic(self):
        """Binary format must start with ASIM magic header."""
        data = self.msg.to_bytes()
        self.assertEqual(data[:4], P2P_MAGIC)

    def test_to_bytes_has_version(self):
        """Binary format must have version byte after magic."""
        data = self.msg.to_bytes()
        self.assertEqual(data[4], P2P_VERSION)

    def test_to_bytes_has_length_prefix(self):
        """Binary format must have 4-byte body length."""
        data = self.msg.to_bytes()
        body_len = struct.unpack("!I", data[5:9])[0]
        self.assertEqual(body_len, len(data) - 9)

    def test_roundtrip(self):
        """to_bytes() then from_bytes() must produce identical message."""
        data = self.msg.to_bytes()
        restored = P2PMessage.from_bytes(data)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.msg_type, self.msg.msg_type)
        self.assertEqual(restored.sender_id, self.msg.sender_id)
        self.assertEqual(restored.msg_id, self.msg.msg_id)
        self.assertEqual(restored.payload, self.msg.payload)
        self.assertEqual(restored.ttl, self.msg.ttl)

    def test_from_bytes_invalid_short(self):
        """Messages shorter than 7 bytes must return None."""
        self.assertIsNone(P2PMessage.from_bytes(b""))

    def test_from_bytes_invalid_magic(self):
        """Messages without correct magic must return None."""
        data = b"FAKE" + struct.pack("!BH", 1, 5) + b"hello"
        self.assertIsNone(P2PMessage.from_bytes(data))

    def test_from_bytes_invalid_json(self):
        """Messages with invalid JSON body must return None."""
        data = P2P_MAGIC + struct.pack("!BH", 1, 5) + b"NOT_JSON"
        self.assertIsNone(P2PMessage.from_bytes(data))


# ---------------------------------------------------------------------------
# PeerInfo tests
# ---------------------------------------------------------------------------

class TestPeerInfo(unittest.TestCase):
    """Test PeerInfo stale/bad detection."""

    def setUp(self):
        self.peer = PeerInfo(
            node_id="peer_1",
            host="192.168.1.10",
            port_udp=7332,
            port_ws=7333,
        )

    def test_is_stale_fresh(self):
        """Freshly created peer must not be stale."""
        self.assertFalse(self.peer.is_stale(max_age=300.0))

    def test_is_stale_expired(self):
        """Peer with old last_seen must be stale."""
        self.peer.last_seen = time.time() - 600
        self.assertTrue(self.peer.is_stale(max_age=300.0))

    def test_is_bad_zero_failures(self):
        """Peer with no failures must not be bad."""
        self.assertFalse(self.peer.is_bad(max_failures=3))

    def test_is_bad_max_failures(self):
        """Peer with >= max_failures must be bad."""
        self.peer.consecutive_failures = 5
        self.assertTrue(self.peer.is_bad(max_failures=3))


# ---------------------------------------------------------------------------
# P2PTransport lifecycle and peer management tests
# ---------------------------------------------------------------------------

class TestP2PTransport(unittest.TestCase):
    """Test P2PTransport peer management and handler registration."""

    def setUp(self):
        self.transport = P2PTransport(
            node_id="test_node",
            host="127.0.0.1",
            port_udp=19332,  # Use non-standard ports to avoid conflicts
            port_ws=19333,
        )

    def tearDown(self):
        reset_p2p_transport()

    def _run_async(self, coro):
        """Helper to run async methods synchronously."""
        return asyncio.run(coro)

    def test_add_peer(self):
        """add_peer must register and return a PeerInfo."""
        peer = self._run_async(
            self.transport.add_peer("peer_1", "192.168.1.10", 7332, 7333)
        )
        self.assertIsNotNone(peer)
        self.assertEqual(peer.node_id, "peer_1")
        self.assertEqual(peer.host, "192.168.1.10")
        self.assertIn("peer_1", self.transport.peers)

    def test_add_peer_updates_existing(self):
        """add_peer on existing node_id must update host/port."""
        self._run_async(
            self.transport.add_peer("peer_1", "192.168.1.10", 7332, 7333)
        )
        updated = self._run_async(
            self.transport.add_peer("peer_1", "10.0.0.1", 8332, 8333)
        )
        self.assertEqual(updated.host, "10.0.0.1")
        self.assertEqual(updated.port_udp, 8332)

    def test_remove_peer(self):
        """remove_peer must remove from peers dict."""
        self._run_async(
            self.transport.add_peer("peer_1", "192.168.1.10", 7332, 7333)
        )
        self._run_async(self.transport.remove_peer("peer_1"))
        self.assertNotIn("peer_1", self.transport.peers)

    def test_get_peer(self):
        """get_peer must return None for unknown peer."""
        result = self._run_async(self.transport.get_peer("nonexistent"))
        self.assertIsNone(result)

    def test_get_online_peers(self):
        """get_online_peers must only return connected, non-bad peers."""
        self._run_async(
            self.transport.add_peer("peer_1", "192.168.1.10", 7332, 7333)
        )
        self._run_async(
            self.transport.add_peer("peer_2", "192.168.1.11", 7332, 7333)
        )
        self._run_async(
            self.transport.add_peer("peer_3", "192.168.1.12", 7332, 7333)
        )

        # Mark peer_1 as connected
        self.transport.peers["peer_1"].connection_state = ConnectionState.CONNECTED
        # Mark peer_2 as connected but bad
        self.transport.peers["peer_2"].connection_state = ConnectionState.CONNECTED
        self.transport.peers["peer_2"].consecutive_failures = 5

        online = self._run_async(self.transport.get_online_peers())
        self.assertEqual(len(online), 1)
        self.assertEqual(online[0].node_id, "peer_1")

    def test_next_msg_id_unique(self):
        """_next_msg_id must generate unique IDs."""
        ids = {self.transport._next_msg_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_on_rpc_registration(self):
        """on_rpc must register handler in _rpc_handlers."""
        async def handler(msg):
            return None
        self.transport.on_rpc("ping", handler)
        self.assertIn("ping", self.transport._rpc_handlers)

    def test_on_ws_message_registration(self):
        """on_ws_message must register handler in _ws_handlers."""
        async def handler(msg):
            pass
        self.transport.on_ws_message("sync_request", handler)
        self.assertIn("sync_request", self.transport._ws_handlers)


# ---------------------------------------------------------------------------
# RPC call flow tests (mocked UDP)
# ---------------------------------------------------------------------------

class TestP2PTransportRPC(unittest.IsolatedAsyncioTestCase):
    """Test RPC call/response matching with mocked UDP transport."""

    async def asyncSetUp(self):
        self.transport = P2PTransport(
            node_id="test_node",
            host="127.0.0.1",
            port_udp=19334,
            port_ws=19335,
        )
        self.peer = await self.transport.add_peer(
            "peer_1", "127.0.0.1", 19334, 19335
        )
        self.peer.connection_state = ConnectionState.CONNECTED

    async def asyncTearDown(self):
        reset_p2p_transport()

    async def test_rpc_call_response_matching(self):
        """
        rpc_call must match response by msg_id.
        Simulate: send PING -> receive PONG with same msg_id.
        """
        # Mock send_udp to succeed
        self.transport.send_udp = AsyncMock(return_value=True)

        # Simulate a delayed PONG response
        async def simulate_pong():
            await asyncio.sleep(0.05)
            # Find the expected response handler and call it
            expected_type = RPCMessageType.PONG.value
            handler = self.transport._rpc_handlers.get(expected_type)
            if handler:
                # Create a response with the correct msg_id from pending_rpcs
                response_msg = P2PMessage(
                    msg_type=RPCMessageType.PONG.value,
                    sender_id="peer_1",
                    msg_id=list(self.transport._pending_rpcs.keys())[0],
                    payload={"echo": {"hello": "world"}},
                )
                await handler(response_msg)

        # Start simulation in background
        asyncio.create_task(simulate_pong())

        # Call rpc
        result = await self.transport.rpc_call(
            self.peer,
            RPCMessageType.PING.value,
            {"hello": "world"},
            timeout=2.0,
        )

        # Should receive the PONG response
        self.assertIsNotNone(result)
        self.assertEqual(result.msg_type, RPCMessageType.PONG.value)
        self.assertEqual(result.payload, {"echo": {"hello": "world"}})

    async def test_rpc_call_timeout(self):
        """rpc_call must return None on timeout."""
        self.transport.send_udp = AsyncMock(return_value=True)

        result = await self.transport.rpc_call(
            self.peer,
            RPCMessageType.FIND_NODE.value,
            {"target": "abc123"},
            timeout=0.1,
        )

        self.assertIsNone(result)

    async def test_rpc_call_send_failure(self):
        """rpc_call must return None if UDP send fails."""
        self.transport.send_udp = AsyncMock(return_value=False)

        result = await self.transport.rpc_call(
            self.peer,
            RPCMessageType.PING.value,
            {},
            timeout=1.0,
        )

        self.assertIsNone(result)

    async def test_rpc_handler_cleanup(self):
        """One-shot response handler must be removed after timeout."""
        self.transport.send_udp = AsyncMock(return_value=True)

        expected_type = RPCMessageType.PONG.value
        self.assertNotIn(expected_type, self.transport._rpc_handlers)

        await self.transport.rpc_call(
            self.peer,
            RPCMessageType.PING.value,
            {},
            timeout=0.1,
        )

        # After timeout, handler must be cleaned up
        self.assertNotIn(expected_type, self.transport._rpc_handlers)


# ---------------------------------------------------------------------------
# Global singleton tests
# ---------------------------------------------------------------------------

class TestGlobalSingleton(unittest.TestCase):
    """Test get_p2p_transport / reset_p2p_transport."""

    def tearDown(self):
        reset_p2p_transport()

    def test_get_or_create(self):
        """get_p2p_transport must create singleton on first call."""
        t1 = get_p2p_transport(node_id="singleton_test", port_udp=19336, port_ws=19337)
        t2 = get_p2p_transport()
        self.assertIs(t1, t2)
        self.assertEqual(t2.node_id, "singleton_test")

    def test_reset(self):
        """reset_p2p_transport must clear singleton."""
        t1 = get_p2p_transport(node_id="reset_test", port_udp=19338, port_ws=19339)
        reset_p2p_transport()
        t2 = get_p2p_transport(node_id="new_instance", port_udp=19338, port_ws=19339)
        self.assertIsNot(t1, t2)


# ---------------------------------------------------------------------------
# WebSocket broadcast tests (mocked connections)
# ---------------------------------------------------------------------------

class TestP2PTransportWS(unittest.IsolatedAsyncioTestCase):
    """Test WebSocket send/broadcast with mocked connections."""

    async def asyncSetUp(self):
        self.transport = P2PTransport(
            node_id="ws_test_node",
            host="127.0.0.1",
            port_udp=19340,
            port_ws=19341,
        )
        # Add two online peers
        self.peer1 = await self.transport.add_peer("p1", "127.0.0.1", 19340, 19341)
        self.peer1.connection_state = ConnectionState.CONNECTED
        self.peer2 = await self.transport.add_peer("p2", "127.0.0.2", 19340, 19341)
        self.peer2.connection_state = ConnectionState.CONNECTED

    async def asyncTearDown(self):
        reset_p2p_transport()

    async def test_send_ws_failure(self):
        """send_ws must return False when connection fails."""
        # No server listening — should fail fast
        msg = P2PMessage(
            msg_type=WSMessageType.PEER_HELLO.value,
            sender_id="ws_test_node",
            msg_id="hello_001",
        )
        result = await self.transport.send_ws(self.peer1, msg)
        self.assertFalse(result)
        # ping_failures should increment on failure
        self.assertGreater(self.peer1.ping_failures, 0)

    async def test_broadcast_ws(self):
        """broadcast_ws must attempt sending to all online peers."""
        msg = P2PMessage(
            msg_type=WSMessageType.PEER_HELLO.value,
            sender_id="ws_test_node",
            msg_id="bcast_001",
        )
        # No server listening — should fail for both
        count = await self.transport.broadcast_ws(msg)
        self.assertEqual(count, 0)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
