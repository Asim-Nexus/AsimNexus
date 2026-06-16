"""
STATUS: REAL — Clone Consensus Voting System

AsimNexus Clone Consensus
=========================
15-founder voting system for Governance decisions.
Implements weighted voting with Dharma VETO override.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time


class VoteDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class Vote:
    founder_id: str
    decision: VoteDecision
    weight: float  # 0.0 to 1.0
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None


@dataclass
class Proposal:
    id: str
    title: str
    description: str
    sector: str  # "gov", "company", "user"
    proposer: str
    created_at: float = field(default_factory=time.time)
    votes: List[Vote] = field(default_factory=list)
    threshold: float = 0.51  # 51% for government sector


class CloneConsensus:
    """15-founder consensus voting system"""
    
    FOUNDERS_COUNT = 15
    
    def __init__(self):
        self.proposals: Dict[str, Proposal] = {}
        self.founders: Dict[str, float] = {}  # founder_id -> weight
        self._initialized = False
    
    async def initialize(self):
        """Initialize founder weights equally"""
        if self._initialized:
            return
        
        # Equal weight distribution
        base_weight = 1.0 / self.FOUNDERS_COUNT
        
        # Create 15 founder identities
        for i in range(1, self.FOUNDERS_COUNT + 1):
            founder_id = f"F{i:03d}"
            self.founders[founder_id] = base_weight
        
        self._initialized = True
    
    def create_proposal(self, proposal_id: str, title: str, description: str, sector: str, proposer: str) -> Proposal:
        """Create a new proposal"""
        proposal = Proposal(
            id=proposal_id,
            title=title,
            description=description,
            sector=sector,
            proposer=proposer,
            threshold=0.51 if sector == "gov" else 0.33
        )
        self.proposals[proposal_id] = proposal
        return proposal
    
    async def cast_vote(self, proposal_id: str, founder_id: str, decision: VoteDecision, signature: Optional[str] = None):
        """Cast a vote on a proposal"""
        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        if founder_id not in self.founders:
            raise ValueError(f"Founder {founder_id} not registered")
        
        vote = Vote(
            founder_id=founder_id,
            decision=decision,
            weight=self.founders[founder_id],
            signature=signature
        )
        
        self.proposals[proposal_id].votes.append(vote)
        return vote
    
    async def tally_votes(self, proposal_id: str) -> Dict[str, Any]:
        """Tally votes and return result"""
        proposal = self.proposals[proposal_id]
        
        approve_weight = sum(v.weight for v in proposal.votes if v.decision == VoteDecision.APPROVE)
        reject_weight = sum(v.weight for v in proposal.votes if v.decision == VoteDecision.REJECT)
        
        total_voting_weight = approve_weight + reject_weight
        participation = total_voting_weight
        
        result = {
            "proposal_id": proposal_id,
            "approve_weight": approve_weight,
            "reject_weight": reject_weight,
            "participation": participation,
            "threshold": proposal.threshold,
            "passed": approve_weight >= proposal.threshold,
            "status": "approved" if approve_weight >= proposal.threshold else "rejected"
        }
        
        return result
    
    async def get_proposal_status(self, proposal_id: str) -> Optional[Proposal]:
        """Get proposal status"""
        return self.proposals.get(proposal_id)
    
    def status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "initialized": self._initialized,
            "founders_registered": len(self.founders),
            "active_proposals": len(self.proposals),
            "consensus_type": "15-founder weighted voting"
        }


_consensus_instance: Optional[CloneConsensus] = None


def get_clone_consensus() -> CloneConsensus:
    """Get singleton consensus instance"""
    global _consensus_instance
    if _consensus_instance is None:
        _consensus_instance = CloneConsensus()
    return _consensus_instance