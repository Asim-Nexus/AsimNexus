---
import_attempts:
  - module: "security.power_balance_constitution"
    names: ["SectorControl", "BalanceVerdict", "BalanceResult", "SectorBalance", "AmendmentProposal", "PowerBalanceConstitution", "SECTOR_BALANCE_MAP", "DEFAULT_PUBLIC_THRESHOLD", "DEFAULT_PRIVATE_THRESHOLD", "AMENDMENT_SUPERMAJORITY", "get_power_balance", "reset_power_balance"]
  - module: "core.life_journey"
    names: ["LifeStage", "TransitionStatus", "LifeStageTransition", "TransitionRecord", "LifeProfile", "LifeJourneyModule", "LIFE_JOURNEY_MACHINE", "get_life_journey_module", "reset_life_journey_module"]
  - module: "mesh.p2p_transport"
    names: ["P2PTransport", "P2PMessage", "PeerInfo", "RPCMessageType", "WSMessageType"]
  - module: "mesh.kademlia_dht"
    names: ["KademliaDHT", "NodeID", "DHTNode", "ID_LENGTH"]
  - module: "mesh.crdt_sync"
    names: ["CRDTStore"]
  - module: "mesh.p2p_integration"
    names: ["create_local_node_set", "LocalNode"]
  - module: "mesh.autodiscovery"
    names: ["AutoDiscovery", "NodeInfo", "reset_auto_discovery"]
  - module: "mesh.node_registry"
    names: ["NodeRegistry", "TrustLevel", "NodeStatus", "reset_node_registry"]
  - module: "mesh.relay"
    names: ["RelayService", "RelayRole", "reset_relay_service"]
  - module: "mesh.bootstrap"
    names: ["BootstrapService", "BootstrapNode", "BootstrapRegion", "reset_bootstrap_service"]
---
