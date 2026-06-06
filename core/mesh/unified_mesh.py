
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified Mesh Coordinator
=================================
Combines Kademlia DHT + WebRTC + LAN Discovery
Single interface for all mesh operations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ASIM_MESH")

class MeshLayer(Enum):
    """Mesh architecture layers"""
    LOCAL = "local"       # Same device
    LAN = "lan"          # Local network (WiFi/Ethernet)
    COMMUNITY = "community"  # Nearby mesh nodes
    GLOBAL = "global"    # Internet-connected nodes

@dataclass
class MeshPeer:
    """Unified mesh peer"""
    peer_id: str
    layers: List[MeshLayer]
    addresses: Dict[str, str]  # layer -> address
    capabilities: List[str]
    last_seen: datetime
    latency_ms: Optional[float]
    trust_score: float

class UnifiedMeshCoordinator:
    """
    Unified Mesh Coordinator
    
    Combines:
    - Kademlia DHT (global discovery)
    - WebRTC (P2P connections)
    - LAN Discovery (local network)
    
    Provides single API for all mesh operations
    """
    
    def __init__(self, node_id: str = None):
        self.node_id = node_id or self._generate_node_id()
        self.started_at = datetime.now()
        self.status = "initializing"
        
        # Sub-systems (initialized on demand)
        self._kademlia = None
        self._webrtc = None
        self._lan = None
        
        # Peer registry
        self.peers: Dict[str, MeshPeer] = {}
        self.local_peers: set = set()  # Peer IDs available on LAN
        
        # Message routing
        self.message_handlers: Dict[str, List[Callable]] = {}
        
        # Sync state
        self.sync_state: Dict[str, Any] = {}
        
        logger.info(f"🌐 Unified Mesh initialized: {self.node_id[:16]}")
    
    def _generate_node_id(self) -> str:
        """Generate unique node ID"""
        import hashlib
        import random
        return hashlib.sha1(
            f"{datetime.now().isoformat()}:{random.getrandbits(128)}".encode()
        ).hexdigest()
    
    async def initialize(self):
        """Initialize all mesh sub-systems"""
        logger.info("🚀 Initializing mesh sub-systems...")
        
        # 1. Kademlia DHT (global discovery)
        try:
            from .kademlia_dht import get_kademlia_dht
            self._kademlia = get_kademlia_dht(self.node_id)
            logger.info("  ✅ Kademlia DHT")
        except Exception as e:
            logger.warning(f"  ⚠️ Kademlia DHT deferred: {e}")
        
        # 2. WebRTC (P2P connections)
        try:
            from .webrtc_mesh import get_webrtc_mesh
            self._webrtc = get_webrtc_mesh(self.node_id)
            self._webrtc.start_monitoring()
            logger.info("  ✅ WebRTC Mesh")
        except Exception as e:
            logger.warning(f"  ⚠️ WebRTC deferred: {e}")
        
        # 3. LAN Discovery
        try:
            from .auto_discovery import get_lan_discovery
            self._lan = get_lan_discovery()
            self._lan.start()
            logger.info("  ✅ LAN Discovery")
        except Exception as e:
            logger.warning(f"  ⚠️ LAN Discovery deferred: {e}")
        
        self.status = "running"
        logger.info("🎉 Mesh initialization complete")
    
    async def shutdown(self):
        """Shutdown mesh systems"""
        logger.info("🛑 Shutting down mesh...")
        
        if self._webrtc:
            self._webrtc.stop_monitoring()
        
        if self._lan:
            self._lan.stop()
        
        self.status = "shutdown"
        logger.info("✅ Mesh shutdown complete")
    
    # === Peer Discovery ===
    
    async def discover_peers(self, layer: MeshLayer = None) -> List[MeshPeer]:
        """Discover peers across all or specific layer"""
        discovered = []
        
        if layer is None or layer == MeshLayer.LAN:
            # LAN discovery
            if self._lan:
                lan_peers = self._lan.get_peers()
                for peer in lan_peers:
                    mesh_peer = MeshPeer(
                        peer_id=peer.node_id,
                        layers=[MeshLayer.LAN],
                        addresses={'lan': f"{peer.ip}:{peer.port}"},
                        capabilities=peer.capabilities,
                        last_seen=datetime.now(),
                        latency_ms=None,
                        trust_score=0.8  # LAN peers are trusted
                    )
                    self.peers[peer.node_id] = mesh_peer
                    self.local_peers.add(peer.node_id)
                    discovered.append(mesh_peer)
        
        if layer is None or layer == MeshLayer.GLOBAL:
            # DHT discovery
            if self._kademlia:
                closest = self._kademlia.get_closest_nodes(self.node_id, 20)
                for node in closest:
                    if node.node_id not in self.peers:
                        mesh_peer = MeshPeer(
                            peer_id=node.node_id,
                            layers=[MeshLayer.GLOBAL],
                            addresses={'global': f"{node.ip}:{node.port}"},
                            capabilities=node.capabilities,
                            last_seen=node.last_seen,
                            latency_ms=None,
                            trust_score=0.5  # Global peers need verification
                        )
                        self.peers[node.node_id] = mesh_peer
                        discovered.append(mesh_peer)
        
        return discovered
    
    def get_peer(self, peer_id: str) -> Optional[MeshPeer]:
        """Get peer by ID"""
        return self.peers.get(peer_id)
    
    def get_peers_by_layer(self, layer: MeshLayer) -> List[MeshPeer]:
        """Get all peers in specific layer"""
        return [
            peer for peer in self.peers.values()
            if layer in peer.layers
        ]
    
    # === Connection Management ===
    
    async def connect_peer(self, peer_id: str, layer: MeshLayer = None) -> bool:
        """Connect to a specific peer"""
        peer = self.peers.get(peer_id)
        if not peer:
            logger.error(f"Peer not found: {peer_id[:16]}")
            return False
        
        # Try layers in order of preference
        layers_to_try = [layer] if layer else [MeshLayer.LAN, MeshLayer.COMMUNITY, MeshLayer.GLOBAL]
        
        for try_layer in layers_to_try:
            if try_layer in peer.layers:
                if try_layer == MeshLayer.LAN:
                    # LAN connections are implicit
                    return True
                
                elif try_layer in [MeshLayer.COMMUNITY, MeshLayer.GLOBAL]:
                    # Use WebRTC
                    if self._webrtc:
                        offer = await self._webrtc.create_offer(peer_id)
                        # In real implementation, would send offer via signaling
                        logger.info(f"Created WebRTC offer for {peer_id[:16]}")
                        return True
        
        return False
    
    async def send_to_peer(self, peer_id: str, message: Dict) -> bool:
        """Send message to specific peer"""
        peer = self.peers.get(peer_id)
        if not peer:
            return False
        
        # Find best connection
        if MeshLayer.LAN in peer.layers and peer_id in self.local_peers:
            # Send via LAN (would use direct socket)
            logger.debug(f"Sending via LAN to {peer_id[:16]}")
            return True
        
        # Try WebRTC
        if self._webrtc:
            conn = self._webrtc.get_connection(peer_id)
            if conn:
                return await self._webrtc.send_message(conn.connection_id, message)
        
        return False
    
    async def broadcast(self, message: Dict, layers: List[MeshLayer] = None,
                       exclude: List[str] = None) -> Dict[str, int]:
        """Broadcast message to all peers in specified layers"""
        layers = layers or [MeshLayer.LAN, MeshLayer.COMMUNITY, MeshLayer.GLOBAL]
        exclude = set(exclude or [])
        
        results = {'sent': 0, 'failed': 0, 'by_layer': {}}
        
        for layer in layers:
            layer_peers = self.get_peers_by_layer(layer)
            layer_sent = 0
            layer_failed = 0
            
            for peer in layer_peers:
                if peer.peer_id in exclude:
                    continue
                
                success = await self.send_to_peer(peer.peer_id, message)
                if success:
                    layer_sent += 1
                    results['sent'] += 1
                else:
                    layer_failed += 1
                    results['failed'] += 1
            
            results['by_layer'][layer.value] = {
                'sent': layer_sent,
                'failed': layer_failed,
                'total': len(layer_peers)
            }
        
        return results
    
    # === Data Sync ===
    
    async def sync_data(self, peer_id: str, data_type: str = "all") -> Dict:
        """Synchronize data with peer"""
        message = {
            'type': 'sync_request',
            'from': self.node_id,
            'data_type': data_type,
            'timestamp': datetime.now().isoformat()
        }
        
        success = await self.send_to_peer(peer_id, message)
        
        return {
            'peer': peer_id[:16],
            'success': success,
            'data_type': data_type
        }
    
    async def handle_sync_request(self, peer_id: str, request: Dict):
        """Handle incoming sync request"""
        data_type = request.get('data_type', 'all')
        
        logger.info(f"Sync request from {peer_id[:16]}: {data_type}")
        
        # Would prepare and send data here
        response = {
            'type': 'sync_response',
            'from': self.node_id,
            'data': {},  # Would include actual data
            'timestamp': datetime.now().isoformat()
        }
        
        await self.send_to_peer(peer_id, response)
    
    # === Event Handling ===
    
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.message_handlers:
            self.message_handlers[event_type] = []
        self.message_handlers[event_type].append(handler)
    
    async def _notify_handlers(self, event_type: str, data: Dict):
        """Notify event handlers"""
        handlers = self.message_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Handler error: {e}")
    
    # === Federation ===
    
    def get_federation_map(self) -> Dict[str, Any]:
        """Get federation status"""
        return {
            'this_node': self.node_id[:16] + "...",
            'status': self.status,
            'total_peers': len(self.peers),
            'by_layer': {
                'lan': len(self.get_peers_by_layer(MeshLayer.LAN)),
                'community': len(self.get_peers_by_layer(MeshLayer.COMMUNITY)),
                'global': len(self.get_peers_by_layer(MeshLayer.GLOBAL))
            },
            'local_peers': len(self.local_peers),
            'started_at': self.started_at.isoformat()
        }
    
    def join_federation(self, node_type: str = "personal", 
                       country: str = "XX") -> Dict:
        """Join the mesh federation"""
        return {
            'node_id': self.node_id,
            'type': node_type,
            'country': country,
            'joined_at': datetime.now().isoformat(),
            'status': 'active'
        }
    
    # === Statistics ===
    
    def get_mesh_stats(self) -> Dict[str, Any]:
        """Get complete mesh statistics"""
        stats = {
            'node_id': self.node_id[:16] + "...",
            'status': self.status,
            'uptime_seconds': (datetime.now() - self.started_at).total_seconds(),
            'peers': {
                'total': len(self.peers),
                'by_layer': {}
            },
            'subsystems': {}
        }
        
        # Layer breakdown
        for layer in MeshLayer:
            count = len(self.get_peers_by_layer(layer))
            stats['peers']['by_layer'][layer.value] = count
        
        # Subsystem stats
        if self._kademlia:
            stats['subsystems']['kademlia'] = self._kademlia.get_stats()
        
        if self._webrtc:
            stats['subsystems']['webrtc'] = self._webrtc.get_stats()
        
        if self._lan:
            stats['subsystems']['lan'] = {
                'running': self._lan.running,
                'peers': len(self._lan.get_peers())
            }
        
        return stats

_coordinator = None

async def get_mesh_coordinator(node_id: str = None) -> UnifiedMeshCoordinator:
    """Get mesh coordinator singleton"""
    global _coordinator
    if _coordinator is None:
        _coordinator = UnifiedMeshCoordinator(node_id)
        await _coordinator.initialize()
    return _coordinator

if __name__ == "__main__":
    import asyncio
    import sys
    
    async def main():
        mesh = await get_mesh_coordinator()
        
        if len(sys.argv) > 1 and sys.argv[1] == "discover":
            peers = await mesh.discover_peers()
            print(f"Discovered {len(peers)} peers")
            for peer in peers:
                print(f"  - {peer.peer_id[:16]}... ({', '.join(l.value for l in peer.layers)})")
        
        elif len(sys.argv) > 1 and sys.argv[1] == "stats":
            import json
            print(json.dumps(mesh.get_mesh_stats(), indent=2))
        
        elif len(sys.argv) > 1 and sys.argv[1] == "federation":
            import json
            print(json.dumps(mesh.get_federation_map(), indent=2))
        
        else:
            print("Usage: python unified_mesh.py [discover|stats|federation]")
        
        await mesh.shutdown()
    
    asyncio.run(main())
