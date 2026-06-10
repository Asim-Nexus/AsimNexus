import logging
from typing import Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_credits = None
def _get_credits():
    global _credits
    if _credits is None:
        try:
            from economy.nexus_credits import get_nexus_credits, PackageType
            _credits = get_nexus_credits()
            logger.info("NexusCredits loaded")
        except Exception as e:
            logger.warning(f"NexusCredits unavailable: {e}")
    return _credits


class CreateCreditRequest(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0)

class PurchasePackageRequest(BaseModel):
    user_id: str
    package_type: str

class RewardTaskRequest(BaseModel):
    agent_id: str
    task_id: str
    reward_amount: float = Field(..., gt=0)

class TransferCreditsRequest(BaseModel):
    sender_id: str
    receiver_id: str
    amount: float = Field(..., gt=0)


@router.get("/api/credits/stats")
async def credits_stats():
    """Get Nexus Credits economy statistics."""
    nc = _get_credits()
    if not nc:
        raise HTTPException(status_code=503, detail="NexusCredits not available")
    return nc.get_economy_statistics()


@router.get("/api/credits/balance/{user_id}")
async def credits_balance(user_id: str):
    """Get balance for a user."""
    nc = _get_credits()
    if not nc:
        raise HTTPException(status_code=503, detail="NexusCredits not available")
    return {"user_id": user_id, "balance": nc.get_balance(user_id)}


@router.post("/api/credits/create")
async def credits_create(req: CreateCreditRequest):
    """Create Nexus Credits for a user."""
    nc = _get_credits()
    if not nc:
        raise HTTPException(status_code=503, detail="NexusCredits not available")

    try:
        credit = await nc.create_credit(req.user_id, req.amount)
        logger.info(f"Credit created: {credit.credit_id} for {req.user_id}")
        return {
            "success": True,
            "credit_id": credit.credit_id,
            "user_id": req.user_id,
            "amount": req.amount,
            "balance": nc.get_balance(req.user_id),
        }
    except Exception as e:
        logger.error(f"Credit creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/credits/purchase-package")
async def credits_purchase_package(req: PurchasePackageRequest):
    """Purchase an agent package."""
    nc = _get_credits()
    if not nc:
        raise HTTPException(status_code=503, detail="NexusCredits not available")

    try:
        from economy.nexus_credits import PackageType
        package_map = {
            "five_days": PackageType.FIVE_DAYS,
            "fifteen_days": PackageType.FIFTEEN_DAYS,
            "thirty_days": PackageType.THIRTY_DAYS,
        }
        ptype = package_map.get(req.package_type)
        if not ptype:
            raise HTTPException(status_code=400, detail=f"Invalid package_type: {req.package_type}")

        txn = await nc.purchase_package(req.user_id, ptype)
        return {
            "success": True,
            "transaction_id": txn.transaction_id,
            "amount": txn.amount,
            "balance": nc.get_balance(req.user_id),
            "status": txn.status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Package purchase error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/credits/reward")
async def credits_reward(req: RewardTaskRequest):
    """Reward an agent for task completion."""
    nc = _get_credits()
    if not nc:
        raise HTTPException(status_code=503, detail="NexusCredits not available")

    try:
        txn = await nc.reward_task_completion(req.agent_id, req.task_id, req.reward_amount)
        return {
            "success": txn.status == "completed",
            "transaction_id": txn.transaction_id,
            "agent_id": req.agent_id,
            "amount": req.reward_amount,
            "balance": nc.get_balance(req.agent_id),
            "status": txn.status,
        }
    except Exception as e:
        logger.error(f"Reward error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/credits/transfer")
async def credits_transfer(req: TransferCreditsRequest):
    """Transfer credits between users."""
    nc = _get_credits()
    if not nc:
        raise HTTPException(status_code=503, detail="NexusCredits not available")

    try:
        txn = await nc.transfer_credits(req.sender_id, req.receiver_id, req.amount)
        return {
            "success": txn.status == "completed",
            "transaction_id": txn.transaction_id,
            "sender_id": req.sender_id,
            "receiver_id": req.receiver_id,
            "amount": req.amount,
            "sender_balance": nc.get_balance(req.sender_id),
            "receiver_balance": nc.get_balance(req.receiver_id),
            "status": txn.status,
        }
    except Exception as e:
        logger.error(f"Transfer error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/credits/transactions/{user_id}")
async def credits_transactions(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
):
    """Get transaction history for a user."""
    nc = _get_credits()
    if not nc:
        raise HTTPException(status_code=503, detail="NexusCredits not available")

    history = nc.get_transaction_history(user_id, limit=limit)
    return {
        "user_id": user_id,
        "total": len(history),
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "type": t.transaction_type,
                "sender": t.sender_id,
                "receiver": t.receiver_id,
                "amount": t.amount,
                "status": t.status,
                "timestamp": t.timestamp,
            }
            for t in history
        ],
    }
