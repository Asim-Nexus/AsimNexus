"""
Token API Routes
================
FastAPI router for token endpoints (/api/economy/tokens/*).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/economy/tokens", tags=["economy-tokens"])

# Module-level singleton reference (reset by test fixture)
_registry = None


def _get_registry():
    global _registry
    if _registry is None:
        from core.economy.tokens import get_token_registry
        _registry = get_token_registry()
    return _registry


# ── Static routes first (before /{token_id}) ────────────────────────────── #


@router.get("/stats")
async def token_stats():
    """Get token registry statistics."""
    registry = _get_registry()
    stats = await registry.get_stats()
    return stats


@router.get("/holdings/{owner_id}")
async def owner_holdings(owner_id: str):
    """Get token holdings for an owner."""
    registry = _get_registry()
    holdings = await registry.get_owner_holdings(owner_id=owner_id)
    return {
        "holdings": [
            {
                "token_id": h.token_id,
                "owner_id": h.holder_id,
                "balance": h.amount,
                "locked_amount": h.locked_amount,
                "available": h.available,
            }
            for h in holdings
        ]
    }


@router.post("/register")
async def register_token(data: dict):
    """Register a new token."""
    registry = _get_registry()
    name = data.get("name")
    symbol = data.get("symbol")
    decimals = data.get("decimals", 18)
    standard = data.get("standard", "nexus")
    is_soul_bound = data.get("is_soul_bound", False)
    if not name or not symbol:
        raise HTTPException(status_code=400, detail="name and symbol are required")
    try:
        token = await registry.register_token(
            name=name,
            symbol=symbol,
            standard=standard,
            decimals=int(decimals),
            is_soul_bound=is_soul_bound,
        )
        return {"success": True, "token_id": token.token_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_tokens(standard: Optional[str] = None):
    """List all registered tokens."""
    registry = _get_registry()
    tokens = await registry.list_tokens(standard=standard)
    return {
        "tokens": [
            {
                "token_id": t.token_id,
                "standard": t.standard,
                "name": t.name,
                "symbol": t.symbol,
                "total_supply": t.total_supply,
                "circulating_supply": t.circulating_supply,
                "decimals": t.decimals,
                "status": t.status,
            }
            for t in tokens
        ],
        "count": len(tokens),
    }


# ── Dynamic routes (with path params) ──────────────────────────────────── #


@router.get("/{token_id}")
async def get_token(token_id: str):
    """Get token by ID."""
    registry = _get_registry()
    token = await registry.get_token(token_id)
    if token is None:
        raise HTTPException(status_code=404, detail="Token not found")
    return {
        "token_id": token.token_id,
        "standard": token.standard,
        "name": token.name,
        "symbol": token.symbol,
        "total_supply": token.total_supply,
        "circulating_supply": token.circulating_supply,
        "decimals": token.decimals,
        "is_transferable": token.is_transferable,
        "is_soul_bound": token.is_soul_bound,
        "status": token.status,
    }


@router.post("/{token_id}/mint")
async def mint_tokens(token_id: str, data: dict):
    """Mint tokens to an owner."""
    registry = _get_registry()
    recipient = data.get("recipient") or data.get("to_owner_id")
    amount = data.get("amount", 0.0)
    if not recipient:
        raise HTTPException(status_code=400, detail="recipient is required")
    success, msg = await registry.mint(token_id=token_id, recipient=recipient, amount=float(amount))
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "event_id": msg}


@router.post("/{token_id}/burn")
async def burn_tokens(token_id: str, data: dict):
    """Burn tokens from an owner."""
    registry = _get_registry()
    holder = data.get("holder") or data.get("from_owner_id")
    amount = data.get("amount", 0.0)
    if not holder:
        raise HTTPException(status_code=400, detail="holder is required")
    success, msg = await registry.burn(holder=holder, token_id=token_id, amount=float(amount))
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "event_id": msg}


@router.post("/{token_id}/lock")
async def lock_tokens(token_id: str, data: dict):
    """Lock tokens for an owner."""
    registry = _get_registry()
    holder_id = data.get("holder_id") or data.get("owner_id")
    amount = data.get("amount", 0.0)
    if not holder_id:
        raise HTTPException(status_code=400, detail="holder_id is required")
    success, msg = await registry.lock_tokens(token_id=token_id, holder_id=holder_id, amount=float(amount))
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}


@router.post("/{token_id}/unlock")
async def unlock_tokens(token_id: str, data: dict):
    """Unlock tokens for an owner."""
    registry = _get_registry()
    holder_id = data.get("holder_id") or data.get("owner_id")
    amount = data.get("amount", 0.0)
    if not holder_id:
        raise HTTPException(status_code=400, detail="holder_id is required")
    success, msg = await registry.unlock_tokens(token_id=token_id, holder_id=holder_id, amount=float(amount))
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}
