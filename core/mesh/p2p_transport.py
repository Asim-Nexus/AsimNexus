#!/usr/bin/env python3
"""
STATUS: REAL — Real P2P Transport
ASIMNEXUS P2P Transport Layer
============================
WebSocket + WebRTC + UDP RPC for real P2P connections.
"""

import json
import uuid
import asyncio
import logging
import time
import struct
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

logger = logging.getLogger("AsimNexus.P2PTransport")

try:
    import websockets
    # Use the modern asyncio server API (websockets >= 14.0)
    try:
        from websockets.asyncio.server import serve
    except ImportError:
        # Fallback for older websockets versions
        from websockets.server import serve  # type: ignore[no-redef]
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets library not available - P2P server disabled")

P2P_MAGIC = b"ASIM"
P2P_VERSION = 1


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


class RPCMessageType(Enum):
    PING = "ping"
    PONG = "pong"
    FIND_NODE = "find_node"
    FIND_VALUE = "find_value"
    STORE = "store"


class WSMessageType(Enum):
    PING = "ping"
    PONG = "pong"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    SYNC_OPERATIONS = "sync_operations"
    SYNC_ACK = "sync_ack"
    REGISTER = "register"
    HEARTBEAT = "heartbeat"
    PEER_HELLO = "peer_hello"


@dataclass
class P2PMessage:
    msg_type: str
    sender_id: str
    msg_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3

    def to_bytes(self) -> bytes:
        payload_bytes = json.dumps({
            "msg_type": self.msg_type,
            "sender_id": self.sender_id,
            "msg_id": self.msg_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "ttl": self.ttl
        }).encode("utf-8")
        # Format: MAGIC (4 bytes) + VERSION (1 byte) + LENGTH (4 bytes) + PAYLOAD
        header = P2P_MAGIC + struct.pack("!BI", P2P_VERSION, len(payload_bytes))
        return header + payload_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional["P2PMessage"]:
        if len(data) < 9:
            return None
        if data[:4] != P2P_MAGIC:
            return None
        version = data[4]
        if version != P2P_VERSION:
            return None
        body_len = struct.unpack("!I", data[5:9])[0]
        if len(data) < 9 + body_len:
            return None
        
        try:
            payload_str = data[9:9+body_len].decode("utf-8")
            obj = json.loads(payload_str)
            return cls(
                msg_type=obj.get("msg_type", ""),
                sender_id=obj.get("sender_id", ""),
                msg_id=obj.get("msg_id", ""),
                payload=obj.get("payload", {}),
                timestamp=obj.get("timestamp", 0.0),
                ttl=obj.get("ttl", 3)
            )
        except Exception:
            return None


@dataclass
class PeerInfo:
    node_id: str
    host: str = "localhost"
    port_udp: int = 0
    port_ws: int = 0
    trust_score: float = 0.5
    capabilities: List[str] = field(default_factory=list)
    last_seen: float = field(default_factory=time.time)
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    consecutive_failures: int = 0
    ping_failures: int = 0

    def is_stale(self, max_age: float) -> bool:
        return (time.time() - self.last_seen) > max_age

    def is_bad(self, max_failures: int) -> bool:
        return self.consecutive_failures >= max_failures


class P2PTransport:
    """P2P Transport for real P2P connections."""
    
    def __init__(self, node_id: str = None, host: str = "0.0.0.0", port_udp: int = 8765, port_ws: int = 8766):
        self.node_id = node_id or f"p2p_{uuid.uuid4().hex[:8]}"
        self.host = host
        self.port_udp = port_udp
        self.port_ws = port_ws
        self.peers: Dict[str, PeerInfo] = {}
        self.connections: Dict[str, Any] = {}  # peer_id -> websocket
        self._server = None
        self._running = False
        self._ws_handlers: Dict[str, Callable] = {}
        self._rpc_handlers: Dict[str, Callable] = {}
        self._pending_rpcs: Dict[str, asyncio.Future] = {}
        self._udp_transport: Optional[asyncio.DatagramTransport] = None
        self._udp_protocol: Optional[asyncio.DatagramProtocol] = None
        
    def _next_msg_id(self) -> str:
        return uuid.uuid4().hex

    def on_ws_message(self, msg_type: str, handler: Callable):
        self._ws_handlers[msg_type] = handler

    def on_rpc(self, msg_type: str, handler: Callable):
        self._rpc_handlers[msg_type] = handler
        
    async def add_peer(self, node_id: str, host: str, port_udp: int, port_ws: int) -> PeerInfo:
        if node_id in self.peers:
            peer = self.peers[node_id]
            peer.host = host
            peer.port_udp = port_udp
            peer.port_ws = port_ws
            peer.last_seen = time.time()
            return peer
        peer = PeerInfo(node_id=node_id, host=host, port_udp=port_udp, port_ws=port_ws)
        self.peers[node_id] = peer
        return peer

    async def remove_peer(self, node_id: str):
        if node_id in self.peers:
            del self.peers[node_id]

    async def get_peer(self, node_id: str) -> Optional[PeerInfo]:
        return self.peers.get(node_id)

    async def get_online_peers(self) -> List[PeerInfo]:
        return [
            p for p in self.peers.values()
            if p.connection_state == ConnectionState.CONNECTED and not p.is_bad(3)
        ]

    async def send_ws(self, peer: PeerInfo, msg: P2PMessage) -> bool:
        if not self._running or not WEBSOCKETS_AVAILABLE:
            peer.ping_failures += 1
            return False
        try:
            ws = self.connections.get(peer.node_id)
            if ws is None:
                # Attempt outbound WebSocket connection
                uri = f"ws://{peer.host}:{peer.port_ws}"
                try:
                    import websockets
                    ws = await websockets.connect(uri, open_timeout=5, close_timeout=2)
                    self.connections[peer.node_id] = ws
                    peer.connection_state = ConnectionState.CONNECTED
                except Exception as conn_err:
                    logger.debug(f"WS connect to {uri} failed: {conn_err}")
                    peer.ping_failures += 1
                    peer.connection_state = ConnectionState.FAILED
                    return False
            # Send the message as JSON
            payload = {
                "type": msg.msg_type,
                "sender_id": msg.sender_id,
                "msg_id": msg.msg_id,
                "payload": msg.payload,
                "timestamp": msg.timestamp,
                "ttl": msg.ttl,
            }
            await ws.send(json.dumps(payload))
            peer.last_seen = time.time()
            peer.ping_failures = 0
            return True
        except Exception as e:
            logger.debug(f"WS send error to {peer.node_id}: {e}")
            peer.ping_failures += 1
            # Remove stale connection
            if peer.node_id in self.connections:
                try:
                    await self.connections[peer.node_id].close()
                except Exception:
                    pass
                del self.connections[peer.node_id]
            peer.connection_state = ConnectionState.DISCONNECTED
            return False
        
    async def broadcast_ws(self, msg: P2PMessage) -> int:
        count = 0
        online = await self.get_online_peers()
        for p in online:
            if await self.send_ws(p, msg):
                count += 1
        return count

    async def send_udp(self, peer: PeerInfo, msg: P2PMessage) -> bool:
        """Send a message via UDP datagram."""
        if not self._running:
            return False
        try:
            data = msg.to_bytes()
            if self._udp_transport:
                self._udp_transport.sendto(data, (peer.host, peer.port_udp))
                peer.last_seen = time.time()
                peer.ping_failures = 0
                return True
            else:
                # Fallback: use asyncio UDP socket directly
                loop = asyncio.get_running_loop()
                transport, protocol = await loop.create_datagram_endpoint(
                    lambda: asyncio.DatagramProtocol(),
                    remote_addr=(peer.host, peer.port_udp),
                )
                try:
                    transport.sendto(data)
                    return True
                finally:
                    transport.close()
        except Exception as e:
            logger.debug(f"UDP send error to {peer.node_id}: {e}")
            peer.ping_failures += 1
            return False

    async def rpc_call(self, peer: PeerInfo, msg_type: str, payload: dict, timeout: float = 2.0) -> Optional[P2PMessage]:
        msg_id = self._next_msg_id()
        msg = P2PMessage(msg_type=msg_type, sender_id=self.node_id, msg_id=msg_id, payload=payload)
        
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_rpcs[msg_id] = future
        
        # Temporary handler to resolve the future
        async def response_handler(response: P2PMessage):
            if not future.done() and response.msg_id == msg_id:
                future.set_result(response)
        
        # Map response type
        resp_map = {
            RPCMessageType.PING.value: RPCMessageType.PONG.value,
            RPCMessageType.FIND_NODE.value: "find_node_response",
            RPCMessageType.FIND_VALUE.value: "find_value_response",
            RPCMessageType.STORE.value: "store_response",
        }
        expected_type = resp_map.get(msg_type)
        if expected_type:
            self._rpc_handlers[expected_type] = response_handler
            
        success = await self.send_udp(peer, msg)
        if not success:
            del self._pending_rpcs[msg_id]
            if expected_type in self._rpc_handlers:
                del self._rpc_handlers[expected_type]
            return None
            
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return None
        finally:
            if msg_id in self._pending_rpcs:
                del self._pending_rpcs[msg_id]
            if expected_type in self._rpc_handlers:
                del self._rpc_handlers[expected_type]

    async def start_server(self) -> None:
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSocket server disabled - library not available")
            return

        self._running = True

        # Start WebSocket server
        async def handler(websocket):
            peer_id = f"peer_{uuid.uuid4().hex[:8]}"
            logger.info(f"P2P peer connected: {peer_id}")

            # Register connection
            self.connections[peer_id] = websocket
            peer_info = PeerInfo(
                node_id=peer_id,
                host=websocket.remote_address[0] if hasattr(websocket, 'remote_address') else "unknown",
                port_ws=websocket.remote_address[1] if hasattr(websocket, 'remote_address') else 0,
                connection_state=ConnectionState.CONNECTED,
            )
            self.peers[peer_id] = peer_info

            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_message(peer_id, data, websocket)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from {peer_id}")
                    except Exception as e:
                        logger.error(f"P2P message error from {peer_id}: {e}")
            except Exception as e:
                logger.debug(f"P2P peer {peer_id} disconnected: {e}")
            finally:
                # Cleanup on disconnect
                if peer_id in self.connections:
                    del self.connections[peer_id]
                if peer_id in self.peers:
                    self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED
                logger.info(f"P2P peer disconnected: {peer_id}")

        self._server = await serve(handler, self.host, self.port_ws)
        logger.info(f"P2P WebSocket server listening on ws://{self.host}:{self.port_ws}")

        # Start UDP listener
        try:
            loop = asyncio.get_running_loop()

            class UDPProtocol(asyncio.DatagramProtocol):
                def __init__(self, transport_ref):
                    self._transport_ref = transport_ref

                def datagram_received(self, data: bytes, addr):
                    transport = self._transport_ref()
                    if transport:
                        asyncio.ensure_future(transport._handle_udp_datagram(data, addr))

            def _get_transport():
                return self

            self._udp_transport, self._udp_protocol = await loop.create_datagram_endpoint(
                lambda: UDPProtocol(_get_transport),
                local_addr=(self.host, self.port_udp),
            )
            logger.info(f"P2P UDP listener on udp://{self.host}:{self.port_udp}")
        except Exception as e:
            logger.warning(f"UDP listener failed to start: {e}")

    async def _handle_udp_datagram(self, data: bytes, addr: tuple) -> None:
        """Handle an incoming UDP datagram."""
        try:
            msg = P2PMessage.from_bytes(data)
            if msg is None:
                return
            peer_id = msg.sender_id
            # Update or create peer entry
            if peer_id not in self.peers:
                self.peers[peer_id] = PeerInfo(
                    node_id=peer_id,
                    host=addr[0],
                    port_udp=addr[1],
                    connection_state=ConnectionState.CONNECTED,
                )
            else:
                self.peers[peer_id].last_seen = time.time()
                self.peers[peer_id].connection_state = ConnectionState.CONNECTED

            # Handle RPC responses
            if msg.msg_id and msg.msg_id in self._pending_rpcs:
                future = self._pending_rpcs.pop(msg.msg_id)
                if not future.done():
                    future.set_result(msg)
            # Handle registered RPC handlers
            elif msg.msg_type in self._rpc_handlers:
                handler = self._rpc_handlers[msg.msg_type]
                if asyncio.iscoroutinefunction(handler):
                    await handler(msg)
                else:
                    handler(msg)
        except Exception as e:
            logger.debug(f"UDP datagram handling error: {e}")

    async def _handle_message(self, peer_id: str, data: Dict, websocket) -> None:
        msg_type = data.get("type")

        if msg_type == "ping":
            await websocket.send(json.dumps({"type": "pong", "node_id": self.node_id}))
        elif msg_type == "pong":
            # Update peer health
            if peer_id in self.peers:
                self.peers[peer_id].last_seen = time.time()
                self.peers[peer_id].ping_failures = 0
        elif msg_type == "register":
            node_id = data.get("node_id", peer_id)
            capabilities = data.get("capabilities", [])
            if node_id not in self.peers:
                self.peers[node_id] = PeerInfo(
                    node_id=node_id,
                    host=data.get("host", "unknown"),
                    port_udp=data.get("port_udp", 0),
                    port_ws=data.get("port_ws", 0),
                    capabilities=capabilities,
                    connection_state=ConnectionState.CONNECTED,
                )
            else:
                self.peers[node_id].last_seen = time.time()
                self.peers[node_id].connection_state = ConnectionState.CONNECTED
            # Send acknowledgment
            await websocket.send(json.dumps({
                "type": "registered",
                "node_id": self.node_id,
                "peer_id": node_id,
            }))
            # Update peer_id mapping
            if peer_id != node_id:
                self.connections[node_id] = self.connections.pop(peer_id, websocket)
                if peer_id in self.peers:
                    del self.peers[peer_id]
                peer_id = node_id
        elif msg_type == "peer_hello":
            sender = data.get("sender_id", peer_id)
            logger.info(f"Peer hello from {sender}")
            await websocket.send(json.dumps({
                "type": "peer_hello_ack",
                "node_id": self.node_id,
            }))
        elif msg_type == "sync_request":
            logger.info(f"Sync request from {peer_id}")
            # Forward to registered sync handler
            handler = self._ws_handlers.get("sync_request")
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
        elif msg_type == "sync_operations":
            logger.info(f"Received {len(data.get('operations', []))} sync ops from {peer_id}")
            handler = self._ws_handlers.get("sync_operations")
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
        elif msg_type == "heartbeat":
            # Respond with pong
            await websocket.send(json.dumps({"type": "pong", "node_id": self.node_id}))
        elif msg_type == "sync_data":
            logger.info(f"Received sync data from {peer_id}")
            handler = self._ws_handlers.get("sync_data")
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
        else:
            # Forward to generic handler if registered
            handler = self._ws_handlers.get(msg_type)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)

    def get_peers(self) -> List[PeerInfo]:
        return list(self.peers.values())

    async def stop(self) -> None:
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for ws in self.connections.values():
            await ws.close()

        logger.info("P2P server stopped")


_global_p2p_transport = None

def get_p2p_transport(node_id: str = None, host: str = "0.0.0.0", port_udp: int = 8765, port_ws: int = 8766) -> P2PTransport:
    global _global_p2p_transport
    if _global_p2p_transport is None:
        _global_p2p_transport = P2PTransport(node_id=node_id, host=host, port_udp=port_udp, port_ws=port_ws)
    return _global_p2p_transport

def reset_p2p_transport():
    global _global_p2p_transport
    _global_p2p_transport = None

# For backwards compatibility with old imports
p2p_transport = get_p2p_transport()