
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Federated Mesh Network
==================================
Hybrid Federated Mesh: Star + Mesh + Tree + Ring
P2P, resource sharing, offline-first sync
"""

import asyncio
import json
import logging
import hashlib
import time
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger("ASIM_FEDERATED_MESH")

class NodeType(Enum):
    SOVEREIGN = "sovereign"      # Government/governance nodes
    ENTERPRISE = "enterprise"    # Corporate nodes
    COMMUNITY = "community"      # Community/local nodes
    PERSONAL = "personal"        # Individual user nodes
    EDGE = "edge"               # Edge computing nodes
    SATELLITE = "satellite"     # Satellite nodes

class NodeStatus(Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    SYNCING = "syncing"
    MAINTENANCE = "maintenance"

@dataclass
class MeshNode:
    """Node in the federated mesh"""
    node_id: str
    node_type: NodeType
    name: str
    country: str
    region: str
    latitude: float
    longitude: float
    capabilities: List[str] = field(default_factory=list)
    resources: Dict[str, float] = field(default_factory=dict)  # CPU, RAM, storage
    connections: List[str] = field(default_factory=list)  # Connected node IDs
    status: NodeStatus = NodeStatus.OFFLINE
    last_seen: Optional[datetime] = None
    reputation: float = 1.0  # 0.0 - 5.0
    dharma_score: float = 100.0  # Compliance with Dharma principles
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'name': self.name,
            'country': self.country,
            'region': self.region,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'capabilities': self.capabilities,
            'resources': self.resources,
            'connections': self.connections,
            'status': self.status.value,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'reputation': self.reputation,
            'dharma_score': self.dharma_score
        }

class FederatedMeshNetwork:
    """
    Federated Mesh Network (Quad-System + Personal)
    - Personal: Individual users
    - Family: Household nodes
    - Community: Local community mesh
    - Enterprise: Corporate infrastructure
    - Sovereign: Government nodes
    """
    
    def __init__(self):
        self.nodes: Dict[str, MeshNode] = {}
        self.my_node_id: Optional[str] = None
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> node_ids
        self.routing_table: Dict[str, List[str]] = {}  # destination -> next_hop
        self.resource_pool: Dict[str, Dict[str, float]] = {}  # node_id -> resources
        
        # Initialize with known sovereign nodes
        self._init_sovereign_nodes()
    
    def _init_sovereign_nodes(self):
        """Initialize sovereign/government nodes"""
        sovereign_nodes = [
            MeshNode(
                node_id="sov-us-1",
                node_type=NodeType.SOVEREIGN,
                name="US Federal Node",
                country="US",
                region="North America",
                latitude=38.9072,
                longitude=-77.0369,
                capabilities=["identity", "notarization", "voting"],
                resources={"cpu": 1000, "ram": 2048, "storage": 10000},
                status=NodeStatus.OFFLINE,
                dharma_score=85.0
            ),
            MeshNode(
                node_id="sov-eu-1",
                node_type=NodeType.SOVEREIGN,
                name="EU Commission Node",
                country="EU",
                region="Europe",
                latitude=50.8503,
                longitude=4.3517,
                capabilities=["identity", "gdpr_compliance", "eidas"],
                resources={"cpu": 1000, "ram": 2048, "storage": 10000},
                status=NodeStatus.OFFLINE,
                dharma_score=95.0  # High Dharma alignment
            ),
            MeshNode(
                node_id="sov-np-1",
                node_type=NodeType.SOVEREIGN,
                name="Nepal Government Node",
                country="NP",
                region="Asia Pacific",
                latitude=27.7172,
                longitude=85.3240,
                capabilities=["identity", "nagarik_app", "tax_filing"],
                resources={"cpu": 500, "ram": 1024, "storage": 5000},
                status=NodeStatus.OFFLINE,
                dharma_score=98.0  # Highest Dharma - birthplace
            ),
            MeshNode(
                node_id="sov-in-1",
                node_type=NodeType.SOVEREIGN,
                name="India Aadhaar Node",
                country="IN",
                region="Asia Pacific",
                latitude=28.6139,
                longitude=77.2090,
                capabilities=["identity", "aadhaar", "upi"],
                resources={"cpu": 2000, "ram": 4096, "storage": 20000},
                status=NodeStatus.OFFLINE,
                dharma_score=92.0
            ),
            MeshNode(
                node_id="sov-sg-1",
                node_type=NodeType.SOVEREIGN,
                name="Singapore SingPass Node",
                country="SG",
                region="Asia Pacific",
                latitude=1.3521,
                longitude=103.8198,
                capabilities=["identity", "singpass", "myinfo"],
                resources={"cpu": 800, "ram": 1600, "storage": 8000},
                status=NodeStatus.OFFLINE,
                dharma_score=94.0
            ),
            MeshNode(
                node_id="sov-uk-1",
                node_type=NodeType.SOVEREIGN,
                name="UK Government Node",
                country="GB",
                region="Europe",
                latitude=51.5074,
                longitude=-0.1278,
                capabilities=["identity", "govuk_verify", "nhs"],
                resources={"cpu": 1000, "ram": 2048, "storage": 10000},
                status=NodeStatus.OFFLINE,
                dharma_score=88.0
            ),
        ]
        
        for node in sovereign_nodes:
            self.nodes[node.node_id] = node
    
    def register_node(self, node: MeshNode) -> bool:
        """Register a new node in the mesh"""
        if node.node_id in self.nodes:
            logger.warning(f"Node {node.node_id} already exists, updating")
        
        self.nodes[node.node_id] = node
        logger.info(f"✅ Registered {node.node_type.value} node: {node.name} ({node.country})")
        return True
    
    def create_personal_node(self, user_id: str, country: str, 
                          lat: float, lon: float) -> MeshNode:
        """Create a personal node for a user"""
        node_id = f"pers-{user_id}-{uuid.uuid4().hex[:8]}"
        
        node = MeshNode(
            node_id=node_id,
            node_type=NodeType.PERSONAL,
            name=f"Personal Node {user_id}",
            country=country,
            region=self._get_region(country),
            latitude=lat,
            longitude=lon,
            capabilities=["storage", "compute", "relay"],
            resources={"cpu": 50, "ram": 256, "storage": 1000},
            status=NodeStatus.ONLINE,
            last_seen=datetime.now(),
            dharma_score=100.0  # Personal nodes start at 100
        )
        
        self.register_node(node)
        self.my_node_id = node_id
        
        return node
    
    def _get_region(self, country: str) -> str:
        """Get geographic region for country"""
        regions = {
            'US': 'North America', 'CA': 'North America', 'MX': 'North America',
            'GB': 'Europe', 'DE': 'Europe', 'FR': 'Europe', 'IT': 'Europe', 'ES': 'Europe',
            'NP': 'Asia Pacific', 'IN': 'Asia Pacific', 'CN': 'Asia Pacific', 
            'JP': 'Asia Pacific', 'KR': 'Asia Pacific', 'SG': 'Asia Pacific',
            'AU': 'Asia Pacific', 'NZ': 'Asia Pacific',
            'BR': 'South America', 'AR': 'South America', 'CL': 'South America',
            'ZA': 'Africa', 'NG': 'Africa', 'KE': 'Africa', 'EG': 'Africa',
            'AE': 'Middle East', 'SA': 'Middle East', 'IL': 'Middle East',
        }
        return regions.get(country.upper(), 'Unknown')
    
    def discover_peers(self, node_id: str, radius_km: float = 100) -> List[MeshNode]:
        """Discover nearby peer nodes"""
        import math
        
        node = self.nodes.get(node_id)
        if not node:
            return []
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth radius in km
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        peers = []
        for other in self.nodes.values():
            if other.node_id != node_id and other.status == NodeStatus.ONLINE:
                distance = haversine(node.latitude, node.longitude, 
                                   other.latitude, other.longitude)
                if distance <= radius_km:
                    peers.append(other)
        
        return sorted(peers, key=lambda n: n.dharma_score, reverse=True)
    
    def connect_to_peers(self, node_id: str, max_peers: int = 5) -> List[str]:
        """Connect a node to nearby peers"""
        node = self.nodes.get(node_id)
        if not node:
            return []
        
        # Find best peers (by Dharma score and distance)
        peers = self.discover_peers(node_id, radius_km=500)[:max_peers]
        
        connected = []
        for peer in peers:
            node.connections.append(peer.node_id)
            peer.connections.append(node_id)
            connected.append(peer.node_id)
            logger.info(f"🔗 {node_id} connected to {peer.node_id} ({peer.name})")
        
        return connected
    
    def share_resources(self, from_node: str, to_node: str, 
                       resource_type: str, amount: float) -> bool:
        """Share resources between nodes (2-5% sharing)"""
        from_n = self.nodes.get(from_node)
        to_n = self.nodes.get(to_node)
        
        if not from_n or not to_n:
            return False
        
        available = from_n.resources.get(resource_type, 0)
        # Share 2-5% (configurable)
        share_amount = min(amount, available * 0.05)
        
        if share_amount > 0:
            from_n.resources[resource_type] -= share_amount
            to_n.resources[resource_type] += share_amount
            
            logger.info(f"📤 {from_node} shared {share_amount:.1f} {resource_type} with {to_node}")
            return True
        
        return False
    
    def route_message(self, from_node: str, to_node: str, 
                     message: Dict[str, Any]) -> bool:
        """Route a message through the mesh"""
        if to_node not in self.nodes:
            return False
        
        # Direct connection
        if to_node in self.nodes.get(from_node, MeshNode("", NodeType.PERSONAL, "", "", "", 0, 0)).connections:
            logger.info(f"📨 Direct message: {from_node} -> {to_node}")
            return True
        
        # Multi-hop routing
        path = self._find_path(from_node, to_node)
        if path:
            logger.info(f"📨 Routed message: {' -> '.join(path)}")
            return True
        
        return False
    
    def _find_path(self, start: str, end: str, max_hops: int = 5) -> Optional[List[str]]:
        """Find path between nodes using BFS"""
        from collections import deque
        
        visited = {start}
        queue = deque([(start, [start])])
        
        while queue and len(queue[0][1]) <= max_hops:
            current, path = queue.popleft()
            
            if current == end:
                return path
            
            node = self.nodes.get(current)
            if node:
                for neighbor in node.connections:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def sync_data(self, node_id: str) -> Dict[str, Any]:
        """Sync data with connected peers (CRDT-based)"""
        node = self.nodes.get(node_id)
        if not node:
            return {'error': 'Node not found'}
        
        sync_results = {
            'node_id': node_id,
            'peers_synced': 0,
            'data_transferred': 0,
            'conflicts_resolved': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        for peer_id in node.connections:
            peer = self.nodes.get(peer_id)
            if peer and peer.status == NodeStatus.ONLINE:
                # Simulate CRDT sync
                sync_results['peers_synced'] += 1
                sync_results['data_transferred'] += 100  # KB
                logger.info(f"🔄 {node_id} synced with {peer_id}")
        
        return sync_results
    
    def get_mesh_stats(self) -> Dict[str, Any]:
        """Get mesh network statistics"""
        total = len(self.nodes)
        by_type = {}
        by_status = {}
        by_country = {}
        
        for node in self.nodes.values():
            by_type[node.node_type.value] = by_type.get(node.node_type.value, 0) + 1
            by_status[node.status.value] = by_status.get(node.status.value, 0) + 1
            by_country[node.country] = by_country.get(node.country, 0) + 1
        
        online_count = by_status.get('online', 0)
        avg_dharma = sum(n.dharma_score for n in self.nodes.values()) / total if total > 0 else 0
        
        return {
            'total_nodes': total,
            'online_nodes': online_count,
            'offline_nodes': total - online_count,
            'by_type': by_type,
            'by_status': by_status,
            'by_country': len(by_country),
            'avg_dharma_score': round(avg_dharma, 2),
            'total_connections': sum(len(n.connections) for n in self.nodes.values()) // 2
        }
    
    def get_quad_system_status(self) -> Dict[str, Any]:
        """Get Quad-System (Personal/Family/Community/Enterprise/Sovereign) status"""
        layers = {
            'personal': {
                'nodes': [n.to_dict() for n in self.nodes.values() 
                         if n.node_type == NodeType.PERSONAL],
                'total_resources': sum(
                    n.resources.get('storage', 0) 
                    for n in self.nodes.values() 
                    if n.node_type == NodeType.PERSONAL
                )
            },
            'sovereign': {
                'nodes': [n.to_dict() for n in self.nodes.values() 
                         if n.node_type == NodeType.SOVEREIGN],
                'total_resources': sum(
                    n.resources.get('storage', 0) 
                    for n in self.nodes.values() 
                    if n.node_type == NodeType.SOVEREIGN
                )
            },
            'enterprise': {
                'nodes': [n.to_dict() for n in self.nodes.values() 
                         if n.node_type == NodeType.ENTERPRISE],
                'total_resources': 0  # No enterprise nodes yet
            },
            'community': {
                'nodes': [n.to_dict() for n in self.nodes.values() 
                         if n.node_type == NodeType.COMMUNITY],
                'total_resources': 0  # No community nodes yet
            }
        }
        
        return {
            'layers': layers,
            'total_nodes': len(self.nodes),
            'my_node': self.my_node_id,
            'mesh_topology': 'federated_hybrid',
            'sync_protocol': 'crdt_offline_first'
        }

_mesh_network = None

def get_mesh_network() -> FederatedMeshNetwork:
    """Get or create mesh network singleton"""
    global _mesh_network
    if _mesh_network is None:
        _mesh_network = FederatedMeshNetwork()
    return _mesh_network

if __name__ == "__main__":
    import sys
    mesh = get_mesh_network()
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(mesh.get_mesh_stats(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "sovereign":
        print("Sovereign Nodes:")
        for node in mesh.nodes.values():
            if node.node_type == NodeType.SOVEREIGN:
                print(f"  {node.node_id:15} {node.name:30} {node.country:5} Dharma:{node.dharma_score}")
    elif len(sys.argv) > 1 and sys.argv[1] == "quad":
        print(json.dumps(mesh.get_quad_system_status(), indent=2))
    else:
        print("Usage: python federated_mesh.py [stats|sovereign|quad]")
