"""
Real ZKP Manager — production-grade zero-knowledge proof system.
=================================================================
Provides Pedersen commitments, Schnorr proofs, identity proofs,
and batch verification for the ASIMNEXUS e2e critical flows.

Exports:
    RealZKPManager  — main class with create_commitment / prove_knowledge / verify_proof / etc.
    ZKProof         — dataclass representing a proof
    VerificationResult — dataclass for verification results
    get_zkp_manager_real()  — singleton factory
    HAS_REAL_ZKP    — feature flag (always True)
"""

import hashlib
import secrets
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List


# ── Feature flag ─────────────────────────────────────────────────────────────

HAS_REAL_ZKP: bool = True  # Real ZKP is always available in this implementation


# ── secp256k1 prime field ───────────────────────────────────────────────────
_P: int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_G: int = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_H: int = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


# ── Proof dataclass ─────────────────────────────────────────────────────────

@dataclass
class ZKProof:
    """A zero-knowledge proof produced by RealZKPManager."""
    commitment: str
    challenge: int = 0
    s1: int = 0
    s2: int = 0
    statement: str = ""
    proof_type: str = "generic"
    public_inputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    proof: str = ""
    timestamp: str = ""
    verifier_key_hash: str = ""


@dataclass
class VerificationResult:
    """Result of a proof verification."""
    valid: bool
    confidence: float = 1.0
    details: Optional[Dict[str, Any]] = None


# ── Helpers ─────────────────────────────────────────────────────────────────

def _hash_to_int(data: bytes) -> int:
    return int(hashlib.sha256(data).hexdigest(), 16) % _P


def _pedersen_commit(value: int, blinding: int) -> int:
    """C = G^v * H^r mod P"""
    return (pow(_G, value, _P) * pow(_H, blinding, _P)) % _P


def _schnorr_prove(value: int, opening: int, statement: str) -> Dict[str, Any]:
    """Create a Schnorr proof of knowledge for a Pedersen commitment."""
    k1 = int(secrets.token_hex(32), 16) % _P
    k2 = int(secrets.token_hex(32), 16) % _P
    R = (pow(_G, k1, _P) * pow(_H, k2, _P)) % _P

    challenge_input = f"{R}:{statement}".encode()
    e = _hash_to_int(challenge_input)

    s1 = (k1 + e * value) % (_P - 1)
    s2 = (k2 + e * opening) % (_P - 1)

    return {
        "commitment": _pedersen_commit(value, opening),
        "challenge": e,
        "s1": s1,
        "s2": s2,
        "statement": statement,
    }


def _schnorr_verify(proof: Dict[str, Any], statement: str) -> bool:
    """Verify a Schnorr proof of knowledge."""
    try:
        C = proof["commitment"]
        s1 = proof["s1"]
        s2 = proof["s2"]
        e = proof["challenge"]

        # Recover R' = G^s1 * H^s2 * C^{-e}
        C_neg_e = pow(C, e * (_P - 2), _P)
        R_prime = (pow(_G, s1, _P) * pow(_H, s2, _P) * C_neg_e) % _P

        # Recompute challenge
        e_prime = _hash_to_int(f"{R_prime}:{statement}".encode())

        return e_prime == e
    except (KeyError, TypeError, ValueError):
        return False


# ── Singleton ───────────────────────────────────────────────────────────────

_zkp_manager_instance: Optional["RealZKPManager"] = None


def get_zkp_manager_real() -> "RealZKPManager":
    """Return the singleton RealZKPManager instance."""
    global _zkp_manager_instance
    if _zkp_manager_instance is None:
        _zkp_manager_instance = RealZKPManager()
    return _zkp_manager_instance


# ── Main class ──────────────────────────────────────────────────────────────

class RealZKPManager:
    """Production-grade ZKP manager with commitment, proof, and verification."""

    def __init__(self, security_parameter: int = 128):
        self.security_param: int = security_parameter
        self._commitments: Dict[str, Dict[str, Any]] = {}  # commitment_hex -> {value, blinding, context}
        self._commitment_counter: int = 0
        self._proof_counter: int = 0
        self._prover_secret: str = secrets.token_hex(16)
        self._verifier_key: str = hashlib.sha256(
            f"asim_zkp_v1_{secrets.token_hex(8)}".encode()
        ).hexdigest()[:32]
        self._verifier_key_hash: str = self._verifier_key[:16]

    # ── Commitment ──────────────────────────────────────────────────────

    def create_commitment(self, private_data: str, context: str = "") -> Tuple[str, str]:
        """Create a Pedersen commitment to private data.

        Args:
            private_data: The secret string to commit to
            context: Optional context string

        Returns:
            (commitment_hex, opening_hex) as hex strings
        """
        value = _hash_to_int(private_data.encode())
        blinding = int(secrets.token_hex(32), 16) % _P
        commitment = _pedersen_commit(value, blinding)
        commitment_hex = hex(commitment)

        self._commitments[commitment_hex] = {
            "value": value,
            "blinding": blinding,
            "context": context,
        }

        return commitment_hex, hex(blinding)

    # ── Prove knowledge ─────────────────────────────────────────────────

    def prove_knowledge(self, private_data: str, commitment: str, statement: str) -> ZKProof:
        """Prove knowledge of the data behind a commitment.

        Args:
            private_data: The original secret string
            commitment: The commitment hex string returned by create_commitment
            statement: Challenge statement

        Returns:
            ZKProof instance

        Raises:
            ValueError: If the commitment is unknown
        """
        if commitment not in self._commitments:
            raise ValueError(f"Unknown commitment: {commitment}")

        entry = self._commitments[commitment]
        value = entry["value"]
        opening = entry["blinding"]

        proof_dict = _schnorr_prove(value, opening, statement)
        self._proof_counter += 1

        proof_hex = hashlib.sha256(
            f"{proof_dict['commitment']}:{proof_dict['challenge']}:{statement}".encode()
        ).hexdigest()

        return ZKProof(
            commitment=commitment,
            challenge=proof_dict["challenge"],
            s1=proof_dict["s1"],
            s2=proof_dict["s2"],
            statement=proof_dict["statement"],
            proof_type="knowledge",
            proof=proof_hex,
            timestamp=datetime.now().isoformat(),
            verifier_key_hash=self._verifier_key,
            public_inputs={
                "commitment": commitment,
                "statement": statement,
                "context": entry.get("context", ""),
            },
            metadata={"proof_index": self._proof_counter},
        )

    # ── Verify proof ────────────────────────────────────────────────────

    def verify_proof(self, proof: ZKProof, statement: str) -> VerificationResult:
        """Verify a ZK proof.

        Args:
            proof: ZKProof instance
            statement: The statement to verify against

        Returns:
            VerificationResult with .valid (bool), .confidence (float), and .details (dict)
        """
        details: Dict[str, Any] = {}

        # Check verifier key match
        if proof.verifier_key_hash and proof.verifier_key_hash != self._verifier_key:
            details["error"] = "key mismatch"
            return VerificationResult(valid=False, confidence=0.0, details=details)

        # Check expiry (60 minutes)
        if proof.timestamp:
            try:
                proof_time = datetime.fromisoformat(proof.timestamp)
                if datetime.now() - proof_time > timedelta(minutes=60):
                    details["error"] = "expired"
                    return VerificationResult(valid=False, confidence=0.0, details=details)
            except (ValueError, TypeError):
                pass

        # Check statement mismatch
        if proof.statement and proof.statement != statement:
            details["error"] = "statement mismatch"
            return VerificationResult(valid=False, confidence=0.0, details=details)

        # Parse commitment back to int
        try:
            cmt_int = int(proof.commitment, 16) if isinstance(proof.commitment, str) else int(proof.commitment)
        except (ValueError, TypeError):
            cmt_int = 0

        proof_dict = {
            "commitment": cmt_int,
            "challenge": proof.challenge,
            "s1": proof.s1,
            "s2": proof.s2,
            "statement": proof.statement or statement,
        }

        is_valid = _schnorr_verify(proof_dict, statement)
        details["commitment"] = proof.commitment
        details["verifier_match"] = True

        return VerificationResult(
            valid=is_valid,
            confidence=0.95 if is_valid else 0.0,
            details=details,
        )

    # ── Identity proof ──────────────────────────────────────────────────

    def create_identity_proof(self, identity: Dict[str, Any], nonce: str) -> ZKProof:
        """Create a ZK proof of identity.

        Args:
            identity: Dict with 'did', 'public_key', 'roles' etc.
            nonce: Unique nonce to prevent replay

        Returns:
            ZKProof with public_inputs["statement"] containing the identity claim
        """
        did = identity.get("did", "unknown")
        public_key = identity.get("public_key", "")
        roles = identity.get("roles", [])

        # Create a statement that binds the identity to the nonce
        statement = f"Valid identity for {did} with nonce {nonce}"
        identity_data = json.dumps({"did": did, "public_key": public_key, "roles": roles}, sort_keys=True)

        value = _hash_to_int(identity_data.encode())
        blinding = int(secrets.token_hex(32), 16) % _P
        commitment = _pedersen_commit(value, blinding)
        commitment_hex = hex(commitment)

        self._commitments[commitment_hex] = {
            "value": value,
            "blinding": blinding,
            "context": f"identity:{did}",
        }

        proof_dict = _schnorr_prove(value, blinding, statement)
        self._proof_counter += 1

        proof_hex = hashlib.sha256(
            f"{proof_dict['commitment']}:{proof_dict['challenge']}:{statement}".encode()
        ).hexdigest()

        return ZKProof(
            commitment=commitment_hex,
            challenge=proof_dict["challenge"],
            s1=proof_dict["s1"],
            s2=proof_dict["s2"],
            statement=proof_dict["statement"],
            proof_type="identity",
            proof=proof_hex,
            timestamp=datetime.now().isoformat(),
            verifier_key_hash=self._verifier_key,
            public_inputs={
                "statement": statement,
                "did": did,
                "nonce": nonce,
            },
            metadata={"proof_index": self._proof_counter},
        )

    # ── Action Approval ─────────────────────────────────────────────────

    def create_action_approval(self, action: str, user_id: str, context: Dict[str, Any]) -> ZKProof:
        """Create a ZK proof for action approval (Dharma-Chakra integration).

        Args:
            action: The action being approved (e.g. "transfer_funds")
            user_id: The user requesting approval
            context: Additional context dict

        Returns:
            ZKProof with statement containing action and user info
        """
        statement = f"Action approval: {action} by {user_id}"
        action_data = json.dumps({"action": action, "user_id": user_id, **context}, sort_keys=True)

        value = _hash_to_int(action_data.encode())
        blinding = int(secrets.token_hex(32), 16) % _P
        commitment = _pedersen_commit(value, blinding)
        commitment_hex = hex(commitment)

        self._commitments[commitment_hex] = {
            "value": value,
            "blinding": blinding,
            "context": f"action_approval:{action}",
        }

        proof_dict = _schnorr_prove(value, blinding, statement)
        self._proof_counter += 1

        proof_hex = hashlib.sha256(
            f"{proof_dict['commitment']}:{proof_dict['challenge']}:{statement}".encode()
        ).hexdigest()

        return ZKProof(
            commitment=commitment_hex,
            challenge=proof_dict["challenge"],
            s1=proof_dict["s1"],
            s2=proof_dict["s2"],
            statement=proof_dict["statement"],
            proof_type="action_approval",
            proof=proof_hex,
            timestamp=datetime.now().isoformat(),
            verifier_key_hash=self._verifier_key,
            public_inputs={
                "statement": statement,
                "action": action,
                "user_id": user_id,
            },
            metadata={"proof_index": self._proof_counter},
        )

    # ── Batch verify ────────────────────────────────────────────────────

    def batch_verify(self, proofs: List[ZKProof]) -> Dict[str, VerificationResult]:
        """Verify multiple proofs at once.

        Args:
            proofs: List of ZKProof instances

        Returns:
            Dict mapping proof index/ID to VerificationResult
        """
        results: Dict[str, VerificationResult] = {}
        for i, proof in enumerate(proofs):
            stmt = proof.statement or proof.public_inputs.get("statement", "")
            results[f"proof_{i}"] = self.verify_proof(proof, stmt)
        return results

    # ── Stats ───────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get ZKP system statistics."""
        used = sum(1 for v in self._commitments.values() if v.get("context", "").startswith("identity:") or v.get("context", "").startswith("action_approval:"))
        return {
            "total_commitments": len(self._commitments),
            "total_proofs": self._proof_counter,
            "used_commitments": used,
            "security_parameter": self.security_param,
            "verifier_key_hash": self._verifier_key_hash,
            "real_zkp_available": HAS_REAL_ZKP,
        }
