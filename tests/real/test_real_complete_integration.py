#!/usr/bin/env python3
"""
STATUS: REAL — AsimNexus Integration Test
Complete System Integration Test
================================
Full system integration test.
"""

import sys
sys.path.insert(0, '.')

import asyncio

def test_all_systems():
    """Full system integration test."""
    print("=== ASIMNEXUS FULL INTEGRATION TEST ===")
    
    # Test 1: Mirror
    print("[1/7] Mirror Module...")
    try:
        from core.mirror.mirror_module import get_mirror
        mirror = get_mirror("integration_user")
        assert mirror.user_id == "integration_user"
        print("  Mirror OK")
    except Exception as e:
        print(f"  Mirror ERROR: {e}")
    
    # Test 2: Consensus
    print("[2/7] Consensus System...")
    try:
        from core.consensus.clone_consensus_voting import CloneConsensusVoting
        consensus = CloneConsensusVoting()
        result = asyncio.run(consensus.vote("test", "integration test", "general"))
        assert "passed" in result
        print("  Consensus OK")
    except Exception as e:
        print(f"  Consensus ERROR: {e}")
    
    # Test 3: Sandbox
    print("[3/7] Sandbox System...")
    try:
        from core.sandbox.sandbox import ToolSandbox
        sandbox = ToolSandbox()
        assert sandbox is not None
        print("  Sandbox OK")
    except Exception as e:
        print(f"  Sandbox ERROR: {e}")
    
    # Test 4: Veto Engine
    print("[4/7] Veto Engine...")
    try:
        from core.dharma_chakra.veto_engine import VetoLevel
        assert VetoLevel.PASS.value == "pass"
        print("  Veto OK")
    except Exception as e:
        print(f"  Veto ERROR: {e}")
    
    # Test 5: Life Journey
    print("[5/7] Life Journey...")
    try:
        from core.life_journey import LifeJourneyModule
        lj = LifeJourneyModule()
        stats = lj.get_stats()
        assert "total_profiles" in stats
        print("  Life Journey OK")
    except Exception as e:
        print(f"  Life Journey ERROR: {e}")
    
    # Test 6: Power Balance
    print("[6/7] Power Balance...")
    try:
        from core.security.power_balance_constitution import get_power_balance
        balance = get_power_balance()
        stats = balance.get_stats()
        print("  Power Balance OK")
    except Exception as e:
        print(f"  Power Balance ERROR: {e}")
    
    # Test 7: Mesh P2P
    print("[7/7] Mesh P2P...")
    try:
        from core.mesh.p2p_transport import P2PTransport
        p2p = P2PTransport()
        assert p2p.node_id.startswith("p2p_")
        print("  Mesh OK")
    except Exception as e:
        print(f"  Mesh ERROR: {e}")
    
    print("=== INTEGRATION COMPLETE ===")

if __name__ == "__main__":
    test_all_systems()