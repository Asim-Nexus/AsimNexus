"""
STATUS: REAL — Weighted ensemble consensus voting for multi-clone decision making

ASIMNEXUS Multi-Clone Consensus Engine
=======================================
Provides weighted ensemble voting across all 15 clones.
Uses dharma_weight from CloneSpec for authority-based voting.
Supports multiple voting strategies and quorum requirements.
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger("AsimNexus.ConsensusEngine")


class Vote(Enum):
    """Individual vote options."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class VotingStrategy(Enum):
    """Voting strategy determines how votes are counted."""
    SIMPLE_MAJORITY = "simple_majority"       # >50% of votes
    SUPER_MAJORITY = "super_majority"          # >=67% of votes
    UNANIMOUS = "unanimous"                    # 100% approval
    WEIGHTED_MAJORITY = "weighted_majority"    # >50% of weighted vote
    WEIGHTED_SUPER = "weighted_super"          # >=67% of weighted vote


@dataclass
class VoteProposal:
    """A proposal to be voted on by clones."""
    id: str
    title: str
    description: str
    proposed_by: str  # clone name or role
    strategy: VotingStrategy = VotingStrategy.WEIGHTED_MAJORITY
    quorum_threshold: float = 0.5  # minimum % of eligible voters required
    expires_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CastVote:
    """A single vote cast by a clone."""
    voter_id: str
    voter_name: str
    vote: Vote
    weight: float = 1.0
    rationale: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VoteResult:
    """The result of a completed vote."""
    proposal: VoteProposal
    votes: List[CastVote]
    total_weight: float
    approval_weight: float
    rejection_weight: float
    abstain_weight: float
    voter_count: int
    quorum_met: bool
    passed: bool
    strategy_used: VotingStrategy
    completed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal.id,
            "title": self.proposal.title,
            "strategy": self.strategy_used.value,
            "votes": [
                {
                    "voter": v.voter_name,
                    "vote": v.vote.value,
                    "weight": v.weight,
                    "rationale": v.rationale,
                }
                for v in self.votes
            ],
            "total_weight": self.total_weight,
            "approval_weight": self.approval_weight,
            "rejection_weight": self.rejection_weight,
            "abstain_weight": self.abstain_weight,
            "voter_count": self.voter_count,
            "quorum_met": self.quorum_met,
            "passed": self.passed,
            "completed_at": self.completed_at.isoformat(),
        }


class ConsensusEngine:
    """
    Weighted ensemble consensus voting engine.
    
    Features:
    - Weighted voting using dharma_weight (0.0–1.0)
    - Multiple voting strategies
    - Quorum requirements
    - Voting history with audit trail
    - Support for time-limited proposals
    """
    
    def __init__(self):
        self._proposals: Dict[str, VoteProposal] = {}
        self._results: Dict[str, VoteResult] = {}
        self._active_votes: Dict[str, List[CastVote]] = {}
        self._voter_registry: Dict[str, Dict[str, Any]] = {}
        logger.info("🏛️ ConsensusEngine initialized")

    # ─── Voter Registration ────────────────────────────────────────────────────

    def register_voter(self, voter_id: str, name: str, weight: float = 1.0,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a voter (clone) with their voting weight."""
        self._voter_registry[voter_id] = {
            "name": name,
            "weight": max(0.0, min(1.0, weight)),
            "metadata": metadata or {},
        }
        logger.debug(f"Registered voter: {name} (weight={weight})")

    def register_voters_from_specs(self, specs: List[Any]) -> None:
        """Register voters from CloneSpec list (has dharma_weight)."""
        for spec in specs:
            weight = getattr(spec, 'dharma_weight', 0.5)
            self.register_voter(
                voter_id=str(spec.clone_id) if hasattr(spec, 'clone_id') else spec.name.lower(),
                name=spec.name if hasattr(spec, 'name') else str(spec.role.value),
                weight=weight,
            )

    def get_voter_weight(self, voter_id: str) -> float:
        """Get a voter's weight."""
        info = self._voter_registry.get(voter_id)
        return info["weight"] if info else 0.0

    def get_registered_voters(self) -> List[Dict[str, Any]]:
        """Get all registered voters."""
        return [
            {"id": vid, "name": info["name"], "weight": info["weight"]}
            for vid, info in self._voter_registry.items()
        ]

    # ─── Proposal Management ──────────────────────────────────────────────────

    def create_proposal(self, title: str, description: str, proposed_by: str,
                        strategy: VotingStrategy = VotingStrategy.WEIGHTED_MAJORITY,
                        quorum_threshold: float = 0.5,
                        expires_in_seconds: Optional[int] = None,
                        context: Optional[Dict[str, Any]] = None) -> VoteProposal:
        """Create a new voting proposal."""
        import secrets
        proposal = VoteProposal(
            id=secrets.token_hex(8),
            title=title,
            description=description,
            proposed_by=proposed_by,
            strategy=strategy,
            quorum_threshold=quorum_threshold,
            expires_at=(
                datetime.utcnow() + timedelta(seconds=expires_in_seconds)
                if expires_in_seconds else None
            ),
            context=context or {},
        )
        self._proposals[proposal.id] = proposal
        self._active_votes[proposal.id] = []
        logger.info(f"📋 Proposal created: '{title}' (id={proposal.id}, strategy={strategy.value})")
        return proposal

    def get_proposal(self, proposal_id: str) -> Optional[VoteProposal]:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)

    def list_active_proposals(self) -> List[VoteProposal]:
        """List all active (not yet resolved) proposals."""
        now = datetime.utcnow()
        return [
            p for pid, p in self._proposals.items()
            if pid not in self._results
            and (p.expires_at is None or p.expires_at > now)
        ]

    def list_all_proposals(self) -> List[Dict[str, Any]]:
        """List all proposals with their status."""
        now = datetime.utcnow()
        result = []
        for pid, proposal in self._proposals.items():
            if pid in self._results:
                status = "resolved"
            elif proposal.expires_at and proposal.expires_at < now:
                status = "expired"
            else:
                status = "active"
            result.append({
                "id": pid,
                "title": proposal.title,
                "status": status,
                "strategy": proposal.strategy.value,
                "created_at": proposal.created_at.isoformat(),
            })
        return result

    # ─── Voting ────────────────────────────────────────────────────────────────

    def cast_vote(self, proposal_id: str, voter_id: str, vote: Vote,
                  rationale: str = "") -> Optional[VoteResult]:
        """
        Cast a vote on a proposal.
        Accepts both Vote enum and string values ("approve", "reject", "abstain").
        Returns the VoteResult immediately if the vote resolves the proposal.
        """
        # Normalize vote from string to enum if needed
        if isinstance(vote, str):
            vote_str = vote.lower().strip()
            if vote_str == "approve":
                vote = Vote.APPROVE
            elif vote_str == "reject":
                vote = Vote.REJECT
            elif vote_str == "abstain":
                vote = Vote.ABSTAIN
            else:
                logger.error(f"Invalid vote string '{vote}': must be approve/reject/abstain")
                return None

        # Validate proposal
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            logger.error(f"Proposal {proposal_id} not found")
            return None

        # Check if already resolved
        if proposal_id in self._results:
            logger.warning(f"Proposal {proposal_id} already resolved")
            return self._results[proposal_id]

        # Check expiration
        if proposal.expires_at and datetime.utcnow() > proposal.expires_at:
            logger.warning(f"Proposal {proposal_id} has expired")
            return self._resolve_expired(proposal)

        # Validate voter
        voter_info = self._voter_registry.get(voter_id)
        if not voter_info:
            logger.error(f"Voter {voter_id} not registered")
            return None

        # Check for duplicate vote
        existing_votes = self._active_votes.get(proposal_id, [])
        if any(v.voter_id == voter_id for v in existing_votes):
            logger.warning(f"Voter {voter_id} already voted on proposal {proposal_id}")
            return None

        # Cast the vote
        cast = CastVote(
            voter_id=voter_id,
            voter_name=voter_info["name"],
            vote=vote,
            weight=voter_info["weight"],
            rationale=rationale,
        )
        existing_votes.append(cast)
        logger.info(f"🗳️  {voter_info['name']} voted {vote.value} on '{proposal.title}' (weight={cast.weight})")

        # Check if we should resolve
        result = self._try_resolve(proposal, existing_votes)
        if result:
            self._results[proposal_id] = result
            # Cleanup active votes
            self._active_votes.pop(proposal_id, None)
            logger.info(
                f"🏁 Vote resolved on '{proposal.title}': "
                f"{'PASSED' if result.passed else 'REJECTED'} "
                f"({result.approval_weight:.1f}/{result.total_weight:.1f} weight)"
            )
            return result

        return None

    def get_vote_status(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get current vote status without resolving."""
        if proposal_id in self._results:
            return self._results[proposal_id].to_dict()

        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None

        votes = self._active_votes.get(proposal_id, [])
        total_weight = sum(v.weight for v in votes)
        approval_weight = sum(v.weight for v in votes if v.vote == Vote.APPROVE)
        rejection_weight = sum(v.weight for v in votes if v.vote == Vote.REJECT)
        abstain_weight = sum(v.weight for v in votes if v.vote == Vote.ABSTAIN)

        eligible_weight = sum(
            info["weight"] for info in self._voter_registry.values()
        )
        quorum_met = (total_weight / eligible_weight >= proposal.quorum_threshold
                      if eligible_weight > 0 else False)

        return {
            "proposal_id": proposal_id,
            "title": proposal.title,
            "status": "active",
            "strategy": proposal.strategy.value,
            "votes_cast": len(votes),
            "total_weight": total_weight,
            "approval_weight": approval_weight,
            "rejection_weight": rejection_weight,
            "abstain_weight": abstain_weight,
            "quorum_met": quorum_met,
            "quorum_threshold": proposal.quorum_threshold,
            "eligible_weight": eligible_weight,
            "voters": [
                {"name": v.voter_name, "vote": v.vote.value, "weight": v.weight}
                for v in votes
            ],
        }

    # ─── Resolution ────────────────────────────────────────────────────────────

    def _try_resolve(self, proposal: VoteProposal, votes: List[CastVote]) -> Optional[VoteResult]:
        """Try to resolve a proposal based on current votes."""
        # Calculate weights
        total_weight = sum(v.weight for v in votes)
        approval_weight = sum(v.weight for v in votes if v.vote == Vote.APPROVE)
        rejection_weight = sum(v.weight for v in votes if v.vote == Vote.REJECT)
        abstain_weight = sum(v.weight for v in votes if v.vote == Vote.ABSTAIN)

        # Check quorum (only if we have all voters or quorum is met)
        eligible_weight = sum(
            info["weight"] for info in self._voter_registry.values()
        )
        quorum_met = (total_weight / eligible_weight >= proposal.quorum_threshold
                      if eligible_weight > 0 else False)

        if not quorum_met:
            return None  # Cannot resolve without quorum

        # Determine pass/fail based on strategy
        passed = False
        if proposal.strategy == VotingStrategy.UNANIMOUS:
            # All non-abstaining voters must approve
            non_abstain_weight = approval_weight + rejection_weight
            passed = (non_abstain_weight > 0 and rejection_weight == 0)

        elif proposal.strategy == VotingStrategy.SUPER_MAJORITY:
            # >= 67% of total weight (excluding abstain)
            non_abstain_weight = approval_weight + rejection_weight
            if non_abstain_weight > 0:
                passed = (approval_weight / non_abstain_weight) >= 0.67

        elif proposal.strategy == VotingStrategy.SIMPLE_MAJORITY:
            # > 50% of total weight (excluding abstain)
            non_abstain_weight = approval_weight + rejection_weight
            if non_abstain_weight > 0:
                passed = (approval_weight / non_abstain_weight) > 0.5

        elif proposal.strategy == VotingStrategy.WEIGHTED_MAJORITY:
            # > 50% of weighted vote including abstain as neutral
            if total_weight > 0:
                passed = (approval_weight / total_weight) > 0.5

        elif proposal.strategy == VotingStrategy.WEIGHTED_SUPER:
            # >= 67% of weighted vote
            if total_weight > 0:
                passed = (approval_weight / total_weight) >= 0.67

        # Check if all voters have voted (auto-resolve)
        voted_ids = {v.voter_id for v in votes}
        all_voters = set(self._voter_registry.keys())
        all_voted = voted_ids == all_voters

        if all_voted or self._quorum_sufficient(proposal, total_weight, eligible_weight, passed):
            return VoteResult(
                proposal=proposal,
                votes=votes,
                total_weight=total_weight,
                approval_weight=approval_weight,
                rejection_weight=rejection_weight,
                abstain_weight=abstain_weight,
                voter_count=len(votes),
                quorum_met=quorum_met,
                passed=passed,
                strategy_used=proposal.strategy,
            )

        return None

    def _quorum_sufficient(self, proposal: VoteProposal, total_weight: float,
                           eligible_weight: float, would_pass: bool) -> bool:
        """Check if we can resolve early based on remaining votes."""
        # If it can't pass even with all remaining votes, resolve as rejected
        remaining_weight = eligible_weight - total_weight
        approval_weight = sum(
            v.weight for v in self._active_votes.get(proposal.id, [])
            if v.vote == Vote.APPROVE
        )

        if not would_pass:
            # Check if remaining votes could flip it
            if proposal.strategy in [VotingStrategy.UNANIMOUS, VotingStrategy.SUPER_MAJORITY]:
                return False  # Can't know for sure
            return True  # Simple majorities can be resolved when quorum met and not passing

        # If passing, check if remaining votes could flip to fail
        if proposal.strategy == VotingStrategy.UNANIMOUS:
            return remaining_weight == 0
        elif proposal.strategy in [VotingStrategy.SUPER_MAJORITY, VotingStrategy.WEIGHTED_SUPER]:
            # Need enough remaining weight to drop below 67%
            total_if_all_oppose = total_weight + remaining_weight
            if total_if_all_oppose > 0:
                would_fail = (approval_weight / total_if_all_oppose) < 0.67
                return not would_fail
            return True
        else:
            # Simple majority — check if remaining votes could flip
            total_if_all_oppose = total_weight + remaining_weight
            if total_if_all_oppose > 0:
                would_fail = (approval_weight / total_if_all_oppose) <= 0.5
                return not would_fail
            return True

    def _resolve_expired(self, proposal: VoteProposal) -> VoteResult:
        """Resolve an expired proposal (auto-reject)."""
        votes = self._active_votes.get(proposal.id, [])
        total_weight = sum(v.weight for v in votes)
        approval_weight = sum(v.weight for v in votes if v.vote == Vote.APPROVE)
        rejection_weight = sum(v.weight for v in votes if v.vote == Vote.REJECT)
        abstain_weight = sum(v.weight for v in votes if v.vote == Vote.ABSTAIN)

        result = VoteResult(
            proposal=proposal,
            votes=votes,
            total_weight=total_weight,
            approval_weight=approval_weight,
            rejection_weight=rejection_weight,
            abstain_weight=abstain_weight,
            voter_count=len(votes),
            quorum_met=False,
            passed=False,  # Expired = rejected
            strategy_used=proposal.strategy,
        )
        self._results[proposal.id] = result
        self._active_votes.pop(proposal.id, None)
        logger.info(f"⏰ Proposal '{proposal.title}' expired and rejected")
        return result

    # ─── History & Status ──────────────────────────────────────────────────────

    def get_voting_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent voting history."""
        results = sorted(
            self._results.values(),
            key=lambda r: r.completed_at,
            reverse=True,
        )
        return [r.to_dict() for r in results[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        """Get consensus engine statistics."""
        total = len(self._results)
        passed = sum(1 for r in self._results.values() if r.passed)
        rejected = total - passed

        return {
            "total_proposals": total + len(self._active_votes),
            "resolved": total,
            "passed": passed,
            "rejected": rejected,
            "active": len(self._active_votes),
            "registered_voters": len(self._voter_registry),
            "strategies_used": {
                s.value: sum(
                    1 for r in self._results.values()
                    if r.strategy_used == s
                )
                for s in VotingStrategy
            },
        }


# ─── Singleton ────────────────────────────────────────────────────────────────
_consensus_engine: Optional[ConsensusEngine] = None


def get_consensus_engine() -> ConsensusEngine:
    """Get or create global ConsensusEngine instance."""
    global _consensus_engine
    if _consensus_engine is None:
        _consensus_engine = ConsensusEngine()
    return _consensus_engine


def reset_consensus_engine():
    """Reset global instance (for testing)."""
    global _consensus_engine
    _consensus_engine = None
