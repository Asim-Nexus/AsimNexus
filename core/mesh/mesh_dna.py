# core/mesh/mesh_dna.py
# AsimNexus — Mesh DNA: Node identity and trust scoring

import uuid
import time
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class MeshNode:
    """A node registered in the mesh DNA system."""
    node_id: str
    public_key: str
    trust_score: float = 0.5
    registered_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "public_key": self.public_key,
            "trust_score": self.trust_score,
            "registered_at": self.registered_at,
            "last_seen": self.last_seen,
            "metadata": self.metadata,
        }


class MeshDNA:
    """
    Mesh DNA — Manages node identities and trust scores in the mesh network.
    """

    def __init__(self):
        self._nodes: Dict[str, MeshNode] = {}
        self._lock = threading.Lock()

    def register_node(
        self,
        node_id: str,
        public_key: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MeshNode:
        """Register a new node in the mesh DNA system."""
        with self._lock:
            node = MeshNode(
                node_id=node_id,
                public_key=public_key,
                trust_score=0.5,
                metadata=metadata or {},
            )
            self._nodes[node_id] = node
            return node

    def get_node(self, node_id: str) -> Optional[MeshNode]:
        """Get a node by its ID."""
        with self._lock:
            return self._nodes.get(node_id)

    def update_trust_score(self, node_id: str, score: float) -> bool:
        """Update the trust score for a node."""
        with self._lock:
            if node_id not in self._nodes:
                return False
            self._nodes[node_id].trust_score = max(0.0, min(1.0, score))
            return True

    def list_nodes(self) -> Dict[str, MeshNode]:
        """List all registered nodes."""
        with self._lock:
            return dict(self._nodes)

    def get_stats(self) -> Dict[str, Any]:
        """Get mesh DNA statistics."""
        with self._lock:
            return {
                "total_nodes": len(self._nodes),
                "average_trust_score": (
                    sum(n.trust_score for n in self._nodes.values()) / len(self._nodes)
                    if self._nodes
                    else 0.0
                ),
            }


# Singleton pattern
_instance: Optional[MeshDNA] = None
_instance_lock = threading.Lock()


def get_mesh_dna() -> MeshDNA:
    """Get the singleton MeshDNA instance."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = MeshDNA()
    return _instance


def reset_mesh_dna() -> None:
    """Reset the singleton for testing."""
    global _instance
    with _instance_lock:
        _instance = None
