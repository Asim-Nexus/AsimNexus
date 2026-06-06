
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Mesh DNA System
=========================
Network identity and trust scoring
Tracks node behavior across mesh
Prevents Sybil attacks
Dynamic trust adjustment
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger("ASIM_MESH_DNA")

class NodeReputation(Enum):
    """Node reputation levels"""
    UNKNOWN = "unknown"
    NEW = "new"
    ESTABLISHED = "established"
    TRUSTED = "trusted"
    ELITE = "elite"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"

@dataclass
class NodeBehavior:
    """Behavioral metrics for node"""
    messages_sent: int = 0
    messages_received: int = 0
    data_shared: int = 0  # MB
    data_requested: int = 0  # MB
    contracts_fulfilled: int = 0
    contracts_breached: int = 0
    uptime_hours: float = 0.0
    response_time_ms: float = 0.0
    
    # Quality metrics
    invalid_messages: int = 0
    spam_count: int = 0
    consensus_violations: int = 0
    
    def calculate_quality_score(self) -> float:
        """Calculate behavior quality score (0-1)"""
        if self.messages_sent == 0:
            return 0.5
        
        # Penalize bad behavior
        penalties = (
            self.invalid_messages * 0.1 +
            self.spam_count * 0.05 +
            self.consensus_violations * 0.2 +
            self.contracts_breached * 0.3
        )
        
        # Reward good behavior
        rewards = (
            min(self.contracts_fulfilled * 0.05, 0.3) +
            min(self.uptime_hours / 1000, 0.2)
        )
        
        score = 1.0 - penalties + rewards
        return max(0.0, min(1.0, score))

@dataclass
class MeshNodeDNA:
    """DNA profile for mesh node"""
    node_id: str
    public_key: str
    dna_hash: str
    
    # Network info
    ip_address: Optional[str]
    port: int
    first_seen: datetime
    last_seen: datetime
    
    # Trust metrics
    reputation: NodeReputation
    trust_score: float  # 0-1
    confidence: float  # Statistical confidence in score
    
    # Behavior
    behavior: NodeBehavior = field(default_factory=NodeBehavior)
    
    # Connections
    connected_peers: Set[str] = field(default_factory=set)
    connection_history: List[Dict] = field(default_factory=list)
    
    # Attestations from other nodes
    peer_attestations: Dict[str, float] = field(default_factory=dict)  # node_id -> score
    
    # Flags
    is_verified: bool = False
    is_gateway: bool = False
    is_relay: bool = False

class MeshDNA:
    """
    Mesh DNA Trust System
    
    Features:
    - Node identity verification
    - Behavioral analysis
    - Trust score calculation
    - Sybil attack detection
    - Dynamic reputation adjustment
    """
    
    def __init__(self):
        self.nodes: Dict[str, MeshNodeDNA] = {}
        self.suspicious_nodes: Set[str] = set()
        self.banned_nodes: Set[str] = set()
        
        # Trust algorithm parameters
        self.min_trust_for_relay = 0.7
        self.min_trust_for_gateway = 0.8
        self.sybil_threshold = 0.9  # Similarity threshold for Sybil detection
        
        # History
        self.trust_history: List[Dict] = []
        
        logger.info("🌐 Mesh DNA system initialized")
    
    def register_node(self, node_id: str, public_key: str,
                     ip: str = None, port: int = 0) -> MeshNodeDNA:
        """Register new mesh node"""
        
        # Generate DNA hash
        dna_data = f"{node_id}:{public_key}:{datetime.now().timestamp()}"
        dna_hash = hashlib.sha256(dna_data.encode()).hexdigest()
        
        node = MeshNodeDNA(
            node_id=node_id,
            public_key=public_key,
            dna_hash=dna_hash,
            ip_address=ip,
            port=port,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            reputation=NodeReputation.NEW,
            trust_score=0.3,  # Start with low trust
            confidence=0.1
        )
        
        self.nodes[node_id] = node
        
        # Check for Sybil attack
        self._check_sybil_attack(node_id)
        
        logger.info(f"🌐 Node registered: {node_id[:16]}... (trust: 0.30)")
        return node
    
    def update_behavior(self, node_id: str, metrics: Dict):
        """Update node behavior metrics"""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        behavior = node.behavior
        
        # Update counters
        behavior.messages_sent += metrics.get('messages_sent', 0)
        behavior.messages_received += metrics.get('messages_received', 0)
        behavior.data_shared += metrics.get('data_shared', 0)
        behavior.data_requested += metrics.get('data_requested', 0)
        behavior.contracts_fulfilled += metrics.get('contracts_fulfilled', 0)
        behavior.contracts_breached += metrics.get('contracts_breached', 0)
        behavior.uptime_hours += metrics.get('uptime_hours', 0)
        
        # Update penalties
        behavior.invalid_messages += metrics.get('invalid_messages', 0)
        behavior.spam_count += metrics.get('spam_count', 0)
        behavior.consensus_violations += metrics.get('consensus_violations', 0)
        
        # Recalculate trust
        self._recalculate_trust(node_id)
        
        return True
    
    def _recalculate_trust(self, node_id: str):
        """Recalculate trust score for node"""
        node = self.nodes[node_id]
        behavior = node.behavior
        
        # Base score from behavior
        behavior_score = behavior.calculate_quality_score()
        
        # Peer attestations (weighted by attester trust)
        attestation_score = 0.0
        attestation_weight = 0.0
        
        for peer_id, score in node.peer_attestations.items():
            if peer_id in self.nodes:
                peer_trust = self.nodes[peer_id].trust_score
                attestation_score += score * peer_trust
                attestation_weight += peer_trust
        
        if attestation_weight > 0:
            attestation_score /= attestation_weight
        else:
            attestation_score = 0.5
        
        # Time factor (older nodes get boost)
        age_days = (datetime.now() - node.first_seen).days
        time_factor = min(age_days / 30, 1.0)  # Max boost at 30 days
        
        # Combine scores
        new_trust = (
            behavior_score * 0.5 +
            attestation_score * 0.3 +
            time_factor * 0.2
        )
        
        # Update node
        old_trust = node.trust_score
        node.trust_score = new_trust
        node.confidence = min(node.confidence + 0.05, 1.0)
        node.last_seen = datetime.now()
        
        # Update reputation level
        node.reputation = self._get_reputation_level(new_trust)
        
        # Update capabilities
        node.is_relay = new_trust >= self.min_trust_for_relay
        node.is_gateway = new_trust >= self.min_trust_for_gateway
        
        # Log significant changes
        if abs(new_trust - old_trust) > 0.1:
            logger.info(f"📊 Trust update: {node_id[:16]}... ({old_trust:.2f} → {new_trust:.2f})")
            
            self.trust_history.append({
                'node_id': node_id,
                'timestamp': datetime.now().isoformat(),
                'old_score': old_trust,
                'new_score': new_trust,
                'reputation': node.reputation.value
            })
        
        # Check for suspicious behavior
        if new_trust < 0.2:
            self.suspicious_nodes.add(node_id)
            logger.warning(f"🚨 Node flagged suspicious: {node_id[:16]}...")
    
    def _get_reputation_level(self, trust_score: float) -> NodeReputation:
        """Determine reputation level from trust score"""
        if trust_score >= 0.95:
            return NodeReputation.ELITE
        elif trust_score >= 0.8:
            return NodeReputation.TRUSTED
        elif trust_score >= 0.6:
            return NodeReputation.ESTABLISHED
        elif trust_score >= 0.3:
            return NodeReputation.NEW
        elif trust_score >= 0.1:
            return NodeReputation.SUSPICIOUS
        else:
            return NodeReputation.MALICIOUS
    
    def _check_sybil_attack(self, new_node_id: str):
        """Check if new node is Sybil attack"""
        new_node = self.nodes[new_node_id]
        
        for existing_id, existing_node in self.nodes.items():
            if existing_id == new_node_id:
                continue
            
            # Check DNA similarity
            similarity = self._calculate_similarity(
                new_node.dna_hash,
                existing_node.dna_hash
            )
            
            if similarity > self.sybil_threshold:
                logger.warning(f"🚨 Sybil attack detected!")
                logger.warning(f"   New: {new_node_id[:16]}...")
                logger.warning(f"   Existing: {existing_id[:16]}...")
                logger.warning(f"   Similarity: {similarity:.2%}")
                
                # Flag both nodes
                self.suspicious_nodes.add(new_node_id)
                self.suspicious_nodes.add(existing_id)
                
                # Reduce trust
                new_node.trust_score *= 0.5
                existing_node.trust_score *= 0.8
    
    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two DNA hashes"""
        # Simple hamming distance
        if len(hash1) != len(hash2):
            return 0.0
        
        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return matches / len(hash1)
    
    def add_attestation(self, from_node: str, to_node: str, score: float):
        """Add trust attestation from one node to another"""
        if to_node not in self.nodes:
            return False
        
        # Only allow attestations from trusted nodes
        if from_node in self.nodes:
            from_trust = self.nodes[from_node].trust_score
            if from_trust < 0.5:
                return False  # Low-trust nodes can't attest
        
        self.nodes[to_node].peer_attestations[from_node] = score
        self._recalculate_trust(to_node)
        
        return True
    
    def ban_node(self, node_id: str, reason: str) -> bool:
        """Permanently ban malicious node"""
        if node_id not in self.nodes:
            return False
        
        self.banned_nodes.add(node_id)
        self.nodes[node_id].trust_score = 0.0
        self.nodes[node_id].reputation = NodeReputation.MALICIOUS
        
        logger.warning(f"🚫 Node banned: {node_id[:16]}... ({reason})")
        return True
    
    def get_trusted_peers(self, min_trust: float = 0.5) -> List[MeshNodeDNA]:
        """Get list of trusted peer nodes"""
        return [
            node for node in self.nodes.values()
            if node.trust_score >= min_trust
            and node.node_id not in self.banned_nodes
        ]
    
    def get_recommended_peers(self, node_id: str, count: int = 5) -> List[str]:
        """Get recommended peers for a node (similar trust levels)"""
        if node_id not in self.nodes:
            return []
        
        my_trust = self.nodes[node_id].trust_score
        
        # Find peers with similar trust
        candidates = [
            (n.node_id, abs(n.trust_score - my_trust))
            for n in self.nodes.values()
            if n.node_id != node_id
            and n.trust_score >= 0.3
            and n.node_id not in self.banned_nodes
        ]
        
        # Sort by trust similarity
        candidates.sort(key=lambda x: x[1])
        
        return [c[0] for c in candidates[:count]]
    
    def get_network_health(self) -> Dict:
        """Get overall network health metrics"""
        if not self.nodes:
            return {'status': 'empty'}
        
        total = len(self.nodes)
        trusted = sum(1 for n in self.nodes.values() if n.trust_score >= 0.5)
        elite = sum(1 for n in self.nodes.values() if n.trust_score >= 0.9)
        suspicious = len(self.suspicious_nodes)
        banned = len(self.banned_nodes)
        
        avg_trust = sum(n.trust_score for n in self.nodes.values()) / total
        
        # Calculate decentralization (Gini coefficient of connections)
        connection_counts = [len(n.connected_peers) for n in self.nodes.values()]
        gini = self._calculate_gini(connection_counts) if connection_counts else 0
        
        return {
            'total_nodes': total,
            'trusted_nodes': trusted,
            'elite_nodes': elite,
            'suspicious_nodes': suspicious,
            'banned_nodes': banned,
            'average_trust': avg_trust,
            'decentralization_score': 1 - gini,  # Higher is more decentralized
            'health_status': 'healthy' if avg_trust > 0.6 and gini < 0.5 else 'degraded'
        }
    
    def _calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient"""
        if not values or sum(values) == 0:
            return 0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = 0
        for i, v in enumerate(sorted_values, 1):
            cumsum += (2 * i - n - 1) * v
        
        return cumsum / (n * sum(sorted_values))
    
    def get_node_profile(self, node_id: str) -> Optional[Dict]:
        """Get detailed profile for a node"""
        if node_id not in self.nodes:
            return None
        
        node = self.nodes[node_id]
        
        return {
            'node_id': node_id,
            'dna_hash': node.dna_hash[:32] + "...",
            'reputation': node.reputation.value,
            'trust_score': node.trust_score,
            'confidence': node.confidence,
            'behavior': {
                'messages_sent': node.behavior.messages_sent,
                'contracts_fulfilled': node.behavior.contracts_fulfilled,
                'uptime_hours': node.behavior.uptime_hours,
                'quality_score': node.behavior.calculate_quality_score()
            },
            'capabilities': {
                'is_relay': node.is_relay,
                'is_gateway': node.is_gateway,
                'is_verified': node.is_verified
            },
            'connected_peers': len(node.connected_peers),
            'peer_attestations': len(node.peer_attestations),
            'age_days': (datetime.now() - node.first_seen).days
        }

_mesh_dna = None

def get_mesh_dna() -> MeshDNA:
    """Get mesh DNA singleton"""
    global _mesh_dna
    if _mesh_dna is None:
        _mesh_dna = MeshDNA()
    return _mesh_dna

if __name__ == "__main__":
    import sys
    
    mesh_dna = get_mesh_dna()
    
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        node = mesh_dna.register_node(
            f"node_{datetime.now().timestamp()}",
            "pk_" + hashlib.sha256(b"test").hexdigest()[:32]
        )
        print(f"Registered: {node.node_id[:16]}...")
        
    elif len(sys.argv) > 1 and sys.argv[1] == "health":
        print(json.dumps(mesh_dna.get_network_health(), indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Create test nodes
        for i in range(5):
            node = mesh_dna.register_node(
                f"test_node_{i}",
                f"pk_{i}_" + hashlib.sha256(f"test{i}".encode()).hexdigest()[:32]
            )
            # Simulate good behavior
            mesh_dna.update_behavior(node.node_id, {
                'messages_sent': 100,
                'contracts_fulfilled': 5,
                'uptime_hours': 100
            })
        
        print(json.dumps(mesh_dna.get_network_health(), indent=2))
        
    else:
        print("Usage: python mesh_dna.py [register|health|test]")
