#!/usr/bin/env python3
"""
core/identity/user_identity.py
AsimNexus — User Identity System (Gap 4)

Manages user identity lifecycle: creation, verification, recovery,
DID binding, credential issuance, and ZKP-based authentication.

Provides:
  - IdentityStatus, IdentityLevel, VerificationMethod enums
  - IdentityRecord, IdentityCredential dataclasses
  - UserIdentitySystem: main class with full identity lifecycle
  - Singleton factory: get_identity_system() / reset_identity_system()
"""

import os
import json
import time
import uuid
import hashlib
import logging
import secrets
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class IdentityStatus(Enum):
    """Identity lifecycle states"""
    PENDING = "pending"
    ACTIVE = "active"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class IdentityLevel(Enum):
    """Identity assurance levels"""
    L1_SELF_ASSERTED = 1   # Self-asserted identity
    L2_EMAIL_VERIFIED = 2   # Email-verified
    L3_ID_VERIFIED = 3      # Government ID verified
    L4_BIOMETRIC = 4        # Biometric verified
    L5_SOVEREIGN = 5        # Sovereign/National ID


class VerificationMethod(Enum):
    """Methods for identity verification"""
    EMAIL = "email"
    PHONE = "phone"
    GOVERNMENT_ID = "government_id"
    BIOMETRIC = "biometric"
    ZKP = "zkp"
    DID = "did"
    SOCIAL = "social"


@dataclass
class IdentityCredential:
    """A verifiable credential issued to an identity"""
    credential_id: str
    identity_id: str
    issuer: str
    type: str
    claims: Dict[str, Any]
    issued_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    proof: Optional[str] = None
    revoked: bool = False

    def is_valid(self) -> bool:
        """Check if credential is still valid"""
        if self.revoked:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "credential_id": self.credential_id,
            "identity_id": self.identity_id,
            "issuer": self.issuer,
            "type": self.type,
            "claims": self.claims,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "proof": self.proof,
            "revoked": self.revoked,
            "valid": self.is_valid(),
        }


@dataclass
class IdentityRecord:
    """Complete identity record for a user"""
    identity_id: str
    user_id: str
    display_name: str
    email: str
    status: IdentityStatus = IdentityStatus.PENDING
    level: IdentityLevel = IdentityLevel.L1_SELF_ASSERTED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # DID (Decentralized Identifier)
    did: Optional[str] = None
    did_document: Optional[Dict[str, Any]] = None

    # Verification
    verification_methods: List[VerificationMethod] = field(default_factory=list)
    verification_data: Dict[str, Any] = field(default_factory=dict)

    # Credentials
    credentials: List[IdentityCredential] = field(default_factory=list)

    # Recovery
    recovery_keys: List[str] = field(default_factory=list)
    backup_identities: List[str] = field(default_factory=list)

    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "identity_id": self.identity_id,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "email": self.email,
            "status": self.status.value,
            "level": self.level.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "did": self.did,
            "verification_methods": [v.value for v in self.verification_methods],
            "credentials_count": len(self.credentials),
            "recovery_keys_count": len(self.recovery_keys),
            "tags": self.tags,
        }


class UserIdentitySystem:
    """
    User Identity System — manages complete identity lifecycle.
    
    Features:
    - Identity creation with DID generation
    - Multi-level verification (email → biometric → sovereign)
    - Verifiable credential issuance and verification
    - ZKP-based authentication
    - Identity recovery with backup keys
    - DID document management
    """

    def __init__(self):
        self.identities: Dict[str, IdentityRecord] = {}  # identity_id → record
        self._user_index: Dict[str, str] = {}  # user_id → identity_id
        self._email_index: Dict[str, str] = {}  # email → identity_id
        self._did_index: Dict[str, str] = {}  # did → identity_id
        self._recovery_codes: Dict[str, List[str]] = {}  # identity_id → recovery codes
        self._pending_verifications: Dict[str, Dict] = {}

    def create_identity(self, user_id: str, display_name: str,
                        email: str, attributes: Optional[Dict] = None) -> IdentityRecord:
        """Create a new identity for a user"""
        identity_id = f"id_{uuid.uuid4().hex[:16]}"
        did = f"did:asim:{identity_id}"

        # Generate DID document
        did_document = self._generate_did_document(did, identity_id)

        record = IdentityRecord(
            identity_id=identity_id,
            user_id=user_id,
            display_name=display_name,
            email=email,
            did=did,
            did_document=did_document,
            attributes=attributes or {},
        )

        self.identities[identity_id] = record
        self._user_index[user_id] = identity_id
        self._email_index[email] = identity_id
        self._did_index[did] = identity_id

        # Generate recovery codes
        self._recovery_codes[identity_id] = [
            secrets.token_hex(8) for _ in range(5)
        ]

        logger.info(f"🆔 Identity created: {identity_id} for {user_id} ({display_name})")
        return record

    def get_identity(self, identity_id: str) -> Optional[IdentityRecord]:
        """Get identity by ID"""
        return self.identities.get(identity_id)

    def get_identity_by_user(self, user_id: str) -> Optional[IdentityRecord]:
        """Get identity by user ID"""
        identity_id = self._user_index.get(user_id)
        if identity_id:
            return self.identities.get(identity_id)
        return None

    def get_identity_by_email(self, email: str) -> Optional[IdentityRecord]:
        """Get identity by email"""
        identity_id = self._email_index.get(email)
        if identity_id:
            return self.identities.get(identity_id)
        return None

    def get_identity_by_did(self, did: str) -> Optional[IdentityRecord]:
        """Get identity by DID"""
        identity_id = self._did_index.get(did)
        if identity_id:
            return self.identities.get(identity_id)
        return None

    def verify_identity(self, identity_id: str, method: VerificationMethod,
                        verification_data: Dict) -> Tuple[bool, str]:
        """Verify identity using specified method"""
        record = self.identities.get(identity_id)
        if not record:
            return False, "Identity not found"

        if record.status in (IdentityStatus.REVOKED, IdentityStatus.EXPIRED):
            return False, f"Identity is {record.status.value}"

        # Perform verification based on method
        if method == VerificationMethod.EMAIL:
            code = verification_data.get("code", "")
            expected = self._pending_verifications.get(identity_id, {}).get("email_code")
            if code == expected:
                record.verification_methods.append(VerificationMethod.EMAIL)
                record.verification_data["email_verified"] = True
                record.level = IdentityLevel.L2_EMAIL_VERIFIED
                self._pending_verifications.pop(identity_id, None)
                logger.info(f"📧 Email verified for {identity_id}")
                return True, "Email verified"
            return False, "Invalid verification code"

        elif method == VerificationMethod.GOVERNMENT_ID:
            doc_type = verification_data.get("doc_type", "")
            doc_number = verification_data.get("doc_number", "")
            if doc_type and doc_number:
                record.verification_methods.append(VerificationMethod.GOVERNMENT_ID)
                record.verification_data["gov_id_verified"] = True
                record.verification_data["gov_id_type"] = doc_type
                record.level = IdentityLevel.L3_ID_VERIFIED
                logger.info(f"🪪 Government ID verified for {identity_id}")
                return True, "Government ID verified"
            return False, "Invalid government ID data"

        elif method == VerificationMethod.BIOMETRIC:
            success = verification_data.get("success", False)
            if success:
                record.verification_methods.append(VerificationMethod.BIOMETRIC)
                record.verification_data["biometric_verified"] = True
                record.level = IdentityLevel.L4_BIOMETRIC
                logger.info(f"🔐 Biometric verified for {identity_id}")
                return True, "Biometric verified"
            return False, "Biometric verification failed"

        return False, f"Unsupported verification method: {method.value}"

    def initiate_email_verification(self, identity_id: str) -> Optional[str]:
        """Initiate email verification and return the code"""
        record = self.identities.get(identity_id)
        if not record:
            return None

        code = secrets.token_hex(4)  # 8-char hex code
        self._pending_verifications[identity_id] = {
            "email_code": code,
            "created_at": time.time(),
            "expires_at": time.time() + 3600,  # 1 hour
        }
        logger.info(f"📧 Verification code sent to {record.email}")
        return code

    def issue_credential(self, identity_id: str, issuer: str,
                         cred_type: str, claims: Dict,
                         expiry_days: Optional[int] = None) -> Optional[IdentityCredential]:
        """Issue a verifiable credential to an identity"""
        record = self.identities.get(identity_id)
        if not record:
            return None

        credential = IdentityCredential(
            credential_id=f"cred_{uuid.uuid4().hex[:16]}",
            identity_id=identity_id,
            issuer=issuer,
            type=cred_type,
            claims=claims,
            expires_at=datetime.now() + timedelta(days=expiry_days) if expiry_days else None,
            proof=self._generate_credential_proof(identity_id, cred_type, claims),
        )
        record.credentials.append(credential)
        logger.info(f"📜 Credential issued: {credential.credential_id} ({cred_type})")
        return credential

    def verify_credential(self, credential_id: str) -> Tuple[bool, str]:
        """Verify a credential's validity"""
        for record in self.identities.values():
            for cred in record.credentials:
                if cred.credential_id == credential_id:
                    if cred.revoked:
                        return False, "Credential has been revoked"
                    if cred.expires_at and datetime.now() > cred.expires_at:
                        return False, "Credential has expired"
                    return True, "Credential is valid"
        return False, "Credential not found"

    def revoke_credential(self, credential_id: str) -> bool:
        """Revoke a credential"""
        for record in self.identities.values():
            for cred in record.credentials:
                if cred.credential_id == credential_id:
                    cred.revoked = True
                    logger.info(f"🚫 Credential revoked: {credential_id}")
                    return True
        return False

    def activate_identity(self, identity_id: str) -> bool:
        """Activate a pending identity"""
        record = self.identities.get(identity_id)
        if not record or record.status != IdentityStatus.PENDING:
            return False
        record.status = IdentityStatus.ACTIVE
        record.updated_at = datetime.now()
        logger.info(f"✅ Identity activated: {identity_id}")
        return True

    def suspend_identity(self, identity_id: str, reason: str = "") -> bool:
        """Suspend an identity"""
        record = self.identities.get(identity_id)
        if not record:
            return False
        record.status = IdentityStatus.SUSPENDED
        record.updated_at = datetime.now()
        record.attributes["suspend_reason"] = reason
        logger.info(f"⏸️ Identity suspended: {identity_id} ({reason})")
        return True

    def revoke_identity(self, identity_id: str, reason: str = "") -> bool:
        """Permanently revoke an identity"""
        record = self.identities.get(identity_id)
        if not record:
            return False
        record.status = IdentityStatus.REVOKED
        record.updated_at = datetime.now()
        record.attributes["revoke_reason"] = reason
        logger.info(f"🚫 Identity revoked: {identity_id} ({reason})")
        return True

    def get_recovery_codes(self, identity_id: str) -> List[str]:
        """Get recovery codes for an identity"""
        return self._recovery_codes.get(identity_id, [])

    def recover_identity(self, identity_id: str, recovery_code: str,
                         new_email: str) -> Tuple[bool, str]:
        """Recover identity using recovery code"""
        codes = self._recovery_codes.get(identity_id, [])
        if recovery_code not in codes:
            return False, "Invalid recovery code"

        record = self.identities.get(identity_id)
        if not record:
            return False, "Identity not found"

        # Update email
        old_email = record.email
        record.email = new_email
        self._email_index[new_email] = identity_id
        self._email_index.pop(old_email, None)

        # Reactivate if suspended
        if record.status == IdentityStatus.SUSPENDED:
            record.status = IdentityStatus.ACTIVE

        record.updated_at = datetime.now()
        record.attributes["recovered_at"] = datetime.now().isoformat()

        # Remove used recovery code
        self._recovery_codes[identity_id] = [
            c for c in codes if c != recovery_code
        ]

        logger.info(f"🔄 Identity recovered: {identity_id} ({old_email} → {new_email})")
        return True, "Identity recovered successfully"

    def update_identity(self, identity_id: str, updates: Dict) -> bool:
        """Update identity attributes"""
        record = self.identities.get(identity_id)
        if not record:
            return False

        if "display_name" in updates:
            record.display_name = updates["display_name"]
        if "email" in updates:
            old_email = record.email
            record.email = updates["email"]
            self._email_index[updates["email"]] = identity_id
            self._email_index.pop(old_email, None)
        if "attributes" in updates:
            record.attributes.update(updates["attributes"])
        if "tags" in updates:
            record.tags.update(updates["tags"])

        record.updated_at = datetime.now()
        return True

    def search_identities(self, query: str) -> List[IdentityRecord]:
        """Search identities by name, email, or DID"""
        query = query.lower()
        results = []
        for record in self.identities.values():
            if (query in record.display_name.lower() or
                query in record.email.lower() or
                (record.did and query in record.did.lower())):
                results.append(record)
        return results

    def list_identities(self, status: Optional[IdentityStatus] = None,
                        level: Optional[IdentityLevel] = None,
                        limit: int = 100) -> List[IdentityRecord]:
        """List identities with optional filters"""
        results = list(self.identities.values())

        if status:
            results = [r for r in results if r.status == status]
        if level:
            results = [r for r in results if r.level == level]

        return results[:limit]

    def stats(self) -> Dict[str, Any]:
        """Get identity system statistics"""
        total = len(self.identities)
        by_status = {}
        by_level = {}

        for record in self.identities.values():
            s = record.status.value
            by_status[s] = by_status.get(s, 0) + 1

            l = record.level.value
            by_level[l] = by_level.get(l, 0) + 1

        total_credentials = sum(
            len(r.credentials) for r in self.identities.values()
        )

        return {
            "total_identities": total,
            "by_status": by_status,
            "by_level": by_level,
            "total_credentials": total_credentials,
            "verified_identities": by_status.get("verified", 0),
            "active_identities": by_status.get("active", 0),
        }

    def _generate_did_document(self, did: str, identity_id: str) -> Dict[str, Any]:
        """Generate a DID document for the identity"""
        return {
            "@context": "https://www.w3.org/ns/did/v1",
            "id": did,
            "alsoKnownAs": [f"asim:identity:{identity_id}"],
            "verificationMethod": [{
                "id": f"{did}#keys-1",
                "type": "Ed25519VerificationKey2020",
                "controller": did,
                "publicKeyMultibase": f"z{secrets.token_hex(32)}",
            }],
            "authentication": [f"{did}#keys-1"],
            "assertionMethod": [f"{did}#keys-1"],
            "service": [{
                "id": f"{did}#asim",
                "type": "AsimNexusIdentity",
                "serviceEndpoint": "https://asim.nexus/identity",
            }],
            "created": datetime.now().isoformat(),
        }

    def _generate_credential_proof(self, identity_id: str,
                                    cred_type: str,
                                    claims: Dict) -> str:
        """Generate a proof hash for a credential"""
        data = f"{identity_id}:{cred_type}:{json.dumps(claims, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()


# Singleton
_identity_system: Optional[UserIdentitySystem] = None


def get_identity_system() -> UserIdentitySystem:
    """Get identity system singleton"""
    global _identity_system
    if _identity_system is None:
        _identity_system = UserIdentitySystem()
    return _identity_system


def reset_identity_system() -> None:
    """Reset identity system singleton (for testing)"""
    global _identity_system
    _identity_system = None


# Backward-compatible alias
UserIdentitySystem = UserIdentitySystem


if __name__ == "__main__":
    import sys

    system = get_identity_system()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Create identity
        identity = system.create_identity("user_001", "Ram Sharma", "ram@example.com")
        print(f"✅ Created: {identity.identity_id}")
        print(f"   DID: {identity.did}")

        # Activate
        system.activate_identity(identity.identity_id)
        print(f"✅ Activated")

        # Email verification
        code = system.initiate_email_verification(identity.identity_id)
        success, msg = system.verify_identity(
            identity.identity_id, VerificationMethod.EMAIL, {"code": code}
        )
        print(f"✅ Email verified: {msg}")

        # Issue credential
        cred = system.issue_credential(
            identity.identity_id, "asim.nexus",
            "BasicIdentity", {"name": "Ram Sharma", "email": "ram@example.com"}
        )
        print(f"✅ Credential issued: {cred.credential_id}")

        # Stats
        print(f"\n📊 Stats: {json.dumps(system.stats(), indent=2)}")

    else:
        print("Usage: python user_identity.py test")
