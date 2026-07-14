"""
P2P Network Module
==================
Peer-to-peer networking with DHT, mesh routing, and message passing.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class PeerState(Enum):
    """State of a peer in the network."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    KNOWN = "known"


@dataclass
class Peer:
    """A peer in the P2P network."""
    id: str
    address: Tuple[str, int]
    state: PeerState = PeerState.KNOWN

    @property
    def peer_id(self) -> str:
        return self.id

    @property
    def host(self) -> str:
        return self.address[0]

    @property
    def port(self) -> int:
        return self.address[1]

    def distance_to(self, other_id: str) -> int:
        """Calculate XOR distance to another peer ID."""
        self_int = int(self.id, 16) if self.id else 0
        other_int = int(other_id, 16) if other_id else 0
        return self_int ^ other_int


@dataclass
class NetworkMessage:
    """A message in the P2P network."""
    id: str
    from_peer: str
    to_peer: str
    message_type: str
    payload: Dict[str, Any]
    ttl: int = 10
    timestamp: float = 0.0

    @property
    def message_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_peer": self.from_peer,
            "to_peer": self.to_peer,
            "message_type": self.message_type,
            "payload": self.payload,
            "ttl": self.ttl,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "NetworkMessage":
        data = json.loads(json_str)
        return cls(
            id=data["id"],
            from_peer=data["from_peer"],
            to_peer=data["to_peer"],
            message_type=data["message_type"],
            payload=data["payload"],
            ttl=data.get("ttl", 10),
            timestamp=data.get("timestamp", 0.0),
        )


class DHTNode:
    """Distributed Hash Table node for peer discovery."""

    def __init__(self, node_id: Optional[str] = None, k: int = 20):
        if node_id:
            self.node_id = node_id
        else:
            self.node_id = hashlib.sha1(str(id(self)).encode()).hexdigest()
        self.k = k
        self._lock = threading.Lock()
        self._peers: Dict[str, Peer] = {}
        self._store: Dict[str, Any] = {}

    def store(self, key: str, value: Any) -> bool:
        """Store a key-value pair."""
        with self._lock:
            self._store[key] = value
            return True

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        with self._lock:
            return self._store.get(key)

    def retrieve(self, key: str) -> Optional[Any]:
        """Alias for get()."""
        return self.get(key)

    def remove(self, key: str) -> bool:
        """Remove a key-value pair."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def add_peer(self, peer: Peer) -> None:
        """Add a peer to the routing table."""
        with self._lock:
            self._peers[peer.id] = peer

    def remove_peer(self, peer_id: str) -> None:
        """Remove a peer from the routing table."""
        with self._lock:
            self._peers.pop(peer_id, None)

    def find_peer(self, peer_id: str) -> Optional[Peer]:
        """Find a peer by ID."""
        with self._lock:
            return self._peers.get(peer_id)

    def find_closest_peers(self, target_id: str, count: int = 5) -> List[Peer]:
        """Find the closest peers to a target ID."""
        with self._lock:
            if not self._peers:
                return []
            sorted_peers = sorted(
                self._peers.values(),
                key=lambda p: p.distance_to(target_id),
            )
            return sorted_peers[:count]

    def get_closest_peers(self, target_id: str, count: int = 5) -> List[Peer]:
        """Alias for find_closest_peers."""
        return self.find_closest_peers(target_id, count)

    def get_all_peers(self) -> List[Peer]:
        """Get all known peers."""
        with self._lock:
            return list(self._peers.values())


class MeshRouter:
    """Mesh network router for peer management and message routing."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._lock = threading.Lock()
        self.peers: Dict[str, Peer] = {}

    def add_peer(self, peer: Peer) -> None:
        """Add a peer to the mesh."""
        with self._lock:
            self.peers[peer.id] = peer

    def remove_peer(self, peer_id: str) -> bool:
        """Remove a peer from the mesh."""
        with self._lock:
            if peer_id in self.peers:
                del self.peers[peer_id]
                return True
            return False

    def route_message(self, message: NetworkMessage) -> Optional[str]:
        """Route a message to its destination peer.
        
        Returns the destination peer ID if found, None otherwise.
        """
        with self._lock:
            if message.to_peer in self.peers:
                return message.to_peer
            return None

    def broadcast(self, message: NetworkMessage) -> List[str]:
        """Broadcast a message to all connected peers.
        
        Returns list of recipient peer IDs.
        """
        with self._lock:
            recipients = list(self.peers.keys())
            return recipients

    def add_route(self, destination: str, path: List[str]) -> None:
        """Legacy: add a route (stub for backward compatibility)."""
        pass

    def remove_route(self, destination: str) -> None:
        """Legacy: remove a route (stub for backward compatibility)."""
        pass

    def find_route(self, destination: str) -> Optional[List[str]]:
        """Legacy: find a route (stub for backward compatibility)."""
        with self._lock:
            if destination in self.peers:
                return [destination]
            return None

    def get_all_routes(self) -> Dict[str, List[str]]:
        """Legacy: get all routes (stub for backward compatibility)."""
        with self._lock:
            return {pid: [pid] for pid in self.peers}


class P2PNetwork:
    """Main P2P network manager."""

    def __init__(self, node_id: Optional[str] = None, host: str = "127.0.0.1", port: int = 6881):
        self.node_id = node_id or hashlib.sha1(str(id(self)).encode()).hexdigest()
        self.host = host
        self.port = port
        self._lock = threading.Lock()
        self.dht = DHTNode(node_id=self.node_id)
        self.mesh = MeshRouter(self.node_id)
        self._messages: Dict[str, NetworkMessage] = {}

    def dht_store(self, key: str, value: Any) -> bool:
        """Store a value in the DHT."""
        return self.dht.store(key, value)

    def dht_get(self, key: str) -> Optional[Any]:
        """Get a value from the DHT."""
        return self.dht.get(key)

    def bootstrap(self, seed_peers: List[Peer]) -> None:
        """Bootstrap the network with seed peers."""
        for peer in seed_peers:
            self.dht.add_peer(peer)
            self.mesh.add_peer(peer)

    def send_message(self, message: NetworkMessage) -> bool:
        """Send a message through the network."""
        with self._lock:
            self._messages[message.id] = message
            return True

    def receive_message(self, message_id: str) -> Optional[NetworkMessage]:
        """Receive a message by ID."""
        with self._lock:
            return self._messages.get(message_id)

    def broadcast(self, content: str, sender_id: str) -> List[str]:
        """Broadcast a message to all peers."""
        message = NetworkMessage(
            id=f"broadcast_{id(self)}",
            from_peer=sender_id,
            to_peer="*",
            message_type="broadcast",
            payload={"content": content},
        )
        with self._lock:
            self._messages[message.id] = message
            return self.mesh.broadcast(message)

    def get_peers(self) -> List[Peer]:
        """Get all known peers."""
        return self.dht.get_all_peers()

    def get_status(self) -> Dict[str, Any]:
        """Get network status."""
        with self._lock:
            return {
                "node_id": self.node_id,
                "peers": len(self.mesh.peers),
                "dht_peers": len(self.dht.get_all_peers()),
                "messages": len(self._messages),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get network statistics (alias for get_status)."""
        return self.get_status()


def calculate_peer_distance(peer1: Peer, peer2: Peer) -> float:
    """Calculate the distance between two peers."""
    return float(peer1.distance_to(peer2.id))
