"""
TokenRegistry REST API endpoints for ASIMNEXUS.

Provides REST API access to TokenRegistry operations including:
token registration, minting, burning, locking, holdings, and statistics.
"""

from typing import Optional, List
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_registry = None

def _get_registry():
    global _registry
    if _registry is None:
        try:
            from economy.tokens import get_token_registry
            _registry = get_token_registry()
            logger.info("TokenRegistry loaded")
        except Exception as e:
            logger.warning(f"TokenRegistry unavailable: {e}")
    return _registry


# ─── Request Models ───────────────────────────────────────────────────────────


class RegisterTokenRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=1, max_length=20)
    standard: str = Field("NEXUS", pattern="^(NEXUS|SVT|HDT|NFT)$")
    total_supply: float = Field(default=0, ge=0)
    owner_id: str = Field("", min_length=0)
    is_soul_bound: bool = False
    metadata: dict = Field(default_factory=dict)


class MintRequest(BaseModel):
    token_id: str = ""
    to_owner_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)


class BurnRequest(BaseModel):
    token_id: str = ""
    from_owner_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)


class LockRequest(BaseModel):
    token_id: str = ""
    owner_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)


class UnlockRequest(BaseModel):
    token_id: str = ""
    owner_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/api/economy/tokens/register", tags=["Economy Tokens"])
async def register_token(req: RegisterTokenRequest):
    """Register a new token definition."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    token = await r.register_token(
        name=req.name,
        symbol=req.symbol,
        standard=req.standard,
        total_supply=req.total_supply,
        is_soul_bound=req.is_soul_bound,
        metadata=req.metadata,
    )
    return {"success": True, "token_id": token.token_id, "token": token.to_dict()}


@router.get("/api/economy/tokens/stats", tags=["Economy Tokens"])
async def token_stats():
    """Get token registry statistics."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    return await r.get_stats()


@router.get("/api/economy/tokens/{token_id}", tags=["Economy Tokens"])
async def get_token(token_id: str):
    """Get token definition by ID."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    token = await r.get_token(token_id)
    if not token:
        raise HTTPException(status_code=404, detail=f"Token {token_id} not found")
    return token.to_dict()


@router.get("/api/economy/tokens/by-symbol/{symbol}", tags=["Economy Tokens"])
async def get_token_by_symbol(symbol: str):
    """Get token definition by symbol."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    token = await r.get_token_by_symbol(symbol)
    if not token:
        raise HTTPException(status_code=404, detail=f"Token with symbol {symbol} not found")
    return token.to_dict()


@router.get("/api/economy/tokens", tags=["Economy Tokens"])
async def list_tokens(standard: Optional[str] = Query(None)):
    """List all registered tokens, optionally filtered by standard."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    tokens = await r.list_tokens(standard=standard)
    return {"tokens": [t.to_dict() for t in tokens], "count": len(tokens)}


@router.post("/api/economy/tokens/mint", tags=["Economy Tokens"])
async def mint(req: MintRequest):
    """Mint new tokens to an owner."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    result = await r.mint(req.token_id, req.amount, req.to_owner_id)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "token_id": req.token_id, "owner_id": req.to_owner_id, "amount": req.amount}


@router.post("/api/economy/tokens/{token_id}/mint", tags=["Economy Tokens"])
async def mint_token(token_id: str, req: MintRequest):
    """Mint tokens to an owner (token_id from path, overrides body)."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    result = await r.mint(token_id, req.amount, req.to_owner_id)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "token_id": token_id, "owner_id": req.to_owner_id, "amount": req.amount}


@router.post("/api/economy/tokens/burn", tags=["Economy Tokens"])
async def burn(req: BurnRequest):
    """Burn tokens from an owner."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    result = await r.burn(req.from_owner_id, req.token_id, req.amount)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "token_id": req.token_id, "owner_id": req.from_owner_id, "amount": req.amount}


@router.post("/api/economy/tokens/{token_id}/burn", tags=["Economy Tokens"])
async def burn_token(token_id: str, req: BurnRequest):
    """Burn tokens from an owner (token_id from path, overrides body)."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    result = await r.burn(req.from_owner_id, token_id, req.amount)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "token_id": token_id, "owner_id": req.from_owner_id, "amount": req.amount}


@router.get("/api/economy/tokens/holdings/{owner_id}", tags=["Economy Tokens"])
async def get_owner_holdings(owner_id: str):
    """Get all token holdings for an owner."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    holdings = await r.get_owner_holdings(owner_id)
    return {"owner_id": owner_id, "holdings": [h.to_dict() for h in holdings], "count": len(holdings)}


@router.get("/api/economy/tokens/holdings/{owner_id}/{token_id}", tags=["Economy Tokens"])
async def get_holding(owner_id: str, token_id: str):
    """Get a specific holding for an owner and token."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    holding = await r.get_holding(owner_id, token_id)
    if not holding:
        raise HTTPException(status_code=404, detail=f"Holding not found for owner {owner_id}, token {token_id}")
    return holding.to_dict()


@router.get("/api/economy/tokens/balance/{owner_id}/{token_id}", tags=["Economy Tokens"])
async def get_owner_balance(owner_id: str, token_id: str):
    """Get balance of a specific token for an owner."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    balance = await r.get_owner_balance(owner_id, token_id)
    return {"owner_id": owner_id, "token_id": token_id, "balance": balance}


@router.post("/api/economy/tokens/lock", tags=["Economy Tokens"])
async def lock_tokens(req: LockRequest):
    """Lock tokens (e.g., for staking)."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    result = await r.lock_tokens(req.owner_id, req.token_id, req.amount)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "token_id": req.token_id, "owner_id": req.owner_id, "locked_amount": req.amount}


@router.post("/api/economy/tokens/{token_id}/lock", tags=["Economy Tokens"])
async def lock_tokens_path(token_id: str, req: LockRequest):
    """Lock tokens (token_id from path, overrides body)."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    result = await r.lock_tokens(req.owner_id, token_id, req.amount)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "token_id": token_id, "owner_id": req.owner_id, "locked_amount": req.amount}


@router.post("/api/economy/tokens/unlock", tags=["Economy Tokens"])
async def unlock_tokens(req: UnlockRequest):
    """Unlock previously locked tokens."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    result = await r.unlock_tokens(req.owner_id, req.token_id, req.amount)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "token_id": req.token_id, "owner_id": req.owner_id, "unlocked_amount": req.amount}


@router.post("/api/economy/tokens/{token_id}/unlock", tags=["Economy Tokens"])
async def unlock_tokens_path(token_id: str, req: UnlockRequest):
    """Unlock tokens (token_id from path, overrides body)."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    result = await r.unlock_tokens(req.owner_id, token_id, req.amount)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "token_id": token_id, "owner_id": req.owner_id, "unlocked_amount": req.amount}


@router.post("/api/economy/tokens/initialize-defaults", tags=["Economy Tokens"])
async def initialize_default_tokens():
    """Initialize default system tokens (NEXUS, SVT, HDT)."""
    r = _get_registry()
    if not r:
        raise HTTPException(status_code=503, detail="TokenRegistry not available")
    from economy.tokens import initialize_default_tokens as init_defaults
    await init_defaults(r)
    return {"success": True, "message": "Default tokens initialized"}
