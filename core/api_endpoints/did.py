from typing import Dict, Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_did = None
def _get_did():
    global _did
    if _did is None:
        try:
            from core.identity.did_system import get_did_system, DIDMethod
            _did = get_did_system()
            logger.info("DIDSystem loaded")
        except Exception as e:
            logger.warning(f"DIDSystem unavailable: {e}")
    return _did


class DIDCreateRequest(BaseModel):
    subject_id: str
    subject_type: str = "user"
    method: str = "asim"
    tags: Dict[str, str] = Field(default_factory=dict)


@router.get("/api/did/stats")
async def did_stats():
    """Get DID system statistics."""
    ds = _get_did()
    if not ds:
        raise HTTPException(status_code=503, detail="DIDSystem not available")
    return ds.stats()


@router.post("/api/did/create")
async def did_create(req: DIDCreateRequest):
    """Create a new DID."""
    ds = _get_did()
    if not ds:
        raise HTTPException(status_code=503, detail="DIDSystem not available")

    try:
        from core.identity.did_system import DIDMethod
        method_map = {e.value: e for e in DIDMethod}
        method = method_map.get(req.method, DIDMethod.ASIM)

        record = ds.create_did(req.subject_id, req.subject_type, method, req.tags)
        logger.info(f"DID created: {record.did} for {req.subject_id}")
        return {
            "success": True,
            "did": record.did,
            "method": record.method.value,
            "status": record.status.value,
        }
    except Exception as e:
        logger.error(f"DID creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/did/resolve/{did}")
async def did_resolve(did: str):
    """Resolve a DID to its document."""
    ds = _get_did()
    if not ds:
        raise HTTPException(status_code=503, detail="DIDSystem not available")

    doc = ds.resolve(did)
    if not doc:
        raise HTTPException(status_code=404, detail=f"DID {did} not found or revoked")
    return {"did": did, "document": doc.to_dict()}


@router.get("/api/did/list")
async def did_list(
    subject_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """List DIDs with optional subject_type filter."""
    ds = _get_did()
    if not ds:
        raise HTTPException(status_code=503, detail="DIDSystem not available")

    records = ds.list_dids(subject_type=subject_type, limit=limit)
    return {
        "total": len(records),
        "dids": [r.to_dict() for r in records],
    }
