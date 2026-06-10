import logging
from typing import Dict, Any, Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger

_executor = None
def _get_executor():
    global _executor
    if _executor is None:
        try:
            from core.economy.contract_executor import get_contract_executor, ContractDuration, ContractType
            _executor = get_contract_executor()
            logger.info("ContractExecutor loaded")
        except Exception as e:
            logger.warning(f"ContractExecutor unavailable: {e}")
    return _executor


class CreateContractRequest(BaseModel):
    job_id: str
    client_id: str
    worker_id: str
    duration_days: int = Field(7, ge=1, le=365)
    details: Dict[str, Any] = Field(default_factory=lambda: {"title": "", "payment": 0.0, "currency": "NPR"})

class DisputeRequest(BaseModel):
    raised_by: str
    reason: str

class CancelRequest(BaseModel):
    cancelled_by: str
    reason: str = ""


@router.get("/api/contracts/stats")
async def contracts_stats():
    """Get contract executor statistics."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")
    return ex.get_stats()


@router.get("/api/contracts/list")
async def contracts_list(
    worker_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """List all contracts, optionally filtered by worker."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    if worker_id:
        return ex.get_worker_contracts(worker_id)
    else:
        contracts = list(ex.contracts.values())
        contracts.sort(key=lambda c: c.created_at, reverse=True)
        return {
            "total": len(contracts),
            "contracts": [c.to_dict() for c in contracts[:limit]],
        }


@router.get("/api/contracts/{contract_id}")
async def contracts_get(contract_id: str):
    """Get a single contract by ID."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    contract = ex.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    return contract.to_dict()


@router.post("/api/contracts/create")
async def contracts_create(req: CreateContractRequest):
    """Create a new contract."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    try:
        from core.economy.contract_executor import ContractDuration
        duration = ContractDuration.SHORT
        if req.duration_days >= 30:
            duration = ContractDuration.LONG
        elif req.duration_days >= 14:
            duration = ContractDuration.MEDIUM

        contract = await ex.create_contract(
            req.job_id, req.client_id, req.worker_id,
            duration, req.details,
        )
        logger.info(f"Contract created: {contract.id}")
        return {"success": True, "contract_id": contract.id, "status": contract.status}
    except Exception as e:
        logger.error(f"Contract creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/contracts/{contract_id}/accept")
async def contracts_accept(contract_id: str, worker_id: str = Query(..., description="Worker ID")):
    """Accept a contract."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    ok = await ex.accept_contract(contract_id, worker_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to accept contract")
    return {"success": True, "status": "accepted"}


@router.post("/api/contracts/{contract_id}/start")
async def contracts_start(contract_id: str, worker_id: str = Query(..., description="Worker ID")):
    """Start work on a contract."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    ok = await ex.start_contract(contract_id, worker_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to start contract")
    return {"success": True, "status": "active"}


@router.post("/api/contracts/{contract_id}/complete")
async def contracts_complete(contract_id: str, worker_id: str = Query(..., description="Worker ID")):
    """Mark a contract as completed."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    ok = await ex.complete_contract(contract_id, worker_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to complete contract")
    return {"success": True, "status": "completed"}


@router.post("/api/contracts/{contract_id}/approve")
async def contracts_approve(contract_id: str, client_id: str = Query(..., description="Client ID")):
    """Approve a completed contract."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    result = await ex.approve_contract(contract_id, client_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to approve"))
    return result


@router.post("/api/contracts/{contract_id}/release-payment")
async def contracts_release_payment(
    contract_id: str,
    client_id: str = Query(..., description="Client ID"),
):
    """Release payment for an approved contract."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    result = await ex.release_payment(contract_id, client_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to release payment"))
    return result


@router.post("/api/contracts/{contract_id}/dispute")
async def contracts_dispute(contract_id: str, req: DisputeRequest):
    """Raise a dispute on a contract."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    ok = await ex.dispute_contract(contract_id, req.raised_by, req.reason)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to dispute contract")
    return {"success": True, "status": "disputed"}


@router.post("/api/contracts/{contract_id}/cancel")
async def contracts_cancel(contract_id: str, req: CancelRequest):
    """Cancel a contract."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    ok = await ex.cancel_contract(contract_id, req.cancelled_by, req.reason)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to cancel contract")
    return {"success": True, "status": "cancelled"}


@router.get("/api/contracts/{contract_id}/audit")
async def contracts_audit(
    contract_id: str,
    limit: int = Query(50, ge=1, le=500),
):
    """Get audit trail for a contract."""
    ex = _get_executor()
    if not ex:
        raise HTTPException(status_code=503, detail="ContractExecutor not available")

    trail = ex.get_audit_trail(contract_id=contract_id, limit=limit)
    return {"contract_id": contract_id, "entries": trail, "total": len(trail)}
