
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Sharding Manager
==========================
Horizontal scaling through sharding
Automatic data partitioning
Cross-shard queries
Rebalancing and migration
"""

import logging
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ASIM_SHARDING")

class ShardStatus(Enum):
    """Shard status"""
    ACTIVE = "active"
    READONLY = "readonly"
    MIGRATING = "migrating"
    OFFLINE = "offline"

@dataclass
class Shard:
    """Data shard"""
    shard_id: str
    node_id: str
    range_start: str  # Hash range start
    range_end: str    # Hash range end
    status: ShardStatus
    
    # Metrics
    record_count: int = 0
    size_mb: float = 0.0
    last_accessed: datetime = None
    
    # Replication
    replicas: List[str] = None  # Node IDs of replicas
    
    def __post_init__(self):
        if self.replicas is None:
            self.replicas = []

class ShardingManager:
    """
    Horizontal Scaling through Sharding
    
    Features:
    - Consistent hashing for data distribution
    - Automatic rebalancing
    - Cross-shard query aggregation
    - Hot-spot detection
    - Dynamic shard splitting
    """
    
    def __init__(self, shard_count: int = 16):
        self.shard_count = shard_count
        self.shards: Dict[str, Shard] = {}
        self.nodes: Dict[str, List[str]] = {}  # node_id -> [shard_ids]
        
        # Consistent hashing ring
        self.hash_ring: List[tuple] = []  # (hash, shard_id)
        
        # Configuration
        self.max_shard_size_mb = 1024  # 1GB per shard
        self.max_records_per_shard = 1000000
        self.replication_factor = 3
        
        self._init_shards()
        logger.info(f"🗂️ Sharding Manager initialized ({shard_count} shards)")
    
    def _init_shards(self):
        """Initialize shard layout"""
        # Create shards with equal hash ranges
        range_size = 2**32 // self.shard_count
        
        for i in range(self.shard_count):
            start = i * range_size
            end = start + range_size - 1 if i < self.shard_count - 1 else 2**32 - 1
            
            shard = Shard(
                shard_id=f"shard_{i:04d}",
                node_id=f"node_{i % 4}",  # Distribute across 4 nodes initially
                range_start=f"{start:08x}",
                range_end=f"{end:08x}",
                status=ShardStatus.ACTIVE
            )
            
            self.shards[shard.shard_id] = shard
            
            # Add to hash ring
            self.hash_ring.append((start, shard.shard_id))
            
            # Update node mapping
            if shard.node_id not in self.nodes:
                self.nodes[shard.node_id] = []
            self.nodes[shard.node_id].append(shard.shard_id)
        
        # Sort hash ring
        self.hash_ring.sort(key=lambda x: x[0])
    
    def get_shard_for_key(self, key: str) -> Shard:
        """
        Get shard for a key using consistent hashing
        """
        # Hash the key
        key_hash = int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
        
        # Find shard in hash ring (binary search)
        shard_id = self._find_shard(key_hash)
        
        return self.shards[shard_id]
    
    def _find_shard(self, key_hash: int) -> str:
        """Find shard for hash using consistent hashing"""
        # Find first ring entry >= key_hash
        for ring_hash, shard_id in self.hash_ring:
            if key_hash <= ring_hash:
                return shard_id
        
        # Wrap around to first shard
        return self.hash_ring[0][1]
    
    def route_query(self, key: str, operation: str = "read") -> Dict:
        """
        Route query to appropriate shard
        
        Returns routing info including primary and replica nodes
        """
        shard = self.get_shard_for_key(key)
        
        if shard.status == ShardStatus.OFFLINE:
            # Use replica
            if shard.replicas:
                return {
                    'shard_id': shard.shard_id,
                    'primary_node': shard.replicas[0],
                    'replica_nodes': shard.replicas[1:],
                    'status': 'replica_route'
                }
            else:
                raise Exception(f"Shard {shard.shard_id} offline, no replicas")
        
        return {
            'shard_id': shard.shard_id,
            'primary_node': shard.node_id,
            'replica_nodes': shard.replicas,
            'status': 'direct_route'
        }
    
    def execute_cross_shard_query(self, query_func, keys: List[str]) -> List[Any]:
        """
        Execute query across multiple shards
        
        Aggregates results from all relevant shards
        """
        # Group keys by shard
        shard_groups: Dict[str, List[str]] = {}
        for key in keys:
            shard = self.get_shard_for_key(key)
            if shard.shard_id not in shard_groups:
                shard_groups[shard.shard_id] = []
            shard_groups[shard.shard_id].append(key)
        
        logger.info(f"Cross-shard query: {len(keys)} keys across {len(shard_groups)} shards")
        
        # Execute on each shard (parallel in production)
        results = []
        for shard_id, shard_keys in shard_groups.items():
            shard_results = query_func(shard_id, shard_keys)
            results.extend(shard_results)
        
        return results
    
    def check_hot_spots(self) -> List[Dict]:
        """Identify hot shards (overloaded)"""
        hot_shards = []
        
        for shard in self.shards.values():
            is_hot = (
                shard.size_mb > self.max_shard_size_mb or
                shard.record_count > self.max_records_per_shard
            )
            
            if is_hot:
                hot_shards.append({
                    'shard_id': shard.shard_id,
                    'node_id': shard.node_id,
                    'size_mb': shard.size_mb,
                    'records': shard.record_count,
                    'action': 'split_recommended'
                })
        
        return hot_shards
    
    def split_shard(self, shard_id: str) -> bool:
        """Split hot shard into two shards"""
        if shard_id not in self.shards:
            return False
        
        old_shard = self.shards[shard_id]
        
        # Calculate new range
        old_start = int(old_shard.range_start, 16)
        old_end = int(old_shard.range_end, 16)
        mid = (old_start + old_end) // 2
        
        # Create new shard
        new_shard_id = f"shard_{len(self.shards):04d}"
        new_shard = Shard(
            shard_id=new_shard_id,
            node_id=old_shard.node_id,  # Same node initially
            range_start=f"{mid+1:08x}",
            range_end=old_shard.range_end,
            status=ShardStatus.MIGRATING
        )
        
        # Update old shard
        old_shard.range_end = f"{mid:08x}"
        old_shard.status = ShardStatus.MIGRATING
        
        # Add to collections
        self.shards[new_shard_id] = new_shard
        self.nodes[old_shard.node_id].append(new_shard_id)
        
        # Update hash ring
        self._rebuild_hash_ring()
        
        logger.info(f"✂️ Shard split: {shard_id} → {shard_id} + {new_shard_id}")
        
        # Trigger data migration (async in production)
        # self._migrate_shard_data(old_shard, new_shard)
        
        old_shard.status = ShardStatus.ACTIVE
        new_shard.status = ShardStatus.ACTIVE
        
        return True
    
    def rebalance_shards(self) -> Dict:
        """Rebalance shards across nodes for even distribution"""
        # Calculate target shards per node
        total_shards = len(self.shards)
        node_count = len(self.nodes)
        target_per_node = total_shards // node_count
        
        moves = []
        
        for node_id, shard_ids in self.nodes.items():
            excess = len(shard_ids) - target_per_node
            
            if excess > 0:
                # Find underloaded nodes
                for target_node, target_shards in self.nodes.items():
                    if len(target_shards) < target_per_node:
                        # Move shard
                        shard_to_move = shard_ids[0]
                        self._move_shard(shard_to_move, node_id, target_node)
                        moves.append({
                            'shard': shard_to_move,
                            'from': node_id,
                            'to': target_node
                        })
                        excess -= 1
                        if excess == 0:
                            break
        
        logger.info(f"🔄 Rebalanced {len(moves)} shards")
        return {'moves': moves, 'total_shards': total_shards}
    
    def _move_shard(self, shard_id: str, from_node: str, to_node: str):
        """Move shard to different node"""
        shard = self.shards[shard_id]
        shard.status = ShardStatus.MIGRATING
        
        # Update mappings
        self.nodes[from_node].remove(shard_id)
        self.nodes[to_node].append(shard_id)
        
        # Update shard
        shard.node_id = to_node
        shard.status = ShardStatus.ACTIVE
        
        logger.info(f"📦 Shard moved: {shard_id} {from_node} → {to_node}")
    
    def _rebuild_hash_ring(self):
        """Rebuild consistent hash ring after changes"""
        self.hash_ring = []
        for shard in self.shards.values():
            start = int(shard.range_start, 16)
            self.hash_ring.append((start, shard.shard_id))
        
        self.hash_ring.sort(key=lambda x: x[0])
    
    def get_shard_stats(self) -> Dict:
        """Get comprehensive shard statistics"""
        total_records = sum(s.record_count for s in self.shards.values())
        total_size = sum(s.size_mb for s in self.shards.values())
        
        node_distribution = {
            node_id: len(shards)
            for node_id, shards in self.nodes.items()
        }
        
        return {
            'shard_count': len(self.shards),
            'node_count': len(self.nodes),
            'total_records': total_records,
            'total_size_mb': total_size,
            'avg_shard_size_mb': total_size / len(self.shards) if self.shards else 0,
            'node_distribution': node_distribution,
            'hot_spots': len(self.check_hot_spots()),
            'replication_factor': self.replication_factor
        }
    
    def add_node(self, node_id: str) -> bool:
        """Add new node to cluster"""
        if node_id in self.nodes:
            return False
        
        self.nodes[node_id] = []
        
        # Rebalance to use new node
        self.rebalance_shards()
        
        logger.info(f"➕ Node added: {node_id}")
        return True
    
    def remove_node(self, node_id: str) -> bool:
        """Remove node from cluster (with migration)"""
        if node_id not in self.nodes:
            return False
        
        shards_to_move = self.nodes[node_id][:]
        
        # Move all shards to other nodes
        for shard_id in shards_to_move:
            # Find target node
            target_node = min(self.nodes.keys(), key=lambda n: len(self.nodes[n]) if n != node_id else float('inf'))
            self._move_shard(shard_id, node_id, target_node)
        
        del self.nodes[node_id]
        
        logger.info(f"➖ Node removed: {node_id} ({len(shards_to_move)} shards migrated)")
        return True

_sharding = None

def get_sharding_manager() -> ShardingManager:
    """Get sharding manager singleton"""
    global _sharding
    if _sharding is None:
        _sharding = ShardingManager()
    return _sharding

if __name__ == "__main__":
    import sys
    
    sharding = get_sharding_manager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "route":
        # Test routing
        for key in ["user_001", "user_002", "user_003", "contract_123"]:
            route = sharding.route_query(key)
            print(f"{key} → {route['shard_id']} on {route['primary_node']}")
            
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        import json
        print(json.dumps(sharding.get_shard_stats(), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "hotspots":
        hotspots = sharding.check_hot_spots()
        print(f"Hot spots: {len(hotspots)}")
        for h in hotspots:
            print(f"  {h['shard_id']}: {h['records']} records, {h['size_mb']} MB")
            
    elif len(sys.argv) > 1 and sys.argv[1] == "rebalance":
        result = sharding.rebalance_shards()
        print(f"Rebalanced {len(result['moves'])} shards")
        for move in result['moves']:
            print(f"  {move['shard']}: {move['from']} → {move['to']}")
            
    else:
        print("Usage: python sharding_manager.py [route|stats|hotspots|rebalance]")
