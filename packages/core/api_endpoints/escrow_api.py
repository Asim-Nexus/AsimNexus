"""
EscrowEngine REST API endpoints for ASIMNEXUS.

Provides REST API access to EscrowEngine operations including:
escrow creation, funding, release, refund, dispute management, and statistics.
"""

from typing import Optional
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_escrow = None

def _get_escrow():
    global _escrow
    if _escrow is None:
        try:
            from economy.escrow import get_escrow_engine
            _escrow = get_escrow_engine()
            logger.info("EscrowEngine loaded")
        except Exception as e:
            logger.warning(f"EscrowEngine unavailable: {e}")
    return _escrow


# ─── Request Models ───────────────────────────────────────────────────────────


class CreateEscrowRequest(BaseModel):
    buyer_id: str = Field(..., min_length=1)
    seller_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    token_type: str = "nexus"
    fee_percent: float = Field(default=0.0, ge=0, le=100)
    metadata: dict = Field(default_factory=dict)


class FundEscrowRequest(BaseModel):
    escrow_id: str


class ReleaseRequest(BaseModel):
    escrow_id: str


class RefundRequest(BaseModel):
    escrow_id: str
    reason: str = ""


class RaiseDisputeRequest(BaseModel):
    escrow_id: str
    raised_by: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    description: str = ""


class ResolveDisputeRequest(BaseModel):
    escrow_id: str
    resolution: str = Field(..., pattern="^(release|refund)$")
    resolved_by: str = Field(..., min_length=1)
    notes: str = ""


# ─── Endpoints ────────────────────────────────────────────────────────────────

# NOTE: Route ordering matters — static paths like /stats MUST come before
# path-parameterised routes like /{escrow_id}.


@router.post("/api/economy/escrow/create", tags=["Economy Escrow"])
async def create_escrow(req: CreateEscrowRequest):
    """Create a new escrow transaction."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    try:
        escrow = await e.create_escrow(
            buyer_id=req.buyer_id,
            seller_id=req.seller_id,
            amount=req.amount,
            token_type=req.token_type,
            fee=req.fee_percent,
            metadata=req.metadata,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    return {"success": True, "escrow_id": escrow.escrow_id, "escrow": escrow.to_dict()}


@router.get("/api/economy/escrow/stats", tags=["Economy Escrow"])
async def escrow_stats():
    """Get escrow engine statistics."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    return await e.get_stats()


@router.get("/api/economy/escrow/{escrow_id}", tags=["Economy Escrow"])
async def get_escrow(escrow_id: str):
    """Get escrow details by ID."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    escrow = await e.get_escrow(escrow_id)
    if not escrow:
        raise HTTPException(status_code=404, detail=f"Escrow {escrow_id} not found")
    return escrow.to_dict()


@router.post("/api/economy/escrow/fund", tags=["Economy Escrow"])
async def fund_escrow(req: FundEscrowRequest):
    """Fund an escrow (buyer deposits)."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    result = await e.fund_escrow(req.escrow_id)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    escrow = await e.get_escrow(req.escrow_id)
    # escrow.status is a str (dataclass field), not an Enum — no .value needed
    return {"success": True, "escrow_id": req.escrow_id, "status": escrow.status if escrow else "unknown"}


@router.post("/api/economy/escrow/release", tags=["Economy Escrow"])
async def release_to_seller(req: ReleaseRequest):
    """Release escrow funds to seller."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    result = await e.release_to_seller(req.escrow_id)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "escrow_id": req.escrow_id, "message": result[1]}


@router.post("/api/economy/escrow/refund", tags=["Economy Escrow"])
async def refund_to_buyer(req: RefundRequest):
    """Refund escrow funds to buyer."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    result = await e.refund_to_buyer(req.escrow_id, reason=req.reason)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "escrow_id": req.escrow_id, "message": result[1]}


@router.post("/api/economy/escrow/dispute", tags=["Economy Escrow"])
async def raise_dispute(req: RaiseDisputeRequest):
    """Raise a dispute on an escrow."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    result = await e.raise_dispute(
        req.escrow_id,
        raised_by=req.raised_by,
        reason=req.reason,
        description=req.description,
    )
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "escrow_id": req.escrow_id, "dispute_id": result[1]}


@router.post("/api/economy/escrow/dispute/resolve", tags=["Economy Escrow"])
async def resolve_dispute(req: ResolveDisputeRequest):
    """Resolve a dispute on an escrow."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    # Engine's resolve_dispute expects dispute_id (first param), not escrow_id.
    # Look up the open dispute for this escrow.
    disputes = await e.get_escrow_disputes(req.escrow_id)
    open_disputes = [d for d in disputes if d.status == "open"]
    if not open_disputes:
        raise HTTPException(status_code=404, detail=f"No open dispute found for escrow {req.escrow_id}")
    dispute_id = open_disputes[0].dispute_id
    result = await e.resolve_dispute(
        dispute_id,
        resolution=req.resolution,
        resolved_by=req.resolved_by,
        release_to_seller=(req.resolution == "release"),
    )
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "escrow_id": req.escrow_id, "resolution": req.resolution}


@router.get("/api/economy/escrow/user/{user_id}", tags=["Economy Escrow"])
async def get_escrows_for_user(user_id: str):
    """Get all escrows where the user is buyer or seller."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    # Engine returns escrows where user is buyer OR seller; no role/status filter needed.
    escrows = await e.get_escrows_for_user(user_id)
    return {"user_id": user_id, "escrows": [esc.to_dict() for esc in escrows], "count": len(escrows)}


@router.get("/api/economy/escrow/{escrow_id}/disputes", tags=["Economy Escrow"])
async def get_escrow_disputes(escrow_id: str):
    """Get all disputes for an escrow."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    disputes = await e.get_escrow_disputes(escrow_id)
    return {"escrow_id": escrow_id, "disputes": [d.to_dict() for d in disputes], "count": len(disputes)}


@router.post("/api/economy/escrow/check-expired", tags=["Economy Escrow"])
async def check_expired_escrows():
    """Check and process expired escrows."""
    e = _get_escrow()
    if not e:
        raise HTTPException(status_code=503, detail="EscrowEngine not available")
    expired = await e.check_expired()
    return {"expired_count": len(expired), "expired_ids": expired}
