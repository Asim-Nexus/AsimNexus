
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Mesh Layer - Kademlia DHT
=====================================
Distributed hash table for peer discovery
Kademlia protocol implementation
"""

import hashlib
import logging
import random
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger("ASIM_MESH_DHT")

K = 20  # Bucket size
ALPHA = 3  # Parallel lookups
KEY_SIZE = 160  # SHA-1 hash size

@dataclass
class NodeInfo:
    """Kademlia node information"""
    node_id: str
    ip: str
    port: int
    last_seen: datetime
    capabilities: List[str]

class KBucket:
    """Kademlia bucket (k-bucket)"""
    
    def __init__(self, min_range: int, max_range: int):
        self.min_range = min_range
        self.max_range = max_range
        self.nodes: List[NodeInfo] = []
        self.replacement_cache: List[NodeInfo] = []
    
    def add_node(self, node: NodeInfo) -> bool:
        """Add node to bucket"""
        # Check if already in bucket
        for i, n in enumerate(self.nodes):
            if n.node_id == node.node_id:
                # Update last seen (most recently seen at end)
                self.nodes.pop(i)
                self.nodes.append(node)
                return True
        
        # Add if space available
        if len(self.nodes) < K:
            self.nodes.append(node)
            return True
        
        # Bucket full, add to replacement cache
        self.replacement_cache.append(node)
        if len(self.replacement_cache) > K:
            self.replacement_cache.pop(0)
        
        return False
    
    def remove_node(self, node_id: str) -> bool:
        """Remove node from bucket"""
        for i, n in enumerate(self.nodes):
            if n.node_id == node_id:
                self.nodes.pop(i)
                # Promote from replacement cache
                if self.replacement_cache:
                    self.nodes.append(self.replacement_cache.pop(0))
                return True
        return False
    
    def get_nodes(self, count: int = K) -> List[NodeInfo]:
        """Get nodes from bucket"""
        return self.nodes[:count]
    
    def contains(self, node_id: str) -> bool:
        """Check if node is in bucket"""
        return any(n.node_id == node_id for n in self.nodes)

class KademliaDHT:
    """
    Kademlia Distributed Hash Table
    
    Key Features:
    - Peer discovery via node ID distance
    - XOR metric for distance calculation
    - K-buckets for efficient routing
    - Parallel lookups (ALPHA)
    """
    
    def __init__(self, node_id: str = None, ip: str = "127.0.0.1", port: int = 8000):
        self.node_id = node_id or self._generate_node_id()
        self.ip = ip
        self.port = port
        
        # Routing table: 160 k-buckets
        self.buckets: List[KBucket] = []
        self._init_buckets()
        
        # Data storage
        self.storage: Dict[str, Dict] = {}
        self.replication_factor = 3
        
        # Active lookups
        self.active_lookups: Set[str] = set()
        
        logger.info(f"🌐 Kademlia DHT initialized: {self.node_id[:16]}...")
    
    def _generate_node_id(self) -> str:
        """Generate random 160-bit node ID"""
        return hashlib.sha1(
            f"{datetime.now().isoformat()}:{random.getrandbits(128)}".encode()
        ).hexdigest()
    
    def _init_buckets(self):
        """Initialize 160 k-buckets"""
        for i in range(KEY_SIZE):
            min_range = 2 ** i
            max_range = 2 ** (i + 1) - 1
            self.buckets.append(KBucket(min_range, max_range))
    
    def _distance(self, node_id1: str, node_id2: str) -> int:
        """Calculate XOR distance between two node IDs"""
        # Convert hex to int
        id1 = int(node_id1, 16)
        id2 = int(node_id2, 16)
        return id1 ^ id2
    
    def _bucket_index(self, distance: int) -> int:
        """Get bucket index for distance"""
        if distance == 0:
            return 0
        return distance.bit_length() - 1
    
    def _get_bucket(self, node_id: str) -> KBucket:
        """Get appropriate bucket for node"""
        dist = self._distance(self.node_id, node_id)
        idx = self._bucket_index(dist)
        return self.buckets[idx]
    
    def add_node(self, node: NodeInfo) -> bool:
        """Add node to routing table"""
        # Don't add self
        if node.node_id == self.node_id:
            return False
        
        bucket = self._get_bucket(node.node_id)
        added = bucket.add_node(node)
        
        if added:
            logger.debug(f"Added node {node.node_id[:8]}... to bucket")
        
        return added
    
    def remove_node(self, node_id: str) -> bool:
        """Remove node from routing table"""
        bucket = self._get_bucket(node_id)
        return bucket.remove_node(node_id)
    
    def get_closest_nodes(self, target_id: str, count: int = K) -> List[NodeInfo]:
        """Get K closest nodes to target"""
        all_nodes: List[Tuple[int, NodeInfo]] = []
        
        # Collect nodes from all buckets
        for bucket in self.buckets:
            for node in bucket.nodes:
                dist = self._distance(target_id, node.node_id)
                all_nodes.append((dist, node))
        
        # Sort by distance and return closest
        all_nodes.sort(key=lambda x: x[0])
        return [node for _, node in all_nodes[:count]]
    
    def lookup_node(self, target_id: str) -> Optional[NodeInfo]:
        """Lookup specific node by ID"""
        # Check if target is us
        if target_id == self.node_id:
            return NodeInfo(
                node_id=self.node_id,
                ip=self.ip,
                port=self.port,
                last_seen=datetime.now(),
                capabilities=[]
            )
        
        # Check all buckets
        for bucket in self.buckets:
            for node in bucket.nodes:
                if node.node_id == target_id:
                    return node
        
        return None
    
    def iterative_lookup(self, target_id: str) -> List[NodeInfo]:
        """Iterative node lookup (Kademlia algorithm)"""
        if target_id == self.node_id:
            return []
        
        # Start with closest known nodes
        closest = self.get_closest_nodes(target_id, ALPHA)
        queried: Set[str] = set()
        all_results: Dict[str, NodeInfo] = {}
        
        while True:
            # Query closest unqueried nodes
            to_query = [n for n in closest if n.node_id not in queried][:ALPHA]
            
            if not to_query:
                break
            
            # In real implementation, would RPC to these nodes
            # For now, just mark as queried
            for node in to_query:
                queried.add(node.node_id)
                all_results[node.node_id] = node
            
            # Get new closest from results
            all_nodes = list(all_results.values())
            all_nodes.sort(key=lambda n: self._distance(target_id, n.node_id))
            closest = all_nodes[:K]
        
        return closest
    
    def store(self, key: str, value: Dict) -> bool:
        """Store value in DHT"""
        # Find closest nodes to key
        target_id = hashlib.sha1(key.encode()).hexdigest()
        closest = self.get_closest_nodes(target_id, self.replication_factor)
        
        # Store locally
        self.storage[key] = {
            'value': value,
            'stored_at': datetime.now().isoformat(),
            'replicated_to': [n.node_id for n in closest]
        }
        
        logger.info(f"Stored {key[:16]}... to {len(closest)} nodes")
        return True
    
    def find_value(self, key: str) -> Optional[Dict]:
        """Find value in DHT"""
        # Check local storage
        if key in self.storage:
            return self.storage[key]['value']
        
        # Find closest nodes to key
        target_id = hashlib.sha1(key.encode()).hexdigest()
        closest = self.get_closest_nodes(target_id, ALPHA)
        
        # In real implementation, would query these nodes
        # For now, return None
        return None
    
    def refresh_buckets(self):
        """Refresh buckets by querying random IDs in range"""
        for i, bucket in enumerate(self.buckets):
            if not bucket.nodes:
                # Pick random ID in this bucket's range
                random_id = random.randint(bucket.min_range, bucket.max_range)
                random_hex = format(random_id, '040x')
                
                # Start lookup
                self.iterative_lookup(random_hex)
    
    def get_stats(self) -> Dict:
        """Get DHT statistics"""
        total_nodes = sum(len(b.nodes) for b in self.buckets)
        active_buckets = sum(1 for b in self.buckets if b.nodes)
        
        return {
            'node_id': self.node_id[:16] + "...",
            'address': f"{self.ip}:{self.port}",
            'total_nodes': total_nodes,
            'active_buckets': active_buckets,
            'stored_keys': len(self.storage),
            'buckets_with_replacement': sum(1 for b in self.buckets if b.replacement_cache)
        }

_dht = None

def get_kademlia_dht(node_id: str = None) -> KademliaDHT:
    """Get Kademlia DHT singleton"""
    global _dht
    if _dht is None:
        _dht = KademliaDHT(node_id)
    return _dht

if __name__ == "__main__":
    import sys
    
    dht = get_kademlia_dht()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Add test nodes
        for i in range(10):
            node = NodeInfo(
                node_id=dht._generate_node_id(),
                ip=f"192.168.1.{100+i}",
                port=8000,
                last_seen=datetime.now(),
                capabilities=[]
            )
            dht.add_node(node)
        
        print("Added 10 test nodes")
        print(f"Stats: {dht.get_stats()}")
        
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        import json
        print(json.dumps(dht.get_stats(), indent=2))
        
    else:
        print("Usage: python kademlia_dht.py [test|stats]")
