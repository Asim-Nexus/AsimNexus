"""
Staking API Routes
==================
FastAPI router for staking endpoints (/api/economy/staking/*).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/economy/staking", tags=["economy-staking"])

# Module-level singleton reference (reset by test fixture)
_staking = None


def _get_staking():
    global _staking
    if _staking is None:
        from core.economy.staking import get_staking_engine
        _staking = get_staking_engine()
    return _staking


# ── Static routes first ────────────────────────────────────────────────── #


@router.get("/stats")
async def staking_stats():
    """Get staking system statistics."""
    engine = _get_staking()
    stats = await engine.get_stats()
    return stats


@router.get("/positions")
async def get_stake_positions(staker_id: str = ""):
    """Get stake positions for a user."""
    engine = _get_staking()
    if not staker_id:
        raise HTTPException(status_code=400, detail="staker_id is required")
    stakes = await engine.get_stakes_for_user(user_id=staker_id)
    return {
        "stakes": [
            {
                "stake_id": s.stake_id,
                "staker_id": s.staker_id,
                "validator_id": s.validator_id,
                "amount": s.amount,
                "status": s.status,
                "lock_days": s.lock_days,
                "created_at": s.created_at,
                "apy_at_stake": s.apy_at_stake,
                "auto_compound": s.auto_compound,
            }
            for s in stakes
        ]
    }


@router.post("/validators/jail")
async def jail_validator(data: dict):
    """Jail a validator."""
    engine = _get_staking()
    validator_id = data.get("validator_id")
    reason = data.get("reason", "Unknown violation")
    if not validator_id:
        raise HTTPException(status_code=400, detail="validator_id is required")
    result = await engine.jail_validator(validator_id=validator_id, reason=reason)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to jail validator")
    return {"success": True}


@router.post("/validators/unjail")
async def unjail_validator(data: dict):
    """Unjail a validator."""
    engine = _get_staking()
    validator_id = data.get("validator_id")
    if not validator_id:
        raise HTTPException(status_code=400, detail="validator_id is required")
    result = await engine.unjail_validator(validator_id=validator_id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to unjail validator")
    return {"success": True}


@router.post("/validators")
async def register_validator(data: dict):
    """Register a new validator."""
    engine = _get_staking()
    name = data.get("name")
    owner_id = data.get("owner_id")
    commission_rate = data.get("commission_rate", 0.1)
    self_stake = data.get("self_stake", 0.0)
    if not name or not owner_id:
        raise HTTPException(status_code=400, detail="name and owner_id are required")
    try:
        validator = await engine.register_validator(
            name=name,
            owner_id=owner_id,
            commission_rate=float(commission_rate),
            self_stake=float(self_stake),
        )
        return {"success": True, "validator_id": validator.validator_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/validators")
async def list_validators():
    """List all validators."""
    engine = _get_staking()
    validators = await engine.list_validators()
    return {
        "validators": [
            {
                "validator_id": v.validator_id,
                "name": v.name,
                "owner_id": v.owner_id,
                "commission_rate": v.commission_rate,
                "total_staked": v.total_staked,
                "status": v.status,
            }
            for v in validators
        ]
    }


@router.get("/validators/{validator_id}")
async def get_validator(validator_id: str):
    """Get a validator by ID."""
    engine = _get_staking()
    validator = await engine.get_validator(validator_id=validator_id)
    if validator is None:
        raise HTTPException(status_code=404, detail="Validator not found")
    return {
        "validator_id": validator.validator_id,
        "name": validator.name,
        "owner_id": validator.owner_id,
        "commission_rate": validator.commission_rate,
        "total_staked": validator.total_staked,
        "status": validator.status,
    }


@router.post("/stake")
async def stake(data: dict):
    """Stake tokens with a validator."""
    engine = _get_staking()
    staker_id = data.get("staker_id")
    validator_id = data.get("validator_id")
    amount = data.get("amount", 0.0)
    token_type = data.get("token_type", "nexus")
    lock_days = data.get("lock_days", 30)
    auto_compound = data.get("auto_compound", False)
    if not staker_id or not validator_id:
        raise HTTPException(status_code=400, detail="staker_id and validator_id are required")
    success, stake_id = await engine.stake(
        staker_id=staker_id,
        token_type=token_type,
        validator_id=validator_id,
        amount=float(amount),
        lock_days=int(lock_days),
        auto_compound=auto_compound,
    )
    if not success:
        raise HTTPException(status_code=400, detail=stake_id)
    return {"success": True, "stake_id": stake_id}


@router.post("/unstake")
async def unstake(data: dict):
    """Unstake tokens from a position."""
    engine = _get_staking()
    stake_id = data.get("stake_id")
    staker_id = data.get("staker_id")
    if not stake_id or not staker_id:
        raise HTTPException(status_code=400, detail="stake_id and staker_id are required")
    success, msg = await engine.unstake(stake_id=stake_id, user_id=staker_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}


@router.post("/claim")
async def claim_rewards(data: dict):
    """Claim rewards for a stake position."""
    engine = _get_staking()
    stake_id = data.get("stake_id")
    staker_id = data.get("staker_id")
    if not stake_id or not staker_id:
        raise HTTPException(status_code=400, detail="stake_id and staker_id are required")
    success, msg = await engine.claim_unstaked(stake_id=stake_id, user_id=staker_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True}


@router.post("/distribute-rewards")
async def distribute_rewards():
    """Distribute rewards to all stakers."""
    engine = _get_staking()
    result = await engine.distribute_all_rewards()
    return {"success": True, "result": result}
