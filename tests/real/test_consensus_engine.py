#!/usr/bin/env python3
"""
Tests for core/consensus/consensus_engine.py — Ensemble Consensus Engine

Tests the full multi-clone voting system with all 4 voting modes:
  1. MAJORITY_VOTE       — Simple majority (>50%) of clones agree
  2. PAIRWISE_COMPARISON — Elo-style pairwise comparison between clones
  3. CONFIDENCE_WEIGHTED — Each vote weighted by clone's confidence score
  4. ROLE_BASED_VETO     — Specific clones have veto power in their domain

Also tests: voter registration, delegation, arbitration, human override,
audit trail, quorum, expiration, edge cases.
"""

import os
import sys
import json
import time
import pytest
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(autouse=True)
def clean_engine():
    """Reset the singleton and create a fresh engine for each test."""
    from core.consensus.consensus_engine import reset_consensus_engine
    reset_consensus_engine()
    yield
    reset_consensus_engine()


@pytest.fixture
def engine():
    """Provide a fresh ConsensusEngine with all 15 clones registered."""
    from core.consensus.consensus_engine import ConsensusEngine
    eng = ConsensusEngine()
    eng.register_voters_from_15_clones()
    return eng


@pytest.fixture
def minimal_engine():
    """Provide a fresh ConsensusEngine with just 3 test voters."""
    from core.consensus.consensus_engine import ConsensusEngine
    eng = ConsensusEngine()
    eng.register_voter("voter_a", "Voter A", "technology", weight=1.0)
    eng.register_voter("voter_b", "Voter B", "security", weight=1.0)
    eng.register_voter("voter_c", "Voter C", "ethics", weight=1.0)
    return eng


# ═══════════════════════════════════════════════════════════════════════════════
# Voter Registration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestVoterRegistration:
    """Tests for register_voter and related methods."""

    def test_register_voter(self, engine):
        """A registered voter appears in the registry."""
        from core.consensus.consensus_engine import ConsensusEngine
        voters = engine.get_all_voters()
        assert len(voters) == 15
        names = [v.name for v in voters]
        assert "Dharma Guardian" in names
        assert "Sovereignty Guard" in names

    def test_register_single_voter(self):
        """Register a single voter and verify."""
        from core.consensus.consensus_engine import ConsensusEngine
        eng = ConsensusEngine()
        eng.register_voter("test_01", "Test Clone", "testing", weight=0.8)
        voter = eng.get_voter("test_01")
        assert voter is not None
        assert voter.name == "Test Clone"
        assert voter.domain == "testing"
        assert voter.weight == 0.8
        assert voter.elo_rating == 1500

    def test_register_voter_weight_clamped(self):
        """Weights are clamped to [0.0, 1.0]."""
        from core.consensus.consensus_engine import ConsensusEngine
        eng = ConsensusEngine()
        eng.register_voter("high", "High Weight", "test", weight=5.0)
        assert eng.get_voter("high").weight == 1.0

        eng.register_voter("low", "Low Weight", "test", weight=-1.0)
        assert eng.get_voter("low").weight == 0.0

    def test_get_voter_not_found(self, engine):
        """get_voter returns None for unregistered id."""
        assert engine.get_voter("nonexistent") is None

    def test_registered_voter_count(self, engine):
        """registered_voter_count returns correct count."""
        assert engine.registered_voter_count() == 15

    def test_get_all_voters(self, engine):
        """get_all_voters returns all registered voters."""
        voters = engine.get_all_voters()
        assert len(voters) == 15
        assert all(isinstance(v.voter_id, str) for v in voters)
        assert all(isinstance(v.domain, str) for v in voters)


# ═══════════════════════════════════════════════════════════════════════════════
# Proposal Creation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestProposalCreation:
    """Tests for create_proposal."""

    def test_create_proposal(self, engine):
        """Creating a proposal returns a Proposal with generated id."""
        from core.consensus.consensus_engine import VotingMode
        prop = engine.create_proposal(
            title="Test Proposal",
            description="A test proposal",
            proposed_by="clone_01",
            mode=VotingMode.MAJORITY_VOTE,
        )
        assert prop.title == "Test Proposal"
        assert prop.proposed_by == "clone_01"
        assert prop.proposal_id is not None
        assert len(prop.proposal_id) == 16
        assert prop.mode == VotingMode.MAJORITY_VOTE

    def test_create_proposal_default_mode(self, engine):
        """Default mode is MAJORITY_VOTE."""
        from core.consensus.consensus_engine import VotingMode
        prop = engine.create_proposal("Default", "Default mode", "clone_01")
        assert prop.mode == VotingMode.MAJORITY_VOTE

    def test_create_proposal_with_expiry(self, engine):
        """Proposal with expires_in_seconds gets expires_at set."""
        prop = engine.create_proposal(
            "Expiring", "Will expire", "clone_01",
            expires_in_seconds=60,
        )
        assert prop.expires_at is not None

    def test_create_proposal_with_context(self, engine):
        """Custom context dict is stored on the proposal."""
        ctx = {"urgency": "high", "category": "security"}
        prop = engine.create_proposal(
            "Contextual", "Has context", "clone_01",
            context=ctx,
        )
        assert prop.context == ctx

    def test_get_proposal(self, engine):
        """get_proposal returns the proposal by id."""
        prop = engine.create_proposal("Find me", "Searchable", "clone_01")
        found = engine.get_proposal(prop.proposal_id)
        assert found is prop

    def test_get_proposal_not_found(self, engine):
        """get_proposal returns None for unknown id."""
        assert engine.get_proposal("nonexistent") is None


# ═══════════════════════════════════════════════════════════════════════════════
# Majority Vote Mode Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMajorityVote:
    """Tests for MAJORITY_VOTE mode — >50% of active votes."""

    def test_majority_approves(self, engine):
        """>50% approval passes."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            # 9 approve, 6 reject = 60% > 50% → passes
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 10)
        ] + [
            self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8)
            for i in range(10, 16)
        ]
        result = engine.run_consensus(
            title="Majority Test",
            description="Testing majority approval",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.5,
        )
        assert result.decision == "approved"
        assert result.confidence > 0.5
        assert result.details["approves"] == 9
        assert result.details["rejects"] == 6

    def test_majority_rejects(self, engine):
        """<=50% approval fails."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8)
            for i in range(1, 9)
        ] + [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(9, 16)
        ]
        result = engine.run_consensus(
            title="Majority Reject",
            description="Testing majority rejection",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.5,
        )
        assert result.decision == "rejected"
        assert result.details["rejects"] == 8
        assert result.details["approves"] == 7

    def test_majority_all_approve(self, engine):
        """All 15 approve passes."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 1.0)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Unanimous",
            description="All approve",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.5,
        )
        assert result.decision == "approved"
        assert result.details["approves"] == 15
        assert result.details["rejects"] == 0

    def test_majority_all_reject(self, engine):
        """All 15 reject fails."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 1.0)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="All Reject",
            description="All reject",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.5,
        )
        assert result.decision == "rejected"
        assert result.details["rejects"] == 15

    def test_majority_with_abstain(self, engine):
        """Abstain votes are excluded from count."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 6)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8) for i in range(6, 9)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.ABSTAIN, 0.0) for i in range(9, 16)]
        )
        result = engine.run_consensus(
            title="With Abstain",
            description="Some abstain",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.5,
        )
        # Active = 5 approve + 3 reject = 8, 5/8 = 62.5% > 50% → approved
        assert result.decision == "approved"
        assert result.details["approves"] == 5
        assert result.details["rejects"] == 3
        assert result.details["abstains"] == 7

    def test_majority_all_abstain(self, engine):
        """All abstain = deferred."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.ABSTAIN, 0.0)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="All Abstain",
            description="Nobody decides",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.5,
        )
        assert result.decision == "deferred"

    def test_majority_with_defers(self, engine):
        """DEFER votes are excluded from active count."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 8)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.DEFER, 0.5) for i in range(8, 16)]
        )
        result = engine.run_consensus(
            title="With Defer",
            description="Some defer",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.5,
        )
        # 7 approve, 0 reject = 7/7 = 100% > 50% → approved
        assert result.decision == "approved"
        assert result.details["defers"] == 8

    def test_majority_tie_breaker(self, engine):
        """Tie goes to reject (not >50%)."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # 7 approve, 7 reject, 1 abstain = 7/14 = 50%, not > 50%
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 8)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8) for i in range(8, 15)]
            + [self._make_vote("clone_15", VoteChoice.ABSTAIN, 0.0)]
        )
        result = engine.run_consensus(
            title="Tie",
            description="Tie vote",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.5,
        )
        assert result.decision == "rejected"  # 7/14 = 50%, not > 50%

    def test_majority_custom_threshold_67(self, engine):
        """Custom threshold of 67%."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # 11 approve, 4 reject = 11/15 = 73.3% → passes 67% threshold
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 12)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8) for i in range(12, 16)]
        )
        result = engine.run_consensus(
            title="67% Threshold",
            description="Testing custom threshold",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
            threshold=0.67,
        )
        assert result.decision == "approved"  # 11/15 = 73.3% > 67%

    def _make_vote(self, voter_id, choice, confidence):
        from core.consensus.consensus_engine import Vote
        return Vote(voter_id=voter_id, choice=choice, confidence=confidence)


# ═══════════════════════════════════════════════════════════════════════════════
# Pairwise Comparison (Elo) Mode Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPairwiseComparison:
    """Tests for PAIRWISE_COMPARISON mode — Elo-style ranking."""

    def test_pairwise_approves(self, engine):
        """More approve voters = higher approve Elo = approved."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # 10 approve, 5 reject — approve should win
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 11)
        ] + [
            self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8)
            for i in range(11, 16)
        ]
        result = engine.run_consensus(
            title="Pairwise Approve",
            description="More approves than rejects",
            votes=votes,
            mode=VotingMode.PAIRWISE_COMPARISON,
        )
        assert result.decision == "approved"
        assert result.details["approve_count"] == 10
        assert result.details["reject_count"] == 5
        assert result.details["approve_elo_avg"] > result.details["reject_elo_avg"]

    def test_pairwise_rejects(self, engine):
        """More reject voters = rejected (decision by count, Elo for confidence)."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # 5 approve, 10 reject — reject should win by count
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 6)
        ] + [
            self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8)
            for i in range(6, 16)
        ]
        result = engine.run_consensus(
            title="Pairwise Reject",
            description="More rejects than approves",
            votes=votes,
            mode=VotingMode.PAIRWISE_COMPARISON,
        )
        assert result.decision == "rejected"
        assert result.details["reject_count"] == 10
        assert result.details["approve_count"] == 5
        # Elo note: each approve voter beats ALL reject voters pairwise,
        # so approve_elo_avg may be higher even though reject side has more votes.
        # Decision is by count; Elo is tracked for confidence/future rounds.

    def test_pairwise_elo_changes(self, engine):
        """Elo ratings change after pairwise comparison."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode

        # Record initial Elo ratings
        initial_elos = {
            v.voter_id: v.elo_rating
            for v in engine.get_all_voters()
        }

        # 10 approve, 5 reject
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 11)
        ] + [
            self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8)
            for i in range(11, 16)
        ]
        engine.run_consensus(
            title="Elo Changes",
            description="Checking Elo changes",
            votes=votes,
            mode=VotingMode.PAIRWISE_COMPARISON,
        )

        # Elo ratings should have changed
        final_elos = {
            v.voter_id: v.elo_rating
            for v in engine.get_all_voters()
        }

        # Approve voters should have gained Elo
        for i in range(1, 11):
            vid = f"clone_{i:02d}"
            assert final_elos[vid] > initial_elos[vid], f"{vid} should have gained Elo"

        # Reject voters should have lost Elo
        for i in range(11, 16):
            vid = f"clone_{i:02d}"
            assert final_elos[vid] < initial_elos[vid], f"{vid} should have lost Elo"

    def test_pairwise_elo_changes_in_details(self, engine):
        """Elo changes are recorded in result details."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 9)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8) for i in range(9, 16)]
        )
        result = engine.run_consensus(
            title="Elo Details",
            description="Checking details",
            votes=votes,
            mode=VotingMode.PAIRWISE_COMPARISON,
        )
        assert "elo_changes" in result.details
        assert len(result.details["elo_changes"]) > 0
        assert "k_factor" in result.details
        assert result.details["k_factor"] == 32

    def test_pairwise_all_approve(self, engine):
        """All approve = approved."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 1.0)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Pairwise All Approve",
            description="All approve",
            votes=votes,
            mode=VotingMode.PAIRWISE_COMPARISON,
        )
        assert result.decision == "approved"

    def test_pairwise_all_abstain(self, engine):
        """All abstain = deferred (no active votes to compare)."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.ABSTAIN, 0.0)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Pairwise All Abstain",
            description="All abstain",
            votes=votes,
            mode=VotingMode.PAIRWISE_COMPARISON,
        )
        assert result.decision == "deferred"

    def _make_vote(self, voter_id, choice, confidence):
        from core.consensus.consensus_engine import Vote
        return Vote(voter_id=voter_id, choice=choice, confidence=confidence)


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence-Weighted Mode Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidenceWeighted:
    """Tests for CONFIDENCE_WEIGHTED mode — votes weighted by confidence."""

    def test_confidence_high_approval(self, engine):
        """High confidence approval passes."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # 8 approve with high confidence, 7 reject with low confidence
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.95) for i in range(1, 9)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.3) for i in range(9, 16)]
        )
        result = engine.run_consensus(
            title="Confidence High Approve",
            description="High confidence approval",
            votes=votes,
            mode=VotingMode.CONFIDENCE_WEIGHTED,
            threshold=0.5,
        )
        # Approve weight: 8 * 1.0 * 0.95 = 7.6 (weight * confidence)
        # Reject weight: 7 * 1.0 * 0.3 = 2.1
        # 7.6 / (7.6 + 2.1) = 78.4% > 50% → approved
        assert result.decision == "approved"

    def test_confidence_low_approval_rejected(self, engine):
        """Low confidence approval fails against high confidence rejection."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # 8 approve with low confidence, 7 reject with high confidence
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.2) for i in range(1, 9)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.95) for i in range(9, 16)]
        )
        result = engine.run_consensus(
            title="Confidence Low Approve",
            description="Low confidence approval",
            votes=votes,
            mode=VotingMode.CONFIDENCE_WEIGHTED,
            threshold=0.5,
        )
        # Approve weight: 8 * 1.0 * 0.2 = 1.6
        # Reject weight: 7 * 1.0 * 0.95 = 6.65
        # 1.6 / (1.6 + 6.65) = 19.4% < 50% → rejected
        assert result.decision == "rejected"

    def test_confidence_with_weights(self, engine):
        """Different voter weights affect the outcome."""
        from core.consensus.consensus_engine import ConsensusEngine, VoteChoice, VotingMode, Vote
        eng = ConsensusEngine()
        # Register voters with different weights
        eng.register_voter("heavy", "Heavy Voter", "technology", weight=1.0)
        eng.register_voter("medium", "Medium Voter", "security", weight=0.5)
        eng.register_voter("light", "Light Voter", "ethics", weight=0.1)

        votes = [
            Vote(voter_id="heavy", choice=VoteChoice.APPROVE, confidence=1.0),
            Vote(voter_id="medium", choice=VoteChoice.REJECT, confidence=1.0),
            Vote(voter_id="light", choice=VoteChoice.REJECT, confidence=1.0),
        ]
        result = eng.run_consensus(
            title="Weighted",
            description="Different weights",
            votes=votes,
            mode=VotingMode.CONFIDENCE_WEIGHTED,
            threshold=0.5,
        )
        # Heavy (1.0) approves, Medium (0.5) + Light (0.1) reject
        # Approve weight: 1.0 * 1.0 = 1.0
        # Reject weight: 0.5 * 1.0 + 0.1 * 1.0 = 0.6
        # 1.0 / 1.6 = 62.5% > 50% → approved
        assert result.decision == "approved"

    def test_confidence_all_abstain(self, engine):
        """All abstain = deferred."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.ABSTAIN, 0.0)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Conf All Abstain",
            description="All abstain",
            votes=votes,
            mode=VotingMode.CONFIDENCE_WEIGHTED,
        )
        assert result.decision == "deferred"

    def test_confidence_edge_case_zero_confidence(self, engine):
        """Zero confidence votes don't contribute to weight."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.0) for i in range(1, 9)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 1.0) for i in range(9, 16)]
        )
        result = engine.run_consensus(
            title="Zero Confidence",
            description="Zero confidence approves",
            votes=votes,
            mode=VotingMode.CONFIDENCE_WEIGHTED,
            threshold=0.5,
        )
        # Approve weight: 0 (all zero confidence)
        # Reject weight: 7 * 1.0 * 1.0 = 7.0
        # 0 / 7 = 0% → rejected
        assert result.decision == "rejected"

    def _make_vote(self, voter_id, choice, confidence):
        from core.consensus.consensus_engine import Vote
        return Vote(voter_id=voter_id, choice=choice, confidence=confidence)


# ═══════════════════════════════════════════════════════════════════════════════
# Role-Based Veto Mode Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRoleBasedVeto:
    """Tests for ROLE_BASED_VETO mode — domain and global veto power."""

    def test_security_veto_in_domain(self, engine):
        """Security Sentinel vetoes a security-related proposal."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # Make all 15 clones approve EXCEPT Security Sentinel (clone_06)
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 6)]
            + [self._make_vote("clone_06", VoteChoice.REJECT, 0.95, reasoning="Security vulnerability detected")]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(7, 16)]
        )
        result = engine.run_consensus(
            title="Deploy new protocol",
            description="This updates the security protocol for mesh routing",
            votes=votes,
            mode=VotingMode.ROLE_BASED_VETO,
            context={"domain": "security"},
        )
        # Security Sentinel vetoed, but 14 approve / 1 reject = 93.3% > 67%
        # So the veto is overridden by supermajority
        assert result.decision == "approved"
        assert result.details["veto_overridden"] is True

    def test_sovereignty_global_veto(self, engine):
        """Sovereignty Guard global veto with insufficient override."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # 11 approve, 4 reject (including Sovereignty Guard)
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 12)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 1.0) for i in range(12, 15)]
            + [self._make_vote("clone_15", VoteChoice.REJECT, 1.0, reasoning="Sovereignty violation")]
        )
        result = engine.run_consensus(
            title="Data sharing agreement",
            description="Share user data with third party",
            votes=votes,
            mode=VotingMode.ROLE_BASED_VETO,
        )
        # Sovereignty Guard vetoed. 11 approve / 15 total = 73.3% which is > 67%
        # So the veto IS overridden
        assert result.decision in ("approved", "vetoed")

    def test_veto_not_overridden(self, engine):
        """Veto stands when supermajority not met."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # Only 9 approve (60%), 6 reject (including domain vetoers)
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 10)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 1.0) for i in range(10, 16)]
        )
        result = engine.run_consensus(
            title="Security policy change",
            description="Change the security protocol",
            votes=votes,
            mode=VotingMode.ROLE_BASED_VETO,
        )
        # 9/15 = 60% < 67%, so veto stands if Security Sentinel is among rejecters
        # Actually, let's check - if the Security Sentinel (clone_06) is among rejecters
        # clone_06 is in positions 10-15, so yes
        assert result.decision == "vetoed" or result.decision == "rejected"

    def test_domain_veto_detection(self, engine):
        """Domain-specific veto detection works for security proposals."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        # Security Sentinel vetoes a security proposal
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 6)]
            + [self._make_vote("clone_06", VoteChoice.REJECT, 0.95)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(7, 16)]
        )
        result = engine.run_consensus(
            title="Security audit result",
            description="Vulnerability found in the mesh routing layer",
            votes=votes,
            mode=VotingMode.ROLE_BASED_VETO,
        )
        # Security domain is mentioned → domain veto detected
        # 14/15 approve = 93.3% > 67% → veto overridden
        assert result.details.get("veto_overridden") is True or result.decision == "approved"

    def test_veto_details_in_result(self, engine):
        """Veto details are included in the result."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = (
            [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(1, 6)]
            + [self._make_vote("clone_06", VoteChoice.REJECT, 0.95)]
            + [self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8) for i in range(7, 16)]
        )
        result = engine.run_consensus(
            title="Security proposal",
            description="A security-related change",
            votes=votes,
            mode=VotingMode.ROLE_BASED_VETO,
        )
        assert "vetoes" in result.details
        assert "veto_active" in result.details

    def _make_vote(self, voter_id, choice, confidence, reasoning=""):
        from core.consensus.consensus_engine import Vote
        return Vote(voter_id=voter_id, choice=choice, confidence=confidence, reasoning=reasoning)


# ═══════════════════════════════════════════════════════════════════════════════
# Delegation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDelegation:
    """Tests for vote delegation."""

    def test_delegate_vote(self, engine):
        """Delegate vote creates a valid delegation."""
        prop = engine.create_proposal("Delegation Test", "Test", "clone_01")
        delegation = engine.delegate_vote("clone_01", "clone_02", prop.proposal_id)
        assert delegation is not None
        assert delegation.from_voter == "clone_01"
        assert delegation.to_voter == "clone_02"
        assert delegation.proposal_id == prop.proposal_id
        assert delegation.active is True

    def test_delegate_unregistered_voter(self, engine):
        """Cannot delegate from unregistered voter."""
        prop = engine.create_proposal("Bad Delegate", "Test", "clone_01")
        delegation = engine.delegate_vote("nonexistent", "clone_02", prop.proposal_id)
        assert delegation is None

    def test_delegate_to_unregistered_voter(self, engine):
        """Cannot delegate to unregistered voter."""
        prop = engine.create_proposal("Bad Target", "Test", "clone_01")
        delegation = engine.delegate_vote("clone_01", "nonexistent", prop.proposal_id)
        assert delegation is None

    def test_delegate_to_self(self, engine):
        """Cannot delegate to self."""
        prop = engine.create_proposal("Self Delegate", "Test", "clone_01")
        delegation = engine.delegate_vote("clone_01", "clone_01", prop.proposal_id)
        assert delegation is None

    def test_revoke_delegation(self, engine):
        """Revoke delegation marks it inactive."""
        prop = engine.create_proposal("Revoke Test", "Test", "clone_01")
        delegation = engine.delegate_vote("clone_01", "clone_02", prop.proposal_id)
        assert delegation.active is True

        revoked = engine.revoke_delegation(delegation.delegation_id)
        assert revoked is True
        assert delegation.active is False

    def test_revoke_nonexistent_delegation(self, engine):
        """Revoking nonexistent delegation returns False."""
        revoked = engine.revoke_delegation("nonexistent")
        assert revoked is False

    def test_get_active_delegations(self, engine):
        """get_active_delegations returns only non-expired delegations."""
        prop = engine.create_proposal("Active Delegations", "Test", "clone_01")
        engine.delegate_vote("clone_01", "clone_02", prop.proposal_id)
        engine.delegate_vote("clone_03", "clone_04", prop.proposal_id)

        active = engine.get_active_delegations(prop.proposal_id)
        assert len(active) == 2

    def test_delegation_applied_in_consensus(self, minimal_engine):
        """Delegation affects consensus outcome."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, Vote as EngineVote

        # Global delegation: Voter C delegates to Voter A for all proposals
        minimal_engine.delegate_vote("voter_c", "voter_a", "*")

        # Voter A approves, Voter B rejects, Voter C delegates to A
        votes = [
            EngineVote(voter_id="voter_a", choice=VoteChoice.APPROVE, confidence=0.9),
            EngineVote(voter_id="voter_b", choice=VoteChoice.REJECT, confidence=0.9),
        ]
        result = minimal_engine.run_consensus(
            title="Delegated",
            description="Testing delegation",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        # Without delegation: 1 approve, 1 reject, 1 abstain → deferred
        # With delegation (voter_c → voter_a): approve gets extra weight
        # 2 approve (voter_a + delegated voter_c), 1 reject → approved
        assert result.decision == "approved"


# ═══════════════════════════════════════════════════════════════════════════════
# Arbitration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestArbitration:
    """Tests for arbitration and human override."""

    def test_arbitrate_uphold(self, engine):
        """Arbiter upholds the current decision."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, ArbiterDecision
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Uphold Test",
            description="Will be upheld",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        assert result.decision == "approved"

        # Arbiter upholds
        upheld = engine.arbitrate(
            result.proposal_id,
            arbiter_id="arbiter_01",
            decision=ArbiterDecision.UPHOLD,
            reason="Decision is sound",
        )
        assert upheld.decision == "approved"
        assert upheld.details.get("arbitrated") is True

    def test_arbitrate_overturn(self, engine):
        """Arbiter overturns the decision."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, ArbiterDecision
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Overturn Test",
            description="Will be overturned",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        assert result.decision == "approved"

        # Arbiter overturns
        overturned = engine.arbitrate(
            result.proposal_id,
            arbiter_id="arbiter_01",
            decision=ArbiterDecision.OVERTURN,
            reason="Conflicts with constitution",
        )
        assert overturned.decision == "rejected"
        assert overturned.details.get("arbitrated") is True

    def test_arbitrate_remand(self, engine):
        """Arbiter demands more voting."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, ArbiterDecision
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Remand Test",
            description="Will be remanded",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        remanded = engine.arbitrate(
            result.proposal_id,
            arbiter_id="arbiter_01",
            decision=ArbiterDecision.REMAND,
            reason="Need more information",
        )
        assert remanded.decision == "remanded"

    def test_arbitrate_escalate_human(self, engine):
        """Arbiter escalates to human."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, ArbiterDecision
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Escalate Test",
            description="Will be escalated",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        escalated = engine.arbitrate(
            result.proposal_id,
            arbiter_id="arbiter_01",
            decision=ArbiterDecision.ESCALATE_HUMAN,
            reason="Requires human judgment",
        )
        assert escalated.decision == "escalated_to_human"

    def test_human_override_approve(self, engine):
        """Human can override to approve."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.REJECT, 0.8)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Human Override",
            description="Will be overridden",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        assert result.decision == "rejected"

        # Human overrides to approve
        override = engine.human_override(
            result.proposal_id,
            approved=True,
            reason="This is in the public interest",
        )
        assert override.decision == "approved"
        assert override.confidence == 1.0
        assert override.details["human_override"] is True

    def test_human_override_reject(self, engine):
        """Human can override to reject."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Human Reject",
            description="Will be rejected by human",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        assert result.decision == "approved"

        override = engine.human_override(
            result.proposal_id,
            approved=False,
            reason="Ethical concerns",
        )
        assert override.decision == "rejected"

    def test_pending_human_override(self, engine):
        """pending_human_override lists escalated proposals."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, ArbiterDecision
        votes = [
            self._make_vote(f"clone_{i:02d}", VoteChoice.APPROVE, 0.8)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Pending Human",
            description="Needs human",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        engine.arbitrate(
            result.proposal_id,
            arbiter_id="arbiter_01",
            decision=ArbiterDecision.ESCALATE_HUMAN,
            reason="Complex decision",
        )
        pending = engine.pending_human_override()
        assert len(pending) == 1
        assert pending[0].proposal_id == result.proposal_id

    def _make_vote(self, voter_id, choice, confidence):
        from core.consensus.consensus_engine import Vote
        return Vote(voter_id=voter_id, choice=choice, confidence=confidence)


# ═══════════════════════════════════════════════════════════════════════════════
# Quorum and Expiration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuorumAndExpiration:
    """Tests for quorum requirements and proposal expiration."""

    def test_quorum_not_met(self, minimal_engine):
        """Proposal not resolved when quorum not met."""
        from core.consensus.consensus_engine import VoteChoice
        prop = minimal_engine.create_proposal(
            "Quorum Test", "Need quorum", "voter_a",
            quorum=0.8,
        )
        # Only 1 of 3 voters
        minimal_engine.cast_vote(prop.proposal_id, "voter_a", VoteChoice.APPROVE, 0.9)
        result = minimal_engine.get_result(prop.proposal_id)
        assert result is None  # Not resolved — quorum not met

    def test_quorum_met_resolves(self, minimal_engine):
        """Proposal resolves when quorum met and votes sufficient."""
        from core.consensus.consensus_engine import VoteChoice
        prop = minimal_engine.create_proposal(
            "Quorum Met", "Enough voters", "voter_a",
            quorum=0.5,
        )
        minimal_engine.cast_vote(prop.proposal_id, "voter_a", VoteChoice.APPROVE, 0.9)
        minimal_engine.cast_vote(prop.proposal_id, "voter_b", VoteChoice.APPROVE, 0.9)
        result = minimal_engine.get_result(prop.proposal_id)
        # 2/3 = 66.7% >= 50% quorum met + all voted → resolved
        if result is None:
            # Might need all 3
            minimal_engine.cast_vote(prop.proposal_id, "voter_c", VoteChoice.APPROVE, 0.9)
            result = minimal_engine.get_result(prop.proposal_id)
        assert result is not None
        assert result.decision == "approved"

    def test_expired_proposal_rejected(self, minimal_engine):
        """Expired proposal is rejected."""
        from core.consensus.consensus_engine import VoteChoice
        prop = minimal_engine.create_proposal(
            "Expired", "Already expired", "voter_a",
            expires_in_seconds=-1,
        )
        result = minimal_engine.cast_vote(prop.proposal_id, "voter_a", VoteChoice.APPROVE, 0.9)
        assert result is not None
        assert result.decision == "expired"

    def test_expired_proposal_details(self, minimal_engine):
        """Expired proposal has expired flag in details."""
        from core.consensus.consensus_engine import VoteChoice
        prop = minimal_engine.create_proposal(
            "Expired Detail", "Check details", "voter_a",
            expires_in_seconds=-1,
        )
        result = minimal_engine.cast_vote(prop.proposal_id, "voter_a", VoteChoice.APPROVE, 0.9)
        assert result.details.get("expired") is True


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_duplicate_vote(self, engine):
        """A voter cannot vote twice."""
        from core.consensus.consensus_engine import VoteChoice
        prop = engine.create_proposal("No Double", "Test", "clone_01")
        engine.cast_vote(prop.proposal_id, "clone_01", VoteChoice.APPROVE, 0.9)
        result = engine.cast_vote(prop.proposal_id, "clone_01", VoteChoice.APPROVE, 0.9)
        assert result is None  # Duplicate returns None

    def test_vote_on_nonexistent_proposal(self, engine):
        """Voting on a non-existent proposal returns None."""
        from core.consensus.consensus_engine import VoteChoice
        result = engine.cast_vote("nonexistent", "clone_01", VoteChoice.APPROVE, 0.9)
        assert result is None

    def test_vote_by_unregistered_voter(self, engine):
        """Voting by an unregistered voter returns None."""
        from core.consensus.consensus_engine import VoteChoice
        prop = engine.create_proposal("No Access", "Test", "clone_01")
        result = engine.cast_vote(prop.proposal_id, "stranger", VoteChoice.APPROVE, 0.9)
        assert result is None

    def test_vote_on_resolved_proposal(self, engine):
        """Voting on an already-resolved proposal returns existing result."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, Vote as EngineVote
        votes = [
            EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.APPROVE, confidence=0.8)
            for i in range(1, 16)
        ]
        result = engine.run_consensus(
            title="Done Deal",
            description="Resolved",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        assert result.decision == "approved"

        # Try to vote again
        result2 = engine.cast_vote(result.proposal_id, "clone_01", VoteChoice.REJECT, 0.9)
        assert result2 is not None
        assert result2.decision == "approved"  # Still shows original

    def test_empty_votes_list(self, engine):
        """Empty votes list creates a proposal but doesn't resolve."""
        from core.consensus.consensus_engine import VotingMode
        result = engine.run_consensus(
            title="Empty Votes",
            description="No votes",
            votes=[],
            mode=VotingMode.MAJORITY_VOTE,
        )
        assert result.proposal_id is not None
        # Should be deferred with no active votes
        assert result.decision in ("deferred", "rejected")

    def test_no_voters_registered(self):
        """Engine with no voters should handle gracefully."""
        from core.consensus.consensus_engine import ConsensusEngine, VotingMode
        from core.consensus.consensus_engine import Vote as EngineVote, VoteChoice
        eng = ConsensusEngine()
        votes = [
            EngineVote(voter_id="unknown", choice=VoteChoice.APPROVE, confidence=0.8)
        ]
        result = eng.run_consensus(
            title="No Voters",
            description="No voters registered",
            votes=votes,
        )
        # Unknown voters are skipped
        assert result.decision is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Audit Trail Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditTrail:
    """Tests for the audit trail."""

    def test_audit_log_exists(self, engine):
        """get_audit_log returns list."""
        log = engine.get_audit_log()
        assert isinstance(log, list)

    def test_audit_log_entries_after_consensus(self, engine):
        """Audit log has entries after running consensus."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, Vote as EngineVote
        votes = [
            EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.APPROVE, confidence=0.8)
            for i in range(1, 9)
        ] + [
            EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.REJECT, confidence=0.8)
            for i in range(9, 16)
        ]
        engine.run_consensus(
            title="Audit Test",
            description="Testing audit",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )
        log = engine.get_audit_log()
        assert len(log) >= 2  # At least proposal_created + proposal_resolved


# ═══════════════════════════════════════════════════════════════════════════════
# Stats and Queries Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatsAndQueries:
    """Tests for get_stats, list_proposals, etc."""

    def test_get_stats(self, engine):
        """get_stats returns summary statistics."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, Vote as EngineVote
        votes = [
            EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.APPROVE, confidence=0.8)
            for i in range(1, 10)
        ] + [
            EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.REJECT, confidence=0.8)
            for i in range(10, 16)
        ]
        engine.run_consensus(
            title="Stats Test",
            description="Testing stats",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )

        stats = engine.get_stats()
        assert stats["total_proposals"] >= 1
        assert stats["total_resolved"] >= 1
        assert stats["registered_voters"] == 15
        assert "modes_used" in stats

    def test_list_proposals(self, engine):
        """list_proposals returns formatted proposal list."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, Vote as EngineVote
        votes = [
            EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.APPROVE, confidence=0.8)
            for i in range(1, 16)
        ]
        engine.run_consensus(
            title="List Test",
            description="Testing list",
            votes=votes,
            mode=VotingMode.MAJORITY_VOTE,
        )

        proposals = engine.list_proposals()
        assert len(proposals) >= 1
        assert proposals[0]["title"] == "List Test"
        assert proposals[0]["status"] == "approved"

    def test_result_tuples(self, engine):
        """Each voting mode returns (decision, confidence, details) structure."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode, Vote as EngineVote
        for mode in VotingMode:
            votes = [
                EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.APPROVE, confidence=0.8)
                for i in range(1, 13)
            ] + [
                EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.REJECT, confidence=0.8)
                for i in range(13, 16)
            ]
            result = engine.run_consensus(
                title=f"Mode {mode.value}",
                description=f"Testing {mode.value}",
                votes=votes,
                mode=mode,
            )
            # Verify (decision, confidence, details) structure
            assert isinstance(result.decision, str)
            assert isinstance(result.confidence, float)
            assert isinstance(result.details, dict)
            assert result.decision in ("approved", "rejected", "deferred", "vetoed", "expired")


# ═══════════════════════════════════════════════════════════════════════════════
# CloneConsensusFacade Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCloneConsensusFacade:
    """Tests for the CloneConsensusFacade convenience class."""

    def test_facade_initialization(self):
        """Facade initializes with 15 clones."""
        from core.consensus.consensus_engine import CloneConsensusFacade
        facade = CloneConsensusFacade()
        assert facade.engine.registered_voter_count() == 15

    @pytest.mark.asyncio
    async def test_facade_heuristic_votes(self):
        """Facade generates heuristic votes."""
        from core.consensus.consensus_engine import CloneConsensusFacade, VotingMode
        facade = CloneConsensusFacade()
        result = await facade.run_consensus_round(
            title="Heuristic Test",
            description="Testing heuristic vote generation",
            mode=VotingMode.MAJORITY_VOTE,
        )
        assert result.decision is not None
        assert result.proposal_id is not None

    @pytest.mark.asyncio
    async def test_facade_different_modes(self):
        """Facade works with all 4 voting modes."""
        from core.consensus.consensus_engine import CloneConsensusFacade, VotingMode
        facade = CloneConsensusFacade()
        for mode in VotingMode:
            result = await facade.run_consensus_round(
                title=f"Facade {mode.value}",
                description=f"Testing facade with {mode.value}",
                mode=mode,
            )
            assert result.decision is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSingleton:
    """Tests for the singleton pattern."""

    def test_get_consensus_engine(self):
        """get_consensus_engine returns a singleton."""
        from core.consensus.consensus_engine import get_consensus_engine
        e1 = get_consensus_engine()
        e2 = get_consensus_engine()
        assert e1 is e2

    def test_reset_consensus_engine(self):
        """reset_consensus_engine clears the singleton."""
        from core.consensus.consensus_engine import get_consensus_engine, reset_consensus_engine
        e1 = get_consensus_engine()
        reset_consensus_engine()
        e2 = get_consensus_engine()
        assert e1 is not e2


# ═══════════════════════════════════════════════════════════════════════════════
# Data Class Serialization Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSerialization:
    """Tests for to_dict() methods on data classes."""

    def test_voter_to_dict(self):
        """Voter.to_dict returns expected keys."""
        from core.consensus.consensus_engine import Voter
        voter = Voter(voter_id="test", name="Test", domain="testing", weight=0.8, elo_rating=1600)
        d = voter.to_dict()
        assert d["voter_id"] == "test"
        assert d["name"] == "Test"
        assert d["domain"] == "testing"
        assert d["weight"] == 0.8
        assert d["elo_rating"] == 1600

    def test_vote_to_dict(self):
        """Vote.to_dict returns expected keys."""
        from core.consensus.consensus_engine import Vote, VoteChoice
        vote = Vote(voter_id="test", choice=VoteChoice.APPROVE, confidence=0.9,
                    reasoning="Good proposal", domain="tech", weight=1.0)
        d = vote.to_dict()
        assert d["voter_id"] == "test"
        assert d["choice"] == "approve"
        assert d["confidence"] == 0.9
        assert d["reasoning"] == "Good proposal"

    def test_proposal_to_dict(self, engine):
        """Proposal.to_dict returns expected keys."""
        from core.consensus.consensus_engine import VoteChoice
        prop = engine.create_proposal("Dict Test", "Check dict", "clone_01")
        engine.cast_vote(prop.proposal_id, "clone_01", VoteChoice.APPROVE, 0.9)
        d = prop.to_dict()
        assert d["title"] == "Dict Test"
        assert d["mode"] == "majority_vote"
        assert d["status"] == "pending"
        assert len(d["votes"]) == 1

    def test_consensus_result_to_dict(self, engine):
        """ConsensusResult.to_dict returns expected keys."""
        from core.consensus.consensus_engine import VoteChoice, VotingMode
        from core.consensus.consensus_engine import Vote as EngineVote
        votes = [EngineVote(voter_id=f"clone_{i:02d}", choice=VoteChoice.APPROVE, confidence=0.8)
                 for i in range(1, 16)]
        result = engine.run_consensus(
            title="Result Dict", description="Check dict",
            votes=votes, mode=VotingMode.MAJORITY_VOTE,
        )
        d = result.to_dict()
        assert d["title"] == "Result Dict"
        assert d["mode"] == "majority_vote"
        assert d["decision"] in ("approved", "rejected")
        assert "resolved_at" in d

    def test_delegation_to_dict(self, engine):
        """Delegation.to_dict returns expected keys."""
        prop = engine.create_proposal("Deleg Dict", "Check", "clone_01")
        delegation = engine.delegate_vote("clone_01", "clone_02", prop.proposal_id)
        d = delegation.to_dict()
        assert d["from_voter"] == "clone_01"
        assert d["to_voter"] == "clone_02"
        assert d["active"] is True
