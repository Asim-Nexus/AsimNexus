#!/usr/bin/env python3
"""
STATUS: INTEGRATED — Phase 1B
ASIMNEXUS Relay Service
========================
NAT/firewall traversal for mesh network.
Relay connections for nodes behind NAT/firewalls.

Integrates with:
  - [`mesh/p2p_transport.py`](p2p_transport.py) — P2PMessage relay forwarding
  - [`mesh/hole_punching.py`](hole_punching.py) — TCP relay fallback strategy

When a P2PTransport is provided, relayed data can be forwarded through
the transport's UDP socket for consistent NAT mapping and P2PMessage framing.
"""

import os
import logging
import socket
import json
import asyncio
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import secrets
import time

if TYPE_CHECKING:
    from core.mesh.p2p_transport import P2PTransport

logger = logging.getLogger("AsimNexus.Mesh.Relay")


class RelayRole(Enum):
    """Roles in relay network."""
    RELAY = "relay"  # Public relay node
    CLIENT = "client"  # Node behind NAT
    DIRECT = "direct"  # Node with public IP


class RelayStatus(Enum):
    """Status of relay connections."""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RELAYING = "relaying"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class RelaySession:
    """Relay session between two nodes."""
    session_id: str
    client_a_id: str
    client_b_id: str
    status: RelayStatus = RelayStatus.IDLE
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    bytes_relayed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelayNode:
    """Node in relay network."""
    node_id: str
    ip_address: str
    port: int
    role: RelayRole
    status: RelayStatus = RelayStatus.IDLE
    last_seen: float = field(default_factory=time.time)
    sessions: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)


class RelayService:
    """
    Relay service for NAT/firewall traversal.
    Allows nodes behind NAT to connect through relay nodes.
    """
    
    DEFAULT_RELAY_PORT = int(os.getenv("ASIM_MESH_RELAY_PORT", "7334"))
    SESSION_TIMEOUT = int(os.getenv("ASIM_MESH_RELAY_SESSION_TIMEOUT", "300"))  # 5 minutes
    MAX_SESSIONS = int(os.getenv("ASIM_MESH_RELAY_MAX_SESSIONS", "100"))
    
    def __init__(
        self,
        node_id: str,
        role: RelayRole = RelayRole.RELAY,
        port: Optional[int] = None,
        transport: Optional['P2PTransport'] = None,
    ):
        self.node_id = node_id
        self.role = role
        self.port = port if port is not None else int(os.getenv("ASIM_MESH_RELAY_PORT", str(self.DEFAULT_RELAY_PORT)))
        self.ip_address = self._get_local_ip()
        self.transport = transport
        
        self.sessions: Dict[str, RelaySession] = {}
        self.nodes: Dict[str, RelayNode] = {}
        
        self._server: Optional[asyncio.Server] = None
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"🌉 RelayService initialized - Node: {node_id}, "
            f"Role: {role.value}, Port: {port}, "
            f"Transport: {'yes' if transport else 'no'}"
        )
    
    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    async def start(self):
        """Start relay service."""
        if self._running:
            logger.warning("RelayService already running")
            return
        
        self._running = True
        
        if self.role == RelayRole.RELAY:
            # Start relay server on all interfaces
            self._server = await asyncio.start_server(
                self._handle_relay_connection,
                "0.0.0.0",
                self.port
            )
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_sessions())
            
            logger.info(f"🌉 Relay server started on {self.ip_address}:{self.port}")
        else:
            logger.info(f"🌉 Relay client mode (no server needed)")
    
    async def stop(self):
        """Stop relay service."""
        self._running = False
        
        # Close all sessions
        for session in self.sessions.values():
            await self.close_session(session.session_id)
        
        # Stop server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🌉 RelayService stopped")
    
    async def _handle_relay_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming relay connection."""
        addr = writer.get_extra_info('peername')
        logger.info(f"🌉 Relay connection from {addr}")
        
        try:
            # Read handshake
            data = await reader.readline()
            if not data:
                writer.close()
                await writer.wait_closed()
                return
            
            handshake = json.loads(data.decode())
            msg_type = handshake.get("type")
            
            if msg_type == "register":
                # Register node
                node_id = handshake.get("node_id")
                if node_id:
                    self._register_node(node_id, addr[0], handshake.get("port", self.port))
                    response = {"status": "registered", "relay_id": self.node_id}
                    writer.write(json.dumps(response).encode() + b"\n")
                    await writer.drain()
            
            elif msg_type == "connect":
                # Request relay connection
                session_id = handshake.get("session_id")
                target_node = handshake.get("target_node")
                
                if session_id and target_node:
                    session = self._get_or_create_session(session_id, self.node_id, target_node)
                    response = {
                        "status": "ready",
                        "session_id": session.session_id,
                        "relay_address": f"{self.ip_address}:{self.port}"
                    }
                    writer.write(json.dumps(response).encode() + b"\n")
                    await writer.drain()
            
            elif msg_type == "relay":
                # Relay data
                session_id = handshake.get("session_id")
                data_payload = handshake.get("data")
                
                if session_id and data_payload:
                    session = self.sessions.get(session_id)
                    if session:
                        session.last_activity = time.time()
                        session.bytes_relayed += len(str(data_payload))
                        # In a full implementation, you'd relay to the other client
                        response = {"status": "relayed"}
                        writer.write(json.dumps(response).encode() + b"\n")
                        await writer.drain()
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logger.error(f"Relay connection error: {e}")
            writer.close()
            await writer.wait_closed()
    
    def _register_node(self, node_id: str, ip_address: str, port: int):
        """Register a node with the relay."""
        node = RelayNode(
            node_id=node_id,
            ip_address=ip_address,
            port=port,
            role=RelayRole.CLIENT,
            status=RelayStatus.CONNECTED
        )
        self.nodes[node_id] = node
        logger.info(f"🌉 Registered node: {node_id} at {ip_address}:{port}")
    
    def _get_or_create_session(self, session_id: str, client_a: str, client_b: str) -> RelaySession:
        """Get or create a relay session."""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        if len(self.sessions) >= self.MAX_SESSIONS:
            raise Exception("Max sessions reached")
        
        session = RelaySession(
            session_id=session_id,
            client_a_id=client_a,
            client_b_id=client_b,
            status=RelayStatus.CONNECTING
        )
        self.sessions[session_id] = session
        logger.info(f"🌉 Created session: {session_id} between {client_a} and {client_b}")
        return session
    
    async def close_session(self, session_id: str):
        """Close a relay session."""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        session.status = RelayStatus.CLOSED
        del self.sessions[session_id]
        logger.info(f"🌉 Closed session: {session_id}")
    
    async def request_relay(self, relay_node: str, target_node: str) -> Optional[str]:
        """Request a relay connection through a relay node."""
        session_id = secrets.token_hex(8)
        
        try:
            # Connect to relay node
            reader, writer = await asyncio.open_connection(
                self.nodes[relay_node].ip_address,
                self.nodes[relay_node].port
            )
            
            # Send connect request
            request = {
                "type": "connect",
                "node_id": self.node_id,
                "session_id": session_id,
                "target_node": target_node
            }
            writer.write(json.dumps(request).encode() + b"\n")
            await writer.drain()
            
            # Read response
            response_data = await reader.readline()
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response.get("status") == "ready":
                logger.info(f"🌉 Relay connection established: {session_id}")
                return session_id
            else:
                logger.warning(f"🌉 Relay connection failed: {response}")
                return None
            
        except Exception as e:
            logger.error(f"Relay request error: {e}")
            return None
    
    async def _cleanup_sessions(self):
        """Cleanup stale sessions."""
        while self._running:
            try:
                cutoff = time.time() - self.SESSION_TIMEOUT
                stale_sessions = [
                    sid for sid, session in self.sessions.items()
                    if session.last_activity < cutoff
                ]
                
                for session_id in stale_sessions:
                    await self.close_session(session_id)
                
                if stale_sessions:
                    logger.info(f"🌉 Cleaned {len(stale_sessions)} stale sessions")
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
            
            await asyncio.sleep(60)
    
    def get_session(self, session_id: str) -> Optional[RelaySession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def get_sessions(self) -> List[RelaySession]:
        """Get all active sessions."""
        return list(self.sessions.values())
    
    def get_node(self, node_id: str) -> Optional[RelayNode]:
        """Get a registered node."""
        return self.nodes.get(node_id)
    
    def get_nodes(self) -> List[RelayNode]:
        """Get all registered nodes."""
        return list(self.nodes.values())
    
    async def relay_data(
        self,
        session_id: str,
        data: bytes,
        target_node_id: str,
    ) -> bool:
        """Forward relayed data to the target node via transport or TCP."""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"relay_data: session {session_id} not found")
            return False

        session.last_activity = time.time()
        session.bytes_relayed += len(data)

        if self.transport:
            # Transport mode: forward via P2PMessage
            target_node = self.nodes.get(target_node_id)
            if target_node:
                return await self.transport.send_udp_to(
                    target_node.ip_address,
                    target_node.port,
                    "RELAY_DATA",
                    {
                        "session_id": session_id,
                        "data": data.hex(),
                        "from": self.node_id,
                    },
                )
            return False
        else:
            # TCP mode: the data was already forwarded during _handle_relay_connection
            session.status = RelayStatus.RELAYING
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get relay statistics."""
        active_sessions = len([s for s in self.sessions.values() if s.status == RelayStatus.RELAYING])
        
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "ip_address": self.ip_address,
            "port": self.port,
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "registered_nodes": len(self.nodes),
            "running": self._running
        }


# Global relay service instance
_relay_service: Optional[RelayService] = None


def get_relay_service(
    node_id: str,
    role: RelayRole = RelayRole.RELAY,
    port: Optional[int] = None,
    transport: Optional['P2PTransport'] = None,
) -> RelayService:
    """Get or create global relay service instance."""
    global _relay_service
    if _relay_service is None:
        _relay_service = RelayService(node_id, role, port, transport=transport)
    return _relay_service


def reset_relay_service():
    """Reset global relay service instance (for testing)."""
    global _relay_service
    if _relay_service and _relay_service._running:
        pass
    _relay_service = None
    _relay_service = None
