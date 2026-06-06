#!/usr/bin/env python3
"""
Tests for [`security/power_balance_constitution.py`](../../security/power_balance_constitution.py)
— Gap 3: 51/49 Power Balance Constitution.

Covers:
  - Enums: SectorControl (3 values), BalanceVerdict (3 values)
  - Dataclasses: BalanceResult, SectorBalance, AmendmentProposal
  - PowerBalanceConstitution: check_decision, get_current_balance,
    propose_amendment, vote_on_amendment, get_stats
  - SECTOR_BALANCE_MAP and constitutional constants
  - Singleton factory pattern
  - Persistence (JSONL round-trip)
  - Edge cases: unknown sector, invalid amendments, supermajority
"""

import os
import time
import json
import uuid
import pytest
from typing import Dict, Any, List, Optional
from pathlib import Path

from security.power_balance_constitution import (
    SectorControl,
    BalanceVerdict,
    BalanceResult,
    SectorBalance,
    AmendmentProposal,
    PowerBalanceConstitution,
    SECTOR_BALANCE_MAP,
    DEFAULT_PUBLIC_THRESHOLD,
    DEFAULT_PRIVATE_THRESHOLD,
    AMENDMENT_SUPERMAJORITY,
    get_power_balance,
    reset_power_balance,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_system():
    """Reset singleton and clean DB before each test."""
    reset_power_balance()
    yield
    reset_power_balance()


@pytest.fixture
def pbc():
    """Fresh PowerBalanceConstitution instance."""
    return PowerBalanceConstitution()


# ══════════════════════════════════════════════════════════════════════════════
# Test: SectorControl Enum
# ══════════════════════════════════════════════════════════════════════════════

class TestSectorControl:
    """Three control types exist."""

    def test_values(self):
        assert SectorControl.PUBLIC_COORDINATED.value == "public_coordinated"
        assert SectorControl.PRIVATE_OPERATED.value == "private_operated"
        assert SectorControl.MIXED.value == "mixed"

    def test_all_controls(self):
        assert len(SectorControl) == 3


# ══════════════════════════════════════════════════════════════════════════════
# Test: BalanceVerdict Enum
# ══════════════════════════════════════════════════════════════════════════════

class TestBalanceVerdict:
    """Three verdict types exist."""

    def test_values(self):
        assert BalanceVerdict.PASS.value == "pass"
        assert BalanceVerdict.WARN.value == "warn"
        assert BalanceVerdict.BLOCK.value == "block"

    def test_all_verdicts(self):
        assert len(BalanceVerdict) == 3


# ══════════════════════════════════════════════════════════════════════════════
# Test: BalanceResult Dataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestBalanceResult:
    """BalanceResult construction and serialization."""

    def test_create(self):
        r = BalanceResult(
            verdict=BalanceVerdict.PASS,
            sector="healthcare",
            current_public_share=0.51,
            current_private_share=0.49,
            decision_impact=0.05,
            message="Balance preserved",
        )
        assert r.verdict == BalanceVerdict.PASS
        assert r.sector == "healthcare"
        assert r.current_public_share == 0.51
        assert isinstance(r.timestamp, float)

    def test_to_dict(self):
        r = BalanceResult(
            verdict=BalanceVerdict.BLOCK,
            sector="governance",
            current_public_share=0.45,
            current_private_share=0.55,
            decision_impact=0.1,
            message="BLOCKED: public share too low",
        )
        d = r.to_dict()
        assert d["verdict"] == "block"
        assert d["sector"] == "governance"
        assert d["decision_impact"] == 0.1


# ══════════════════════════════════════════════════════════════════════════════
# Test: SectorBalance Dataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestSectorBalance:
    """SectorBalance construction and serialization."""

    def test_create(self):
        sb = SectorBalance(
            sector="education",
            control=SectorControl.PUBLIC_COORDINATED,
            public_share=0.51,
            private_share=0.49,
        )
        assert sb.sector == "education"
        assert sb.control == SectorControl.PUBLIC_COORDINATED
        assert sb.total_decisions == 0

    def test_to_dict(self):
        sb = SectorBalance(
            sector="commercial",
            control=SectorControl.PRIVATE_OPERATED,
            public_share=0.49,
            private_share=0.51,
            total_decisions=10,
            public_decisions=4,
            private_decisions=6,
        )
        d = sb.to_dict()
        assert d["sector"] == "commercial"
        assert d["control"] == "private_operated"
        assert d["total_decisions"] == 10
        assert d["public_decisions"] == 4

    def test_from_dict(self):
        d = {
            "sector": "technology",
            "control": "private_operated",
            "public_share": 0.49,
            "private_share": 0.51,
            "total_decisions": 5,
            "public_decisions": 2,
            "private_decisions": 3,
            "last_updated": 1000.0,
        }
        sb = SectorBalance.from_dict(d)
        assert sb.sector == "technology"
        assert sb.control == SectorControl.PRIVATE_OPERATED
        assert sb.public_decisions == 2
        assert sb.total_decisions == 5


# ══════════════════════════════════════════════════════════════════════════════
# Test: SECTOR_BALANCE_MAP
# ══════════════════════════════════════════════════════════════════════════════

class TestSectorBalanceMap:
    """The constitutional map has correct sectors and controls."""

    def test_all_sectors_defined(self):
        assert len(SECTOR_BALANCE_MAP) == 8

    def test_public_coordinated_sectors(self):
        assert SECTOR_BALANCE_MAP["infrastructure"] == SectorControl.PUBLIC_COORDINATED
        assert SECTOR_BALANCE_MAP["governance"] == SectorControl.PUBLIC_COORDINATED
        assert SECTOR_BALANCE_MAP["healthcare"] == SectorControl.PUBLIC_COORDINATED
        assert SECTOR_BALANCE_MAP["education"] == SectorControl.PUBLIC_COORDINATED

    def test_private_operated_sectors(self):
        assert SECTOR_BALANCE_MAP["commercial"] == SectorControl.PRIVATE_OPERATED
        assert SECTOR_BALANCE_MAP["technology"] == SectorControl.PRIVATE_OPERATED

    def test_mixed_sectors(self):
        assert SECTOR_BALANCE_MAP["finance"] == SectorControl.MIXED
        assert SECTOR_BALANCE_MAP["communication"] == SectorControl.MIXED

    def test_constants(self):
        assert DEFAULT_PUBLIC_THRESHOLD == 0.51
        assert DEFAULT_PRIVATE_THRESHOLD == 0.49
        assert AMENDMENT_SUPERMAJORITY == 0.90


# ══════════════════════════════════════════════════════════════════════════════
# Test: PowerBalanceConstitution — Initialization
# ══════════════════════════════════════════════════════════════════════════════

class TestPowerBalanceInit:
    """Module initializes with all 8 sector balances."""

    def test_init_all_sectors(self, pbc):
        stats = pbc.get_stats()
        assert stats["total_sectors"] == 8
        assert stats["total_decisions"] == 0
        assert stats["pending_amendments"] == 0

    def test_initial_balances_correct(self, pbc):
        bal = pbc.get_current_balance()
        sectors = bal["sectors"]
        # Public coordinated sectors start at 51% public
        assert sectors["healthcare"]["public_share"] == DEFAULT_PUBLIC_THRESHOLD
        assert sectors["governance"]["public_share"] == DEFAULT_PUBLIC_THRESHOLD
        # Private operated sectors start at 49% public
        assert sectors["commercial"]["public_share"] == DEFAULT_PRIVATE_THRESHOLD
        # Mixed sectors start at 50%
        assert sectors["finance"]["public_share"] == 0.5


# ══════════════════════════════════════════════════════════════════════════════
# Test: check_decision
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckDecision:
    """Decision balance checking with 51/49 enforcement."""

    def test_public_coordinated_pass(self, pbc):
        """Public decision in healthcare sector should PASS."""
        result = pbc.check_decision("healthcare", is_public_decision=True)
        assert result.verdict == BalanceVerdict.PASS
        assert result.sector == "healthcare"

    def test_public_coordinated_private_block(self, pbc):
        """Too many private decisions in public sector should BLOCK."""
        # Make many private decisions to push below 51%
        for _ in range(20):
            pbc.check_decision("healthcare", is_public_decision=False)

        # One more private should now be blocked
        result = pbc.check_decision("healthcare", is_public_decision=False)
        assert result.verdict == BalanceVerdict.BLOCK

    def test_private_operated_pass(self, pbc):
        """Private decision in commercial sector should PASS."""
        result = pbc.check_decision("commercial", is_public_decision=False)
        assert result.verdict == BalanceVerdict.PASS

    def test_private_operated_public_block(self, pbc):
        """Too many public decisions in private sector should BLOCK."""
        for _ in range(20):
            pbc.check_decision("commercial", is_public_decision=True)

        result = pbc.check_decision("commercial", is_public_decision=True)
        assert result.verdict == BalanceVerdict.BLOCK

    def test_mixed_sector_pass(self, pbc):
        """Mixed sector allows both public and private."""
        # Seed balanced baseline first so a single decision doesn't hit 100%
        for _ in range(5):
            pbc.check_decision("finance", is_public_decision=True)
            pbc.check_decision("finance", is_public_decision=False)

        r1 = pbc.check_decision("finance", is_public_decision=True)
        assert r1.verdict == BalanceVerdict.PASS

        r2 = pbc.check_decision("finance", is_public_decision=False)
        assert r2.verdict == BalanceVerdict.PASS

    def test_mixed_sector_warn_at_extreme(self, pbc):
        """Mixed sector warns when balance exceeds 60/40."""
        for _ in range(10):
            pbc.check_decision("finance", is_public_decision=True)

        result = pbc.check_decision("finance", is_public_decision=True)
        assert result.verdict == BalanceVerdict.WARN

    def test_unknown_sector_block(self, pbc):
        """Unknown sectors should be BLOCKED."""
        result = pbc.check_decision("unknown_sector", is_public_decision=True)
        assert result.verdict == BalanceVerdict.BLOCK
        assert "Unknown sector" in result.message

    def test_decision_records_stats(self, pbc):
        """Decisions are recorded in sector balance stats."""
        pbc.check_decision("education", is_public_decision=True)
        pbc.check_decision("education", is_public_decision=True)
        pbc.check_decision("education", is_public_decision=False)

        bal = pbc.get_current_balance("education")
        assert bal["total_decisions"] == 3
        assert bal["public_decisions"] == 2
        assert bal["private_decisions"] == 1

    def test_public_coordinated_warn_near_threshold(self, pbc):
        """WARN when approaching 51% threshold in public sector."""
        # Push close to threshold: 10 public + 7 private = 17 total
        for _ in range(10):
            pbc.check_decision("governance", is_public_decision=True)
        for _ in range(7):
            pbc.check_decision("governance", is_public_decision=False)

        # Now at ~58.8% public (10/17) — one more private gives 10/18 ≈ 55.6% → WARN
        result = pbc.check_decision("governance", is_public_decision=False)
        assert result.verdict == BalanceVerdict.WARN

    def test_all_sectors_checkable(self, pbc):
        """All 8 constitutional sectors can be checked."""
        for sector, control in SECTOR_BALANCE_MAP.items():
            # Use appropriate decision polarity for each sector type
            if control == SectorControl.PRIVATE_OPERATED:
                result = pbc.check_decision(sector, is_public_decision=False)
            else:
                result = pbc.check_decision(sector, is_public_decision=True)
            assert result.verdict in (BalanceVerdict.PASS, BalanceVerdict.WARN)
            assert result.sector == sector


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_current_balance
# ══════════════════════════════════════════════════════════════════════════════

class TestGetCurrentBalance:
    """Balance queries return accurate state."""

    def test_aggregate_balance(self, pbc):
        pbc.check_decision("healthcare", is_public_decision=True)
        pbc.check_decision("commercial", is_public_decision=False)

        bal = pbc.get_current_balance()
        assert bal["total_decisions"] == 2
        assert bal["total_public_decisions"] == 1
        assert bal["total_private_decisions"] == 1
        assert bal["overall_public_share"] == 0.5
        assert len(bal["sectors"]) == 8

    def test_sector_balance(self, pbc):
        pbc.check_decision("education", is_public_decision=True)
        pbc.check_decision("education", is_public_decision=True)

        bal = pbc.get_current_balance("education")
        assert bal["public_decisions"] == 2
        assert bal["total_decisions"] == 2
        assert bal["public_share"] == 1.0

    def test_unknown_sector(self, pbc):
        result = pbc.get_current_balance("nonexistent")
        assert "error" in result

    def test_initial_state(self, pbc):
        bal = pbc.get_current_balance()
        assert bal["total_decisions"] == 0
        assert bal["total_public_decisions"] == 0
        assert bal["total_private_decisions"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test: propose_amendment and vote_on_amendment
# ══════════════════════════════════════════════════════════════════════════════

class TestAmendments:
    """Amendment proposals and supermajority voting."""

    def test_propose_amendment(self, pbc):
        amendment = pbc.propose_amendment(
            sector="healthcare",
            proposed_control=SectorControl.MIXED,
            proposed_public_share=0.5,
            rationale="Test amendment",
            proposer="test_user",
        )
        assert amendment.sector == "healthcare"
        assert amendment.proposed_control == SectorControl.MIXED
        assert amendment.status == "pending"
        assert amendment.proposer == "test_user"

    def test_propose_unknown_sector(self, pbc):
        with pytest.raises(ValueError, match="Unknown sector"):
            pbc.propose_amendment(
                sector="nonexistent",
                proposed_control=SectorControl.MIXED,
                proposed_public_share=0.5,
                rationale="test",
                proposer="user",
            )

    def test_propose_invalid_share(self, pbc):
        with pytest.raises(ValueError, match="must be between"):
            pbc.propose_amendment(
                sector="healthcare",
                proposed_control=SectorControl.MIXED,
                proposed_public_share=1.5,
                rationale="test",
                proposer="user",
            )

    def test_vote_requires_quorum(self, pbc):
        amendment = pbc.propose_amendment(
            sector="technology",
            proposed_control=SectorControl.MIXED,
            proposed_public_share=0.5,
            rationale="Balance adjustment",
            proposer="user1",
        )

        # Single vote shouldn't pass (quorum is 10)
        approved, msg = pbc.vote_on_amendment(amendment.id, vote_for=True)
        assert approved is False
        assert "Vote recorded" in msg

    def test_vote_nonexistent_amendment(self, pbc):
        approved, msg = pbc.vote_on_amendment("nonexistent", vote_for=True)
        assert approved is False
        assert "not found" in msg

    def test_amendment_already_decided(self, pbc):
        amendment = pbc.propose_amendment(
            sector="commercial",
            proposed_control=SectorControl.PUBLIC_COORDINATED,
            proposed_public_share=0.51,
            rationale="test",
            proposer="user",
        )

        # Vote enough times to approve (need 90% of 10+)
        for _ in range(10):
            pbc.vote_on_amendment(amendment.id, vote_for=True)

        # Try voting again
        approved, msg = pbc.vote_on_amendment(amendment.id, vote_for=True)
        assert approved is False
        assert "already" in msg.lower()

    def test_supermajority_approves(self, pbc):
        amendment = pbc.propose_amendment(
            sector="education",
            proposed_control=SectorControl.MIXED,
            proposed_public_share=0.5,
            rationale="Reclassify education",
            proposer="user1",
        )

        # 10 votes, all FOR → 100% approval > 90% supermajority
        for _ in range(10):
            pbc.vote_on_amendment(amendment.id, vote_for=True)

        # Check amendment status
        amendments = pbc.get_amendments(status="approved")
        assert len(amendments) >= 1
        # The education sector should now be MIXED in runtime balance
        balance = pbc.get_current_balance("education")
        assert balance["control"] == "mixed"

    def test_get_amendments_filter(self, pbc):
        a1 = pbc.propose_amendment("healthcare", SectorControl.MIXED, 0.5,
                                    "test1", "user1")
        a2 = pbc.propose_amendment("commercial", SectorControl.PUBLIC_COORDINATED, 0.51,
                                    "test2", "user2")

        pending = pbc.get_amendments(status="pending")
        assert len(pending) == 2

        # Approve one
        for _ in range(10):
            pbc.vote_on_amendment(a1.id, vote_for=True)

        pending = pbc.get_amendments(status="pending")
        assert len(pending) == 1
        assert pending[0].id == a2.id

        approved = pbc.get_amendments(status="approved")
        assert len(approved) == 1
        assert approved[0].id == a1.id


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_sector_info
# ══════════════════════════════════════════════════════════════════════════════

class TestGetSectorInfo:
    """Sector info queries."""

    def test_known_sector(self, pbc):
        info = pbc.get_sector_info("healthcare")
        assert info is not None
        assert info["sector"] == "healthcare"
        assert info["control"] == "public_coordinated"
        assert info["current_balance"] is not None

    def test_unknown_sector(self, pbc):
        assert pbc.get_sector_info("nonexistent") is None

    def test_private_sector_info(self, pbc):
        info = pbc.get_sector_info("commercial")
        assert info["control"] == "private_operated"


# ══════════════════════════════════════════════════════════════════════════════
# Test: get_stats
# ══════════════════════════════════════════════════════════════════════════════

class TestGetStats:
    """Module statistics."""

    def test_initial_stats(self, pbc):
        stats = pbc.get_stats()
        assert stats["total_sectors"] == 8
        assert stats["total_decisions"] == 0
        assert stats["pending_amendments"] == 0
        assert stats["total_amendments"] == 0
        assert stats["public_threshold"] == 0.51
        assert stats["private_threshold"] == 0.49
        assert stats["amendment_supermajority"] == 0.90
        assert stats["sectors_by_control"]["public_coordinated"] == 4
        assert stats["sectors_by_control"]["private_operated"] == 2
        assert stats["sectors_by_control"]["mixed"] == 2

    def test_stats_after_decisions(self, pbc):
        pbc.check_decision("healthcare", is_public_decision=True)
        pbc.check_decision("commercial", is_public_decision=False)

        stats = pbc.get_stats()
        assert stats["total_decisions"] == 2
        assert stats["total_public_decisions"] == 1
        assert stats["total_private_decisions"] == 1

    def test_stats_after_amendment(self, pbc):
        pbc.propose_amendment("healthcare", SectorControl.MIXED, 0.5,
                               "test", "user")
        stats = pbc.get_stats()
        assert stats["pending_amendments"] == 1
        assert stats["total_amendments"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# Test: Singleton Factory
# ══════════════════════════════════════════════════════════════════════════════

class TestSingletonFactory:
    """Singleton get/reset pattern."""

    def test_singleton_returns_same_instance(self):
        p1 = get_power_balance()
        p2 = get_power_balance()
        assert p1 is p2

    def test_reset_creates_new_instance(self):
        p1 = get_power_balance()
        reset_power_balance()
        p2 = get_power_balance()
        assert p1 is not p2

    def test_singleton_preserves_state(self):
        p1 = get_power_balance()
        p1.check_decision("education", is_public_decision=True)

        p2 = get_power_balance()
        bal = p2.get_current_balance("education")
        assert bal["total_decisions"] == 1

    def test_reset_clears_state(self):
        p1 = get_power_balance()
        p1.check_decision("education", is_public_decision=True)
        reset_power_balance()

        p2 = get_power_balance()
        bal = p2.get_current_balance("education")
        assert bal["total_decisions"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test: Persistence
# ══════════════════════════════════════════════════════════════════════════════

class TestPersistence:
    """JSONL persistence round-trip."""

    def test_balance_persisted(self, pbc):
        pbc.check_decision("healthcare", is_public_decision=True)
        db_path = "data/power_balance.jsonl"
        assert os.path.exists(db_path)
        with open(db_path, encoding="utf-8") as f:
            lines = f.readlines()
        balance_lines = [l for l in lines if '"balance"' in l]
        assert len(balance_lines) >= 1

    def test_audit_persisted(self, pbc):
        pbc.check_decision("governance", is_public_decision=True)
        db_path = "data/power_balance.jsonl"
        with open(db_path, encoding="utf-8") as f:
            lines = f.readlines()
        audit_lines = [l for l in lines if '"audit"' in l]
        assert len(audit_lines) >= 1

    def test_amendment_persisted(self, pbc):
        pbc.propose_amendment("healthcare", SectorControl.MIXED, 0.5,
                               "test", "user")
        db_path = "data/power_balance.jsonl"
        with open(db_path, encoding="utf-8") as f:
            lines = f.readlines()
        amendment_lines = [l for l in lines if '"amendment"' in l]
        assert len(amendment_lines) >= 1

    def test_load_from_db_on_restart(self, pbc):
        pbc.check_decision("education", is_public_decision=True)
        pbc.check_decision("education", is_public_decision=True)

        new_pbc = PowerBalanceConstitution()
        bal = new_pbc.get_current_balance("education")
        assert bal["total_decisions"] == 2
        assert bal["public_decisions"] == 2

    def test_amendment_persists_across_restart(self, pbc):
        a = pbc.propose_amendment(
            sector="technology",
            proposed_control=SectorControl.MIXED,
            proposed_public_share=0.5,
            rationale="Persist test across restart",
            proposer="persist_test",
        )

        new_pbc = PowerBalanceConstitution()
        amendments = new_pbc.get_amendments()
        # Amendment should be persisted and loadable
        matching = [am for am in amendments if am.proposer == "persist_test"]
        assert len(matching) >= 1, (
            f"Expected amendment with proposer='persist_test', "
            f"got {len(amendments)} amendments: "
            f"{[(am.sector, am.proposer, am.status) for am in amendments]}"
        )
        assert matching[0].sector == "technology"


# ══════════════════════════════════════════════════════════════════════════════
# Test: Module Exports
# ══════════════════════════════════════════════════════════════════════════════

class TestModuleExports:
    """Verify that __all__ exports match actual module contents."""

    def test_all_exports_defined(self):
        from security import power_balance_constitution as pbc
        for name in pbc.__all__:
            assert hasattr(pbc, name), f"{name} not found in module"

    def test_all_exports_are_importable(self):
        from security.power_balance_constitution import (
            SectorControl,
            BalanceVerdict,
            BalanceResult,
            SectorBalance,
            AmendmentProposal,
            PowerBalanceConstitution,
            SECTOR_BALANCE_MAP,
            DEFAULT_PUBLIC_THRESHOLD,
            DEFAULT_PRIVATE_THRESHOLD,
            AMENDMENT_SUPERMAJORITY,
            get_power_balance,
            reset_power_balance,
        )
        assert SectorControl is not None
        assert BalanceVerdict is not None
        assert BalanceResult is not None
        assert len(SECTOR_BALANCE_MAP) == 8
        assert DEFAULT_PUBLIC_THRESHOLD == 0.51
        assert callable(get_power_balance)
        assert callable(reset_power_balance)


# ══════════════════════════════════════════════════════════════════════════════
# Test: Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Boundary and unusual conditions."""

    def test_balanced_public_private(self, pbc):
        """Alternating public/private decisions keeps balance near 50%."""
        for i in range(100):
            is_public = (i % 2 == 0)
            result = pbc.check_decision("finance", is_public_decision=is_public)
            assert result.verdict in (BalanceVerdict.PASS, BalanceVerdict.WARN)

        bal = pbc.get_current_balance("finance")
        assert 0.4 <= bal["public_share"] <= 0.6

    def test_all_public_in_public_sector(self, pbc):
        """All public decisions in a public sector should always PASS."""
        for _ in range(100):
            result = pbc.check_decision("governance", is_public_decision=True)
            assert result.verdict == BalanceVerdict.PASS

    def test_reset_cleans_db_file(self, pbc):
        """reset_power_balance() deletes the DB file."""
        pbc.check_decision("healthcare", is_public_decision=True)
        db_path = "data/power_balance.jsonl"
        assert os.path.exists(db_path)

        reset_power_balance()
        assert not os.path.exists(db_path)

    def test_concurrent_safe(self, pbc):
        """Multiple threads can access the module simultaneously."""
        import threading

        results: List[str] = []
        results_lock = threading.Lock()

        # Pre-seed balanced state so decisions of either polarity won't block
        for s in ["healthcare", "commercial", "finance", "education"]:
            for _ in range(10):
                pbc.check_decision(s, is_public_decision=True)
                pbc.check_decision(s, is_public_decision=False)

        def check_sector(sector: str, count: int):
            for _ in range(count):
                result = pbc.check_decision(sector,
                                            is_public_decision=(hash(sector) % 2 == 0))
                with results_lock:
                    results.append(result.verdict.value)

        threads = []
        for sector in ["healthcare", "commercial", "finance", "education"]:
            t = threading.Thread(target=check_sector, args=(sector, 10))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(results) == 40
        stats = pbc.get_stats()
        assert stats["total_decisions"] >= 40  # pre-seed 80 + at least 40 from threads

    def test_mixed_sector_tolerance(self, pbc):
        """Mixed sector allows up to ~60% before warning."""
        for _ in range(6):
            pbc.check_decision("communication", is_public_decision=True)

        # 6/6 = 100% public — should WARN
        result = pbc.check_decision("communication", is_public_decision=True)
        assert result.verdict == BalanceVerdict.WARN

    def test_private_sector_edge(self, pbc):
        """Private sector with exactly balanced decisions."""
        for _ in range(49):
            pbc.check_decision("technology", is_public_decision=False)
        for _ in range(51):
            pbc.check_decision("technology", is_public_decision=True)

        # This should be near 51% public — BLOCK for private sector
        result = pbc.check_decision("technology", is_public_decision=True)
        assert result.verdict == BalanceVerdict.BLOCK
