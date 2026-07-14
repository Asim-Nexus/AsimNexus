"""
Blockchain Identity Advanced — DID creation, credential issuance, and verification.
=====================================================================================
Provides a simulated blockchain identity system with support for
DID creation, verifiable credential issuance, and credential verification.

Exports:
    BlockchainNetwork     — enum of supported blockchain networks
    AttestationType       — enum of credential/attestation types
    DIDDocument           — dataclass for DID documents
    VerifiableCredential  — dataclass for verifiable credentials
    ZKProof               — dataclass for zero-knowledge proofs
    SoulboundToken        — dataclass for soulbound tokens
    BlockchainIdentityAdvanced  — main class
    get_blockchain_identity_advanced()  — singleton factory
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List


class BlockchainNetwork(Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    SOLANA = "solana"
    HYPERLEDGER = "hyperledger"
    ASIM_CHAIN = "asim_chain"
    POLKADOT = "polkadot"


class AttestationType(Enum):
    """Types of attestations/credentials."""
    IDENTITY = "identity"
    CREDENTIAL = "credential"
    REPUTATION = "reputation"
    MEMBERSHIP = "membership"
    AUTHORIZATION = "authorization"
    EDUCATION = "education"
    EMPLOYMENT = "employment"


@dataclass
class DIDDocument:
    """Decentralized Identifier document."""
    did: str
    public_key: str
    network: BlockchainNetwork
    created: str
    updated: str
    status: str = "active"
    controller: str = ""


@dataclass
class VerifiableCredential:
    """A verifiable credential issued by a DID."""
    vc_id: str
    issuer_did: str
    subject_did: str
    credential_type: AttestationType
    claims: Dict[str, Any]
    issued: str
    expires: str
    valid: bool = True
    revoked: bool = False
    revocation_reason: str = ""


@dataclass
class ZKProof:
    """A zero-knowledge proof."""
    proof_id: str
    prover_did: str
    statement: str
    created: str
    verified: bool = False


@dataclass
class SoulboundToken:
    """A non-transferable soulbound token."""
    sbt_id: str
    owner_did: str
    token_type: str
    metadata: Dict[str, Any]
    issuer: str
    network: BlockchainNetwork
    issued: str


class BlockchainIdentityAdvanced:
    """Blockchain-based identity management with DID and VC support."""

    def __init__(self):
        self._dids: Dict[str, DIDDocument] = {}
        self._credentials: Dict[str, VerifiableCredential] = {}
        self._sbts: Dict[str, SoulboundToken] = {}
        self._zk_proofs: Dict[str, ZKProof] = {}
        self._ledger: List[Dict[str, Any]] = []

    def _log_ledger(self, action: str, detail: Dict[str, Any]) -> None:
        """Add an entry to the audit ledger."""
        self._ledger.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            **detail,
        })

    def create_did(self, public_key: str, network: BlockchainNetwork) -> str:
        """Create a new Decentralized Identifier (DID).

        Args:
            public_key: The public key hex string
            network: The blockchain network

        Returns:
            DID string (e.g., did:asim:<hash>)
        """
        did_hash = hashlib.sha256(f"{public_key}:{network.value}:{secrets.token_hex(4)}".encode()).hexdigest()[:24]
        did = f"did:asim:{did_hash}"

        now = datetime.utcnow().isoformat()
        doc = DIDDocument(
            did=did,
            public_key=public_key,
            network=network,
            created=now,
            updated=now,
            controller=did,
        )
        self._dids[did] = doc
        self._log_ledger("create_did", {"did": did, "network": network.value})
        return did

    def get_did_document(self, did: str) -> Optional[DIDDocument]:
        """Get a DID document object directly.

        Args:
            did: The DID string

        Returns:
            DIDDocument if found, None otherwise
        """
        return self._dids.get(did)

    def get_did(self, did: str) -> Optional[Dict[str, Any]]:
        """Get a DID document as a dict.

        Args:
            did: The DID string

        Returns:
            Dict with DID details if found, None otherwise
        """
        doc = self._dids.get(did)
        if doc:
            return {
                "did": doc.did,
                "public_key": doc.public_key,
                "network": doc.network.value,
                "status": doc.status,
                "controller": doc.controller,
            }
        return None

    def issue_credential(
        self,
        issuer_did: str,
        subject_did: str,
        credential_type: AttestationType,
        claims: Dict[str, Any],
        expiration_days: int = 365,
    ) -> str:
        """Issue a verifiable credential.

        Args:
            issuer_did: The DID of the issuer
            subject_did: The DID of the subject
            credential_type: Type of credential
            claims: Claims data
            expiration_days: Days until expiration (default: 365)

        Returns:
            Verifiable credential ID string
        """
        vc_id = f"vc_{hashlib.sha256(f'{issuer_did}:{subject_did}:{credential_type.value}:{secrets.token_hex(4)}'.encode()).hexdigest()[:16]}"

        now = datetime.utcnow()
        expires = (now + timedelta(days=expiration_days)).isoformat()

        vc = VerifiableCredential(
            vc_id=vc_id,
            issuer_did=issuer_did,
            subject_did=subject_did,
            credential_type=credential_type,
            claims=claims,
            issued=now.isoformat(),
            expires=expires,
        )
        self._credentials[vc_id] = vc
        self._log_ledger("issue_credential", {
            "vc_id": vc_id,
            "issuer": issuer_did,
            "subject": subject_did,
            "type": credential_type.value,
        })
        return vc_id

    def verify_credential(self, vc_id: str) -> Dict[str, Any]:
        """Verify a verifiable credential.

        Args:
            vc_id: The credential ID to verify

        Returns:
            Dict with 'valid' bool and details
        """
        vc = self._credentials.get(vc_id)
        if not vc:
            return {"valid": False, "error": "Credential not found"}

        # Check revocation
        if vc.revoked:
            return {"valid": False, "error": vc.revocation_reason}

        # Check expiry
        expires = datetime.fromisoformat(vc.expires)
        if datetime.utcnow() > expires:
            vc.valid = False
            return {"valid": False, "error": "Credential expired"}

        # Check issuer exists
        if vc.issuer_did not in self._dids:
            return {"valid": False, "error": "Issuer DID not found"}

        return {
            "valid": vc.valid,
            "vc_id": vc_id,
            "issuer_did": vc.issuer_did,
            "subject_did": vc.subject_did,
            "credential_type": vc.credential_type.value,
            "claims": vc.claims,
            "type": vc.credential_type.value,
        }

    def get_credentials_for_subject(
        self, subject_did: str, credential_type: Optional[AttestationType] = None
    ) -> List[VerifiableCredential]:
        """Get all credentials for a subject, optionally filtered by type.

        Args:
            subject_did: The subject's DID
            credential_type: Optional filter by credential type

        Returns:
            List of matching VerifiableCredential objects
        """
        results = []
        for vc in self._credentials.values():
            if vc.subject_did == subject_did:
                if credential_type is None or vc.credential_type == credential_type:
                    results.append(vc)
        return results

    def revoke_credential(self, vc_id: str, reason: str = "") -> bool:
        """Revoke a verifiable credential.

        Args:
            vc_id: The credential ID to revoke
            reason: Reason for revocation

        Returns:
            True if revoked, False if not found
        """
        vc = self._credentials.get(vc_id)
        if not vc:
            return False
        vc.revoked = True
        vc.revocation_reason = reason
        vc.valid = False
        self._log_ledger("revoke_credential", {
            "vc_id": vc_id,
            "reason": reason,
        })
        return True

    def issue_soulbound_token(
        self,
        owner_did: str,
        token_type: str,
        metadata: Dict[str, Any],
        issuer: str,
        network: BlockchainNetwork,
    ) -> str:
        """Issue a non-transferable soulbound token.

        Args:
            owner_did: The owner's DID
            token_type: Type of SBT (e.g., "identity", "membership")
            metadata: Token metadata
            issuer: Issuer identifier
            network: Blockchain network

        Returns:
            SBT ID string
        """
        sbt_id = f"sbt_{hashlib.sha256(f'{owner_did}:{token_type}:{secrets.token_hex(4)}'.encode()).hexdigest()[:16]}"

        sbt = SoulboundToken(
            sbt_id=sbt_id,
            owner_did=owner_did,
            token_type=token_type,
            metadata=metadata,
            issuer=issuer,
            network=network,
            issued=datetime.utcnow().isoformat(),
        )
        self._sbts[sbt_id] = sbt
        self._log_ledger("issue_sbt", {
            "sbt_id": sbt_id,
            "owner": owner_did,
            "type": token_type,
        })
        return sbt_id

    def get_sbts_for_owner(self, owner_did: str) -> List[SoulboundToken]:
        """Get all soulbound tokens for an owner.

        Args:
            owner_did: The owner's DID

        Returns:
            List of matching SoulboundToken objects
        """
        return [sbt for sbt in self._sbts.values() if sbt.owner_did == owner_did]

    def create_zk_proof(
        self, prover_did: str, statement: str, secret_data: str
    ) -> ZKProof:
        """Create a zero-knowledge proof.

        Args:
            prover_did: The prover's DID
            statement: The statement being proved
            secret_data: The secret data (simulated)

        Returns:
            ZKProof object
        """
        proof_id = f"zkp_{hashlib.sha256(f'{prover_did}:{statement}:{secrets.token_hex(4)}'.encode()).hexdigest()[:16]}"

        proof = ZKProof(
            proof_id=proof_id,
            prover_did=prover_did,
            statement=statement,
            created=datetime.utcnow().isoformat(),
            verified=True,
        )
        self._zk_proofs[proof_id] = proof
        self._log_ledger("create_zk_proof", {
            "proof_id": proof_id,
            "prover": prover_did,
            "statement": statement,
        })
        return proof

    def verify_zk_proof(self, proof_id: str) -> bool:
        """Verify a zero-knowledge proof.

        Args:
            proof_id: The proof ID to verify

        Returns:
            True if valid, False otherwise
        """
        proof = self._zk_proofs.get(proof_id)
        if not proof:
            return False
        return proof.verified

    def get_stats(self) -> Dict[str, Any]:
        """Get blockchain identity statistics."""
        # Count credentials by type
        by_type: Dict[str, int] = {}
        for vc in self._credentials.values():
            t = vc.credential_type.value
            by_type[t] = by_type.get(t, 0) + 1

        # Count DIDs by network
        by_network: Dict[str, int] = {}
        for doc in self._dids.values():
            n = doc.network.value
            by_network[n] = by_network.get(n, 0) + 1

        active_creds = sum(1 for vc in self._credentials.values() if vc.valid and not vc.revoked)
        revoked_creds = sum(1 for vc in self._credentials.values() if vc.revoked)

        return {
            "dids": {
                "total": len(self._dids),
                "active": sum(1 for d in self._dids.values() if d.status == "active"),
                "by_network": by_network,
            },
            "credentials": {
                "total": len(self._credentials),
                "active": active_creds,
                "revoked": revoked_creds,
                "by_type": by_type,
            },
            "attestations": len(self._credentials),
            "sbts": len(self._sbts),
            "zk_proofs": {
                "total": len(self._zk_proofs),
                "verified": sum(1 for p in self._zk_proofs.values() if p.verified),
            },
            "ledger_entries": len(self._ledger),
        }


# ── Singleton ───────────────────────────────────────────────────────────────

_instance: Optional[BlockchainIdentityAdvanced] = None


def get_blockchain_identity_advanced() -> BlockchainIdentityAdvanced:
    """Return the singleton BlockchainIdentityAdvanced instance."""
    global _instance
    if _instance is None:
        _instance = BlockchainIdentityAdvanced()
    return _instance
