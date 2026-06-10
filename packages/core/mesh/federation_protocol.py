
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS World Federation Protocol
======================================
Federates ALL nodes into global mesh
Secure, decentralized, self-organizing
"""

import json
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger("ASIM_FEDERATION")

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
            'endorsed_by': list(self.endorsed_by),
            'resources': self.resources_shared
        }

class FederationProtocol:
    """
    World Federation Protocol
    Connects all AsimNexus nodes globally
    - Countries federate with countries
    - Companies federate with companies and countries
    - People federate with everyone
    """
    
    def __init__(self):
        self.members: Dict[str, FederationMember] = {}
        self.trust_graph: Dict[str, Dict[str, TrustLevel]] = {}
        self.federation_rules: Dict[str, Any] = {}
        self.consensus_log: List[Dict] = []
        
    def join_federation(self, node_id: str, level: FederationLevel,
                       initial_endorsers: List[str] = None) -> FederationMember:
        """Join the world federation"""
        
        # Create member
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
        
        logger.info(f"🌐 Node joined federation: {node_id} ({level.value})")
        return member
    
    def endorse_member(self, endorser_id: str, endorsee_id: str,
                      trust_level: TrustLevel) -> bool:
        """Endorse another federation member"""
        if endorser_id not in self.members or endorsee_id not in self.members:
            return False
        
        member = self.members[endorsee_id]
        member.endorsed_by.add(endorser_id)
        
        # Update trust graph
        if endorser_id not in self.trust_graph:
            self.trust_graph[endorser_id] = {}
        self.trust_graph[endorser_id][endorsee_id] = trust_level
        
        # Update member trust if high enough endorsements
        if len(member.endorsed_by) >= 3:
            member.trust = TrustLevel.PEER
        if len(member.endorsed_by) >= 10:
            member.trust = TrustLevel.TRUSTED
        
        logger.info(f"✅ {endorser_id} endorsed {endorsee_id} at level {trust_level.value}")
        return True
    
    def share_resource(self, node_id: str, resource_type: str,
                      resource_data: Dict) -> bool:
        """Share a resource with the federation"""
        if node_id not in self.members:
            return False
        
        member = self.members[node_id]
        member.resources_shared[resource_type] = {
            **resource_data,
            'shared_at': datetime.now().isoformat()
        }
        
        logger.info(f"📤 {node_id} shared {resource_type} with federation")
        return True
    
    def query_federation(self, query_type: str, 
                        params: Dict) -> List[Dict]:
        """Query resources across federation"""
        results = []
        
        for node_id, member in self.members.items():
            # Check trust level
            if member.trust.value < TrustLevel.PEER.value:
                continue
            
            # Check if has resource
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
        """Reach consensus on proposal (simplified)"""
        # In real system, would use BFT consensus
        
        votes_for = 0
        votes_against = 0
        
        for node_id in voting_nodes:
            if node_id in self.members:
                # Weight by trust level
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
        return result
    
    def get_federation_map(self) -> Dict[str, Any]:
        """Get federation topology map"""
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
            'consensus_events': len(self.consensus_log)
        }
    
    def get_member_path(self, from_node: str, to_node: str,
                       max_hops: int = 5) -> Optional[List[str]]:
        """Find trust path between nodes (Web of Trust)"""
        # BFS for trust path
        visited = {from_node}
        queue = [(from_node, [from_node])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == to_node:
                return path
            
            if len(path) >= max_hops:
                continue
            
            # Get trusted neighbors
            neighbors = self.trust_graph.get(current, {})
            for neighbor, trust in neighbors.items():
                if trust.value >= TrustLevel.PEER.value and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None

_federation = None

def get_mesh_federation() -> FederationProtocol:
    """Get mesh federation singleton"""
    global _federation
    if _federation is None:
        _federation = FederationProtocol()
    return _federation

# Alias for backward-compatibility with mesh/__init__.py imports
get_federation = get_mesh_federation

if __name__ == "__main__":
    import sys
    
    fed = get_mesh_federation()
    
    if len(sys.argv) > 1 and sys.argv[1] == "join":
        member = fed.join_federation("np_gov_001", FederationLevel.FULL)
        print(json.dumps(member.to_dict(), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "map":
        print(json.dumps(fed.get_federation_map(), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "consensus":
        # First add some members
        for i in range(5):
            fed.join_federation(f"node_{i}", FederationLevel.FULL)
        
        result = fed.reach_consensus("test_proposal", [f"node_{i}" for i in range(5)])
        print(json.dumps(result, indent=2))
        
    else:
        print("Usage: python federation_protocol.py [join|map|consensus]")
