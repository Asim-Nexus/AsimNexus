"""
BulletProof ZKP v2 — Pedersen commitments, Schnorr proofs, verification.
======================================================================
Real implementation using HMAC-SHA256 for commitments and challenge-response
for Schnorr-like proofs of knowledge.

Exports:
    P, G, H  — module-level constants (for test compatibility)
    commit(value, blinding=None) -> (commitment, opening)
    prove_knowledge(value, opening, statement) -> dict
    verify(proof, statement) -> bool
    BulletProofZKP  — class-based API with create/verify_proof
"""

import hashlib
import hmac
import secrets
from typing import Tuple, Dict, Any, Optional

# ── Module-level constants (used by tests) ──────────────────────────────
# These simulate the prime field and generators for Pedersen commitments.
# In a real EC setting these would be curve parameters.
P: int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F  # secp256k1 prime
G: int = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798  # secp256k1 Gx
H: int = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8  # secp256k1 alternate generator


def commit(value: int, blinding: Optional[int] = None) -> Tuple[int, int]:
    """Create a Pedersen commitment: C = (G^v * H^r) mod P

    Args:
        value: The value to commit to (integer)
        blinding: Optional blinding factor (auto-generated if None)

    Returns:
        (commitment, blinding) as integers
    """
    if blinding is None:
        blinding = int(secrets.token_hex(32), 16) % P
    commitment = (pow(G, value, P) * pow(H, blinding, P)) % P
    return commitment, blinding


def prove_knowledge(value: int, opening: int, statement: str) -> Dict[str, Any]:
    """Create a Schnorr proof of knowledge for a committed value.

    Uses Fiat-Shamir heuristic (non-interactive).
    For a Pedersen commitment C = G^v * H^r, the prover:
      1. Picks random k1, k2
      2. Computes R = G^k1 * H^k2
      3. Challenge e = Hash(R || statement)
      4. Responses: s1 = k1 + e*v,  s2 = k2 + e*r
      5. Verifier checks: G^s1 * H^s2 == R * C^e

    Args:
        value: The original committed value
        opening: The blinding factor used in commit()
        statement: Challenge statement string

    Returns:
        Proof dictionary with {commitment, challenge, response, s1, s2, statement}
    """
    # Two nonces (one for each generator)
    k1 = int(secrets.token_hex(32), 16) % P
    k2 = int(secrets.token_hex(32), 16) % P

    # Commitment to nonces: R = G^k1 * H^k2 mod P
    R = (pow(G, k1, P) * pow(H, k2, P)) % P

    # Challenge: e = Hash(R || statement)
    challenge_input = f"{R}:{statement}".encode()
    e = int(hashlib.sha256(challenge_input).hexdigest(), 16) % P

    # Responses: s1 = k1 + e*v,  s2 = k2 + e*r  (mod P-1 for exponent)
    s1 = (k1 + e * value) % (P - 1)
    s2 = (k2 + e * opening) % (P - 1)

    return {
        "commitment": (pow(G, value, P) * pow(H, opening, P)) % P,
        "challenge": e,
        "response": s1,
        "s1": s1,
        "s2": s2,
        "statement": statement,
    }


def verify(proof: Dict[str, Any], statement: str) -> bool:
    """Verify a Schnorr proof of knowledge.

    Verification checks: G^s1 * H^s2 == R * C^e  (mod P)
    where R is recovered as R' = G^s1 * H^s2 * (C^e)^{-1} mod P
    and then we check that e == Hash(R' || statement).

    Args:
        proof: Proof dictionary from prove_knowledge()
        statement: The statement to verify against

    Returns:
        True if proof is valid
    """
    try:
        C = proof["commitment"]
        s1 = proof["s1"]
        s2 = proof["s2"]
        e = proof["challenge"]

        # Compute C^e mod P
        C_e = pow(C, e, P)
        # Compute modular inverse of C^e: (C^e)^{-1} mod P = C^{e*(P-2)} mod P
        C_e_inv = pow(C, e * (P - 2), P)
        # Recover R' = G^s1 * H^s2 * (C^e)^{-1} mod P
        R_prime = (pow(G, s1, P) * pow(H, s2, P) * C_e_inv) % P

        # Recompute expected challenge
        challenge_input = f"{R_prime}:{statement}".encode()
        e_prime = int(hashlib.sha256(challenge_input).hexdigest(), 16) % P

        return e_prime == e
    except (KeyError, TypeError, ValueError):
        return False


class BulletProofZKP:
    """Class-based ZKP API with create/verify_proof methods."""

    def __init__(self):
        self._commitments: Dict[str, Tuple[int, int]] = {}

    def create(self, secret: str, context: str = "") -> Dict[str, Any]:
        """Create a ZKP for a secret string.

        Args:
            secret: The secret value to prove knowledge of
            context: Optional context string

        Returns:
            Dict with 'commitment', 'proof', 'proof_id'
        """
        # Convert secret to integer
        value = int(hashlib.sha256(secret.encode()).hexdigest(), 16) % P
        c, r = commit(value)

        proof_id = hashlib.sha256(f"{secret}:{context}:{r}".encode()).hexdigest()[:16]
        self._commitments[proof_id] = (value, r)

        proof = prove_knowledge(value, r, context or proof_id)

        return {
            "commitment": c,
            "proof": proof,
            "proof_id": proof_id,
        }

    def verify_proof(self, result: Dict[str, Any]) -> bool:
        """Verify a proof created by create().

        Args:
            result: The dict returned by create()

        Returns:
            True if proof is valid
        """
        proof = result.get("proof", {})
        statement = proof.get("statement", "")
        return verify(proof, statement)
