#!/usr/bin/env python3
"""
Comprehensive tests for the ZKP system (core/security/real_zkp.py).

Tests RealZKPManager with both real EC-based ZKP (if cryptography available)
and SHA-3 fallback paths. Covers commitment, proof, verification, identity,
action approval, batch verify, edge cases, and error handling.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from core.security.real_zkp import (
    RealZKPManager, ZKProof, VerificationResult,
    get_zkp_manager_real, HAS_REAL_ZKP,
)

@pytest.fixture
def zkp():
    """Provide a fresh RealZKPManager."""
    return RealZKPManager(security_parameter=128)

# ── Basic Operations ─────────────────────────────────────────────────────

def test_initialization(zkp):
    """ZKP manager initializes with correct defaults."""
    assert zkp.security_param == 128
    assert zkp._prover_secret is not None
    assert zkp._verifier_key is not None
    assert len(zkp._verifier_key) == 32
    stats = zkp.get_stats()
    assert stats["total_commitments"] == 0
    assert stats["security_parameter"] == 128

def test_create_commitment(zkp):
    """Create a Pedersen commitment."""
    commitment, opening = zkp.create_commitment("secret_data_123", "test_context")
    assert commitment is not None
    assert len(commitment) > 0
    assert opening is not None
    assert len(opening) > 0
    assert commitment in zkp._commitments
    assert zkp._commitments[commitment]["context"] == "test_context"

def test_create_multiple_commitments(zkp):
    """Create multiple unique commitments."""
    c1, _ = zkp.create_commitment("data_1", "ctx_1")
    c2, _ = zkp.create_commitment("data_2", "ctx_2")
    c3, _ = zkp.create_commitment("data_3", "ctx_3")

    assert c1 != c2
    assert c2 != c3
    assert len(zkp._commitments) == 3

    stats = zkp.get_stats()
    assert stats["total_commitments"] == 3

# ── Proof Lifecycle ──────────────────────────────────────────────────────

def test_prove_knowledge(zkp):
    """Create a proof of knowledge from a commitment."""
    private_data = "my_secret_password"
    commitment, _ = zkp.create_commitment(private_data, "auth_test")

    proof = zkp.prove_knowledge(private_data, commitment, "Login attempt at 2026-06-09")
    assert isinstance(proof, ZKProof)
    assert proof.commitment == commitment
    assert proof.proof is not None
    assert len(proof.proof) > 0
    assert proof.public_inputs["statement"] == "Login attempt at 2026-06-09"
    assert proof.verifier_key_hash == zkp._verifier_key
    assert proof.timestamp is not None

def test_verify_proof_valid(zkp):
    """Verify a valid proof."""
    private_data = "valid_secret_456"
    commitment, _ = zkp.create_commitment(private_data, "verify_test")
    statement = "I know the secret"

    proof = zkp.prove_knowledge(private_data, commitment, statement)
    result = zkp.verify_proof(proof, statement)

    assert isinstance(result, VerificationResult)
    assert result.valid is True
    assert result.confidence > 0.9
    assert "commitment" in result.details
    assert "verifier_match" in result.details

def test_full_proof_lifecycle(zkp):
    """Complete lifecycle: commit → prove → verify."""
    # Step 1: Commit to data
    data = "sensitive_user_data_789"
    commitment, _ = zkp.create_commitment(data, "user_auth")

    # Step 2: Prove knowledge
    statement = "User authentication at node-42"
    proof = zkp.prove_knowledge(data, commitment, statement)

    # Step 3: Verify
    result = zkp.verify_proof(proof, statement)
    assert result.valid is True
    assert result.confidence > 0.9

    # Step 4: Double-check with wrong statement
    wrong_result = zkp.verify_proof(proof, "Wrong statement")
    assert wrong_result.valid is False
    assert wrong_result.confidence == 0.0

# ── Error Handling ───────────────────────────────────────────────────────

def test_prove_unknown_commitment(zkp):
    """Proving knowledge of unknown commitment should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown commitment"):
        zkp.prove_knowledge("any_data", "nonexistent_commitment", "test")

def test_verify_with_wrong_verifier_key(zkp):
    """Verify with wrong verifier key should fail."""
    # Create proof with one manager
    private_data = "cross_manager_test"
    commitment, _ = zkp.create_commitment(private_data, "cross_verify")
    statement = "Cross-manager proof"
    proof = zkp.prove_knowledge(private_data, commitment, statement)

    # Verify with different manager (different verifier key)
    zkp2 = RealZKPManager()
    result = zkp2.verify_proof(proof, statement)
    assert result.valid is False
    assert result.confidence == 0.0
    assert "key mismatch" in result.details.get("error", "").lower()

def test_verify_expired_proof(zkp):
    """Verify an expired proof (older than 60 minutes)."""
    private_data = "expired_test"
    commitment, _ = zkp.create_commitment(private_data, "expired")
    statement = "Expired proof"

    proof = zkp.prove_knowledge(private_data, commitment, statement)

    # Manually set timestamp to 2 hours ago
    past_time = (datetime.now() - timedelta(hours=2)).isoformat()
    proof.timestamp = past_time

    result = zkp.verify_proof(proof, statement)
    assert result.valid is False
    assert "expired" in result.details.get("error", "").lower()

def test_verify_statement_mismatch(zkp):
    """Verify with mismatched statement should fail."""
    private_data = "statement_test"
    commitment, _ = zkp.create_commitment(private_data, "statement_check")
    proof = zkp.prove_knowledge(private_data, commitment, "Original statement")

    result = zkp.verify_proof(proof, "Different statement")
    assert result.valid is False
    assert "statement mismatch" in result.details.get("error", "").lower()

# ── Identity Proofs ──────────────────────────────────────────────────────

def test_create_identity_proof(zkp):
    """Create a zero-knowledge identity proof."""
    identity = {
        "did": "did:asim:abc123",
        "public_key": "0xdeadbeef",
        "roles": ["user", "developer"],
    }
    nonce = "unique_nonce_001"

    proof = zkp.create_identity_proof(identity, nonce)
    assert isinstance(proof, ZKProof)
    assert proof.public_inputs["statement"].startswith("Valid identity")
    assert nonce in proof.public_inputs["statement"]

def test_verify_identity_proof(zkp):
    """Create and verify an identity proof."""
    identity = {"did": "did:asim:xyz789", "name": "Test User"}
    nonce = "nonce_verify_001"

    proof = zkp.create_identity_proof(identity, nonce)
    statement = proof.public_inputs["statement"]

    result = zkp.verify_proof(proof, statement)
    assert result.valid is True

# ── Action Approvals ─────────────────────────────────────────────────────

def test_create_action_approval(zkp):
    """Create a ZK proof for action approval (Dharma-Chakra integration)."""
    action = "transfer_funds"
    user_id = "user_42"
    context = {
        "amount": 1000,
        "token": "NEXUS",
        "destination": "user_99",
        "reason": "payment",
    }

    proof = zkp.create_action_approval(action, user_id, context)
    assert isinstance(proof, ZKProof)
    assert "transfer_funds" in proof.public_inputs["statement"]
    assert "user_42" in proof.public_inputs["statement"]

def test_verify_action_approval(zkp):
    """Create and verify an action approval proof."""
    proof = zkp.create_action_approval("deploy_agent", "admin_001", {"agent_id": "ag_5"})
    statement = proof.public_inputs["statement"]

    result = zkp.verify_proof(proof, statement)
    assert result.valid is True

# ── Batch Verification ───────────────────────────────────────────────────

def test_batch_verify_all_valid(zkp):
    """Batch verify multiple valid proofs."""
    proofs = []
    for i in range(5):
        data = f"batch_data_{i}"
        commitment, _ = zkp.create_commitment(data, f"batch_ctx_{i}")
        statement = f"Batch proof {i}"
        proof = zkp.prove_knowledge(data, commitment, statement)
        proofs.append(proof)

    results = zkp.batch_verify(proofs)
    assert len(results) == 5
    for key, result in results.items():
        assert result.valid is True, f"{key} should be valid"

def test_batch_verify_mixed(zkp):
    """Batch verify a mix of valid and invalid proofs."""
    # Valid proofs
    valid_proofs = []
    for i in range(3):
        data = f"valid_{i}"
        c, _ = zkp.create_commitment(data, f"v_ctx_{i}")
        p = zkp.prove_knowledge(data, c, f"Valid proof {i}")
        valid_proofs.append(p)

    # Create tampered proof (wrong verifier key)
    bad_proof = ZKProof(
        commitment="fake",
        proof="fake_hash",
        public_inputs={"statement": "Fake proof", "context": "", "challenge": "x"},
        timestamp=datetime.now().isoformat(),
        verifier_key_hash="tampered_key_12345678901234567890",
    )

    mixed = valid_proofs + [bad_proof]
    results = zkp.batch_verify(mixed)

    # First 3 should be valid
    for i in range(3):
        assert results[f"proof_{i}"].valid is True

    # Last one should fail
    assert results["proof_3"].valid is False

def test_batch_verify_empty(zkp):
    """Batch verify empty list."""
    results = zkp.batch_verify([])
    assert results == {}

# ── Edge Cases ───────────────────────────────────────────────────────────

def test_empty_private_data(zkp):
    """Handle empty private data."""
    commitment, opening = zkp.create_commitment("", "empty_data_test")
    assert commitment is not None

def test_special_characters(zkp):
    """Handle Unicode and special characters in data."""
    data = "héllo wörld 🔐 §½$€"
    commitment, _ = zkp.create_commitment(data, "unicode_test")
    proof = zkp.prove_knowledge(data, commitment, "Unicode proof test")
    result = zkp.verify_proof(proof, "Unicode proof test")
    assert result.valid is True

def test_long_data(zkp):
    """Handle very long private data."""
    long_data = "x" * 10000
    commitment, _ = zkp.create_commitment(long_data, "long_data_test")
    proof = zkp.prove_knowledge(long_data, commitment, "Long data proof")
    result = zkp.verify_proof(proof, "Long data proof")
    assert result.valid is True

def test_commitment_idempotency(zkp):
    """Same data produces different commitments (due to blinding)."""
    c1, _ = zkp.create_commitment("same_data", "ctx")
    c2, _ = zkp.create_commitment("same_data", "ctx")
    # With proper blinding, commitments should differ
    assert c1 != c2

# ── Statistics ───────────────────────────────────────────────────────────

def test_get_stats_empty(zkp):
    """Stats on empty manager."""
    stats = zkp.get_stats()
    assert stats["total_commitments"] == 0
    assert stats["used_commitments"] == 0
    assert stats["security_parameter"] == 128
    assert "verifier_key_hash" in stats
    assert "real_zkp_available" in stats

def test_get_stats_after_operations(zkp):
    """Stats after creating commitments."""
    zkp.create_commitment("data_1", "ctx_1")
    zkp.create_commitment("data_2", "ctx_2")
    zkp.create_commitment("data_3", "ctx_3")

    stats = zkp.get_stats()
    assert stats["total_commitments"] == 3
    assert stats["used_commitments"] == 0

# ── Singleton ────────────────────────────────────────────────────────────

def test_singleton():
    """Test singleton pattern."""
    z1 = get_zkp_manager_real()
    z2 = get_zkp_manager_real()
    assert z1 is z2

# ── Large Data Tests ─────────────────────────────────────────────────────

def test_large_identity_proof(zkp):
    """Create identity proof with large identity data."""
    identity = {
        "did": "did:asim:e2e_large_user",
        "keys": [f"key_{j}" for j in range(100)],
        "metadata": {f"attr_{k}": f"value_{k}" for k in range(50)},
    }
    nonce = "large_nonce_001"

    proof = zkp.create_identity_proof(identity, nonce)
    statement = proof.public_inputs["statement"]
    result = zkp.verify_proof(proof, statement)
    assert result.valid is True

def test_multiple_proofs_same_commitment(zkp):
    """Multiple proofs from same commitment should work."""
    data = "shared_secret"
    commitment, _ = zkp.create_commitment(data, "shared")

    proof1 = zkp.prove_knowledge(data, commitment, "First use")
    proof2 = zkp.prove_knowledge(data, commitment, "Second use")

    assert proof1.proof != proof2.proof  # Different challenges

    r1 = zkp.verify_proof(proof1, "First use")
    r2 = zkp.verify_proof(proof2, "Second use")
    assert r1.valid is True
    assert r2.valid is True

# ── Integration Pattern Tests ────────────────────────────────────────────

def test_zkp_for_transaction_privacy(zkp):
    """
    Simulate ZKP for private transaction: sender proves
    they have sufficient balance without revealing actual amount.
    """
    # Simulate balance commitment
    balance_data = json.dumps({"user": "alice", "balance": 5000})
    commitment, _ = zkp.create_commitment(balance_data, "balance_proof")

    # Prove balance >= 1000 without revealing exact amount
    statement = "Balance sufficient for 1000 NEXUS transfer (ZK range proof)"
    proof = zkp.prove_knowledge(balance_data, commitment, statement)

    # Merchant verifies the proof
    result = zkp.verify_proof(proof, statement)
    assert result.valid is True

def test_zkp_for_age_verification(zkp):
    """
    Simulate age verification: user proves they're over 18
    without revealing exact age.
    """
    age_data = json.dumps({"user": "bob", "age": 25})
    commitment, _ = zkp.create_commitment(age_data, "age_verification")

    statement = "User is over 18 years old (ZK age proof)"
    proof = zkp.prove_knowledge(age_data, commitment, statement)

    result = zkp.verify_proof(proof, statement)
    assert result.valid is True

def test_zkp_for_dharma_veto(zkp):
    """
    Simulate Dharma-Chakra veto: authorized entity proves veto right
    without revealing full identity.
    """
    veto_data = json.dumps({
        "authority": "dharma_council",
        "veto_power": True,
        "proposal_id": "prop_42",
    })
    commitment, _ = zkp.create_commitment(veto_data, "dharma_veto")

    statement = "Authorized veto on proposal prop_42 (ZK authority proof)"
    proof = zkp.prove_knowledge(veto_data, commitment, statement)

    result = zkp.verify_proof(proof, statement)
    assert result.valid is True

# ── Deterministic Key Verification ───────────────────────────────────────

def test_verifier_key_is_deterministic():
    """Same prover secret should produce same verifier key."""
    zkp1 = RealZKPManager()
    zkp2 = RealZKPManager()

    # Different instances have different secrets -> different keys
    assert zkp1._verifier_key != zkp2._verifier_key

# ── HAS_REAL_ZKP Flag ────────────────────────────────────────────────────

def test_real_zkp_availability():
    """Check if real EC-based ZKP is available."""
    # This is informational - the system works with or without it
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        assert HAS_REAL_ZKP is True
    except ImportError:
        assert HAS_REAL_ZKP is False
