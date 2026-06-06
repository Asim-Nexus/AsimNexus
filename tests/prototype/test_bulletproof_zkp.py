"""
STATUS: PARTIAL→REAL test — BulletProofZKP v2
Tests Pedersen commitments, Schnorr proofs, verification.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.security.bulletproof_zkp import commit, prove_knowledge, verify, BulletProofZKP


class TestPedersenCommitment:
    def test_commit_is_hiding(self):
        c1, r1 = commit(42)
        c2, r2 = commit(42)
        assert c1 != c2  # different blinding => different commitment

    def test_commit_verifies(self):
        v, r = 100, 12345
        c, _ = commit(v, r)
        assert c == (pow(2, v, 170141183460469231731687303715884105727) *
                     pow(pow(2, int(__import__('hashlib').sha256(b"asimnexus_trapdoor").hexdigest(), 16) %
                              ((170141183460469231731687303715884105727 - 1) // 2),
                         170141183460469231731687303715884105727), r,
                         170141183460469231731687303715884105727)) % 170141183460469231731687303715884105727


class TestSchnorrProof:
    def test_honest_proof_verifies(self):
        v, r = 42, 12345
        c, _ = commit(v, r)
        proof = prove_knowledge(v, r, "test")
        assert verify(proof, "test") is True

    def test_wrong_statement_fails(self):
        v, r = 42, 12345
        proof = prove_knowledge(v, r, "correct")
        assert verify(proof, "wrong") is False

    def test_wrong_value_fails(self):
        v, r = 42, 12345
        proof = prove_knowledge(v, r, "test")
        proof["s1"] = (proof["s1"] + 1)  # tamper
        assert verify(proof, "test") is False


class TestBulletProofZKP:
    def test_create_and_verify(self):
        zkp = BulletProofZKP()
        result = zkp.create("my_secret", "context_abc")
        assert zkp.verify_proof(result) is True

    def test_different_secrets_different_commitments(self):
        zkp = BulletProofZKP()
        r1 = zkp.create("secret1")
        r2 = zkp.create("secret2")
        assert r1["commitment"] != r2["commitment"]
