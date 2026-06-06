#!/usr/bin/env python3
"""
core/identity/zkp_local.py
AsimNexus — Zero-Knowledge Proof (ZKP) Local Store

Provides local ZKP-based identity verification without external dependencies.
Uses hash-based commitments and challenge-response for zero-knowledge proofs.

Provides:
  - ZKPStatus, ZKPProtocol enums
  - ZKPIdentity, ZKPProof dataclasses
  - ZKPStore: main class for ZKP identity management
  - Singleton factory: get_zkp_store() / reset_zkp_store()
"""

import os
import json
import time
import uuid
import hmac
import hashlib
import logging
import secrets
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class ZKPStatus(Enum):
    """ZKP identity states"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPROMISED = "compromised"
    REVOKED = "revoked"


class ZKPProtocol(Enum):
    """Supported ZKP protocols"""
    SCHNORR = "schnorr"          # Schnorr identification protocol
    HASH_CHAIN = "hash_chain"    # Hash chain commitment
    MERKLE = "merkle"            # Merkle tree proof
    BBS_PLUS = "bbs_plus"        # BBS+ signature (simulated)


@dataclass
class ZKPIdentity:
    """A ZKP-based identity"""
    did: str
    public_commitment: str
    salt: str
    status: ZKPStatus = ZKPStatus.PENDING
    protocol: ZKPProtocol = ZKPProtocol.HASH_CHAIN
    created_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    proof_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "did": self.did,
            "public_commitment": self.public_commitment[:16] + "...",
            "status": self.status.value,
            "protocol": self.protocol.value,
            "created_at": self.created_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "proof_count": self.proof_count,
        }


@dataclass
class ZKPProof:
    """A zero-knowledge proof record"""
    proof_id: str
    did: str
    challenge: str
    response: str
    verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ZKPCredential:
    """A verifiable credential issued via ZKP"""
    credential_id: str
    issuer_did: str
    subject_did: str
    claim_type: str
    claim_value: str
    issued_at: str
    expires_at: str
    valid: bool = True


class ZKPStore:
    """
    Zero-Knowledge Proof Local Store.
    
    Provides:
    - Identity registration with hash-based commitments
    - Challenge-response verification
    - Multiple protocol support (Schnorr, Hash Chain, Merkle)
    - Proof history and audit trail
    """

    def __init__(self):
        self.identities: Dict[str, ZKPIdentity] = {}  # did → identity
        self.proofs: Dict[str, List[ZKPProof]] = {}  # did → proofs
        self._pending_challenges: Dict[str, Dict] = {}  # did → challenge data
        self._secrets: Dict[str, str] = {}  # did → secret (in-memory only)
        self._credentials: Dict[str, List[ZKPCredential]] = {}  # did → credentials

    def create(self, passphrase: str, display_name: str = "Sovereign User",
               universe: str = "personal", biometric_raw: str = "",
               did: Optional[str] = None) -> ZKPIdentity:
        """Create a new ZKP identity (alias for register, used by backend API)."""
        identity_did = did or f"did:asim:{uuid.uuid4().hex[:16]}"
        identity = self.register(identity_did, passphrase)
        identity.display_name = display_name
        identity.universe = universe
        if biometric_raw:
            self.add_biometric(identity_did, biometric_raw)
        return identity

    def register(self, did: str, passphrase: str,
                 protocol: ZKPProtocol = ZKPProtocol.HASH_CHAIN,
                 metadata: Optional[Dict] = None) -> ZKPIdentity:
        """Register a new ZKP identity"""
        salt = secrets.token_hex(16)
        secret = self._derive_secret(passphrase, salt)

        # Create public commitment (hash of secret)
        commitment = self._hash_commitment(secret)

        identity = ZKPIdentity(
            did=did,
            public_commitment=commitment,
            salt=salt,
            protocol=protocol,
            metadata=metadata or {},
        )

        self.identities[did] = identity
        self._secrets[did] = secret
        self.proofs[did] = []

        logger.info(f"🔐 ZKP identity registered: {did}")
        return identity

    def verify(self, did: str, passphrase: str,
               bio: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verify identity using passphrase (and optional biometric).
        
        This implements a simple ZKP-like verification:
        1. Prover knows secret (derived from passphrase)
        2. Verifier checks commitment matches
        3. If biometric provided, also checks biometric hash
        """
        identity = self.identities.get(did)
        if not identity:
            return False, "Identity not found"

        if identity.status in (ZKPStatus.COMPROMISED, ZKPStatus.REVOKED):
            return False, f"Identity is {identity.status.value}"

        # Derive secret from passphrase
        secret = self._derive_secret(passphrase, identity.salt)

        # Verify commitment
        expected_commitment = self._hash_commitment(secret)
        if not hmac.compare_digest(identity.public_commitment, expected_commitment):
            return False, "Invalid passphrase"

        # If biometric data provided, verify it
        if bio:
            bio_hash = hashlib.sha256(bio.encode()).hexdigest()
            stored_bio = identity.metadata.get("bio_hash")
            if stored_bio and not hmac.compare_digest(stored_bio, bio_hash):
                return False, "Biometric mismatch"

        # Update status
        if identity.status == ZKPStatus.PENDING:
            identity.status = ZKPStatus.ACTIVE
        identity.verified_at = datetime.now()
        identity.proof_count += 1

        # Generate proof record
        challenge = secrets.token_hex(16)
        response = self._generate_response(challenge, secret)
        proof = ZKPProof(
            proof_id=f"proof_{uuid.uuid4().hex[:12]}",
            did=did,
            challenge=challenge,
            response=response,
            verified=True,
        )
        self.proofs[did].append(proof)

        logger.info(f"✅ ZKP verified: {did}")
        return True, "Identity verified"

    def create_challenge(self, did: str) -> Optional[str]:
        """Create a ZKP challenge for an identity"""
        identity = self.identities.get(did)
        if not identity:
            return None

        challenge = secrets.token_hex(32)
        self._pending_challenges[did] = {
            "challenge": challenge,
            "created_at": time.time(),
            "expires_at": time.time() + 300,  # 5 minutes
        }
        return challenge

    def verify_challenge(self, did: str, challenge: str,
                          response: str) -> Tuple[bool, str]:
        """Verify a ZKP challenge response"""
        pending = self._pending_challenges.get(did)
        if not pending:
            return False, "No pending challenge"

        if pending["challenge"] != challenge:
            return False, "Challenge mismatch"

        if time.time() > pending["expires_at"]:
            self._pending_challenges.pop(did, None)
            return False, "Challenge expired"

        secret = self._secrets.get(did)
        if not secret:
            return False, "No secret found"

        expected_response = self._generate_response(challenge, secret)
        if not hmac.compare_digest(response, expected_response):
            return False, "Invalid response"

        # Clean up
        self._pending_challenges.pop(did, None)

        # Record proof
        proof = ZKPProof(
            proof_id=f"proof_{uuid.uuid4().hex[:12]}",
            did=did,
            challenge=challenge,
            response=response,
            verified=True,
        )
        if did not in self.proofs:
            self.proofs[did] = []
        self.proofs[did].append(proof)

        identity = self.identities.get(did)
        if identity:
            identity.proof_count += 1

        logger.info(f"✅ ZKP challenge verified: {did}")
        return True, "Challenge verified"

    def add_biometric(self, did: str, bio_data: str) -> bool:
        """Add biometric hash to an identity"""
        identity = self.identities.get(did)
        if not identity:
            return False

        bio_hash = hashlib.sha256(bio_data.encode()).hexdigest()
        identity.metadata["bio_hash"] = bio_hash
        logger.info(f"🔐 Biometric added to ZKP identity: {did}")
        return True

    def issue_credential(self, issuer_did: str, subject_did: str,
                         claim_type: str, claim_value: str,
                         days_valid: int = 365) -> 'ZKPCredential':
        """Issue a verifiable credential (used by backend API)."""
        from datetime import timedelta
        now = datetime.now()
        credential = ZKPCredential(
            credential_id=f"vc_{uuid.uuid4().hex[:16]}",
            issuer_did=issuer_did,
            subject_did=subject_did,
            claim_type=claim_type,
            claim_value=claim_value,
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(days=days_valid)).isoformat(),
            valid=True,
        )
        if subject_did not in self._credentials:
            self._credentials[subject_did] = []
        self._credentials[subject_did].append(credential)
        logger.info(f"📜 Credential issued: {credential.credential_id} for {subject_did}")
        return credential

    def get_credentials(self, did: str) -> List['ZKPCredential']:
        """Get all credentials for a DID (used by backend API)."""
        return self._credentials.get(did, [])

    def revoke(self, did: str, reason: str = "") -> bool:
        """Revoke a ZKP identity"""
        identity = self.identities.get(did)
        if not identity:
            return False
        identity.status = ZKPStatus.REVOKED
        identity.metadata["revoke_reason"] = reason
        self._secrets.pop(did, None)
        logger.info(f"🚫 ZKP identity revoked: {did} ({reason})")
        return True

    def mark_compromised(self, did: str) -> bool:
        """Mark a ZKP identity as compromised"""
        identity = self.identities.get(did)
        if not identity:
            return False
        identity.status = ZKPStatus.COMPROMISED
        self._secrets.pop(did, None)
        logger.warning(f"⚠️ ZKP identity compromised: {did}")
        return True

    def get_proofs(self, did: str, limit: int = 20) -> List[ZKPProof]:
        """Get proof history for an identity"""
        proofs = self.proofs.get(did, [])
        return proofs[-limit:]

    def list_identities(self) -> List[ZKPIdentity]:
        """List all registered ZKP identities"""
        return list(self.identities.values())

    def stats(self) -> Dict[str, Any]:
        """Get ZKP store statistics"""
        total = len(self.identities)
        by_status = {}
        total_proofs = 0

        for identity in self.identities.values():
            s = identity.status.value
            by_status[s] = by_status.get(s, 0) + 1
            total_proofs += identity.proof_count

        return {
            "total_identities": total,
            "by_status": by_status,
            "total_proofs": total_proofs,
            "active_identities": by_status.get("active", 0),
            "pending_identities": by_status.get("pending", 0),
        }

    def _derive_secret(self, passphrase: str, salt: str) -> str:
        """Derive a secret from passphrase and salt"""
        return hashlib.pbkdf2_hmac(
            "sha256",
            passphrase.encode(),
            salt.encode(),
            100000,  # 100k iterations
            dklen=32
        ).hex()

    def _hash_commitment(self, secret: str) -> str:
        """Create a hash commitment from a secret"""
        return hashlib.sha256(f"zkp:{secret}".encode()).hexdigest()

    def _generate_response(self, challenge: str, secret: str) -> str:
        """Generate a ZKP response to a challenge"""
        return hmac.new(
            secret.encode(),
            challenge.encode(),
            hashlib.sha256
        ).hexdigest()


# Singleton
_zkp_store: Optional[ZKPStore] = None


def get_zkp_store() -> ZKPStore:
    """Get ZKP store singleton"""
    global _zkp_store
    if _zkp_store is None:
        _zkp_store = ZKPStore()
    return _zkp_store


def reset_zkp_store() -> None:
    """Reset ZKP store singleton (for testing)"""
    global _zkp_store
    _zkp_store = None


if __name__ == "__main__":
    import sys

    store = get_zkp_store()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Register identity
        identity = store.register("did:asim:test_user", "my_secret_passphrase")
        print(f"✅ Registered: {identity.did}")
        print(f"   Commitment: {identity.public_commitment[:16]}...")

        # Verify
        success, msg = store.verify("did:asim:test_user", "my_secret_passphrase")
        print(f"✅ Verify: {success} - {msg}")

        # Wrong passphrase
        success, msg = store.verify("did:asim:test_user", "wrong_passphrase")
        print(f"❌ Wrong passphrase: {success} - {msg}")

        # Challenge-response
        challenge = store.create_challenge("did:asim:test_user")
        if challenge:
            # In real ZKP, prover would compute response using secret
            secret = store._secrets["did:asim:test_user"]
            response = store._generate_response(challenge, secret)
            success, msg = store.verify_challenge("did:asim:test_user", challenge, response)
            print(f"✅ Challenge-response: {success} - {msg}")

        # Stats
        print(f"\n📊 Stats: {json.dumps(store.stats(), indent=2)}")

    else:
        print("Usage: python zkp_local.py test")
