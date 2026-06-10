#!/usr/bin/env python3
"""
STATUS: INTEGRATED — UDP Hole Punching (Phase 1B)
ASIMNEXUS UDP Hole Punching
============================
Coordinates UDP hole punching between peers behind NAT.
Uses a rendezvous server for endpoint coordination.
Falls back to TURN/relay when hole punching fails.

Integrates with:
  - [`mesh/stun_turn.py`](stun_turn.py) — NAT classification & mapped addresses
  - [`mesh/relay.py`](relay.py) — Fallback relay for symmetric NATs
  - [`mesh/p2p_transport.py`](p2p_transport.py) — UDP transport for hole punching
  - [`mesh/bootstrap.py`](bootstrap.py) — Rendezvous peer discovery

When a P2PTransport is provided, punch messages are sent via the
transport's UDP socket (ensuring NAT mapping consistency) and
incoming punch messages are dispatched through the transport's
RPC handler system.
"""

import os
import json
import time
import struct
import socket
import random
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Awaitable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

from mesh.stun_turn import (
    NATClassification,
    NATType,
    MappedAddress,
    STUNClient,
    NATDetector,
    TURNClient,
    ConnectionStrategy,
    select_connection_strategy,
    get_nat_detector,
    get_stun_client,
    get_turn_client,
)

if TYPE_CHECKING:
    from mesh.p2p_transport import P2PTransport

logger = logging.getLogger("AsimNexus.Mesh.HolePunching")

# ─── Environment Configuration ────────────────────────────────────────────────

_HOLE_PUNCH_TIMEOUT_SEC = int(os.getenv("ASIM_MESH_HOLE_PUNCH_TIMEOUT", "10"))
_HOLE_PUNCH_RETRIES = int(os.getenv("ASIM_MESH_HOLE_PUNCH_RETRIES", "3"))
_PUNCH_INTERVAL_SEC = float(os.getenv("ASIM_MESH_PUNCH_INTERVAL", "0.1"))
_RENDEZVOUS_PORT = int(os.getenv("ASIM_MESH_RENDEZVOUS_PORT", "7336"))
_KEEPALIVE_INTERVAL_SEC = float(os.getenv("ASIM_MESH_PUNCH_KEEPALIVE", "15"))


# ─── Enums & Data Classes ────────────────────────────────────────────────────


class PunchStatus(Enum):
    """Status of a hole punch attempt."""
    PENDING = "pending"
    PUNCHING = "punching"
    ESTABLISHED = "established"
    FAILED = "failed"
    FALLBACK_RELAY = "fallback_relay"
    TIMEOUT = "timeout"


class RendezvousMessageType(Enum):
    """Message types for rendezvous protocol."""
    REGISTER = 0x01
    REGISTER_ACK = 0x02
    QUERY_PEER = 0x03
    QUERY_RESPONSE = 0x04
    PUNCH_REQUEST = 0x05
    PUNCH_NOTIFY = 0x06
    PUNCH_READY = 0x07
    PUNCH_RESULT = 0x08
    KEEPALIVE = 0x09
    ERROR = 0xFF


@dataclass
class PunchEndpoint:
    """An endpoint that a peer is reachable at."""
    node_id: str
    public_addr: Optional[Tuple[str, int]] = None    # STUN-discovered public
    local_addr: Optional[Tuple[str, int]] = None      # Local interface
    relay_addr: Optional[Tuple[str, int]] = None      # TURN relay (if available)
    nat_type: Optional[NATType] = None
    nat_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"node_id": self.node_id}
        if self.public_addr:
            d["public_addr"] = {"ip": self.public_addr[0], "port": self.public_addr[1]}
        if self.local_addr:
            d["local_addr"] = {"ip": self.local_addr[0], "port": self.local_addr[1]}
        if self.relay_addr:
            d["relay_addr"] = {"ip": self.relay_addr[0], "port": self.relay_addr[1]}
        if self.nat_type:
            d["nat_type"] = self.nat_type.value
            d["nat_confidence"] = self.nat_confidence
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PunchEndpoint":
        pub = data.get("public_addr")
        loc = data.get("local_addr")
        rel = data.get("relay_addr")
        return cls(
            node_id=data["node_id"],
            public_addr=(pub["ip"], pub["port"]) if pub else None,
            local_addr=(loc["ip"], loc["port"]) if loc else None,
            relay_addr=(rel["ip"], rel["port"]) if rel else None,
            nat_type=NATType(data["nat_type"]) if "nat_type" in data else None,
            nat_confidence=data.get("nat_confidence", 0.0),
        )


@dataclass
class PunchSession:
    """Tracks a hole-punch session between two peers."""
    peer_id: str
    status: PunchStatus = PunchStatus.PENDING
    local_endpoint: Optional[PunchEndpoint] = None
    remote_endpoint: Optional[PunchEndpoint] = None
    strategy: ConnectionStrategy = ConnectionStrategy.DIRECT
    attempts: int = 0
    last_punch_time: float = 0.0
    established_addr: Optional[Tuple[str, int]] = None
    started_at: float = field(default_factory=time.time)
    fallback_used: bool = False

    @property
    def elapsed(self) -> float:
        return time.time() - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "status": self.status.value,
            "strategy": self.strategy.value,
            "attempts": self.attempts,
            "elapsed": self.elapsed,
            "fallback_used": self.fallback_used,
            "established_addr": (
                f"{self.established_addr[0]}:{self.established_addr[1]}"
                if self.established_addr else None
            ),
        }


# ─── Rendezvous Server ───────────────────────────────────────────────────────


class RendezvousServer:
    """
    Lightweight rendezvous server for coordinating hole punches.

    Peers register their public endpoints, then query for other peers
    and receive punch notifications to begin simultaneous hole punching.

    Protocol: Simple binary messages over UDP on RENDEZVOUS_PORT.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = _RENDEZVOUS_PORT,
        peer_timeout: float = 300.0,
    ):
        self._host = host
        self._port = port
        self._peer_timeout = peer_timeout
        self._peers: Dict[str, PunchEndpoint] = {}          # node_id → endpoint
        self._pending_punches: Dict[str, List[str]] = {}     # target_id → list of requesters
        self._server: Optional[asyncio.DatagramServer] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._running = False

    @property
    def port(self) -> int:
        """Return the actual bound port (may differ from constructor arg if port=0)."""
        return self._port

    async def start(self) -> None:
        """Start the rendezvous UDP server."""
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: _RendezvousProtocol(self),
            local_addr=(self._host, self._port),
        )
        self._server = transport
        self._running = True
        # Capture the actual bound port (important when port=0)
        if self._port == 0:
            sockname = transport.get_extra_info("sockname")
            if sockname:
                self._port = sockname[1]
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Rendezvous server listening on {self._host}:{self._port}")

    async def stop(self) -> None:
        """Stop the rendezvous server."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        if self._server:
            self._server.close()
        self._running = False
        logger.info("Rendezvous server stopped")

    async def handle_message(self, data: bytes, addr: Tuple[str, int]) -> Optional[bytes]:
        """Handle an incoming rendezvous message. Returns response bytes or None."""
        try:
            if len(data) < 2:
                return self._encode_error("Message too short")

            msg_type = data[0]
            payload = data[1:]

            if msg_type == RendezvousMessageType.REGISTER.value:
                return await self._handle_register(payload, addr)
            elif msg_type == RendezvousMessageType.QUERY_PEER.value:
                return await self._handle_query_peer(payload)
            elif msg_type == RendezvousMessageType.PUNCH_REQUEST.value:
                return await self._handle_punch_request(payload, addr)
            elif msg_type == RendezvousMessageType.KEEPALIVE.value:
                return await self._handle_keepalive(payload)
            else:
                return self._encode_error(f"Unknown message type: {msg_type}")

        except Exception as exc:
            logger.error(f"Error handling rendezvous message from {addr}: {exc}")
            return self._encode_error(str(exc))

    async def _handle_register(self, payload: bytes, addr: Tuple[str, int]) -> bytes:
        """Register a peer's endpoint information."""
        try:
            data = json.loads(payload.decode("utf-8"))
            node_id = data.get("node_id", "")
            if not node_id:
                return self._encode_error("Missing node_id")

            endpoint = PunchEndpoint.from_dict(data)

            # Fill in source address from UDP packet if not provided
            if endpoint.public_addr is None:
                endpoint.public_addr = addr
            if endpoint.local_addr is None:
                endpoint.local_addr = addr

            async with self._lock:
                self._peers[node_id] = endpoint

            logger.info(f"Peer registered: {node_id} @ {endpoint.public_addr}")
            return bytes([RendezvousMessageType.REGISTER_ACK.value]) + json.dumps({
                "status": "ok",
                "your_addr": {"ip": addr[0], "port": addr[1]},
            }).encode("utf-8")

        except json.JSONDecodeError:
            return self._encode_error("Invalid JSON payload")

    async def _handle_query_peer(self, payload: bytes) -> bytes:
        """Query for a peer's endpoint information."""
        try:
            data = json.loads(payload.decode("utf-8"))
            target_id = data.get("target_id", "")

            async with self._lock:
                endpoint = self._peers.get(target_id)

            if endpoint is None:
                return bytes([RendezvousMessageType.QUERY_RESPONSE.value]) + json.dumps({
                    "found": False,
                    "target_id": target_id,
                }).encode("utf-8")

            return bytes([RendezvousMessageType.QUERY_RESPONSE.value]) + json.dumps({
                "found": True,
                "target_id": target_id,
                "endpoint": endpoint.to_dict(),
            }).encode("utf-8")

        except json.JSONDecodeError:
            return self._encode_error("Invalid JSON payload")

    async def _handle_punch_request(self, payload: bytes, addr: Tuple[str, int]) -> bytes:
        """Handle a punch request — notify the target peer to start punching."""
        try:
            data = json.loads(payload.decode("utf-8"))
            requester_id = data.get("requester_id", "")
            target_id = data.get("target_id", "")

            if not requester_id or not target_id:
                return self._encode_error("Missing requester_id or target_id")

            async with self._lock:
                # Store the pending punch request
                if target_id not in self._pending_punches:
                    self._pending_punches[target_id] = []
                self._pending_punches[target_id].append(requester_id)

                # Get both endpoints
                requester_endpoint = self._peers.get(requester_id)
                target_endpoint = self._peers.get(target_id)

            if requester_endpoint is None:
                return self._encode_error(f"Requester {requester_id} not registered")
            if target_endpoint is None:
                return self._encode_error(f"Target {target_id} not registered")

            # Notify the target about the incoming punch request
            notify_data = json.dumps({
                "type": "punch_request",
                "requester_id": requester_id,
                "requester_endpoint": requester_endpoint.to_dict(),
            }).encode("utf-8")

            notify_msg = bytes([RendezvousMessageType.PUNCH_NOTIFY.value]) + notify_data

            # Send notification to target via UDP
            if target_endpoint.public_addr:
                try:
                    loop = asyncio.get_running_loop()
                    transport = self._server  # type: ignore
                    if transport:
                        transport.sendto(notify_msg, target_endpoint.public_addr)
                        logger.info(f"Sent punch notify to {target_id} @ {target_endpoint.public_addr}")
                except Exception as exc:
                    logger.warning(f"Failed to send punch notify to {target_id}: {exc}")

            # Also notify requester about target's endpoint (so they can start punching)
            response_data = json.dumps({
                "status": "notified",
                "target_id": target_id,
                "target_endpoint": target_endpoint.to_dict(),
            }).encode("utf-8")

            return bytes([RendezvousMessageType.PUNCH_READY.value]) + response_data

        except json.JSONDecodeError:
            return self._encode_error("Invalid JSON payload")

    async def _handle_keepalive(self, payload: bytes) -> bytes:
        """Handle a keepalive from a peer."""
        try:
            data = json.loads(payload.decode("utf-8"))
            node_id = data.get("node_id", "")

            if node_id:
                async with self._lock:
                    if node_id in self._peers:
                        # Update last seen by just having the entry exist
                        pass

            return bytes([RendezvousMessageType.KEEPALIVE.value]) + json.dumps({
                "status": "ok",
            }).encode("utf-8")

        except json.JSONDecodeError:
            return self._encode_error("Invalid JSON payload")

    def _encode_error(self, msg: str) -> bytes:
        """Encode an error response."""
        return bytes([RendezvousMessageType.ERROR.value]) + msg.encode("utf-8")

    def get_connected_peers(self) -> int:
        return len(self._peers)

    async def _cleanup_loop(self) -> None:
        """Periodically remove stale peers."""
        while self._running:
            await asyncio.sleep(60)
            now = time.time()
            async with self._lock:
                stale = [
                    nid for nid, ep in self._peers.items()
                    if now - getattr(ep, "_last_seen", now) > self._peer_timeout
                ]
                for nid in stale:
                    del self._peers[nid]
                if stale:
                    logger.debug(f"Cleaned up {len(stale)} stale peers from rendezvous")


class _RendezvousProtocol(asyncio.DatagramProtocol):
    """Internal UDP protocol handler for RendezvousServer."""

    def __init__(self, server: RendezvousServer):
        self._server = server
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """Called when the UDP transport is created."""
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Called when a datagram is received."""
        asyncio.ensure_future(self._handle(data, addr))

    def error_received(self, exc: Exception) -> None:
        """Called when an error occurs (e.g. ICMP unreachable)."""
        logger.warning(f"_RendezvousProtocol error: {exc}")

    async def _handle(self, data: bytes, addr: Tuple[str, int]) -> None:
        response = await self._server.handle_message(data, addr)
        if response and self.transport:
            self.transport.sendto(response, addr)


# ─── Rendezvous Client ───────────────────────────────────────────────────────


class RendezvousClient:
    """
    Client for communicating with the RendezvousServer.

    Used by peers to register, discover other peers, and coordinate
    hole punching.
    """

    def __init__(
        self,
        node_id: str,
        rendezvous_addr: Tuple[str, int] = ("127.0.0.1", _RENDEZVOUS_PORT),
        local_endpoint: Optional[PunchEndpoint] = None,
    ):
        self._node_id = node_id
        self._rendezvous_addr = rendezvous_addr
        self._local_endpoint = local_endpoint or PunchEndpoint(node_id=node_id)
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._running = False
        self._pending_responses: List[asyncio.Future] = []

    async def start(self) -> None:
        """Create a UDP socket for rendezvous communication."""
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _RendezvousClientProtocol(self),
            local_addr=("0.0.0.0", 0),
        )
        self._transport = transport
        self._running = True

    async def stop(self) -> None:
        self._running = False
        if self._transport:
            self._transport.close()
            self._transport = None

    async def register(self, endpoint: PunchEndpoint) -> bool:
        """Register with the rendezvous server."""
        if not self._transport:
            return False

        payload = json.dumps(endpoint.to_dict()).encode("utf-8")
        msg = bytes([RendezvousMessageType.REGISTER.value]) + payload
        response = await self._send_and_wait(msg, timeout=5.0)

        if response and response[0] == RendezvousMessageType.REGISTER_ACK.value:
            return True
        return False

    async def query_peer(self, target_id: str) -> Optional[PunchEndpoint]:
        """Query the rendezvous server for a peer's endpoint."""
        if not self._transport:
            return None

        payload = json.dumps({"target_id": target_id}).encode("utf-8")
        msg = bytes([RendezvousMessageType.QUERY_PEER.value]) + payload
        response = await self._send_and_wait(msg, timeout=5.0)

        if response and response[0] == RendezvousMessageType.QUERY_RESPONSE.value:
            try:
                data = json.loads(response[1:].decode("utf-8"))
                if data.get("found"):
                    return PunchEndpoint.from_dict(data["endpoint"])
            except (json.JSONDecodeError, KeyError):
                pass
        return None

    async def request_punch(self, target_id: str) -> Optional[Dict[str, Any]]:
        """Request a hole punch with a target peer via the rendezvous server."""
        if not self._transport:
            return None

        payload = json.dumps({
            "requester_id": self._node_id,
            "target_id": target_id,
        }).encode("utf-8")
        msg = bytes([RendezvousMessageType.PUNCH_REQUEST.value]) + payload
        response = await self._send_and_wait(msg, timeout=8.0)

        if response and response[0] == RendezvousMessageType.PUNCH_READY.value:
            try:
                return json.loads(response[1:].decode("utf-8"))
            except json.JSONDecodeError:
                pass
        return None

    async def send_keepalive(self) -> bool:
        """Send a keepalive to the rendezvous server."""
        if not self._transport:
            return False

        payload = json.dumps({"node_id": self._node_id}).encode("utf-8")
        msg = bytes([RendezvousMessageType.KEEPALIVE.value]) + payload
        try:
            self._transport.sendto(msg, self._rendezvous_addr)
            return True
        except Exception:
            return False

    async def _send_and_wait(self, msg: bytes, timeout: float = 5.0) -> Optional[bytes]:
        """Send a message and wait for a response."""
        if not self._transport:
            return None

        future: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()

        # Register pending response
        self._pending_responses.append(future)

        try:
            self._transport.sendto(msg, self._rendezvous_addr)
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            if future in self._pending_responses:
                self._pending_responses.remove(future)

    def _on_response(self, data: bytes) -> None:
        """Called by protocol when a response is received."""
        if self._pending_responses:
            future = self._pending_responses.pop(0)
            if not future.done():
                future.set_result(data)


class _RendezvousClientProtocol(asyncio.DatagramProtocol):
    """Internal UDP protocol handler for RendezvousClient."""

    def __init__(self, client: RendezvousClient):
        self._client = client

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        self._client._on_response(data)


# ─── Hole Puncher ────────────────────────────────────────────────────────────


class _PunchResponseProtocol(asyncio.DatagramProtocol):
    """Internal protocol for receiving punch responses via a Future."""
    def __init__(self, response_future: asyncio.Future[bytes]):
        self._response_future = response_future
    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        if not self._response_future.done():
            self._response_future.set_result(data)
    def error_received(self, exc: Exception) -> None:
        if not self._response_future.done():
            self._response_future.set_exception(exc)


class HolePuncher:
    """
    Coordinates UDP hole punching between peers.

    Strategies (in priority order):
      1. DIRECT       — Both peers have public IPs, connect directly
      2. STUN_PUNCH   — Standard UDP hole punching using STUN-discovered addresses
      3. RENDEZVOUS   — Coordinated simultaneous punch via rendezvous server
      4. TURN_RELAY   — Use TURN relay for symmetric NAT
      5. RELAY        — TCP relay fallback

    When a P2PTransport is provided:
      - Punch messages are sent via transport.send_udp_to() for consistent NAT mapping
      - On punch success, on_punch_established callback updates transport peer state
      - Incoming punch messages arrive via transport's RPC handler system

    Usage:
        puncher = HolePuncher(node_id, transport=transport)
        await puncher.punch(remote_peer_id, remote_endpoint)
    """

    def __init__(
        self,
        node_id: str,
        stun_client: Optional[STUNClient] = None,
        nat_detector: Optional[NATDetector] = None,
        turn_client: Optional[TURNClient] = None,
        rendezvous_client: Optional[RendezvousClient] = None,
        local_addr: Optional[Tuple[str, int]] = None,
        transport: Optional['P2PTransport'] = None,
        on_punch_established: Optional[Callable[[str, Tuple[str, int]], Awaitable[None]]] = None,
    ):
        self._node_id = node_id
        self._stun_client = stun_client or get_stun_client()
        self._nat_detector = nat_detector or get_nat_detector()
        self._turn_client = turn_client or get_turn_client()
        self._rendezvous_client = rendezvous_client
        self._local_addr = local_addr
        self._transport = transport
        self._on_punch_established = on_punch_established
        self._sessions: Dict[str, PunchSession] = {}
        self._lock = asyncio.Lock()
        self._nat_classification: Optional[NATClassification] = None

        # Register punch handler with transport if available
        if transport:
            transport.register_punch_handler(self._handle_incoming_punch)

    async def initialize(self) -> NATClassification:
        """Run NAT detection and cache the result."""
        if self._nat_classification is None:
            self._nat_classification = await self._nat_detector.classify()
            logger.info(
                f"NAT classification: {self._nat_classification.nat_type.value} "
                f"(public: {self._nat_classification.public_address})"
            )
        return self._nat_classification

    async def _handle_incoming_punch(self, sender_id: str, payload: Dict[str, Any]) -> None:
        """
        Handle an incoming HOLE_PUNCH message from the transport.
        
        This is registered as the transport's punch handler. When a peer
        sends a HOLE_PUNCH message, we record the session and notify
        the application.
        """
        punch_type = payload.get("punch_type", "")
        peer_addr_tuple = payload.get("peer_addr")
        if peer_addr_tuple:
            peer_addr = (peer_addr_tuple[0], peer_addr_tuple[1])
        else:
            peer_addr = ("0.0.0.0", 0)

        if punch_type in ("direct_test", "stun_punch", "rendezvous_punch"):
            # Create or update session
            async with self._lock:
                if sender_id not in self._sessions:
                    session = PunchSession(peer_id=sender_id)
                    session.remote_endpoint = PunchEndpoint(
                        node_id=sender_id,
                        public_addr=peer_addr,
                    )
                    self._sessions[sender_id] = session
                else:
                    session = self._sessions[sender_id]

            # Send ACK back
            await self.send_punch_ack(peer_addr, sender_id)
            logger.info(f"🤜 Incoming hole punch from {sender_id} @ {peer_addr}")

        elif punch_type == "punch_ack":
            # Punch confirmed
            async with self._lock:
                session = self._sessions.get(sender_id)
                if session and session.status != PunchStatus.ESTABLISHED:
                    session.status = PunchStatus.ESTABLISHED
                    session.established_addr = peer_addr
                    logger.info(f"🤜 Hole punch confirmed by {sender_id} @ {peer_addr}")
                    # Notify transport via callback
                    if self._on_punch_established:
                        await self._on_punch_established(sender_id, peer_addr)

    async def punch(
        self,
        peer_id: str,
        remote_endpoint: PunchEndpoint,
        timeout: float = _HOLE_PUNCH_TIMEOUT_SEC,
    ) -> PunchSession:
        """
        Initiate hole punching with a remote peer.

        Returns a PunchSession tracking the result.
        """
        nat = await self.initialize()

        async with self._lock:
            if peer_id in self._sessions:
                session = self._sessions[peer_id]
                if session.status in (PunchStatus.ESTABLISHED, PunchStatus.FAILED):
                    return session
            session = PunchSession(peer_id=peer_id)
            self._sessions[peer_id] = session

        session.remote_endpoint = remote_endpoint

        # Determine strategy based on both NAT types
        local_nat_type = nat
        remote_nat_type_val = remote_endpoint.nat_type or NATType.UNKNOWN

        remote_classification = NATClassification(
            nat_type=remote_nat_type_val,
            public_address=remote_endpoint.public_addr
            and MappedAddress(
                ip_address=remote_endpoint.public_addr[0],
                port=remote_endpoint.public_addr[1],
            )
            or None,
        )

        strategy = select_connection_strategy(
            local_nat_type, remote_classification
        )
        session.strategy = strategy
        session.status = PunchStatus.PUNCHING

        logger.info(
            f"Hole punching {peer_id} — strategy={strategy.value}, "
            f"local_nat={nat.nat_type.value}, remote_nat={remote_nat_type_val.value}"
        )

        try:
            result = await asyncio.wait_for(
                self._execute_strategy(session, strategy),
                timeout=timeout,
            )
            return result
        except asyncio.TimeoutError:
            session.status = PunchStatus.TIMEOUT
            logger.warning(f"Hole punch timeout for {peer_id}")
            return session

    async def _execute_strategy(
        self,
        session: PunchSession,
        strategy: ConnectionStrategy,
    ) -> PunchSession:
        """Execute the selected hole punching strategy."""
        if strategy == ConnectionStrategy.DIRECT:
            return await self._try_direct(session)
        elif strategy == ConnectionStrategy.STUN_PUNCH:
            return await self._try_stun_punch(session)
        elif strategy == ConnectionStrategy.RENDEZVOUS:
            return await self._try_rendezvous_punch(session)
        elif strategy == ConnectionStrategy.TURN_RELAY:
            return await self._try_turn_relay(session)
        else:
            return await self._try_tcp_relay(session)

    async def _try_direct(self, session: PunchSession) -> PunchSession:
        """
        Try direct connection (both peers are on public internet).

        When transport is available, sends P2PMessage via transport.send_udp_to()
        and relies on _handle_incoming_punch for ACK delivery.
        Falls back to asyncio DatagramProtocol when no transport.
        """
        remote = session.remote_endpoint
        if not remote or not remote.public_addr:
            session.status = PunchStatus.FAILED
            return session

        if self._transport:
            # ── Transport mode: consistent NAT mapping ────────────────────────
            test_payload = {
                "punch_type": "direct_test",
                "peer_addr": list(remote.public_addr),
            }
            for i in range(_HOLE_PUNCH_RETRIES + 1):
                await self._transport.send_udp_to(
                    remote.public_addr[0], remote.public_addr[1],
                    "HOLE_PUNCH", test_payload,
                )
                session.attempts += 1
                # Session may have been established by _handle_incoming_punch
                async with self._lock:
                    if session.status == PunchStatus.ESTABLISHED:
                        logger.info(
                            f"Direct connection established with {session.peer_id}"
                        )
                        return session
                await asyncio.sleep(_PUNCH_INTERVAL_SEC)

            session.status = PunchStatus.FAILED
            return session
        else:
            # ── Fallback mode: asyncio DatagramProtocol ───────────────────────
            loop = asyncio.get_event_loop()
            response_future: asyncio.Future[bytes] = loop.create_future()
            protocol_factory = lambda: _PunchResponseProtocol(response_future)
            transport, protocol = await loop.create_datagram_endpoint(
                protocol_factory,
                local_addr=self._local_addr or ("0.0.0.0", 0),
            )
            try:
                test_msg = b"ASIM_PUNCH_DIRECT_TEST"
                transport.sendto(test_msg, remote.public_addr)

                # Wait for response with timeout
                try:
                    data = await asyncio.wait_for(response_future, timeout=2.0)
                    if data == b"ASIM_PUNCH_DIRECT_ACK":
                        session.status = PunchStatus.ESTABLISHED
                        session.established_addr = remote.public_addr
                        logger.info(
                            f"Direct connection established with {session.peer_id}"
                        )
                        return session
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass

                # Try a few more times
                for i in range(_HOLE_PUNCH_RETRIES):
                    transport.sendto(test_msg, remote.public_addr)
                    session.attempts += 1
                    try:
                        data = await asyncio.wait_for(response_future, timeout=2.0)
                        if data == b"ASIM_PUNCH_DIRECT_ACK":
                            session.status = PunchStatus.ESTABLISHED
                            session.established_addr = remote.public_addr
                            return session
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        await asyncio.sleep(_PUNCH_INTERVAL_SEC)

                session.status = PunchStatus.FAILED
                return session
            finally:
                transport.close()

    async def _try_stun_punch(self, session: PunchSession) -> PunchSession:
        """
        Standard UDP hole punching using STUN-discovered public addresses.

        When transport is available, punch messages are sent via
        transport.send_udp_to() for consistent NAT mapping. The ACK
        arrives through _handle_incoming_punch via the transport's RPC
        handler system.
        Falls back to asyncio DatagramProtocol when no transport.
        """
        remote = session.remote_endpoint
        if not remote or not remote.public_addr:
            session.status = PunchStatus.FAILED
            return session

        local_nat = await self.initialize()
        local_public = local_nat.public_address
        local_addr_tuple = (
            (self._local_addr[0], self._local_addr[1])
            if self._local_addr else None
        )

        if self._transport:
            # ── Transport mode: consistent NAT mapping ────────────────────────
            punch_payload = {
                "punch_type": "stun_punch",
                "from": self._node_id,
                "public_addr": (
                    [local_public.ip_address, local_public.port]
                    if local_public else None
                ),
                "local_addr": (
                    [self._local_addr[0], self._local_addr[1]]
                    if self._local_addr else None
                ),
                "timestamp": time.time(),
            }

            for i in range(_HOLE_PUNCH_RETRIES * 3):
                await self._transport.send_udp_to(
                    remote.public_addr[0], remote.public_addr[1],
                    "HOLE_PUNCH", punch_payload,
                )
                session.attempts += 1

                # Also send to local address for LAN peers
                if remote.local_addr and remote.local_addr != remote.public_addr:
                    await self._transport.send_udp_to(
                        remote.local_addr[0], remote.local_addr[1],
                        "HOLE_PUNCH", punch_payload,
                    )

                # Check if session was established by _handle_incoming_punch
                async with self._lock:
                    if session.status == PunchStatus.ESTABLISHED:
                        return session
                await asyncio.sleep(_PUNCH_INTERVAL_SEC)

            session.status = PunchStatus.FAILED
            return session
        else:
            # ── Fallback mode: asyncio DatagramProtocol ───────────────────────
            loop = asyncio.get_event_loop()
            response_future: asyncio.Future[bytes] = loop.create_future()
            protocol_factory = lambda: _PunchResponseProtocol(response_future)
            transport, protocol = await loop.create_datagram_endpoint(
                protocol_factory,
                local_addr=self._local_addr or ("0.0.0.0", 0),
            )
            try:
                punch_msg = json.dumps({
                    "type": "hole_punch",
                    "from": self._node_id,
                    "local_addr": local_addr_tuple,
                    "public_addr": local_public and (local_public.ip_address, local_public.port),
                    "timestamp": time.time(),
                }).encode("utf-8")

                for i in range(_HOLE_PUNCH_RETRIES * 3):
                    transport.sendto(punch_msg, remote.public_addr)
                    session.attempts += 1

                    if remote.local_addr and remote.local_addr != remote.public_addr:
                        transport.sendto(punch_msg, remote.local_addr)

                    try:
                        data = await asyncio.wait_for(response_future, timeout=1.0)
                        try:
                            resp = json.loads(data.decode("utf-8"))
                            if resp.get("type") == "hole_punch_ack":
                                session.status = PunchStatus.ESTABLISHED
                                session.established_addr = remote.public_addr
                                return session
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            if data == b"ASIM_PUNCH_ACK":
                                session.status = PunchStatus.ESTABLISHED
                                session.established_addr = remote.public_addr
                                return session
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass

                    await asyncio.sleep(_PUNCH_INTERVAL_SEC)

                session.status = PunchStatus.FAILED
                return session
            finally:
                transport.close()

    async def _try_rendezvous_punch(self, session: PunchSession) -> PunchSession:
        """
        Coordinated hole punching via the rendezvous server.

        When transport is available, punch messages use transport.send_udp_to()
        for consistent NAT mapping and ACKs arrive via _handle_incoming_punch.
        Falls back to asyncio DatagramProtocol when no transport.
        """
        if not self._rendezvous_client:
            logger.warning("No rendezvous client available for coordinated punch")
            session.status = PunchStatus.FAILED
            return session

        remote = session.remote_endpoint
        if not remote:
            session.status = PunchStatus.FAILED
            return session

        # Request punch coordination via rendezvous server
        result = await self._rendezvous_client.request_punch(session.peer_id)
        if result is None:
            session.status = PunchStatus.FAILED
            return session

        # Rendezvous server will notify both peers simultaneously
        target_endpoint_data = result.get("target_endpoint", {})
        target_public = target_endpoint_data.get("public_addr")
        target_local = target_endpoint_data.get("local_addr")

        target_public_addr: Optional[Tuple[str, int]] = (
            (target_public["ip"], target_public["port"]) if target_public else None
        )

        # Prefer info from remote_endpoint if available
        if remote.public_addr:
            target_public_addr = remote.public_addr

        if not target_public_addr:
            session.status = PunchStatus.FAILED
            return session

        if self._transport:
            # ── Transport mode: consistent NAT mapping ────────────────────────
            punch_payload = {
                "punch_type": "rendezvous_punch",
                "from": self._node_id,
                "timestamp": time.time(),
            }

            for i in range(_HOLE_PUNCH_RETRIES * 2):
                await self._transport.send_udp_to(
                    target_public_addr[0], target_public_addr[1],
                    "HOLE_PUNCH", punch_payload,
                )
                session.attempts += 1

                # Also try local address for LAN peers
                if target_local:
                    local_addr_tuple = (target_local["ip"], target_local["port"])
                    if local_addr_tuple != target_public_addr:
                        await self._transport.send_udp_to(
                            local_addr_tuple[0], local_addr_tuple[1],
                            "HOLE_PUNCH", punch_payload,
                        )

                # Check if session was established by _handle_incoming_punch
                async with self._lock:
                    if session.status == PunchStatus.ESTABLISHED:
                        return session
                await asyncio.sleep(_PUNCH_INTERVAL_SEC)

            session.status = PunchStatus.FAILED
            return session
        else:
            # ── Fallback mode: asyncio DatagramProtocol ───────────────────────
            loop = asyncio.get_event_loop()
            response_future: asyncio.Future[bytes] = loop.create_future()
            protocol_factory = lambda: _PunchResponseProtocol(response_future)
            transport, protocol = await loop.create_datagram_endpoint(
                protocol_factory,
                local_addr=("0.0.0.0", 0),
            )
            try:
                punch_msg = json.dumps({
                    "type": "rendezvous_punch",
                    "from": self._node_id,
                    "timestamp": time.time(),
                }).encode("utf-8")

                for i in range(_HOLE_PUNCH_RETRIES * 2):
                    transport.sendto(punch_msg, target_public_addr)
                    session.attempts += 1

                    if target_local:
                        local_addr_tuple = (target_local["ip"], target_local["port"])
                        if local_addr_tuple != target_public_addr:
                            transport.sendto(punch_msg, local_addr_tuple)

                    try:
                        data = await asyncio.wait_for(response_future, timeout=1.0)
                        if b"rendezvous_punch" in data or b"PUNCH_ACK" in data:
                            session.status = PunchStatus.ESTABLISHED
                            session.established_addr = target_public_addr
                            return session
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass

                    await asyncio.sleep(_PUNCH_INTERVAL_SEC)

                session.status = PunchStatus.FAILED
                return session
            finally:
                transport.close()

    async def _try_turn_relay(self, session: PunchSession) -> PunchSession:
        """
        Use TURN relay for peers behind symmetric NAT.

        Allocates a TURN relay address from environment-configured TURN
        servers and returns the relayed endpoint.
        """
        # Use environment-configured TURN server (no _servers attribute access)
        turn_server = os.getenv("ASIM_MESH_TURN_SERVER", "turn:localhost:3478")
        allocation = await self._turn_client.allocate(
            server=turn_server,
            username=os.getenv("ASIM_MESH_TURN_USERNAME", ""),
            password=os.getenv("ASIM_MESH_TURN_PASSWORD", ""),
        )

        if allocation and allocation.relayed_address:
            session.status = PunchStatus.ESTABLISHED
            session.established_addr = (
                allocation.relayed_address.ip_address,
                allocation.relayed_address.port,
            )
            session.fallback_used = True
            session.strategy = ConnectionStrategy.TURN_RELAY
            logger.info(
                f"TURN relay established for {session.peer_id} @ "
                f"{allocation.relayed_address}"
            )
        else:
            session.status = PunchStatus.FAILED

        return session

    async def _try_tcp_relay(self, session: PunchSession) -> PunchSession:
        """
        Fall back to TCP relay when everything else fails.
        """
        session.status = PunchStatus.FALLBACK_RELAY
        session.fallback_used = True
        logger.info(f"Falling back to TCP relay for {session.peer_id}")
        return session

    async def send_punch_ack(
        self,
        peer_addr: Tuple[str, int],
        peer_id: str,
    ) -> bool:
        """
        Send a hole punch acknowledgment to a peer.

        When transport is available, sends via transport.send_udp_to()
        for consistent NAT mapping and P2PMessage framing.
        Falls back to asyncio DatagramProtocol when no transport.
        """
        # Update session state regardless of transport method
        async with self._lock:
            if peer_id not in self._sessions:
                session = PunchSession(peer_id=peer_id)
                session.remote_endpoint = PunchEndpoint(
                    node_id=peer_id,
                    public_addr=peer_addr,
                )
                self._sessions[peer_id] = session
            session = self._sessions[peer_id]
            session.status = PunchStatus.ESTABLISHED
            session.established_addr = peer_addr

        if self._transport:
            # ── Transport mode: P2PMessage via transport ──────────────────────
            ack_payload = {
                "punch_type": "punch_ack",
                "peer_addr": list(peer_addr),
            }
            return await self._transport.send_udp_to(
                peer_addr[0], peer_addr[1],
                "HOLE_PUNCH", ack_payload,
            )
        else:
            # ── Fallback mode: asyncio DatagramProtocol ───────────────────────
            try:
                loop = asyncio.get_event_loop()
                transport, protocol = await loop.create_datagram_endpoint(
                    asyncio.DatagramProtocol,
                    remote_addr=peer_addr,
                )
                try:
                    ack_msg = json.dumps({
                        "type": "hole_punch_ack",
                        "from": self._node_id,
                        "timestamp": time.time(),
                    }).encode("utf-8")
                    transport.sendto(ack_msg)
                    return True
                finally:
                    transport.close()
            except Exception as exc:
                logger.warning(f"Failed to send punch ACK to {peer_addr}: {exc}")
                return False

    def get_session(self, peer_id: str) -> Optional[PunchSession]:
        """Get the current punch session for a peer."""
        return self._sessions.get(peer_id)

    def get_established_peers(self) -> List[str]:
        """Get list of peer IDs with established connections."""
        return [
            pid for pid, s in self._sessions.items()
            if s.status == PunchStatus.ESTABLISHED
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get hole punching statistics."""
        established = sum(1 for s in self._sessions.values() if s.status == PunchStatus.ESTABLISHED)
        failed = sum(1 for s in self._sessions.values() if s.status == PunchStatus.FAILED)
        fallback = sum(1 for s in self._sessions.values() if s.fallback_used)
        return {
            "total_sessions": len(self._sessions),
            "established": established,
            "failed": failed,
            "fallback_relay": fallback,
            "success_rate": (established / len(self._sessions) * 100)
            if self._sessions else 0.0,
        }


# ─── Incoming Punch Listener ─────────────────────────────────────────────────


class PunchListener:
    """
    Listens for incoming hole punch requests on a UDP socket.

    When a punch request is received, it calls the provided callback
    so the application can respond with a punch ACK.

    This runs alongside the normal P2P transport to handle
    the hole-punch handshake messages.
    """

    def __init__(
        self,
        node_id: str,
        hole_puncher: HolePuncher,
        listen_addr: Tuple[str, int] = ("0.0.0.0", 0),
        on_punch_request: Optional[Callable] = None,
    ):
        self._node_id = node_id
        self._hole_puncher = hole_puncher
        self._listen_addr = listen_addr
        self._on_punch_request = on_punch_request
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._running = False

    async def start(self) -> int:
        """Start listening for incoming punch requests. Returns the port."""
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: _PunchProtocol(self),
            local_addr=self._listen_addr,
        )
        self._transport = transport
        self._running = True
        port = transport.get_extra_info("sockname")[1]
        logger.info(f"Punch listener started on port {port}")
        return port

    async def stop(self) -> None:
        self._running = False
        if self._transport:
            self._transport.close()
            self._transport = None

    async def handle_datagram(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle an incoming hole punch message."""
        try:
            msg = json.loads(data.decode("utf-8"))
            msg_type = msg.get("type", "")

            if msg_type in ("hole_punch", "rendezvous_punch"):
                peer_id = msg.get("from", "")
                if peer_id:
                    logger.info(f"Incoming hole punch from {peer_id} @ {addr}")

                    # Send ACK via hole puncher (transport-aware)
                    await self._hole_puncher.send_punch_ack(addr, peer_id)

                    # Notify application
                    if self._on_punch_request:
                        await self._on_punch_request(peer_id, addr)

            elif msg_type == "hole_punch_ack":
                # Punch completed from the other side
                peer_id = msg.get("from", "")
                if peer_id:
                    session = self._hole_puncher.get_session(peer_id)
                    if session and session.status != PunchStatus.ESTABLISHED:
                        session.status = PunchStatus.ESTABLISHED
                        session.established_addr = addr
                        logger.info(f"Hole punch confirmed by {peer_id} @ {addr}")

            elif msg_type == "direct_punch":
                # Respond to direct test using listener's own transport
                if self._transport:
                    self._transport.sendto(b"ASIM_PUNCH_DIRECT_ACK", addr)

        except (json.JSONDecodeError, UnicodeDecodeError):
            # Handle raw messages
            if data == b"ASIM_PUNCH_DIRECT_TEST":
                if self._transport:
                    self._transport.sendto(b"ASIM_PUNCH_DIRECT_ACK", addr)
            elif data == b"ASIM_PUNCH_ACK":
                pass  # Handled elsewhere


class _PunchProtocol(asyncio.DatagramProtocol):
    """Internal UDP protocol handler for PunchListener."""

    def __init__(self, listener: PunchListener):
        self._listener = listener

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        asyncio.ensure_future(self._listener.handle_datagram(data, addr))


# ─── Singleton Accessors ─────────────────────────────────────────────────────

_HOLE_PUNCHER: Optional[HolePuncher] = None
_RENDEZVOUS_SERVER: Optional[RendezvousServer] = None
_HOLE_PUNCHER_LOCK = asyncio.Lock()


async def get_hole_puncher(
    node_id: str,
    stun_client: Optional[STUNClient] = None,
    nat_detector: Optional[NATDetector] = None,
    turn_client: Optional[TURNClient] = None,
    rendezvous_client: Optional[RendezvousClient] = None,
    local_addr: Optional[Tuple[str, int]] = None,
) -> HolePuncher:
    """Get or create the singleton HolePuncher."""
    global _HOLE_PUNCHER
    if _HOLE_PUNCHER is None:
        async with _HOLE_PUNCHER_LOCK:
            if _HOLE_PUNCHER is None:
                _HOLE_PUNCHER = HolePuncher(
                    node_id=node_id,
                    stun_client=stun_client,
                    nat_detector=nat_detector,
                    turn_client=turn_client,
                    rendezvous_client=rendezvous_client,
                    local_addr=local_addr,
                )
    return _HOLE_PUNCHER


async def get_rendezvous_server(
    host: str = "0.0.0.0",
    port: int = _RENDEZVOUS_PORT,
) -> RendezvousServer:
    """Get or create the singleton RendezvousServer."""
    global _RENDEZVOUS_SERVER
    if _RENDEZVOUS_SERVER is None:
        _RENDEZVOUS_SERVER = RendezvousServer(host=host, port=port)
        await _RENDEZVOUS_SERVER.start()
    return _RENDEZVOUS_SERVER


def reset_hole_puncher() -> None:
    """Reset the singleton (for testing)."""
    global _HOLE_PUNCHER
    _HOLE_PUNCHER = None
