"""
AsimNexus — Global Mesh Network
================================
Global distributed mesh network with edge node management, bootstrap nodes,
and optimal route calculation.
"""

import uuid
import math
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class Region(Enum):
    ASIA = "asia"
    NORTH_AMERICA = "north_america"
    SOUTH_AMERICA = "south_america"
    EUROPE = "europe"
    AFRICA = "africa"
    OCEANIA = "oceania"
    ANTARCTICA = "antarctica"


@dataclass
class BootstrapNode:
    """A bootstrap node that helps peers join the network."""
    node_id: str
    host: str
    port: int
    region: Region
    is_online: bool = True
    max_peers: int = 1000
    current_peers: int = 0


@dataclass
class EdgeNode:
    """An edge node providing compute resources to the network."""
    node_id: str
    region: Region
    location: Tuple[float, float]
    compute_capacity: float
    memory_gb: float
    gpu_available: bool = False
    is_online: bool = True
    current_load: float = 0.0


@dataclass
class MeshRoute:
    """A calculated route through the mesh network."""
    route_id: str
    path: List[str]
    latency_ms: float
    hops: int = 0


class GlobalMeshNetwork:
    """Global mesh network managing bootstrap nodes and edge nodes."""

    def __init__(self):
        self._lock = threading.Lock()
        self._bootstrap_nodes: Dict[str, BootstrapNode] = {}
        self._edge_nodes: Dict[str, EdgeNode] = {}
        self._init_default_bootstrap_nodes()

    def _init_default_bootstrap_nodes(self) -> None:
        """Initialize default bootstrap nodes across regions."""
        defaults = [
            ("bootstrap_asia_1", "asia1.asimnexus.io", 8080, Region.ASIA),
            ("bootstrap_asia_2", "asia2.asimnexus.io", 8080, Region.ASIA),
            ("bootstrap_na_1", "na1.asimnexus.io", 8080, Region.NORTH_AMERICA),
            ("bootstrap_na_2", "na2.asimnexus.io", 8080, Region.NORTH_AMERICA),
            ("bootstrap_eu_1", "eu1.asimnexus.io", 8080, Region.EUROPE),
            ("bootstrap_eu_2", "eu2.asimnexus.io", 8080, Region.EUROPE),
            ("bootstrap_sa_1", "sa1.asimnexus.io", 8080, Region.SOUTH_AMERICA),
            ("bootstrap_af_1", "af1.asimnexus.io", 8080, Region.AFRICA),
            ("bootstrap_oc_1", "oc1.asimnexus.io", 8080, Region.OCEANIA),
        ]
        for node_id, host, port, region in defaults:
            self._bootstrap_nodes[node_id] = BootstrapNode(
                node_id=node_id,
                host=host,
                port=port,
                region=region
            )

    def add_edge_node(
        self,
        region: Region,
        location: Tuple[float, float],
        compute_capacity: float,
        memory_gb: float,
        gpu_available: bool = False
    ) -> str:
        """Add an edge node to the network."""
        node_id = f"edge_{uuid.uuid4().hex[:8]}"
        with self._lock:
            self._edge_nodes[node_id] = EdgeNode(
                node_id=node_id,
                region=region,
                location=location,
                compute_capacity=compute_capacity,
                memory_gb=memory_gb,
                gpu_available=gpu_available
            )
        return node_id

    def find_optimal_edge_node(
        self,
        required_compute: float,
        required_memory: float,
        required_gpu: bool = False,
        region: Optional[Region] = None
    ) -> Optional[EdgeNode]:
        """Find the optimal edge node for given requirements."""
        candidates = []
        with self._lock:
            for node in self._edge_nodes.values():
                if not node.is_online:
                    continue
                if region and node.region != region:
                    continue
                if node.compute_capacity < required_compute:
                    continue
                if node.memory_gb < required_memory:
                    continue
                if required_gpu and not node.gpu_available:
                    continue
                candidates.append(node)

        if not candidates:
            return None

        # Return the node with lowest current load
        return min(candidates, key=lambda n: n.current_load)

    def get_nearest_bootstrap_node(
        self,
        location: Tuple[float, float],
        max_distance_km: float = 5000
    ) -> Optional[BootstrapNode]:
        """Find the nearest bootstrap node to a location."""
        nearest = None
        min_distance = float("inf")

        with self._lock:
            for node in self._bootstrap_nodes.values():
                if not node.is_online:
                    continue
                # Approximate distance based on region centroids
                dist = self._estimate_distance(location, node.region)
                if dist < min_distance and dist <= max_distance_km:
                    min_distance = dist
                    nearest = node

        return nearest

    def calculate_mesh_route(
        self,
        source_id: str,
        target_id: str
    ) -> Optional[MeshRoute]:
        """Calculate a route between two nodes in the mesh."""
        # Simple direct route calculation
        route_id = f"route_{uuid.uuid4().hex[:8]}"
        path = [source_id, target_id]
        return MeshRoute(
            route_id=route_id,
            path=path,
            latency_ms=50.0,  # Estimated latency
            hops=1
        )

    async def health_check_all_nodes(self) -> Dict[str, Any]:
        """Perform health check on all nodes."""
        online_bootstrap = sum(1 for n in self._bootstrap_nodes.values() if n.is_online)
        online_edge = sum(1 for n in self._edge_nodes.values() if n.is_online)
        return {
            "bootstrap_online": online_bootstrap,
            "bootstrap_total": len(self._bootstrap_nodes),
            "edge_online": online_edge,
            "edge_total": len(self._edge_nodes)
        }

    def get_network_status(self) -> Dict[str, Any]:
        """Get comprehensive network status."""
        with self._lock:
            by_region: Dict[str, int] = {}
            for node in self._bootstrap_nodes.values():
                r = node.region.value
                by_region[r] = by_region.get(r, 0) + 1

            total_capacity = sum(n.max_peers for n in self._bootstrap_nodes.values())
            online_bootstrap = sum(1 for n in self._bootstrap_nodes.values() if n.is_online)
            online_edge = sum(1 for n in self._edge_nodes.values() if n.is_online)

            total_edge_compute = sum(n.compute_capacity for n in self._edge_nodes.values())
            used_edge_compute = sum(n.current_load for n in self._edge_nodes.values())
            utilization = (used_edge_compute / total_edge_compute * 100) if total_edge_compute > 0 else 0

            return {
                "bootstrap_nodes": {
                    "total": len(self._bootstrap_nodes),
                    "online": online_bootstrap,
                    "total_capacity": total_capacity,
                    "by_region": by_region
                },
                "edge_nodes": {
                    "total": len(self._edge_nodes),
                    "online": online_edge,
                    "utilization_percent": round(utilization, 1)
                }
            }

    @staticmethod
    def _estimate_distance(location: Tuple[float, float], region: Region) -> float:
        """Estimate distance from a location to a region's centroid."""
        centroids = {
            Region.ASIA: (34.0, 100.0),
            Region.NORTH_AMERICA: (40.0, -100.0),
            Region.SOUTH_AMERICA: (-15.0, -60.0),
            Region.EUROPE: (50.0, 10.0),
            Region.AFRICA: (0.0, 20.0),
            Region.OCEANIA: (-25.0, 135.0),
            Region.ANTARCTICA: (-82.0, 0.0),
        }
        centroid = centroids.get(region, (0.0, 0.0))
        # Haversine approximation
        lat1, lon1 = map(math.radians, location)
        lat2, lon2 = map(math.radians, centroid)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c  # Earth radius in km


# Singleton
_global_mesh: Optional[GlobalMeshNetwork] = None
_global_mesh_lock = threading.Lock()


def get_global_mesh_network() -> GlobalMeshNetwork:
    """Get or create the global mesh network singleton."""
    global _global_mesh
    if _global_mesh is None:
        with _global_mesh_lock:
            if _global_mesh is None:
                _global_mesh = GlobalMeshNetwork()
    return _global_mesh


def reset_global_mesh_network() -> None:
    """Reset the singleton (for testing)."""
    global _global_mesh
    with _global_mesh_lock:
        _global_mesh = None
