#!/usr/bin/env python3
"""
REAL test: Mesh NAT Traversal (Phase 1B)
=========================================
Tests STUN/TURN, hole punching, and relay services with real asyncio.

Coverage:
- STUNClient async query lifecycle
- NATDetector initialisation and classification mapping
- TURNClient allocate request (will timeout — no real TURN server)
- RendezvousServer start/stop/message handling
- RendezvousClient register/query/punch-request
- HolePuncher initialisation (with and without P2PTransport)
- PunchSession state tracking and strategy selection
- send_udp_to transport integration
- RelayService start/stop/session lifecycle
- Transport-aware relay_data forwarding
"""

import os
import sys
import json
import time
import asyncio
import logging
import socket
from typing import Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest

from mesh.stun_turn import (
    STUNClient,
    NATDetector,
    TURNClient,
    NATClassification,
    NATType,
    MappedAddress,
    ConnectionStrategy,
    select_connection_strategy,
    get_stun_client,
    get_nat_detector,
    reset_stun_turn,
)
from mesh.hole_punching import (
    HolePuncher,
    PunchSession,
    PunchEndpoint,
    PunchStatus,
    RendezvousServer,
    RendezvousClient,
    RendezvousMessageType,
    PunchListener,
    get_hole_puncher,
    reset_hole_puncher,
)
from mesh.relay import (
    RelayService,
    RelayRole,
    RelaySession,
    RelayStatus,
    get_relay_service,
    reset_relay_service,
)
from mesh.p2p_transport import (
    P2PTransport,
    P2PMessage,
    ConnectionState,
    get_p2p_transport,
    reset_p2p_transport,
)
from mesh.nat_traversal import (
    NATDetector as NATraversalDetector,
    NATTraversal,
    NATType as NATraversalNATType,
)

logger = logging.getLogger("TestMeshNAT")
logger.setLevel(logging.DEBUG)


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


# ---------------------------------------------------------------------------
# Test: STUNClient
# ---------------------------------------------------------------------------

class TestSTUNClient:
    """STUN client lifecycle and query handling."""

    @pytest.mark.asyncio
    async def test_create_stun_client(self):
        """A STUNClient can be created with default params."""
        client = STUNClient(timeout=2.0)
        assert client.timeout == 2.0
        assert client.transport_port is None

    @pytest.mark.asyncio
    async def test_create_stun_client_with_transport_port(self):
        """STUNClient accepts transport_port for consistent NAT mapping."""
        client = STUNClient(timeout=2.0, transport_port=54321)
        assert client.transport_port == 54321

    @pytest.mark.asyncio
    async def test_stun_query_to_nowhere_returns_none(self):
        """Querying a non-existent STUN server returns None (timeout)."""
        client = STUNClient(timeout=1.0)
        result = await client.query("127.0.0.1:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_stun_query_multiple_empty(self):
        """query_multiple returns None when no servers respond."""
        client = STUNClient(timeout=1.0)
        results = await client.query_multiple(["127.0.0.1:9999", "127.0.0.1:9998"])
        assert results is None

    @pytest.mark.asyncio
    async def test_get_stun_client_singleton(self):
        """Singleton accessor returns same instance."""
        reset_stun_turn()
        c1 = get_stun_client(transport_port=12345)
        c2 = get_stun_client()
        assert c1 is c2
        assert c1.transport_port == 12345  # first-wins
        reset_stun_turn()

    @pytest.mark.asyncio
    async def test_get_stun_client_transport_port(self):
        """Singleton respects first transport_port."""
        reset_stun_turn()
        c1 = get_stun_client(transport_port=11111)
        assert c1.transport_port == 11111
        reset_stun_turn()


# ---------------------------------------------------------------------------
# Test: NATDetector
# ---------------------------------------------------------------------------

class TestNATDetector:
    """NAT detector initialisation and classification mapping."""

    @pytest.mark.asyncio
    async def test_create_nat_detector(self):
        """NATDetector can be created without STUN servers responding."""
        detector = NATDetector(timeout=1.0)
        assert detector.timeout == 1.0

    @pytest.mark.asyncio
    async def test_classify_when_no_stun_returns_blocked(self):
        """When no STUN servers respond, classify returns UDP_BLOCKED."""
        # Override servers to non-existent ones
        detector = NATDetector(timeout=0.5)
        # Patch the STUN servers list temporarily
        from mesh import stun_turn as st
        original_servers = st._STUN_SERVERS
        try:
            st._STUN_SERVERS = ["127.0.0.1:9999", "127.0.0.1:9998", "127.0.0.1:9997"]
            result = await detector.classify()
            assert isinstance(result, NATClassification)
            assert result.nat_type == NATType.UDP_BLOCKED
            assert result.public_address is None
        finally:
            st._STUN_SERVERS = original_servers

    @pytest.mark.asyncio
    async def test_classify_requires_stun_servers(self):
        """classify() completes even with all timeouts (no crash)."""
        detector = NATDetector(timeout=0.3)
        from mesh import stun_turn as st
        original_servers = st._STUN_SERVERS
        try:
            st._STUN_SERVERS = ["127.0.0.1:19999", "127.0.0.1:19998", "127.0.0.1:19997"]
            result = await detector.classify()
            assert result.nat_type in (NATType.UNKNOWN, NATType.UDP_BLOCKED)
        finally:
            st._STUN_SERVERS = original_servers

    @pytest.mark.asyncio
    async def test_nat_classification_properties(self):
        """hole_punchable and requires_relay properties work."""
        # OPEN_INTERNET -> hole_punchable
        c1 = NATClassification(
            nat_type=NATType.OPEN_INTERNET,
            public_address=MappedAddress(ip_address="1.2.3.4", port=12345),
        )
        assert c1.is_hole_punchable is True
        assert c1.requires_relay is False

        # SYMMETRIC -> requires relay
        c2 = NATClassification(
            nat_type=NATType.SYMMETRIC,
            public_address=MappedAddress(ip_address="1.2.3.4", port=12345),
        )
        assert c2.is_hole_punchable is False
        assert c2.requires_relay is True

        # UDP_BLOCKED -> requires relay
        c3 = NATClassification(
            nat_type=NATType.UDP_BLOCKED,
            public_address=None,
        )
        assert c3.is_hole_punchable is False
        assert c3.requires_relay is True

    @pytest.mark.asyncio
    async def test_get_nat_detector_singleton(self):
        """Singleton accessor returns same instance."""
        reset_stun_turn()
        d1 = get_nat_detector()
        d2 = get_nat_detector()
        assert d1 is d2
        reset_stun_turn()


# ---------------------------------------------------------------------------
# Test: ConnectionStrategy Selection
# ---------------------------------------------------------------------------

class TestConnectionStrategy:
    """Strategy selection based on NAT types."""

    def test_direct_both_public(self):
        """Both peers on public internet -> DIRECT."""
        local = NATClassification(
            nat_type=NATType.OPEN_INTERNET,
            public_address=MappedAddress("1.2.3.4", 12345),
        )
        remote = NATClassification(
            nat_type=NATType.OPEN_INTERNET,
            public_address=MappedAddress("5.6.7.8", 54321),
        )
        strategy = select_connection_strategy(local, remote)
        assert strategy == ConnectionStrategy.DIRECT

    def test_stun_punch_cone_to_cone(self):
        """Both peers behind full/restricted cone NAT -> STUN_PUNCH."""
        local = NATClassification(
            nat_type=NATType.FULL_CONE,
            public_address=MappedAddress("1.2.3.4", 12345),
        )
        remote = NATClassification(
            nat_type=NATType.RESTRICTED_CONE,
            public_address=MappedAddress("5.6.7.8", 54321),
        )
        strategy = select_connection_strategy(local, remote)
        assert strategy == ConnectionStrategy.STUN_PUNCH

    def test_stun_punch_port_restricted_cone(self):
        """Port-restricted cone + restricted cone -> STUN_PUNCH (both hole-punchable)."""
        local = NATClassification(
            nat_type=NATType.PORT_RESTRICTED_CONE,
            public_address=MappedAddress("1.2.3.4", 12345),
        )
        remote = NATClassification(
            nat_type=NATType.RESTRICTED_CONE,
            public_address=MappedAddress("5.6.7.8", 54321),
        )
        strategy = select_connection_strategy(local, remote)
        assert strategy == ConnectionStrategy.STUN_PUNCH

    def test_rendezvous_symmetric_cone(self):
        """Symmetric + full cone -> RENDEZVOUS (port prediction may work)."""
        local = NATClassification(
            nat_type=NATType.SYMMETRIC,
            public_address=MappedAddress("1.2.3.4", 12345),
        )
        remote = NATClassification(
            nat_type=NATType.FULL_CONE,
            public_address=MappedAddress("5.6.7.8", 54321),
        )
        strategy = select_connection_strategy(local, remote)
        assert strategy == ConnectionStrategy.RENDEZVOUS

    def test_relay_when_udp_blocked(self):
        """If either peer is UDP_BLOCKED -> RELAY."""
        local = NATClassification(
            nat_type=NATType.OPEN_INTERNET,
            public_address=MappedAddress("1.2.3.4", 12345),
        )
        remote = NATClassification(
            nat_type=NATType.UDP_BLOCKED,
            public_address=None,
        )
        strategy = select_connection_strategy(local, remote)
        assert strategy == ConnectionStrategy.RELAY

    def test_unknown_falls_to_rendezvous(self):
        """Both UNKNOWN -> RENDEZVOUS."""
        local = NATClassification(
            nat_type=NATType.UNKNOWN,
            public_address=None,
        )
        remote = NATClassification(
            nat_type=NATType.UNKNOWN,
            public_address=None,
        )
        strategy = select_connection_strategy(local, remote)
        assert strategy == ConnectionStrategy.RENDEZVOUS


# ---------------------------------------------------------------------------
# Test: RendezvousServer
# ---------------------------------------------------------------------------

class TestRendezvousServer:
    """Rendezvous server lifecycle and message handling."""

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """RendezvousServer can be started and stopped without errors."""
        server = RendezvousServer(host="127.0.0.1", port=0)
        await server.start()
        assert server._running
        assert server._server is not None  # stored as _server, not _transport
        assert server.port > 0

        await server.stop()
        assert not server._running
        # After close(), _server is still set but closed

    @pytest.mark.asyncio
    async def test_register_and_query_peer(self):
        """A peer can register, then another can query for it."""
        server = RendezvousServer(host="127.0.0.1", port=0)
        await server.start()

        try:
            # Register peer-1 — message format: [REGISTER_TYPE] + JSON payload
            reg_data = json.dumps({
                "type": "register",
                "node_id": "peer-1",
                "public_addr": {"ip": "10.0.0.1", "port": 9001},
                "local_addr": {"ip": "192.168.1.1", "port": 9001},
                "nat_type": "full_cone",
            }).encode("utf-8")
            reg_payload = bytes([RendezvousMessageType.REGISTER.value]) + reg_data
            resp_data = await server.handle_message(reg_payload, ("10.0.0.1", 9001))
            assert resp_data is not None
            assert resp_data[0] == RendezvousMessageType.REGISTER_ACK.value
            resp = json.loads(resp_data[1:].decode("utf-8"))
            assert resp.get("status") == "ok"

            # Query peer-1 — message format: [QUERY_TYPE] + JSON payload
            query_data = json.dumps({
                "target_id": "peer-1",
            }).encode("utf-8")
            query_payload = bytes([RendezvousMessageType.QUERY_PEER.value]) + query_data
            resp_data = await server.handle_message(query_payload, ("10.0.0.2", 9002))
            assert resp_data is not None
            assert resp_data[0] == RendezvousMessageType.QUERY_RESPONSE.value
            resp = json.loads(resp_data[1:].decode("utf-8"))
            assert resp.get("found") is True
            assert resp.get("endpoint") is not None
            assert resp["endpoint"]["public_addr"]["ip"] == "10.0.0.1"

            # Query non-existent peer
            query_payload = bytes([RendezvousMessageType.QUERY_PEER.value]) + query_data.replace(
                b"peer-1", b"ghost"
            )
            resp_data = await server.handle_message(query_payload, ("10.0.0.2", 9002))
            assert resp_data is not None
            assert resp_data[0] == RendezvousMessageType.QUERY_RESPONSE.value
            resp = json.loads(resp_data[1:].decode("utf-8"))
            assert resp.get("found") is False

        finally:
            await server.stop()


# ---------------------------------------------------------------------------
# Test: RendezvousClient
# ---------------------------------------------------------------------------

class TestRendezvousClient:
    """Rendezvous client can register and query via a running server."""

    @pytest.mark.asyncio
    async def test_register_and_query(self):
        """Client registers with server, then another client queries."""
        server = RendezvousServer(host="127.0.0.1", port=0)
        await server.start()
        port = server.port

        try:
            # Client A registers
            client_a = RendezvousClient(
                node_id="client-A",
                rendezvous_addr=("127.0.0.1", port),
            )
            await client_a.start()
            ep_a = PunchEndpoint(
                node_id="client-A",
                public_addr=("10.0.0.1", 9001),
                local_addr=("192.168.1.1", 9001),
            )
            registered = await client_a.register(ep_a)
            assert registered is True

            # Client B queries
            client_b = RendezvousClient(
                node_id="client-B",
                rendezvous_addr=("127.0.0.1", port),
            )
            await client_b.start()
            endpoint = await client_b.query_peer("client-A")
            assert endpoint is not None
            assert endpoint.node_id == "client-A"
            assert endpoint.public_addr == ("10.0.0.1", 9001)

            # Query non-existent
            endpoint = await client_b.query_peer("ghost")
            assert endpoint is None

            await client_a.stop()
            await client_b.stop()
        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_request_punch(self):
        """Client requests a punch coordination."""
        server = RendezvousServer(host="127.0.0.1", port=0)
        await server.start()
        port = server.port

        try:
            # Register peer-1 first with a reachable loopback address
            # so the server's PUNCH_NOTIFY sendto doesn't trigger
            # Windows ICMP WSAENETUNREACH errors
            dummy_port = find_free_port()
            client = RendezvousClient(
                node_id="peer-1",
                rendezvous_addr=("127.0.0.1", port),
            )
            await client.start()
            ep = PunchEndpoint(
                node_id="peer-1",
                public_addr=("127.0.0.1", dummy_port),
            )
            await client.register(ep)

            # Request punch to peer-1
            result = await client.request_punch("peer-1")
            assert result is not None
            assert "target_endpoint" in result
            assert result["target_endpoint"]["public_addr"]["ip"] == "127.0.0.1"
            assert result["target_endpoint"]["public_addr"]["port"] == dummy_port

            # Request punch to non-existent peer
            result = await client.request_punch("ghost")
            assert result is None

            await client.stop()
        finally:
            await server.stop()


# ---------------------------------------------------------------------------
# Test: HolePuncher (without transport — fallback mode)
# ---------------------------------------------------------------------------

class TestHolePuncherNoTransport:
    """HolePuncher initialisation and session tracking (no transport)."""

    @pytest.mark.asyncio
    async def test_create_hole_puncher(self):
        """HolePuncher can be created without a transport."""
        puncher = HolePuncher(node_id="test-puncher")
        assert puncher._node_id == "test-puncher"
        assert puncher._transport is None
        assert len(puncher._sessions) == 0

    @pytest.mark.asyncio
    async def test_initialize_nat_unknown(self):
        """initialize() returns UNKNOWN when no STUN servers respond."""
        from mesh import stun_turn as st
        original_servers = st._STUN_SERVERS
        try:
            st._STUN_SERVERS = ["127.0.0.1:29999", "127.0.0.1:29998", "127.0.0.1:29997"]
            puncher = HolePuncher(node_id="test-nat", local_addr=("127.0.0.1", 0))
            nat = await puncher.initialize()
            assert nat.nat_type in (NATType.UNKNOWN, NATType.UDP_BLOCKED)
            # Second call should return cached result
            nat2 = await puncher.initialize()
            assert nat2 is nat
        finally:
            st._STUN_SERVERS = original_servers

    @pytest.mark.asyncio
    async def test_punch_creates_session(self):
        """Calling punch creates a PunchSession."""
        puncher = HolePuncher(node_id="test-puncher")
        ep = PunchEndpoint(
            node_id="remote-peer",
            public_addr=("10.0.0.2", 9002),
        )
        # Without STUN, the session will fail quickly
        session = await puncher.punch("remote-peer", ep, timeout=2.0)
        assert isinstance(session, PunchSession)
        assert session.peer_id == "remote-peer"

    def test_get_session(self):
        """Sessions can be retrieved by peer ID."""
        puncher = HolePuncher(node_id="test-puncher")
        assert puncher.get_session("nonexistent") is None

    def test_get_established_peers_empty(self):
        """get_established_peers returns empty list initially."""
        puncher = HolePuncher(node_id="test-puncher")
        assert puncher.get_established_peers() == []

    def test_get_stats_empty(self):
        """get_stats returns zeroed stats."""
        puncher = HolePuncher(node_id="test-puncher")
        stats = puncher.get_stats()
        assert stats["total_sessions"] == 0
        assert stats["established"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_send_punch_ack_no_transport(self):
        """send_punch_ack works in fallback mode (no transport)."""
        puncher = HolePuncher(node_id="test-ack")
        # Send to 127.0.0.1:0 — will fail gracefully
        result = await puncher.send_punch_ack(("127.0.0.1", 19999), "ghost-peer")
        # In fallback mode, the session should be created even if send fails
        session = puncher.get_session("ghost-peer")
        assert session is not None
        assert session.status == PunchStatus.ESTABLISHED


# ---------------------------------------------------------------------------
# Test: HolePuncher (with transport — integrated mode)
# ---------------------------------------------------------------------------

class TestHolePuncherWithTransport:
    """HolePuncher integrated with a real P2PTransport."""

    @pytest.mark.asyncio
    async def test_create_with_transport(self):
        """HolePuncher can be created with a transport."""
        port_a = find_free_port()
        transport = P2PTransport(
            node_id="transport-node",
            host="127.0.0.1",
            port_udp=port_a,
            port_ws=find_free_port(),
        )
        await transport.start()

        try:
            puncher = HolePuncher(
                node_id="test-puncher",
                transport=transport,
            )
            assert puncher._transport is transport
            assert transport._punch_handler is not None

            # Verify punch handler is registered
            assert "HOLE_PUNCH" in transport._rpc_handlers
        finally:
            await transport.stop()

    @pytest.mark.asyncio
    async def test_punch_handler_dispatches_to_transport(self):
        """Incoming HOLE_PUNCH messages dispatch through transport's RPC."""
        port_a = find_free_port()
        port_b = find_free_port()

        transport_a = P2PTransport("node-A", "127.0.0.1", port_a, find_free_port())
        transport_b = P2PTransport("node-B", "127.0.0.1", port_b, find_free_port())

        await transport_a.start()
        await transport_b.start()

        try:
            # Add peers to each other's routing tables
            await transport_a.add_peer("node-B", "127.0.0.1", port_b, find_free_port())
            await transport_b.add_peer("node-A", "127.0.0.1", port_a, find_free_port())

            # Create puncher on B
            received_punches = []

            async def on_punch(sender_id, payload):
                received_punches.append((sender_id, payload))

            puncher_b = HolePuncher(
                node_id="node-B",
                transport=transport_b,
            )

            # Send a HOLE_PUNCH message from A to B via UDP
            await transport_a.send_udp_to(
                "127.0.0.1", port_b,
                "HOLE_PUNCH",
                {"punch_type": "direct_test", "peer_addr": ["127.0.0.1", port_a]},
            )

            # Give time for message to arrive and be processed
            await asyncio.sleep(0.3)

            # B should have created a session for node-A
            session = puncher_b.get_session("node-A")
            assert session is not None, "Session should be created from incoming punch"
            assert session.peer_id == "node-A"

        finally:
            await transport_a.stop()
            await transport_b.stop()

    @pytest.mark.asyncio
    async def test_send_punch_ack_via_transport(self):
        """send_punch_ack uses transport.send_udp_to when transport is set."""
        port = find_free_port()
        transport = P2PTransport(
            node_id="ack-node",
            host="127.0.0.1",
            port_udp=port,
            port_ws=find_free_port(),
        )
        await transport.start()

        try:
            puncher = HolePuncher(
                node_id="ack-node",
                transport=transport,
            )

            # send_punch_ack should use transport and return True
            # (send to 127.0.0.1:19999 — will reach the transport's socket but timeout on read)
            result = await puncher.send_punch_ack(("127.0.0.1", 19999), "remote-peer")
            assert result is True

            # Session should be created
            session = puncher.get_session("remote-peer")
            assert session is not None
            assert session.status == PunchStatus.ESTABLISHED
        finally:
            await transport.stop()


# ---------------------------------------------------------------------------
# Test: HolePuncher Strategy Execution
# ---------------------------------------------------------------------------

class TestHolePuncherStrategies:
    """Strategy execution fallbacks work without real peers."""

    @pytest.mark.asyncio
    async def test_direct_strategy_fails_no_remote(self):
        """_try_direct fails when remote endpoint has no public_addr."""
        puncher = HolePuncher(node_id="test-strat")
        session = PunchSession(peer_id="ghost")
        result = await puncher._try_direct(session)
        assert result.status == PunchStatus.FAILED

    @pytest.mark.asyncio
    async def test_stun_punch_fails_no_remote(self):
        """_try_stun_punch fails when remote has no public_addr."""
        puncher = HolePuncher(node_id="test-strat")
        session = PunchSession(peer_id="ghost")
        result = await puncher._try_stun_punch(session)
        assert result.status == PunchStatus.FAILED

    @pytest.mark.asyncio
    async def test_rendezvous_punch_fails_no_client(self):
        """_try_rendezvous_punch fails when no rendezvous client."""
        puncher = HolePuncher(node_id="test-strat")
        session = PunchSession(peer_id="ghost")
        session.remote_endpoint = PunchEndpoint(
            node_id="ghost",
            public_addr=("10.0.0.1", 9001),
        )
        result = await puncher._try_rendezvous_punch(session)
        assert result.status == PunchStatus.FAILED

    @pytest.mark.asyncio
    async def test_tcp_relay_fallback(self):
        """_try_tcp_relay sets FALLBACK_RELAY status."""
        puncher = HolePuncher(node_id="test-strat")
        session = PunchSession(peer_id="ghost")
        result = await puncher._try_tcp_relay(session)
        assert result.status == PunchStatus.FALLBACK_RELAY
        assert result.fallback_used is True

    @pytest.mark.asyncio
    async def test_turn_relay_uses_env_server(self):
        """_try_turn_relay uses ASIM_MESH_TURN_SERVER env var, not _servers."""
        os.environ["ASIM_MESH_TURN_SERVER"] = "turn:127.0.0.1:3478"
        try:
            puncher = HolePuncher(node_id="test-turn")
            session = PunchSession(peer_id="ghost")
            session.remote_endpoint = PunchEndpoint(
                node_id="ghost",
                public_addr=("10.0.0.1", 9001),
            )
            # Will fail (no real TURN server) but shouldn't crash
            result = await puncher._try_turn_relay(session)
            assert result.status == PunchStatus.FAILED
        finally:
            os.environ.pop("ASIM_MESH_TURN_SERVER", None)

    @pytest.mark.asyncio
    async def test_strategy_execution_unknown(self):
        """_execute_strategy with UNKNOWN type tries RENDEZVOUS."""
        puncher = HolePuncher(node_id="test-exec")
        session = PunchSession(peer_id="ghost")
        session.remote_endpoint = PunchEndpoint(
            node_id="ghost",
            public_addr=("10.0.0.1", 9001),
        )
        # UNKNOWN falls to RENDEZVOUS which needs a client
        result = await puncher._execute_strategy(session, ConnectionStrategy.RENDEZVOUS)
        assert result.status == PunchStatus.FAILED

    @pytest.mark.asyncio
    async def test_direct_with_transport_timeout(self):
        """_try_direct with transport doesn't create blocking sockets."""
        port = find_free_port()
        transport = P2PTransport(
            node_id="direct-test",
            host="127.0.0.1",
            port_udp=port,
            port_ws=find_free_port(),
        )
        await transport.start()
        try:
            puncher = HolePuncher(
                node_id="direct-test",
                transport=transport,
            )
            session = PunchSession(peer_id="timeout-peer")
            session.remote_endpoint = PunchEndpoint(
                node_id="timeout-peer",
                public_addr=("192.0.2.1", 9999),  # RFC 5737 TEST-NET
            )
            result = await puncher._try_direct(session)
            assert result.status == PunchStatus.FAILED
        finally:
            await transport.stop()


# ---------------------------------------------------------------------------
# Test: PunchListener
# ---------------------------------------------------------------------------

class TestPunchListener:
    """PunchListener lifecycle and datagram handling."""

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """PunchListener can start and stop."""
        puncher = HolePuncher(node_id="listener-test")
        listener = PunchListener(
            node_id="listener-node",
            hole_puncher=puncher,
        )
        port = await listener.start()
        assert isinstance(port, int)
        assert port > 0
        assert listener._transport is not None

        await listener.stop()
        assert listener._transport is None

    @pytest.mark.asyncio
    async def test_handle_direct_test_raw(self):
        """PunchListener handles raw ASIM_PUNCH_DIRECT_TEST without blocking sockets."""
        puncher = HolePuncher(node_id="listener-test")
        listener = PunchListener(
            node_id="listener-node",
            hole_puncher=puncher,
        )
        await listener.start()
        try:
            # This should not raise (no transport yet, but handle_datagram skips send)
            await listener.handle_datagram(
                b"ASIM_PUNCH_DIRECT_TEST",
                ("127.0.0.1", 9999),
            )
            # No assertion — just verifying no crash
        finally:
            await listener.stop()

    @pytest.mark.asyncio
    async def test_handle_json_punch(self):
        """PunchListener handles JSON hole_punch messages."""
        puncher = HolePuncher(node_id="listener-test")
        listener = PunchListener(
            node_id="listener-node",
            hole_puncher=puncher,
        )
        await listener.start()
        try:
            msg = json.dumps({
                "type": "hole_punch",
                "from": "remote-peer",
                "timestamp": time.time(),
            }).encode("utf-8")
            await listener.handle_datagram(msg, ("127.0.0.1", 9999))

            # Session should have been created via send_punch_ack
            session = puncher.get_session("remote-peer")
            assert session is not None
            assert session.status == PunchStatus.ESTABLISHED
        finally:
            await listener.stop()


# ---------------------------------------------------------------------------
# Test: RelayService
# ---------------------------------------------------------------------------

class TestRelayService:
    """Relay service lifecycle and session management."""

    @pytest.mark.asyncio
    async def test_create_relay_service(self):
        """RelayService can be created."""
        svc = RelayService(node_id="relay-1", role=RelayRole.RELAY)
        assert svc.node_id == "relay-1"
        assert svc.role == RelayRole.RELAY

    @pytest.mark.asyncio
    async def test_start_stop_relay(self):
        """Relay server can be started and stopped."""
        port = find_free_port()
        svc = RelayService(node_id="relay-1", role=RelayRole.RELAY, port=port)
        await svc.start()
        assert svc._running
        assert svc._server is not None

        await svc.stop()
        assert not svc._running

    @pytest.mark.asyncio
    async def test_start_stop_client(self):
        """Relay client mode starts without a server."""
        svc = RelayService(node_id="client-1", role=RelayRole.CLIENT)
        await svc.start()
        assert svc._running
        assert svc._server is None
        await svc.stop()

    @pytest.mark.asyncio
    async def test_register_node(self):
        """A node can be registered with the relay."""
        svc = RelayService(node_id="relay-1", role=RelayRole.RELAY, port=find_free_port())
        svc._register_node("node-A", "10.0.0.1", 9001)
        node = svc.get_node("node-A")
        assert node is not None
        assert node.ip_address == "10.0.0.1"
        assert node.port == 9001

    @pytest.mark.asyncio
    async def test_create_and_close_session(self):
        """Sessions can be created and closed."""
        svc = RelayService(node_id="relay-1", role=RelayRole.RELAY, port=find_free_port())
        session = svc._get_or_create_session("sess-1", "client-A", "client-B")
        assert session.session_id == "sess-1"
        assert session.client_a_id == "client-A"
        assert session.client_b_id == "client-B"
        assert session.status == RelayStatus.CONNECTING

        # Close session
        await svc.close_session("sess-1")
        assert svc.get_session("sess-1") is None

    @pytest.mark.asyncio
    async def test_create_relay_with_transport(self):
        """RelayService can be created with a P2PTransport."""
        transport = P2PTransport(
            node_id="relay-transport",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
        )
        await transport.start()
        try:
            svc = RelayService(
                node_id="relay-with-tp",
                role=RelayRole.RELAY,
                port=find_free_port(),
                transport=transport,
            )
            assert svc.transport is transport
        finally:
            await transport.stop()

    @pytest.mark.asyncio
    async def test_relay_data_no_transport(self):
        """relay_data returns True in TCP mode (no transport)."""
        svc = RelayService(node_id="relay-1", role=RelayRole.RELAY, port=find_free_port())
        svc._get_or_create_session("sess-1", "client-A", "client-B")
        result = await svc.relay_data("sess-1", b"test data", "client-B")
        assert result is True

        session = svc.get_session("sess-1")
        assert session is not None
        assert session.bytes_relayed == 9  # len(b"test data")
        assert session.status == RelayStatus.RELAYING

    @pytest.mark.asyncio
    async def test_relay_data_nonexistent_session(self):
        """relay_data returns False for unknown session."""
        svc = RelayService(node_id="relay-1", role=RelayRole.RELAY, port=find_free_port())
        result = await svc.relay_data("ghost-session", b"data", "target")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """get_stats returns expected keys."""
        svc = RelayService(node_id="relay-1", role=RelayRole.RELAY, port=find_free_port())
        stats = svc.get_stats()
        assert stats["node_id"] == "relay-1"
        assert stats["role"] == "relay"
        assert stats["total_sessions"] == 0
        assert stats["running"] is False

    @pytest.mark.asyncio
    async def test_get_relay_service_singleton(self):
        """Singleton accessor returns same instance."""
        reset_relay_service()
        s1 = get_relay_service("test-relay", port=find_free_port())
        s2 = get_relay_service("test-relay")
        assert s1 is s2
        reset_relay_service()


# ---------------------------------------------------------------------------
# Test: P2PTransport NAT Integration
# ---------------------------------------------------------------------------

class TestP2PTransportNATIntegration:
    """P2PTransport's NAT-related methods work correctly."""

    @pytest.mark.asyncio
    async def test_send_udp_to_arbitrary_address(self):
        """send_udp_to sends to arbitrary address without PeerInfo."""
        port_a = find_free_port()
        port_b = find_free_port()

        transport_a = P2PTransport("node-A", "127.0.0.1", port_a, find_free_port())
        transport_b = P2PTransport("node-B", "127.0.0.1", port_b, find_free_port())

        received_messages = []

        async def on_test_msg(msg: P2PMessage):
            received_messages.append(msg)

        await transport_a.start()
        await transport_b.start()

        try:
            # Register a handler on B via on_rpc
            transport_b.on_rpc("TEST_MSG", on_test_msg)

            # Send from A to B without adding B as a peer
            sent = await transport_a.send_udp_to(
                "127.0.0.1", port_b,
                "TEST_MSG",
                {"hello": "world"},
            )
            assert sent is True

            await asyncio.sleep(0.3)
            assert len(received_messages) >= 1
            assert received_messages[0].payload.get("hello") == "world"
        finally:
            await transport_a.stop()
            await transport_b.stop()

    @pytest.mark.asyncio
    async def test_register_punch_handler(self):
        """register_punch_handler creates HOLE_PUNCH RPC handler."""
        transport = P2PTransport(
            node_id="punch-test",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
        )
        await transport.start()
        try:
            received = []

            async def handler(sender_id, payload):
                received.append((sender_id, payload))

            transport.register_punch_handler(handler)
            assert "HOLE_PUNCH" in transport._rpc_handlers

            # The handler is wrapped in an RPC handler — verify it exists
            rpc_handler = transport._rpc_handlers["HOLE_PUNCH"]
            assert rpc_handler is not None
        finally:
            await transport.stop()

    @pytest.mark.asyncio
    async def test_set_nat_classification(self):
        """set_nat_classification stores classification."""
        transport = P2PTransport(
            node_id="nat-cls",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
        )
        await transport.start()
        try:
            classification = NATClassification(
                nat_type=NATType.FULL_CONE,
                public_address=MappedAddress("1.2.3.4", 12345),
            )
            transport.set_nat_classification(classification)
            assert transport.nat_classification is classification
            assert transport.nat_classification.nat_type == NATType.FULL_CONE
        finally:
            await transport.stop()


# ---------------------------------------------------------------------------
# Phase 1B: Localhost Short-Circuit
# ---------------------------------------------------------------------------


class TestNATLocalhostShortCircuit:
    """NAT traversal short-circuits correctly on localhost (Phase 1B)."""

    @pytest.mark.asyncio
    async def test_nat_traversal_detector_localhost(self):
        """nat_traversal.NATDetector.detect() returns OPEN for 127.0.0.1."""
        detector = NATraversalDetector(local_ip="127.0.0.1", local_port=9999)
        nat_type = await detector.detect(timeout=1.0)
        assert nat_type == NATraversalNATType.OPEN
        assert detector.nat_type == NATraversalNATType.OPEN
        assert detector.public_ip == "127.0.0.1"
        assert detector.public_port == 9999

    @pytest.mark.asyncio
    async def test_nat_traversal_detector_localhost_v6(self):
        """nat_traversal.NATDetector.detect() returns OPEN for ::1."""
        detector = NATraversalDetector(local_ip="::1", local_port=9999)
        nat_type = await detector.detect(timeout=1.0)
        assert nat_type == NATraversalNATType.OPEN

    @pytest.mark.asyncio
    async def test_nat_traversal_detector_localhost_zero(self):
        """nat_traversal.NATDetector.detect() returns OPEN for 0.0.0.0."""
        detector = NATraversalDetector(local_ip="0.0.0.0", local_port=9999)
        nat_type = await detector.detect(timeout=1.0)
        assert nat_type == NATraversalNATType.OPEN

    @pytest.mark.asyncio
    async def test_nat_traversal_start_localhost(self):
        """NATTraversal.start() short-circuits when transport.host is localhost."""
        p2p = P2PTransport(
            node_id="nat-localhost",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
        )
        await p2p.start()
        try:
            nat = NATTraversal(node_id="nat-localhost", transport=p2p)
            await nat.start()
            try:
                assert nat.nat_type == NATraversalNATType.OPEN
                assert nat.public_ip == "127.0.0.1"
                stats = nat.get_stats()
                assert stats["nat_type"] == "open"
                assert stats["running"] is True
            finally:
                await nat.stop()
        finally:
            await p2p.stop()

    @pytest.mark.asyncio
    async def test_stun_turn_detector_localhost(self):
        """stun_turn.NATDetector.classify() short-circuits on localhost."""
        detector = NATDetector(local_ip="127.0.0.1")
        classification = await detector.classify()
        assert classification.nat_type == NATType.OPEN_INTERNET
        assert classification.confidence == 1.0
        reason = classification.details.get("reason", "")
        assert "localhost" in reason.lower()

    @pytest.mark.asyncio
    async def test_stun_turn_detector_localhost_v6(self):
        """stun_turn.NATDetector.classify() short-circuits on ::1."""
        detector = NATDetector(local_ip="::1")
        classification = await detector.classify()
        assert classification.nat_type == NATType.OPEN_INTERNET

    @pytest.mark.asyncio
    async def test_stun_turn_detector_without_localip(self):
        """stun_turn.NATDetector.classify() without local_ip proceeds normally."""
        detector = NATDetector(local_ip=None)
        # No local_ip set → no short-circuit, falls through to STUN check
        # Since no STUN servers respond in test env, returns UDP_BLOCKED
        classification = await detector.classify()
        assert classification.nat_type in (NATType.UDP_BLOCKED, NATType.UNKNOWN)
    @pytest.mark.asyncio
    async def test_nat_classification_default_none(self):
        """nat_classification is None by default."""
        transport = P2PTransport(
            node_id="nat-cls-default",
            host="127.0.0.1",
            port_udp=find_free_port(),
            port_ws=find_free_port(),
        )
        await transport.start()
        try:
            assert transport.nat_classification is None
        finally:
            await transport.stop()
