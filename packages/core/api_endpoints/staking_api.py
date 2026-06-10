"""
StakingEngine REST API endpoints for ASIMNEXUS.

Provides REST API access to StakingEngine operations including:
staking positions, unstaking, reward distribution, validator management,
slashing, and statistics.
"""

from typing import Optional
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field

from . import router, logger


_staking = None

def _get_staking():
    global _staking
    if _staking is None:
        try:
            from economy.staking import get_staking_engine
            _staking = get_staking_engine()
            logger.info("StakingEngine loaded")
        except Exception as e:
            logger.warning(f"StakingEngine unavailable: {e}")
    return _staking


# ─── Request Models ───────────────────────────────────────────────────────────


class StakeRequest(BaseModel):
    staker_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    token_type: str = "nexus"
    lock_days: int = Field(default=30, ge=7, le=365)
    auto_compound: bool = False
    validator_id: Optional[str] = None


class UnstakeRequest(BaseModel):
    stake_id: str
    staker_id: str = Field(..., min_length=1)


class ClaimUnstakedRequest(BaseModel):
    stake_id: str
    staker_id: str = Field(..., min_length=1)


class RegisterValidatorRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    owner_id: str = Field(..., min_length=1)
    commission_rate: float = Field(default=0.1, ge=0, le=1)
    description: str = ""
    website: str = ""


class JailValidatorRequest(BaseModel):
    validator_id: str
    reason: str = ""


class UnjailValidatorRequest(BaseModel):
    validator_id: str


class SlashRequest(BaseModel):
    validator_id: str
    slash_percent: float = Field(default=0.1, gt=0, le=1)
    reason: str = ""


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/api/economy/staking/stake", tags=["Economy Staking"])
async def stake(req: StakeRequest):
    """Create a new staking position."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    result = await s.stake(
        staker_id=req.staker_id,
        amount=req.amount,
        token_type=req.token_type,
        lock_days=req.lock_days,
        auto_compound=req.auto_compound,
        validator_id=req.validator_id,
    )
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    stake_obj = await s.get_stake(result[1])
    return {"success": True, "stake_id": result[1], "stake": stake_obj.to_dict() if stake_obj else {}}


@router.post("/api/economy/staking/unstake", tags=["Economy Staking"])
async def unstake(req: UnstakeRequest):
    """Request unstaking (starts cooldown period)."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    result = await s.unstake(req.stake_id, req.staker_id)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "stake_id": req.stake_id, "message": result[1]}


@router.post("/api/economy/staking/claim", tags=["Economy Staking"])
async def claim_unstaked(req: ClaimUnstakedRequest):
    """Claim unstaked funds after cooldown."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    result = await s.claim_unstaked(req.stake_id, req.staker_id)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "stake_id": req.stake_id, "message": result[1]}


@router.get("/api/economy/staking/positions/{stake_id}", tags=["Economy Staking"])
async def get_stake(stake_id: str):
    """Get a staking position by ID."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    stake_obj = await s.get_stake(stake_id)
    if not stake_obj:
        raise HTTPException(status_code=404, detail=f"Stake {stake_id} not found")
    return stake_obj.to_dict()


@router.get("/api/economy/staking/positions", tags=["Economy Staking"])
async def get_stakes_for_user(staker_id: str = Query(..., min_length=1)):
    """Get all staking positions for a user."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    stakes = await s.get_stakes_for_user(staker_id)
    return {"staker_id": staker_id, "stakes": [st.to_dict() for st in stakes], "count": len(stakes)}


@router.get("/api/economy/staking/total-staked", tags=["Economy Staking"])
async def get_total_staked(token_type: str = Query("nexus")):
    """Get total staked amount."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    total = await s.get_total_staked(token_type=token_type)
    return {"token_type": token_type, "total_staked": total}


@router.post("/api/economy/staking/distribute-rewards", tags=["Economy Staking"])
async def distribute_all_rewards():
    """Distribute rewards to all eligible staking positions."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    count = await s.distribute_all_rewards()
    return {"success": True, "positions_rewarded": count}


@router.get("/api/economy/staking/rewards/{staker_id}", tags=["Economy Staking"])
async def get_rewards_history(staker_id: str, limit: int = Query(50, ge=1, le=500)):
    """Get reward distribution history for a user."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    rewards = await s.get_rewards_history(staker_id, limit=limit)
    return {"staker_id": staker_id, "rewards": [r.to_dict() for r in rewards], "count": len(rewards)}


@router.post("/api/economy/staking/validators", tags=["Economy Staking"])
async def register_validator(req: RegisterValidatorRequest):
    """Register a new validator."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    try:
        validator = await s.register_validator(
            name=req.name,
            owner_id=req.owner_id,
            commission_rate=req.commission_rate,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "validator_id": validator.validator_id, "validator": validator.to_dict()}


@router.get("/api/economy/staking/validators/{validator_id}", tags=["Economy Staking"])
async def get_validator(validator_id: str):
    """Get a validator by ID."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    validator = await s.get_validator(validator_id)
    if not validator:
        raise HTTPException(status_code=404, detail=f"Validator {validator_id} not found")
    return validator.to_dict()


@router.get("/api/economy/staking/validators", tags=["Economy Staking"])
async def list_validators(status: Optional[str] = Query(None, pattern="^(active|jailed|inactive)$")):
    """List all validators, optionally filtered by status."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    validators = await s.list_validators(status=status)
    return {"validators": [v.to_dict() for v in validators], "count": len(validators)}


@router.post("/api/economy/staking/validators/jail", tags=["Economy Staking"])
async def jail_validator(req: JailValidatorRequest):
    """Jail a validator."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    result = await s.jail_validator(req.validator_id, reason=req.reason)
    if not result:
        raise HTTPException(status_code=400, detail=f"Failed to jail validator {req.validator_id}")
    return {"success": True, "validator_id": req.validator_id, "status": "jailed"}


@router.post("/api/economy/staking/validators/unjail", tags=["Economy Staking"])
async def unjail_validator(req: UnjailValidatorRequest):
    """Unjail a validator."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    result = await s.unjail_validator(req.validator_id)
    if not result:
        raise HTTPException(status_code=400, detail=f"Failed to unjail validator {req.validator_id}")
    return {"success": True, "validator_id": req.validator_id, "status": "active"}


@router.post("/api/economy/staking/slash", tags=["Economy Staking"])
async def slash_validator(req: SlashRequest):
    """Slash a validator's staked funds."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    result = await s.slash(req.validator_id, slash_percent=req.slash_percent, reason=req.reason)
    if not result[0]:
        raise HTTPException(status_code=400, detail=result[1])
    return {"success": True, "validator_id": req.validator_id, "message": result[1]}


@router.post("/api/economy/staking/unlock-matured", tags=["Economy Staking"])
async def unlock_stakes():
    """Unlock all matured staking positions."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    unlocked = await s.unlock_stakes()
    return {"unlocked_count": len(unlocked), "unlocked_ids": unlocked}


@router.get("/api/economy/staking/stats", tags=["Economy Staking"])
async def staking_stats():
    """Get staking engine statistics."""
    s = _get_staking()
    if not s:
        raise HTTPException(status_code=503, detail="StakingEngine not available")
    return await s.get_stats()
