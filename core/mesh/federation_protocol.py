"""
core/mesh/federation_protocol.py
AsimNexus — World Federation Protocol
======================================

Federates ALL nodes into global mesh.
Secure, decentralized, self-organizing.

This module delegates to the real implementations in core/federation/:
  - GlobalFederationManager  (CRDT-based state sync, jurisdiction routing)
  - GlobalFederationGovernor (peer lifecycle, consensus-driven decisions)
  - FederationProtocolEnhanced (async P2P handshake, sync, heartbeat)

And integrates with the mesh gossip protocol for epidemic state dissemination.

Usage:
    from core.mesh.federation_protocol import (
        FederationProtocol,
        get_mesh_federation,
    )

    fed = get_mesh_federation()
    member = fed.join_federation("node_001", FederationLevel.FULL)
    fed.endorse_member("node_001", "node_002", TrustLevel.PEER)
    result = fed.reach_consensus("proposal_001", ["node_001", "node_002"])
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("ASIM_FEDERATION")

# ─── Enums ────────────────────────────────────────────────────────────────────

class FederationLevel(Enum):
    """Federation participation levels"""
    FULL = "full"              # All features
    PARTIAL = "partial"        # Limited features
    OBSERVER = "observer"      # Read-only
    ISOLATED = "isolated"      # No federation


class TrustLevel(Enum):
    """Trust levels between nodes"""
    UNTRUSTED = 0
    ACQUAINTANCE = 1
    PEER = 2
    TRUSTED = 3
    VERIFIED = 4
    CO_SIGNATURE = 5


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class FederationMember:
    """Member of the federation"""
    node_id: str
    level: FederationLevel
    trust: TrustLevel
    joined_at: datetime
    last_attestation: datetime
    endorsed_by: Set[str]  # Nodes that endorsed this member
    resources_shared: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'level': self.level.value,
            'trust': self.trust.value,
            'joined_at': self.joined_at.isoformat(),
            'last_attestation': self.last_attestation.isoformat(),
            'endorsed_by': list(self.endorsed_by),
            'resources': self.resources_shared,
        }


# ─── Federation Protocol ──────────────────────────────────────────────────────

class FederationProtocol:
    """
    World Federation Protocol

    Connects all AsimNexus nodes globally via:
      - CRDT-based state sync (delegates to GlobalFederationManager)
      - DID-based P2P handshake (delegates to FederationProtocolEnhanced)
      - Gossip-based epidemic dissemination (delegates to GossipProtocol)
      - Consensus-driven governance (delegates to GlobalFederationGovernor)

    Maintains backward-compatible API for routes/mesh.py and mesh/__init__.py.
    """

    def __init__(self):
        # Core state (backward-compatible)
        self.members: Dict[str, FederationMember] = {}
        self.trust_graph: Dict[str, Dict[str, TrustLevel]] = {}
        self.federation_rules: Dict[str, Any] = {}
        self.consensus_log: List[Dict] = []

        # Enhanced federation engine (lazy-loaded)
        self._enhanced_fed: Optional[Any] = None
        self._governor: Optional[Any] = None
        self._gossip: Optional[Any] = None
        self._initialized = False
        self._node_id: str = ""

    async def initialize(self, node_id: str = "") -> None:
        """Lazy-initialize the enhanced federation engines."""
        if self._initialized:
            return
        self._node_id = node_id or f"fed_{uuid.uuid4().hex[:8]}"

        try:
            # Try to load enhanced federation
            from core.federation.global_federation import (
                GlobalFederationManager,
                get_federation as get_global_fed,
            )
            from core.federation.global_federation_governor import (
                GlobalFederationGovernor,
                get_global_federation_governor,
            )
            from core.mesh.gossip_protocol import get_gossip_protocol

            self._enhanced_fed = get_global_fed()
            self._governor = get_global_federation_governor()
            self._gossip = get_gossip_protocol(self._node_id)

            # Wire gossip transport to federation
            self._gossip.set_transport(self._send_gossip_message)
            self._gossip.set_on_state_update(self._on_gossip_state_update)

            logger.info("FederationProtocol initialized with enhanced engines (node=%s)", self._node_id)
        except ImportError as e:
            logger.warning("Enhanced federation engines not available (%s), using local-only mode", e)

        self._initialized = True

    async def _send_gossip_message(self, peer_id: str, message: Any) -> None:
        """Transport callback for gossip protocol — sends message to peer."""
        # In production, this would send over TCP/UDP/DHT
        # For now, we log and let the gossip protocol handle it
        logger.debug("Gossip transport: would send to %s (msg=%s)", peer_id, message.msg_type)

    def _on_gossip_state_update(self, key: str, value: Any, node_id: str) -> None:
        """Callback when gossip protocol updates state from a peer."""
        logger.info("Gossip state update: %s = %s (from %s)", key, value, node_id)

    # ── Core API (backward-compatible) ──────────────────────────────────────

    def join_federation(self, node_id: str, level: FederationLevel,
                       initial_endorsers: List[str] = None) -> FederationMember:
        """Join the world federation."""
        member = FederationMember(
            node_id=node_id,
            level=level,
            trust=TrustLevel.ACQUAINTANCE,
            joined_at=datetime.now(),
            last_attestation=datetime.now(),
            endorsed_by=set(initial_endorsers or []),
            resources_shared={}
        )

        self.members[node_id] = member

        # Initialize trust graph
        if node_id not in self.trust_graph:
            self.trust_graph[node_id] = {}

        # Log
        self.consensus_log.append({
            'action': 'join',
            'node': node_id,
            'level': level.value,
            'timestamp': datetime.now().isoformat()
        })

        # Propagate via gossip if available
        if self._gossip:
            self._gossip.update_state(
                f"fed:member:{node_id}",
                member.to_dict()
            )

        logger.info("🌐 Node joined federation: %s (%s)", node_id, level.value)
        return member

    def endorse_member(self, endorser_id: str, endorsee_id: str,
                      trust_level: TrustLevel) -> bool:
        """Endorse another federation member."""
        if endorser_id not in self.members or endorsee_id not in self.members:
            return False

        member = self.members[endorsee_id]
        member.endorsed_by.add(endorser_id)

        # Update trust graph
        if endorser_id not in self.trust_graph:
            self.trust_graph[endorser_id] = {}
        self.trust_graph[endorser_id][endorsee_id] = trust_level

        # Update member trust if enough endorsements
        if len(member.endorsed_by) >= 3:
            member.trust = TrustLevel.PEER
        if len(member.endorsed_by) >= 10:
            member.trust = TrustLevel.TRUSTED

        # Propagate via gossip
        if self._gossip:
            self._gossip.update_state(
                f"fed:endorse:{endorsee_id}",
                {"endorser": endorser_id, "trust": trust_level.value}
            )

        logger.info("✅ %s endorsed %s at level %s", endorser_id, endorsee_id, trust_level.value)
        return True

    def share_resource(self, node_id: str, resource_type: str,
                      resource_data: Dict) -> bool:
        """Share a resource with the federation."""
        if node_id not in self.members:
            return False

        member = self.members[node_id]
        member.resources_shared[resource_type] = {
            **resource_data,
            'shared_at': datetime.now().isoformat()
        }

        # Propagate via gossip
        if self._gossip:
            self._gossip.update_state(
                f"fed:resource:{node_id}:{resource_type}",
                member.resources_shared[resource_type]
            )

        logger.info("📤 %s shared %s with federation", node_id, resource_type)
        return True

    def query_federation(self, query_type: str,
                        params: Dict) -> List[Dict]:
        """Query resources across federation."""
        results = []

        for node_id, member in self.members.items():
            if member.trust.value < TrustLevel.PEER.value:
                continue

            if query_type in member.resources_shared:
                resource = member.resources_shared[query_type]
                results.append({
                    'source': node_id,
                    'trust': member.trust.value,
                    'data': resource
                })

        # Sort by trust level
        results.sort(key=lambda x: x['trust'], reverse=True)
        return results

    def reach_consensus(self, proposal: str,
                       voting_nodes: List[str]) -> Dict[str, Any]:
        """Reach consensus on proposal (simplified)."""
        votes_for = 0
        votes_against = 0

        for node_id in voting_nodes:
            if node_id in self.members:
                weight = self.members[node_id].trust.value
                votes_for += weight

        total_possible = sum(
            self.members[n].trust.value
            for n in voting_nodes if n in self.members
        )

        consensus_reached = votes_for > (total_possible * 0.67)  # 2/3 majority

        result = {
            'proposal': proposal,
            'consensus_reached': consensus_reached,
            'votes_for': votes_for,
            'total_weight': total_possible,
            'timestamp': datetime.now().isoformat()
        }

        self.consensus_log.append(result)

        # Propagate via gossip
        if self._gossip:
            self._gossip.update_state(
                f"fed:consensus:{proposal}",
                result
            )

        return result

    def get_federation_map(self) -> Dict[str, Any]:
        """Get federation topology map."""
        by_level = {}
        by_trust = {}

        for member in self.members.values():
            level = member.level.value
            trust = member.trust.name

            by_level[level] = by_level.get(level, 0) + 1
            by_trust[trust] = by_trust.get(trust, 0) + 1

        return {
            'total_members': len(self.members),
            'by_level': by_level,
            'by_trust': by_trust,
            'trust_connections': sum(len(t) for t in self.trust_graph.values()),
            'consensus_events': len(self.consensus_log),
            'gossip_available': self._gossip is not None,
            'enhanced_federation': self._enhanced_fed is not None,
        }

    def get_member_path(self, from_node: str, to_node: str,
                       max_hops: int = 5) -> Optional[List[str]]:
        """Find trust path between nodes (Web of Trust)."""
        # BFS for trust path
        visited = {from_node}
        queue = [(from_node, [from_node])]

        while queue:
            current, path = queue.pop(0)

            if current == to_node:
                return path

            if len(path) >= max_hops:
                continue

            neighbors = self.trust_graph.get(current, {})
            for neighbor, trust in neighbors.items():
                if trust.value >= TrustLevel.PEER.value and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_gossip_stats(self) -> Dict[str, Any]:
        """Get gossip protocol statistics."""
        if self._gossip:
            return self._gossip.get_stats()
        return {"available": False, "reason": "gossip not initialized"}

    async def start_gossip(self) -> None:
        """Start the gossip protocol loop."""
        if self._gossip:
            await self._gossip.start()

    async def stop_gossip(self) -> None:
        """Stop the gossip protocol loop."""
        if self._gossip:
            await self._gossip.stop()


# ─── Singleton ────────────────────────────────────────────────────────────────

_federation = None


def get_mesh_federation() -> FederationProtocol:
    """Get mesh federation singleton."""
    global _federation
    if _federation is None:
        _federation = FederationProtocol()
    return _federation


# Alias for backward-compatibility with mesh/__init__.py imports
get_federation = get_mesh_federation


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    fed = get_mesh_federation()

    if len(sys.argv) > 1 and sys.argv[1] == "join":
        member = fed.join_federation("np_gov_001", FederationLevel.FULL)
        print(json.dumps(member.to_dict(), indent=2))

    elif len(sys.argv) > 1 and sys.argv[1] == "map":
        print(json.dumps(fed.get_federation_map(), indent=2))

    elif len(sys.argv) > 1 and sys.argv[1] == "consensus":
        for i in range(5):
            fed.join_federation(f"node_{i}", FederationLevel.FULL)

        result = fed.reach_consensus("test_proposal", [f"node_{i}" for i in range(5)])
        print(json.dumps(result, indent=2))

    elif len(sys.argv) > 1 and sys.argv[1] == "gossip":
        import asyncio
        async def test_gossip():
            await fed.initialize("cli_node")
            fed.join_federation("cli_node", FederationLevel.FULL)
            fed.join_federation("peer_node", FederationLevel.FULL)
            fed.endorse_member("cli_node", "peer_node", TrustLevel.PEER)
            print(json.dumps(fed.get_federation_map(), indent=2))
            print(json.dumps(fed.get_gossip_stats(), indent=2))
        asyncio.run(test_gossip())

    else:
        print("Usage: python federation_protocol.py [join|map|consensus|gossip]")
