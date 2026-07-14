"""
AsimNexus Kademlia DHT Implementation
======================================
Distributed Hash Table for peer discovery, capability lookup,
and decentralized routing in the mesh network.
"""

import hashlib
import logging
import asyncio
import time
import random
from typing import Dict, List, Optional, Set, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("ASIM_DHT")

K = 20
ALPHA = 3
B = 160
REFRESH_INTERVAL = 3600
REPLICATE_INTERVAL = 3600
EXPIRE_TIME = 86400


class PeerStatus(Enum):
    """Status of a DHT peer."""
    UNKNOWN = "unknown"
    ALIVE = "alive"
    SUSPECT = "suspect"
    DEAD = "dead"


@dataclass
class DHTPeer:
    """A peer in the DHT network."""
    node_id: str
    address: str
    peer_id: str
    status: PeerStatus = PeerStatus.UNKNOWN
    last_seen: float = 0.0
    capabilities: Dict[str, Any] = field(default_factory=dict)
    distance: Optional[int] = None

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DHTPeer):
            return NotImplemented
        return self.node_id == other.node_id


@dataclass
class DHTNode:
    """A node in the DHT routing table."""
    peer: DHTPeer
    last_seen: float = 0.0
    failures: int = 0
    is_replacement: bool = False


class KBucket:
    """Kademlia k-bucket containing up to K nodes."""

    def __init__(self, range_start: int, range_end: int):
        self.range_start = range_start
        self.range_end = range_end
        self.nodes: List[DHTNode] = []
        self.replacement_cache: List[DHTNode] = []
        self.last_accessed: float = time.time()

    def has_room(self) -> bool:
        return len(self.nodes) < K

    def add_node(self, node: DHTNode) -> bool:
        for i, existing in enumerate(self.nodes):
            if existing.peer.node_id == node.peer.node_id:
                self.nodes.pop(i)
                self.nodes.append(node)
                self.last_accessed = time.time()
                return True
        if len(self.nodes) < K:
            self.nodes.append(node)
            self.last_accessed = time.time()
            return True
        self.replacement_cache.append(node)
        if len(self.replacement_cache) > K:
            self.replacement_cache.pop(0)
        return False

    def remove_node(self, node_id: str) -> bool:
        for i, existing in enumerate(self.nodes):
            if existing.peer.node_id == node_id:
                self.nodes.pop(i)
                if self.replacement_cache:
                    promoted = self.replacement_cache.pop(0)
                    promoted.is_replacement = False
                    self.nodes.append(promoted)
                return True
        return False

    def get_peers(self, count: int = K) -> List[DHTPeer]:
        alive = [n for n in self.nodes if n.peer.status == PeerStatus.ALIVE]
        random.shuffle(alive)
        return [n.peer for n in alive[:count]]

    def is_in_range(self, node_id: int) -> bool:
        return self.range_start <= node_id < self.range_end


class RoutingTable:
    """Kademlia routing table composed of k-buckets."""

    def __init__(self, local_node_id: str):
        self.local_id = int(local_node_id, 16)
        self.buckets: List[KBucket] = [KBucket(0, 2**B)]

    def _bucket_index(self, node_id: int) -> int:
        distance = self.local_id ^ node_id
        if distance == 0:
            return 0
        return distance.bit_length() - 1

    def add_peer(self, peer: DHTPeer) -> bool:
        node_id = int(peer.node_id, 16)
        idx = self._bucket_index(node_id)
        if idx >= len(self.buckets):
            idx = len(self.buckets) - 1
        dht_node = DHTNode(peer=peer, last_seen=time.time())
        return self.buckets[idx].add_node(dht_node)

    def find_closest(self, target_id: str, count: int = K) -> List[DHTPeer]:
        target = int(target_id, 16)
        idx = self._bucket_index(target)
        candidates: List[Tuple[int, DHTPeer]] = []
        checked = set()
        for offset in range(len(self.buckets)):
            bidx = idx + offset
            if bidx < len(self.buckets) and bidx not in checked:
                checked.add(bidx)
                for n in self.buckets[bidx].nodes:
                    dist = target ^ int(n.peer.node_id, 16)
                    candidates.append((dist, n.peer))
            bidx = idx - offset
            if bidx >= 0 and bidx not in checked:
                checked.add(bidx)
                for n in self.buckets[bidx].nodes:
                    dist = target ^ int(n.peer.node_id, 16)
                    candidates.append((dist, n.peer))
        candidates.sort(key=lambda x: x[0])
        return [p for _, p in candidates[:count]]

    def get_all_peers(self) -> List[DHTPeer]:
        peers = []
        for bucket in self.buckets:
            for node in bucket.nodes:
                peers.append(node.peer)
        return peers


class KademliaDHT:
    """Kademlia Distributed Hash Table implementation."""

    def __init__(self, local_peer_id: str, local_address: str = "0.0.0.0:0"):
        self.local_id = hashlib.sha1(local_peer_id.encode()).hexdigest()
        self.local_peer = DHTPeer(
            node_id=self.local_id,
            address=local_address,
            peer_id=local_peer_id,
            status=PeerStatus.ALIVE,
            last_seen=time.time(),
        )
        self.routing_table = RoutingTable(self.local_id)
        self.routing_table.add_peer(self.local_peer)
        self.store: Dict[str, Tuple[bytes, float]] = {}
        self._running = False
        self._refresh_task: Optional[asyncio.Task] = None

    async def bootstrap(self, bootstrap_peers: List[str]) -> int:
        connected = 0
        for addr in bootstrap_peers:
            peer = DHTPeer(
                node_id=hashlib.sha1(addr.encode()).hexdigest(),
                address=addr,
                peer_id=addr,
                status=PeerStatus.ALIVE,
                last_seen=time.time(),
            )
            self.routing_table.add_peer(peer)
            connected += 1
        logger.info(f"DHT bootstrapped with {connected} peers")
        return connected

    async def find_node(self, target_id: str) -> List[DHTPeer]:
        return self.routing_table.find_closest(target_id, K)

    async def find_value(self, key: str) -> Optional[bytes]:
        if key in self.store:
            value, expiry = self.store[key]
            if time.time() < expiry:
                return value
            else:
                del self.store[key]
        return None

    async def store_value(self, key: str, value: bytes, ttl: int = EXPIRE_TIME) -> bool:
        self.store[key] = (value, time.time() + ttl)
        return True

    async def start(self):
        self._running = True
        logger.info(f"DHT started (node_id={self.local_id[:16]}...)")

    async def stop(self):
        self._running = False
        if self._refresh_task:
            self._refresh_task.cancel()
        logger.info("DHT stopped")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "node_id": self.local_id[:16] + "...",
            "peers": len(self.routing_table.get_all_peers()),
            "buckets": len(self.routing_table.buckets),
            "stored_keys": len(self.store),
            "status": "running" if self._running else "stopped",
        }


_dht_instance: Optional[KademliaDHT] = None


def get_dht() -> KademliaDHT:
    """Get the global DHT singleton."""
    global _dht_instance
    if _dht_instance is None:
        _dht_instance = KademliaDHT("local")
    return _dht_instance