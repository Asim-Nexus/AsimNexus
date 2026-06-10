from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_bridge = None
def _get_bridge():
    global _bridge
    if _bridge is None:
        try:
            from core.economy.token_bridge import get_token_bridge
            _bridge = get_token_bridge()
            logger.info("TokenBridge loaded")
        except Exception as e:
            logger.warning(f"TokenBridge unavailable: {e}")
    return _bridge


class CreatePoolRequest(BaseModel):
    chain: str
    token_symbol: str
    token_address: str = "0x0"
    initial_balance: float = 0.0
    min_bridge: float = 0.01
    max_bridge: float = 100000.0
    fee_rate: Optional[float] = None

class AddLiquidityRequest(BaseModel):
    pool_id: str
    amount: float = Field(..., gt=0)

class RemoveLiquidityRequest(BaseModel):
    pool_id: str
    amount: float = Field(..., gt=0)

class InitiateBridgeRequest(BaseModel):
    from_chain: str
    to_chain: str
    asset: str
    amount: float = Field(..., gt=0)
    sender: str
    recipient: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LockTokensRequest(BaseModel):
    tx_id: str
    lock_tx_hash: str

class ReleaseTokensRequest(BaseModel):
    tx_id: str
    release_tx_hash: str

class FailBridgeRequest(BaseModel):
    tx_id: str
    reason: str = ""


@router.get("/api/bridge/stats")
async def bridge_stats():
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    return b.get_bridge_stats()


@router.post("/api/bridge/pool/create")
async def bridge_create_pool(req: CreatePoolRequest):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    try:
        pool = b.create_pool(req.chain, req.token_symbol, req.token_address,
                             req.initial_balance, req.min_bridge, req.max_bridge, req.fee_rate)
        return {"success": True, "pool": pool.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/bridge/pools")
async def bridge_list_pools(chain: Optional[str] = Query(None)):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    return {"pools": b.list_pools(chain)}


@router.post("/api/bridge/pool/add-liquidity")
async def bridge_add_liquidity(req: AddLiquidityRequest):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    pool = b.add_liquidity(req.pool_id, req.amount)
    if not pool:
        raise HTTPException(status_code=400, detail="Failed to add liquidity")
    return {"success": True, "pool": pool.to_dict()}


@router.post("/api/bridge/pool/remove-liquidity")
async def bridge_remove_liquidity(req: RemoveLiquidityRequest):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    pool = b.remove_liquidity(req.pool_id, req.amount)
    if not pool:
        raise HTTPException(status_code=400, detail="Failed to remove liquidity")
    return {"success": True, "pool": pool.to_dict()}


@router.post("/api/bridge/initiate")
async def bridge_initiate(req: InitiateBridgeRequest):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    result = b.initiate_bridge(req.from_chain, req.to_chain, req.asset,
                               req.amount, req.sender, req.recipient, req.metadata)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Bridge initiation failed"))
    return result


@router.post("/api/bridge/lock")
async def bridge_lock(req: LockTokensRequest):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    result = b.lock_tokens(req.tx_id, req.lock_tx_hash)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Lock failed"))
    return result


@router.post("/api/bridge/confirm/{tx_id}")
async def bridge_confirm(tx_id: str):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    result = b.confirm_transaction(tx_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Confirmation failed"))
    return result


@router.post("/api/bridge/release")
async def bridge_release(req: ReleaseTokensRequest):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    result = b.release_tokens(req.tx_id, req.release_tx_hash)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Release failed"))
    return result


@router.post("/api/bridge/fail")
async def bridge_fail(req: FailBridgeRequest):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    result = b.fail_transaction(req.tx_id, req.reason)
    return result


@router.post("/api/bridge/{tx_id}/refund")
async def bridge_refund(tx_id: str):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    result = b.refund_transaction(tx_id)
    return result


@router.get("/api/bridge/tx/{tx_id}")
async def bridge_get_transaction(tx_id: str):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    tx = b.get_transaction(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction not found: {tx_id}")
    return tx


@router.get("/api/bridge/transactions")
async def bridge_list_transactions(
    status: Optional[str] = Query(None),
    sender: Optional[str] = Query(None),
    recipient: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    return {"transactions": b.list_transactions(status, sender, recipient, limit)}


@router.get("/api/bridge/fee")
async def bridge_calculate_fee(
    from_chain: str = Query(...),
    amount: float = Query(..., gt=0),
):
    b = _get_bridge()
    if not b:
        raise HTTPException(status_code=503, detail="TokenBridge not available")
    fee = b.calculate_fee(from_chain, amount)
    return {"from_chain": from_chain, "amount": amount, "fee": fee, "net_amount": round(amount - fee, 8)}
