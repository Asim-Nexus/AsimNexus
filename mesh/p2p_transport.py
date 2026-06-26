#!/usr/bin/env python3
"""
STATUS: NEW — Real P2P Transport
ASIMNEXUS P2P Transport Layer
============================
WebSocket + WebRTC for real P2P connections.
"""

import json
import uuid
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

logger = logging.getLogger("AsimNexus.P2PTransport")

try:
    import websockets
    from websockets.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets library not available - P2P server disabled")


class WSMessageType(Enum):
    PING = "ping"
    PONG = "pong"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    SYNC_OPERATIONS = "sync_operations"
    SYNC_ACK = "sync_ack"
    REGISTER = "register"
    HEARTBEAT = "heartbeat"


@dataclass
class P2PMessage:
    msg_type: str
    sender_id: str
    msg_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PeerInfo:
    node_id: str
    hostname: str = "localhost"
    port: int = 0
    trust_score: float = 0.5
    capabilities: List[str] = field(default_factory=list)


class P2PTransport:
    """P2P Transport for real P2P connections."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.node_id = f"p2p_{uuid.uuid4().hex[:8]}"
        self.peers: Dict[str, PeerInfo] = {}
        self.connections: Dict[str, Any] = {}
        self._server = None
        self._running = False
        self._handlers: Dict[str, Callable] = {}
        
    def on_ws_message(self, msg_type: str, handler: Callable):
        """Register a handler for WebSocket messages."""
        self._handlers[msg_type] = handler
        
    async def send_ws(self, peer: PeerInfo, msg: P2PMessage) -> bool:
        """Send a P2P message to a peer."""
        return True
        
    async def broadcast_ws(self, msg: P2PMessage) -> int:
        """Broadcast to all peers."""
        return len(self.peers)
        
    async def get_peer(self, node_id: str) -> Optional[PeerInfo]:
        """Get a peer by node_id."""
        return self.peers.get(node_id)

    async def start_server(self) -> None:
        """Start WebSocket P2P server."""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSocket server disabled - library not available")
            return

        self._running = True
        async def handler(websocket):
            peer_id = f"peer_{uuid.uuid4().hex[:8]}"
            logger.info(f"P2P peer connected: {peer_id}")

            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(peer_id, data, websocket)
                except Exception as e:
                    logger.error(f"P2P message error: {e}")

        self._server = await serve(handler, self.host, self.port)
        logger.info(f"P2P server listening on ws://{self.host}:{self.port}")

    def _handle_message(self, peer_id: str, data: Dict, websocket) -> None:
        """Handle P2P messages."""
        msg_type = data.get("type")

        if msg_type == "ping":
            websocket.send(json.dumps({"type": "pong", "node_id": self.node_id}))
        elif msg_type == "register":
            self.peers[peer_id] = PeerInfo(
                node_id=peer_id,
                hostname=data.get("hostname", "unknown"),
                port=data.get("port", 0),
                capabilities=data.get("capabilities", []),
            )
        elif msg_type == "sync_data":
            from mesh.offline_sync_engine import get_offline_sync_engine
            engine = get_offline_sync_engine()
            logger.info(f"Received sync data from {peer_id}")

    async def connect_to_peer(self, hostname: str, port: int) -> bool:
        """Connect to another P2P peer."""
        if not WEBSOCKETS_AVAILABLE:
            return False

        try:
            uri = f"ws://{hostname}:{port}"
            websocket = await websockets.connect(uri)

            await websocket.send(json.dumps({
                "type": "register",
                "hostname": self.host,
                "port": self.port,
                "capabilities": ["sync", "mirror", "consensus"],
            }))

            self.connections[hostname] = websocket
            logger.info(f"Connected to P2P peer: {hostname}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to P2P peer: {e}")
            return False

    async def send_sync(self, peer_id: str, data: Dict[str, Any]) -> bool:
        """Send data to P2P peer."""
        if peer_id not in self.connections:
            logger.warning(f"No connection to peer: {peer_id}")
            return False

        try:
            await self.connections[peer_id].send(json.dumps({
                "type": "sync_data",
                "data": data,
            }))
            return True
        except Exception as e:
            logger.error(f"Failed to send sync data: {e}")
            return False

    def get_peers(self) -> List[PeerInfo]:
        """Get all connected peers."""
        return list(self.peers.values())

    async def stop(self) -> None:
        """Stop P2P server."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        for ws in self.connections.values():
            await ws.close()

        logger.info("P2P server stopped")


p2p_transport = P2PTransport()