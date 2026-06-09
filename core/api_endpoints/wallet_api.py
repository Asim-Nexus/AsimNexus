"""
WalletEngine REST API endpoints for ASIMNEXUS.

Provides REST API access to WalletEngine operations including:
wallet creation, deposits, withdrawals, transfers, freeze/close,
balance inquiries, and transaction history.
"""

from typing import Optional, List
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_wallet = None

def _get_wallet():
    global _wallet
    if _wallet is None:
        try:
            from economy.wallet import get_wallet_engine
            _wallet = get_wallet_engine()
            logger.info("WalletEngine loaded")
        except Exception as e:
            logger.warning(f"WalletEngine unavailable: {e}")
    return _wallet


# ─── Request / Response Models ────────────────────────────────────────────────


class CreateWalletRequest(BaseModel):
    owner_id: str = Field(..., min_length=1, description="Unique owner identifier")
    owner_type: str = Field("user", pattern="^(user|agent|system)$")


class DepositRequest(BaseModel):
    wallet_id: str
    amount: float = Field(..., gt=0)
    token_type: str = "nexus"
    memo: str = ""


class WithdrawRequest(BaseModel):
    wallet_id: str
    amount: float = Field(..., gt=0)
    token_type: str = "nexus"
    memo: str = ""


class TransferRequest(BaseModel):
    from_wallet_id: str
    to_wallet_id: str
    amount: float = Field(..., gt=0)
    token_type: str = "nexus"
    memo: str = ""


class FreezeRequest(BaseModel):
    wallet_id: str
    reason: str = ""


# ─── Endpoints ────────────────────────────────────────────────────────────────

# NOTE: Route ordering matters — static paths like /stats MUST come before /{wallet_id}
# to avoid FastAPI matching "stats" as a wallet_id parameter.


@router.post("/api/economy/wallet/create", tags=["Economy Wallet"])
async def create_wallet(req: CreateWalletRequest):
    """Create a new wallet for a user or agent."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    # Check for duplicate wallet for same owner
    existing = await w.get_wallet_by_owner(req.owner_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Wallet already exists for owner {req.owner_id}")
    wallet = await w.create_wallet(req.owner_id, owner_type=req.owner_type)
    return {"success": True, "wallet_id": wallet.wallet_id, "wallet": wallet.to_dict()}


@router.get("/api/economy/wallet/stats", tags=["Economy Wallet"])
async def wallet_stats():
    """Get wallet engine statistics."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    return await w.get_stats()


@router.get("/api/economy/wallet/{wallet_id}", tags=["Economy Wallet"])
async def get_wallet(wallet_id: str):
    """Get wallet details by ID."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    entry = await w.get_wallet(wallet_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Wallet {wallet_id} not found")
    return entry.to_dict()


@router.get("/api/economy/wallet/by-owner/{owner_id}", tags=["Economy Wallet"])
async def get_wallet_by_owner(owner_id: str):
    """Get wallet by owner ID."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    entry = await w.get_wallet_by_owner(owner_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Wallet for owner {owner_id} not found")
    return entry.to_dict()


@router.get("/api/economy/wallet/{wallet_id}/balance", tags=["Economy Wallet"])
async def get_balance(wallet_id: str, token_type: str = Query("nexus")):
    """Get balance for a wallet and token type."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    balance = await w.get_balance(wallet_id, token_type)
    if not balance:
        raise HTTPException(status_code=404, detail=f"Wallet {wallet_id} or token {token_type} not found")
    return {"wallet_id": wallet_id, "token_type": token_type, "balance": balance.to_dict()}


@router.post("/api/economy/wallet/deposit", tags=["Economy Wallet"])
async def deposit(req: DepositRequest):
    """Deposit funds into a wallet."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    # Engine signature: deposit(self, wallet_id, token_type, amount, reference="", metadata=None)
    result = await w.deposit(req.wallet_id, req.token_type, req.amount, reference=req.memo)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    tx = await w.get_transaction(result[1])
    return {"success": True, "transaction_id": result[1], "transaction": tx.to_dict() if tx else {}}


@router.post("/api/economy/wallet/withdraw", tags=["Economy Wallet"])
async def withdraw(req: WithdrawRequest):
    """Withdraw funds from a wallet."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    # Engine signature: withdraw(self, wallet_id, token_type, amount, destination="", metadata=None)
    result = await w.withdraw(req.wallet_id, req.token_type, req.amount, destination=req.memo)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    tx = await w.get_transaction(result[1])
    return {"success": True, "transaction_id": result[1], "transaction": tx.to_dict() if tx else {}}


@router.post("/api/economy/wallet/transfer", tags=["Economy Wallet"])
async def transfer(req: TransferRequest):
    """Transfer funds between wallets."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    # Engine signature: transfer(self, from_wallet_id, to_wallet_id, token_type, amount, description="", metadata=None)
    result = await w.transfer(req.from_wallet_id, req.to_wallet_id, req.token_type, req.amount, description=req.memo)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    tx = await w.get_transaction(result[1])
    return {"success": True, "transaction_id": result[1], "transaction": tx.to_dict() if tx else {}}


@router.post("/api/economy/wallet/freeze", tags=["Economy Wallet"])
async def freeze_wallet(req: FreezeRequest):
    """Freeze a wallet."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    result = await w.freeze_wallet(req.wallet_id, reason=req.reason)
    if not result:
        raise HTTPException(status_code=400, detail=f"Failed to freeze wallet {req.wallet_id}")
    return {"success": True, "wallet_id": req.wallet_id, "status": "frozen"}


@router.post("/api/economy/wallet/{wallet_id}/close", tags=["Economy Wallet"])
async def close_wallet(wallet_id: str):
    """Close a wallet."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    result = await w.close_wallet(wallet_id)
    if not result:
        raise HTTPException(status_code=400, detail=f"Failed to close wallet {wallet_id}")
    return {"success": True, "wallet_id": wallet_id, "status": "closed"}


@router.get("/api/economy/wallet/{wallet_id}/transactions", tags=["Economy Wallet"])
async def list_transactions(wallet_id: str, limit: int = Query(50, ge=1, le=500)):
    """List transactions for a wallet."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    txns = await w.list_transactions(wallet_id, limit=limit)
    return {"wallet_id": wallet_id, "transactions": [t.to_dict() for t in txns], "count": len(txns)}


@router.get("/api/economy/wallet/{wallet_id}/transactions/{tx_id}", tags=["Economy Wallet"])
async def get_transaction(wallet_id: str, tx_id: str):
    """Get a specific transaction."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    tx = await w.get_transaction(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {tx_id} not found")
    return tx.to_dict()


@router.get("/api/economy/wallet/supply/{token_type}", tags=["Economy Wallet"])
async def get_total_supply(token_type: str = "nexus"):
    """Get total supply of a token type."""
    w = _get_wallet()
    if not w:
        raise HTTPException(status_code=503, detail="WalletEngine not available")
    supply = await w.get_total_supply(token_type)
    return {"token_type": token_type, "total_supply": supply}
