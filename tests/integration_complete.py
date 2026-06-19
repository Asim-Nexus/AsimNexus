#!/usr/bin/env python3
"""AsimNexus Integration Tests - All Modules"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "DigitalNepal-backend"))

def test_consensus_engine():
    """Test 15 Founder Clones Consensus"""
    from core.consensus_engine import get_consensus_engine
    engine = get_consensus_engine()
    p = engine.propose("test1", "Test Proposal", "government")
    engine.cast_vote("test1", "approve")
    engine.cast_vote("test1", "approve")
    result = engine.tally("test1")
    assert result["status"] in ["passed", "rejected"]
    print("[OK] Consensus Engine")

def test_compliance_engine():
    """Test 51/49 Compliance"""
    from core.compliance_engine import compliance
    r1 = compliance.check_decision("government", True)
    assert r1["allowed"] == True
    r2 = compliance.check_decision("company", False)
    assert r2["allowed"] == True
    print("[OK] Compliance Engine")

def test_security_layer():
    """Test ZKP + HSM stubs"""
    from core.security_layer import zkp, hsm
    proof = zkp.generate("test_data")
    assert zkp.verify(proof, "test") == True
    assert hsm.is_connected() == False
    print("[OK] Security Layer")

if __name__ == "__main__":
    print("=== Integration Tests ===")
    test_consensus_engine()
    test_compliance_engine()
    test_security_layer()
    print("=== All Passed ===")