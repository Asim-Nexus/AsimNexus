#!/usr/bin/env python3
"""
STATUS: NEW — Mirror Module Tests
AsimNexus Mirror Module Unit Tests
=================================
Mirror Module functionality tests.
"""

import pytest
import asyncio
from datetime import date


def test_consciousness_layer():
    """Test Consciousness Layer."""
    from core.mirror.consciousness import ConsciousnessLayer
    
    layer = ConsciousnessLayer("test_user")
    state = layer.get_state()
    
    assert state["user_id"] == "test_user"
    assert "principles_count" in state


def test_mirror_singleton():
    """Test Mirror singleton pattern."""
    from core.mirror.mirror_module import get_mirror, MirrorModule
    
    m1 = get_mirror("user1")
    m2 = get_mirror("user1")
    
    assert m1 is m2
    assert isinstance(m1, MirrorModule)


def test_mirror_reflect():
    """Test Mirror reflect method."""
    from core.mirror.mirror_module import get_mirror
    
    mirror = get_mirror("reflect_test")
    reflection = asyncio.run(mirror.reflect({
        "intent": "help user",
        "outcome": "user satisfied"
    }))
    
    assert reflection.intent == "help user"
    assert len(reflection.contradictions) == 0


def test_sandbox_initialization():
    """Test Sandbox initialization."""
    from core.sandbox.sandbox import ToolSandbox
    
    sandbox = ToolSandbox()
    assert sandbox is not None


def test_consensus_voting():
    """Test Consensus voting."""
    from core.consensus.clone_consensus import CloneConsensus
    
    consensus = CloneConsensus()
    result = asyncio.run(consensus.vote({"title": "Test Proposal"}, "general"))
    
    assert "votes" in result
    assert "passed" in result


def test_mesh_imports():
    """Test Mesh module imports."""
    from mesh.p2p_transport import P2PTransport
    from mesh.crdt_sync import CRDTStore
    
    assert P2PTransport is not None
    assert CRDTStore is not None


if __name__ == "__main__":
    test_consciousness_layer()
    test_mirror_singleton()
    test_mirror_reflect()
    test_sandbox_initialization()
    test_consensus_voting()
    test_mesh_imports()
    print("All Mirror Module tests passed")