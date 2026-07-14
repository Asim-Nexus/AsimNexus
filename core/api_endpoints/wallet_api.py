"""
Wallet API Routes
=================
FastAPI router for wallet endpoints (/api/economy/wallet/*).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/economy/wallet", tags=["economy-wallet"])

# Module-level singleton reference (reset by test fixture)
_wallet = None


def _get_wallet():
    global _wallet
    if _wallet is None:
        from core.economy.wallet import get_wallet_engine
        _wallet = get_wallet_engine()
    return _wallet


# ─── Static routes (must be before /{wallet_id}) ────────────────────────────


@router.get("/stats")
async def wallet_stats():
    """Get wallet system statistics."""
    engine = _get_wallet()
    stats = await engine.get_stats()
    return stats


@router.get("/supply/{token_type}")
async def total_supply(token_type: str):
    """Get total supply of a token."""
    engine = _get_wallet()
    supply = await engine.get_total_supply(token_type=token_type)
    return {"total_supply": supply}


@router.post("/create")
async def create_wallet(data: dict):
    """Create a new wallet."""
    engine = _get_wallet()
    owner_id = data.get("owner_id")
    if not owner_id:
        raise HTTPException(status_code=400, detail="owner_id is required")
    try:
        wallet = await engine.create_wallet(owner_id=owner_id)
        return {"success": True, "wallet_id": wallet.wallet_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deposit")
async def deposit(data: dict):
    """Deposit tokens to a wallet."""
    engine = _get_wallet()
    wallet_id = data.get("wallet_id")
    token_type = data.get("token_type", "nexus")
    amount = data.get("amount", 0.0)
    if not wallet_id:
        raise HTTPException(status_code=400, detail="wallet_id is required")
    success, msg = await engine.deposit(wallet_id=wallet_id, token_type=token_type, amount=float(amount))
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "tx_id": msg}


@router.post("/withdraw")
async def withdraw(data: dict):
    """Withdraw tokens from a wallet."""
    engine = _get_wallet()
    wallet_id = data.get("wallet_id")
    token_type = data.get("token_type", "nexus")
    amount = data.get("amount", 0.0)
    if not wallet_id:
        raise HTTPException(status_code=400, detail="wallet_id is required")
    success, msg = await engine.withdraw(wallet_id=wallet_id, token_type=token_type, amount=float(amount))
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "tx_id": msg}


@router.post("/transfer")
async def transfer(data: dict):
    """Transfer tokens between wallets."""
    engine = _get_wallet()
    from_wallet_id = data.get("from_wallet_id")
    to_wallet_id = data.get("to_wallet_id")
    token_type = data.get("token_type", "nexus")
    amount = data.get("amount", 0.0)
    if not from_wallet_id or not to_wallet_id:
        raise HTTPException(status_code=400, detail="from_wallet_id and to_wallet_id are required")
    success, msg = await engine.transfer(
        from_wallet_id=from_wallet_id,
        to_wallet_id=to_wallet_id,
        token_type=token_type,
        amount=float(amount),
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "tx_id": msg}


@router.post("/freeze")
async def freeze_wallet(data: dict):
    """Freeze a wallet."""
    engine = _get_wallet()
    wallet_id = data.get("wallet_id")
    reason = data.get("reason", "")
    if not wallet_id:
        raise HTTPException(status_code=400, detail="wallet_id is required")
    success = await engine.freeze_wallet(wallet_id=wallet_id, reason=reason)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to freeze wallet")
    return {"success": True}


# ─── Dynamic routes (with path parameters) ──────────────────────────────────


@router.get("/by-owner/{owner_id}")
async def get_wallet_by_owner(owner_id: str):
    """Get wallet by owner ID."""
    engine = _get_wallet()
    wallet = await engine.get_wallet_by_owner(owner_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found for owner")
    return {
        "wallet_id": wallet.wallet_id,
        "owner_id": wallet.owner_id,
        "owner_type": wallet.owner_type,
        "status": wallet.status,
        "balances": {k: {"token_type": k, "available": v.available, "locked": v.locked, "total": v.total} for k, v in wallet.balances.items()},
        "created_at": wallet.created_at,
    }


@router.get("/{wallet_id}")
async def get_wallet(wallet_id: str):
    """Get wallet by ID."""
    engine = _get_wallet()
    wallet = await engine.get_wallet(wallet_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {
        "wallet_id": wallet.wallet_id,
        "owner_id": wallet.owner_id,
        "owner_type": wallet.owner_type,
        "status": wallet.status,
        "balances": {k: {"token_type": k, "available": v.available, "locked": v.locked, "total": v.total} for k, v in wallet.balances.items()},
        "created_at": wallet.created_at,
    }


@router.get("/{wallet_id}/balance")
async def get_balance(wallet_id: str):
    """Get wallet balance."""
    engine = _get_wallet()
    wallet = await engine.get_wallet(wallet_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {
        "wallet_id": wallet_id,
        "balance": {k: v.available for k, v in wallet.balances.items()},
    }


@router.post("/{wallet_id}/close")
async def close_wallet(wallet_id: str):
    """Close a wallet."""
    engine = _get_wallet()
    success = await engine.close_wallet(wallet_id=wallet_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to close wallet")
    return {"success": True}


@router.get("/{wallet_id}/transactions")
async def list_transactions(wallet_id: str):
    """List transactions for a wallet."""
    engine = _get_wallet()
    txns = await engine.list_transactions(wallet_id=wallet_id)
    return {
        "transactions": [
            {
                "tx_id": t.tx_id,
                "wallet_id": t.wallet_id,
                "tx_type": t.tx_type,
                "token_type": t.token_type,
                "amount": t.amount,
                "reference": t.reference,
                "timestamp": t.timestamp,
                "status": t.status,
            }
            for t in txns
        ]
    }
