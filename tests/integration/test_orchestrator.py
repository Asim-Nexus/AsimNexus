"""
tests/test_orchestrator.py
Tests for the AsimNexus Orchestrator pipeline:
  intent detection → policy check → plan → veto → consensus → execute
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def orchestrator():
    """Create a test Orchestrator with mocked sub-components."""
    with (
        patch('core.orchestrator.orchestrator.dharma_available', False),
        patch('core.orchestrator.orchestrator.consensus_available', False),
    ):
        from core.orchestrator.orchestrator import Orchestrator
        orch = Orchestrator()
        return orch

# ─── Basic process tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_citizen_basic(orchestrator):
    """Citizen request resolves without blocking."""
    result = await orchestrator.process(
        user_id="test_user_001",
        message="What is my tax balance?",
        mode="citizen"
    )
    assert result is not None
    assert isinstance(result, dict)
    assert "status" in result

@pytest.mark.asyncio
async def test_process_company_mode(orchestrator):
    """Company mode does not raise and returns a dict."""
    result = await orchestrator.process(
        user_id="company_abc",
        message="Register my company for VAT",
        mode="company"
    )
    assert isinstance(result, dict)

@pytest.mark.asyncio
async def test_process_government_mode(orchestrator):
    """Government mode returns structured response."""
    result = await orchestrator.process(
        user_id="gov_official_1",
        message="Audit citizen record 789",
        mode="government"
    )
    assert isinstance(result, dict)

# ─── Policy blocking ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_policy_blocks_restricted_action(orchestrator):
    """Policy engine blocks actions not permitted for the given mode."""
    # Patch PolicyEngine to simulate a block
    orchestrator.policy.check = AsyncMock(return_value=(False, "Role not authorized"))

    result = await orchestrator.process(
        user_id="citizen_1",
        message="Delete all government records",
        mode="citizen"
    )
    assert result["status"] == "blocked"
    assert "Policy restriction" in result["message"]

# ─── Intent detection ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_intent_parsing_tax(orchestrator):
    intent = await orchestrator._parse_intent("I want to check my tax record")
    assert intent.get("action") in ("tax", "general")

@pytest.mark.asyncio
async def test_intent_parsing_health(orchestrator):
    intent = await orchestrator._parse_intent("Book a hospital appointment")
    assert intent.get("action") in ("health", "general")

@pytest.mark.asyncio
async def test_intent_parsing_finance(orchestrator):
    intent = await orchestrator._parse_intent("Transfer 100 tokens to user_xyz")
    assert intent.get("action") in ("finance", "general")

# ─── Plan creation ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_plan_is_created(orchestrator):
    """Planner produces a non-empty plan for a valid intent."""
    intent = {"action": "tax", "entities": {}}
    plan = await orchestrator.planner.create_plan(intent, "show tax", "u1", "citizen")
    assert isinstance(plan, dict)
    assert "steps" in plan

# ─── Verifier ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verifier_accepts_valid_plan(orchestrator):
    plan = {
        "intent": "tax",
        "steps": [{"agent": "tax", "action": "get_balance", "params": {}}],
        "verified": True,
    }
    result = await orchestrator.verifier.verify(plan)
    assert result is True

@pytest.mark.asyncio
async def test_verifier_rejects_empty_plan(orchestrator):
    plan = {"intent": "tax", "steps": []}
    result = await orchestrator.verifier.verify(plan)
    assert result is False
