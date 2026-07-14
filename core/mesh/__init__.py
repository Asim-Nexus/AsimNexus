# AsimNexus Mesh Layer
# ====================
# Offline-first P2P mesh network with CRDT sync
# Consolidated hub — re-exports from both legacy mesh/ and core/mesh/ modules

# --- Legacy mesh/ modules (copied from root mesh/) ---
from .offline_sync_engine import OfflineSyncEngine, SyncPriority, SyncOperationStatus
from .crdt_sync import CRDTStore, LWWRegister, GCounter, PNCounter
from .mesh_node import MeshNode
from .p2p_transport import P2PTransport
from .node_registry import NodeRegistry
from .multi_mesh_router import MultiMeshRouter
from .autodiscovery import AutoDiscovery
from .bootstrap import BootstrapService
from .device_registry import DeviceRegistry
from .hole_punching import HolePuncher
from .kademlia_dht import KademliaDHT
from .mesh_routing_agent_v2 import MeshRoutingAgentV2
from .multi_hop_router import MultiHopRouter
from .nat_traversal import NATTraversal
from .network_intelligence import NetworkIntelligenceLayer
from .p2p_integration import P2PIntegration
from .relay import RelayService
from .sms_gateway import SMSGateway
from .stun_turn import STUNClient, NATDetector, TURNClient, NATClassification

# --- Native core/mesh/ concept modules (all imports now resolved) ---
from .mesh_coordinator import MeshCoordinator, NodeType, NodeTier, ConnectionState, get_mesh_coordinator
from .federation_protocol import FederationProtocol, get_mesh_federation
from .gossip_protocol import GossipProtocol, GossipMessage
from .mesh_dna import MeshDNA, MeshNode as DNAMeshNode
from .unified_mesh import UnifiedMeshCoordinator, MeshLayer, MeshPeer

class P2PNetwork:
    pass

class OfflineSync:
    pass


# Re-export from root-level module: global_mesh.py
from core.global_mesh import (
    BootstrapNode,
    EdgeNode,
    GlobalMeshNetwork,
    MeshRoute,
    Region,
    get_global_mesh_network,
    reset_global_mesh_network,
)


__all__ = [
    # Legacy mesh/
    "OfflineSyncEngine", "SyncPriority", "SyncOperationStatus",
    "CRDTStore", "LWWRegister", "GCounter", "PNCounter",
    "MeshNode", "P2PTransport", "NodeRegistry", "MultiMeshRouter",
    "AutoDiscovery", "BootstrapService", "DeviceRegistry", "HolePuncher",
    "KademliaDHT", "MeshRoutingAgentV2", "MultiHopRouter", "NATTraversal",
    "NetworkIntelligenceLayer", "P2PIntegration", "RelayService", "SMSGateway",
    "STUNClient", "NATDetector", "TURNClient", "NATClassification",
    # Native core/mesh/ concept modules
    "MeshCoordinator", "NodeType", "NodeTier", "ConnectionState", "get_mesh_coordinator",
    "FederationProtocol", "GossipProtocol", "GossipMessage",
    "MeshDNA", "DNAMeshNode",
    "UnifiedMeshCoordinator", "MeshLayer", "MeshPeer",
    # Placeholders
    "P2PNetwork", "OfflineSync",
]
