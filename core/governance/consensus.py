#!/usr/bin/env python3
"""
core/governance/consensus.py
AsimNexus — Governance & Consensus Engine

Provides:
  - ConsensusType enum (MAJORITY_VOTE, QUORUM, WEIGHTED_VOTE, DELEGATED, CONSENSUS)
  - ProposalStatus enum (DRAFT, ACTIVE, PASSED, REJECTED, EXECUTED)
  - Proposal, Vote, GovernanceMember dataclasses
  - GovernanceEngine: member management, proposal lifecycle, voting, consensus
  - Singleton factory: get_governance()
"""

import os
import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


# ── ConsensusType Enum ────────────────────────────────────────────────────────

class ConsensusType(str, Enum):
    """Types of consensus mechanisms."""
    MAJORITY_VOTE = "majority_vote"
    QUORUM = "quorum"
    WEIGHTED_VOTE = "weighted_vote"
    DELEGATED = "delegated"
    CONSENSUS = "consensus"


# ── ProposalStatus Enum ───────────────────────────────────────────────────────

class ProposalStatus(str, Enum):
    """Lifecycle status of a governance proposal."""
    DRAFT = "draft"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"


# ── Proposal Dataclass ────────────────────────────────────────────────────────

@dataclass
class Proposal:
    """A governance proposal with voting state."""
    proposal_id: str
    title: str
    description: str
    proposer: str
    consensus_type: ConsensusType = ConsensusType.MAJORITY_VOTE
    quorum_required: int = 51
    voting_period_hours: int = 72
    status: ProposalStatus = ProposalStatus.DRAFT
    votes_for: float = 0.0
    votes_against: float = 0.0
    votes_abstain: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    voting_ends_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None


# ── Vote Dataclass ────────────────────────────────────────────────────────────

@dataclass
class Vote:
    """A single vote cast on a proposal."""
    vote_id: str
    proposal_id: str
    voter: str
    decision: str  # "for" | "against" | "abstain"
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ── GovernanceMember Dataclass ────────────────────────────────────────────────

@dataclass
class GovernanceMember:
    """A member of the governance system."""
    member_id: str
    address: str
    voting_weight: float = 1.0
    reputation_score: float = 1.0
    joined_at: datetime = field(default_factory=datetime.utcnow)


# ── GovernanceEngine ──────────────────────────────────────────────────────────

class GovernanceEngine:
    """
    Governance engine managing members, proposals, voting, and consensus.

    Supports env var overrides:
      - ASIM_GOV_QUORUM_PERCENT (default: 51)
      - ASIM_GOV_VOTING_PERIOD_HOURS (default: 72)
      - ASIM_GOV_MIN_VOTING_WEIGHT (default: 1.0)
    """

    def __init__(self, quorum_percent: Optional[int] = None,
                 voting_period_hours: Optional[int] = None,
                 min_voting_weight: Optional[float] = None):
        # Load defaults from env vars, then override with explicit params
        self.default_quorum_percent = quorum_percent or int(
            os.environ.get("ASIM_GOV_QUORUM_PERCENT", "51"))
        self.default_voting_period_hrs = voting_period_hours or int(
            os.environ.get("ASIM_GOV_VOTING_PERIOD_HOURS", "72"))
        self.default_min_voting_weight = min_voting_weight or float(
            os.environ.get("ASIM_GOV_MIN_VOTING_WEIGHT", "1.0"))

        self.proposals: Dict[str, Proposal] = {}
        self.votes: Dict[str, List[Vote]] = {}  # proposal_id -> list of votes
        self.members: Dict[str, GovernanceMember] = {}
        self._member_counter = 0
        self._proposal_counter = 0
        self._vote_counter = 0

    # ── Member Management ─────────────────────────────────────────────────

    def add_member(self, address: str, voting_weight: float = 1.0,
                   reputation_score: float = 1.0) -> GovernanceMember:
        """Add a new governance member."""
        self._member_counter += 1
        member_id = f"member_{self._member_counter:04d}"
        member = GovernanceMember(
            member_id=member_id,
            address=address,
            voting_weight=voting_weight,
            reputation_score=reputation_score,
        )
        self.members[member_id] = member
        return member

    # ── Proposal Lifecycle ─────────────────────────────────────────────────

    def create_proposal(self, title: str, description: str, proposer: str,
                        quorum_required: Optional[int] = None,
                        voting_period_hours: Optional[int] = None,
                        consensus_type: ConsensusType = ConsensusType.MAJORITY_VOTE) -> Proposal:
        """Create a new proposal in DRAFT status."""
        self._proposal_counter += 1
        proposal_id = f"prop_{self._proposal_counter:04d}"

        prop = Proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer=proposer,
            consensus_type=consensus_type,
            quorum_required=quorum_required or self.default_quorum_percent,
            voting_period_hours=voting_period_hours or self.default_voting_period_hrs,
        )
        self.proposals[proposal_id] = prop
        self.votes[proposal_id] = []
        return prop

    def activate_proposal(self, proposal_id: str) -> bool:
        """Move a proposal from DRAFT to ACTIVE status."""
        prop = self.proposals.get(proposal_id)
        if prop is None:
            return False

        prop.status = ProposalStatus.ACTIVE
        prop.voting_ends_at = datetime.utcnow() + timedelta(hours=prop.voting_period_hours)
        return True

    def finalize_proposal(self, proposal_id: str) -> bool:
        """Finalize a proposal based on consensus calculation."""
        prop = self.proposals.get(proposal_id)
        if prop is None:
            return False

        result = self.calculate_consensus(proposal_id)
        if result.get("consensus_reached"):
            prop.status = ProposalStatus.PASSED
        else:
            prop.status = ProposalStatus.REJECTED
        prop.executed_at = datetime.utcnow()
        return True

    def execute_proposal(self, proposal_id: str) -> bool:
        """Execute a passed proposal."""
        prop = self.proposals.get(proposal_id)
        if prop is None:
            return False
        if prop.status != ProposalStatus.PASSED:
            return False

        prop.status = ProposalStatus.EXECUTED
        return True

    # ── Voting ─────────────────────────────────────────────────────────────

    def cast_vote(self, proposal_id: str, voter_address: str,
                  decision: str, weight: Optional[float] = None) -> Vote:
        """Cast a vote on an active proposal."""
        prop = self.proposals.get(proposal_id)
        if prop is None:
            raise ValueError(f"Proposal {proposal_id} not found")

        # Find member by address
        member = None
        for m in self.members.values():
            if m.address == voter_address:
                member = m
                break

        # Use explicit weight if provided, otherwise member weight, otherwise default
        if weight is not None:
            vote_weight = weight
        else:
            vote_weight = member.voting_weight if member else self.default_min_voting_weight

        self._vote_counter += 1
        vote = Vote(
            vote_id=f"vote_{self._vote_counter:04d}",
            proposal_id=proposal_id,
            voter=voter_address,
            decision=decision,
            weight=vote_weight,
        )

        self.votes[proposal_id].append(vote)

        # Update proposal vote tallies
        if decision == "for":
            prop.votes_for += vote_weight
        elif decision == "against":
            prop.votes_against += vote_weight
        elif decision == "abstain":
            prop.votes_abstain += vote_weight

        return vote

    # ── Consensus Calculation ──────────────────────────────────────────────

    def calculate_consensus(self, proposal_id: str) -> Dict[str, Any]:
        """Calculate consensus for a proposal."""
        prop = self.proposals.get(proposal_id)
        if prop is None:
            return {"error": "Proposal not found"}

        total_votes = prop.votes_for + prop.votes_against + prop.votes_abstain
        # Total weight of all members (for quorum calculation)
        total_weight = sum(m.voting_weight for m in self.members.values())

        if total_votes == 0:
            return {
                "status": "no_votes",
                "consensus_reached": False,
                "quorum_met": False,
                "for_votes": 0.0,
                "against_votes": 0.0,
                "abstain_votes": 0.0,
                "for_percentage": 0.0,
                "total_votes": 0,
                "total_members": len(self.members),
            }

        # Quorum check: what percentage of total weight has voted?
        quorum_percent = (total_votes / total_weight * 100) if total_weight > 0 else 0
        quorum_met = quorum_percent >= prop.quorum_required

        # For percentage: what percentage of total weight is for?
        for_pct = (prop.votes_for / total_weight * 100) if total_weight > 0 else 0
        consensus_reached = quorum_met and for_pct > 50

        return {
            "status": "calculated",
            "consensus_reached": consensus_reached,
            "quorum_met": quorum_met,
            "for_votes": prop.votes_for,
            "against_votes": prop.votes_against,
            "abstain_votes": prop.votes_abstain,
            "for_percentage": round(for_pct, 2),
            "total_votes": total_votes,
            "total_members": len(self.members),
        }

    # ── Queries ────────────────────────────────────────────────────────────

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get a proposal by ID."""
        return self.proposals.get(proposal_id)

    def get_active_proposals(self) -> List[Proposal]:
        """Get all active proposals."""
        return [p for p in self.proposals.values() if p.status == ProposalStatus.ACTIVE]

    def get_member_votes(self, voter_address: str) -> List[Vote]:
        """Get all votes cast by a specific voter."""
        result = []
        for votes_list in self.votes.values():
            for v in votes_list:
                if v.voter == voter_address:
                    result.append(v)
        return result

    def get_governance_stats(self) -> Dict[str, Any]:
        """Get governance statistics."""
        total_proposals = len(self.proposals)
        total_members = len(self.members)
        total_votes = sum(len(v) for v in self.votes.values())
        active_count = len(self.get_active_proposals())

        # Build proposal status distribution
        status_dist: Dict[str, int] = {}
        for p in self.proposals.values():
            key = p.status.value
            status_dist[key] = status_dist.get(key, 0) + 1

        return {
            "total_proposals": total_proposals,
            "total_members": total_members,
            "total_votes": total_votes,
            "active_proposals": active_count,
            "proposal_status_distribution": status_dist,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get extended stats including config fields."""
        stats = self.get_governance_stats()
        stats["default_quorum_percent"] = self.default_quorum_percent
        stats["default_voting_period_hrs"] = self.default_voting_period_hrs
        stats["default_min_voting_weight"] = self.default_min_voting_weight
        return stats


# ── Singleton Factory ─────────────────────────────────────────────────────────

_governance: Optional[GovernanceEngine] = None


def get_governance() -> GovernanceEngine:
    """Return the singleton GovernanceEngine instance."""
    global _governance
    if _governance is None:
        _governance = GovernanceEngine()
    return _governance
