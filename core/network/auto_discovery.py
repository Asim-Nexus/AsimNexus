
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Auto Discovery & Connect
====================================
Network discovery for devices, services, and nodes.
Auto-connects to AsimNexus mesh without manual configuration.
"""
import asyncio
import socket
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import struct

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredNode:
    """A discovered node on the network."""
    node_id: str
    ip: str
    port: int
    node_type: str  # personal, company, government, satellite
    capabilities: List[str]
    public_key: str
    last_seen: str
    latency_ms: float


class AutoDiscoveryService:
    """
    Automatic network discovery for AsimNexus.
    Finds and connects to nearby nodes without manual setup.
    """
    
    MULTICAST_GROUP = "239.255.42.99"  # AsimNexus multicast address
    DISCOVERY_PORT = 19472  # AN = Asim Nexus
    BROADCAST_INTERVAL = 5  # seconds
    
    def __init__(self, node_id: str, node_type: str = "personal", 
                 capabilities: Optional[List[str]] = None):
        self.node_id = node_id
        self.node_type = node_type
        self.capabilities = capabilities or ["chat", "file_share", "mesh"]
        self.public_key = ""  # Would be actual crypto key
        self.port = 8000
        
        self.discovered_nodes: Dict[str, DiscoveredNode] = {}
        self._running = False
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._protocol: Optional[asyncio.DatagramProtocol] = None
        
    async def start(self):
        """Start the auto-discovery service."""
        self._running = True
        
        # Start listener
        await self._start_listener()
        
        # Start broadcaster
        asyncio.create_task(self._broadcast_loop())
        
        # Start node cleaner (remove stale nodes)
        asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"Auto-discovery started on {self.MULTICAST_GROUP}:{self.DISCOVERY_PORT}")
        
    async def _start_listener(self):
        """Start multicast listener."""
        try:
            # Create multicast socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self.DISCOVERY_PORT))
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(self.MULTICAST_GROUP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.setblocking(False)
            
            # Create asyncio protocol
            loop = asyncio.get_event_loop()
            self._transport, self._protocol = await loop.create_datagram_endpoint(
                lambda: DiscoveryProtocol(self),
                sock=sock
            )
            
        except Exception as e:
            logger.error(f"Failed to start discovery listener: {e}")
            
    async def _broadcast_loop(self):
        """Periodically broadcast our presence."""
        while self._running:
            try:
                await self._broadcast_presence()
                await asyncio.sleep(self.BROADCAST_INTERVAL)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                await asyncio.sleep(1)
                
    async def _broadcast_presence(self):
        """Broadcast our node info to the network."""
        message = {
            "type": "DISCOVERY",
            "node_id": self.node_id,
            "node_type": self.node_type,
            "capabilities": self.capabilities,
            "public_key": self.public_key,
            "port": self.port,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            
            data = json.dumps(message).encode()
            sock.sendto(data, (self.MULTICAST_GROUP, self.DISCOVERY_PORT))
            sock.close()
            
        except Exception as e:
            logger.debug(f"Broadcast failed: {e}")
            
    async def _cleanup_loop(self):
        """Remove nodes not seen recently."""
        while self._running:
            await asyncio.sleep(30)
            await self._cleanup_stale_nodes()
            
    async def _cleanup_stale_nodes(self):
        """Remove nodes not seen in 2 minutes."""
        now = datetime.now()
        stale = []
        
        for node_id, node in self.discovered_nodes.items():
            last_seen = datetime.fromisoformat(node.last_seen)
            if (now - last_seen).seconds > 120:
                stale.append(node_id)
                
        for node_id in stale:
            del self.discovered_nodes[node_id]
            logger.info(f"Removed stale node: {node_id}")
            
    def handle_discovery(self, data: dict, addr: Tuple[str, int]):
        """Handle incoming discovery message."""
        if data.get("node_id") == self.node_id:
            return  # Ignore ourselves
            
        # Calculate latency
        received_time = datetime.now()
        sent_time = datetime.fromisoformat(data.get("timestamp", received_time.isoformat()))
        latency_ms = (received_time - sent_time).total_seconds() * 1000
        
        node = DiscoveredNode(
            node_id=data["node_id"],
            ip=addr[0],
            port=data.get("port", 8000),
            node_type=data.get("node_type", "unknown"),
            capabilities=data.get("capabilities", []),
            public_key=data.get("public_key", ""),
            last_seen=received_time.isoformat(),
            latency_ms=latency_ms
        )
        
        # Update or add node
        is_new = node.node_id not in self.discovered_nodes
        self.discovered_nodes[node.node_id] = node
        
        if is_new:
            logger.info(f"New node discovered: {node.node_id} at {node.ip}")
            
    def get_nearby_nodes(self, node_type: Optional[str] = None) -> List[DiscoveredNode]:
        """Get list of discovered nodes."""
        nodes = list(self.discovered_nodes.values())
        if node_type:
            nodes = [n for n in nodes if n.node_type == node_type]
        return sorted(nodes, key=lambda n: n.latency_ms)
        
    def get_best_node(self, capability: str) -> Optional[DiscoveredNode]:
        """Get lowest-latency node with specific capability."""
        candidates = [
            n for n in self.discovered_nodes.values()
            if capability in n.capabilities
        ]
        if candidates:
            return min(candidates, key=lambda n: n.latency_ms)
        return None
        
    async def stop(self):
        """Stop the discovery service."""
        self._running = False
        if self._transport:
            self._transport.close()


class DiscoveryProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for discovery."""
    
    def __init__(self, service: AutoDiscoveryService):
        self.service = service
        
    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming UDP packet."""
        try:
            message = json.loads(data.decode())
            if message.get("type") == "DISCOVERY":
                self.service.handle_discovery(message, addr)
        except json.JSONDecodeError:
            pass  # Ignore invalid packets
        except Exception as e:
            logger.debug(f"Error handling discovery: {e}")


# Singleton
_discovery_service: Optional[AutoDiscoveryService] = None

async def start_discovery(node_id: str, node_type: str = "personal") -> AutoDiscoveryService:
    """Start auto-discovery service."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = AutoDiscoveryService(node_id, node_type)
        await _discovery_service.start()
    return _discovery_service

def get_discovery() -> Optional[AutoDiscoveryService]:
    """Get discovery service if running."""
    return _discovery_service
