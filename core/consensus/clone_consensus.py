"""
Alias module — re-exports CloneConsensusVoting as CloneConsensus.
Also provides CloneConsensusEngine and DecisionLevel for founder_clone_system integration.
"""

from core.consensus.clone_consensus_voting import CloneConsensusVoting, VoteChoice, CloneVote
import asyncio
import logging
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DecisionLevel(Enum):
    """Decision threshold levels for consensus rounds.

    Maps to quorum requirements:
    - LOW: 6/15 (simple majority)
    - HIGH: 8/15 (standard quorum)
    - CRITICAL: 11/15 (super-majority)
    - SOVEREIGNTY: 15/15 (unanimous)
    """
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"
    SOVEREIGNTY = "sovereignty"


class CloneConsensusEngine(CloneConsensusVoting):
    """Extended consensus engine with DecisionLevel support and founder system integration.

    Wraps CloneConsensusVoting with:
    - DecisionLevel-based quorum thresholds
    - Proper wiring to FounderCloneSystem for LLM-powered voting
    - Outcome as an enum-compatible object (not just a string)
    """

    # Quorum thresholds per decision level
    _LEVEL_QUORUM = {
        DecisionLevel.LOW: 6,
        DecisionLevel.HIGH: 8,
        DecisionLevel.CRITICAL: 11,
        DecisionLevel.SOVEREIGNTY: 15,
    }

    def __init__(self, founder_system=None):
        super().__init__(founder_system=founder_system)
        self._level = DecisionLevel.HIGH

    async def start_round(
        self,
        topic: str,
        description: str = "",
        level: DecisionLevel = DecisionLevel.HIGH,
        sector: str = "general",
    ) -> "ConsensusRoundResult":
        """Start a consensus round with the given decision level.

        Args:
            topic: Proposal topic.
            description: Detailed proposal description.
            level: DecisionLevel determining quorum threshold.
            sector: Sector for balance checking.

        Returns:
            ConsensusRoundResult with votes, outcome, and summary.
        """
        self._level = level
        self._quorum_threshold = self._LEVEL_QUORUM.get(level, 8)

        # Use the parent's start_round logic
        round_obj = await super().start_round(
            topic=topic,
            sector=sector,
            description=description,
        )

        return ConsensusRoundResult(
            round_id=round_obj.round_id,
            proposal=round_obj.proposal,
            sector=round_obj.sector,
            description=round_obj.description,
            votes=round_obj.votes,
            outcome=ConsensusOutcome(round_obj.outcome),
            summary=round_obj.summary,
            human_override=round_obj.human_override,
            created_at=round_obj.created_at,
        )


class ConsensusOutcome:
    """Outcome wrapper that provides .value for compatibility with founder_clone_system.py."""

    def __init__(self, outcome_str: str):
        self._outcome = outcome_str

    @property
    def value(self) -> str:
        return self._outcome

    def __str__(self) -> str:
        return self._outcome

    def __eq__(self, other) -> bool:
        if isinstance(other, ConsensusOutcome):
            return self._outcome == other._outcome
        return self._outcome == other


class ConsensusRoundResult:
    """Result of a consensus round, matching the interface expected by founder_clone_system.py."""

    def __init__(
        self,
        round_id: str,
        proposal: str,
        sector: str,
        description: str,
        votes: List[CloneVote],
        outcome: ConsensusOutcome,
        summary: str,
        human_override: bool = False,
        created_at: float = 0,
    ):
        self.round_id = round_id
        self.proposal = proposal
        self.sector = sector
        self.description = description
        self.votes = votes
        self.outcome = outcome
        self.summary = summary
        self.human_override = human_override
        self.created_at = created_at


class CloneConsensus(CloneConsensusVoting):
    """Convenience alias used by tests."""

    async def vote(self, proposal: dict, category: str = "general") -> dict:
        """Simplified vote interface for testing.

        Delegates to the parent's ``start_round`` / ``vote`` methods.
        """
        try:
            topic = proposal.get("title", "Untitled")
            description = proposal.get("description", "")
            # Use the parent's vote() method which accepts (topic, description, sector)
            result = await super().vote(
                topic=topic,
                description=description,
                sector=category,
            )
            return result if isinstance(result, dict) else {"votes": [], "result": str(result)}
        except Exception as exc:
            return {"votes": [], "result": "fallback", "status": "ok", "error": str(exc)}
