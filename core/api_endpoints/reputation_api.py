from typing import Optional

from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_reputation = None
def _get_reputation():
    global _reputation
    if _reputation is None:
        try:
            from core.economy.reputation_system import get_reputation_system
            _reputation = get_reputation_system()
            logger.info("ReputationSystem loaded")
        except Exception as e:
            logger.warning(f"ReputationSystem unavailable: {e}")
    return _reputation


class RegisterEntityRequest(BaseModel):
    entity_id: str
    initial_score: float = 0.0

class AddReputationRequest(BaseModel):
    entity_id: str
    amount: float = Field(..., gt=0)
    reason: str = ""

class RemoveReputationRequest(BaseModel):
    entity_id: str
    amount: float = Field(..., gt=0)
    reason: str = ""

class StakeRequest(BaseModel):
    entity_id: str
    amount: float = Field(..., gt=0)
    reason: str = ""

class UnstakeRequest(BaseModel):
    stake_id: str

class SlashRequest(BaseModel):
    stake_id: str
    penalty_pct: float = Field(1.0, ge=0.0, le=1.0)
    reason: str = ""


@router.get("/api/reputation/stats")
async def reputation_stats():
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    return rs.get_system_stats()


@router.get("/api/reputation/leaderboard")
async def reputation_leaderboard(limit: int = Query(10, ge=1, le=100)):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    return {"leaderboard": rs.get_leaderboard(limit)}


@router.post("/api/reputation/register")
async def reputation_register(req: RegisterEntityRequest):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    score = rs.register_entity(req.entity_id, req.initial_score)
    return {"success": True, "entity": score.to_dict()}


@router.get("/api/reputation/{entity_id}")
async def reputation_get(entity_id: str):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    result = rs.get_reputation(entity_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Entity not found: {entity_id}")
    return result


@router.get("/api/reputation/{entity_id}/events")
async def reputation_events(entity_id: str, limit: int = Query(50, ge=1, le=500)):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    return {"entity_id": entity_id, "events": rs.get_entity_events(entity_id, limit)}


@router.post("/api/reputation/add")
async def reputation_add(req: AddReputationRequest):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    result = rs.add_reputation(req.entity_id, req.amount, req.reason)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to add reputation")
    return {"success": True, "entity": result.to_dict()}


@router.post("/api/reputation/remove")
async def reputation_remove(req: RemoveReputationRequest):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    result = rs.remove_reputation(req.entity_id, req.amount, req.reason)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to remove reputation")
    return {"success": True, "entity": result.to_dict()}


@router.post("/api/reputation/stake")
async def reputation_stake(req: StakeRequest):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    stake = rs.stake(req.entity_id, req.amount, req.reason)
    if not stake:
        raise HTTPException(status_code=400, detail="Failed to stake. Insufficient reputation?")
    return {"success": True, "stake": stake.to_dict()}


@router.post("/api/reputation/unstake")
async def reputation_unstake(req: UnstakeRequest):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    stake = rs.unstake(req.stake_id)
    if not stake:
        raise HTTPException(status_code=400, detail="Failed to unstake")
    return {"success": True, "stake": stake.to_dict()}


@router.post("/api/reputation/slash")
async def reputation_slash(req: SlashRequest):
    rs = _get_reputation()
    if not rs:
        raise HTTPException(status_code=503, detail="ReputationSystem not available")
    stake = rs.slash(req.stake_id, req.penalty_pct, req.reason)
    if not stake:
        raise HTTPException(status_code=400, detail="Failed to slash stake")
    return {"success": True, "stake": stake.to_dict()}
