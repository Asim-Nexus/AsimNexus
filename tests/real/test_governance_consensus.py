#!/usr/bin/env python3
"""
tests/real/test_governance_consensus.py
AsimNexus — Governance & Consensus Engine Tests

Tests for core/governance/consensus.py:
  - ConsensusType and ProposalStatus enums
  - Proposal, Vote, GovernanceMember dataclasses
  - GovernanceEngine: member management, proposal lifecycle, voting,
    quorum calculation, delegation, statistics
"""

import os
import time
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from core.governance.consensus import (
    ConsensusType,
    ProposalStatus,
    Proposal,
    Vote,
    GovernanceMember,
    GovernanceEngine,
    get_governance,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_env():
    """Reset env vars before/after each test."""
    saved = {}
    for key in ("ASIM_GOV_QUORUM_PERCENT", "ASIM_GOV_VOTING_PERIOD_HOURS", "ASIM_GOV_MIN_VOTING_WEIGHT"):
        saved[key] = os.environ.pop(key, None)
    yield
    for key, val in saved.items():
        if val is not None:
            os.environ[key] = val
        else:
            os.environ.pop(key, None)
    # Reset singleton
    import core.governance.consensus as gov_mod
    gov_mod._governance = None


# ── ConsensusType Enum Tests ────────────────────────────────────────────────

class TestConsensusType:
    """ConsensusType enum values."""

    def test_values(self):
        assert ConsensusType.MAJORITY_VOTE.value == "majority_vote"
        assert ConsensusType.QUORUM.value == "quorum"
        assert ConsensusType.WEIGHTED_VOTE.value == "weighted_vote"
        assert ConsensusType.DELEGATED.value == "delegated"
        assert ConsensusType.CONSENSUS.value == "consensus"

    def test_distinct(self):
        values = {c.value for c in ConsensusType}
        assert len(values) == 5


# ── ProposalStatus Enum Tests ──────────────────────────────────────────────

class TestProposalStatus:
    """ProposalStatus enum values."""

    def test_values(self):
        assert ProposalStatus.DRAFT.value == "draft"
        assert ProposalStatus.ACTIVE.value == "active"
        assert ProposalStatus.PASSED.value == "passed"
        assert ProposalStatus.REJECTED.value == "rejected"
        assert ProposalStatus.EXECUTED.value == "executed"

    def test_distinct(self):
        values = {p.value for p in ProposalStatus}
        assert len(values) == 5

    def test_lifecycle_order(self):
        """Verify lifecycle: DRAFT → ACTIVE → PASSED/REJECTED → EXECUTED."""
        assert ProposalStatus.DRAFT.value == "draft"
        assert ProposalStatus.ACTIVE.value == "active"
        assert ProposalStatus.PASSED.value == "passed"


# ── Proposal Dataclass Tests ────────────────────────────────────────────────

class TestProposal:
    """Proposal dataclass creation and defaults."""

    def test_create(self):
        prop = Proposal(
            proposal_id="prop_001",
            title="Test Proposal",
            description="A test governance proposal",
            proposer="member_001",
            consensus_type=ConsensusType.MAJORITY_VOTE,
            quorum_required=51,
            voting_period_hours=72,
            status=ProposalStatus.DRAFT,
        )
        assert prop.proposal_id == "prop_001"
        assert prop.title == "Test Proposal"
        assert prop.votes_for == 0
        assert prop.votes_against == 0
        assert prop.votes_abstain == 0
        assert prop.created_at is not None
        assert prop.voting_ends_at is None
        assert prop.executed_at is None


# ── Vote Dataclass Tests ────────────────────────────────────────────────────

class TestVote:
    """Vote dataclass creation and defaults."""

    def test_create(self):
        vote = Vote(
            vote_id="vote_001",
            proposal_id="prop_001",
            voter="member_001",
            decision="for",
        )
        assert vote.vote_id == "vote_001"
        assert vote.weight == 1.0
        assert vote.timestamp is not None

    def test_create_with_weight(self):
        vote = Vote(
            vote_id="vote_002",
            proposal_id="prop_001",
            voter="member_002",
            decision="against",
            weight=2.5,
        )
        assert vote.weight == 2.5


# ── GovernanceMember Dataclass Tests ────────────────────────────────────────

class TestGovernanceMember:
    """GovernanceMember dataclass creation and defaults."""

    def test_create(self):
        member = GovernanceMember(
            member_id="m_001",
            address="addr_001",
            voting_weight=1.0,
            reputation_score=1.0,
        )
        assert member.member_id == "m_001"
        assert member.address == "addr_001"
        assert member.joined_at is not None

    def test_create_with_high_weight(self):
        member = GovernanceMember(
            member_id="m_002",
            address="addr_002",
            voting_weight=10.0,
            reputation_score=0.5,
        )
        assert member.voting_weight == 10.0
        assert member.reputation_score == 0.5


# ── GovernanceEngine Tests ─────────────────────────────────────────────────

class TestGovernanceEngine:
    """GovernanceEngine core functionality tests."""

    # ── Initialization ──────────────────────────────────────────────────────

    def test_init(self):
        engine = GovernanceEngine()
        assert engine.proposals == {}
        assert engine.votes == {}
        assert engine.members == {}
        assert engine.default_quorum_percent == 51
        assert engine.default_voting_period_hrs == 72
        assert engine.default_min_voting_weight == 1.0

    def test_init_with_custom_values(self):
        engine = GovernanceEngine(
            quorum_percent=60,
            voting_period_hours=48,
            min_voting_weight=0.5,
        )
        assert engine.default_quorum_percent == 60
        assert engine.default_voting_period_hrs == 48
        assert engine.default_min_voting_weight == 0.5

    def test_init_with_env_vars(self):
        os.environ["ASIM_GOV_QUORUM_PERCENT"] = "75"
        os.environ["ASIM_GOV_VOTING_PERIOD_HOURS"] = "24"
        os.environ["ASIM_GOV_MIN_VOTING_WEIGHT"] = "2.0"
        engine = GovernanceEngine()
        assert engine.default_quorum_percent == 75
        assert engine.default_voting_period_hrs == 24
        assert engine.default_min_voting_weight == 2.0

    def test_init_explicit_overrides_env(self):
        os.environ["ASIM_GOV_QUORUM_PERCENT"] = "99"
        engine = GovernanceEngine(quorum_percent=50)
        assert engine.default_quorum_percent == 50

    # ── Member Management ───────────────────────────────────────────────────

    def test_add_member(self):
        engine = GovernanceEngine()
        member = engine.add_member("addr_001", voting_weight=2.0, reputation_score=1.5)
        assert member.member_id.startswith("member_")
        assert member.address == "addr_001"
        assert member.voting_weight == 2.0
        assert member.reputation_score == 1.5
        assert member.member_id in engine.members

    def test_add_member_defaults(self):
        engine = GovernanceEngine()
        member = engine.add_member("addr_default")
        assert member.voting_weight == 1.0
        assert member.reputation_score == 1.0

    def test_add_multiple_members(self):
        engine = GovernanceEngine()
        m1 = engine.add_member("addr_1")
        m2 = engine.add_member("addr_2")
        m3 = engine.add_member("addr_3")
        assert len(engine.members) == 3
        assert m1.member_id != m2.member_id
        assert m2.member_id != m3.member_id

    # ── Proposal Creation ───────────────────────────────────────────────────

    def test_create_proposal(self):
        engine = GovernanceEngine()
        engine.add_member("proposer_addr")
        proposer = list(engine.members.values())[0]
        prop = engine.create_proposal(
            title="Increase quorum",
            description="Should we increase quorum to 60%?",
            proposer=proposer.member_id,
            consensus_type=ConsensusType.WEIGHTED_VOTE,
        )
        assert prop.proposal_id.startswith("prop_")
        assert prop.title == "Increase quorum"
        assert prop.status == ProposalStatus.DRAFT
        assert prop.consensus_type == ConsensusType.WEIGHTED_VOTE
        assert prop.quorum_required == 51
        assert prop.voting_period_hours == 72

    def test_create_proposal_custom_quorum(self):
        engine = GovernanceEngine()
        prop = engine.create_proposal(
            title="Custom quorum",
            description="Test",
            proposer="member_x",
            quorum_required=75,
            voting_period_hours=24,
        )
        assert prop.quorum_required == 75
        assert prop.voting_period_hours == 24

    def test_create_multiple_proposals(self):
        engine = GovernanceEngine()
        p1 = engine.create_proposal("P1", "D1", "proposer_a")
        p2 = engine.create_proposal("P2", "D2", "proposer_b")
        assert len(engine.proposals) == 2
        assert p1.proposal_id != p2.proposal_id

    # ── Proposal Activation ─────────────────────────────────────────────────

    def test_activate_proposal(self):
        engine = GovernanceEngine()
        prop = engine.create_proposal("Activate test", "Testing activation", "proposer")
        result = engine.activate_proposal(prop.proposal_id)
        assert result is True
        activated = engine.proposals[prop.proposal_id]
        assert activated.status == ProposalStatus.ACTIVE
        assert activated.voting_ends_at is not None

    def test_activate_nonexistent_proposal(self):
        engine = GovernanceEngine()
        result = engine.activate_proposal("nonexistent")
        assert result is False

    def test_activate_proposal_sets_deadline(self):
        engine = GovernanceEngine()
        prop = engine.create_proposal(
            "Deadline test", "Testing deadline", "proposer",
            voting_period_hours=1,
        )
        engine.activate_proposal(prop.proposal_id)
        activated = engine.proposals[prop.proposal_id]
        expected_end = activated.created_at + timedelta(hours=1)
        assert activated.voting_ends_at is not None
        assert abs((activated.voting_ends_at - expected_end).total_seconds()) < 1

    # ── Voting ──────────────────────────────────────────────────────────────

    def test_cast_vote_for(self):
        engine = GovernanceEngine()
        engine.add_member("voter_addr", voting_weight=1.0)
        prop = engine.create_proposal("Vote test", "Testing votes", "proposer")
        engine.activate_proposal(prop.proposal_id)
        vote = engine.cast_vote(prop.proposal_id, "voter_addr", "for")
        assert vote.decision == "for"
        assert vote.weight == 1.0
        assert engine.proposals[prop.proposal_id].votes_for == 1.0

    def test_cast_vote_against(self):
        engine = GovernanceEngine()
        engine.add_member("voter_addr", voting_weight=2.0)
        prop = engine.create_proposal("Against test", "Testing against", "proposer")
        engine.activate_proposal(prop.proposal_id)
        vote = engine.cast_vote(prop.proposal_id, "voter_addr", "against")
        assert vote.decision == "against"
        assert engine.proposals[prop.proposal_id].votes_against == 2.0

    def test_cast_vote_abstain(self):
        engine = GovernanceEngine()
        engine.add_member("voter_addr", voting_weight=1.5)
        prop = engine.create_proposal("Abstain test", "Testing abstain", "proposer")
        engine.activate_proposal(prop.proposal_id)
        vote = engine.cast_vote(prop.proposal_id, "voter_addr", "abstain")
        assert vote.decision == "abstain"
        assert engine.proposals[prop.proposal_id].votes_abstain == 1.5

    def test_cast_vote_nonexistent_proposal_raises(self):
        engine = GovernanceEngine()
        with pytest.raises(ValueError, match="not found"):
            engine.cast_vote("nonexistent", "voter", "for")

    def test_cast_vote_with_explicit_weight(self):
        engine = GovernanceEngine()
        engine.add_member("voter_addr", voting_weight=1.0)
        prop = engine.create_proposal("Weight test", "Testing weight", "proposer")
        engine.activate_proposal(prop.proposal_id)
        vote = engine.cast_vote(prop.proposal_id, "voter_addr", "for", weight=5.0)
        assert vote.weight == 5.0
        assert engine.proposals[prop.proposal_id].votes_for == 5.0

    def test_cast_vote_unknown_voter_uses_default_weight(self):
        engine = GovernanceEngine()
        prop = engine.create_proposal("Unknown voter", "Testing unknown voter", "proposer")
        engine.activate_proposal(prop.proposal_id)
        vote = engine.cast_vote(prop.proposal_id, "unknown_voter", "for")
        assert vote.weight == 1.0  # default_min_voting_weight

    def test_multiple_votes_on_proposal(self):
        engine = GovernanceEngine()
        for i in range(3):
            engine.add_member(f"voter_{i}", voting_weight=1.0 + i)
        prop = engine.create_proposal("Multi vote", "Multiple votes", "proposer")
        engine.activate_proposal(prop.proposal_id)

        engine.cast_vote(prop.proposal_id, "voter_0", "for")
        engine.cast_vote(prop.proposal_id, "voter_1", "against")
        engine.cast_vote(prop.proposal_id, "voter_2", "for")

        p = engine.proposals[prop.proposal_id]
        assert p.votes_for == 2.0 + 2.0  # voter_0=1.0, voter_2=3.0... wait, let me recalculate
        # voter_0 has weight=1.0, votes "for" → votes_for = 1.0
        # voter_1 has weight=2.0, votes "against" → votes_against = 2.0
        # voter_2 has weight=3.0, votes "for" → votes_for = 1.0 + 3.0 = 4.0
        assert p.votes_for == 4.0
        assert p.votes_against == 2.0

    # ── Consensus Calculation ───────────────────────────────────────────────

    def test_calculate_consensus_no_votes(self):
        engine = GovernanceEngine()
        prop = engine.create_proposal("No votes", "No votes yet", "proposer")
        result = engine.calculate_consensus(prop.proposal_id)
        assert result["status"] == "no_votes"

    def test_calculate_consensus_nonexistent(self):
        engine = GovernanceEngine()
        result = engine.calculate_consensus("nonexistent")
        assert "error" in result

    def test_consensus_reached(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        engine.add_member("voter_b", voting_weight=10.0)
        prop = engine.create_proposal("Consensus test", "Should pass", "proposer")
        engine.activate_proposal(prop.proposal_id)

        engine.cast_vote(prop.proposal_id, "voter_a", "for")
        engine.cast_vote(prop.proposal_id, "voter_b", "for")

        result = engine.calculate_consensus(prop.proposal_id)
        assert result["consensus_reached"] is True
        # total_weight = 10+10 = 20, votes_for = 10+10 = 20
        # for_percentage = (20/20)*100 = 100%
        assert result["for_percentage"] == 100.0
        assert result["quorum_met"] is True

    def test_consensus_not_reached(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        engine.add_member("voter_b", voting_weight=10.0)
        engine.add_member("voter_c", voting_weight=10.0)
        prop = engine.create_proposal(
            "Fail test", "Should fail", "proposer",
            quorum_required=51,
        )
        engine.activate_proposal(prop.proposal_id)

        engine.cast_vote(prop.proposal_id, "voter_a", "for")
        # Only 1/3 voted, total weight = 30, for = 10
        # for_percentage = (10/30)*100 = 33.3%
        # quorum = (10/30)*100 = 33.3% < 51%

        result = engine.calculate_consensus(prop.proposal_id)
        assert result["consensus_reached"] is False
        assert result["quorum_met"] is False

    def test_consensus_quorum_met_but_for_below_50(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        engine.add_member("voter_b", voting_weight=10.0)
        engine.add_member("voter_c", voting_weight=10.0)
        engine.add_member("voter_d", voting_weight=10.0)
        prop = engine.create_proposal(
            "Quorum met but not for", "Test", "proposer",
            quorum_required=50,
        )
        engine.activate_proposal(prop.proposal_id)

        engine.cast_vote(prop.proposal_id, "voter_a", "for")
        engine.cast_vote(prop.proposal_id, "voter_b", "against")
        engine.cast_vote(prop.proposal_id, "voter_c", "against")

        # total_weight = 40, votes_for = 10
        # for_percentage = (10/40)*100 = 25%
        # quorum = (30/40)*100 = 75% >= 50%
        result = engine.calculate_consensus(prop.proposal_id)
        assert result["quorum_met"] is True
        assert result["consensus_reached"] is False

    # ── Proposal Finalization ──────────────────────────────────────────────

    def test_finalize_proposal_passed(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        engine.add_member("voter_b", voting_weight=10.0)
        prop = engine.create_proposal("Finalize pass", "Should pass", "proposer")
        engine.activate_proposal(prop.proposal_id)

        engine.cast_vote(prop.proposal_id, "voter_a", "for")
        engine.cast_vote(prop.proposal_id, "voter_b", "for")

        result = engine.finalize_proposal(prop.proposal_id)
        assert result is True
        assert engine.proposals[prop.proposal_id].status == ProposalStatus.PASSED
        assert engine.proposals[prop.proposal_id].executed_at is not None

    def test_finalize_proposal_rejected(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        prop = engine.create_proposal("Finalize reject", "Should reject", "proposer")
        engine.activate_proposal(prop.proposal_id)

        engine.cast_vote(prop.proposal_id, "voter_a", "against")

        result = engine.finalize_proposal(prop.proposal_id)
        assert result is True
        assert engine.proposals[prop.proposal_id].status == ProposalStatus.REJECTED

    def test_finalize_nonexistent_proposal(self):
        engine = GovernanceEngine()
        result = engine.finalize_proposal("nonexistent")
        assert result is False

    # ── Proposal Execution ──────────────────────────────────────────────────

    def test_execute_passed_proposal(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        engine.add_member("voter_b", voting_weight=10.0)
        prop = engine.create_proposal("Execute test", "Should execute", "proposer")
        engine.activate_proposal(prop.proposal_id)
        engine.cast_vote(prop.proposal_id, "voter_a", "for")
        engine.cast_vote(prop.proposal_id, "voter_b", "for")
        engine.finalize_proposal(prop.proposal_id)

        result = engine.execute_proposal(prop.proposal_id)
        assert result is True
        assert engine.proposals[prop.proposal_id].status == ProposalStatus.EXECUTED

    def test_execute_non_passed_proposal(self):
        engine = GovernanceEngine()
        prop = engine.create_proposal("No execute", "Should not execute", "proposer")
        result = engine.execute_proposal(prop.proposal_id)
        assert result is False

    def test_execute_nonexistent_proposal(self):
        engine = GovernanceEngine()
        result = engine.execute_proposal("nonexistent")
        assert result is False

    # ── Query Methods ──────────────────────────────────────────────────────

    def test_get_proposal(self):
        engine = GovernanceEngine()
        prop = engine.create_proposal("Get test", "Testing get", "proposer")
        retrieved = engine.get_proposal(prop.proposal_id)
        assert retrieved is not None
        assert retrieved.proposal_id == prop.proposal_id

    def test_get_proposal_nonexistent(self):
        engine = GovernanceEngine()
        assert engine.get_proposal("nonexistent") is None

    def test_get_active_proposals(self):
        engine = GovernanceEngine()
        p1 = engine.create_proposal("Active 1", "D1", "proposer")
        p2 = engine.create_proposal("Active 2", "D2", "proposer")
        p3 = engine.create_proposal("Draft", "Draft prop", "proposer")

        engine.activate_proposal(p1.proposal_id)
        engine.activate_proposal(p2.proposal_id)

        active = engine.get_active_proposals()
        assert len(active) == 2
        assert all(p.status == ProposalStatus.ACTIVE for p in active)

    def test_get_active_proposals_empty(self):
        engine = GovernanceEngine()
        assert engine.get_active_proposals() == []

    def test_get_member_votes(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=1.0)
        prop = engine.create_proposal("Member votes", "Test", "proposer")
        engine.activate_proposal(prop.proposal_id)
        engine.cast_vote(prop.proposal_id, "voter_a", "for")

        votes = engine.get_member_votes("voter_a")
        assert len(votes) == 1
        assert votes[0].voter == "voter_a"

    def test_get_member_votes_no_votes(self):
        engine = GovernanceEngine()
        assert engine.get_member_votes("unknown_voter") == []

    # ── Statistics ──────────────────────────────────────────────────────────

    def test_get_governance_stats_empty(self):
        engine = GovernanceEngine()
        stats = engine.get_governance_stats()
        assert stats["total_proposals"] == 0
        assert stats["total_members"] == 0
        assert stats["total_votes"] == 0
        assert stats["active_proposals"] == 0

    def test_get_governance_stats_with_data(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a")
        p1 = engine.create_proposal("Prop 1", "D1", "proposer")
        p2 = engine.create_proposal("Prop 2", "D2", "proposer")
        engine.activate_proposal(p1.proposal_id)
        engine.cast_vote(p1.proposal_id, "voter_a", "for")

        stats = engine.get_governance_stats()
        assert stats["total_proposals"] == 2
        assert stats["total_members"] == 1
        assert stats["total_votes"] == 1
        assert stats["active_proposals"] == 1

    def test_get_stats_alias(self):
        engine = GovernanceEngine(
            quorum_percent=60,
            voting_period_hours=48,
            min_voting_weight=0.5,
        )
        stats = engine.get_stats()
        assert stats["default_quorum_percent"] == 60
        assert stats["default_voting_period_hrs"] == 48
        assert stats["default_min_voting_weight"] == 0.5
        assert "total_proposals" in stats

    # ── Full Proposal Lifecycle ─────────────────────────────────────────────

    def test_full_lifecycle_approval(self):
        """Complete lifecycle: create → activate → vote → finalize → execute."""
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        engine.add_member("voter_b", voting_weight=10.0)
        engine.add_member("voter_c", voting_weight=10.0)

        prop = engine.create_proposal(
            "Full lifecycle",
            "Complete lifecycle test",
            "voter_a",
            quorum_required=50,
        )
        assert prop.status == ProposalStatus.DRAFT

        engine.activate_proposal(prop.proposal_id)
        assert engine.proposals[prop.proposal_id].status == ProposalStatus.ACTIVE

        engine.cast_vote(prop.proposal_id, "voter_a", "for")
        engine.cast_vote(prop.proposal_id, "voter_b", "for")
        engine.cast_vote(prop.proposal_id, "voter_c", "abstain")

        engine.finalize_proposal(prop.proposal_id)
        assert engine.proposals[prop.proposal_id].status == ProposalStatus.PASSED

        engine.execute_proposal(prop.proposal_id)
        assert engine.proposals[prop.proposal_id].status == ProposalStatus.EXECUTED

    def test_full_lifecycle_rejection(self):
        """Complete lifecycle with rejection."""
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)

        prop = engine.create_proposal("Rejection lifecycle", "Will be rejected", "voter_a")
        engine.activate_proposal(prop.proposal_id)
        engine.cast_vote(prop.proposal_id, "voter_a", "against")
        engine.finalize_proposal(prop.proposal_id)
        assert engine.proposals[prop.proposal_id].status == ProposalStatus.REJECTED

    # ── Delegation Simulation ──────────────────────────────────────────────

    def test_delegated_voting_simulation(self):
        """Simulate delegation: one member votes on behalf of another."""
        engine = GovernanceEngine()
        engine.add_member("delegator", voting_weight=1.0)
        engine.add_member("delegate", voting_weight=5.0)

        prop = engine.create_proposal(
            "Delegation test",
            "Delegate votes on behalf of delegator",
            "delegator",
        )
        engine.activate_proposal(prop.proposal_id)

        # Delegate votes with combined weight (delegator + delegate)
        engine.cast_vote(prop.proposal_id, "delegate", "for", weight=6.0)
        assert engine.proposals[prop.proposal_id].votes_for == 6.0

    # ─── Edge Cases ─────────────────────────────────────────────────────────

    def test_draft_proposal_not_in_active(self):
        engine = GovernanceEngine()
        engine.create_proposal("Draft prop", "Stays draft", "proposer")
        active = engine.get_active_proposals()
        assert len(active) == 0

    def test_proposal_status_distribution(self):
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        engine.add_member("voter_b", voting_weight=10.0)

        p1 = engine.create_proposal("P1", "D1", "proposer")
        p2 = engine.create_proposal("P2", "D2", "proposer")
        p3 = engine.create_proposal("P3", "D3", "proposer")

        # P1: pass
        engine.activate_proposal(p1.proposal_id)
        engine.cast_vote(p1.proposal_id, "voter_a", "for")
        engine.cast_vote(p1.proposal_id, "voter_b", "for")
        engine.finalize_proposal(p1.proposal_id)

        # P2: reject
        engine.activate_proposal(p2.proposal_id)
        engine.cast_vote(p2.proposal_id, "voter_a", "against")
        engine.finalize_proposal(p2.proposal_id)

        # P3: active
        engine.activate_proposal(p3.proposal_id)

        stats = engine.get_governance_stats()
        dist = stats["proposal_status_distribution"]
        assert dist.get("passed", 0) == 1
        assert dist.get("rejected", 0) == 1
        assert dist.get("active", 0) == 1

    def test_weighted_vote_scenario(self):
        """Weighted voting: members with higher weight have more influence."""
        engine = GovernanceEngine()
        engine.add_member("whale", voting_weight=100.0)
        engine.add_member("minnow", voting_weight=1.0)

        prop = engine.create_proposal(
            "Weighted voting",
            "Whale should dominate",
            "whale",
            consensus_type=ConsensusType.WEIGHTED_VOTE,
        )
        engine.activate_proposal(prop.proposal_id)

        engine.cast_vote(prop.proposal_id, "whale", "for")
        engine.cast_vote(prop.proposal_id, "minnow", "against")

        result = engine.calculate_consensus(prop.proposal_id)
        # for_percentage = (100/101)*100 ≈ 99%
        assert result["for_percentage"] > 80
        assert result["consensus_reached"] is True

    def test_proposal_quorum_required_zero(self):
        """Quorum of 0 means no minimum participation needed."""
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        prop = engine.create_proposal(
            "Zero quorum",
            "Quorum = 0",
            "proposer",
            quorum_required=0,
        )
        engine.activate_proposal(prop.proposal_id)
        engine.cast_vote(prop.proposal_id, "voter_a", "for")

        result = engine.calculate_consensus(prop.proposal_id)
        # quorum_met = (10/10)*100 >= 0 -> True
        assert result["quorum_met"] is True
        # for_percentage = (10/10)*100 = 100% > 50%
        assert result["consensus_reached"] is True

    def test_high_quorum_not_met(self):
        """High quorum threshold prevents passing with low turnout."""
        engine = GovernanceEngine()
        engine.add_member("voter_a", voting_weight=10.0)
        engine.add_member("voter_b", voting_weight=10.0)
        prop = engine.create_proposal(
            "High quorum",
            "Need 90% quorum",
            "proposer",
            quorum_required=90,
        )
        engine.activate_proposal(prop.proposal_id)
        engine.cast_vote(prop.proposal_id, "voter_a", "for")

        result = engine.calculate_consensus(prop.proposal_id)
        # quorum = (10/20)*100 = 50% < 90%
        assert result["quorum_met"] is False
        assert result["consensus_reached"] is False

    # ── Singleton ───────────────────────────────────────────────────────────

    def test_get_governance_singleton(self):
        gf1 = get_governance()
        gf2 = get_governance()
        assert gf1 is gf2
