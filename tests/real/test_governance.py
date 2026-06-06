#!/usr/bin/env python3
"""
tests/real/test_governance.py
AsimNexus — Governance Engine Tests (Phase B)

Tests for core/governance/consensus.py:
  - GovernanceEngine init, member management, proposal lifecycle
  - Voting and consensus calculation
  - Env var overrides
"""

import os
import gc
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
def clean_governance_env():
    """Reset singleton and env vars before/after each test."""
    saved = {}
    for key in ("ASIM_GOV_QUORUM_PERCENT", "ASIM_GOV_VOTING_PERIOD_HOURS",
                "ASIM_GOV_MIN_VOTING_WEIGHT"):
        saved[key] = os.environ.pop(key, None)

    # Reset singleton
    import core.governance.consensus as gov_mod
    gov_mod._governance = None

    yield

    for key, val in saved.items():
        if val is not None:
            os.environ[key] = val
        else:
            os.environ.pop(key, None)
    gov_mod._governance = None


# ── GovernanceEngine Tests ──────────────────────────────────────────────────

class TestGovernanceEngine:
    """GovernanceEngine initialization and member management tests."""

    def test_import(self):
        assert GovernanceEngine is not None

    def test_init(self):
        g = GovernanceEngine()
        assert g.proposals == {}
        assert g.votes == {}
        assert g.members == {}

    def test_init_creates_empty_state(self):
        g = GovernanceEngine()
        assert len(g.proposals) == 0
        assert len(g.members) == 0

    def test_add_member(self):
        g = GovernanceEngine()
        member = g.add_member("addr_1")
        assert member.address == "addr_1"
        assert member.voting_weight == 1.0
        assert member.reputation_score == 1.0
        assert member.member_id.startswith("member_")

    def test_add_member_custom_weight(self):
        g = GovernanceEngine()
        member = g.add_member("addr_heavy", voting_weight=5.0)
        assert member.voting_weight == 5.0

    def test_add_member_stored(self):
        g = GovernanceEngine()
        m1 = g.add_member("addr_a")
        m2 = g.add_member("addr_b")
        assert len(g.members) == 2
        assert m1.member_id in g.members
        assert m2.member_id in g.members

    def test_create_proposal(self):
        g = GovernanceEngine()
        prop = g.create_proposal(
            title="Test Proposal",
            description="A test proposal",
            proposer="addr_1",
        )
        assert prop.proposal_id.startswith("prop_")
        assert prop.title == "Test Proposal"
        assert prop.status == ProposalStatus.DRAFT

    def test_create_proposal_default_quorum(self):
        g = GovernanceEngine()
        prop = g.create_proposal("Test", "Desc", "addr_1")
        assert prop.quorum_required == 51

    def test_create_proposal_default_voting_period(self):
        g = GovernanceEngine()
        prop = g.create_proposal("Test", "Desc", "addr_1")
        assert prop.voting_period_hours == 72

    def test_activate_proposal(self):
        g = GovernanceEngine()
        prop = g.create_proposal("Test", "Desc", "addr_1")
        result = g.activate_proposal(prop.proposal_id)
        assert result is True
        assert prop.status == ProposalStatus.ACTIVE
        assert prop.voting_ends_at is not None

    def test_activate_proposal_not_found(self):
        g = GovernanceEngine()
        assert g.activate_proposal("nonexistent") is False

    def test_cast_vote_for(self):
        g = GovernanceEngine()
        g.add_member("addr_voter", voting_weight=2.0)
        prop = g.create_proposal("Test", "Desc", "addr_voter")
        g.activate_proposal(prop.proposal_id)

        vote = g.cast_vote(prop.proposal_id, "addr_voter", "for")
        assert vote.decision == "for"
        assert vote.weight == 2.0
        assert prop.votes_for == 2.0

    def test_cast_vote_against(self):
        g = GovernanceEngine()
        g.add_member("addr_voter2", voting_weight=1.0)
        prop = g.create_proposal("Test", "Desc", "addr_voter2")
        g.activate_proposal(prop.proposal_id)

        vote = g.cast_vote(prop.proposal_id, "addr_voter2", "against")
        assert vote.decision == "against"
        assert prop.votes_against == 1.0

    def test_cast_vote_abstain(self):
        g = GovernanceEngine()
        g.add_member("addr_voter3", voting_weight=1.0)
        prop = g.create_proposal("Test", "Desc", "addr_voter3")
        g.activate_proposal(prop.proposal_id)

        g.cast_vote(prop.proposal_id, "addr_voter3", "abstain")
        assert prop.votes_abstain == 1.0

    def test_cast_vote_not_found_raises(self):
        g = GovernanceEngine()
        with pytest.raises(ValueError, match="not found"):
            g.cast_vote("nonexistent", "addr_1", "for")

    def test_calculate_consensus_majority(self):
        g = GovernanceEngine()
        g.add_member("addr_a", voting_weight=1.0)
        g.add_member("addr_b", voting_weight=1.0)
        g.add_member("addr_c", voting_weight=1.0)

        prop = g.create_proposal("Majority", "Test majority", "addr_a",
                                 quorum_required=51, voting_period_hours=72)
        g.activate_proposal(prop.proposal_id)

        g.cast_vote(prop.proposal_id, "addr_a", "for")
        g.cast_vote(prop.proposal_id, "addr_b", "for")
        g.cast_vote(prop.proposal_id, "addr_c", "against")

        result = g.calculate_consensus(prop.proposal_id)
        assert result["consensus_reached"] is True
        assert result["quorum_met"] is True
        assert result["for_percentage"] > 50
        assert result["for_votes"] == 2.0

    def test_calculate_consensus_not_found(self):
        g = GovernanceEngine()
        result = g.calculate_consensus("nonexistent")
        assert "error" in result

    def test_calculate_consensus_no_votes(self):
        g = GovernanceEngine()
        prop = g.create_proposal("Test", "Desc", "addr_1")
        g.activate_proposal(prop.proposal_id)
        result = g.calculate_consensus(prop.proposal_id)
        assert result["status"] == "no_votes"

    def test_finalize_proposal_passed(self):
        g = GovernanceEngine()
        g.add_member("addr_a", voting_weight=1.0)
        g.add_member("addr_b", voting_weight=1.0)

        prop = g.create_proposal("PassTest", "Will pass", "addr_a",
                                 quorum_required=51)
        g.activate_proposal(prop.proposal_id)
        g.cast_vote(prop.proposal_id, "addr_a", "for")
        g.cast_vote(prop.proposal_id, "addr_b", "for")

        result = g.finalize_proposal(prop.proposal_id)
        assert result is True
        assert prop.status == ProposalStatus.PASSED
        assert prop.executed_at is not None

    def test_finalize_proposal_rejected(self):
        g = GovernanceEngine()
        g.add_member("addr_a", voting_weight=1.0)
        g.add_member("addr_b", voting_weight=1.0)

        prop = g.create_proposal("RejectTest", "Will fail", "addr_a",
                                 quorum_required=51)
        g.activate_proposal(prop.proposal_id)
        g.cast_vote(prop.proposal_id, "addr_a", "for")
        g.cast_vote(prop.proposal_id, "addr_b", "against")

        result = g.finalize_proposal(prop.proposal_id)
        assert result is True
        assert prop.status == ProposalStatus.REJECTED

    def test_finalize_proposal_not_found(self):
        g = GovernanceEngine()
        assert g.finalize_proposal("nonexistent") is False

    def test_execute_proposal(self):
        g = GovernanceEngine()
        g.add_member("addr_a", voting_weight=1.0)

        prop = g.create_proposal("ExecTest", "Will execute", "addr_a",
                                 quorum_required=51)
        g.activate_proposal(prop.proposal_id)
        g.cast_vote(prop.proposal_id, "addr_a", "for")
        g.finalize_proposal(prop.proposal_id)

        result = g.execute_proposal(prop.proposal_id)
        assert result is True
        assert prop.status == ProposalStatus.EXECUTED

    def test_cannot_execute_non_passed(self):
        g = GovernanceEngine()
        prop = g.create_proposal("NoExec", "Not passed", "addr_a")
        g.activate_proposal(prop.proposal_id)

        # Not PASSED → cannot execute
        result = g.execute_proposal(prop.proposal_id)
        assert result is False
        assert prop.status == ProposalStatus.ACTIVE  # unchanged

    def test_execute_proposal_not_found(self):
        g = GovernanceEngine()
        assert g.execute_proposal("nonexistent") is False

    def test_get_active_proposals(self):
        g = GovernanceEngine()
        p1 = g.create_proposal("Active1", "Desc", "addr_a")
        p2 = g.create_proposal("Active2", "Desc", "addr_b")
        p3 = g.create_proposal("Draft3", "Desc", "addr_c")

        g.activate_proposal(p1.proposal_id)
        g.activate_proposal(p2.proposal_id)

        active = g.get_active_proposals()
        assert len(active) == 2

    def test_get_member_votes(self):
        g = GovernanceEngine()
        g.add_member("addr_voter", voting_weight=1.0)

        prop = g.create_proposal("VoteTest", "Desc", "addr_voter")
        g.activate_proposal(prop.proposal_id)
        g.cast_vote(prop.proposal_id, "addr_voter", "for")

        votes = g.get_member_votes("addr_voter")
        assert len(votes) == 1
        assert votes[0].decision == "for"

    def test_get_member_votes_empty(self):
        g = GovernanceEngine()
        votes = g.get_member_votes("nonexistent")
        assert votes == []

    def test_get_governance_stats(self):
        g = GovernanceEngine()
        g.add_member("addr_a")
        g.add_member("addr_b")

        p1 = g.create_proposal("Stats1", "Desc", "addr_a")
        g.activate_proposal(p1.proposal_id)
        g.cast_vote(p1.proposal_id, "addr_a", "for")

        stats = g.get_governance_stats()
        assert stats["total_proposals"] == 1
        assert stats["total_members"] == 2
        assert stats["total_votes"] == 1
        assert stats["active_proposals"] == 1

    def test_get_stats_alias(self):
        """get_stats() adds extra config fields."""
        g = GovernanceEngine()
        stats = g.get_stats()
        assert "default_quorum_percent" in stats
        assert "default_voting_period_hrs" in stats
        assert "default_min_voting_weight" in stats

    def test_get_proposal(self):
        g = GovernanceEngine()
        prop = g.create_proposal("GetTest", "Desc", "addr_a")
        assert g.get_proposal(prop.proposal_id) is prop

    def test_get_proposal_not_found(self):
        g = GovernanceEngine()
        assert g.get_proposal("nonexistent") is None

    def test_get_governance_singleton(self):
        gf1 = get_governance()
        gf2 = get_governance()
        assert gf1 is gf2

    def test_default_quorum_from_env(self):
        os.environ["ASIM_GOV_QUORUM_PERCENT"] = "60"
        g = GovernanceEngine()
        assert g.default_quorum_percent == 60

    def test_default_voting_period_from_env(self):
        os.environ["ASIM_GOV_VOTING_PERIOD_HOURS"] = "48"
        g = GovernanceEngine()
        assert g.default_voting_period_hrs == 48

    def test_default_min_voting_weight_from_env(self):
        os.environ["ASIM_GOV_MIN_VOTING_WEIGHT"] = "2.5"
        g = GovernanceEngine()
        assert g.default_min_voting_weight == 2.5

    def test_explicit_params_override_env(self):
        os.environ["ASIM_GOV_QUORUM_PERCENT"] = "99"
        os.environ["ASIM_GOV_VOTING_PERIOD_HOURS"] = "999"
        g = GovernanceEngine(quorum_percent=50, voting_period_hours=24)
        assert g.default_quorum_percent == 50
        assert g.default_voting_period_hrs == 24
