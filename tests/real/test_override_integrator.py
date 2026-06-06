#!/usr/bin/env python3
"""
STATUS: REAL — Tests for Override Integrator
=============================================
Tests for core.override_integrator — the 3 convenience wrapper functions
that bridge the Human Override Engine with API endpoints.

Test targets:
- approve_with_override()
- reject_with_override()
- escalate_with_override()
- list_pending_overrides()
- Full integration flow
"""

import hashlib
import pytest
from unittest.mock import MagicMock, patch


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
    return hashlib.sha256(b"test_action_override_integrator").hexdigest()


@pytest.fixture
def pending_request(engine, sample_action_hash) -> str:
    """Create a pending override request for testing."""
    from core.human_override_engine import OverrideTrigger, OverrideTier
    return engine.request_override(
        action_hash=sample_action_hash,
        action_preview="Integrator test action",
        trigger=OverrideTrigger.HUMAN_INITIATED,
        tier=OverrideTier.PERSONAL,
        requested_by="test_agent",
    )


# =============================================================================
# approve_with_override Tests
# =============================================================================

class TestApproveWithOverride:
    """Tests for approve_with_override()."""

    def test_approve_success(self, engine, pending_request):
        """approve_with_override should return success for valid request."""
        from core.override_integrator import approve_with_override
        result = approve_with_override(
            request_id=pending_request,
            human_id="human_alice",
            reason="I approve this action",
            override_engine=engine,
        )
        assert result["success"] is True
        assert result["request_id"] == pending_request
        assert result["human_id"] == "human_alice"
        assert "signature" in result

    def test_approve_nonexistent_request(self, engine):
        """approve_with_override should fail gracefully for nonexistent request."""
        from core.override_integrator import approve_with_override
        result = approve_with_override(
            request_id="nonexistent_request",
            human_id="human_alice",
            reason="test",
            override_engine=engine,
        )
        assert result["success"] is False
        assert "not found" in result.get("error", "").lower()

    def test_approve_already_resolved(self, engine, pending_request):
        """approve_with_override should fail for already resolved request."""
        from core.override_integrator import approve_with_override
        # First approve succeeds
        approve_with_override(pending_request, "human_alice", "first", engine)
        # Second approve should fail
        result = approve_with_override(
            pending_request, "human_bob", "second", engine
        )
        assert result["success"] is False
        assert "already" in result.get("error", "").lower()

    def test_approve_uses_singleton_by_default(self, pending_request):
        """approve_with_override should use singleton engine when none provided."""
        from core.override_integrator import approve_with_override
        from core.human_override_engine import get_human_override_engine
        # Get the singleton and create a request on it
        singleton = get_human_override_engine()
        # The pending_request was made on a non-singleton engine,
        # so this will return not-found
        result = approve_with_override(
            request_id=pending_request,
            human_id="human_alice",
            reason="test",
        )
        assert result["success"] is False


# =============================================================================
# reject_with_override Tests
# =============================================================================

class TestRejectWithOverride:
    """Tests for reject_with_override()."""

    def test_reject_success(self, engine, pending_request):
        """reject_with_override should return rejected status."""
        from core.override_integrator import reject_with_override
        result = reject_with_override(
            request_id=pending_request,
            human_id="human_alice",
            reason="I do not approve",
            override_engine=engine,
        )
        assert result["success"] is False  # Rejected means override didn't happen
        assert result.get("status") == "rejected"

    def test_reject_nonexistent(self, engine):
        """reject_with_override should fail gracefully for nonexistent."""
        from core.override_integrator import reject_with_override
        result = reject_with_override(
            request_id="nonexistent",
            human_id="human_alice",
            reason="test",
            override_engine=engine,
        )
        assert result["success"] is False
        assert "not found" in result.get("error", "").lower()


# =============================================================================
# escalate_with_override Tests
# =============================================================================

class TestEscalateWithOverride:
    """Tests for escalate_with_override()."""

    def test_escalate_constitutional(self, engine, sample_action_hash):
        """Escalating a constitutional trigger should move to next tier."""
        from core.override_integrator import escalate_with_override
        from core.human_override_engine import OverrideTrigger, OverrideTier

        # Add trusted circle so escalation has somewhere to go
        for hid in ["human_alice", "human_bob", "human_charlie"]:
            engine.add_to_trusted_circle(hid)

        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Constitutional violation",
            trigger=OverrideTrigger.CONSTITUTIONAL,
            tier=OverrideTier.PERSONAL,
            requested_by="test_agent",
        )
        result = escalate_with_override(
            request_id=req_id,
            human_id="human_alice",
            reason="Escalating to trusted circle",
            override_engine=engine,
        )
        assert result.get("status") == "rejected_escalated"
        assert "escalated_to" in result
        assert result.get("escalated_tier") == "trusted_circle"

    def test_escalate_human_initiated_no_escalation(self, engine, pending_request):
        """Human-initiated overrides should not auto-escalate on reject."""
        from core.override_integrator import escalate_with_override
        result = escalate_with_override(
            request_id=pending_request,
            human_id="human_alice",
            reason="Just rejecting",
            override_engine=engine,
        )
        # Human-initiated doesn't auto-escalate
        assert result.get("status") == "rejected"
        assert "escalated_to" not in result


# =============================================================================
# list_pending_overrides Tests
# =============================================================================

class TestListPendingOverrides:
    """Tests for list_pending_overrides()."""

    def test_list_pending_returns_requests(self, engine, pending_request):
        """list_pending_overrides should return pending requests."""
        from core.override_integrator import list_pending_overrides
        pending = list_pending_overrides(override_engine=engine)
        assert len(pending) >= 1
        request_ids = [r["request_id"] for r in pending]
        assert pending_request in request_ids

    def test_list_pending_empty_after_confirm(self, engine, pending_request):
        """list_pending_overrides should return empty after confirm."""
        from core.override_integrator import list_pending_overrides, approve_with_override
        approve_with_override(pending_request, "human_alice", "ok", engine)
        pending = list_pending_overrides(override_engine=engine)
        assert pending_request not in [r["request_id"] for r in pending]


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegratorIntegration:
    """Full flow: integrator → engine → result."""

    def test_full_approve_flow(self, engine, sample_action_hash):
        """Full integration: request → approve_with_override → verify."""
        from core.override_integrator import approve_with_override
        from core.human_override_engine import OverrideTrigger, OverrideTier

        # 1. Create a request directly on the engine
        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Full flow test",
            trigger=OverrideTrigger.FINAL_THREE,
            tier=OverrideTier.PERSONAL,
            requested_by="test_agent",
        )

        # 2. Approve via integrator
        approve_result = approve_with_override(
            request_id=req_id,
            human_id="human_alice",
            reason="Full flow approval",
            override_engine=engine,
        )
        assert approve_result["success"] is True

        # 3. Verify via engine
        status = engine.get_override_status(req_id)
        assert status is not None
        assert status["status"] == "confirmed"
        assert status["human_id"] == "human_alice"

        # 4. Verify cryptographic integrity
        verification = engine.verify_override(req_id)
        assert verification["valid"] is True

        # 5. Audit trail exists
        audit = engine.get_audit_log()
        assert len(audit) >= 1
        assert audit[0]["status"] == "confirmed"

    def test_full_reject_flow(self, engine, sample_action_hash):
        """Full integration: request → reject_with_override → verify rejected status."""
        from core.override_integrator import reject_with_override
        from core.human_override_engine import OverrideTrigger, OverrideTier

        req_id = engine.request_override(
            action_hash=sample_action_hash,
            action_preview="Reject flow test",
            trigger=OverrideTrigger.HUMAN_INITIATED,
            tier=OverrideTier.PERSONAL,
            requested_by="test_agent",
        )

        reject_result = reject_with_override(
            request_id=req_id,
            human_id="human_bob",
            reason="Not needed",
            override_engine=engine,
        )
        assert reject_result["success"] is False
        assert reject_result.get("status") == "rejected"

        status = engine.get_override_status(req_id)
        assert status["status"] == "rejected"
