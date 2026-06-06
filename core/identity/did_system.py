#!/usr/bin/env python3
"""
core/identity/did_system.py
AsimNexus — Decentralized Identifier (DID) System

Implements W3C DID Core specification for decentralized identity management.
DIDs are used for mesh nodes, agents, clones, and user identities.

Provides:
  - DIDMethod, DIDStatus enums
  - DIDDocument, DIDRecord dataclasses
  - DIDSystem: main class for DID lifecycle management
  - Singleton factory: get_did_system() / reset_did_system()
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
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class DIDMethod(Enum):
    """Supported DID methods"""
    ASIM = "asim"          # Native AsimNexus DID
    KEY = "key"            # did:key
    WEB = "web"            # did:web
    PEER = "peer"          # did:peer (DIDComm)
    ETHR = "ethr"          # did:ethr (Ethereum)


class DIDStatus(Enum):
    """DID lifecycle states"""
    CREATED = "created"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class DIDDocument:
    """W3C DID Document"""
    id: str
    also_known_as: List[str] = field(default_factory=list)
    controller: Optional[str] = None
    verification_method: List[Dict] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    assertion_method: List[str] = field(default_factory=list)
    key_agreement: List[str] = field(default_factory=list)
    capability_invocation: List[str] = field(default_factory=list)
    capability_delegation: List[str] = field(default_factory=list)
    service: List[Dict] = field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None
    proof: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        result = {
            "@context": "https://www.w3.org/ns/did/v1",
            "id": self.id,
        }
        if self.also_known_as:
            result["alsoKnownAs"] = self.also_known_as
        if self.controller:
            result["controller"] = self.controller
        if self.verification_method:
            result["verificationMethod"] = self.verification_method
        if self.authentication:
            result["authentication"] = self.authentication
        if self.assertion_method:
            result["assertionMethod"] = self.assertion_method
        if self.key_agreement:
            result["keyAgreement"] = self.key_agreement
        if self.capability_invocation:
            result["capabilityInvocation"] = self.capability_invocation
        if self.capability_delegation:
            result["capabilityDelegation"] = self.capability_delegation
        if self.service:
            result["service"] = self.service
        if self.created:
            result["created"] = self.created
        if self.updated:
            result["updated"] = self.updated
        if self.proof:
            result["proof"] = self.proof
        return result


@dataclass
class DIDRecord:
    """Internal DID record with metadata"""
    did: str
    method: DIDMethod
    subject_id: str  # The entity this DID belongs to
    subject_type: str  # user | node | agent | clone
    status: DIDStatus = DIDStatus.CREATED
    document: Optional[DIDDocument] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "did": self.did,
            "method": self.method.value,
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "status": self.status.value,
            "document": self.document.to_dict() if self.document else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
        }


class DIDSystem:
    """
    Decentralized Identifier (DID) System.
    
    Implements W3C DID Core for:
    - DID creation and resolution
    - DID document management
    - Key management (verification methods)
    - Service endpoint registration
    - DID revocation and recovery
    """

    def __init__(self):
        self.records: Dict[str, DIDRecord] = {}  # did → record
        self._subject_index: Dict[str, List[str]] = {}  # subject_id → [dids]

    def create_did(self, subject_id: str, subject_type: str = "user",
                   method: DIDMethod = DIDMethod.ASIM,
                   tags: Optional[Dict] = None) -> DIDRecord:
        """Create a new DID for a subject"""
        # Generate unique identifier
        identifier = uuid.uuid4().hex[:24]
        did = f"did:{method.value}:{identifier}"

        # Generate key pair (simulated)
        public_key = f"z{secrets.token_hex(32)}"
        key_id = f"{did}#keys-1"

        # Build DID document
        document = DIDDocument(
            id=did,
            also_known_as=[f"asim:{subject_type}:{subject_id}"],
            controller=did,
            verification_method=[{
                "id": key_id,
                "type": "Ed25519VerificationKey2020",
                "controller": did,
                "publicKeyMultibase": public_key,
            }],
            authentication=[key_id],
            assertion_method=[key_id],
            capability_invocation=[key_id],
            capability_delegation=[key_id],
            service=[{
                "id": f"{did}#asim-nexus",
                "type": "AsimNexusMesh",
                "serviceEndpoint": "https://asim.nexus/mesh",
            }],
            created=datetime.now().isoformat(),
            updated=datetime.now().isoformat(),
        )

        record = DIDRecord(
            did=did,
            method=method,
            subject_id=subject_id,
            subject_type=subject_type,
            document=document,
            tags=tags or {},
        )

        self.records[did] = record

        # Index by subject
        if subject_id not in self._subject_index:
            self._subject_index[subject_id] = []
        self._subject_index[subject_id].append(did)

        logger.info(f"🔑 DID created: {did} for {subject_type}:{subject_id}")
        return record

    def resolve(self, did: str) -> Optional[DIDDocument]:
        """Resolve a DID to its document"""
        record = self.records.get(did)
        if not record:
            return None
        if record.status in (DIDStatus.REVOKED, DIDStatus.EXPIRED):
            return None
        return record.document

    def resolve_with_metadata(self, did: str) -> Optional[DIDRecord]:
        """Resolve a DID with full metadata"""
        record = self.records.get(did)
        if not record:
            return None
        return record

    def get_by_subject(self, subject_id: str) -> List[DIDRecord]:
        """Get all DIDs for a subject"""
        dids = self._subject_index.get(subject_id, [])
        return [self.records[d] for d in dids if d in self.records]

    def add_verification_method(self, did: str, method_type: str,
                                 public_key: str) -> bool:
        """Add a verification method to a DID document"""
        record = self.records.get(did)
        if not record or not record.document:
            return False

        key_id = f"{did}#keys-{len(record.document.verification_method) + 1}"
        method = {
            "id": key_id,
            "type": method_type,
            "controller": did,
            "publicKeyMultibase": public_key,
        }
        record.document.verification_method.append(method)
        record.document.updated = datetime.now().isoformat()
        record.updated_at = datetime.now()
        return True

    def add_service_endpoint(self, did: str, service_type: str,
                              endpoint: str) -> bool:
        """Add a service endpoint to a DID document"""
        record = self.records.get(did)
        if not record or not record.document:
            return False

        service = {
            "id": f"{did}#svc-{len(record.document.service) + 1}",
            "type": service_type,
            "serviceEndpoint": endpoint,
        }
        record.document.service.append(service)
        record.document.updated = datetime.now().isoformat()
        record.updated_at = datetime.now()
        return True

    def activate(self, did: str) -> bool:
        """Activate a DID"""
        record = self.records.get(did)
        if not record:
            return False
        record.status = DIDStatus.ACTIVE
        record.updated_at = datetime.now()
        if record.document:
            record.document.updated = datetime.now().isoformat()
        logger.info(f"✅ DID activated: {did}")
        return True

    def suspend(self, did: str, reason: str = "") -> bool:
        """Suspend a DID"""
        record = self.records.get(did)
        if not record:
            return False
        record.status = DIDStatus.SUSPENDED
        record.updated_at = datetime.now()
        record.metadata["suspend_reason"] = reason
        if record.document:
            record.document.updated = datetime.now().isoformat()
        logger.info(f"⏸️ DID suspended: {did} ({reason})")
        return True

    def revoke(self, did: str, reason: str = "") -> bool:
        """Permanently revoke a DID"""
        record = self.records.get(did)
        if not record:
            return False
        record.status = DIDStatus.REVOKED
        record.updated_at = datetime.now()
        record.metadata["revoke_reason"] = reason
        if record.document:
            record.document.updated = datetime.now().isoformat()
        logger.info(f"🚫 DID revoked: {did} ({reason})")
        return True

    def deactivate(self, did: str) -> bool:
        """Deactivate a DID (alias for revoke)"""
        return self.revoke(did, "Deactivated by user")

    def update_did_document(self, did: str, updates: Dict) -> bool:
        """Update DID document fields"""
        record = self.records.get(did)
        if not record or not record.document:
            return False

        doc = record.document
        if "also_known_as" in updates:
            doc.also_known_as = updates["also_known_as"]
        if "controller" in updates:
            doc.controller = updates["controller"]
        if "service" in updates:
            doc.service = updates["service"]

        doc.updated = datetime.now().isoformat()
        record.updated_at = datetime.now()
        return True

    def verify_did(self, did: str) -> Tuple[bool, str]:
        """Verify a DID is valid and active"""
        record = self.records.get(did)
        if not record:
            return False, "DID not found"
        if record.status == DIDStatus.REVOKED:
            return False, "DID has been revoked"
        if record.status == DIDStatus.EXPIRED:
            return False, "DID has expired"
        if record.status == DIDStatus.SUSPENDED:
            return False, "DID is suspended"
        return True, "DID is valid and active"

    def search(self, query: str) -> List[DIDRecord]:
        """Search DIDs by subject ID or tags"""
        query = query.lower()
        results = []
        for record in self.records.values():
            if (query in record.subject_id.lower() or
                query in record.did.lower() or
                any(query in v.lower() for v in record.tags.values())):
                results.append(record)
        return results

    def list_dids(self, status: Optional[DIDStatus] = None,
                  method: Optional[DIDMethod] = None,
                  subject_type: Optional[str] = None,
                  limit: int = 100) -> List[DIDRecord]:
        """List DIDs with optional filters"""
        results = list(self.records.values())

        if status:
            results = [r for r in results if r.status == status]
        if method:
            results = [r for r in results if r.method == method]
        if subject_type:
            results = [r for r in results if r.subject_type == subject_type]

        return results[:limit]

    def stats(self) -> Dict[str, Any]:
        """Get DID system statistics"""
        total = len(self.records)
        by_status = {}
        by_method = {}
        by_type = {}

        for record in self.records.values():
            s = record.status.value
            by_status[s] = by_status.get(s, 0) + 1

            m = record.method.value
            by_method[m] = by_method.get(m, 0) + 1

            t = record.subject_type
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total_dids": total,
            "by_status": by_status,
            "by_method": by_method,
            "by_subject_type": by_type,
            "active_dids": by_status.get("active", 0),
        }


# Singleton
_did_system: Optional[DIDSystem] = None


def get_did_system() -> DIDSystem:
    """Get DID system singleton"""
    global _did_system
    if _did_system is None:
        _did_system = DIDSystem()
    return _did_system


def reset_did_system() -> None:
    """Reset DID system singleton (for testing)"""
    global _did_system
    _did_system = None


if __name__ == "__main__":
    import sys

    system = get_did_system()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Create DIDs
        user_did = system.create_did("user_001", "user")
        print(f"✅ User DID: {user_did.did}")

        node_did = system.create_did("node_001", "node", DIDMethod.PEER)
        print(f"✅ Node DID: {node_did.did}")

        agent_did = system.create_did("agent_001", "agent", DIDMethod.KEY)
        print(f"✅ Agent DID: {agent_did.did}")

        # Activate
        system.activate(user_did.did)
        print(f"✅ Activated: {user_did.did}")

        # Resolve
        doc = system.resolve(user_did.did)
        print(f"✅ Resolved: {doc.id if doc else 'None'}")

        # Stats
        print(f"\n📊 Stats: {json.dumps(system.stats(), indent=2)}")

    else:
        print("Usage: python did_system.py test")
