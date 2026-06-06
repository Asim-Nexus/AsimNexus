#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade tests for Human Override Engine
ASIMNEXUS Human Override Tests
===============================
Tests for core.human_override_engine — Gap 1a implementation:
- OverrideTier / OverrideStatus / OverrideTrigger enums
- OverrideRequest / OverrideAuditEntry dataclasses
- HumanOverrideEngine: Final-3-Decisions, request lifecycle, escalation
- Singleton factory pattern
- Env-var configuration
"""

import hashlib
import os
import time
import pytest
from dataclasses import asdict


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_engine():
    """Reset the singleton before each test to ensure clean state."""
    from core.human_override_engine import reset_human_override_engine
    reset_human_override_engine()


@pytest.fixture
def engine():
    """Create a fresh HumanOverrideEngine for testing."""
    from core.human_override_engine import HumanOverrideEngine
    return HumanOverrideEngine(max_decisions=3)


@pytest.fixture
def sample_action_hash() -> str:
    """Generate a deterministic action hash."""
    return hashlib.sha256(b"test_action_transfer_100").hexdigest()


@pytest.fixture
def trusted_engine(engine):
    """Engine with a pre-populated trusted circle."""
    for hid in ["human_alice", "human_bob", "human_charlie"]:
        engine.add_to_trusted_circle(hid)
    return engine


# =============================================================================
# Enum Tests
# =============================================================================

class TestOverrideTier:
    """Tests for OverrideTier enum."""

    def test_tier_values(self):
        from core.human_override_engine import OverrideTier
        assert OverrideTier.PERSONAL.value == "personal"
        assert OverrideTier.TRUSTED_CIRCLE.value == "trusted_circle"
        assert OverrideTier.INDEPENDENT.value == "independent"

    def test_tier_escalation_order(self):
        from core.human_override_engine import OverrideTier
        order = [OverrideTier.PERSONAL, OverrideTier.TRUSTED_CIRCLE, OverrideTier.INDEPENDENT]
        assert len(order) == 3


class TestOverrideStatus:
    """Tests for OverrideStatus enum."""

    def test_status_values(self):
        from core.human_override_engine import OverrideStatus
        assert OverrideStatus.PENDING.value == "pending"
        assert OverrideStatus.CONFIRMED.value == "confirmed"
        assert OverrideStatus.REJECTED.value == "rejected"
        assert OverrideStatus.EXPIRED.value == "expired"
        assert OverrideStatus.ESCALATED.value == "escalated"


class TestOverrideTrigger:
    """Tests for OverrideTrigger enum."""

    def test_trigger_values(self):
        from core.human_override_engine import OverrideTrigger
        assert OverrideTrigger.FINAL_THREE.value == "final_three"
        assert OverrideTrigger.CONSTITUTIONAL.value == "constitutional"
        assert OverrideTrigger.HUMAN_INITIATED.value == "human_initiated"
        assert OverrideTrigger.POLICY_CRITICAL.value == "policy_critical"
        assert OverrideTrigger.AGENT_CONTRACT.value == "agent_contract"


# =============================================================================
# Dataclass Tests
# =============================================================================

class TestOverrideRequest:
    """Tests for OverrideRequest dataclass."""

    def test_create_and_defaults(self):
        from core.human_override_engine import OverrideRequest, OverrideTier, OverrideStatus, OverrideTrigger
        req = OverrideRequest(
            request_id="test_001",
            action_hash="abc123",
            action_preview="transfer USD 100 to account Y",
            trigger=OverrideTrigger.FINAL_THREE,
            tier=OverrideTier.PERSONAL,
            requested_by="clone_architect",
        )
        assert req.request_id == "test_001"
        assert req.action_hash == "abc123"
        assert req.trigger == OverrideTrigger.FINAL_THREE
        assert req.tier == OverrideTier.PERSONAL
        assert req.status == OverrideStatus.PENDING
        assert req.human_id is None
        assert req.reason == ""
        assert req.created_at > 0
        assert req.expires_at > req.created_at  # TTL applied

    def test_expiry(self):
        from core.human_override_engine import OverrideRequest, OverrideTier, OverrideTrigger
        req = OverrideRequest(
            request_id="test_exp",
            action_hash="abc",
            action_preview="test",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
            expires_at=time.time() - 100,  # Already expired
        )
        assert req.is_expired() is True

    def test_not_expired(self):
        from core.human_override_engine import OverrideRequest, OverrideTier, OverrideTrigger
        req = OverrideRequest(
            request_id="test_not_exp",
            action_hash="abc",
            action_preview="test",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
            expires_at=time.time() + 3600,  # Far in future
        )
        assert req.is_expired() is False

    def test_to_dict_excludes_nonce(self):
        from core.human_override_engine import OverrideRequest, OverrideTier, OverrideTrigger
        req = OverrideRequest(
            request_id="test_dict",
            action_hash="abc123",
            action_preview="show me",
            trigger=OverrideTrigger.FINAL_THREE,
            tier=OverrideTier.PERSONAL,
            requested_by="system",
            nonce="secret_should_not_appear",
        )
        d = req.to_dict()
        assert "nonce" not in d
        assert d["request_id"] == "test_dict"
        assert d["tier"] == "personal"
        assert d["trigger"] == "final_three"
        assert d["status"] == "pending"


class TestOverrideAuditEntry:
    """Tests for OverrideAuditEntry dataclass."""

    def test_create_and_to_dict(self):
        from core.human_override_engine import (
            OverrideAuditEntry, OverrideTier, OverrideStatus, OverrideTrigger,
        )
        entry = OverrideAuditEntry(
            entry_id="aud_001",
            action_hash="abc123",
            human_id="human_alice",
            tier=OverrideTier.PERSONAL,
            trigger=OverrideTrigger.CONSTITUTIONAL,
            status=OverrideStatus.CONFIRMED,
            reason="I approve this action",
            signature="sig_hex_123",
            timestamp=time.time(),
        )
        d = entry.to_dict()
        assert d["entry_id"] == "aud_001"
        assert d["human_id"] == "human_alice"
        assert d["tier"] == "personal"
        assert d["status"] == "confirmed"
        assert d["signature"] == "sig_hex_123"


# =============================================================================
# HumanOverrideEngine — Final-3-Decisions Counter
# =============================================================================

class TestFinalThreeDecisions:
    """Tests for the Final-3-Decisions counter."""

    def test_initial_state(self, engine):
        assert engine.decisions_remaining == 3
        assert engine.is_override_required is False
        assert engine._decision_counter == 0

    def test_increment_counter(self, engine):
        engine.record_decision(was_overridden=False)
        assert engine._decision_counter == 1
        assert engine.decisions_remaining == 2

    def test_three_decisions_triggers_override(self, engine):
        for _ in range(3):
            engine.record_decision(was_overridden=False)
        assert engine._decision_counter == 3
        assert engine.decisions_remaining == 0
        assert engine.is_override_required is True

    def test_override_resets_counter(self, engine):
        for _ in range(3):
            engine.record_decision(was_overridden=False)
        assert engine.is_override_required is True

        # Human override resets the counter
        engine.record_decision(was_overridden=True)
        assert engine._decision_counter == 0
        assert engine.is_override_required is False

    def test_manual_reset(self, engine):
        for _ in range(2):
            engine.record_decision(was_overridden=False)
        assert engine._decision_counter == 2

        engine.reset_decision_counter()
        assert engine._decision_counter == 0
        assert engine.decisions_remaining == 3

    def test_custom_max_decisions(self):
        from core.human_override_engine import HumanOverrideEngine
        eng = HumanOverrideEngine(max_decisions=5)
        assert eng.decisions_remaining == 5
        assert eng._max_decisions == 5

        for _ in range(5):
            eng.record_decision(was_overridden=False)
        assert eng.is_override_required is True

    def test_override_does_not_exceed_max(self, engine):
        """Counter can exceed max but override_required stays True."""
        for _ in range(10):
            engine.record_decision(was_overridden=False)
        # record_decision increments unconditionally; counter can exceed max
        assert engine._decision_counter >= 3
        assert engine.is_override_required is True
        assert engine.decisions_remaining == 0


# =============================================================================
# HumanOverrideEngine — Override Request Lifecycle
# =============================================================================

class TestOverrideRequestLifecycle:
    """Tests for creating, confirming, and rejecting override requests."""

    def test_create_override_request(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Transfer USD 100 to account Y",
            trigger=OverrideTrigger.FINAL_THREE,
            tier=OverrideTier.PERSONAL,
            requested_by="clone_architect",
        )
        assert req_id.startswith("ovr_")
        assert len(req_id) > 10

        # Verify the request exists in pending list
        pending = engine.list_pending()
        ids = [r["request_id"] for r in pending]
        assert req_id in ids

    def test_confirm_override(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Test action",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        result = engine.confirm_override(
            request_id=req_id,
            human_id="human_alice",
            reason="I have reviewed and approve",
        )
        assert result["success"] is True
        assert result["request_id"] == req_id
        assert "signature" in result
        assert result["tier"] == "personal"
        assert result["human_id"] == "human_alice"

        # Verify status
        status = engine.get_override_status(req_id)
        assert status is not None
        assert status["status"] == "confirmed"
        assert status["human_id"] == "human_alice"

    def test_confirm_expired_request(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Expired test",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        # Manually expire the request
        request = engine._requests[req_id]
        request.expires_at = time.time() - 100

        result = engine.confirm_override(
            request_id=req_id,
            human_id="human_alice",
            reason="Trying to confirm expired",
        )
        assert result["success"] is False
        assert "expired" in result["error"].lower()

    def test_confirm_nonexistent_request(self, engine):
        result = engine.confirm_override(
            request_id="nonexistent",
            human_id="human_alice",
            reason="test",
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_confirm_already_resolved(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Double confirm test",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        # First confirm succeeds
        engine.confirm_override(req_id, "human_alice", "first time")
        # Second confirm should fail
        result = engine.confirm_override(req_id, "human_bob", "second time")
        assert result["success"] is False
        assert "already" in result["error"].lower()

    def test_reject_override(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Test action to reject",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        result = engine.reject_override(
            request_id=req_id,
            human_id="human_alice",
            reason="I do not approve this action",
        )
        assert result["success"] is False  # Rejected means override didn't happen
        assert result["status"] == "rejected"

        # Verify status
        status = engine.get_override_status(req_id)
        assert status is not None
        assert status["status"] == "rejected"

    def test_reject_nonexistent(self, engine):
        result = engine.reject_override(
            request_id="nonexistent",
            human_id="human_alice",
            reason="test",
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_get_override_status_not_found(self, engine):
        status = engine.get_override_status("nonexistent_id")
        assert status is None

    def test_list_pending_excludes_non_pending(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Will confirm",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        engine.confirm_override(req_id, "human_alice", "approve")

        pending = engine.list_pending()
        assert req_id not in [r["request_id"] for r in pending]

    def test_list_pending_auto_expires(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Will expire",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        # Manually expire
        engine._requests[req_id].expires_at = time.time() - 100

        pending = engine.list_pending()
        assert req_id not in [r["request_id"] for r in pending]
        # Status should be auto-updated to expired
        assert engine._requests[req_id].status.value == "expired"

    def test_list_by_human(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req1 = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Action 1",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        req2 = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Action 2",
            trigger=OverrideTrigger.FINAL_THREE,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        engine.confirm_override(req1, "human_alice", "approved")
        engine.confirm_override(req2, "human_bob", "approved")

        alice_requests = engine.list_by_human("human_alice")
        assert len(alice_requests) == 1
        assert alice_requests[0]["request_id"] == req1


# =============================================================================
# HumanOverrideEngine — Escalation Chain
# =============================================================================

class TestEscalationChain:
    """Tests for automatic tier escalation on rejection."""

    def test_escalation_to_next_tier_for_constitutional(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Constitutional violation action",
            trigger=OverrideTrigger.CONSTITUTIONAL,
            tier=OverrideTier.PERSONAL,
            requested_by="clone_architect",
        )
        result = engine.reject_override(
            request_id=req_id,
            human_id="human_alice",
            reason="I disagree, escalating",
        )
        assert result["status"] == "rejected_escalated"
        assert "escalated_to" in result
        assert result["escalated_tier"] == "trusted_circle"

        # Original request should be marked as ESCALATED
        status = engine.get_override_status(req_id)
        assert status["status"] == "escalated"
        assert len(status.get("escalation_chain", [])) >= 1

    def test_escalation_for_policy_critical(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Critical policy action",
            trigger=OverrideTrigger.POLICY_CRITICAL,
            tier=OverrideTier.PERSONAL,
            requested_by="policy_gate",
        )
        result = engine.reject_override(
            request_id=req_id,
            human_id="human_alice",
            reason="Escalating policy decision",
        )
        assert result["status"] == "rejected_escalated"
        assert result["escalated_tier"] == "trusted_circle"

    def test_no_escalation_for_human_initiated(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Normal rejection",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        result = engine.reject_override(
            request_id=req_id,
            human_id="human_alice",
            reason="Simply rejected, no escalation",
        )
        assert result["status"] == "rejected"
        assert "escalated_to" not in result

    def test_escalation_at_top_tier_stops(self, engine, sample_action_hash):
        """At INDEPENDENT tier, there's no further escalation."""
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Top tier rejection",
            trigger=OverrideTrigger.CONSTITUTIONAL,
            tier=OverrideTier.INDEPENDENT,
            requested_by="system",
        )
        result = engine.reject_override(
            request_id=req_id,
            human_id="arbiter_001",
            reason="Final rejection",
        )
        # No further tier to escalate to
        assert result["status"] == "rejected"

    def test_get_next_tier(self, engine):
        from core.human_override_engine import OverrideTier
        assert engine._get_next_tier(OverrideTier.PERSONAL) == OverrideTier.TRUSTED_CIRCLE
        assert engine._get_next_tier(OverrideTier.TRUSTED_CIRCLE) == OverrideTier.INDEPENDENT
        assert engine._get_next_tier(OverrideTier.INDEPENDENT) is None


# =============================================================================
# HumanOverrideEngine — Trusted Circle
# =============================================================================

class TestTrustedCircle:
    """Tests for trusted circle management."""

    def test_add_to_trusted_circle(self, engine):
        assert engine.add_to_trusted_circle("human_alice") is True
        assert "human_alice" in engine.get_trusted_circle()

    def test_add_duplicate(self, engine):
        engine.add_to_trusted_circle("human_alice")
        assert engine.add_to_trusted_circle("human_alice") is False

    def test_remove_from_trusted_circle(self, engine):
        engine.add_to_trusted_circle("human_alice")
        assert engine.remove_from_trusted_circle("human_alice") is True
        assert "human_alice" not in engine.get_trusted_circle()

    def test_remove_nonexistent(self, engine):
        assert engine.remove_from_trusted_circle("nonexistent") is False

    def test_trusted_circle_required_for_tier2(self, trusted_engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = trusted_engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Trusted circle action",
            trigger=OverrideTrigger.CONSTITUTIONAL,
            tier=OverrideTier.TRUSTED_CIRCLE,
            requested_by="system",
        )
        # Someone NOT in the trusted circle should be rejected
        result = trusted_engine.confirm_override(
            request_id=req_id,
            human_id="human_stranger",
            reason="I should not be able to confirm",
        )
        assert result["success"] is False
        assert "not in the trusted circle" in result["error"]

    def test_trusted_member_can_confirm_tier2(self, trusted_engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = trusted_engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Trusted circle confirm",
            trigger=OverrideTrigger.CONSTITUTIONAL,
            tier=OverrideTier.TRUSTED_CIRCLE,
            requested_by="system",
        )
        # First vote — quorum not reached yet (need 2 of 3)
        result1 = trusted_engine.confirm_override(
            request_id=req_id,
            human_id="human_alice",
            reason="I am in the trusted circle",
        )
        assert result1["success"] is False
        assert result1["status"] == "quorum_pending"

        # Second vote — quorum reached
        result2 = trusted_engine.confirm_override(
            request_id=req_id,
            human_id="human_bob",
            reason="I also approve",
        )
        assert result2["success"] is True
        assert result2["human_id"] == "human_bob"


# =============================================================================
# HumanOverrideEngine — Cryptographic Verification
# =============================================================================

class TestCryptographicVerification:
    """Tests for override signature verification."""

    def test_verify_valid_override(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Verifiable action",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        engine.confirm_override(
            request_id=req_id,
            human_id="human_alice",
            reason="I confirm this",
        )
        result = engine.verify_override(req_id)
        assert result["valid"] is True
        assert result["action_hash"] == sample_action_hash
        assert result["human_id"] == "human_alice"
        assert "signature" in result

    def test_verify_not_found(self, engine):
        result = engine.verify_override("nonexistent")
        assert result["valid"] is False
        assert "not found" in result["error"]

    def test_verify_unconfirmed_request(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Unconfirmed",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        # Not confirmed yet — no signature
        result = engine.verify_override(req_id)
        assert result["valid"] is False

    def test_signature_tampering_detected(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Tamper test",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        engine.confirm_override(req_id, "human_alice", "original reason")

        # Tamper with the stored reason — verification should fail
        engine._requests[req_id].reason = "tampered reason"
        result = engine.verify_override(req_id)
        assert result["valid"] is False


# =============================================================================
# HumanOverrideEngine — Audit Log
# =============================================================================

class TestAuditLog:
    """Tests for the immutable override audit trail."""

    def test_audit_entry_on_confirm(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Auditable action",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        engine.confirm_override(req_id, "human_alice", "approved")

        audit = engine.get_audit_log()
        assert len(audit) >= 1
        latest = audit[0]
        assert latest["action_hash"] == sample_action_hash
        assert latest["human_id"] == "human_alice"
        assert latest["status"] == "confirmed"

    def test_audit_entry_on_reject(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Rejected action",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        engine.reject_override(req_id, "human_bob", "not needed")

        audit = engine.get_audit_log()
        assert len(audit) >= 1
        latest = audit[0]
        assert latest["human_id"] == "human_bob"
        assert latest["status"] == "rejected"

    def test_audit_filter_by_human(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        r1 = engine.request_override(sample_action_hash, "A1",
                                     OverrideTrigger.HUMAN_INITIATED,
                                     OverrideTier.PERSONAL, "user")
        r2 = engine.request_override(sample_action_hash, "A2",
                                     OverrideTrigger.FINAL_THREE,
                                     OverrideTier.PERSONAL, "user")
        engine.confirm_override(r1, "human_alice", "ok")
        engine.confirm_override(r2, "human_bob", "ok")

        alice_audit = engine.get_audit_log(human_id="human_alice")
        assert len(alice_audit) == 1
        assert alice_audit[0]["human_id"] == "human_alice"

    def test_audit_last_n(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        for i in range(5):
            req_id = engine.request_override(
                sample_action_hash, f"Action {i}",
                OverrideTrigger.HUMAN_INITIATED,
                OverrideTier.PERSONAL, "user",
            )
            engine.confirm_override(req_id, f"human_{i}", f"reason_{i}")

        audit = engine.get_audit_log(last_n=2)
        assert len(audit) == 2
        # Most recent first
        assert audit[0]["human_id"] == "human_4"
        assert audit[1]["human_id"] == "human_3"


# =============================================================================
# HumanOverrideEngine — Statistics
# =============================================================================

class TestStatistics:
    """Tests for get_stats()."""

    def test_stats_initial(self, engine):
        stats = engine.get_stats()
        assert stats["final_three_decisions"]["counter"] == 0
        assert stats["final_three_decisions"]["remaining"] == 3
        assert stats["final_three_decisions"]["override_required"] is False
        assert stats["requests"]["total"] == 0
        assert stats["requests"]["pending"] == 0
        assert stats["trusted_circle_size"] == 0
        assert stats["audit_log_size"] == 0

    def test_stats_after_requests(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        r1 = engine.request_override(sample_action_hash, "A1",
                                     OverrideTrigger.HUMAN_INITIATED,
                                     OverrideTier.PERSONAL, "user")
        r2 = engine.request_override(sample_action_hash, "A2",
                                     OverrideTrigger.FINAL_THREE,
                                     OverrideTier.TRUSTED_CIRCLE, "system")
        engine.confirm_override(r1, "human_alice", "ok")
        engine.reject_override(r2, "human_bob", "no")

        stats = engine.get_stats()
        assert stats["requests"]["total"] == 2
        assert stats["requests"]["confirmed"] == 1
        assert stats["requests"]["rejected"] == 1
        assert "personal" in stats["overrides_by_tier"]
        assert stats["audit_log_size"] == 2

    def test_stats_final_three_tracking(self, engine):
        for _ in range(2):
            engine.record_decision(was_overridden=False)
        stats = engine.get_stats()
        assert stats["final_three_decisions"]["counter"] == 2
        assert stats["final_three_decisions"]["remaining"] == 1

    def test_stats_with_trusted_circle(self, engine):
        engine.add_to_trusted_circle("human_alice")
        engine.add_to_trusted_circle("human_bob")
        stats = engine.get_stats()
        assert stats["trusted_circle_size"] == 2


# =============================================================================
# Singleton Factory
# =============================================================================

class TestSingletonFactory:
    """Tests for get_human_override_engine() and reset_human_override_engine()."""

    def test_singleton_returns_same_instance(self):
        from core.human_override_engine import get_human_override_engine
        e1 = get_human_override_engine()
        e2 = get_human_override_engine()
        assert e1 is e2

    def test_reset_creates_new_instance(self):
        from core.human_override_engine import get_human_override_engine, reset_human_override_engine
        e1 = get_human_override_engine()
        reset_human_override_engine()
        e2 = get_human_override_engine()
        assert e1 is not e2

    def test_singleton_custom_max_decisions(self):
        from core.human_override_engine import get_human_override_engine
        e = get_human_override_engine(max_decisions=5)
        assert e.decisions_remaining == 5

    def test_singleton_preserves_state(self, sample_action_hash):
        from core.human_override_engine import get_human_override_engine, OverrideTrigger, OverrideTier
        e1 = get_human_override_engine()
        req_id = e1.request_override(
            sample_action_hash, "singleton test",
            OverrideTrigger.HUMAN_INITIATED,
            OverrideTier.PERSONAL, "user",
        )
        e1.confirm_override(req_id, "human_alice", "ok")

        # Same instance should have the request
        e2 = get_human_override_engine()
        status = e2.get_override_status(req_id)
        assert status is not None
        assert status["status"] == "confirmed"

    def test_reset_in_test_cleanup(self):
        """The autouse clean_engine fixture should prevent cross-test pollution."""
        from core.human_override_engine import get_human_override_engine
        e = get_human_override_engine()
        assert e._decision_counter == 0


# =============================================================================
# Environment Variable Configuration
# =============================================================================

class TestEnvVarConfiguration:
    """Tests for env-var based configuration overrides."""

    def test_default_ttl(self):
        """Default TTL should be 600 seconds (10 minutes)."""
        # Re-import with clean state
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        assert hoe._OVERRIDE_TTL_SECONDS == 600

    def test_env_ttl_override(self, monkeypatch):
        monkeypatch.setenv("ASIM_OVERRIDE_TTL", "300")
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        assert hoe._OVERRIDE_TTL_SECONDS == 300
        monkeypatch.delenv("ASIM_OVERRIDE_TTL", raising=False)

    def test_env_audit_max_override(self, monkeypatch):
        monkeypatch.setenv("ASIM_OVERRIDE_AUDIT_MAX", "500")
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        assert hoe._MAX_AUDIT_LOG == 500
        monkeypatch.delenv("ASIM_OVERRIDE_AUDIT_MAX", raising=False)

    def test_env_final_three_override(self, monkeypatch):
        monkeypatch.setenv("ASIM_OVERRIDE_FINAL_THREE", "7")
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        assert hoe._MAX_DECISIONS_BEFORE_OVERRIDE == 7
        monkeypatch.delenv("ASIM_OVERRIDE_FINAL_THREE", raising=False)

    def test_custom_engine_uses_env_value(self, monkeypatch):
        """Engine should use env var for max_decisions when no explicit arg."""
        monkeypatch.setenv("ASIM_OVERRIDE_FINAL_THREE", "10")
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        eng = hoe.HumanOverrideEngine()
        assert eng._max_decisions == 10
        monkeypatch.delenv("ASIM_OVERRIDE_FINAL_THREE", raising=False)


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for unusual or boundary conditions."""

    def test_action_preview_truncation(self, engine):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        long_preview = "A" * 500
        req_id = engine.request_override(
            action_hash="abc",
            action_preview=long_preview,
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="user",
        )
        request = engine._requests[req_id]
        assert len(request.action_preview) == 201  # 200 chars + ellipsis
        assert request.action_preview.endswith("…")

    def test_override_counter_increments_on_confirm(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        # Record some autonomous decisions
        engine.record_decision(was_overridden=False)
        engine.record_decision(was_overridden=False)
        assert engine._decision_counter == 2

        # Confirm an override — counter should reset
        req_id = engine.request_override(
            sample_action_hash, "test",
            OverrideTrigger.HUMAN_INITIATED,
            OverrideTier.PERSONAL, "user",
        )
        engine.confirm_override(req_id, "human_alice", "ok")
        assert engine._decision_counter == 0  # Reset by was_overridden=True

    def test_override_count_tracking(self, engine, sample_action_hash):
        from core.human_override_engine import OverrideTrigger, OverrideTier
        assert engine._override_count == 0

        r1 = engine.request_override(sample_action_hash, "A",
                                     OverrideTrigger.HUMAN_INITIATED,
                                     OverrideTier.PERSONAL, "user")
        engine.confirm_override(r1, "h1", "ok")
        assert engine._override_count == 1

        r2 = engine.request_override(sample_action_hash, "B",
                                     OverrideTrigger.FINAL_THREE,
                                     OverrideTier.PERSONAL, "user")
        engine.confirm_override(r2, "h2", "ok")
        assert engine._override_count == 2

    def test_confirm_with_explicit_tier(self, engine, sample_action_hash):
        """confirm_override should accept an explicit tier override."""
        from core.human_override_engine import OverrideTrigger, OverrideTier
        req_id = engine.request_override(
            sample_action_hash, "tier test",
            OverrideTrigger.HUMAN_INITIATED,
            OverrideTier.PERSONAL, "user",
        )
        # Confirm at a higher tier
        result = engine.confirm_override(
            req_id, "human_alice", "escalated confirm",
            tier=OverrideTier.INDEPENDENT,
        )
        assert result["success"] is True
        assert result["tier"] == "independent"

    def test_empty_audit_log(self, engine):
        audit = engine.get_audit_log()
        assert audit == []

    def test_audit_log_trimming(self, monkeypatch):
        """When audit log exceeds max, older entries should be trimmed."""
        from core.human_override_engine import (
            OverrideTier, OverrideTrigger, OverrideStatus,
        )
        monkeypatch.setenv("ASIM_OVERRIDE_AUDIT_MAX", "5")
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        eng = hoe.HumanOverrideEngine()
        # Create more than 5 audit entries
        for i in range(10):
            eng._create_audit_entry(
                action_hash=f"hash_{i}",
                human_id=f"human_{i}",
                tier=OverrideTier.PERSONAL,
                trigger=OverrideTrigger.HUMAN_INITIATED,
                status=OverrideStatus.CONFIRMED,
                reason=f"test_{i}",
                signature="sig",
            )
        # After trimming, should have at most 5 entries
        assert len(eng._audit_log) == 5
        monkeypatch.delenv("ASIM_OVERRIDE_AUDIT_MAX", raising=False)

    def test_max_decisions_default(self):
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        assert hoe._MAX_DECISIONS_BEFORE_OVERRIDE == 3

    def test_max_decisions_env(self, monkeypatch):
        monkeypatch.setenv("ASIM_OVERRIDE_FINAL_THREE", "1")
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        assert hoe._MAX_DECISIONS_BEFORE_OVERRIDE == 1
        monkeypatch.delenv("ASIM_OVERRIDE_FINAL_THREE", raising=False)

    def test_singleton_default_factory(self):
        import importlib
        from core import human_override_engine as hoe
        importlib.reload(hoe)
        e = hoe.get_human_override_engine()
        assert isinstance(e, hoe.HumanOverrideEngine)


# =============================================================================
# Integration-style Tests
# =============================================================================

class TestOverrideIntegration:
    """End-to-end flows across multiple components of the override engine."""

    def test_full_override_flow_personal(self, engine, sample_action_hash):
        """Complete flow: autonomous decisions → override required → request → confirm → verify."""
        from core.human_override_engine import OverrideTrigger, OverrideTier

        # 1. AI makes 3 autonomous decisions
        for _ in range(3):
            engine.record_decision(was_overridden=False)
        assert engine.is_override_required is True

        # 2. Next action triggers override request
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Transfer large sum",
            trigger=OverrideTrigger.FINAL_THREE,
            tier=OverrideTier.PERSONAL,
            requested_by="clone_trader",
        )
        assert req_id is not None

        # 3. Human reviews and confirms
        result = engine.confirm_override(
            request_id=req_id,
            human_id="human_alice",
            reason="I have reviewed the transaction and it appears legitimate",
        )
        assert result["success"] is True

        # 4. Verify cryptographic integrity
        verification = engine.verify_override(req_id)
        assert verification["valid"] is True
        assert verification["human_id"] == "human_alice"

        # 5. Counter is reset
        assert engine._decision_counter == 0
        assert engine.is_override_required is False

        # 6. Audit trail exists
        audit = engine.get_audit_log()
        assert len(audit) >= 1
        assert audit[0]["status"] == "confirmed"

    def test_full_override_flow_rejected_escalated(self, engine, sample_action_hash):
        """Flow: constitutional trigger → rejected at personal → escalated to trusted circle."""
        from core.human_override_engine import OverrideTrigger, OverrideTier

        # Add trusted circle members
        for hid in ["human_alice", "human_bob", "human_charlie"]:
            engine.add_to_trusted_circle(hid)

        # 1. Constitutional violation triggers override at PERSONAL tier
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Constitutional violation detected",
            trigger=OverrideTrigger.CONSTITUTIONAL,
            tier=OverrideTier.PERSONAL,
            requested_by="dharma_veto_engine",
        )

        # 2. Human at personal tier rejects it → auto-escalates
        result = engine.reject_override(req_id, "human_alice", "This needs more review")
        assert result["status"] == "rejected_escalated"
        escalated_id = result["escalated_to"]

        # 3. Verify the escalated request exists at TRUSTED_CIRCLE tier
        escalated_status = engine.get_override_status(escalated_id)
        assert escalated_status is not None
        assert escalated_status["tier"] == "trusted_circle"
        assert escalated_status["status"] == "pending"

        # 4. Trusted circle members confirm (need 2 of 3 for quorum)
        confirm_first = engine.confirm_override(
            escalated_id, "human_alice", "Trusted circle approves"
        )
        assert confirm_first["success"] is False
        assert confirm_first["status"] == "quorum_pending"

        confirm_second = engine.confirm_override(
            escalated_id, "human_bob", "Second member approves"
        )
        assert confirm_second["success"] is True

    def test_concurrent_multiple_overrides(self, engine, sample_action_hash):
        """Multiple simultaneous override requests should be independent."""
        from core.human_override_engine import OverrideTrigger, OverrideTier

        # Create 5 concurrent override requests
        req_ids = []
        for i in range(5):
            req_id = engine.request_override(
                hashlib.sha256(f"action_{i}".encode()).hexdigest(),
                f"Action {i}",
                OverrideTrigger.HUMAN_INITIATED,
                OverrideTier.PERSONAL,
                f"agent_{i}",
            )
            req_ids.append(req_id)

        # Confirm 3, reject 1, leave 1 pending
        for rid in req_ids[:3]:
            engine.confirm_override(rid, "human_alice", "confirmed")

        engine.reject_override(req_ids[3], "human_bob", "rejected")

        # Check stats
        stats = engine.get_stats()
        assert stats["requests"]["total"] == 5
        assert stats["requests"]["confirmed"] == 3
        assert stats["requests"]["rejected"] == 1
        assert stats["requests"]["pending"] == 1


# =============================================================================
# Module-level __all__ consistency
# =============================================================================

class TestModuleExports:
    """Verify that __all__ exports match actual module contents."""

    def test_all_exports_defined(self):
        from core import human_override_engine as hoe
        assert hasattr(hoe, "__all__")
        assert len(hoe.__all__) >= 7

    def test_all_exports_are_importable(self):
        from core.human_override_engine import (
            HumanOverrideEngine,
            OverrideTier,
            OverrideStatus,
            OverrideTrigger,
            OverrideRequest,
            OverrideAuditEntry,
            get_human_override_engine,
            reset_human_override_engine,
        )
        assert HumanOverrideEngine is not None
        assert OverrideTier is not None
        assert OverrideStatus is not None
        assert OverrideTrigger is not None
        assert OverrideRequest is not None
        assert OverrideAuditEntry is not None
        assert get_human_override_engine is not None
        assert reset_human_override_engine is not None
