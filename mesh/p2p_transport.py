#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade P2P transport
ASIMNEXUS P2P Transport Layer
=============================
Asyncio-based UDP + WebSocket transport for mesh networking.
Provides message-based communication between mesh nodes.

Features:
- UDP peer-to-peer messaging (for Kademlia DHT RPC)
- WebSocket server/client (for CRDT sync streaming)
- Connection lifecycle management with session state machine
- Peer handshake protocol (HELLO/ACK)
- Exponential backoff retry on failures
- Periodic health PING/PONG with timeout detection
- Message serialization (JSON + length-prefixed framing)
- Peer health tracking
"""

import os
import json
import time
import logging
import asyncio
import struct
import ssl
from core.event_bus import event_bus, ASIMEvent, EventType
from typing import Dict, List, Optional, Any, Callable, Awaitable, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from mesh.stun_turn import NATClassification

logger = logging.getLogger("AsimNexus.Mesh.P2PTransport")


# ---------------------------------------------------------------------------
# Structured error types
# ---------------------------------------------------------------------------

class TransportError(Exception):
    """Base exception for all P2P transport errors."""
    def __init__(self, message: str, peer_id: Optional[str] = None):
        self.peer_id = peer_id
        super().__init__(message)


class ConnectionError(TransportError):
    """A connection-level failure (TCP/UDP connect failed)."""


class HandshakeError(TransportError):
    """Peer handshake (HELLO/ACK) failed."""


class MessageTooLargeError(TransportError):
    """Message exceeds maximum allowed size."""


class RateLimitError(TransportError):
    """Connection rate limit exceeded."""


class SecurityError(TransportError):
    """TLS/mTLS authentication failure."""


class TransportTimeoutError(TransportError):
    """Operation timed out."""


# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------

P2P_MAGIC = b"ASIM"  # 4-byte magic header (protocol constant — not configurable)
P2P_VERSION = 1

# Retry constants (all configurable via environment variables)
INITIAL_RETRY_DELAY = float(os.getenv("ASIM_MESH_INITIAL_RETRY_DELAY", "1.0"))  # seconds
MAX_RETRY_DELAY = float(os.getenv("ASIM_MESH_MAX_RETRY_DELAY", "60.0"))  # seconds
RETRY_BACKOFF_MULTIPLIER = float(os.getenv("ASIM_MESH_RETRY_BACKOFF", "2.0"))
HEALTH_PING_INTERVAL = float(os.getenv("ASIM_MESH_HEALTH_PING_INTERVAL", "30.0"))  # seconds
HEALTH_PING_TIMEOUT = float(os.getenv("ASIM_MESH_HEALTH_PING_TIMEOUT", "5.0"))  # seconds
PEER_STALE_TIMEOUT = float(os.getenv("ASIM_MESH_PEER_STALE_TIMEOUT", "300.0"))  # seconds (5 min)
PEER_BAD_THRESHOLD = int(os.getenv("ASIM_MESH_PEER_BAD_THRESHOLD", "3"))  # consecutive failures

# Connection limits (configurable via environment variables)
MAX_CONNECTIONS_PER_MINUTE = int(os.getenv("ASIM_MESH_MAX_CONNECTIONS_PER_MIN", "30"))
MAX_PEERS_TOTAL = int(os.getenv("ASIM_MESH_MAX_PEERS", "500"))

# Per-peer message rate limit (max messages per second from a single peer)
PEER_MESSAGE_RATE_LIMIT = int(os.getenv("ASIM_MESH_RATE_LIMIT", "100"))

# Message size limits
MAX_MESSAGE_SIZE = int(os.getenv("ASIM_MESH_MAX_MESSAGE_SIZE", "1048576"))  # 1MB default

# Fragmentation chunk size (configurable)
TRANSPORT_CHUNK_SIZE = int(os.getenv("ASIM_MESH_CHUNK_SIZE", "4096"))


class ConnectionState(Enum):
    """Session state machine for peer connections."""
    INIT = "init"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    TIMEOUT = "timeout"
    BANNED = "banned"


# Message types for UDP DHT RPC
class RPCMessageType(Enum):
    PING = "ping"
    PONG = "pong"
    FIND_NODE = "find_node"
    NODES_FOUND = "nodes_found"
    FIND_VALUE = "find_value"
    VALUE_FOUND = "value_found"
    STORE = "store"
    STORE_ACK = "store_ack"


# Message types for WebSocket CRDT sync + lifecycle
class WSMessageType(Enum):
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    SYNC_OPERATIONS = "sync_operations"
    SYNC_ACK = "sync_ack"
    PEER_HELLO = "peer_hello"
    PEER_HELLO_ACK = "peer_hello_ack"
    PEER_PING = "peer_ping"
    PEER_PONG = "peer_pong"
    PEER_GOODBYE = "peer_goodbye"
    FRAGMENT_CHUNK = "fragment_chunk"


# ---------------------------------------------------------------------------
# Fragmentation helpers
# ---------------------------------------------------------------------------

import base64

CHUNK_SIZE = 256_000  # 256KB per chunk


def chunk_message(msg: "P2PMessage") -> "List[P2PMessage]":
    """Split a large message into chunks for transport."""
    body = msg.to_bytes()
    if len(body) <= MAX_MESSAGE_SIZE:
        return [msg]
    chunks: List[P2PMessage] = []
    total_chunks = (len(body) + CHUNK_SIZE - 1) // CHUNK_SIZE
    for i in range(0, len(body), CHUNK_SIZE):
        chunk_payload = {
            "msg_id": msg.msg_id,
            "chunk_index": i // CHUNK_SIZE,
            "total_chunks": total_chunks,
            "data": base64.b64encode(body[i:i + CHUNK_SIZE]).decode("ascii"),
        }
        chunks.append(P2PMessage(
            msg_type="fragment_chunk",
            sender_id=msg.sender_id,
            msg_id=f"{msg.msg_id}:chunk{i // CHUNK_SIZE}",
            payload=chunk_payload,
        ))
    return chunks


def reassemble_chunks(chunks: "List[P2PMessage]") -> "Optional[P2PMessage]":
    """Reassemble chunked messages into the original P2PMessage."""
    if not chunks:
        return None
    chunks.sort(key=lambda c: c.payload["chunk_index"])
    raw = b"".join(
        base64.b64decode(c.payload["data"]) for c in chunks
    )
    return P2PMessage.from_bytes(raw)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class PeerInfo:
    """Information about a known peer."""
    node_id: str
    host: str
    port_udp: int
    port_ws: int
    version: str = "1.0.0"
    last_seen: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    last_pong: float = 0.0
    ping_failures: int = 0
    consecutive_failures: int = 0
    connection_state: ConnectionState = ConnectionState.INIT
    retry_delay: float = INITIAL_RETRY_DELAY
    capabilities: List[str] = field(default_factory=list)

    def is_stale(self, max_age: float = PEER_STALE_TIMEOUT) -> bool:
        return time.time() - self.last_seen > max_age

    def is_bad(self, max_failures: int = PEER_BAD_THRESHOLD) -> bool:
        return self.consecutive_failures >= max_failures

    def is_connected(self) -> bool:
        return self.connection_state == ConnectionState.CONNECTED

    def record_success(self):
        """Record a successful communication, resetting failure counters."""
        self.last_seen = time.time()
        self.consecutive_failures = 0
        self.retry_delay = INITIAL_RETRY_DELAY
        self.connection_state = ConnectionState.CONNECTED

    def record_failure(self):
        """Record a failure, incrementing counters and applying backoff."""
        self.consecutive_failures += 1
        self.ping_failures += 1
        self.retry_delay = min(
            self.retry_delay * RETRY_BACKOFF_MULTIPLIER,
            MAX_RETRY_DELAY,
        )
        if self.is_bad():
            self.connection_state = ConnectionState.TIMEOUT

    def get_retry_delay(self) -> float:
        return self.retry_delay


@dataclass
class P2PMessage:
    """A message sent between peers."""
    msg_type: str
    sender_id: str
    msg_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3

    def to_bytes(self) -> bytes:
        data = {
            "type": self.msg_type,
            "sender": self.sender_id,
            "msg_id": self.msg_id,
            "payload": self.payload,
            "ts": self.timestamp,
            "ttl": self.ttl,
        }
        body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        header = P2P_MAGIC + struct.pack("!BI", P2P_VERSION, len(body))
        return header + body

    @classmethod
    def from_bytes(cls, raw: bytes) -> Optional['P2PMessage']:
        if len(raw) < 9:
            return None
        if raw[:4] != P2P_MAGIC:
            return None
        body_len = struct.unpack("!I", raw[5:9])[0]
        body = raw[9:9 + body_len]
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        return cls(
            msg_type=data["type"],
            sender_id=data["sender"],
            msg_id=data["msg_id"],
            payload=data.get("payload", {}),
            timestamp=data.get("ts", time.time()),
            ttl=data.get("ttl", 3),
        )


# ---------------------------------------------------------------------------
# P2P Transport
# ---------------------------------------------------------------------------


class P2PTransport:
    """
    Asyncio-based peer-to-peer transport with connection lifecycle management.

    Provides:
    - UDP socket for DHT RPC messages
    - WebSocket server for CRDT sync connections
    - WebSocket client for connecting to peers (persistent)
    - Peer handshake protocol (HELLO/ACK)
    - Session state machine (INIT → CONNECTING → CONNECTED → DISCONNECTED/TIMEOUT)
    - Exponential backoff retry on failures
    - Periodic health PING/PONG with timeout detection
    - Message routing and peer management
    """

    # Class-level constants (can be overridden by env vars)
    DEFAULT_PORT: int = int(os.environ.get("ASIM_MESH_P2P_PORT", "7333"))
    MAX_CONNECTIONS: int = int(os.environ.get("ASIM_MESH_P2P_MAX_CONNECTIONS", "50"))
    MESSAGE_TIMEOUT: int = int(os.environ.get("ASIM_MESH_P2P_MESSAGE_TIMEOUT", "30"))

    def __init__(
        self,
        node_id: str,
        host: str = "0.0.0.0",
        port_udp: int = 7332,
        port_ws: Optional[int] = None,
        port: Optional[int] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
    ):
        self.node_id = node_id
        self.host = host
        self.port_udp = port_udp
        # Resolve port_ws: explicit port > explicit port_ws > env var > class default
        env_port = os.environ.get("ASIM_MESH_P2P_PORT")
        if port is not None:
            self.port_ws = port
        elif port_ws is not None:
            self.port_ws = port_ws
        elif env_port is not None:
            self.port_ws = int(env_port)
        else:
            self.port_ws = self.DEFAULT_PORT
        self._ssl_context = ssl_context

        # Peer management
        self.peers: Dict[str, PeerInfo] = {}

        # Message handlers (registered by components like DHT, CRDT)
        self._rpc_handlers: Dict[str, Callable[[P2PMessage], Awaitable[Optional[P2PMessage]]]] = {}
        self._ws_handlers: Dict[str, Callable[[P2PMessage], Awaitable[None]]] = {}

        # Transport state
        self._running = False
        self._udp_transport: Optional[asyncio.DatagramTransport] = None
        self._ws_server: Optional[asyncio.AbstractServer] = None
        # Persistent WS connections: node_id -> (reader, writer)
        self._ws_connections: Dict[str, Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None

        # Pending RPC responses: msg_id -> Future
        self._pending_rpcs: Dict[str, asyncio.Future] = {}

        # Message ID counter
        self._msg_counter = 0

        # Lock for peer map access
        self._lock = asyncio.Lock()

        # Connection rate limiting (rolling window of connection timestamps)
        self._connection_timestamps: List[float] = []

        # Per-peer message rate limiting: peer_id -> list of message timestamps
        self._rate_limiter: Dict[str, List[float]] = {}

        # Fragment reassembly buffers: msg_id -> list of chunks
        self._chunk_buffers: Dict[str, List[P2PMessage]] = {}

        # Internal event emitters: event_name -> list of handler callbacks
        self._emitters: Dict[str, List[Callable]] = {}

        # NAT classification (populated by NATDetector at startup)
        self.nat_classification: Optional['NATClassification'] = None  # noqa: F821

        # Hole punch handler (registered by HolePuncher for incoming punch messages)
        self._punch_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None

        logger.info(
            f"🔌 P2PTransport initialized — Node: {node_id}, "
            f"UDP: {host}:{port_udp}, WS: {host}:{port_ws}"
        )

    @property
    def port(self) -> int:
        """Return the primary (WebSocket) port for compatibility with tests."""
        return self.port_ws

    def _next_msg_id(self) -> str:
        self._msg_counter += 1
        return f"{self.node_id}:{self._msg_counter:x}:{int(time.time() * 1000)}"

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def on_rpc(self, msg_type: str, handler: Callable[[P2PMessage], Awaitable[Optional[P2PMessage]]]):
        """Register a handler for a UDP RPC message type."""
        self._rpc_handlers[msg_type] = handler

    def on_ws_message(self, msg_type: str, handler: Callable[[P2PMessage], Awaitable[None]]):
        """Register a handler for a WebSocket message type."""
        self._ws_handlers[msg_type] = handler

    def register_punch_handler(self, handler: Callable[[str, Dict[str, Any]], Awaitable[None]]):
        """
        Register a handler for incoming hole punch messages.
        
        When a HOLE_PUNCH message is received via UDP, the transport
        will dispatch it to this handler. The handler receives the
        sender's node_id and the message payload.
        """
        self._punch_handler = handler
        # Register as RPC handler too so it gets dispatched
        async def _punch_rpc_handler(msg: P2PMessage) -> None:
            if self._punch_handler:
                await self._punch_handler(msg.sender_id, msg.payload)
        self._rpc_handlers["HOLE_PUNCH"] = _punch_rpc_handler

    def set_nat_classification(self, classification: 'NATClassification') -> None:
        """Store the NAT classification result from NATDetector."""
        self.nat_classification = classification

    # ------------------------------------------------------------------
    # Internal event emitters
    # ------------------------------------------------------------------

    def on(self, event: str, handler: Callable):
        """
        Register a handler for an internal transport event.

        Args:
            event: Event name (e.g. 'peer_connected', 'peer_disconnected').
            handler: Callable that receives event data as keyword arguments.
        """
        if event not in self._emitters:
            self._emitters[event] = []
        self._emitters[event].append(handler)

    def _emit(self, event: str, **data):
        """
        Emit an internal transport event to all registered handlers.

        Args:
            event: Event name.
            **data: Event data passed as keyword arguments to handlers.
        """
        handlers = self._emitters.get(event, [])
        for handler in handlers:
            try:
                handler(**data)
            except Exception as e:
                logger.debug(f"Emitter handler error for {event}: {e}")

    # ------------------------------------------------------------------
    # Peer management
    # ------------------------------------------------------------------

    @property
    def is_secure(self) -> bool:
        """Whether this transport uses TLS/mTLS."""
        return self._ssl_context is not None


    async def add_peer(self, node_id: str, host: str, port_udp: int, port_ws: int,
                       capabilities: Optional[List[str]] = None) -> PeerInfo:
        """Add or update a peer in the routing table."""
        async with self._lock:
            if node_id in self.peers:
                peer = self.peers[node_id]
                peer.host = host
                peer.port_udp = port_udp
                peer.port_ws = port_ws
                peer.last_seen = time.time()
                if capabilities:
                    peer.capabilities = capabilities
            else:
                peer = PeerInfo(
                    node_id=node_id,
                    host=host,
                    port_udp=port_udp,
                    port_ws=port_ws,
                    capabilities=capabilities or [],
                )
                self.peers[node_id] = peer
            return peer

    async def remove_peer(self, node_id: str):
        """Remove a peer and close its persistent connection."""
        async with self._lock:
            self.peers.pop(node_id, None)
        # Close persistent WS connection if any
        if node_id in self._ws_connections:
            _, writer = self._ws_connections.pop(node_id)
            try:
                writer.close()
            except Exception:
                pass
        logger.info(f"🔌 Removed peer: {node_id}")

    async def get_peer(self, node_id: str) -> Optional[PeerInfo]:
        async with self._lock:
            return self.peers.get(node_id)

    async def get_online_peers(self) -> List[PeerInfo]:
        async with self._lock:
            return [p for p in self.peers.values() if p.is_connected() and not p.is_bad()]

    async def get_all_peers(self) -> List[PeerInfo]:
        async with self._lock:
            return list(self.peers.values())

    # ------------------------------------------------------------------
    # UDP Transport (for DHT RPC + Hole Punch)
    # ------------------------------------------------------------------

    async def _handle_udp_message(self, data: bytes, addr: tuple):
        """Handle an incoming UDP message."""
        host, port = addr
        msg = P2PMessage.from_bytes(data)
        if msg is None:
            # Not a P2PMessage — might be raw STUN or other protocol
            logger.debug(f"Non-P2P UDP message from {host}:{port} ({len(data)} bytes)")
            return

        # Update peer last_seen if known
        async with self._lock:
            if msg.sender_id in self.peers:
                self.peers[msg.sender_id].record_success()

        # Check if this is a response to a pending RPC
        if msg.msg_id in self._pending_rpcs:
            future = self._pending_rpcs.pop(msg.msg_id)
            if not future.done():
                future.set_result(msg)
            return

        handler = self._rpc_handlers.get(msg.msg_type)
        if handler:
            try:
                response = await handler(msg)
                if response is not None and self._udp_transport:
                    self._udp_transport.sendto(response.to_bytes(), addr)
            except Exception as e:
                logger.error(f"RPC handler error for {msg.msg_type}: {e}")
        else:
            logger.debug(f"No handler for RPC type: {msg.msg_type}")

    async def send_udp(self, peer: PeerInfo, msg: P2PMessage,
                       retry: bool = True) -> bool:
        """
        Send a UDP message to a peer with optional exponential backoff retry.

        Uses the main UDP server transport for sending, so that any
        response (e.g., PONG) arrives at our listening socket.
        Falls back to a temporary socket if the server transport
        is not yet available.
        """
        max_attempts = 3 if retry else 1
        delay = INITIAL_RETRY_DELAY

        for attempt in range(max_attempts):
            try:
                if self._udp_transport is not None:
                    self._udp_transport.sendto(
                        msg.to_bytes(),
                        (peer.host, peer.port_udp),
                    )
                    peer.last_ping = time.time()
                    peer.record_success()
                    return True

                # Fallback: create a temporary connected socket
                loop = asyncio.get_event_loop()
                transport, protocol = await loop.create_datagram_endpoint(
                    asyncio.DatagramProtocol,
                    remote_addr=(peer.host, peer.port_udp),
                )
                try:
                    transport.sendto(msg.to_bytes())
                    peer.last_ping = time.time()
                    peer.record_success()
                    return True
                finally:
                    transport.close()

            except Exception as e:
                logger.debug(f"UDP send to {peer.node_id} failed (attempt {attempt + 1}/{max_attempts}): {e}")
                peer.record_failure()
                # Emit RPC timeout event (use msg.msg_type from the P2PMessage object)
                try:
                    await event_bus.publish(ASIMEvent(
                        event_type=EventType.RPC_TIMEOUT,
                        source="P2PTransport",
                        data={"peer_id": peer.node_id, "msg_type": msg.msg_type},
                    ))
                except Exception:
                    pass
                if attempt < max_attempts - 1 and retry:
                    await asyncio.sleep(delay)
                    delay = min(delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)

        return False

    async def send_udp_to(self, host: str, port: int, msg_type: str,
                          payload: Dict[str, Any]) -> bool:
        """
        Send a UDP message to an arbitrary address (no PeerInfo needed).
        
        Used by hole punching to send punch messages to STUN-discovered
        public addresses that are not yet in the routing table.
        """
        msg = P2PMessage(
            msg_type=msg_type,
            sender_id=self.node_id,
            msg_id=self._next_msg_id(),
            payload=payload,
        )
        try:
            if self._udp_transport is not None:
                self._udp_transport.sendto(msg.to_bytes(), (host, port))
                return True
            # Fallback: create temporary socket
            loop = asyncio.get_event_loop()
            transport, protocol = await loop.create_datagram_endpoint(
                asyncio.DatagramProtocol,
                remote_addr=(host, port),
            )
            try:
                transport.sendto(msg.to_bytes())
                return True
            finally:
                transport.close()
        except Exception as e:
            logger.debug(f"send_udp_to({host}:{port}, {msg_type}) failed: {e}")
            return False

    async def rpc_call(
        self, peer: PeerInfo, msg_type: str, payload: Dict[str, Any],
        timeout: float = 5.0
    ) -> Optional[P2PMessage]:
        """
        Send an RPC call and wait for response.
        Uses UDP with a future-based response matching.
        """
        msg_id = self._next_msg_id()
        msg = P2PMessage(
            msg_type=msg_type,
            sender_id=self.node_id,
            msg_id=msg_id,
            payload=payload,
        )

        # Create a future to wait for the response
        response_future: asyncio.Future[P2PMessage] = asyncio.Future()
        self._pending_rpcs[msg_id] = response_future

        # Find the expected response type
        response_type_map = {
            RPCMessageType.PING.value: RPCMessageType.PONG.value,
            RPCMessageType.FIND_NODE.value: RPCMessageType.NODES_FOUND.value,
            RPCMessageType.FIND_VALUE.value: RPCMessageType.VALUE_FOUND.value,
            RPCMessageType.STORE.value: RPCMessageType.STORE_ACK.value,
        }
        expected_response = response_type_map.get(msg_type)

        # Register a one-shot handler for the expected response
        if expected_response:
            original = self._rpc_handlers.get(expected_response)

            async def response_handler(resp_msg: P2PMessage) -> Optional[P2PMessage]:
                if not response_future.done():
                    response_future.set_result(resp_msg)
                return None

            self._rpc_handlers[expected_response] = response_handler

        try:
            sent = await self.send_udp(peer, msg)
            if not sent:
                self._pending_rpcs.pop(msg_id, None)
                return None

            # Wait for response with timeout
            try:
                result = await asyncio.wait_for(response_future, timeout)
                return result
            except asyncio.TimeoutError:
                logger.debug(f"RPC timeout for {msg_type} to {peer.node_id}")
                peer.record_failure()
                self._pending_rpcs.pop(msg_id, None)
                return None
        finally:
            # Clean up one-shot handler
            if expected_response:
                if self._rpc_handlers.get(expected_response) is response_handler:
                    if original:
                        self._rpc_handlers[expected_response] = original
                    else:
                        del self._rpc_handlers[expected_response]

    # ------------------------------------------------------------------
    # WebSocket Transport (for CRDT Sync + persistent connections)
    # ------------------------------------------------------------------

    async def _handle_ws_connection(self, reader: asyncio.StreamReader,
                                    writer: asyncio.StreamWriter):
        """Handle an incoming WebSocket connection with handshake."""
        peer_addr = writer.get_extra_info("peername")
        logger.info(f"🔗 New WS connection from {peer_addr}")

        peer_id: Optional[str] = None

        try:
            while self._running:
                # Read message length prefix (4 bytes, big-endian)
                header = await reader.readexactly(4)
                msg_len = struct.unpack("!I", header)[0]

                if msg_len > 1_000_000:  # 1MB limit
                    logger.warning(f"Message too large: {msg_len} from {peer_addr}")
                    break

                # Read message body
                data = await reader.readexactly(msg_len)
                msg = P2PMessage.from_bytes(data)
                if msg is None:
                    logger.warning(f"Invalid WS message from {peer_addr}")
                    continue

                peer_id = msg.sender_id

                # Per-peer message rate limiting
                if peer_id:
                    now = time.time()
                    if peer_id not in self._rate_limiter:
                        self._rate_limiter[peer_id] = []
                    # Prune timestamps older than 1 second
                    self._rate_limiter[peer_id] = [
                        t for t in self._rate_limiter[peer_id]
                        if now - t < 1.0
                    ]
                    if len(self._rate_limiter[peer_id]) >= PEER_MESSAGE_RATE_LIMIT:
                        logger.warning(
                            f"Rate limit exceeded for peer {peer_id}: "
                            f"{len(self._rate_limiter[peer_id])} msgs in 1s "
                            f"(max {PEER_MESSAGE_RATE_LIMIT})"
                        )
                        # Drop the message — send rate limit error response
                        try:
                            await self._send_ws_raw(writer, P2PMessage(
                                msg_type="rate_limit_error",
                                sender_id=self.node_id,
                                msg_id=self._next_msg_id(),
                                payload={
                                    "message": f"Rate limit exceeded: max {PEER_MESSAGE_RATE_LIMIT} msgs/s",
                                    "retry_after": 1.0,
                                },
                            ))
                        except Exception:
                            pass
                        continue
                    self._rate_limiter[peer_id].append(now)

                # Handle lifecycle messages
                if msg.msg_type == WSMessageType.PEER_HELLO.value:
                    await self._handle_peer_hello(peer_id, msg, reader, writer)
                    continue

                if msg.msg_type == WSMessageType.PEER_PING.value:
                    await self._send_ws_raw(writer, P2PMessage(
                        msg_type=WSMessageType.PEER_PONG.value,
                        sender_id=self.node_id,
                        msg_id=self._next_msg_id(),
                        payload={"timestamp": time.time()},
                    ))
                    continue

                if msg.msg_type == WSMessageType.PEER_PONG.value:
                    async with self._lock:
                        if peer_id in self.peers:
                            self.peers[peer_id].last_pong = time.time()
                            self.peers[peer_id].record_success()
                    continue

                if msg.msg_type == WSMessageType.PEER_GOODBYE.value:
                    logger.info(f"👋 Peer {peer_id} disconnected gracefully")
                    async with self._lock:
                        if peer_id in self.peers:
                            self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED
                    break

                # Fragment chunk: buffer and reassemble when complete
                if msg.msg_type == WSMessageType.FRAGMENT_CHUNK.value:
                    original_id = msg.payload.get("msg_id", msg.msg_id)
                    if original_id not in self._chunk_buffers:
                        self._chunk_buffers[original_id] = []
                    self._chunk_buffers[original_id].append(msg)
                    total = msg.payload.get("total_chunks", 0)
                    if len(self._chunk_buffers[original_id]) >= total:
                        reassembled = reassemble_chunks(self._chunk_buffers.pop(original_id))
                        if reassembled:
                            msg = reassembled
                            peer_id = msg.sender_id
                        else:
                            continue
                    else:
                        continue


                # Update peer state on any message
                async with self._lock:
                    if peer_id in self.peers:
                        self.peers[peer_id].record_success()
                        self.peers[peer_id].connection_state = ConnectionState.CONNECTED

                # Route to registered handler
                handler = self._ws_handlers.get(msg.msg_type)
                if handler:
                    try:
                        await handler(msg)
                    except Exception as e:
                        logger.error(f"WS handler error for {msg.msg_type}: {e}")
                else:
                    logger.debug(f"No handler for WS type: {msg.msg_type}")

        except asyncio.IncompleteReadError:
            logger.debug(f"WS connection closed by {peer_addr}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WS connection error from {peer_addr}: {e}")
        finally:
            if peer_id and peer_id in self._ws_connections:
                self._ws_connections.pop(peer_id, None)
            async with self._lock:
                if peer_id and peer_id in self.peers:
                    self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED
            try:
                writer.close()
            except Exception:
                pass
            # Schedule auto-reconnect if transport is still running
            if peer_id and self._running:
                async with self._lock:
                    peer = self.peers.get(peer_id)
                if peer and not peer.is_bad():
                    delay = min(peer.retry_delay, MAX_RETRY_DELAY)
                    asyncio.create_task(self._reconnect_peer(peer_id, delay))
            # Emit peer disconnected event
            if peer_id:
                try:
                    await event_bus.publish(ASIMEvent(
                        event_type=EventType.PEER_DISCONNECTED,
                        source="P2PTransport",
                        data={"peer_id": peer_id, "reason": "connection_closed"},
                    ))
                except Exception:
                    pass
            logger.info(f"🔌 WS connection closed from {peer_addr}")

    async def _reconnect_peer(self, peer_id: str, delay: float):
        """Attempt to reconnect to a peer after a dropped connection."""
        await asyncio.sleep(delay)
        async with self._lock:
            peer = self.peers.get(peer_id)
            if not peer or peer.connection_state == ConnectionState.CONNECTED:
                return
            peer.connection_state = ConnectionState.CONNECTING
        try:
            new_id = await self.connect_peer(peer.host, peer.port_ws)
            if new_id:
                logger.info(f"🔡 Reconnected to peer {peer_id}")
        except Exception as e:
            logger.debug(f"Reconnection to {peer_id} failed: {e}")
            async with self._lock:
                p = self.peers.get(peer_id)
                if p:
                    p.record_failure()

    async def _handle_peer_hello(self, peer_id: str, msg: P2PMessage,
                                  reader: asyncio.StreamReader,
                                  writer: asyncio.StreamWriter):
        """Handle an incoming PEER_HELLO handshake message."""
        payload = msg.payload
        host = payload.get("host", "0.0.0.0")
        port_udp = payload.get("port_udp", 7332)
        port_ws = payload.get("port_ws", 7333)
        version = payload.get("version", "1.0.0")
        capabilities = payload.get("capabilities", [])

        logger.info(f"🤝 Handshake from peer {peer_id} (v{version})")

        # Add or update peer
        await self.add_peer(
            node_id=peer_id,
            host=host,
            port_udp=port_udp,
            port_ws=port_ws,
            capabilities=capabilities,
        )

        async with self._lock:
            if peer_id in self.peers:
                self.peers[peer_id].connection_state = ConnectionState.CONNECTED
                self.peers[peer_id].version = version

        # Store persistent connection
        self._ws_connections[peer_id] = (reader, writer)

        # Send HELLO_ACK
        ack = P2PMessage(
            msg_type=WSMessageType.PEER_HELLO_ACK.value,
            sender_id=self.node_id,
            msg_id=self._next_msg_id(),
            payload={
                "host": self.host,
                "port_udp": self.port_udp,
                "port_ws": self.port_ws,
                "version": "1.0.0",
                "capabilities": [],
                "peer_id": self.node_id,
            },
        )
        await self._send_ws_raw(writer, ack)
        logger.info(f"✅ Handshake complete with {peer_id}")
        # Emit peer connected event
        try:
            await event_bus.publish(ASIMEvent(
                event_type=EventType.PEER_CONNECTED,
                source="P2PTransport",
                data={
                    "peer_id": peer_id,
                    "host": host,
                    "port_ws": port_ws,
                    "version": version,
                    "transport_secure": self.is_secure,
                },
            ))
        except Exception:
            pass

    async def connect_peer(self, host: str, port_ws: int,
                           timeout: float = 5.0) -> Optional[str]:
        """
        Connect to a peer via WebSocket and perform handshake.

        Returns the peer's node_id on success, None on failure.
        The persistent connection is stored in self._ws_connections.
        """
        # Rate limiting: reject if exceeding MAX_CONNECTIONS_PER_MINUTE
        now = time.time()
        window_start = now - 60.0
        self._connection_timestamps = [t for t in self._connection_timestamps if t > window_start]
        if len(self._connection_timestamps) >= MAX_CONNECTIONS_PER_MINUTE:
            logger.warning(
                f"Rate limit exceeded: {len(self._connection_timestamps)} connections in last 60s "
                f"(max {MAX_CONNECTIONS_PER_MINUTE})"
            )
            raise RateLimitError(
                f"Connection rate limit exceeded: {len(self._connection_timestamps)} "
                f"connections in last 60s"
            )
        self._connection_timestamps.append(now)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port_ws, ssl=self._ssl_context),
                timeout=timeout,
            )

            # Send HELLO
            hello = P2PMessage(
                msg_type=WSMessageType.PEER_HELLO.value,
                sender_id=self.node_id,
                msg_id=self._next_msg_id(),
                payload={
                    "host": self.host,
                    "port_udp": self.port_udp,
                    "port_ws": self.port_ws,
                    "version": "1.0.0",
                    "capabilities": [],
                    "peer_id": self.node_id,
                },
            )
            await self._send_ws_raw(writer, hello)

            # Wait for HELLO_ACK
            header = await asyncio.wait_for(reader.readexactly(4), timeout=timeout)
            msg_len = struct.unpack("!I", header)[0]
            data = await asyncio.wait_for(reader.readexactly(msg_len), timeout=timeout)
            response = P2PMessage.from_bytes(data)

            if response and response.msg_type == WSMessageType.PEER_HELLO_ACK.value:
                peer_id = response.payload.get("peer_id", response.sender_id)
                capabilities = response.payload.get("capabilities", [])

                await self.add_peer(
                    node_id=peer_id,
                    host=response.payload.get("host", host),
                    port_udp=response.payload.get("port_udp", 7332),
                    port_ws=response.payload.get("port_ws", port_ws),
                    capabilities=capabilities,
                )

                async with self._lock:
                    if peer_id in self.peers:
                        self.peers[peer_id].connection_state = ConnectionState.CONNECTED
                        self.peers[peer_id].version = response.payload.get("version", "1.0.0")

                # Store persistent connection
                self._ws_connections[peer_id] = (reader, writer)

                # Start a background reader for this outbound connection.
                # This mirrors the read loop that the server-side handler
                # (_handle_ws_connection) provides for inbound connections.
                # Without this, responses (e.g. PONG, SYNC_RESPONSE) sent
                # by the remote peer would be stuck in the TCP buffer unread.
                asyncio.create_task(self._handle_ws_connection(reader, writer))

                logger.info(f"✅ Connected to peer {peer_id} at {host}:{port_ws}")
                return peer_id
            else:
                logger.warning(f"Unexpected handshake response from {host}:{port_ws}")
                writer.close()
                return None

        except asyncio.TimeoutError:
            logger.debug(f"Connection timeout to {host}:{port_ws}")
            return None
        except Exception as e:
            logger.debug(f"Connection failed to {host}:{port_ws}: {e}")
            return None

    async def _send_ws_raw(self, writer: asyncio.StreamWriter, msg: P2PMessage) -> bool:
        """Send a message over an existing WebSocket connection."""
        try:
            data = msg.to_bytes()
            writer.write(struct.pack("!I", len(data)))
            writer.write(data)
            await writer.drain()
            return True
        except Exception as e:
            logger.debug(f"WS raw send failed: {e}")
            return False

    async def send_ws(self, peer: PeerInfo, msg: P2PMessage,
                      retry: bool = True) -> bool:
        """
        Send a message to a peer over WebSocket using persistent connection.

        If no persistent connection exists, attempts to establish one.
        Falls back to one-shot connection if persistent fails.
        Supports exponential backoff retry.
        Automatically chunks messages larger than MAX_MESSAGE_SIZE.
        """
        # Auto-chunk large messages and send each chunk individually
        chunks = chunk_message(msg)
        if len(chunks) > 1:
            logger.debug(f"Chunking {msg.msg_id} into {len(chunks)} fragments")
            for chunk in chunks:
                ok = await self._send_ws_single(peer, chunk, retry)
                if not ok:
                    return False
            return True

        # Non-chunked message: delegate to _send_ws_single
        return await self._send_ws_single(peer, msg, retry)

    async def _send_ws_single(self, peer: PeerInfo, msg: P2PMessage,
                             retry: bool = True) -> bool:
        """
        Send a single message to a peer over WebSocket.
        Handles persistent connections, connection setup, and retry.
        Used by send_ws() for both regular and chunked messages.
        """
        max_attempts = 3 if retry else 1
        delay = INITIAL_RETRY_DELAY

        for attempt in range(max_attempts):
            try:
                # Try persistent connection first
                if peer.node_id in self._ws_connections:
                    _, writer = self._ws_connections[peer.node_id]
                    success = await self._send_ws_raw(writer, msg)
                    if success:
                        peer.record_success()
                        return True
                    else:
                        # Persistent connection broken, remove it
                        self._ws_connections.pop(peer.node_id, None)
                        logger.debug(f"Persistent WS connection to {peer.node_id} broken, reconnecting...")

                # Try to establish persistent connection
                peer_id = await self.connect_peer(peer.host, peer.port_ws)
                if peer_id:
                    return await self._send_ws_single(peer, msg, retry=False)

                # Fallback: one-shot connection
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(peer.host, peer.port_ws),
                    timeout=5.0,
                )
                try:
                    # Send HELLO first if not already connected
                    hello = P2PMessage(
                        msg_type=WSMessageType.PEER_HELLO.value,
                        sender_id=self.node_id,
                        msg_id=self._next_msg_id(),
                        payload={
                            "host": self.host,
                            "port_udp": self.port_udp,
                            "port_ws": self.port_ws,
                            "version": "1.0.0",
                            "capabilities": [],
                        },
                    )
                    await self._send_ws_raw(writer, hello)

                    # Wait for ACK
                    header = await asyncio.wait_for(reader.readexactly(4), timeout=5.0)
                    msg_len = struct.unpack("!I", header)[0]
                    ack_data = await asyncio.wait_for(reader.readexactly(msg_len), timeout=5.0)
                    P2PMessage.from_bytes(ack_data)

                    # Now send the actual message
                    success = await self._send_ws_raw(writer, msg)
                    if success:
                        peer.record_success()
                        return True

                finally:
                    writer.close()

            except Exception as e:
                logger.debug(f"WS send to {peer.node_id} failed (attempt {attempt + 1}/{max_attempts}): {e}")
                peer.record_failure()
                if attempt < max_attempts - 1 and retry:
                    await asyncio.sleep(delay)
                    delay = min(delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)

        return False

    async def broadcast_ws(self, msg: P2PMessage) -> int:
        """Broadcast a message to all connected peers. Returns count."""
        count = 0
        peers = await self.get_online_peers()
        for peer in peers:
            if await self.send_ws(peer, msg):
                count += 1
        return count

    # ------------------------------------------------------------------
    # Health PING/PONG
    # ------------------------------------------------------------------

    async def _ping_loop(self):
        """Periodically send PING to all connected peers."""
        while self._running:
            await asyncio.sleep(HEALTH_PING_INTERVAL)
            peers = await self.get_online_peers()
            for peer in peers:
                if not self._running:
                    break
                ping = P2PMessage(
                    msg_type=WSMessageType.PEER_PING.value,
                    sender_id=self.node_id,
                    msg_id=self._next_msg_id(),
                    payload={"timestamp": time.time()},
                )
                success = await self.send_ws(peer, ping, retry=False)
                if not success:
                    logger.debug(f"Ping to {peer.node_id} failed")
                    peer.record_failure()
                else:
                    # Check if we got a PONG in time (checked in cleanup)
                    peer.last_ping = time.time()

    async def _check_pong_timeouts(self):
        """Check if any peers failed to respond to PING."""
        async with self._lock:
            now = time.time()
            for peer_id, peer in self.peers.items():
                if (peer.connection_state == ConnectionState.CONNECTED
                        and peer.last_ping > peer.last_pong
                        and now - peer.last_ping > HEALTH_PING_TIMEOUT):
                    logger.warning(f"⚠️ Peer {peer_id} missed PONG, marking TIMEOUT")
                    peer.connection_state = ConnectionState.TIMEOUT
                    peer.record_failure()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self):
        """Start the transport layer."""
        if self._running:
            return
        self._running = True

        loop = asyncio.get_event_loop()

        # Start UDP server for DHT RPC
        udp_port = self.port_udp
        try:
            udp_transport, udp_protocol = await loop.create_datagram_endpoint(
                lambda: _UDPProtocol(self._handle_udp_message),
                local_addr=(self.host, udp_port),
            )
            self._udp_transport = udp_transport
            # If OS assigned port (port 0), capture the actual bound port
            if udp_port == 0:
                sockname = udp_transport.get_extra_info("sockname")
                if sockname:
                    udp_port = sockname[1]
            self.port_udp = udp_port
            logger.info(f"📡 UDP server listening on {self.host}:{self.port_udp}")
        except Exception as e:
            logger.warning(f"UDP server failed to start on {self.host}:{self.port_udp}: {e}")
            # Fallback: try with port 0 (OS-assigned) to avoid port conflicts
            try:
                logger.info(f"🔄 Retrying UDP bind on {self.host}:0 (OS-assigned port)")
                udp_transport, udp_protocol = await loop.create_datagram_endpoint(
                    lambda: _UDPProtocol(self._handle_udp_message),
                    local_addr=(self.host, 0),
                )
                self._udp_transport = udp_transport
                sockname = udp_transport.get_extra_info("sockname")
                if sockname:
                    udp_port = sockname[1]
                self.port_udp = udp_port
                logger.info(f"📡 UDP server listening on {self.host}:{self.port_udp} (fallback)")
            except Exception as e2:
                logger.error(f"UDP server fallback also failed on {self.host}:0: {e2}")

        # Start TCP/WebSocket server for CRDT sync + persistent connections
        try:
            self._ws_server = await asyncio.start_server(
                self._handle_ws_connection,
                self.host,
                self.port_ws,
                ssl=self._ssl_context,
            )
            logger.info(f"🔗 WS server listening on {self.host}:{self.port_ws}")
        except Exception as e:
            logger.warning(f"WS server failed to start on {self.port_ws}: {e}")

        # Start ping loop
        self._ping_task = asyncio.create_task(self._ping_loop())

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info(f"🔌 P2PTransport started — Node: {self.node_id}")
        # Emit transport started event
        try:
            await event_bus.publish(ASIMEvent(
                event_type=EventType.TRANSPORT_STATE_CHANGE,
                source="P2PTransport",
                data={"state": "started", "node_id": self.node_id},
            ))
        except Exception:
            pass

    async def stop(self):
        """Stop the transport layer."""
        self._running = False

        # Cancel ping task
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Send goodbye to all connected peers
        goodbye = P2PMessage(
            msg_type=WSMessageType.PEER_GOODBYE.value,
            sender_id=self.node_id,
            msg_id=self._next_msg_id(),
        )
        peers = await self.get_online_peers()
        for peer in peers:
            try:
                await self.send_ws(peer, goodbye, retry=False)
            except Exception:
                pass

        # Close persistent WS connections
        for node_id in list(self._ws_connections.keys()):
            _, writer = self._ws_connections.pop(node_id)
            try:
                writer.close()
            except Exception:
                pass

        # Close UDP transport
        if self._udp_transport:
            self._udp_transport.close()
            self._udp_transport = None

        # Close WS server
        if self._ws_server:
            self._ws_server.close()
            await self._ws_server.wait_closed()
            self._ws_server = None

        # Clear pending RPCs
        for future in self._pending_rpcs.values():
            if not future.done():
                future.cancel()
        self._pending_rpcs.clear()

        logger.info("🔌 P2PTransport stopped")
        # Emit transport stopped event
        try:
            await event_bus.publish(ASIMEvent(
                event_type=EventType.TRANSPORT_STATE_CHANGE,
                source="P2PTransport",
                data={"state": "stopped", "node_id": self.node_id},
            ))
        except Exception:
            pass

    async def _cleanup_loop(self):
        """Periodic cleanup of stale/bad peers."""
        while self._running:
            await asyncio.sleep(60)
            try:
                await self._check_pong_timeouts()

                async with self._lock:
                    now = time.time()
                    stale_ids = [
                        peer_id for peer_id, peer in self.peers.items()
                        if peer.is_stale()
                    ]
                    bad_ids = [
                        peer_id for peer_id, peer in self.peers.items()
                        if peer.is_bad() and peer_id in self._ws_connections
                    ]

                for peer_id in stale_ids:
                    logger.debug(f"🧹 Removing stale peer: {peer_id}")
                    await self.remove_peer(peer_id)

                for peer_id in bad_ids:
                    logger.debug(f"🧹 Removing bad peer: {peer_id}")
                    await self.remove_peer(peer_id)

            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get transport statistics."""
        connected = sum(1 for p in self.peers.values() if p.is_connected())
        total = len(self.peers)
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port_udp": self.port_udp,
            "port_ws": self.port_ws,
            "running": self._running,
            "peers_total": total,
            "peers_connected": connected,
            "peers_bad": sum(1 for p in self.peers.values() if p.is_bad()),
            "ws_connections": len(self._ws_connections),
            "tls_enabled": self.is_secure,
            "pending_rpcs": len(self._pending_rpcs),
        }


# ---------------------------------------------------------------------------
# UDP Protocol handler
# ---------------------------------------------------------------------------


class _UDPProtocol(asyncio.DatagramProtocol):
    """Internal UDP protocol handler that routes messages to the transport."""

    def __init__(self, message_handler: Callable):
        self._handler = message_handler
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple):
        asyncio.ensure_future(self._handler(data, addr))

    def error_received(self, exc):
        logger.error(f"UDP error: {exc}")


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

_p2p_transport: Optional[P2PTransport] = None


def get_p2p_transport(
    node_id: Optional[str] = None,
    host: str = "0.0.0.0",
    port_udp: int = 7332,
    port_ws: int = 7333,
) -> P2PTransport:
    """Get or create the global P2P transport instance."""
    global _p2p_transport
    if _p2p_transport is None:
        _node_id = node_id or f"node_{os.urandom(4).hex()}"
        _p2p_transport = P2PTransport(_node_id, host, port_udp, port_ws)
    return _p2p_transport


def reset_p2p_transport():
    """Reset global P2P transport instance (for testing)."""
    global _p2p_transport
    _p2p_transport = None
