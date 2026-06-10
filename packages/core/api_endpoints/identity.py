from typing import Dict, Any, Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_identity = None
def _get_identity():
    global _identity
    if _identity is None:
        try:
            from core.identity.user_identity import get_identity_system, VerificationMethod, IdentityStatus, IdentityLevel
            _identity = get_identity_system()
            logger.info("UserIdentitySystem loaded")
        except Exception as e:
            logger.warning(f"UserIdentitySystem unavailable: {e}")
    return _identity


class IdentityCreateRequest(BaseModel):
    user_id: str
    display_name: str
    email: str
    attributes: Dict[str, Any] = Field(default_factory=dict)

class IdentityVerifyEmailRequest(BaseModel):
    identity_id: str
    code: str

class IssueCredentialRequest(BaseModel):
    identity_id: str
    issuer: str
    cred_type: str
    claims: Dict[str, Any]
    expiry_days: Optional[int] = None


@router.get("/api/identity/stats")
async def identity_stats():
    """Get identity system statistics."""
    ids = _get_identity()
    if not ids:
        raise HTTPException(status_code=503, detail="IdentitySystem not available")
    return ids.stats()


@router.get("/api/identity/list")
async def identity_list(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """List identities with optional status filter."""
    ids = _get_identity()
    if not ids:
        raise HTTPException(status_code=503, detail="IdentitySystem not available")

    status_enum = None
    if status:
        from core.identity.user_identity import IdentityStatus
        status_map = {e.value: e for e in IdentityStatus}
        status_enum = status_map.get(status)
        if not status_enum:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    results = ids.list_identities(status=status_enum, limit=limit)
    return {
        "total": len(results),
        "identities": [r.to_dict() for r in results],
    }


@router.post("/api/identity/create")
async def identity_create(req: IdentityCreateRequest):
    """Create a new identity."""
    ids = _get_identity()
    if not ids:
        raise HTTPException(status_code=503, detail="IdentitySystem not available")

    try:
        record = ids.create_identity(
            req.user_id, req.display_name, req.email, req.attributes
        )
        logger.info(f"Identity created: {record.identity_id} for {req.user_id}")
        return {
            "success": True,
            "identity_id": record.identity_id,
            "did": record.did,
            "status": record.status.value,
        }
    except Exception as e:
        logger.error(f"Identity creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/identity/{identity_id}")
async def identity_get(identity_id: str):
    """Get identity by ID."""
    ids = _get_identity()
    if not ids:
        raise HTTPException(status_code=503, detail="IdentitySystem not available")

    record = ids.get_identity(identity_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")
    return record.to_dict()


@router.post("/api/identity/{identity_id}/activate")
async def identity_activate(identity_id: str):
    """Activate a pending identity."""
    ids = _get_identity()
    if not ids:
        raise HTTPException(status_code=503, detail="IdentitySystem not available")

    ok = ids.activate_identity(identity_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to activate identity")
    return {"success": True, "status": "active"}


@router.post("/api/identity/{identity_id}/verify-email")
async def identity_verify_email(identity_id: str, req: IdentityVerifyEmailRequest):
    """Verify identity email with code."""
    ids = _get_identity()
    if not ids:
        raise HTTPException(status_code=503, detail="IdentitySystem not available")

    from core.identity.user_identity import VerificationMethod
    success, msg = ids.verify_identity(
        identity_id, VerificationMethod.EMAIL, {"code": req.code}
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}


@router.post("/api/identity/{identity_id}/initiate-email-verification")
async def identity_initiate_email(identity_id: str):
    """Initiate email verification and get code."""
    ids = _get_identity()
    if not ids:
        raise HTTPException(status_code=503, detail="IdentitySystem not available")

    code = ids.initiate_email_verification(identity_id)
    if not code:
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")
    return {"success": True, "code": code}


@router.post("/api/identity/{identity_id}/issue-credential")
async def identity_issue_credential(identity_id: str, req: IssueCredentialRequest):
    """Issue a verifiable credential to an identity."""
    ids = _get_identity()
    if not ids:
        raise HTTPException(status_code=503, detail="IdentitySystem not available")

    cred = ids.issue_credential(
        identity_id, req.issuer, req.cred_type, req.claims, req.expiry_days
    )
    if not cred:
        raise HTTPException(status_code=404, detail=f"Identity {identity_id} not found")
    return {
        "success": True,
        "credential_id": cred.credential_id,
        "type": cred.type,
        "valid": cred.is_valid(),
    }
