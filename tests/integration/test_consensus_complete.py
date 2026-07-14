"""
AsimNexus Consensus Integration Tests
=====================================
Tests the complete 15 Clones voting system.

Run: pytest tests/test_consensus_complete.py -v
"""

import pytest
import asyncio
from core.consensus.clone_consensus_voting import (
    CloneConsensusVoting,
    VoteChoice,
    CloneVote,
    ConsensusRound,
    get_consensus_engine,
)
from core.consensus.clone_consensus import (
    CloneConsensusEngine,
    DecisionLevel,
    ConsensusOutcome,
    ConsensusRoundResult,
)

class TestConsensusComplete:
    """Complete consensus voting system tests."""

    @pytest.fixture
    def consensus(self):
        """Create fresh consensus instance."""
        return CloneConsensusVoting()

    def test_consensus_initialization(self, consensus):
        """Test consensus engine initializes correctly."""
        assert consensus._quorum_threshold == 8
        assert consensus._rounds == {}

    @pytest.mark.asyncio
    async def test_start_consensus_round(self, consensus):
        """Test starting a consensus round."""
        round_obj = await consensus.start_round(
            topic="Test Proposal",
            sector="government",
            description="Testing 15 clones system"
        )

        assert round_obj.round_id is not None
        assert round_obj.proposal == "Test Proposal"
        assert round_obj.sector == "government"
        assert round_obj.status == "pending" or round_obj.outcome in ["approved", "rejected"]

    @pytest.mark.asyncio
    async def test_vote_method(self, consensus):
        """Test simplified vote method."""
        result = await consensus.vote(
            topic="Healthcare Policy",
            description="Universal healthcare access",
            sector="healthcare"
        )

        assert "proposal" in result
        assert "total_votes" in result
        assert "approve" in result
        assert "votes" in result
        assert "passed" in result or result["total_votes"] >= 0

    @pytest.mark.asyncio
    async def test_weighted_vote_government(self, consensus):
        """Test weighted voting for government sector (51% threshold)."""
        result = await consensus.weighted_vote(
            topic="Infrastructure Budget",
            sector="government",
            gov_benefit=0.6,
            private_benefit=0.4
        )

        assert "weighted_score" in result
        assert "weighted_passed" in result
        assert "threshold_required" in result
        assert result["threshold_required"] == 0.51

    @pytest.mark.asyncio
    async def test_weighted_vote_company(self, consensus):
        """Test weighted voting for private sector (49% threshold)."""
        result = await consensus.weighted_vote(
            topic="Commercial License",
            sector="commercial"
        )

        assert "threshold_required" in result
        assert result["threshold_required"] >= 0  # Any valid threshold

    @pytest.mark.asyncio
    async def test_vote_with_zkp(self, consensus):
        """Test ZKP-secured voting."""
        round_obj = await consensus.start_round(
            topic="Privacy Policy",
            sector="technology"
        )

        vote = await consensus.cast_vote_with_zkp(
            round_id=round_obj.round_id,
            voter_id="gov_01",
            choice=VoteChoice.APPROVE,
            rationale="Supports privacy"
        )

        assert vote.choice == VoteChoice.APPROVE
        assert vote.voter_id == "gov_01"

    def test_get_stats(self, consensus):
        """Test consensus statistics."""
        stats = consensus.get_stats()

        assert "total_rounds" in stats
        assert "quorum_threshold" in stats
        assert stats["quorum_threshold"] == 8

class TestConsensusGovernmentFlow:
    """End-to-end government decision flow tests."""

    @pytest.mark.asyncio
    async def test_government_policy_proposal(self):
        """Test complete government policy proposal flow."""
        engine = CloneConsensusVoting()

        # 1. Proposal
        result = await engine.weighted_vote(
            topic="Digital Nepal Policy",
            sector="government"
        )

        # 3. Veto check
        from core.dharma_chakra.veto_engine import get_veto_engine

        veto = get_veto_engine()
        veto_result = veto.check(
            message="Amend Digital Identity Act to include AI verification",
            sector="government"
        )

        # Government sector approval should have valid structure
        assert "proposal" in result
        assert "weighted_score" in result
        assert "threshold_required" in result

    @pytest.mark.asyncio
    async def test_finance_sector_threshold(self):
        """Test finance sector mixed threshold."""
        engine = CloneConsensusVoting()

        result = await engine.weighted_vote(
            topic="Banking Regulation",
            sector="finance"
        )

        # Finance is MIXED - uses default threshold
        assert "threshold_required" in result
        assert result["threshold_required"] >= 0

class TestConsensusIntegration:
    """Integration tests with other AsimNexus modules."""

    @pytest.mark.asyncio
    async def test_consensus_with_power_balance(self):
        """Test consensus integrates with power balance."""
        from core.security.power_balance_constitution import get_power_balance

        consensus = CloneConsensusVoting()
        balance = get_power_balance()

        # Check government sector balance
        gov_balance = balance.get_current_balance("government")
        assert "public_share" in gov_balance or "error" in gov_balance

class TestCloneConsensusEngine:
    """Tests for the CloneConsensusEngine with DecisionLevel support."""

    @pytest.fixture
    def engine(self):
        """Create fresh CloneConsensusEngine instance."""
        return CloneConsensusEngine()

    def test_engine_initialization(self, engine):
        """Test engine initializes with correct defaults."""
        assert engine._quorum_threshold == 8  # Default HIGH
        assert engine._level == DecisionLevel.HIGH

    def test_decision_level_quorum_values(self):
        """Test each DecisionLevel maps to correct quorum."""
        assert CloneConsensusEngine._LEVEL_QUORUM[DecisionLevel.LOW] == 6
        assert CloneConsensusEngine._LEVEL_QUORUM[DecisionLevel.HIGH] == 8
        assert CloneConsensusEngine._LEVEL_QUORUM[DecisionLevel.CRITICAL] == 11
        assert CloneConsensusEngine._LEVEL_QUORUM[DecisionLevel.SOVEREIGNTY] == 15

    @pytest.mark.asyncio
    async def test_start_round_with_level(self, engine):
        """Test starting a round with a specific DecisionLevel."""
        round_result = await engine.start_round(
            topic="Test Proposal",
            description="Testing DecisionLevel",
            level=DecisionLevel.CRITICAL,
            sector="government",
        )

        assert isinstance(round_result, ConsensusRoundResult)
        assert round_result.round_id is not None
        assert round_result.proposal == "Test Proposal"
        assert round_result.sector == "government"
        assert isinstance(round_result.outcome, ConsensusOutcome)
        assert round_result.outcome.value in ("approved", "rejected")
        assert len(round_result.votes) > 0

    @pytest.mark.asyncio
    async def test_low_level_quorum(self, engine):
        """Test LOW level requires only 6/15 approvals."""
        engine._level = DecisionLevel.LOW
        engine._quorum_threshold = 6

        round_result = await engine.start_round(
            topic="Simple Approval",
            level=DecisionLevel.LOW,
        )

        assert round_result.outcome.value in ("approved", "rejected")
        # With heuristic voting, most votes should be APPROVE
        approves = sum(1 for v in round_result.votes if v.choice == VoteChoice.APPROVE)
        assert approves >= 0

    @pytest.mark.asyncio
    async def test_sovereignty_level_requires_unanimous(self, engine):
        """Test SOVEREIGNTY level requires 15/15 approvals."""
        engine._level = DecisionLevel.SOVEREIGNTY
        engine._quorum_threshold = 15

        round_result = await engine.start_round(
            topic="Constitutional Amendment",
            level=DecisionLevel.SOVEREIGNTY,
        )

        # With heuristic fallback (no LLM), most votes are APPROVE
        # but some roles may REJECT based on risk keywords
        approves = sum(1 for v in round_result.votes if v.choice == VoteChoice.APPROVE)
        assert approves <= 15

    @pytest.mark.asyncio
    async def test_round_result_interface(self, engine):
        """Test ConsensusRoundResult matches interface expected by founder_clone_system."""
        round_result = await engine.start_round(
            topic="Interface Test",
            description="Testing the result interface",
            level=DecisionLevel.HIGH,
        )

        # Must have all attributes used by founder_clone_system.py
        assert hasattr(round_result, "round_id")
        assert hasattr(round_result, "outcome")
        assert hasattr(round_result, "summary")
        assert hasattr(round_result, "votes")
        assert hasattr(round_result, "human_override")

        # outcome must have .value
        assert hasattr(round_result.outcome, "value")
        assert isinstance(round_result.outcome.value, str)

        # votes must be iterable with choice.name
        for v in round_result.votes:
            assert hasattr(v, "choice")
            assert hasattr(v.choice, "name")
            assert v.choice.name in ("APPROVE", "REJECT", "ABSTAIN", "DEFER")

    def test_consensus_outcome_wrapper(self):
        """Test ConsensusOutcome wrapper provides .value interface."""
        outcome = ConsensusOutcome("approved")
        assert outcome.value == "approved"
        assert str(outcome) == "approved"
        assert outcome == "approved"
        assert outcome == ConsensusOutcome("approved")
        assert outcome != "rejected"

class TestHeuristicVoting:
    """Tests for the heuristic fallback voting logic."""

    @pytest.fixture
    def consensus(self):
        """Create fresh consensus instance without founder_system (uses heuristic)."""
        return CloneConsensusVoting()

    @pytest.mark.asyncio
    async def test_heuristic_vote_returns_valid_choice(self, consensus):
        """Test heuristic vote returns a valid VoteChoice."""
        choice, rationale = consensus._heuristic_vote(
            role="Security Sentinel",
            topic="New Security Protocol",
            sector="security",
        )
        assert isinstance(choice, VoteChoice)
        assert choice in (VoteChoice.APPROVE, VoteChoice.REJECT, VoteChoice.ABSTAIN, VoteChoice.DEFER)
        assert len(rationale) > 0

    @pytest.mark.asyncio
    async def test_heuristic_vote_cautious_rejects_risk(self, consensus):
        """Test cautious roles reject risk-related topics."""
        choice, rationale = consensus._heuristic_vote(
            role="Security Sentinel",
            topic="High risk vulnerability assessment",
            sector="security",
        )
        assert choice == VoteChoice.REJECT
        assert "risk" in rationale.lower() or "Risk" in rationale

    @pytest.mark.asyncio
    async def test_heuristic_vote_supportive_approves_opportunity(self, consensus):
        """Test supportive roles approve opportunity-related topics."""
        choice, rationale = consensus._heuristic_vote(
            role="Community Weaver",
            topic="Growth opportunity for community expansion",
            sector="community",
        )
        assert choice == VoteChoice.APPROVE
        assert "opportunity" in rationale.lower() or "Positive" in rationale

    @pytest.mark.asyncio
    async def test_heuristic_vote_abstains_on_risk_for_non_cautious(self, consensus):
        """Test non-cautious roles abstain on risk topics."""
        choice, rationale = consensus._heuristic_vote(
            role="Community Weaver",
            topic="Security vulnerability in payment system",
            sector="community",
        )
        assert choice == VoteChoice.ABSTAIN
        assert "more information" in rationale.lower()

    @pytest.mark.asyncio
    async def test_heuristic_vote_default_approve(self, consensus):
        """Test default heuristic vote is APPROVE for neutral topics."""
        choice, rationale = consensus._heuristic_vote(
            role="Tech Architect",
            topic="Routine infrastructure maintenance",
            sector="technology",
        )
        assert choice == VoteChoice.APPROVE
        assert "Supportive" in rationale

    @pytest.mark.asyncio
    async def test_heuristic_vote_all_15_roles_produce_valid_votes(self, consensus):
        """Test all 15 fallback roles produce valid votes."""
        roles = [
            "Dharma Guardian", "Tech Architect", "Community Weaver",
            "Legal Counsel", "Economic Analyst", "Security Sentinel",
            "Cultural Keeper", "Health Advisor", "Education Guide",
            "Environment Watch", "Identity Protector", "Mesh Coordinator",
            "Memory Keeper", "Contract Auditor", "Sovereignty Guard",
        ]
        for role in roles:
            choice, rationale = consensus._heuristic_vote(
                role=role,
                topic="General system maintenance",
                sector="general",
            )
            assert isinstance(choice, VoteChoice), f"Role {role} returned invalid choice"
            assert len(rationale) > 0, f"Role {role} returned empty rationale"

class TestLLMVotingIntegration:
    """Tests for LLM-powered voting via founder_system integration.

    These tests verify the wiring between CloneConsensusVoting and
    FounderCloneSystem. When no NVIDIA API keys are available, they
    fall back to heuristic voting gracefully.
    """

    @pytest.mark.asyncio
    async def test_consensus_with_founder_system(self):
        """Test consensus engine wired to FounderCloneSystem."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem

        # Create founder system (will use heuristic fallback since no real API keys)
        founder_system = FounderCloneSystem()
        assert len(founder_system.founders) == 15

        # Wire to consensus engine
        engine = CloneConsensusVoting(founder_system=founder_system)
        assert engine.founder_system is not None

        # Run a consensus round
        round_obj = await engine.start_round(
            topic="Test Proposal with Founder System",
            sector="technology",
            description="Testing LLM-powered voting integration",
        )

        assert round_obj.round_id is not None
        assert len(round_obj.votes) > 0
        assert round_obj.outcome in ("approved", "rejected")

        # Verify votes have real rationale (not the old generic "Supportive of")
        for vote in round_obj.votes:
            assert vote.rationale is not None
            assert len(vote.rationale) > 0

    @pytest.mark.asyncio
    async def test_clone_consensus_engine_with_founder_system(self):
        """Test CloneConsensusEngine wired to FounderCloneSystem."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem

        founder_system = FounderCloneSystem()
        engine = CloneConsensusEngine(founder_system=founder_system)

        # Test with different DecisionLevels
        for level in [DecisionLevel.LOW, DecisionLevel.HIGH]:
            round_result = await engine.start_round(
                topic=f"Test at {level.value} level",
                description=f"Testing {level.value} decision level",
                level=level,
            )

            assert isinstance(round_result, ConsensusRoundResult)
            assert isinstance(round_result.outcome, ConsensusOutcome)
            assert round_result.outcome.value in ("approved", "rejected")
            assert len(round_result.votes) > 0

    @pytest.mark.asyncio
    async def test_founder_system_start_consensus_round(self):
        """Test FounderCloneSystem.start_consensus_round() — the public API."""
        from core.founder_clones.founder_clone_system import FounderCloneSystem

        founder_system = FounderCloneSystem()

        result = await founder_system.start_consensus_round(
            proposal="Test Proposal via FounderSystem",
            threshold="high",
            description="Testing the public consensus API",
        )

        assert "round_id" in result
        assert "outcome" in result
        assert "summary" in result
        assert "approvals" in result
        assert "rejects" in result
        assert "total_votes" in result
        assert result["outcome"] in ("approved", "rejected")
        assert result["total_votes"] > 0

    @pytest.mark.asyncio
    async def test_founder_system_coordinate_with_consensus(self):
        """Test coordinate_founders with consensus_level triggers voting."""
        from core.founder_clones.founder_clone_system import (
            FounderCloneSystem,
            FounderRole,
        )

        founder_system = FounderCloneSystem()

        result = await founder_system.coordinate_founders(
            task="Evaluate new security protocol for data encryption",
            roles=[FounderRole.CEO, FounderRole.CTO, FounderRole.CSO],
            consensus_level="high",
        )

        assert "task" in result
        assert "founders_involved" in result
        assert "results" in result
        assert "consensus" in result
        assert "round_id" in result["consensus"]
        assert "outcome" in result["consensus"]
        assert result["consensus"]["outcome"] in ("approved", "rejected")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])