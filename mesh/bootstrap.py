#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade bootstrap service
ASIMNEXUS Bootstrap Service
===========================
Federation seed nodes for mesh network.
Helps new nodes join the mesh network.

Provides:
- TCP-based bootstrap server for seed node discovery
- Peer registration for dynamic peer discovery
- Integration with P2PTransport handshake (connect_peer)
- Regional bootstrap node management
- Peer info exchange (WS/UDP ports, capabilities)
"""

import os
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import secrets
import time
import ssl
import uuid

if TYPE_CHECKING:
    from mesh.p2p_transport import P2PTransport, PeerInfo
    from mesh.kademlia_dht import KademliaDHT

from core.event_bus import event_bus, ASIMEvent, EventType

logger = logging.getLogger("AsimNexus.Mesh.Bootstrap")


class BootstrapRegion(Enum):
    """Regions for bootstrap nodes."""
    GLOBAL = "global"
    ASIA = "asia"
    EUROPE = "europe"
    AMERICAS = "americas"
    AFRICA = "africa"
    OCEANIA = "oceania"


@dataclass
class BootstrapNode:
    """Bootstrap node information."""
    node_id: str
    ip_address: str
    port: int       # TCP bootstrap port
    region: BootstrapRegion
    trust_level: str = "trusted"
    last_seen: float = field(default_factory=time.time)
    load: float = 0.0  # 0.0 to 1.0
    capabilities: List[str] = field(default_factory=list)
    port_ws: Optional[int] = None    # WebSocket port for P2PTransport
    port_udp: Optional[int] = None   # UDP port for P2PTransport
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BootstrapRequest:
    """Request for bootstrap information."""
    node_id: str
    region: Optional[BootstrapRegion] = None
    capabilities: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class BootstrapResponse:
    """Response with bootstrap information."""
    success: bool
    bootstrap_nodes: List[BootstrapNode]
    message: str
    timestamp: float = field(default_factory=time.time)
    peers: List['RegisteredPeer'] = field(default_factory=list)


@dataclass
class RegisteredPeer:
    """A peer that registered itself with the bootstrap service."""
    node_id: str
    ip_address: str
    port_ws: int     # WebSocket port for P2PTransport
    port_udp: int    # UDP port for P2PTransport
    region: str = "global"
    capabilities: List[str] = field(default_factory=list)
    last_seen: float = field(default_factory=time.time)
    version: str = "1.0.0"
    trust_level: str = "anonymous"


class BootstrapService:
    """
    Bootstrap service for mesh network.
    Manages federation seed nodes and helps new nodes join.
    """
    
    DEFAULT_BOOTSTRAP_PORT = int(os.getenv("ASIM_MESH_BOOTSTRAP_PORT", "7335"))
    MAX_BOOTSTRAP_NODES = int(os.getenv("ASIM_MESH_BOOTSTRAP_MAX_NODES", "50"))
    NODE_TIMEOUT = int(os.getenv("ASIM_MESH_BOOTSTRAP_NODE_TIMEOUT", "3600"))  # 1 hour
    BOOTSTRAP_CACHE_TTL = int(os.getenv("ASIM_MESH_BOOTSTRAP_CACHE_TTL", "300"))
    _CUSTOM_BOOTSTRAP = os.getenv("ASIM_MESH_BOOTSTRAP_SEEDS", "")
    # Format: "node_id1:host1:port1:region1,node_id2:host2:port2:region2"
    
    # Default bootstrap nodes (would be loaded from config in production)
    DEFAULT_BOOTSTRAPS = [
        {
            "node_id": "bootstrap_global_1",
            "ip_address": "bootstrap.asimnexus.org",
            "port": 7335,
            "region": "global"
        },
        {
            "node_id": "bootstrap_asia_1",
            "ip_address": "bootstrap-asia.asimnexus.org",
            "port": 7335,
            "region": "asia"
        },
        {
            "node_id": "bootstrap_europe_1",
            "ip_address": "bootstrap-europe.asimnexus.org",
            "port": 7335,
            "region": "europe"
        },
        {
            "node_id": "bootstrap_americas_1",
            "ip_address": "bootstrap-americas.asimnexus.org",
            "port": 7335,
            "region": "americas"
        }
    ]
    
    def __init__(self, node_id: str, is_bootstrap: bool = False, port: Optional[int] = None, ssl_context: Optional[ssl.SSLContext] = None):
        self.node_id = node_id
        self.is_bootstrap = is_bootstrap
        self.port = port if port is not None else int(os.getenv("ASIM_MESH_BOOTSTRAP_PORT", str(self.DEFAULT_BOOTSTRAP_PORT)))
        self.ip_address = self._get_local_ip()
        
        # Pre-populate default bootstrap nodes (synchronously, without DNS)
        self.bootstrap_nodes: Dict[str, BootstrapNode] = {}
        for config in self.DEFAULT_BOOTSTRAPS:
            node = BootstrapNode(
                node_id=config["node_id"],
                ip_address=config["ip_address"],
                port=config["port"],
                region=BootstrapRegion(config["region"]),
            )
            self.bootstrap_nodes[node.node_id] = node
        
        self.known_peers: Dict[str, Dict[str, Any]] = {}
        # Registered peers (peer_id -> RegisteredPeer)
        self._peers: Dict[str, RegisteredPeer] = {}
        
        self._server: Optional[asyncio.Server] = None
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Lock for thread/async safety
        self._ssl_context = ssl_context
        self._bootstrap_cache: Dict[str, Tuple[BootstrapResponse, float]] = {}
        self._bootstrap_cache_ttl = self.BOOTSTRAP_CACHE_TTL
        self._lock = asyncio.Lock()
        
        # Bootstrap nodes loaded in start() via async DNS
        
        logger.info(f"🚀 BootstrapService initialized - Node: {node_id}, IsBootstrap: {is_bootstrap}")
    
    def _get_local_ip(self) -> str:
        """Get local IP address."""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    async def _load_default_bootstraps(self):
        """Load default bootstrap nodes with DNS resolution."""
        # Parse custom bootstrap seeds from env var (read at runtime)
        custom_seeds = os.getenv("ASIM_MESH_BOOTSTRAP_SEEDS", "")
        if custom_seeds:
            for entry in custom_seeds.split(","):
                parts = entry.strip().split(":")
                if len(parts) >= 3:
                    node_id, host, port_str = parts[0], parts[1], parts[2]
                    region_str = parts[3] if len(parts) > 3 else "global"
                    try:
                        ips = await asyncio.get_event_loop().getaddrinfo(host, int(port_str))
                        resolved_ip = ips[0][4][0]
                        node = BootstrapNode(
                            node_id=node_id,
                            ip_address=resolved_ip,
                            port=int(port_str),
                            region=BootstrapRegion(region_str),
                        )
                        self.bootstrap_nodes[node.node_id] = node
                        logger.info(f"DNS resolved custom seed {node_id} -> {resolved_ip}")
                    except Exception as e:
                        logger.warning(f"DNS resolution failed for custom seed {node_id}: {e}")

        # Load default bootstrap nodes with DNS resolution
        for config in self.DEFAULT_BOOTSTRAPS:
            try:
                ips = await asyncio.get_event_loop().getaddrinfo(
                    config["ip_address"], config["port"]
                )
                resolved_ip = ips[0][4][0]
                node = BootstrapNode(
                    node_id=config["node_id"],
                    ip_address=resolved_ip,
                    port=config["port"],
                    region=BootstrapRegion(config["region"]),
                )
                self.bootstrap_nodes[node.node_id] = node
            except Exception as e:
                logger.warning(f"DNS resolution failed for {config['node_id']}: {e}")

        logger.info(f"Loaded {len(self.bootstrap_nodes)} bootstrap nodes")

    async def start(self):
        """Start bootstrap service."""
        if self._running:
            logger.warning("BootstrapService already running")
            return
        
        self._running = True
        
        if self.is_bootstrap:
            await self._load_default_bootstraps()
            # Register self as bootstrap node
            self_node = BootstrapNode(
                node_id=self.node_id,
                ip_address=self.ip_address,
                port=self.port,
                region=BootstrapRegion.GLOBAL,
                trust_level="trusted"
            )
            self.bootstrap_nodes[self.node_id] = self_node
            
            # Start bootstrap server on all interfaces
            self._server = await asyncio.start_server(
                self._handle_bootstrap_request,
                "0.0.0.0",  # bind all interfaces to accept both LAN and loopback
                self.port,
                ssl=self._ssl_context,
            )
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_stale_nodes())
            
            logger.info(f"🚀 Bootstrap server started on {self.ip_address}:{self.port}")
        # Emit bootstrap complete event
        try:
            await event_bus.publish(ASIMEvent(
                event_type=EventType.BOOTSTRAP_COMPLETE,
                source="BootstrapService",
                data={"node_id": self.node_id, "mode": "server"},
            ))
        except Exception:
            pass
        else:
            logger.info(f"🚀 Bootstrap client mode")
    
    async def stop(self):
        """Stop bootstrap service."""
        self._running = False
        
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
        
        logger.info("🚀 BootstrapService stopped")
    
    async def _handle_bootstrap_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle bootstrap request."""
        addr = writer.get_extra_info('peername')
        logger.info(f"🚀 Bootstrap request from {addr}")
        
        try:
            # Read request
            data = await reader.readline()
            if not data:
                writer.close()
                await writer.wait_closed()
                return
            
            request = json.loads(data.decode())
            
            # Get bootstrap nodes
            region = request.get("region")
            if region:
                try:
                    region_enum = BootstrapRegion(region)
                except ValueError:
                    region_enum = None
            else:
                region_enum = None
            
            bootstrap_nodes = self.get_bootstrap_nodes(region=region_enum)
            
            # Check if this is a peer registration request
            request_type = request.get("type", "bootstrap")
            
            if request_type == "register":
                # Register the peer
                peer = RegisteredPeer(
                    node_id=request.get("node_id", "unknown"),
                    ip_address=addr[0] if addr else request.get("ip_address", "0.0.0.0"),
                    port_ws=request.get("port_ws", 7333),
                    port_udp=request.get("port_udp", 7332),
                    region=request.get("region", "global"),
                    capabilities=request.get("capabilities", []),
                    version=request.get("version", "1.0.0"),
                )
                async with self._lock:
                    self._peers[peer.node_id] = peer
                
                # Also return current bootstrap nodes
                registered_peers = await self.get_registered_peers()
                response = BootstrapResponse(
                    success=True,
                    bootstrap_nodes=bootstrap_nodes,
                    peers=registered_peers,
                    message=f"Registered peer {peer.node_id}, got {len(registered_peers)} known peers"
                )
            else:
                # Regular bootstrap request — return bootstrap nodes + registered peers
                registered_peers = await self.get_registered_peers()
                response = BootstrapResponse(
                    success=True,
                    bootstrap_nodes=bootstrap_nodes,
                    peers=registered_peers,
                    message=f"Bootstrap nodes provided, {len(registered_peers)} known peers"
                )
            
            # Send response (include registered peers)
            response_data = {
                "success": response.success,
                "bootstrap_nodes": [
                    {
                        "node_id": n.node_id,
                        "ip_address": n.ip_address,
                        "port": n.port,
                        "region": n.region.value,
                        "trust_level": n.trust_level,
                        "capabilities": n.capabilities,
                        "port_ws": n.port_ws,
                        "port_udp": n.port_udp,
                    }
                    for n in response.bootstrap_nodes
                ],
                "peers": [
                    {
                        "node_id": p.node_id,
                        "ip_address": p.ip_address,
                        "port_ws": p.port_ws,
                        "port_udp": p.port_udp,
                        "region": p.region,
                        "capabilities": p.capabilities,
                        "version": p.version,
                        "trust_level": p.trust_level,
                    }
                    for p in response.peers
                ],
                "message": response.message,
                "timestamp": response.timestamp
            }
            
            writer.write(json.dumps(response_data).encode() + b"\n")
            await writer.drain()
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logger.error(f"Bootstrap request error: {e}")
            writer.close()
            await writer.wait_closed()
    
    def get_bootstrap_nodes(self, region: Optional[BootstrapRegion] = None, limit: Optional[int] = None) -> List[BootstrapNode]:
        """Get bootstrap nodes, optionally filtered by region."""
        nodes = list(self.bootstrap_nodes.values())
        
        # Filter by region if specified
        if region:
            nodes = [n for n in nodes if n.region == region]
        
        # Sort by load (prefer less loaded nodes)
        nodes.sort(key=lambda n: n.load)
        
        # Filter out stale nodes
        cutoff = time.time() - self.NODE_TIMEOUT
        nodes = [n for n in nodes if n.last_seen > cutoff]
        
        max_nodes = limit if limit is not None else int(os.getenv("ASIM_MESH_BOOTSTRAP_RESPONSE_LIMIT", "5"))
        return nodes[:max_nodes]
    
    def add_bootstrap_node(self, node: BootstrapNode) -> bool:
        """Add a bootstrap node."""
        if len(self.bootstrap_nodes) >= self.MAX_BOOTSTRAP_NODES:
            logger.warning("Max bootstrap nodes reached")
            return False
        
        self.bootstrap_nodes[node.node_id] = node
        logger.info(f"🚀 Added bootstrap node: {node.node_id}")
        return True
    
    def remove_bootstrap_node(self, node_id: str) -> bool:
        """Remove a bootstrap node."""
        if node_id in self.bootstrap_nodes:
            del self.bootstrap_nodes[node_id]
            logger.info(f"🚀 Removed bootstrap node: {node_id}")
            return True
        return False
    
    async def request_bootstrap(self, bootstrap_address: str, bootstrap_port: int,
                               region: Optional[BootstrapRegion] = None,
                               register: bool = False,
                               port_ws: Optional[int] = None,
                               port_udp: Optional[int] = None) -> Optional[BootstrapResponse]:
        """Request bootstrap information from a bootstrap node.
        
        Args:
            bootstrap_address: IP/hostname of bootstrap node.
            bootstrap_port: TCP port of bootstrap node.
            region: Optional region filter.
            register: If True, register this node as a peer.
            port_ws: WebSocket port (required if register=True).
            port_udp: UDP port (required if register=True).
        """
        try:
            # Check cache first
            cache_key = f"{bootstrap_address}:{bootstrap_port}"
            if cache_key in self._bootstrap_cache:
                cached, timestamp = self._bootstrap_cache[cache_key]
                if time.time() - timestamp < self._bootstrap_cache_ttl:
                    logger.info(f"Using cached bootstrap response from {bootstrap_address}")
                    return cached

            reader, writer = await asyncio.open_connection(
                bootstrap_address, bootstrap_port,
                ssl=self._ssl_context,
            )
            
            # Send request
            request = {
                "node_id": self.node_id,
                "region": region.value if region else None,
                "timestamp": time.time(),
                "type": "register" if register else "bootstrap",
            }
            if register:
                request["port_ws"] = port_ws or 7333
                request["port_udp"] = port_udp or 7332
                request["capabilities"] = []
                request["version"] = "1.0.0"
            
            writer.write(json.dumps(request).encode() + b"\n")
            await writer.drain()
            
            # Read response
            response_data = await reader.readline()
            response_dict = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            # Parse bootstrap nodes
            bootstrap_nodes = []
            for node_data in response_dict.get("bootstrap_nodes", []):
                node = BootstrapNode(
                    node_id=node_data["node_id"],
                    ip_address=node_data["ip_address"],
                    port=node_data["port"],
                    region=BootstrapRegion(node_data["region"]),
                    trust_level=node_data.get("trust_level", "unknown"),
                    capabilities=node_data.get("capabilities", []),
                    port_ws=node_data.get("port_ws"),
                    port_udp=node_data.get("port_udp"),
                )
                bootstrap_nodes.append(node)
            
            # Parse registered peers from response
            registered_peers = []
            for peer_data in response_dict.get("peers", []):
                peer = RegisteredPeer(
                    node_id=peer_data["node_id"],
                    ip_address=peer_data["ip_address"],
                    port_ws=peer_data.get("port_ws", 7333),
                    port_udp=peer_data.get("port_udp", 7332),
                    region=peer_data.get("region", "global"),
                    capabilities=peer_data.get("capabilities", []),
                    version=peer_data.get("version", "1.0.0"),
                    trust_level=peer_data.get("trust_level", "anonymous"),
                )
                registered_peers.append(peer)
            
            response = BootstrapResponse(
                success=response_dict["success"],
                bootstrap_nodes=bootstrap_nodes,
                peers=registered_peers,
                message=response_dict["message"],
                timestamp=response_dict["timestamp"]
            )
            
            logger.info(f"🚀 Received bootstrap info from {bootstrap_address}")
            # Cache the response
            self._bootstrap_cache[cache_key] = (response, time.time())
            return response
            
        except Exception as e:
            logger.error(f"Bootstrap request error: {e}")
            return None
    
    async def bootstrap(self, register_self: bool = False,
                       port_ws: Optional[int] = None,
                       port_udp: Optional[int] = None) -> List[BootstrapNode]:
        """Bootstrap by contacting known bootstrap nodes with retry logic.

        Args:
            register_self: If True, register this node as a peer on the bootstrap.
            port_ws: WebSocket port (required if register_self=True).
            port_udp: UDP port (required if register_self=True).

        Returns:
            List of discovered bootstrap nodes.
        """
        nodes = []
        max_retries = 3

        for attempt in range(max_retries):
            for bootstrap_node in self.bootstrap_nodes.values():
                if bootstrap_node.node_id == self.node_id:
                    continue  # Skip self

                response = await self.request_bootstrap(
                    bootstrap_node.ip_address,
                    bootstrap_node.port,
                    register=register_self,
                    port_ws=port_ws,
                    port_udp=port_udp,
                )

                if response and response.success:
                    nodes.extend(response.bootstrap_nodes)

                    # Store discovered peers for later connection
                    for peer in response.peers:
                        if peer.node_id != self.node_id:
                            async with self._lock:
                                self._peers[peer.node_id] = peer

                    # Add new bootstrap nodes to our list
                    for node in response.bootstrap_nodes:
                        if node.node_id not in self.bootstrap_nodes:
                            self.add_bootstrap_node(node)

                    # We got a good response, no need to try more
                    break

            if nodes:
                # Emit bootstrap complete event
                try:
                    await event_bus.publish(ASIMEvent(
                        event_type=EventType.BOOTSTRAP_COMPLETE,
                        source="BootstrapService",
                        data={"node_id": self.node_id, "mode": "client", "nodes_found": len(nodes)},
                    ))
                except Exception:
                    pass
                break

            if attempt < max_retries - 1:
                delay = 2.0 ** attempt  # 1s, 2s, 4s
                logger.info(f"Bootstrap retry {attempt+1}/{max_retries} in {delay}s...")
                await asyncio.sleep(delay)
            else:
                # Emit bootstrap failed event
                try:
                    await event_bus.publish(ASIMEvent(
                        event_type=EventType.BOOTSTRAP_FAILED,
                        source="BootstrapService",
                        data={"node_id": self.node_id, "attempts": max_retries},
                    ))
                except Exception:
                    pass

        logger.info(f"Bootstrapped with {len(nodes)} nodes, {len(self._peers)} known peers")
        return nodes

    def add_known_peer(self, peer_id: str, peer_info: Dict[str, Any]):
        """Add a known peer."""
        self.known_peers[peer_id] = {
            **peer_info,
            "last_seen": time.time()
        }
    
    def get_known_peers(self) -> List[Dict[str, Any]]:
        """Get known peers."""
        cutoff = time.time() - self.NODE_TIMEOUT
        return [
            {**peer, "node_id": node_id}
            for node_id, peer in self.known_peers.items()
            if peer["last_seen"] > cutoff
        ]
    
    # ------------------------------------------------------------------
    # Peer Registration (for dynamic discovery via P2PTransport)
    # ------------------------------------------------------------------
    
    async def register_peer(self, peer: RegisteredPeer) -> bool:
        """Register a peer with this bootstrap service.
        
        The peer will be returned to other nodes on bootstrap requests.
        """
        async with self._lock:
            self._peers[peer.node_id] = peer
        logger.info(f"📝 Registered peer: {peer.node_id} at {peer.ip_address}:{peer.port_ws} (WS)")
        # Emit peer registered event
        try:
            await event_bus.publish(ASIMEvent(
                event_type=EventType.PEER_REGISTERED,
                source="BootstrapService",
                data={"peer_id": peer.node_id, "ip": peer.ip_address, "port_ws": peer.port_ws},
            ))
        except Exception:
            pass
        return True
    
    async def unregister_peer(self, node_id: str) -> bool:
        """Remove a peer registration."""
        async with self._lock:
            if node_id in self._peers:
                del self._peers[node_id]
                logger.info(f"📝 Unregistered peer: {node_id}")
                return True
        return False
    
    async def get_registered_peers(self) -> List[RegisteredPeer]:
        """Get all non-stale registered peers."""
        async with self._lock:
            cutoff = time.time() - self.NODE_TIMEOUT
            return [
                p for p in self._peers.values()
                if p.last_seen > cutoff and p.node_id != self.node_id
            ]
    
    async def discover_and_connect(self, transport: 'P2PTransport',
                                    max_peers: int = 5,
                                    dht: Optional['KademliaDHT'] = None) -> int:
        """Discover peers via bootstrap and connect to them via P2PTransport.
        
        This is the main integration point between bootstrap and transport.
        After bootstrapping, call this to establish WebSocket connections
        with discovered peers (triggering HELLO/ACK handshake).
        
        Args:
            transport: The P2PTransport instance to use for connections.
            max_peers: Maximum number of peers to connect to.
            dht: Optional KademliaDHT to populate with discovered peers.
        
        Returns:
            Number of successful connections.
        """
        connected = 0
        
        # Get all known registered peers
        peers = list(self._peers.values())
        
        # Feed peers into Kademlia DHT routing table first
        if dht is not None and peers:
            peer_dicts = [
                {
                    "node_id": p.node_id,
                    "host": p.ip_address,
                    "port_udp": p.port_udp,
                }
                for p in peers
            ]
            dht.add_nodes_from_bootstrap(peer_dicts)
        
        for peer in peers[:max_peers]:
            try:
                peer_id = await transport.connect_peer(
                    host=peer.ip_address,
                    port_ws=peer.port_ws,
                    timeout=5.0,
                )
                if peer_id:
                    connected += 1
                    logger.info(f"🔗 Connected to peer {peer_id} via bootstrap discovery")
                else:
                    logger.debug(f"Failed to connect to peer {peer.node_id} at {peer.ip_address}:{peer.port_ws}")
            except Exception as e:
                logger.debug(f"Error connecting to peer {peer.node_id}: {e}")
        
        logger.info(f"🚀 Bootstrap discovery: connected to {connected}/{len(peers)} peers")
        return connected
    
    async def _cleanup_stale_nodes(self):
        """Cleanup stale bootstrap nodes."""
        while self._running:
            try:
                cutoff = time.time() - self.NODE_TIMEOUT
                stale_nodes = [
                    node_id for node_id, node in self.bootstrap_nodes.items()
                    if node.last_seen < cutoff and node.node_id != self.node_id
                ]
                
                for node_id in stale_nodes:
                    del self.bootstrap_nodes[node_id]
                    logger.info(f"🚀 Removed stale bootstrap node: {node_id}")
                
                # Cleanup stale known peers
                stale_peers = [
                    peer_id for peer_id, peer in self.known_peers.items()
                    if peer["last_seen"] < cutoff
                ]
                
                for peer_id in stale_peers:
                    del self.known_peers[peer_id]
                
                # Cleanup stale registered peers
                async with self._lock:
                    stale_registered = [
                        peer_id for peer_id, peer in self._peers.items()
                        if peer.last_seen < cutoff
                    ]
                    for peer_id in stale_registered:
                        try:
                            del self._peers[peer_id]
                        except KeyError:
                            pass
                
                if stale_nodes or stale_peers or stale_registered:
                    logger.info(f"🚀 Cleaned {len(stale_nodes)} bootstrap nodes, {len(stale_peers)} peers, {len(stale_registered)} registered peers")
                
            except Exception as e:
                logger.error(f"Bootstrap cleanup error: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bootstrap statistics."""
        return {
            "node_id": self.node_id,
            "is_bootstrap": self.is_bootstrap,
            "ip_address": self.ip_address,
            "port": self.port,
            "total_bootstrap_nodes": len(self.bootstrap_nodes),
            "known_peers": len(self.known_peers),
            "registered_peers": len(self._peers),
            "running": self._running
        }


# Global bootstrap service instance
_bootstrap_service: Optional[BootstrapService] = None


def get_bootstrap_service(node_id: str, is_bootstrap: bool = False, port: Optional[int] = None) -> BootstrapService:
    """Get or create global bootstrap service instance."""
    global _bootstrap_service
    if _bootstrap_service is None:
        _bootstrap_service = BootstrapService(node_id, is_bootstrap, port)
    return _bootstrap_service


def reset_bootstrap_service():
    """Reset global bootstrap service instance (for testing)."""
    global _bootstrap_service
    if _bootstrap_service and _bootstrap_service._running:
        # Note: This won't properly stop the async loop in tests
        pass
    _bootstrap_service = None
