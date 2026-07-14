#!/usr/bin/env python3
"""
AsimNexus Security Tests
========================
Tests for production ZKP and HSM implementations.
"""

import pytest
from core.security.zkp_production import ProductionZKP, get_zkp, PedersenCommitment
from core.security.hsm_production import ProductionHSM, get_hsm

class TestProductionZKP:
    """Production ZKP tests."""

    @pytest.fixture
    def zkp(self):
        return ProductionZKP()

    @pytest.mark.asyncio
    async def test_zkp_initialization(self, zkp):
        """Test ZKP initializes correctly."""
        assert zkp._ezkl_available in [True, False]

    @pytest.mark.asyncio
    async def test_demo_proof_generation(self, zkp):
        """Test demo proof generation."""
        result = await zkp.generate_proof(
            statement="Test statement",
            witness={"field": "value"}
        )

        assert "proof" in result
        assert "verified" in result
        assert result["verified"] is True

    @pytest.mark.asyncio
    async def test_zkp_verification(self, zkp):
        """Test proof verification."""
        proof_data = await zkp.generate_proof(
            statement="Verify me",
            witness={"secret": "hidden"}
        )

        verified = await zkp.verify_proof(proof_data)
        assert verified is True

class TestProductionHSM:
    """Production HSM tests."""

    @pytest.fixture
    def hsm(self):
        return ProductionHSM()

    def test_hsm_initialization(self, hsm):
        """Test HSM initializes correctly."""
        assert hsm._available in [True, False]

    @pytest.mark.asyncio
    async def test_demo_signing(self, hsm):
        """Test demo signing works."""
        result = await hsm.sign_level3("test_data")

        assert result["signed"] is True
        assert "signature" in result

    @pytest.mark.asyncio
    async def test_hsm_status(self, hsm):
        """Test HSM status retrieval."""
        status = hsm.get_status()

        assert "available" in status
        assert "type" in status

class TestLegacyCompatibility:
    """Legacy compatibility tests."""

    def test_pedersen_commitment(self):
        """Test Pedersen commitment demo."""
        commitment, nonce = PedersenCommitment.commit("test_message")

        assert commitment is not None
        assert nonce is not None

    def test_pedersen_verify(self):
        """Test Pedersen verification."""
        commitment, nonce = PedersenCommitment.commit("test_message")
        verified = PedersenCommitment.verify(commitment, "test_message", nonce)

        assert verified is True

class TestSingletonFactories:
    """Singleton factory tests."""

    def test_get_zkp(self):
        """Test ZKP singleton."""
        instance1 = get_zkp()
        instance2 = get_zkp()
        assert instance1 is instance2

    def test_get_hsm(self):
        """Test HSM singleton."""
        instance1 = get_hsm()
        instance2 = get_hsm()
        assert instance1 is instance2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])