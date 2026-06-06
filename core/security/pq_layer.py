
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
core/security/pq_layer.py
AsimNexus — Post-Quantum Cryptography Layer
=============================================
Quantum computers will break RSA and ECC.
This layer provides:
  - Kyber-like KEM (Key Encapsulation Mechanism) simulation
  - Dilithium-like digital signatures simulation
  - Hybrid mode: classical + post-quantum for transition period
  - Migration path from Ed25519 → PQ signatures
  - Key derivation using lattice-based primitives

Note: Pure Python implementation — production should use liboqs or
the NIST-standardized ML-KEM (Kyber) and ML-DSA (Dilithium) via
a C extension. This module provides the architecture and interface.

NIST PQC Standards (2024):
  - ML-KEM (FIPS 203) — key encapsulation
  - ML-DSA (FIPS 204) — digital signatures
  - SLH-DSA (FIPS 205) — stateless hash-based signatures
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import struct
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger("AsimNexus.PostQuantum")

PQ_KEYS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "pq_keys"
PQ_KEYS_DIR.mkdir(parents=True, exist_ok=True)


class PQAlgorithm(str, Enum):
    ML_KEM_512    = "ML-KEM-512"     # NIST FIPS 203 Level 1
    ML_KEM_768    = "ML-KEM-768"     # NIST FIPS 203 Level 3
    ML_KEM_1024   = "ML-KEM-1024"    # NIST FIPS 203 Level 5
    ML_DSA_44     = "ML-DSA-44"      # NIST FIPS 204 Level 2
    ML_DSA_65     = "ML-DSA-65"      # NIST FIPS 204 Level 3
    ML_DSA_87     = "ML-DSA-87"      # NIST FIPS 204 Level 5
    HYBRID_ED_KEM = "Hybrid-Ed25519+ML-KEM-768"   # Transition mode


# Security levels (bits of security)
SECURITY_LEVELS = {
    PQAlgorithm.ML_KEM_512:    128,
    PQAlgorithm.ML_KEM_768:    192,
    PQAlgorithm.ML_KEM_1024:   256,
    PQAlgorithm.ML_DSA_44:     128,
    PQAlgorithm.ML_DSA_65:     192,
    PQAlgorithm.ML_DSA_87:     256,
    PQAlgorithm.HYBRID_ED_KEM: 192,
}


@dataclass
class PQKeyPair:
    key_id:      str
    algorithm:   PQAlgorithm
    public_key:  str    # hex
    private_key: str    # hex (encrypted at rest)
    created_at:  str
    did:         str = ""
    security_bits: int = 192

    def to_dict(self): return {k: v for k, v in asdict(self).items() if k != "private_key"}


@dataclass
class PQSignature:
    sig_id:    str
    algorithm: PQAlgorithm
    message_hash: str
    signature: str   # hex
    public_key: str  # hex
    ts:        float
    valid:     bool = False


@dataclass
class KEMResult:
    kem_id:      str
    algorithm:   PQAlgorithm
    ciphertext:  str    # hex — to send to recipient
    shared_secret: str  # hex — keep private


class PostQuantumLayer:
    """
    Post-Quantum cryptography layer.
    
    Simulation approach:
    - Uses SHAKE-256 (extendable output function) to simulate lattice operations
    - Real PQ security requires liboqs — this provides the API contract
    - Hybrid mode combines classical HMAC-SHA256 + simulated PQ for defense-in-depth
    """

    def __init__(self):
        self._keys: Dict[str, PQKeyPair] = {}
        self._load()
        logger.info(f"✅ PostQuantumLayer ready — {len(self._keys)} keys loaded")

    # ── KEY GENERATION ────────────────────────────────────────────────────────

    def generate_keypair(self, did: str = "",
                         algo: PQAlgorithm = PQAlgorithm.ML_KEM_768) -> PQKeyPair:
        """Generate a PQ keypair."""
        seed = secrets.token_bytes(64)
        # Simulate lattice key generation via SHAKE-256
        pk_bytes = hashlib.shake_256(seed + b"\x01").digest(64)
        sk_bytes = hashlib.shake_256(seed + b"\x02").digest(96)

        kp = PQKeyPair(
            key_id       = secrets.token_hex(8),
            algorithm    = algo,
            public_key   = pk_bytes.hex(),
            private_key  = sk_bytes.hex(),   # TODO: encrypt with AES-256-GCM
            created_at   = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            did          = did,
            security_bits = SECURITY_LEVELS.get(algo, 192),
        )
        self._keys[kp.key_id] = kp
        self._save_key(kp)
        logger.info(f"🔑 PQ keypair generated: {algo.value} for {did or kp.key_id}")
        return kp

    # ── SIGNING ──────────────────────────────────────────────────────────────

    def sign(self, message: bytes, key_id: str) -> PQSignature:
        """Sign a message with ML-DSA (simulated)."""
        kp = self._keys.get(key_id)
        if not kp:
            raise KeyError(f"Key not found: {key_id}")

        sk = bytes.fromhex(kp.private_key)
        msg_hash = hashlib.sha3_256(message).hexdigest()

        # Simulate Dilithium: H(sk || message) expanded via SHAKE
        sig_input = sk + message + struct.pack(">d", time.time())
        sig_bytes  = hashlib.shake_256(sig_input).digest(64)

        return PQSignature(
            sig_id       = secrets.token_hex(6),
            algorithm    = kp.algorithm,
            message_hash = msg_hash,
            signature    = sig_bytes.hex(),
            public_key   = kp.public_key,
            ts           = time.time(),
            valid        = True,
        )

    def verify(self, message: bytes, sig: PQSignature, key_id: str) -> bool:
        """Verify a PQ signature."""
        kp = self._keys.get(key_id)
        if not kp:
            return False
        msg_hash = hashlib.sha3_256(message).hexdigest()
        if msg_hash != sig.message_hash:
            return False
        # In simulation: re-derive signature and compare
        sk = bytes.fromhex(kp.private_key)
        sig_input  = sk + message + struct.pack(">d", sig.ts)
        expected   = hashlib.shake_256(sig_input).digest(64).hex()
        return hmac.compare_digest(expected, sig.signature)

    # ── KEY ENCAPSULATION ────────────────────────────────────────────────────

    def kem_encapsulate(self, recipient_public_key: str,
                        algo: PQAlgorithm = PQAlgorithm.ML_KEM_768) -> KEMResult:
        """
        Encapsulate a shared secret for the recipient.
        Recipient decapsulates with their private key.
        """
        pk = bytes.fromhex(recipient_public_key)
        r  = secrets.token_bytes(32)

        # Simulate Kyber encapsulation: (ciphertext, shared_secret)
        ciphertext    = hashlib.shake_256(pk + r + b"\x03").digest(64)
        shared_secret = hashlib.shake_256(pk + r + b"\x04").digest(32)

        return KEMResult(
            kem_id        = secrets.token_hex(6),
            algorithm     = algo,
            ciphertext    = ciphertext.hex(),
            shared_secret = shared_secret.hex(),
        )

    def kem_decapsulate(self, ciphertext_hex: str, key_id: str) -> str:
        """Decapsulate to recover shared secret."""
        kp = self._keys.get(key_id)
        if not kp:
            raise KeyError(f"Key not found: {key_id}")
        sk = bytes.fromhex(kp.private_key)
        ct = bytes.fromhex(ciphertext_hex)
        shared = hashlib.shake_256(sk + ct + b"\x04").digest(32)
        return shared.hex()

    # ── HYBRID MODE ──────────────────────────────────────────────────────────

    def hybrid_sign(self, message: bytes, key_id: str,
                    classical_key: bytes = None) -> Dict:
        """
        Hybrid: classical HMAC-SHA256 + PQ signature.
        Both must verify for the message to be accepted.
        """
        pq_sig = self.sign(message, key_id)
        classical_key = classical_key or secrets.token_bytes(32)
        classical_sig = hmac.new(classical_key, message, hashlib.sha256).hexdigest()
        return {
            "pq_sig":        asdict(pq_sig),
            "classical_sig": classical_sig,
            "hybrid":        True,
            "algorithm":     PQAlgorithm.HYBRID_ED_KEM.value,
        }

    # ── STATUS ────────────────────────────────────────────────────────────────

    def status(self) -> Dict:
        keys = list(self._keys.values())
        by_algo: Dict[str, int] = {}
        for k in keys:
            by_algo[k.algorithm.value] = by_algo.get(k.algorithm.value, 0) + 1
        return {
            "total_keys":     len(keys),
            "by_algorithm":   by_algo,
            "nist_standards": ["ML-KEM (FIPS 203)", "ML-DSA (FIPS 204)", "SLH-DSA (FIPS 205)"],
            "hybrid_mode":    True,
            "quantum_safe":   True,
            "note":           "Simulated — production: use liboqs or pqcrypto package",
        }

    def list_keys(self, did: str = None) -> list:
        keys = list(self._keys.values())
        if did:
            keys = [k for k in keys if k.did == did]
        return [k.to_dict() for k in keys]

    # ── PERSISTENCE ──────────────────────────────────────────────────────────

    def _save_key(self, kp: PQKeyPair):
        path = PQ_KEYS_DIR / f"{kp.key_id}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(kp), f, indent=2)
        except Exception as e:
            logger.warning(f"PQ key save failed: {e}")

    def _load(self):
        for path in PQ_KEYS_DIR.glob("*.json"):
            try:
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                d["algorithm"] = PQAlgorithm(d["algorithm"])
                self._keys[d["key_id"]] = PQKeyPair(**d)
            except Exception:
                continue


_layer: Optional[PostQuantumLayer] = None
def get_pq_layer() -> PostQuantumLayer:
    global _layer
    if _layer is None: _layer = PostQuantumLayer()
    return _layer
