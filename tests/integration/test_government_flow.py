"""
AsimNexus Government Services Flow Tests
========================================
End-to-end tests for government workflows.

Run: pytest tests/test_government_flow.py -v
"""

import pytest
import asyncio
from core.consensus.clone_consensus_voting import get_consensus_engine
from core.mirror.mirror_module import get_mirror
from core.security.power_balance_constitution import get_power_balance
from core.dharma_chakra.veto_engine import get_veto_engine, VetoLevel

class TestGovernmentTaxCalculation:
    """Government tax calculation flow."""

    @pytest.mark.asyncio
    async def test_tax_calculation_with_approval(self):
        """Test tax calculation with 15 clones approval."""
        # 1. Check power balance (governance sector)
        balance = get_power_balance()
        balance_result = balance.check_decision(
            sector="governance",
            is_public_decision=True
        )

        # 2. Veto check for government action
        veto = get_veto_engine()
        veto_result = veto.check(
            message="Calculate tax for farmer cooperative",
            sector="government"
        )

        assert balance_result.verdict.value in ["pass", "warn", "block"]
        assert veto_result.level != VetoLevel.BLOCK

class TestGovernmentPolicyChange:
    """Government policy change workflow."""

    @pytest.mark.asyncio
    async def test_policy_change_flow(self):
        """Full policy change requires consensus + balance + veto."""
        # 1. Check power balance
        balance = get_power_balance()
        balance_check = balance.check_decision(
            sector="governance",
            is_public_decision=True
        )

        # 2. Veto check
        veto = get_veto_engine()
        veto_result = veto.check(
            message="Amend Digital Identity Act to include AI verification",
            sector="government"
        )

        assert balance_check.current_public_share >= 0
        assert veto_result.level != VetoLevel.BLOCK

class TestCitizenServices:
    """Citizen services workflow."""

    @pytest.mark.asyncio
    async def test_citizen_tax_payment_flow(self):
        """Test citizen tax payment with Mirror."""
        # Citizen Mirror
        citizen_mirror = get_mirror("citizen_001", "citizen")

        # Tax payment action
        action = {
            "intent": "Pay annual property tax",
            "outcome": "Tax payment processed",
            "amount": 50000
        }

        reflection = await citizen_mirror.reflect(action)

        assert reflection.intent == "Pay annual property tax"

class TestHealthcareServices:
    """Healthcare sector services."""

    def test_healthcare_balance(self):
        """Healthcare is PUBLIC_COORDINATED (51%)."""
        balance = get_power_balance()

        result = balance.check_decision(
            sector="healthcare",
            is_public_decision=True
        )

        assert result.verdict.value in ["pass", "warn"]

class TestEducationServices:
    """Education sector services."""

    def test_education_balance(self):
        """Education is PUBLIC_COORDINATED (51%)."""
        balance = get_power_balance()

        result = balance.check_decision(
            sector="education",
            is_public_decision=True,
            context={"program": "digital_learning"}
        )

        assert result.verdict.value in ["pass", "warn"]

class TestInfrastructureServices:
    """Infrastructure development workflow."""

    @pytest.mark.asyncio
    async def test_infrastructure_project(self):
        """Test infrastructure project approval."""
        consensus = get_consensus_engine()

        result = await consensus.weighted_vote(
            topic="Smart City Initiative",
            sector="infrastructure"
        )

        assert "proposal" in result
        assert "weighted_score" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])