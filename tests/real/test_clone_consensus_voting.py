"""
STATUS: REAL — Clone Consensus Voting Engine Integration Tests with ZKP Privacy

Tests for 8/15 approval threshold Constitutional AI Council voting with ZKP integration.
"""

import pytest
import asyncio
from core.consensus.clone_consensus_voting import (
    CloneConsensusVoting,
    VoteChoice,
    CloneVote,
    get_consensus_engine
)


class TestCloneConsensusVotingZKP:
    """ZKP Privacy Integration Tests for CloneConsensusVoting"""
    
    @pytest.fixture
    def engine(self):
        """Create consensus engine for testing"""
        return CloneConsensusVoting()
    
    @pytest.mark.asyncio
    async def test_zkp_enabled_in_stats(self, engine):
        """Test ZKP is reported in engine stats"""
        stats = engine.get_stats()
        assert "zkp_enabled" in stats
        assert stats["zkp_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_cast_vote_with_zkp_binding(self, engine):
        """Test casting vote with ZKP commitment binding"""
        round_obj = engine.start_round(
            topic="Test Proposal",
            sector="test",
            description="Testing ZKP vote binding"
        )
        
        vote = await engine.cast_vote_with_zkp(
            round_id=round_obj.round_id,
            voter_id="CEO",
            choice=VoteChoice.APPROVE,
            rationale="Test vote with ZKP"
        )
        
        assert vote.zkp_commitment is not None
        assert vote.zkp_blinding is not None
        assert len(vote.zkp_commitment) > 0
    
    @pytest.mark.asyncio
    async def test_zkp_verification_success(self, engine):
        """Test ZKP commitment verification passes"""
        round_obj = engine.start_round(
            topic="ZKP Verification Test",
            sector="test",
            description="Verify ZKP votes"
        )
        
        # Cast votes with ZKP
        for i in range(1, 6):
            await engine.cast_vote_with_zkp(
                round_id=round_obj.round_id,
                voter_id=f"FOUNDER_{i}",
                choice=VoteChoice.APPROVE,
                rationale="Test"
            )
        
        # Verify ZKP commitments
        result = engine.verify_zkp_votes(round_obj.round_id)
        
        assert result["valid"] is True
        assert result["verified_votes"] == 5
        assert result["total_votes"] == 5
    
    @pytest.mark.asyncio
    async def test_zkp_vote_tally_integration(self, engine):
        """Test that ZKP-bound votes contribute to tally correctly"""
        round_obj = engine.start_round(
            topic="ZKP Tally Integration",
            sector="test",
            description="Ensure ZKP votes work with tallying"
        )
        
        # Cast votes with ZKP
        for i in range(1, 9):
            await engine.cast_vote_with_zkp(
                round_id=round_obj.round_id,
                voter_id=f"FOUNDER_{i}",
                choice=VoteChoice.APPROVE,
                rationale="Approve"
            )
        
        # Verify outcome
        assert round_obj.outcome == "approved"
        
        # Verify ZKP
        zkp_result = engine.verify_zkp_votes(round_obj.round_id)
        assert zkp_result["valid"] is True


class TestCloneVoteWithZKP:
    """Test CloneVote dataclass with ZKP fields"""
    
    def test_vote_creation_with_zkp(self):
        """CloneVote can be created with ZKP fields"""
        vote = CloneVote(
            voter_id="CEO",
            voter_role="Chief Executive Officer",
            choice=VoteChoice.APPROVE,
            rationale="Strategic alignment confirmed",
            zkp_commitment="abc123",
            zkp_blinding=987654
        )
        assert vote.voter_id == "CEO"
        assert vote.zkp_commitment == "abc123"
        assert vote.zkp_blinding == 987654
    
    def test_vote_to_dict_includes_zkp(self):
        """to_dict includes ZKP fields"""
        vote = CloneVote(
            voter_id="CEO",
            voter_role="CEO",
            choice=VoteChoice.APPROVE,
            rationale="Test",
            zkp_commitment="commit123",
            zkp_blinding=42
        )
        d = vote.to_dict()
        assert "zkp_commitment" in d
        assert d["zkp_commitment"] == "commit123"


class TestCloneConsensusVotingProduction:
    """Production-ready integration tests"""
    
    @pytest.mark.asyncio
    async def test_multi_sector_consensus_with_zkp(self):
        """Test consensus across sectors with ZKP verification"""
        engine = get_consensus_engine()
        
        sectors = ["gov", "company", "user"]
        
        for sector in sectors:
            round_obj = engine.start_round(
                topic=f"Cross-sector test for {sector}",
                sector=sector,
                description=f"Testing {sector} sector consensus"
            )
            
            # Add votes with ZKP
            for i in range(1, 9):
                await engine.cast_vote_with_zkp(
                    round_id=round_obj.round_id,
                    voter_id=f"FOUNDER_{i}",
                    choice=VoteChoice.APPROVE,
                    rationale="Sector approval"
                )
            
            # For gov sector, should pass with 8/15
            if sector == "gov":
                assert round_obj.outcome == "approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])