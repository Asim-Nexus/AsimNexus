#!/usr/bin/env python3
"""
Tests for core/founder_clones/consensus_engine.py — Weighted Ensemble Voting ConsensusEngine

Tests the full lifecycle: voter registration → proposal creation → voting → resolution
Covers all 5 voting strategies, quorum, expiration, duplicate prevention.
"""

import os
import sys
import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(autouse=True)
def clean_engine():
    """Reset the singleton and create a fresh engine for each test."""
    from core.founder_clones.consensus_engine import reset_consensus_engine
    reset_consensus_engine()
    yield
    reset_consensus_engine()


@pytest.fixture
def engine():
    """Provide a fresh ConsensusEngine instance."""
    from core.founder_clones.consensus_engine import ConsensusEngine
    eng = ConsensusEngine()
    # Register 5 default voters with varying weights
    for i, (vid, name, weight) in enumerate([
        ("clone_1", "Dharma Guardian", 0.95),
        ("clone_2", "Tech Architect", 0.85),
        ("clone_3", "Economy Manager", 0.80),
        ("clone_4", "Mesh Router", 0.70),
        ("clone_5", "Data Analyst", 0.60),
    ]):
        eng.register_voter(vid, name, weight=weight, metadata={"role": f"role_{i}"})
    return eng


# ─── Voter Registration ────────────────────────────────────────────────────

class TestVoterRegistration:
    """Tests for register_voter and related methods."""

    def test_register_voter(self, engine):
        """A registered voter appears in the registry."""
        voters = engine.get_registered_voters()
        assert len(voters) == 5
        names = [v["name"] for v in voters]
        assert "Dharma Guardian" in names
        assert "Data Analyst" in names

    def test_register_voter_weight_clamped(self, engine):
        """Weights are clamped to [0.0, 1.0]."""
        engine.register_voter("clone_6", "Overpowered", weight=5.0)
        assert engine.get_voter_weight("clone_6") == 1.0

        engine.register_voter("clone_7", "Underpowered", weight=-1.0)
        assert engine.get_voter_weight("clone_7") == 0.0

    def test_register_voter_default_weight(self, engine):
        """Default weight is 1.0."""
        engine.register_voter("clone_8", "Default Weight")
        assert engine.get_voter_weight("clone_8") == 1.0

    def test_get_voter_weight_unregistered(self, engine):
        """Unregistered voter returns weight 0.0."""
        assert engine.get_voter_weight("nonexistent") == 0.0

    def test_register_voters_from_specs(self, engine):
        """register_voters_from_specs handles objects with dharma_weight."""
        from core.founder_clones.consensus_engine import VotingStrategy

        class MockSpec:
            def __init__(self, cid, name, weight):
                self.clone_id = cid
                self.name = name
                self.dharma_weight = weight

        specs = [
            MockSpec(10, "Spec Alpha", 0.9),
            MockSpec(11, "Spec Beta", 0.7),
        ]
        engine.register_voters_from_specs(specs)
        assert engine.get_voter_weight("10") == 0.9
        assert engine.get_voter_weight("11") == 0.7


# ─── Proposal Management ──────────────────────────────────────────────────

class TestProposalManagement:
    """Tests for create_proposal and proposal listing."""

    def test_create_proposal(self, engine):
        """Creating a proposal returns a VoteProposal with generated id."""
        from core.founder_clones.consensus_engine import VotingStrategy
        prop = engine.create_proposal(
            title="Test Proposal",
            description="A test proposal",
            proposed_by="clone_1",
            strategy=VotingStrategy.SIMPLE_MAJORITY,
        )
        assert prop.title == "Test Proposal"
        assert prop.proposed_by == "clone_1"
        assert prop.id is not None
        assert len(prop.id) == 16  # 8 hex bytes = 16 chars
        assert prop.strategy == VotingStrategy.SIMPLE_MAJORITY

    def test_create_proposal_default_strategy(self, engine):
        """Default strategy is WEIGHTED_MAJORITY."""
        from core.founder_clones.consensus_engine import VotingStrategy
        prop = engine.create_proposal("Default", "Default strat", "clone_1")
        assert prop.strategy == VotingStrategy.WEIGHTED_MAJORITY

    def test_create_proposal_with_expiry(self, engine):
        """Proposal with expires_in_seconds gets expires_at set."""
        prop = engine.create_proposal(
            "Expiring", "Will expire", "clone_1",
            expires_in_seconds=60,
        )
        assert prop.expires_at is not None
        assert prop.expires_at > datetime.utcnow()

    def test_create_proposal_with_context(self, engine):
        """Custom context dict is stored on the proposal."""
        ctx = {"urgency": "high", "category": "security"}
        prop = engine.create_proposal(
            "Contextual", "Has context", "clone_1",
            context=ctx,
        )
        assert prop.context == ctx

    def test_get_proposal(self, engine):
        """get_proposal returns the proposal by id."""
        prop = engine.create_proposal("Find me", "Searchable", "clone_1")
        found = engine.get_proposal(prop.id)
        assert found is prop

    def test_get_proposal_not_found(self, engine):
        """get_proposal returns None for unknown id."""
        assert engine.get_proposal("nonexistent") is None

    def test_list_active_proposals(self, engine):
        """Active proposals are listed; resolved ones are not."""
        from core.founder_clones.consensus_engine import Vote
        prop1 = engine.create_proposal("Active", "Still open", "clone_1")
        prop2 = engine.create_proposal("Resolved", "Will close", "clone_1")
        # Resolve prop2 by getting all 5 voters to vote
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
            engine.cast_vote(prop2.id, vid, Vote.APPROVE)

        active = engine.list_active_proposals()
        active_ids = [p.id for p in active]
        assert prop1.id in active_ids
        assert prop2.id not in active_ids

    def test_list_all_proposals(self, engine):
        """list_all_proposals shows all with correct status."""
        from core.founder_clones.consensus_engine import Vote
        prop1 = engine.create_proposal("Active", "Open", "clone_1")
        prop2 = engine.create_proposal("Done", "Closed", "clone_1")
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
            engine.cast_vote(prop2.id, vid, Vote.APPROVE)

        all_props = engine.list_all_proposals()
        status_map = {p["id"]: p["status"] for p in all_props}
        assert status_map[prop1.id] == "active"
        assert status_map[prop2.id] == "resolved"


# ─── Voting Strategies ─────────────────────────────────────────────────────

class TestVotingStrategies:
    """Tests for all 5 voting strategies."""

    def test_simple_majority_passes(self, engine):
        """SIMPLE_MAJORITY: >50% of non-abstain votes passes."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Simple Majority", "Test", "clone_1",
            strategy=VotingStrategy.SIMPLE_MAJORITY,
            quorum_threshold=1.0,
        )
        # 3 approve, 2 reject = 60% > 50% → passes
        for vid in ["clone_1", "clone_2", "clone_3"]:
            assert engine.cast_vote(prop.id, vid, Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_4", Vote.REJECT) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.REJECT)
        assert result is not None
        assert result.passed is True
        assert result.strategy_used == VotingStrategy.SIMPLE_MAJORITY

    def test_simple_majority_fails(self, engine):
        """SIMPLE_MAJORITY: <=50% of non-abstain votes fails."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Simple Fail", "Test", "clone_1",
            strategy=VotingStrategy.SIMPLE_MAJORITY,
            quorum_threshold=1.0,
        )
        # 2 approve, 3 reject = 40% → fails (needs >50%)
        assert engine.cast_vote(prop.id, "clone_1", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_2", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_3", Vote.REJECT) is None
        assert engine.cast_vote(prop.id, "clone_4", Vote.REJECT) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.REJECT)
        assert result is not None
        assert result.passed is False

    def test_super_majority_passes(self, engine):
        """SUPER_MAJORITY: >=67% of non-abstain votes passes."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Super Majority", "Test", "clone_1",
            strategy=VotingStrategy.SUPER_MAJORITY,
            quorum_threshold=1.0,
        )
        # 4 approve, 1 reject = 80% → passes (>=67%)
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4"]:
            assert engine.cast_vote(prop.id, vid, Vote.APPROVE) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.REJECT)
        assert result is not None
        assert result.passed is True

    def test_super_majority_fails(self, engine):
        """SUPER_MAJORITY: <67% of non-abstain votes fails."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Super Fail", "Test", "clone_1",
            strategy=VotingStrategy.SUPER_MAJORITY,
        )
        # 3 approve, 2 reject = 60% → fails (<67%)
        for vid in ["clone_1", "clone_2", "clone_3"]:
            assert engine.cast_vote(prop.id, vid, Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_4", Vote.REJECT) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.REJECT)
        assert result is not None
        assert result.passed is False

    def test_unanimous_passes(self, engine):
        """UNANIMOUS: All non-abstaining voters must approve."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Unanimous", "Test", "clone_1",
            strategy=VotingStrategy.UNANIMOUS,
            quorum_threshold=1.0,
        )
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4"]:
            assert engine.cast_vote(prop.id, vid, Vote.APPROVE) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.APPROVE)
        assert result is not None
        assert result.passed is True

    def test_unanimous_rejected_by_one(self, engine):
        """UNANIMOUS: Any rejection fails the proposal."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Unanimous Fail", "Test", "clone_1",
            strategy=VotingStrategy.UNANIMOUS,
        )
        assert engine.cast_vote(prop.id, "clone_1", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_2", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_3", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_4", Vote.APPROVE) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.REJECT)
        assert result is not None
        assert result.passed is False

    def test_weighted_majority_passes(self, engine):
        """WEIGHTED_MAJORITY: >50% of total weighted vote passes."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Weighted Majority", "Test", "clone_1",
            strategy=VotingStrategy.WEIGHTED_MAJORITY,
        )
        # clone_1 (0.95) + clone_2 (0.85) = 1.80 approve
        # clone_3 (0.80) + clone_4 (0.70) + clone_5 (0.60) = 2.10 total needed
        # 1.80 / (0.95+0.85+0.80+0.70+0.60=3.90) = 46% → fails
        assert engine.cast_vote(prop.id, "clone_1", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_2", Vote.APPROVE) is None
        # Add clone_3 approve too: (0.95+0.85+0.80)=2.60 / 3.90 = 66.7% → passes
        result = engine.cast_vote(prop.id, "clone_3", Vote.APPROVE)
        assert result is not None
        assert result.passed is True

    def test_weighted_super_passes(self, engine):
        """WEIGHTED_SUPER: >=67% of total weighted vote passes."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Weighted Super", "Test", "clone_1",
            strategy=VotingStrategy.WEIGHTED_SUPER,
            quorum_threshold=1.0,
        )
        # clone_1 (0.95) + clone_2 (0.85) + clone_3 (0.80) + clone_4 (0.70) = 3.30
        # Total = 3.90, 3.30/3.90 = 84.6% >= 67% → passes
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4"]:
            assert engine.cast_vote(prop.id, vid, Vote.APPROVE) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.REJECT)
        assert result is not None
        assert result.passed is True

    def test_weighted_super_fails(self, engine):
        """WEIGHTED_SUPER: <67% fails."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Weighted Super Fail", "Test", "clone_1",
            strategy=VotingStrategy.WEIGHTED_SUPER,
            quorum_threshold=1.0,
        )
        # Only clone_1 (0.95) and clone_2 (0.85) approve = 1.80/3.90 = 46%
        assert engine.cast_vote(prop.id, "clone_1", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_2", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_3", Vote.REJECT) is None
        assert engine.cast_vote(prop.id, "clone_4", Vote.REJECT) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.REJECT)
        assert result is not None
        assert result.passed is False


# ─── Quorum ────────────────────────────────────────────────────────────────

class TestQuorum:
    """Tests for quorum requirements."""

    def test_quorum_not_met_does_not_resolve(self, engine):
        """Proposal does not resolve when quorum is not met."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal(
            "Quorum Test", "Test", "clone_1",
            quorum_threshold=0.8,  # need 80% of eligible weight
        )
        # Only 2 of 5 voters (weight sum 1.80 / 3.90 = 46%) — below 80%
        assert engine.cast_vote(prop.id, "clone_1", Vote.APPROVE) is None
        result = engine.cast_vote(prop.id, "clone_2", Vote.APPROVE)
        assert result is None  # Not resolved — quorum not met

    def test_quorum_met_resolves(self, engine):
        """Proposal resolves when quorum is met and votes are sufficient."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal(
            "Quorum Met", "Test", "clone_1",
            quorum_threshold=0.5,  # need 50% of eligible weight
        )
        # clone_1 (0.95) + clone_2 (0.85) + clone_3 (0.80) = 2.60 / 3.90 = 66.7%
        # Meets both quorum (>=50%) and simple majority (>50% of total by default WEIGHTED_MAJORITY)
        assert engine.cast_vote(prop.id, "clone_1", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_2", Vote.APPROVE) is None
        result = engine.cast_vote(prop.id, "clone_3", Vote.APPROVE)
        assert result is not None
        assert result.passed is True
        assert result.quorum_met is True


# ─── Edge Cases ────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_duplicate_vote_rejected(self, engine):
        """A voter cannot vote twice on the same proposal."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal("No Double", "Test", "clone_1")
        engine.cast_vote(prop.id, "clone_1", Vote.APPROVE)
        result = engine.cast_vote(prop.id, "clone_1", Vote.APPROVE)
        assert result is None  # Duplicate returns None

    def test_vote_on_nonexistent_proposal(self, engine):
        """Voting on a non-existent proposal returns None."""
        from core.founder_clones.consensus_engine import Vote
        result = engine.cast_vote("nonexistent", "clone_1", Vote.APPROVE)
        assert result is None

    def test_vote_by_unregistered_voter(self, engine):
        """Voting by an unregistered voter returns None."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal("No Access", "Test", "clone_1")
        result = engine.cast_vote(prop.id, "stranger", Vote.APPROVE)
        assert result is None

    def test_vote_on_resolved_proposal(self, engine):
        """Voting on an already-resolved proposal returns the existing result."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal("Done Deal", "Test", "clone_1")
        # Resolve it
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
            engine.cast_vote(prop.id, vid, Vote.APPROVE)
        # Try voting again
        result = engine.cast_vote(prop.id, "clone_1", Vote.REJECT)
        assert result is not None
        assert result.passed is True  # Still shows original result

    def test_stale_proposal_auto_resolves(self, engine):
        """An expired proposal auto-resolves when voted on after expiry."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal(
            "Stale", "Expired", "clone_1",
            expires_in_seconds=-1,  # Already expired
        )
        result = engine.cast_vote(prop.id, "clone_1", Vote.APPROVE)
        assert result is not None
        assert result.passed is False  # Expired = rejected

    def test_string_vote_normalization(self, engine):
        """String votes ('approve', 'reject', 'abstain') are normalized."""
        prop = engine.create_proposal("String Vote", "Test", "clone_1")
        result = engine.cast_vote(prop.id, "clone_1", "approve")
        assert result is None  # Not resolved yet
        # cast remaining votes as strings
        for vid in ["clone_2", "clone_3", "clone_4"]:
            engine.cast_vote(prop.id, vid, "approve")
        result = engine.cast_vote(prop.id, "clone_5", "approve")
        assert result is not None
        assert result.passed is True

    def test_invalid_string_vote(self, engine):
        """Invalid string votes return None."""
        prop = engine.create_proposal("Bad Vote", "Test", "clone_1")
        result = engine.cast_vote(prop.id, "clone_1", "maybe")
        assert result is None

    def test_abstain_does_not_affect_result(self, engine):
        """Abstain votes don't count toward approval/rejection."""
        from core.founder_clones.consensus_engine import Vote, VotingStrategy
        prop = engine.create_proposal(
            "Abstain Test", "Test", "clone_1",
            strategy=VotingStrategy.SIMPLE_MAJORITY,
        )
        # 2 approve, 1 reject, 2 abstain
        assert engine.cast_vote(prop.id, "clone_1", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_2", Vote.APPROVE) is None
        assert engine.cast_vote(prop.id, "clone_3", Vote.REJECT) is None
        assert engine.cast_vote(prop.id, "clone_4", Vote.ABSTAIN) is None
        result = engine.cast_vote(prop.id, "clone_5", Vote.ABSTAIN)
        assert result is not None
        # For SIMPLE_MAJORITY: non-abstain = 2 approve + 1 reject = 3
        # 2/3 = 66.7% > 50% → passes
        assert result.passed is True


# ─── Vote Status, History & Stats ──────────────────────────────────────────

class TestVoteStatusHistory:
    """Tests for get_vote_status, get_voting_history, get_stats."""

    def test_get_vote_status_active(self, engine):
        """get_vote_status returns active status for unresolved proposal."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal("Status Check", "Check me", "clone_1")
        engine.cast_vote(prop.id, "clone_1", Vote.APPROVE)

        status = engine.get_vote_status(prop.id)
        assert status is not None
        assert status["status"] == "active"
        assert status["title"] == "Status Check"
        assert status["votes_cast"] == 1
        assert status["approval_weight"] > 0

    def test_get_vote_status_resolved(self, engine):
        """get_vote_status returns result dict for resolved proposal."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal("Done", "Finished", "clone_1")
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
            engine.cast_vote(prop.id, vid, Vote.APPROVE)

        status = engine.get_vote_status(prop.id)
        assert status is not None
        assert status["proposal_id"] == prop.id
        assert status["passed"] is True
        assert "completed_at" in status

    def test_get_vote_status_not_found(self, engine):
        """get_vote_status returns None for unknown proposal."""
        assert engine.get_vote_status("nonexistent") is None

    def test_get_voting_history(self, engine):
        """get_voting_history returns resolved proposals in reverse order."""
        from core.founder_clones.consensus_engine import Vote
        prop1 = engine.create_proposal("First", "Old", "clone_1")
        prop2 = engine.create_proposal("Second", "New", "clone_1")
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
            engine.cast_vote(prop1.id, vid, Vote.APPROVE)
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
            engine.cast_vote(prop2.id, vid, Vote.REJECT)

        history = engine.get_voting_history()
        assert len(history) == 2
        titles = [h["title"] for h in history]
        assert "First" in titles
        assert "Second" in titles

    def test_get_voting_history_limit(self, engine):
        """get_voting_history respects the limit parameter."""
        from core.founder_clones.consensus_engine import Vote
        for i in range(5):
            prop = engine.create_proposal(f"Prop {i}", f"Test {i}", "clone_1")
            for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
                engine.cast_vote(prop.id, vid, Vote.APPROVE)

        history = engine.get_voting_history(limit=3)
        assert len(history) == 3

    def test_get_stats(self, engine):
        """get_stats returns summary statistics."""
        from core.founder_clones.consensus_engine import Vote
        # Create and resolve 3 proposals: 2 pass, 1 fail
        for i in range(2):
            prop = engine.create_proposal(f"Pass {i}", "Passing", "clone_1")
            for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
                engine.cast_vote(prop.id, vid, Vote.APPROVE)

        fail_prop = engine.create_proposal("Fail", "Failing", "clone_1")
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
            engine.cast_vote(fail_prop.id, vid, Vote.REJECT)

        stats = engine.get_stats()
        assert stats["total_proposals"] >= 3
        assert stats["resolved"] >= 3
        assert stats["passed"] >= 2
        assert stats["rejected"] >= 1
        assert stats["registered_voters"] == 5
        assert "strategies_used" in stats


# ─── Singleton ─────────────────────────────────────────────────────────────

class TestSingleton:
    """Tests for the singleton pattern."""

    def test_get_consensus_engine(self):
        """get_consensus_engine returns a singleton."""
        from core.founder_clones.consensus_engine import get_consensus_engine
        e1 = get_consensus_engine()
        e2 = get_consensus_engine()
        assert e1 is e2

    def test_reset_consensus_engine(self):
        """reset_consensus_engine clears the singleton."""
        from core.founder_clones.consensus_engine import get_consensus_engine, reset_consensus_engine
        e1 = get_consensus_engine()
        reset_consensus_engine()
        e2 = get_consensus_engine()
        assert e1 is not e2


# ─── VoteResult.to_dict ────────────────────────────────────────────────────

class TestVoteResultToDict:
    """Tests for VoteResult.to_dict()."""

    def test_to_dict_keys(self, engine):
        """to_dict returns all expected keys."""
        from core.founder_clones.consensus_engine import Vote
        prop = engine.create_proposal("Dict Test", "Check dict", "clone_1")
        for vid in ["clone_1", "clone_2", "clone_3", "clone_4", "clone_5"]:
            engine.cast_vote(prop.id, vid, Vote.APPROVE)

        status = engine.get_vote_status(prop.id)
        expected_keys = {
            "proposal_id", "title", "strategy", "votes", "total_weight",
            "approval_weight", "rejection_weight", "abstain_weight",
            "voter_count", "quorum_met", "passed", "completed_at",
        }
        assert expected_keys.issubset(status.keys())
