from typing import Dict, Any, Optional, List

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_hybrid = None
def _get_hybrid():
    global _hybrid
    if _hybrid is None:
        try:
            from core.economy.hybrid_economy import get_hybrid_economy, EconomyMode
            _hybrid = get_hybrid_economy()
            logger.info("HybridEconomy loaded")
        except Exception as e:
            logger.warning(f"HybridEconomy unavailable: {e}")
    return _hybrid


class CreateAccountRequest(BaseModel):
    owner_id: str
    owner_type: str = Field(..., pattern="^(user|agent)$")
    initial_balance: float = 0.0

class DepositRequest(BaseModel):
    owner_id: str
    amount: float = Field(..., gt=0)
    memo: str = ""

class WithdrawRequest(BaseModel):
    owner_id: str
    amount: float = Field(..., gt=0)
    memo: str = ""

class TransferRequest(BaseModel):
    from_id: str
    to_id: str
    amount: float = Field(..., gt=0)
    memo: str = ""

class CreateTaskRequest(BaseModel):
    description: str
    requester_id: str
    reward: float = Field(..., ge=0)
    category: str = "general"
    reward_currency: str = "NPR"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AssignTaskRequest(BaseModel):
    task_id: str
    executor_id: str

class SetModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(user_mode|agent_user_mode|hybrid)$")


@router.get("/api/hybrid-economy/summary")
async def hybrid_economy_summary():
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    return he.get_economy_summary()


@router.post("/api/hybrid-economy/mode")
async def hybrid_economy_set_mode(req: SetModeRequest):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    try:
        from core.economy.hybrid_economy import EconomyMode
        mode = EconomyMode(req.mode)
        return he.set_mode(mode)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/hybrid-economy/account")
async def hybrid_economy_create_account(req: CreateAccountRequest):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    try:
        account = he.create_account(req.owner_id, req.owner_type, req.initial_balance)
        return {"success": True, "account": account.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/hybrid-economy/account/{owner_id}")
async def hybrid_economy_get_account(owner_id: str):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    account = he.get_account(owner_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account not found: {owner_id}")
    return account.to_dict()


@router.get("/api/hybrid-economy/accounts")
async def hybrid_economy_list_accounts(owner_type: Optional[str] = Query(None)):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    return {"accounts": he.get_accounts(owner_type)}


@router.post("/api/hybrid-economy/deposit")
async def hybrid_economy_deposit(req: DepositRequest):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    result = he.deposit(req.owner_id, req.amount, req.memo)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Deposit failed"))
    return result


@router.post("/api/hybrid-economy/withdraw")
async def hybrid_economy_withdraw(req: WithdrawRequest):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    result = he.withdraw(req.owner_id, req.amount, req.memo)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Withdrawal failed"))
    return result


@router.post("/api/hybrid-economy/transfer")
async def hybrid_economy_transfer(req: TransferRequest):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    result = he.transfer(req.from_id, req.to_id, req.amount, req.memo)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Transfer failed"))
    return result


@router.post("/api/hybrid-economy/task")
async def hybrid_economy_create_task(req: CreateTaskRequest):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    try:
        task = he.create_task(req.description, req.requester_id, req.reward,
                              req.category, req.reward_currency, req.metadata)
        return {"success": True, "task": task.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/hybrid-economy/task/assign")
async def hybrid_economy_assign_task(req: AssignTaskRequest):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    result = he.assign_task(req.task_id, req.executor_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Assignment failed"))
    return result


@router.post("/api/hybrid-economy/task/{task_id}/start")
async def hybrid_economy_start_task(task_id: str, executor_id: str = Query(...)):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    result = he.start_task(task_id, executor_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Start failed"))
    return result


@router.post("/api/hybrid-economy/task/{task_id}/complete")
async def hybrid_economy_complete_task(task_id: str, executor_id: str = Query(...)):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    result = he.complete_task(task_id, executor_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Completion failed"))
    return result


@router.post("/api/hybrid-economy/task/{task_id}/fail")
async def hybrid_economy_fail_task(task_id: str, reason: str = Query("")):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    result = he.fail_task(task_id, reason)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to fail task"))
    return result


@router.post("/api/hybrid-economy/task/{task_id}/cancel")
async def hybrid_economy_cancel_task(task_id: str):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    result = he.cancel_task(task_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Cancellation failed"))
    return result


@router.get("/api/hybrid-economy/tasks")
async def hybrid_economy_list_tasks(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    requester_id: Optional[str] = Query(None),
    executor_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    he = _get_hybrid()
    if not he:
        raise HTTPException(status_code=503, detail="HybridEconomy not available")
    tasks = he.get_tasks(status, category, requester_id, executor_id, limit)
    return {"total": len(tasks), "tasks": tasks}
