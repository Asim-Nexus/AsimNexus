#!/usr/bin/env python3
"""AsimNexus Consensus Engine - 15 Founder Clones (8/15 Required)
BFT Consensus Implementation
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class VoteType(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"

@dataclass
class Proposal:
    id: str
    title: str
    sector: str
    votes_for: int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    status: str = "pending"

class ConsensusEngine:
    """Business Frequency Token Consensus"""
    
    def __init__(self):
        self.quorum = 8
        self.total_clones = 15
        self.proposals: Dict[str, Proposal] = {}
    
    def propose(self, proposal_id: str, title: str, sector: str) -> Proposal:
        """Create new proposal"""
        p = Proposal(id=proposal_id, title=title, sector=sector)
        self.proposals[proposal_id] = p
        return p
    
    def cast_vote(self, proposal_id: str, vote: str, weight: int = 1) -> Dict:
        """Cast vote from founder clone"""
        p = self.proposals.get(proposal_id)
        if not p:
            return {"error": "Proposal not found"}
        
        if vote == "approve":
            p.votes_for += weight
        elif vote == "reject":
            p.votes_against += weight
        else:
            p.votes_abstain += weight
        
        return {"status": "recorded", "proposal": proposal_id}
    
    def tally(self, proposal_id: str) -> Dict:
        """Tally votes and return result"""
        p = self.proposals.get(proposal_id)
        if not p:
            return {"error": "Proposal not found"}
        
        total = p.votes_for + p.votes_against + p.votes_abstain
        if p.votes_for >= self.quorum:
            p.status = "passed"
        else:
            p.status = "rejected"
        
        return {
            "proposal_id": proposal_id,
            "votes_for": p.votes_for,
            "votes_against": p.votes_against,
            "status": p.status,
            "quorum_reached": p.votes_for >= self.quorum
        }
    
    def get_stats(self) -> Dict:
        return {"total_proposals": len(self.proposals), "quorum": self.quorum}

# Singleton
_engine = None

def get_consensus_engine() -> ConsensusEngine:
    global _engine
    if _engine is None:
        _engine = ConsensusEngine()
    return _engine

__all__ = ["ConsensusEngine", "VoteType", "Proposal", "get_consensus_engine"]