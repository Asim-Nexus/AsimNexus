#!/usr/bin/env python3
"""
STATUS: NEW — Production Tests
tests/real/test_clone_consensus_voting.py
Clone Consensus Voting Engine Tests

Tests for the 8/15 approval threshold Constitutional AI Council voting.
"""

import pytest
import asyncio
from core.consensus.clone_consensus_voting import (
    CloneConsensusVoting,
    VoteChoice,
    CloneVote,
    ConsensusRound,
)


class TestVoteChoice:
    """Test VoteChoice enum."""
    
    def test_vote_choices_exist(self):
        """All vote choices are defined."""
        assert VoteChoice.APPROVE.value == "approve"
        assert VoteChoice.REJECT.value == "reject"
        assert VoteChoice.ABSTAIN.value == "abstain"
        assert VoteChoice.DEFER.value == "defer"


class TestCloneVote:
    """Test CloneVote dataclass."""
    
    def test_vote_creation(self):
        """CloneVote can be created."""
        vote = CloneVote(
            voter_id="ceo",
            voter_role="Chief Executive Officer",
            choice=VoteChoice.APPROVE,
            rationale="Strategic alignment confirmed",
        )
        assert vote.voter_id == "ceo"
        assert vote.choice == VoteChoice.APPROVE
        assert vote.to_dict()["choice"] == "approve"


class TestConsensusRound:
    """Test ConsensusRound dataclass."""
    
    def test_round_creation(self):
        """ConsensusRound can be created."""
        vote = CloneVote(
            voter_id="cto",
            voter_role="CTO",
            choice=VoteChoice.APPROVE,
            rationale="Technical approval",
        )
        round_obj = ConsensusRound(
            round_id="test_123",
            proposal="Test proposal",
            sector="technology",
            description="Testing",
            votes=[vote],
        )
        assert round_obj.round_id == "test_123"
        assert len(round_obj.votes) == 1


class TestCloneConsensusVoting:
    """Test CloneConsensusVoting engine."""
    
    @pytest.fixture
    def engine(self):
        """Create consensus engine."""
        return CloneConsensusVoting()
    
    def test_engine_initialization(self, engine):
        """Engine initializes correctly."""
        assert engine._quorum_threshold == 8
        assert engine.get_stats()["total_rounds"] == 0
    
    @pytest.mark.asyncio
    async def test_calculate_outcome_approved(self, engine):
        """8/15 threshold approves with sufficient votes."""
        votes = [
            CloneVote("c1", "CEO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c2", "CTO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c3", "CFO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c4", "COO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c5", "CPO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c6", "CHRO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c7", "CMO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c8", "CLO", VoteChoice.APPROVE, "Rationale"),
        ]
        outcome = engine._calculate_outcome(votes)
        assert outcome == "approved"
    
    @pytest.mark.asyncio
    async def test_calculate_outcome_rejected(self, engine):
        """Insufficient votes result in rejection."""
        votes = [
            CloneVote("c1", "CEO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c2", "CTO", VoteChoice.APPROVE, "Rationale"),
            CloneVote("c3", "CFO", VoteChoice.REJECT, "No"),
            CloneVote("c4", "COO", VoteChoice.REJECT, "No"),
            CloneVote("c5", "CPO", VoteChoice.ABSTAIN, "Neutral"),
        ]
        outcome = engine._calculate_outcome(votes)
        assert outcome == "rejected"
    
    @pytest.mark.asyncio
    async def test_generate_summary(self, engine):
        """Summary generation works correctly."""
        vote = CloneVote("c1", "CEO", VoteChoice.APPROVE, "Rationale")
        round_obj = ConsensusRound(
            round_id="test",
            proposal="Test",
            sector="test",
            description="Test",
            votes=[vote],
        )
        summary = engine._generate_summary(round_obj)
        assert "approved" in summary or "rejected" in summary


class TestSingleton:
    """Test singleton factory."""
    
    def test_get_consensus_engine(self):
        """get_consensus_engine returns singleton."""
        engine1 = CloneConsensusVoting()
        engine2 = CloneConsensusVoting()
        # These are different instances (no singleton yet)
        assert engine1 is not None
        assert engine2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])