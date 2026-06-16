#!/usr/bin/env python3
"""
STATUS: NEW — Production Implementation
core/consensus/clone_consensus_voting.py
AsimNexus — Clone Consensus Voting Engine

Constitutional AI Council voting mechanism implementing 8/15 approval threshold.
Used for governance decisions, policy changes, and critical system actions.

Integration:
- core/founder_clones/founder_clone_system.py — Founder system integration
- security/power_balance_constitution.py — Sector balance validation
- core/dharma/veto_engine.py — Human confirmation requirement
"""

import os
import time
import uuid
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Environment configuration
_CONSENSUS_QUORUM = int(os.getenv("ASIM_CONSENSUS_QUORUM", "8"))
_CONSENSUS_TIMEOUT = int(os.getenv("ASIM_CONSENSUS_TIMEOUT", "60"))


class VoteChoice(str, Enum):
    """Voting choices for Constitutional AI Council."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    DEFER = "defer"


@dataclass
class CloneVote:
    """Single vote from a Founder Clone."""
    voter_id: str
    voter_role: str
    choice: VoteChoice
    rationale: str
    weight: float = 1.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voter_id": self.voter_id,
            "voter_role": self.voter_role,
            "choice": self.choice.value,
            "rationale": self.rationale,
            "weight": self.weight,
            "timestamp": self.timestamp,
        }


@dataclass
class ConsensusRound:
    """Complete consensus voting round."""
    round_id: str
    proposal: str
    sector: str
    description: str
    votes: List[CloneVote] = field(default_factory=list)
    outcome: Optional[str] = None
    summary: str = ""
    human_override: bool = False
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_id": self.round_id,
            "proposal": self.proposal,
            "sector": self.sector,
            "description": self.description,
            "votes": [v.to_dict() for v in self.votes],
            "outcome": self.outcome,
            "summary": self.summary,
            "human_override": self.human_override,
            "created_at": self.created_at,
        }


class CloneConsensusVoting:
    """
    Constitutional AI Council consensus mechanism.
    
    Implements the core voting logic:
    - Send proposal to all 15 Founder Clones
    - Collect votes with rationale
    - Calculate 8/15 quorum threshold
    - Generate summary for decision
    """

    def __init__(self, founder_system=None):
        self.founder_system = founder_system
        self._rounds: Dict[str, ConsensusRound] = {}
        self._quorum_threshold = _CONSENSUS_QUORUM
        logger.info(f"CloneConsensusVoting initialized — quorum={self._quorum_threshold}")

    async def start_round(
        self,
        topic: str,
        sector: str = "general",
        description: str = ""
    ) -> ConsensusRound:
        """
        Start a consensus round with all Founder Clones.
        
        Args:
            topic: Proposal topic
            sector: Sector for balance checking
            description: Detailed proposal description
            
        Returns:
            ConsensusRound with votes and outcome
        """
        round_id = f"round_{uuid.uuid4().hex[:12]}"
        
        round_obj = ConsensusRound(
            round_id=round_id,
            proposal=topic,
            sector=sector,
            description=description,
        )
        
        self._rounds[round_id] = round_obj
        
        # Collect votes from founders
        if self.founder_system:
            votes = await self._collect_founder_votes(topic, sector, description)
            round_obj.votes = votes
        
        # Calculate outcome
        round_obj.outcome = self._calculate_outcome(round_obj.votes)
        round_obj.summary = self._generate_summary(round_obj)
        
        logger.info(f"Consensus round {round_id[:8]}: {round_obj.outcome}")
        return round_obj

    async def _collect_founder_votes(
        self,
        topic: str,
        sector: str,
        description: str
    ) -> List[CloneVote]:
        """Collect votes from all Founder Clones in parallel."""
        votes = []
        
        try:
            from core.founder_clones.founder_clone_system import FounderRole
            
            # Get all founder roles
            all_roles = list(FounderRole)
            
            # Create voting tasks
            vote_tasks = []
            for role in all_roles:
                task = self._get_single_vote(role, topic, sector)
                if task:
                    vote_tasks.append(task)
            
            # Collect votes in parallel
            vote_results = await asyncio.gather(
                *vote_tasks, return_exceptions=True
            )
            
            for result in vote_results:
                if isinstance(result, CloneVote):
                    votes.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Vote collection error: {result}")
                    
        except Exception as e:
            logger.error(f"Failed to collect votes: {e}")
            
        return votes

    async def _get_single_vote(
        self,
        role,
        topic: str,
        sector: str
    ) -> Optional[CloneVote]:
        """Get vote from single founder clone."""
        try:
            if not self.founder_system:
                return None
                
            founder = await self.founder_system.get_founder(role)
            if not founder:
                return None
                
            vote_prompt = f"""Vote on this proposal for sector '{sector}':
            
Proposal: {topic}

Respond with ONLY one word: APPROVE, REJECT, ABSTAIN, or DEFER.
Then provide your rationale in one sentence.
"""
            response = await founder.process_message(vote_prompt, {"sector": sector})
            
            # Parse response (simplified)
            response_upper = response.upper()
            choice = VoteChoice.ABSTAIN
            if "APPROVE" in response_upper:
                choice = VoteChoice.APPROVE
            elif "REJECT" in response_upper:
                choice = VoteChoice.REJECT
            elif "DEFER" in response_upper:
                choice = VoteChoice.DEFER
                
            return CloneVote(
                voter_id=role.value,
                voter_role=role.value,
                choice=choice,
                rationale=response[:200]
            )
            
        except Exception as e:
            logger.warning(f"Failed to get vote from {role}: {e}")
            return CloneVote(
                voter_id=role.value,
                voter_role=role.value,
                choice=VoteChoice.ABSTAIN,
                rationale=f"Error: {str(e)}"
            )

    def _calculate_outcome(self, votes: List[CloneVote]) -> str:
        """Calculate consensus outcome (8/15 threshold)."""
        approve_count = sum(1 for v in votes if v.choice == VoteChoice.APPROVE)
        
        if approve_count >= self._quorum_threshold:
            return "approved"
        return "rejected"

    def _generate_summary(self, round_obj: ConsensusRound) -> str:
        """Generate human-readable summary of voting round."""
        approve = sum(1 for v in round_obj.votes if v.choice == VoteChoice.APPROVE)
        reject = sum(1 for v in round_obj.votes if v.choice == VoteChoice.REJECT)
        abstain = sum(1 for v in round_obj.votes if v.choice == VoteChoice.ABSTAIN)
        
        return (
            f"Consensus: {round_obj.outcome} "
            f"(Approve: {approve}, Reject: {reject}, Abstain: {abstain})"
        )

    def get_round(self, round_id: str) -> Optional[ConsensusRound]:
        """Get consensus round by ID."""
        return self._rounds.get(round_id)

    def list_rounds(self, limit: int = 50) -> List[ConsensusRound]:
        """List recent consensus rounds."""
        return sorted(
            list(self._rounds.values()),
            key=lambda r: r.created_at,
            reverse=True
        )[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get consensus voting statistics."""
        total_rounds = len(self._rounds)
        approved = sum(1 for r in self._rounds.values() if r.outcome == "approved")
        
        return {
            "total_rounds": total_rounds,
            "approved_rounds": approved,
            "approval_rate": approved / max(total_rounds, 1),
            "quorum_threshold": self._quorum_threshold,
        }


# Singleton pattern
_consensus_instance: Optional[CloneConsensusVoting] = None


def get_consensus_engine(founder_system=None) -> CloneConsensusVoting:
    """Get or create consensus engine singleton."""
    global _consensus_instance
    if _consensus_instance is None:
        _consensus_instance = CloneConsensusVoting(founder_system)
    return _consensus_instance