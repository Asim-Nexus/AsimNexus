"""
Escrow API Routes
=================
FastAPI router for escrow endpoints (/api/economy/escrow/*).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/economy/escrow", tags=["economy-escrow"])

# Module-level singleton reference (reset by test fixture)
_escrow = None


def _get_escrow():
    global _escrow
    if _escrow is None:
        from core.economy.escrow import get_escrow_engine
        _escrow = get_escrow_engine()
    return _escrow


@router.get("/stats")
async def escrow_stats():
    """Get escrow system statistics."""
    engine = _get_escrow()
    stats = await engine.get_stats()
    return stats


@router.get("/user/{user_id}")
async def get_escrows_for_user(user_id: str):
    """Get escrows for a user."""
    engine = _get_escrow()
    escrows = await engine.get_escrows_for_user(user_id=user_id)
    return {
        "escrows": [
            {
                "escrow_id": e.escrow_id,
                "buyer_id": e.buyer_id,
                "seller_id": e.seller_id,
                "amount": e.amount,
                "token_type": e.token_type,
                "status": e.status,
                "created_at": e.created_at,
            }
            for e in escrows
        ]
    }


@router.post("/create")
async def create_escrow(data: dict):
    """Create a new escrow transaction."""
    engine = _get_escrow()
    buyer_id = data.get("buyer_id")
    seller_id = data.get("seller_id")
    amount = data.get("amount", 0.0)
    token_type = data.get("token_type", "nexus")
    timeout_hours = data.get("timeout_hours", 48)
    if not buyer_id or not seller_id:
        raise HTTPException(status_code=400, detail="buyer_id and seller_id are required")
    try:
        escrow = await engine.create_escrow(
            buyer_id=buyer_id,
            seller_id=seller_id,
            amount=float(amount),
            token_type=token_type,
            timeout_hours=int(timeout_hours),
        )
        return {"success": True, "escrow_id": escrow.escrow_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fund")
async def fund_escrow(data: dict):
    """Fund an escrow transaction."""
    engine = _get_escrow()
    escrow_id = data.get("escrow_id")
    if not escrow_id:
        raise HTTPException(status_code=400, detail="escrow_id is required")
    success, msg = await engine.fund_escrow(escrow_id=escrow_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}


@router.post("/release")
async def release_escrow(data: dict):
    """Release funds to seller."""
    engine = _get_escrow()
    escrow_id = data.get("escrow_id")
    if not escrow_id:
        raise HTTPException(status_code=400, detail="escrow_id is required")
    success, release_id = await engine.release_to_seller(escrow_id=escrow_id)
    if not success:
        raise HTTPException(status_code=400, detail=release_id)
    return {"success": True, "release_id": release_id}


@router.post("/refund")
async def refund_escrow(data: dict):
    """Refund funds to buyer."""
    engine = _get_escrow()
    escrow_id = data.get("escrow_id")
    partial_amount = data.get("partial_amount")
    reason = data.get("reason", "")
    if not escrow_id:
        raise HTTPException(status_code=400, detail="escrow_id is required")
    success, msg = await engine.refund_to_buyer(
        escrow_id=escrow_id,
        partial_amount=float(partial_amount) if partial_amount is not None else None,
        reason=reason,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}


@router.post("/dispute")
async def raise_dispute(data: dict):
    """Raise a dispute on an escrow."""
    engine = _get_escrow()
    escrow_id = data.get("escrow_id")
    raised_by = data.get("raised_by")
    reason = data.get("reason", "other")
    description = data.get("description", "")
    if not escrow_id or not raised_by:
        raise HTTPException(status_code=400, detail="escrow_id and raised_by are required")
    success, dispute_id = await engine.raise_dispute(
        escrow_id=escrow_id,
        raised_by=raised_by,
        reason=reason,
        description=description,
    )
    if not success:
        raise HTTPException(status_code=400, detail=dispute_id)
    return {"success": True, "dispute_id": dispute_id}


@router.post("/dispute/resolve")
async def resolve_dispute(data: dict):
    """Resolve a dispute on an escrow."""
    engine = _get_escrow()
    escrow_id = data.get("escrow_id")
    resolved_by = data.get("resolved_by")
    resolution = data.get("resolution", "release")
    release_to_seller = data.get("release_to_seller", True)
    if not escrow_id or not resolved_by:
        raise HTTPException(status_code=400, detail="escrow_id and resolved_by are required")
    # Find the dispute_id for this escrow
    disputes = await engine.get_escrow_disputes(escrow_id=escrow_id)
    if not disputes:
        raise HTTPException(status_code=404, detail="No disputes found for this escrow")
    dispute_id = disputes[0].dispute_id
    success, msg = await engine.resolve_dispute(
        dispute_id=dispute_id,
        resolution=resolution,
        resolved_by=resolved_by,
        release_to_seller=release_to_seller,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}
