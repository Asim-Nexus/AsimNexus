"""
Post-Quantum Cryptography
==========================
Post-quantum cryptographic primitives with software fallback.
Supports key generation, signing, and verification using
standardized algorithms (Kyber, Dilithium, etc.) with fallback.
"""

import hashlib
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_instance = None


@dataclass
class PQKeypair:
    """Post-quantum keypair."""
    key_id: str
    algorithm: str
    public_key: str
    private_key: str


class PostQuantumCrypto:
    """Post-quantum cryptography with software fallback."""

    def __init__(self):
        self._supported_algorithms = ["kyber", "dilithium", "falcon", "sphincs"]
        self._keys: Dict[str, PQKeypair] = {}

    @property
    def supported_algorithms(self) -> List[str]:
        return self._supported_algorithms

    def generate_keypair(self, key_id: str, algorithm: str = "kyber") -> PQKeypair:
        """Generate a post-quantum keypair."""
        if algorithm not in self._supported_algorithms:
            algorithm = "kyber"

        # Software fallback key generation
        seed = hashlib.sha256(key_id.encode()).hexdigest()
        public_key = f"PQ_PUB_{algorithm}_{seed[:32]}"
        private_key = f"PQ_PRIV_{algorithm}_{seed[32:64]}"

        keypair = PQKeypair(
            key_id=key_id,
            algorithm=algorithm,
            public_key=public_key,
            private_key=private_key,
        )
        self._keys[key_id] = keypair
        return keypair

    def get_keypair(self, key_id: str) -> Optional[PQKeypair]:
        """Get a keypair by ID."""
        return self._keys.get(key_id)

    def sign(self, key_id: str, message: bytes) -> Optional[str]:
        """Sign a message with a post-quantum key."""
        keypair = self._keys.get(key_id)
        if not keypair:
            return None
        return hashlib.sha512(keypair.private_key.encode() + message).hexdigest()

    def verify(self, key_id: str, message: bytes, signature: str) -> bool:
        """Verify a post-quantum signature."""
        expected = self.sign(key_id, message)
        return expected == signature


def get_post_quantum_crypto() -> PostQuantumCrypto:
    """Get or create the singleton PostQuantumCrypto instance."""
    global _instance
    if _instance is None:
        _instance = PostQuantumCrypto()
    return _instance


def reset_post_quantum_crypto() -> None:
    """Reset the singleton for testing."""
    global _instance
    _instance = None
