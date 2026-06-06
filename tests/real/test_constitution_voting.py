#!/usr/bin/env python3
"""
Tests for [`core/constitution/power_balance_constitution.py`]
(../../core/constitution/power_balance_constitution.py)
— Phase 9: Vote-based constitutional governance layer.

Covers:
  - Sector registration and weight validation
  - Simple proposal voting within a sector
  - Cross-sector proposal (constitutional amendment requiring both sides)
  - Government veto on private decision
  - Private veto on government decision
  - Founder emergency veto
  - Founder veto override with 75% supermajority
  - Emergency powers requiring 66% government
  - Audit trail retrieval
  - Singleton factory pattern
"""

import os
import sys
import json
import time
import pytest
from typing import Dict, Any, Optional
from pathlib import Path

# Ensure the module path is available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.constitution.power_balance_constitution import (
    Sector,
    Vote,
    Proposal,
    PowerBalanceConstitutionVoting,
    GOVERNMENT_SECTORS,
    PRIVATE_SECTORS,
    get_sector_group,
    get_power_balance_constitution,
    reset_power_balance_constitution,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_system():
    """Reset singleton and clean DB before each test."""
    reset_power_balance_constitution()
    yield
    reset_power_balance_constitution()


@pytest.fixture
def voting():
    """Fresh PowerBalanceConstitutionVoting instance."""
    return PowerBalanceConstitutionVoting()


# ══════════════════════════════════════════════════════════════════════════════
# Test: Sector Definitions & Weights
# ══════════════════════════════════════════════════════════════════════════════

class TestSectorDefinitions:
    """Sector weight allocations are correct."""

    def test_government_sectors_total(self):
        """Government sectors sum to 0.51 (51%)."""
        total = sum(GOVERNMENT_SECTORS.values())
        assert abs(total - 0.51) < 0.001, f"Government total: {total}"

    def test_private_sectors_total(self):
        """Private sectors sum to 0.49 (49%)."""
        total = sum(PRIVATE_SECTORS.values())
        assert abs(total - 0.49) < 0.001, f"Private total: {total}"

    def test_all_sub_sectors(self, voting):
        """All 8 sub-sectors are registered."""
        assert "executive" in GOVERNMENT_SECTORS
        assert "judicial" in GOVERNMENT_SECTORS
        assert "legislative" in GOVERNMENT_SECTORS
        assert "military" in GOVERNMENT_SECTORS
        assert "corporate" in PRIVATE_SECTORS
        assert "startup" in PRIVATE_SECTORS
        assert "public" in PRIVATE_SECTORS
        assert "non_profit" in PRIVATE_SECTORS

    def test_get_sector_group(self):
        """get_sector_group correctly identifies sector ownership."""
        assert get_sector_group("executive") == "government"
        assert get_sector_group("corporate") == "private"

    def test_get_sector_group_unknown(self):
        """get_sector_group raises ValueError for unknown sectors."""
        with pytest.raises(ValueError):
            get_sector_group("unknown_sector")

    def test_get_sub_sector_weight(self, voting):
        """get_sub_sector_weight returns correct weights."""
        weight = voting.get_sub_sector_weight("government", "executive")
        assert abs(weight - 0.20) < 0.001

        weight = voting.get_sub_sector_weight("private", "non_profit")
        assert abs(weight - 0.09) < 0.001

    def test_register_custom_sector(self, voting):
        """Custom sectors can be registered."""
        custom = Sector(name="test_sector", sub_sectors={"sub_a": 0.5, "sub_b": 0.5})
        assert voting.register_sector(custom) is True
        # Duplicate registration returns False
        assert voting.register_sector(custom) is False

    def test_get_sectors(self, voting):
        """get_sectors returns all registered sectors."""
        sectors = voting.get_sectors()
        assert "government" in sectors
        assert "private" in sectors
        assert len(sectors) == 2


# ══════════════════════════════════════════════════════════════════════════════
# Test: Proposal Creation
# ══════════════════════════════════════════════════════════════════════════════

class TestProposalCreation:
    """Proposal lifecycle."""

    def test_create_standard_proposal(self, voting):
        """Create a standard proposal."""
        pid = voting.create_proposal("Test Proposal", "A test proposal")
        assert pid is not None
        proposal = voting.get_proposal(pid)
        assert proposal is not None
        assert proposal.title == "Test Proposal"
        assert proposal.status == "PENDING"
        assert proposal.is_constitutional_amendment is False
        assert proposal.is_emergency is False

    def test_create_constitutional_amendment(self, voting):
        """Create a constitutional amendment."""
        pid = voting.create_proposal("Amend Constitution",
                                     "Change the balance",
                                     is_constitutional=True)
        proposal = voting.get_proposal(pid)
        assert proposal.is_constitutional_amendment is True

    def test_create_emergency_proposal(self, voting):
        """Create an emergency proposal."""
        pid = voting.create_proposal("Emergency Action",
                                     "Emergency measure",
                                     is_emergency=True)
        proposal = voting.get_proposal(pid)
        assert proposal.is_emergency is True

    def test_get_proposal_status(self, voting):
        """get_proposal_status returns correct status."""
        pid = voting.create_proposal("Test", "Test")
        assert voting.get_proposal_status(pid) == "PENDING"
        assert voting.get_proposal_status("nonexistent") is None

    def test_get_all_proposals(self, voting):
        """get_all_proposals returns all proposals."""
        pid1 = voting.create_proposal("Proposal 1", "First")
        pid2 = voting.create_proposal("Proposal 2", "Second")
        all_props = voting.get_all_proposals()
        assert len(all_props) == 2


# ══════════════════════════════════════════════════════════════════════════════
# Test: Simple Voting
# ══════════════════════════════════════════════════════════════════════════════

class TestSimpleVoting:
    """Standard proposal voting within a sector."""

    def test_cast_vote(self, voting):
        """Cast a single vote on a proposal."""
        pid = voting.create_proposal("Test", "Test")
        success, msg = voting.cast_vote(pid, "executive", "executive",
                                         "voter_1", True)
        assert success is True
        assert "recorded" in msg

    def test_cast_vote_invalid_sector(self, voting):
        """Casting vote with invalid sector fails."""
        pid = voting.create_proposal("Test", "Test")
        with pytest.raises(ValueError):
            voting.cast_vote(pid, "unknown", "unknown",
                             "voter_1", True)

    def test_duplicate_vote_rejected(self, voting):
        """Same voter cannot vote twice."""
        pid = voting.create_proposal("Test", "Test")
        voting.cast_vote(pid, "executive", "executive", "voter_1", True)
        success, msg = voting.cast_vote(pid, "executive", "executive",
                                         "voter_1", False)
        assert success is False
        assert "already voted" in msg

    def test_vote_on_nonexistent_proposal(self, voting):
        """Voting on nonexistent proposal fails."""
        success, msg = voting.cast_vote("nonexistent", "executive",
                                         "executive", "voter_1", True)
        assert success is False

    def test_standard_proposal_passes(self, voting):
        """Standard proposal passes with majority yes."""
        pid = voting.create_proposal("Standard", "Standard proposal")
        # Cast yes votes from government sectors (51%)
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)
        voting.cast_vote(pid, "legislative", "legislative", "gov_3", True)
        # Cast some private yes votes
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)
        # Cast one no vote
        voting.cast_vote(pid, "non_profit", "non_profit", "priv_2", False)

        result = voting.tally_votes(pid)
        assert result["outcome"] == "PASSED"

    def test_standard_proposal_rejected(self, voting):
        """Standard proposal is rejected with majority no."""
        pid = voting.create_proposal("Rejected", "Will be rejected")
        voting.cast_vote(pid, "executive", "executive", "gov_1", False)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", False)
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)

        result = voting.tally_votes(pid)
        assert result["outcome"] == "REJECTED"

    def test_no_votes_tally(self, voting):
        """Tally with no votes returns NO_QUORUM."""
        pid = voting.create_proposal("NoVotes", "No votes cast")
        result = voting.tally_votes(pid)
        assert result["outcome"] == "NO_QUORUM"


# ══════════════════════════════════════════════════════════════════════════════
# Test: Constitutional Amendments
# ══════════════════════════════════════════════════════════════════════════════

class TestConstitutionalAmendments:
    """Constitutional amendments require BOTH sectors to pass."""

    def test_amendment_passes_both_sectors(self, voting):
        """Amendment passes when both government AND private approve."""
        pid = voting.create_proposal("Amend Const", "Change rule",
                                     is_constitutional=True)
        # Government votes yes
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)
        # Private votes yes
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)
        voting.cast_vote(pid, "startup", "startup", "priv_2", True)

        result = voting.tally_votes(pid)
        assert result["outcome"] == "PASSED"

    def test_amendment_rejected_by_government(self, voting):
        """Amendment rejected when government votes no."""
        pid = voting.create_proposal("Amend Reject Gov", "Gov rejects",
                                     is_constitutional=True)
        # Government votes no
        voting.cast_vote(pid, "executive", "executive", "gov_1", False)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)
        # Private votes yes
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)

        result = voting.tally_votes(pid)
        assert result["outcome"] == "REJECTED"
        assert "government" in result["message"]

    def test_amendment_rejected_by_private(self, voting):
        """Amendment rejected when private sector votes no."""
        pid = voting.create_proposal("Amend Reject Priv", "Priv rejects",
                                     is_constitutional=True)
        # Government votes yes
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)
        # Private votes no
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", False)

        result = voting.tally_votes(pid)
        assert result["outcome"] == "REJECTED"
        assert "private" in result["message"]


# ══════════════════════════════════════════════════════════════════════════════
# Test: Emergency Powers
# ══════════════════════════════════════════════════════════════════════════════

class TestEmergencyPowers:
    """Emergency powers require 66% government supermajority."""

    def test_emergency_passes_with_supermajority(self, voting):
        """Emergency passes with 66%+ government support."""
        pid = voting.create_proposal("Emergency", "Emergency action",
                                     is_emergency=True)
        # Government votes yes (executive + judicial + legislative = 0.45 of 0.51 = 88%)
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)
        voting.cast_vote(pid, "legislative", "legislative", "gov_3", True)

        result = voting.tally_votes(pid)
        assert result["outcome"] == "PASSED"
        assert "66%" in result["message"]

    def test_emergency_rejected_without_supermajority(self, voting):
        """Emergency rejected without 66% government support."""
        pid = voting.create_proposal("Emergency Fail", "Not enough support",
                                     is_emergency=True)
        # Only military votes yes (6% of total, 11.7% of government) — not enough
        voting.cast_vote(pid, "military", "military", "gov_1", True)
        # Executive votes no
        voting.cast_vote(pid, "executive", "executive", "gov_2", False)

        result = voting.tally_votes(pid)
        assert result["outcome"] == "REJECTED"

    def test_emergency_no_government_votes(self, voting):
        """Emergency with no government votes returns NO_QUORUM."""
        pid = voting.create_proposal("Emergency NoGov", "No gov votes",
                                     is_emergency=True)
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)

        result = voting.tally_votes(pid)
        assert result["outcome"] == "NO_QUORUM"


# ══════════════════════════════════════════════════════════════════════════════
# Test: Veto Powers
# ══════════════════════════════════════════════════════════════════════════════

class TestVetoPowers:
    """Sector veto and founder veto mechanics."""

    def test_government_veto_on_private_decision(self, voting):
        """Government can veto with 66% support."""
        pid = voting.create_proposal("Private Decision", "Private matter")
        # Cast ALL votes BEFORE tally (tally locks the status)
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)
        voting.cast_vote(pid, "startup", "startup", "priv_2", True)
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)
        voting.cast_vote(pid, "legislative", "legislative", "gov_3", True)
        voting.tally_votes(pid)

        # Now government vetoes with 66% internal support
        success, msg = voting.apply_veto(pid, "government")
        assert success is True, f"Veto failed: {msg}"
        assert voting.get_proposal_status(pid) == "VETOED"

    def test_private_veto_on_government_decision(self, voting):
        """Private sector can veto with 66% support."""
        pid = voting.create_proposal("Gov Decision", "Government matter")
        # Cast ALL votes BEFORE tally
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)
        voting.cast_vote(pid, "startup", "startup", "priv_2", True)
        voting.cast_vote(pid, "public", "public", "priv_3", True)
        voting.cast_vote(pid, "non_profit", "non_profit", "priv_4", True)
        voting.tally_votes(pid)

        # Private vetoes
        success, msg = voting.apply_veto(pid, "private")
        assert success is True, f"Veto failed: {msg}"

    def test_veto_requires_66_percent(self, voting):
        """Veto fails without 66% internal support."""
        pid = voting.create_proposal("Weak Veto", "Not enough support")
        # Government passes it
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)
        # Private votes: corporate yes (0.20), others no (0.10+0.10+0.09=0.29)
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)
        voting.cast_vote(pid, "startup", "startup", "priv_2", False)
        voting.cast_vote(pid, "public", "public", "priv_3", False)
        voting.cast_vote(pid, "non_profit", "non_profit", "priv_4", False)
        voting.tally_votes(pid)

        # Try private veto — corporate supports (20%), others oppose (29%)
        # Support = 20/49 = 40.8% < 66%
        success, msg = voting.apply_veto(pid, "private")
        assert success is False
        assert "Insufficient" in msg

    def test_veto_insufficient_support(self, voting):
        """Veto fails when internal support < 66%."""
        pid = voting.create_proposal("Veto Fail", "Insufficient support")
        # Government passes it (0.20+0.15+0.10+0.06=0.51)
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)
        voting.cast_vote(pid, "legislative", "legislative", "gov_3", True)
        voting.cast_vote(pid, "military", "military", "gov_4", True)
        # Private votes no (0.20+0.10+0.10+0.09=0.49)
        voting.cast_vote(pid, "corporate", "corporate", "c1", False)
        voting.cast_vote(pid, "startup", "startup", "s1", False)
        voting.cast_vote(pid, "public", "public", "p1", False)
        voting.cast_vote(pid, "non_profit", "non_profit", "n1", False)
        voting.tally_votes(pid)

        # Try private veto — all private voted no
        # Support = 0/49 = 0% < 66%
        success, msg = voting.apply_veto(pid, "private")
        assert success is False
        assert "Insufficient" in msg

    def test_founder_veto(self, voting):
        """Founder can apply emergency veto."""
        pid = voting.create_proposal("Founder Veto", "Founder stops this")
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)

        success, msg = voting.founder_veto(pid)
        assert success is True
        assert voting.get_proposal_status(pid) == "VETOED"

    def test_founder_veto_override(self, voting):
        """Founder veto can be overridden by 75% supermajority."""
        pid = voting.create_proposal("Override", "Override founder")
        # Cast many yes votes
        voting.cast_vote(pid, "executive", "executive", "gov_1", True)     # 0.20
        voting.cast_vote(pid, "judicial", "judicial", "gov_2", True)       # 0.15
        voting.cast_vote(pid, "legislative", "legislative", "gov_3", True) # 0.10
        voting.cast_vote(pid, "military", "military", "gov_4", True)       # 0.06
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", True)    # 0.20
        voting.cast_vote(pid, "public", "public", "priv_3", True)          # 0.10
        # Total yes weight: 0.20+0.15+0.10+0.06+0.20+0.10 = 0.81 = 81% > 75%

        # Apply founder veto
        voting.founder_veto(pid)

        # Override the veto
        success, msg = voting.override_founder_veto(pid)
        assert success is True
        assert voting.get_proposal_status(pid) == "PASSED"

    def test_founder_veto_override_fails_without_75(self, voting):
        """Founder veto override fails without 75% support."""
        pid = voting.create_proposal("Weak Override", "Not enough support")
        voting.cast_vote(pid, "military", "military", "gov_4", True)       # 0.06 only
        voting.cast_vote(pid, "corporate", "corporate", "priv_1", False)   # 0.20 against

        voting.founder_veto(pid)

        success, msg = voting.override_founder_veto(pid)
        assert success is False
        assert "Insufficient" in msg

    def test_override_no_active_veto(self, voting):
        """Override fails when no founder veto is active."""
        pid = voting.create_proposal("No Veto", "No veto to override")
        success, msg = voting.override_founder_veto(pid)
        assert success is False
        assert "No active" in msg


# ══════════════════════════════════════════════════════════════════════════════
# Test: Audit Trail
# ══════════════════════════════════════════════════════════════════════════════

class TestAuditTrail:
    """Audit trail records all voting actions."""

    def test_audit_trail_has_entries(self, voting):
        """Audit trail contains entries after actions."""
        pid = voting.create_proposal("Audit Test", "Testing audit")
        voting.cast_vote(pid, "executive", "executive", "voter_1", True)
        voting.tally_votes(pid)

        audit = voting.get_audit_trail()
        assert len(audit) >= 3  # create + vote + tally

    def test_audit_trail_since_filter(self, voting):
        """Audit trail can be filtered by timestamp."""
        pid = voting.create_proposal("Audit Filter", "Testing filter")
        before = time.time() - 1
        after = time.time() + 1

        entries_before = voting.get_audit_trail(since=before)
        entries_after = voting.get_audit_trail(since=after)

        assert len(entries_before) >= 1
        assert len(entries_after) == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test: Singleton Factory
# ══════════════════════════════════════════════════════════════════════════════

class TestSingleton:
    """Singleton factory pattern."""

    def test_get_power_balance_constitution(self):
        """get_power_balance_constitution returns same instance."""
        reset_power_balance_constitution()
        c1 = get_power_balance_constitution()
        c2 = get_power_balance_constitution()
        assert c1 is c2

    def test_reset_power_balance_constitution(self):
        """reset_power_balance_constitution creates new instance."""
        reset_power_balance_constitution()
        c1 = get_power_balance_constitution()
        reset_power_balance_constitution()
        c2 = get_power_balance_constitution()
        assert c1 is not c2


# ══════════════════════════════════════════════════════════════════════════════
# Test: Stats
# ══════════════════════════════════════════════════════════════════════════════

class TestStats:
    """Statistics reporting."""

    def test_get_stats(self, voting):
        """get_stats returns comprehensive statistics."""
        stats = voting.get_stats()
        assert stats["total_proposals"] == 0
        assert stats["sectors_registered"] == 2
        assert abs(stats["government_weight"] - 0.51) < 0.001
        assert abs(stats["private_weight"] - 0.49) < 0.001

    def test_get_stats_after_voting(self, voting):
        """Stats reflect voting activity."""
        pid = voting.create_proposal("Stats Test", "Testing stats")
        voting.cast_vote(pid, "executive", "executive", "v1", True)
        voting.tally_votes(pid)

        stats = voting.get_stats()
        assert stats["total_proposals"] == 1
        assert stats["passed"] == 1
        assert stats["total_votes_cast"] == 1
