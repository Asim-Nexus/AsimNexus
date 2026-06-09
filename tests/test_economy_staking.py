#!/usr/bin/env python3
"""
Tests for economy/staking.py — StakingEngine, StakePosition, Validators, Rewards.
"""

import pytest
import os
from datetime import datetime, timedelta
from economy.staking import (
    StakingEngine, StakePosition, Validator, RewardDistribution,
    StakeStatus, ValidatorStatus,
    get_staking_engine, reset_staking_engine,
)


@pytest.fixture(autouse=True)
def reset():
    """Reset singleton and clear data file before each test."""
    try:
        os.remove(StakingEngine.LEDGER_PATH)
    except FileNotFoundError:
        pass
    reset_staking_engine()
    yield
    reset_staking_engine()


@pytest.fixture
def engine():
    return StakingEngine()


@pytest.mark.asyncio
async def test_stake(engine):
    """Stake tokens."""
    success, stake_id = await engine.stake(
        staker_id="staker_001",
        token_type="nexus",
        amount=1000.0,
        lock_days=30,
    )
    assert success is True
    assert stake_id.startswith("stk_")

    stake = await engine.get_stake(stake_id)
    assert stake is not None
    assert stake.staker_id == "staker_001"
    assert stake.amount == 1000.0
    assert stake.lock_days == 30
    assert stake.status == "locked"
    assert stake.apy_at_stake == 0.12  # 12% for 30 days
    assert stake.locked_until is not None


@pytest.mark.asyncio
async def test_stake_below_minimum(engine):
    """Stake below minimum should fail."""
    success, msg = await engine.stake("staker_min", "nexus", 1.0, lock_days=30)
    assert success is False
    assert "minimum" in msg.lower()


@pytest.mark.asyncio
async def test_stake_invalid_lock_days(engine):
    """Stake with invalid lock period."""
    success, msg = await engine.stake("staker_inv", "nexus", 100.0, lock_days=99)
    assert success is False
    assert "invalid" in msg.lower()


@pytest.mark.asyncio
async def test_stake_multiple_positions(engine):
    """Create multiple stake positions for same user."""
    s1, _ = await engine.stake("multi_user", "nexus", 500.0, lock_days=7)
    s2, _ = await engine.stake("multi_user", "nexus", 1000.0, lock_days=30)
    s3, _ = await engine.stake("multi_user", "svt", 100.0, lock_days=14)

    stakes = await engine.get_stakes_for_user("multi_user")
    assert len(stakes) == 3

    # Filter by status
    locked = await engine.get_stakes_for_user("multi_user", status="locked")
    assert len(locked) == 3


@pytest.mark.asyncio
async def test_unlock_stakes(engine):
    """Transition locked stakes to active."""
    success, stake_id = await engine.stake("unlock_user", "nexus", 100.0, lock_days=7)

    # Override locked_until to past
    stake = await engine.get_stake(stake_id)
    stake.locked_until = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    unlocked = await engine.unlock_stakes()
    assert stake_id in unlocked

    stake = await engine.get_stake(stake_id)
    assert stake.status == "active"


@pytest.mark.asyncio
async def test_unstake(engine):
    """Initiate unstaking."""
    success, stake_id = await engine.stake("unstake_user", "nexus", 500.0, lock_days=7)

    # Force unlock
    stake = await engine.get_stake(stake_id)
    stake.locked_until = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    stake.status = "active"

    success, msg = await engine.unstake(stake_id, "unstake_user")
    assert success is True

    stake = await engine.get_stake(stake_id)
    assert stake.status == "unstaking"
    assert stake.unstaked_at is not None


@pytest.mark.asyncio
async def test_unstake_during_lock(engine):
    """Unstaking during lock period should fail."""
    success, stake_id = await engine.stake("locked_user", "nexus", 100.0, lock_days=30)

    success, msg = await engine.unstake(stake_id, "locked_user")
    assert success is False
    assert "locked" in msg.lower()


@pytest.mark.asyncio
async def test_claim_unstaked(engine):
    """Claim tokens after unstaking cooldown."""
    success, stake_id = await engine.stake("claim_user", "nexus", 1000.0, lock_days=7)

    # Force unlock
    stake = await engine.get_stake(stake_id)
    stake.locked_until = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    stake.status = "active"

    # Initiate unstake
    await engine.unstake(stake_id, "claim_user")

    # Force cooldown completion
    stake = await engine.get_stake(stake_id)
    stake.unstaked_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    success, msg = await engine.claim_unstaked(stake_id, "claim_user")
    assert success is True

    stake = await engine.get_stake(stake_id)
    assert stake.status == "unstaked"


@pytest.mark.asyncio
async def test_total_staked(engine):
    """Calculate total staked amount."""
    await engine.stake("user_a", "nexus", 1000.0, lock_days=30)
    await engine.stake("user_b", "nexus", 2000.0, lock_days=60)
    await engine.stake("user_c", "svt", 500.0, lock_days=14)

    nexus_staked = await engine.get_total_staked("nexus")
    svt_staked = await engine.get_total_staked("svt")

    assert nexus_staked == 3000.0
    assert svt_staked == 500.0


@pytest.mark.asyncio
async def test_reward_distribution(engine):
    """Distribute rewards to stake positions."""
    success, stake_id = await engine.stake("reward_user", "nexus", 10000.0, lock_days=30)

    # Override created_at to 30 days ago for meaningful rewards
    stake = await engine.get_stake(stake_id)
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
    stake.created_at = thirty_days_ago
    stake.locked_until = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    count = await engine.distribute_all_rewards()
    assert count >= 1

    stake = await engine.get_stake(stake_id)
    # 10000 * 0.12 APY * (30/365) days ≈ 98.63 tokens
    assert stake.rewards_earned > 0

    # Check rewards history
    history = await engine.get_rewards_history("reward_user")
    assert len(history) >= 1
    assert history[0].staker_id == "reward_user"


@pytest.mark.asyncio
async def test_auto_compounding(engine):
    """Auto-compound rewards."""
    success, stake_id = await engine.stake(
        "compound_user", "nexus", 10000.0, lock_days=30, auto_compound=True,
    )

    stake = await engine.get_stake(stake_id)
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
    stake.created_at = thirty_days_ago
    stake.locked_until = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    count = await engine.distribute_all_rewards()
    assert count >= 1

    stake = await engine.get_stake(stake_id)
    # With auto-compound, rewards are added to principal (amount)
    assert stake.amount > 10000.0


@pytest.mark.asyncio
async def test_register_validator(engine):
    """Register a validator."""
    validator = await engine.register_validator(
        owner_id="val_owner_001",
        name="Nexus Validator #1",
        self_stake=10000.0,
        commission_rate=0.05,
        description="Primary validator node",
    )
    assert validator.validator_id.startswith("val_")
    assert validator.name == "Nexus Validator #1"
    assert validator.commission_rate == 0.05
    assert validator.total_staked == 10000.0
    assert validator.status == "active"


@pytest.mark.asyncio
async def test_list_validators(engine):
    """List validators."""
    await engine.register_validator("o1", "Validator A", self_stake=5000.0)
    await engine.register_validator("o2", "Validator B", self_stake=10000.0)

    validators = await engine.list_validators()
    assert len(validators) == 2

    # Sorted by total_staked descending
    assert validators[0].name == "Validator B"


@pytest.mark.asyncio
async def test_jail_unjail_validator(engine):
    """Jail and unjail a validator."""
    validator = await engine.register_validator("o_jail", "Jail Test Validator")

    jailed = await engine.jail_validator(validator.validator_id, reason="Downtime")
    assert jailed is True

    v = await engine.get_validator(validator.validator_id)
    assert v.status == "jailed"

    unjailed = await engine.unjail_validator(validator.validator_id)
    assert unjailed is True

    v = await engine.get_validator(validator.validator_id)
    assert v.status == "active"


@pytest.mark.asyncio
async def test_stake_with_validator(engine):
    """Stake to a validator."""
    validator = await engine.register_validator("val_o", "Staking Validator", self_stake=5000.0)

    success, stake_id = await engine.stake(
        "delegator", "nexus", 1000.0, lock_days=30,
        validator_id=validator.validator_id,
    )
    assert success is True

    v = await engine.get_validator(validator.validator_id)
    assert v.total_staked == 6000.0  # 5000 self + 1000 delegated
    assert v.delegator_count == 1


@pytest.mark.asyncio
async def test_slash(engine):
    """Slash a stake position."""
    success, stake_id = await engine.stake("slash_user", "nexus", 1000.0, lock_days=30)

    success, msg = await engine.slash(stake_id, 0.1, reason="Protocol violation")
    assert success is True

    stake = await engine.get_stake(stake_id)
    assert stake.amount == 900.0  # 10% slashed
    assert stake.status == "slashed"
    assert "Protocol violation" in stake.metadata.get("slash_reason", "")


@pytest.mark.asyncio
async def test_slash_invalid_percentage(engine):
    """Slash with invalid percentage."""
    success, stake_id = await engine.stake("slash_inv", "nexus", 100.0, lock_days=7)

    success, msg = await engine.slash(stake_id, 2.0)  # 200%
    assert success is False

    success, msg = await engine.slash(stake_id, -0.1)
    assert success is False


@pytest.mark.asyncio
async def test_get_stats(engine):
    """Get staking statistics."""
    await engine.stake("stat_user1", "nexus", 5000.0, lock_days=30)
    await engine.stake("stat_user2", "nexus", 10000.0, lock_days=90)
    await engine.register_validator("stat_o", "Stat Validator", self_stake=1000.0)

    stats = await engine.get_stats()
    assert stats["total_stake_positions"] >= 2
    assert stats["total_value_staked"] >= 15000.0
    assert stats["total_validators"] >= 1
    assert "30d" in stats["apy_tiers"]
    assert "90d" in stats["apy_tiers"]
    assert stats["apy_tiers"]["30d"]["apy"] == 12.0
    assert stats["apy_tiers"]["90d"]["apy"] == 20.0


@pytest.mark.asyncio
async def test_singleton():
    """Test singleton pattern."""
    e1 = get_staking_engine()
    e2 = get_staking_engine()
    assert e1 is e2

    reset_staking_engine()
    e3 = get_staking_engine()
    assert e3 is not e1


@pytest.mark.asyncio
async def test_persistence(tmp_path, engine):
    """Test JSONL persistence."""
    original_path = engine.LEDGER_PATH
    engine.LEDGER_PATH = str(tmp_path / "test_staking.jsonl")

    await engine.stake("persist_user", "nexus", 5000.0, lock_days=30)
    await engine.register_validator("persist_o", "Persist Validator", self_stake=1000.0)

    engine2 = StakingEngine()
    engine2.LEDGER_PATH = engine.LEDGER_PATH
    await engine2._ensure_loaded()

    stakes = await engine2.get_stakes_for_user("persist_user")
    assert len(stakes) == 1
    assert stakes[0].amount == 5000.0

    validators = await engine2.list_validators()
    assert len(validators) >= 1
    assert validators[0].name == "Persist Validator"
