"""
Consensus Voting Tests - Direct import
"""
from core.consensus.clone_consensus_voting import CloneConsensusVoting

def test_consensus_engine_import():
    """Consensus engine can be imported."""
    assert CloneConsensusVoting is not None

def test_consensus_engine_instantiation():
    """Consensus engine can be instantiated."""
    engine = CloneConsensusVoting()
    stats = engine.get_stats()
    assert "total_rounds" in stats

def test_consensus_vote_sync():
    """Test consensus voting synchronously."""
    import asyncio
    engine = CloneConsensusVoting()
    # Use heuristic voting (no founder system)
    result = asyncio.run(engine.vote("नेपाली सरकार", "government", "Test proposal"))
    assert "proposal" in result
    assert "total_votes" in result
    assert result["total_votes"] == 15  # 15 clones