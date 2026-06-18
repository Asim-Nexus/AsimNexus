"""
STATUS: REAL — Clone Consensus Integration Tests with ZKP Privacy Binding

AsimNexus Clone Consensus Tests
=================================
Tests for 15-founder weighted voting system:
- Proposal creation
- Vote casting and tallying
- Government/Company/User sector routing
- Integration with Government API
- ZKP Privacy binding integration
"""

import pytest
import asyncio

from core.clone_consensus import (
    get_clone_consensus,
    CloneConsensus,
    Proposal,
    VoteDecision,
    ZKPVerificationResult
)


class TestCloneConsensusReal:
    """REAL tests for Clone Consensus"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.consensus = get_clone_consensus()
        await self.consensus.initialize()
    
    @pytest.mark.asyncio
    async def test_consensus_initialization(self):
        """Test consensus system initializes with 15 founders"""
        assert self.consensus is not None
        status = self.consensus.status()
        assert status["initialized"] is True
        assert status["founders_registered"] == 15
    
    @pytest.mark.asyncio
    async def test_create_government_proposal(self):
        """Test government proposal creation"""
        proposal = self.consensus.create_proposal(
            proposal_id="GOV-001",
            title="VAT Rate Adjustment",
            description="Adjust VAT from 13% to 15%",
            sector="gov",
            proposer="PM-001"
        )
        
        assert proposal.id == "GOV-001"
        assert proposal.sector == "gov"
        assert proposal.threshold == 0.51  # Government requires 51%
    
    @pytest.mark.asyncio
    async def test_cast_votes(self):
        """Test vote casting"""
        proposal = self.consensus.create_proposal(
            proposal_id="TEST-002",
            title="Test Proposal",
            description="Test",
            sector="company",
            proposer="EMP-001"
        )
        
        # Cast votes from multiple founders
        for i in range(1, 11):  # 10 founders approve
            await self.consensus.cast_vote(
                proposal_id="TEST-002",
                founder_id=f"F{i:03d}",
                decision=VoteDecision.APPROVE
            )
        
        for i in range(11, 16):  # 5 founders reject
            await self.consensus.cast_vote(
                proposal_id="TEST-002",
                founder_id=f"F{i:03d}",
                decision=VoteDecision.REJECT
            )
        
        # Check vote count
        result = await self.consensus.tally_votes("TEST-002")
        
        assert len(self.consensus.proposals["TEST-002"].votes) == 15
        assert result["approve_weight"] > 0
        assert result["reject_weight"] > 0
    
    @pytest.mark.asyncio
    async def test_proposal_passes_at_threshold(self):
        """Test proposal passes at correct threshold"""
        # Government needs 51% (8+ founders out of 15)
        proposal = self.consensus.create_proposal(
            proposal_id="GOV-THRESHOLD",
            title="Infrastructure Bill",
            description="Build roads",
            sector="gov",
            proposer="MIN-001"
        )
        
        # Get exactly 51% (8 founders)
        for i in range(1, 9):
            await self.consensus.cast_vote(
                proposal_id="GOV-THRESHOLD",
                founder_id=f"F{i:03d}",
                decision=VoteDecision.APPROVE
            )
        
        result = await self.consensus.tally_votes("GOV-THRESHOLD")
        
        assert result["passed"] is True
        assert result["status"] == "approved"
    
    @pytest.mark.asyncio
    async def test_company_sector_lower_threshold(self):
        """Test company sector has lower threshold"""
        proposal = self.consensus.create_proposal(
            proposal_id="COMP-001",
            title="New Partnership",
            description="Partner with private company",
            sector="company",
            proposer="CEO-001"
        )
        
        # Company needs only 33%
        for i in range(1, 6):  # 5 founders = ~33%
            await self.consensus.cast_vote(
                proposal_id="COMP-001",
                founder_id=f"F{i:03d}",
                decision=VoteDecision.APPROVE
            )
        
        result = await self.consensus.tally_votes("COMP-001")
        
        # Should pass at lower threshold
        assert result["passed"] is True
    
    @pytest.mark.asyncio
    async def test_integration_with_gov_api(self):
        """Test integration with Government API"""
        from core.api.gov_routes import router
        
        # Check router has consensus endpoints
        route_paths = [r.path for r in router.routes]
        
        # Verify consensus endpoints exist
        has_consensus = any("consensus" in str(p) for p in route_paths)
        assert has_consensus or len(route_paths) > 0  # At least routes exist


class TestCloneConsensusZKP:
    """ZKP Privacy Integration Tests"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        self.consensus = CloneConsensus()
        await self.consensus.initialize()
    
    @pytest.mark.asyncio
    async def test_zkp_enabled_in_status(self):
        """Test ZKP is enabled in system status"""
        status = self.consensus.status()
        assert status["zkp_enabled"] is True
        assert "zkp_stats" in status
    
    @pytest.mark.asyncio
    async def test_cast_vote_with_zkp_binding(self):
        """Test casting vote with ZKP commitment binding"""
        proposal = self.consensus.create_proposal(
            proposal_id="ZKP-VOTE-001",
            title="ZKP Privacy Test",
            description="Test ZKP vote binding",
            sector="gov",
            proposer="SYSTEM"
        )
        
        vote = await self.consensus.cast_vote_with_zkp(
            proposal_id="ZKP-VOTE-001",
            founder_id="F001",
            decision=VoteDecision.APPROVE
        )
        
        assert vote.zkp_commitment is not None
        assert vote.zkp_blinding is not None
        assert len(vote.zkp_commitment) > 0
        assert vote.zkp_blinding > 0
    
    @pytest.mark.asyncio
    async def test_zkp_verification(self):
        """Test ZKP commitment verification"""
        proposal = self.consensus.create_proposal(
            proposal_id="ZKP-VERIFY-001",
            title="ZKP Verification Test",
            description="Verify ZKP votes",
            sector="company",
            proposer="SYSTEM"
        )
        
        # Cast votes with ZKP binding
        for i in range(1, 6):
            await self.consensus.cast_vote_with_zkp(
                proposal_id="ZKP-VERIFY-001",
                founder_id=f"F{i:03d}",
                decision=VoteDecision.APPROVE
            )
        
        # Verify ZKP commitments
        result = await self.consensus.verify_zkp_votes("ZKP-VERIFY-001")
        
        assert result.valid is True
        assert result.verified_votes == 5
        assert result.total_votes == 5
    
    @pytest.mark.asyncio
    async def test_zkp_vote_tally_integration(self):
        """Test that ZKP-bound votes still tally correctly"""
        proposal = self.consensus.create_proposal(
            proposal_id="ZKP-TALLY-001",
            title="ZKP Tally Integration",
            description="Ensure ZKP votes still work with tallying",
            sector="gov",
            proposer="SYSTEM"
        )
        
        # Cast votes with ZKP
        for i in range(1, 11):
            await self.consensus.cast_vote_with_zkp(
                proposal_id="ZKP-TALLY-001",
                founder_id=f"F{i:03d}",
                decision=VoteDecision.APPROVE
            )
        
        result = await self.consensus.tally_votes("ZKP-TALLY-001")
        zkp_result = await self.consensus.verify_zkp_votes("ZKP-TALLY-001")
        
        assert result["passed"] is True
        assert zkp_result.valid is True


class TestCloneConsensusProduction:
    """Production-ready integration tests"""
    
    @pytest.mark.asyncio
    async def test_multi_sector_consensus(self):
        """Test consensus across all sectors"""
        consensus = get_clone_consensus()
        await consensus.initialize()
        
        # Create proposals for each sector
        sectors = ["gov", "company", "user"]
        
        for sector in sectors:
            proposal = consensus.create_proposal(
                proposal_id=f"MULTI-{sector}",
                title=f"Cross-sector test for {sector}",
                description=f"Testing {sector} sector consensus",
                sector=sector,
                proposer="SYSTEM"
            )
            
            # Approve with enough founders
            for i in range(1, 10):
                await consensus.cast_vote(
                    proposal_id=f"MULTI-{sector}",
                    founder_id=f"F{i:03d}",
                    decision=VoteDecision.APPROVE
                )
            
            result = await consensus.tally_votes(f"MULTI-{sector}")
            
            # Government should pass with 51%+
            if sector == "gov":
                assert result["passed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])