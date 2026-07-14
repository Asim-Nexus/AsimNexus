"""
Blockchain Identity API — DID, Verifiable Credentials, and Soulbound Tokens.
=============================================================================
Exposes BlockchainIdentityAdvanced from core/blockchain_identity_advanced.py
for decentralized identity management.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Body, Query

from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.BlockchainIdentity")

router = APIRouter(tags=["Blockchain Identity"])

# ── Singleton ────────────────────────────────────────────────────────────────

_bc_identity = None


def init_blockchain_identity(app_globals: dict) -> None:
    """Initialize blockchain identity module with shared state."""
    global _bc_identity
    try:
        from core.blockchain_identity_advanced import get_blockchain_identity_advanced
        _bc_identity = get_blockchain_identity_advanced()
        logger.info("BlockchainIdentityAdvanced instance created")
    except Exception as e:
        logger.warning(f"BlockchainIdentityAdvanced not available: {e}")
        _bc_identity = None


def _get_identity():
    """Get the BlockchainIdentityAdvanced singleton."""
    global _bc_identity
    if _bc_identity is None:
        try:
            from core.blockchain_identity_advanced import get_blockchain_identity_advanced
            _bc_identity = get_blockchain_identity_advanced()
        except Exception as e:
            logger.error(f"Cannot get BlockchainIdentityAdvanced: {e}")
    return _bc_identity


# ═══════════════════════════════════════════════════════════════════════════════
# DID (Decentralized Identifier) Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/blockchain/did")
async def bc_create_did(data: dict = Body(...)):
    """Create a new Decentralized Identifier (DID)."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        from core.blockchain_identity_advanced import BlockchainNetwork
        public_key = data.get("public_key", "")
        network_str = data.get("network", "asim_chain")
        network = BlockchainNetwork(network_str)

        did = identity.create_did(public_key, network)
        return ok(data={"did": did, "network": network_str, "public_key": public_key})
    except Exception as e:
        logger.error(f"bc_create_did error: {e}")
        return error(str(e))


@router.get("/api/blockchain/did/{did}")
async def bc_get_did(did: str):
    """Get a DID document."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        doc = identity.get_did(did)
        if doc:
            return ok(data=doc)
        return error(f"DID '{did}' not found")
    except Exception as e:
        logger.error(f"bc_get_did error: {e}")
        return error(str(e))


@router.get("/api/blockchain/dids")
async def bc_list_dids():
    """List all DIDs."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        stats = identity.get_stats()
        dids_data = stats.get("dids", {})
        return ok(data=dids_data)
    except Exception as e:
        logger.error(f"bc_list_dids error: {e}")
        return error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Verifiable Credential Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/blockchain/credentials")
async def bc_issue_credential(data: dict = Body(...)):
    """Issue a verifiable credential."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        from core.blockchain_identity_advanced import AttestationType
        issuer_did = data.get("issuer_did", "")
        subject_did = data.get("subject_did", "")
        credential_type_str = data.get("credential_type", "identity")
        credential_type = AttestationType(credential_type_str)
        claims = data.get("claims", {})
        expiration_days = data.get("expiration_days", 365)

        vc_id = identity.issue_credential(
            issuer_did=issuer_did,
            subject_did=subject_did,
            credential_type=credential_type,
            claims=claims,
            expiration_days=expiration_days,
        )
        return ok(data={
            "vc_id": vc_id,
            "issuer_did": issuer_did,
            "subject_did": subject_did,
            "credential_type": credential_type_str,
        })
    except Exception as e:
        logger.error(f"bc_issue_credential error: {e}")
        return error(str(e))


@router.get("/api/blockchain/credentials/{vc_id}")
async def bc_get_credential(vc_id: str):
    """Get and verify a verifiable credential."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        result = identity.verify_credential(vc_id)
        return ok(data=result)
    except Exception as e:
        logger.error(f"bc_get_credential error: {e}")
        return error(str(e))


@router.get("/api/blockchain/credentials")
async def bc_list_credentials(subject_did: str = Query(""), credential_type: str = Query("")):
    """List credentials for a subject, optionally filtered by type."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        if not subject_did:
            # Return stats if no subject filter
            stats = identity.get_stats()
            return ok(data=stats.get("credentials", {}))

        from core.blockchain_identity_advanced import AttestationType
        vc_type = AttestationType(credential_type) if credential_type else None
        creds = identity.get_credentials_for_subject(subject_did, vc_type)
        return ok(data={
            "subject_did": subject_did,
            "count": len(creds),
            "credentials": [
                {
                    "vc_id": c.vc_id,
                    "issuer_did": c.issuer_did,
                    "credential_type": c.credential_type.value,
                    "claims": c.claims,
                    "issued": c.issued,
                    "expires": c.expires,
                    "valid": c.valid and not c.revoked,
                }
                for c in creds
            ],
        })
    except Exception as e:
        logger.error(f"bc_list_credentials error: {e}")
        return error(str(e))


@router.post("/api/blockchain/credentials/{vc_id}/revoke")
async def bc_revoke_credential(vc_id: str, data: dict = Body(...)):
    """Revoke a verifiable credential."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        reason = data.get("reason", "")
        result = identity.revoke_credential(vc_id, reason)
        if result:
            return ok(data={"vc_id": vc_id, "revoked": True, "reason": reason})
        return error(f"Credential '{vc_id}' not found")
    except Exception as e:
        logger.error(f"bc_revoke_credential error: {e}")
        return error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Soulbound Token Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/blockchain/sbt")
async def bc_issue_sbt(data: dict = Body(...)):
    """Issue a non-transferable soulbound token."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        from core.blockchain_identity_advanced import BlockchainNetwork
        owner_did = data.get("owner_did", "")
        token_type = data.get("token_type", "identity")
        metadata = data.get("metadata", {})
        issuer = data.get("issuer", "")
        network_str = data.get("network", "asim_chain")
        network = BlockchainNetwork(network_str)

        sbt_id = identity.issue_soulbound_token(
            owner_did=owner_did,
            token_type=token_type,
            metadata=metadata,
            issuer=issuer,
            network=network,
        )
        return ok(data={
            "sbt_id": sbt_id,
            "owner_did": owner_did,
            "token_type": token_type,
            "network": network_str,
        })
    except Exception as e:
        logger.error(f"bc_issue_sbt error: {e}")
        return error(str(e))


@router.get("/api/blockchain/sbt")
async def bc_list_sbts(owner_did: str = Query("")):
    """List soulbound tokens for an owner."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        if not owner_did:
            stats = identity.get_stats()
            return ok(data={"total_sbts": stats.get("sbts", 0)})

        sbts = identity.get_sbts_for_owner(owner_did)
        return ok(data={
            "owner_did": owner_did,
            "count": len(sbts),
            "tokens": [
                {
                    "sbt_id": s.sbt_id,
                    "token_type": s.token_type,
                    "metadata": s.metadata,
                    "issuer": s.issuer,
                    "network": s.network.value,
                    "issued": s.issued,
                }
                for s in sbts
            ],
        })
    except Exception as e:
        logger.error(f"bc_list_sbts error: {e}")
        return error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Zero-Knowledge Proof Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/blockchain/zkp")
async def bc_create_zkp(data: dict = Body(...)):
    """Create a zero-knowledge proof."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        prover_did = data.get("prover_did", "")
        statement = data.get("statement", "")
        secret_data = data.get("secret_data", "")

        proof = identity.create_zk_proof(prover_did, statement, secret_data)
        return ok(data={
            "proof_id": proof.proof_id,
            "prover_did": proof.prover_did,
            "statement": proof.statement,
            "created": proof.created,
            "verified": proof.verified,
        })
    except Exception as e:
        logger.error(f"bc_create_zkp error: {e}")
        return error(str(e))


@router.get("/api/blockchain/zkp/{proof_id}")
async def bc_verify_zkp(proof_id: str):
    """Verify a zero-knowledge proof."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        valid = identity.verify_zk_proof(proof_id)
        return ok(data={"proof_id": proof_id, "valid": valid})
    except Exception as e:
        logger.error(f"bc_verify_zkp error: {e}")
        return error(str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Statistics
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/blockchain/stats")
async def bc_stats():
    """Get blockchain identity statistics."""
    try:
        identity = _get_identity()
        if not identity:
            return error("Blockchain identity module not available")

        stats = identity.get_stats()
        return ok(data=stats)
    except Exception as e:
        logger.error(f"bc_stats error: {e}")
        return error(str(e))
