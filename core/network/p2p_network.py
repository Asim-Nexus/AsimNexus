"""
ASIMNEXUS P2P Network
=====================
P2P networking with DHT, mesh routing, and peer discovery.
"""

import uuid
import json
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


class PeerState(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UNREACHABLE = "unreachable"


@dataclass
class Peer:
    id: str
    address: Tuple[str, int]
    state: PeerState = PeerState.DISCONNECTED

    def distance_to(self, other_id: str) -> int:
        """Calculate XOR distance between peer IDs."""
        self_int = int(self.id, 16)
        other_int = int(other_id, 16)
        return self_int ^ other_int


@dataclass
class NetworkMessage:
    id: str
    from_peer: str
    to_peer: str
    message_type: str
    payload: Dict[str, Any]
    ttl: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_peer": self.from_peer,
            "to_peer": self.to_peer,
            "message_type": self.message_type,
            "payload": self.payload,
            "ttl": self.ttl,
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
            payload=data.get("payload", {}),
            ttl=data.get("ttl", 10),
        )


class DHTNode:
    """Distributed Hash Table node with k-bucket routing."""

    def __init__(self, k: int = 20):
        self.node_id = hashlib.sha1(uuid.uuid4().bytes).hexdigest()
        self.k = k
        self.peers: Dict[str, Peer] = {}
        self._store: Dict[str, Any] = {}

    def add_peer(self, peer: Peer) -> None:
        self.peers[peer.id] = peer

    def find_closest_peers(self, target_id: str, count: int = 5) -> List[Peer]:
        """Find closest peers to target ID using XOR distance."""
        target_int = int(target_id, 16)
        sorted_peers = sorted(
            self.peers.values(),
            key=lambda p: int(p.id, 16) ^ target_int,
        )
        return sorted_peers[:count]

    def store(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def remove(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False


class MeshRouter:
    """Mesh network router for peer-to-peer message routing."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.peers: Dict[str, Peer] = {}

    def add_peer(self, peer: Peer) -> None:
        self.peers[peer.id] = peer

    def remove_peer(self, peer_id: str) -> bool:
        if peer_id in self.peers:
            del self.peers[peer_id]
            return True
        return False

    def route_message(self, message: NetworkMessage) -> Optional[str]:
        """Route a message to its destination peer."""
        if message.to_peer in self.peers:
            return message.to_peer
        return None

    def broadcast(self, message: NetworkMessage) -> List[str]:
        """Broadcast message to all connected peers."""
        return list(self.peers.keys())


class P2PNetwork:
    """Main P2P network orchestrator combining DHT and mesh routing."""

    def __init__(self, host: str = "127.0.0.1", port: int = 6881):
        self.node_id = hashlib.sha1(uuid.uuid4().bytes).hexdigest()
        self.host = host
        self.port = port
        self.dht = DHTNode()
        self.mesh = MeshRouter(self.node_id)

    def dht_store(self, key: str, value: Any) -> None:
        self.dht.store(key, value)

    def dht_get(self, key: str) -> Optional[Any]:
        return self.dht.get(key)

    def get_peers(self) -> List[Peer]:
        return list(self.dht.peers.values())

    def get_status(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "peers": len(self.dht.peers),
        }
