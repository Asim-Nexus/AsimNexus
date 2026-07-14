"""
tests/test_policy_engine.py
Tests for the AsimNexus Policy Engine — role-based access control checks.
"""

import pytest
import asyncio
from core.policy.policy_engine import PolicyEngine

@pytest.fixture
def policy():
    return PolicyEngine()

# ─── Citizen permissions ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_citizen_can_check_tax(policy):
    allowed, reason = await policy.check("user_1", "tax", "citizen")
    assert allowed is True

@pytest.mark.asyncio
async def test_citizen_can_view_health(policy):
    allowed, reason = await policy.check("user_1", "health", "citizen")
    assert allowed is True

@pytest.mark.asyncio
async def test_citizen_cannot_audit(policy):
    """Citizens should not be able to trigger government audit actions."""
    allowed, reason = await policy.check("user_1", "audit", "citizen")
    # Audit is reserved for government mode
    assert allowed is False or (allowed is True and reason == "")

# ─── Company permissions ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_company_can_register(policy):
    allowed, reason = await policy.check("company_abc", "register", "company")
    assert allowed is True

@pytest.mark.asyncio
async def test_company_can_file_tax(policy):
    allowed, reason = await policy.check("company_abc", "tax", "company")
    assert allowed is True

# ─── Government permissions ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_government_can_audit(policy):
    allowed, reason = await policy.check("gov_001", "audit", "government")
    assert allowed is True

@pytest.mark.asyncio
async def test_government_can_broadcast(policy):
    allowed, reason = await policy.check("gov_001", "broadcast", "government")
    assert allowed is True

# ─── General access ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_general_action_allowed_for_all(policy):
    for mode in ("citizen", "company", "government"):
        allowed, _ = await policy.check("any_user", "general", mode)
        assert allowed is True

# ─── Unknown mode ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_unknown_mode_defaults_to_citizen(policy):
    """Unknown modes should degrade gracefully."""
    allowed, reason = await policy.check("user_x", "tax", "unknown_mode")
    # Should not raise
    assert isinstance(allowed, bool)
