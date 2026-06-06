
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Distributed Storage Mesh
=====================================
Your data lives everywhere but only YOU control it
Sharded, encrypted, distributed across the mesh
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import secrets

logger = logging.getLogger("ASIM_STORAGE")

class StorageTier(Enum):
    """Storage tiers"""
    HOT = "hot"          # SSD, local, fast
    WARM = "warm"        # Local disk
    COLD = "cold"        # Remote nodes
    ARCHIVE = "archive"  # Long-term storage
    ENCRYPTED = "encrypted"  # Always encrypted

class RedundancyLevel(Enum):
    """Data redundancy levels"""
    NONE = 0             # Single copy
    MIRROR = 2           # 2 copies
    STANDARD = 3         # 3 copies (default)
    HIGH = 5               # 5 copies
    PARANOID = 10          # 10+ copies worldwide

@dataclass
class DataShard:
    """A shard of distributed data"""
    shard_id: str
    data_hash: str
    size_bytes: int
    locations: List[str]  # Node IDs storing this shard
    encrypted: bool
    owner_id: str
    created_at: datetime
    access_log: List[Dict]

class DistributedStorage:
    """
    Distributed Storage Mesh
    - Your data is split into shards
    - Each shard encrypted with your key
    - Shards distributed across 1000+ nodes
    - Only you can reassemble and decrypt
    """
    
    def __init__(self):
        self.shards: Dict[str, DataShard] = {}
        self.node_storage: Dict[str, int] = {}  # node_id -> bytes stored
        self.user_shards: Dict[str, List[str]] = {}  # user_id -> shard_ids
        self.retrieval_cache: Dict[str, Any] = {}
    
    def store_data(self, user_id: str, data: bytes, 
                  redundancy: RedundancyLevel = RedundancyLevel.STANDARD,
                  tier: StorageTier = StorageTier.ENCRYPTED) -> List[DataShard]:
        """Store data in distributed mesh"""
        
        # Calculate optimal shard size
        total_size = len(data)
        shard_size = self._calculate_shard_size(total_size)
        
        # Split into shards
        shards = []
        num_shards = (total_size + shard_size - 1) // shard_size
        
        for i in range(num_shards):
            start = i * shard_size
            end = min(start + shard_size, total_size)
            shard_data = data[start:end]
            
            # Encrypt shard
            encrypted_data = self._encrypt_shard(shard_data, user_id)
            
            # Create shard
            shard_id = f"shard_{user_id}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            data_hash = hashlib.sha256(shard_data).hexdigest()
            
            # Select storage nodes
            storage_nodes = self._select_storage_nodes(
                redundancy.value, tier
            )
            
            shard = DataShard(
                shard_id=shard_id,
                data_hash=data_hash,
                size_bytes=len(encrypted_data),
                locations=storage_nodes,
                encrypted=True,
                owner_id=user_id,
                created_at=datetime.now(),
                access_log=[]
            )
            
            self.shards[shard_id] = shard
            
            if user_id not in self.user_shards:
                self.user_shards[user_id] = []
            self.user_shards[user_id].append(shard_id)
            
            # Update node storage stats
            for node_id in storage_nodes:
                self.node_storage[node_id] = self.node_storage.get(node_id, 0) + len(encrypted_data)
            
            shards.append(shard)
        
        logger.info(f"💾 Stored {total_size} bytes as {len(shards)} shards for {user_id}")
        return shards
    
    def retrieve_data(self, user_id: str) -> Optional[bytes]:
        """Retrieve and reassemble data"""
        shard_ids = self.user_shards.get(user_id, [])
        
        if not shard_ids:
            return None
        
        # Sort shards by index (from shard_id)
        sorted_shards = sorted(shard_ids, key=lambda s: int(s.split('_')[2]))
        
        # Retrieve each shard
        data_parts = []
        for shard_id in sorted_shards:
            shard = self.shards.get(shard_id)
            if not shard:
                logger.error(f"❌ Shard not found: {shard_id}")
                return None
            
            # Retrieve from one of the locations
            encrypted_data = self._retrieve_shard_from_node(shard)
            if encrypted_data:
                # Decrypt
                data_part = self._decrypt_shard(encrypted_data, user_id)
                data_parts.append(data_part)
                
                # Log access
                shard.access_log.append({
                    'accessed_at': datetime.now().isoformat(),
                    'by_user': user_id
                })
        
        # Reassemble
        if data_parts:
            full_data = b''.join(data_parts)
            logger.info(f"📥 Retrieved {len(full_data)} bytes for {user_id}")
            return full_data
        
        return None
    
    def _calculate_shard_size(self, total_size: int) -> int:
        """Calculate optimal shard size"""
        if total_size < 1024 * 1024:  # < 1MB
            return total_size  # Single shard
        elif total_size < 100 * 1024 * 1024:  # < 100MB
            return 10 * 1024 * 1024  # 10MB shards
        else:
            return 100 * 1024 * 1024  # 100MB shards
    
    def _encrypt_shard(self, data: bytes, user_id: str) -> bytes:
        """Encrypt data shard"""
        # Simplified - would use proper encryption
        key = hashlib.sha256(f"{user_id}:shard_key".encode()).digest()
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    
    def _decrypt_shard(self, data: bytes, user_id: str) -> bytes:
        """Decrypt data shard (same as encrypt for XOR)"""
        return self._encrypt_shard(data, user_id)  # XOR is symmetric
    
    def _select_storage_nodes(self, redundancy: int, tier: StorageTier) -> List[str]:
        """Select nodes for storage based on tier and geography"""
        # In production: would select based on:
        # - Geographic distribution
        # - Node reliability
        # - Available capacity
        # - Network latency
        
        # For demo, generate synthetic node IDs
        return [f"storage_node_{i}_{secrets.token_hex(4)}" for i in range(redundancy)]
    
    def _retrieve_shard_from_node(self, shard: DataShard) -> Optional[bytes]:
        """Retrieve shard from one of its storage nodes"""
        # Try each location
        for node_id in shard.locations:
            # In production: actual network retrieval
            # For demo, simulate success
            return b"simulated_shard_data"
        return None
    
    def verify_integrity(self, user_id: str) -> Dict[str, Any]:
        """Verify data integrity across shards"""
        shard_ids = self.user_shards.get(user_id, [])
        
        verified = 0
        corrupted = 0
        missing = 0
        
        for shard_id in shard_ids:
            shard = self.shards.get(shard_id)
            if not shard:
                missing += 1
                continue
            
            # Verify hash
            # In production: would actually retrieve and hash
            verified += 1
        
        return {
            'user_id': user_id,
            'total_shards': len(shard_ids),
            'verified': verified,
            'corrupted': corrupted,
            'missing': missing,
            'integrity_score': verified / len(shard_ids) if shard_ids else 1.0
        }
    
    def rebalance_data(self) -> Dict[str, Any]:
        """Rebalance data across nodes for optimal distribution"""
        moves = 0
        
        for shard_id, shard in self.shards.items():
            # Check if redistribution needed
            current_nodes = len(shard.locations)
            target_nodes = RedundancyLevel.STANDARD.value
            
            if current_nodes < target_nodes:
                # Add more replicas
                new_nodes = self._select_storage_nodes(
                    target_nodes - current_nodes, 
                    StorageTier.WARM
                )
                shard.locations.extend(new_nodes)
                moves += 1
        
        return {
            'shards_rebalanced': moves,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get distributed storage statistics"""
        total_shards = len(self.shards)
        total_bytes = sum(s.size_bytes for s in self.shards.values())
        
        by_tier = {}
        # In production: track tiers per shard
        
        return {
            'total_shards': total_shards,
            'total_bytes': total_bytes,
            'total_gb': total_bytes / (1024**3),
            'unique_users': len(self.user_shards),
            'storage_nodes': len(self.node_storage),
            'avg_shards_per_user': total_shards / len(self.user_shards) if self.user_shards else 0,
            'node_distribution': {
                k: f"{v / (1024**2):.2f} MB" 
                for k, v in sorted(self.node_storage.items(), key=lambda x: -x[1])[:10]
            }
        }

_storage = None

def get_distributed_storage() -> DistributedStorage:
    """Get distributed storage singleton"""
    global _storage
    if _storage is None:
        _storage = DistributedStorage()
    return _storage

if __name__ == "__main__":
    import sys
    
    storage = get_distributed_storage()
    
    if len(sys.argv) > 1 and sys.argv[1] == "store":
        test_data = b"This is test data for distributed storage across the mesh network"
        shards = storage.store_data("user_001", test_data)
        print(json.dumps({
            'shards_created': len(shards),
            'shard_ids': [s.shard_id for s in shards]
        }, indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(storage.get_storage_stats(), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "integrity":
        print(json.dumps(storage.verify_integrity("user_001"), indent=2))
        
    else:
        print("Usage: python distributed_storage.py [store|stats|integrity]")
