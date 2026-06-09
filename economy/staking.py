"""
ASIMNEXUS Staking System
=========================
Token staking with lock periods, reward distribution, and validator management.

Supports:
- Stake/unstake with configurable lock periods
- APY-based reward calculation
- Validator registration and delegation
- Reward compounding and distribution
"""

import asyncio
import logging
import json
import uuid
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("StakingSystem")

# ── Types ────────────────────────────────────────────────────────────────────


class StakeStatus(Enum):
    ACTIVE = "active"
    LOCKED = "locked"          # In lock period
    UNSTAKING = "unstaking"    # Awaiting cooldown
    UNSTAKED = "unstaked"      # Fully unstaked
    SLASHED = "slashed"        # Penalty applied


class ValidatorStatus(Enum):
    ACTIVE = "active"
    JAILED = "jailed"          # Temporarily disabled
    INACTIVE = "inactive"
    RETIRED = "retired"


# ── Data Models ──────────────────────────────────────────────────────────────


@dataclass
class StakePosition:
    """A user's staking position."""
    stake_id: str
    staker_id: str
    token_type: str
    amount: float
    rewards_earned: float = 0.0
    rewards_claimed: float = 0.0
    apy_at_stake: float = 0.0
    status: str = "active"
    lock_days: int = 30
    created_at: str = ""
    locked_until: Optional[str] = None
    unstaked_at: Optional[str] = None
    validator_id: Optional[str] = None
    auto_compound: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_value(self) -> float:
        return self.amount + self.rewards_earned - self.rewards_claimed

    @property
    def is_locked(self) -> bool:
        if not self.locked_until:
            return True
        return datetime.utcnow().isoformat() < self.locked_until

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StakePosition":
        return cls(**data)


@dataclass
class Validator:
    """A network validator."""
    validator_id: str
    owner_id: str
    name: str
    commission_rate: float = 0.05  # 5% default
    total_staked: float = 0.0
    self_stake: float = 0.0
    delegator_count: int = 0
    status: str = "active"
    uptime_percentage: float = 100.0
    created_at: str = ""
    last_active: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Validator":
        return cls(**data)


@dataclass
class RewardDistribution:
    """Record of a reward distribution event."""
    distribution_id: str
    stake_id: str
    staker_id: str
    amount: float
    apy_at_distribution: float = 0.0
    period_start: str = ""
    period_end: str = ""
    timestamp: str = ""
    compounded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RewardDistribution":
        return cls(**data)


# ── Staking Engine ───────────────────────────────────────────────────────────


class StakingEngine:
    """
    Staking engine managing token staking, rewards, and validators.

    Features:
    - Stake tokens with configurable lock periods (7, 14, 30, 60, 90 days)
    - APY tiers based on lock duration
    - Auto-compounding rewards
    - Validator registration and delegation
    - Slashing for malicious behavior
    - Reward distribution scheduling
    """

    LEDGER_PATH = "data/staking_ledger.jsonl"
    DEFAULT_APY_TIERS = {
        7: 0.05,    # 5% APY for 7-day lock
        14: 0.08,   # 8% APY for 14-day lock
        30: 0.12,   # 12% APY for 30-day lock
        60: 0.15,   # 15% APY for 60-day lock
        90: 0.20,   # 20% APY for 90-day lock
    }
    MIN_STAKE = 10.0
    UNSTAKE_COOLDOWN_DAYS = 3

    def __init__(self):
        self._stakes: Dict[str, StakePosition] = {}
        self._validators: Dict[str, Validator] = {}
        self._distributions: List[RewardDistribution] = []
        self._lock = asyncio.Lock()
        self._loaded = False

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def _ensure_loaded(self):
        if not self._loaded:
            await self._load_ledger()
            self._loaded = True

    async def _load_ledger(self):
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        if not ledger.exists():
            ledger.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            for line in ledger.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    etype = entry.get("_type", "")
                    data = entry["data"]
                    if etype == "stake":
                        s = StakePosition.from_dict(data)
                        self._stakes[s.stake_id] = s
                    elif etype == "validator":
                        v = Validator.from_dict(data)
                        self._validators[v.validator_id] = v
                    elif etype == "distribution":
                        d = RewardDistribution.from_dict(data)
                        self._distributions.append(d)
                except (json.JSONDecodeError, KeyError):
                    continue
            logger.info(f"Loaded {len(self._stakes)} stakes, {len(self._validators)} validators")
        except Exception as e:
            logger.error(f"Failed to load staking ledger: {e}")

    async def _append_ledger(self, entry_type: str, data: dict):
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        record = json.dumps({"_type": entry_type, "data": data, "_ts": datetime.utcnow().isoformat()})
        async with self._lock:
            with ledger.open("a") as f:
                f.write(record + "\n")

    # ── Staking Operations ───────────────────────────────────────────────

    async def stake(
        self,
        staker_id: str,
        token_type: str,
        amount: float,
        lock_days: int = 30,
        auto_compound: bool = False,
        validator_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """Stake tokens with a lock period."""
        if amount < self.MIN_STAKE:
            return False, f"Minimum stake is {self.MIN_STAKE}"
        if lock_days not in self.DEFAULT_APY_TIERS:
            return False, f"Invalid lock period {lock_days}d. Options: {list(self.DEFAULT_APY_TIERS.keys())}"

        await self._ensure_loaded()

        # Validate validator if specified
        if validator_id:
            validator = await self.get_validator(validator_id)
            if not validator:
                return False, "Validator not found"
            if validator.status != "active":
                return False, f"Validator is {validator.status}"

        now = datetime.utcnow()
        locked_until = (now + timedelta(days=lock_days)).isoformat()
        apy = self.DEFAULT_APY_TIERS[lock_days]

        stake = StakePosition(
            stake_id=f"stk_{uuid.uuid4().hex[:16]}",
            staker_id=staker_id,
            token_type=token_type,
            amount=amount,
            apy_at_stake=apy,
            status="locked",
            lock_days=lock_days,
            created_at=now.isoformat(),
            locked_until=locked_until,
            validator_id=validator_id,
            auto_compound=auto_compound,
            metadata=metadata or {},
        )

        async with self._lock:
            self._stakes[stake.stake_id] = stake

        # Update validator total staked
        if validator_id and validator:
            validator.total_staked += amount
            validator.delegator_count += 1
            await self._append_ledger("validator", validator.to_dict())

        await self._append_ledger("stake", stake.to_dict())
        logger.info(f"Stake {stake.stake_id}: {amount} {token_type} for {lock_days}d @ {apy*100}% APY")
        return True, stake.stake_id

    async def unstake(self, stake_id: str, staker_id: str) -> Tuple[bool, str]:
        """Initiate unstaking (enters cooldown period)."""
        stake = await self.get_stake(stake_id)
        if not stake:
            return False, "Stake position not found"
        if stake.staker_id != staker_id:
            return False, "Not the stake owner"
        if stake.status not in ("active", "locked"):
            return False, f"Cannot unstake position with status {stake.status}"

        # Check if still in lock period
        if stake.is_locked:
            return False, f"Still locked until {stake.locked_until}"

        now = datetime.utcnow()
        stake.status = "unstaking"
        stake.unstaked_at = (now + timedelta(days=self.UNSTAKE_COOLDOWN_DAYS)).isoformat()

        # Distribute any pending rewards first
        pending = await self._calculate_pending_rewards(stake)
        if pending > 0:
            await self._distribute_rewards(stake, pending)

        await self._append_ledger("stake", stake.to_dict())
        logger.info(f"Stake {stake_id} entering unstaking cooldown ({self.UNSTAKE_COOLDOWN_DAYS}d)")
        return True, stake_id

    async def claim_unstaked(self, stake_id: str, staker_id: str) -> Tuple[bool, str]:
        """Claim tokens after unstaking cooldown."""
        stake = await self.get_stake(stake_id)
        if not stake:
            return False, "Stake position not found"
        if stake.staker_id != staker_id:
            return False, "Not the stake owner"
        if stake.status != "unstaking":
            return False, f"Position is {stake.status}, not unstaking"
        if not stake.unstaked_at or datetime.utcnow().isoformat() < stake.unstaked_at:
            return False, f"Cooldown period not over until {stake.unstaked_at}"

        total_return = stake.amount + stake.rewards_earned - stake.rewards_claimed
        stake.status = "unstaked"
        stake.rewards_claimed = stake.rewards_earned  # Mark all as claimed

        # Update validator if applicable
        if stake.validator_id:
            validator = await self.get_validator(stake.validator_id)
            if validator:
                validator.total_staked = max(0, validator.total_staked - stake.amount)
                validator.delegator_count = max(0, validator.delegator_count - 1)
                await self._append_ledger("validator", validator.to_dict())

        await self._append_ledger("stake", stake.to_dict())
        logger.info(f"Stake {stake_id} claimed: {total_return} {stake.token_type}")
        return True, stake_id

    async def get_stake(self, stake_id: str) -> Optional[StakePosition]:
        """Get a stake position by ID."""
        await self._ensure_loaded()
        return self._stakes.get(stake_id)

    async def get_stakes_for_user(
        self,
        staker_id: str,
        status: Optional[str] = None,
    ) -> List[StakePosition]:
        """Get all stakes for a user."""
        await self._ensure_loaded()
        results = [s for s in self._stakes.values() if s.staker_id == staker_id]
        if status:
            results = [s for s in results if s.status == status]
        results.sort(key=lambda s: s.created_at, reverse=True)
        return results

    async def get_total_staked(self, token_type: str = "nexus") -> float:
        """Get total amount staked for a token type."""
        await self._ensure_loaded()
        return sum(
            s.amount for s in self._stakes.values()
            if s.token_type == token_type and s.status in ("active", "locked", "unstaking")
        )

    # ── Rewards ──────────────────────────────────────────────────────────

    async def _calculate_pending_rewards(self, stake: StakePosition) -> float:
        """Calculate pending rewards for a stake position."""
        if stake.status == "unstaked":
            return 0.0

        now = datetime.utcnow()
        created = datetime.fromisoformat(stake.created_at)
        days_staked = max(0, (now - created).days)

        # Simple linear APY calculation
        annual_reward = stake.amount * stake.apy_at_stake
        daily_reward = annual_reward / 365.0
        total_earned = daily_reward * days_staked

        # Subtract already claimed
        pending = total_earned - stake.rewards_claimed
        return max(0, round(pending, 6))

    async def _distribute_rewards(self, stake: StakePosition, amount: float) -> RewardDistribution:
        """Distribute rewards to a stake position."""
        now = datetime.utcnow()

        distribution = RewardDistribution(
            distribution_id=f"dist_{uuid.uuid4().hex[:16]}",
            stake_id=stake.stake_id,
            staker_id=stake.staker_id,
            amount=amount,
            apy_at_distribution=stake.apy_at_stake,
            period_start=stake.created_at,
            period_end=now.isoformat(),
            timestamp=now.isoformat(),
        )

        if stake.auto_compound:
            # Auto-compound: add rewards to principal
            stake.amount += amount
            stake.rewards_claimed += amount
            distribution.compounded = True
        else:
            stake.rewards_earned += amount

        async with self._lock:
            self._distributions.append(distribution)
        await self._append_ledger("distribution", distribution.to_dict())
        await self._append_ledger("stake", stake.to_dict())

        return distribution

    async def distribute_all_rewards(self) -> int:
        """Distribute rewards to all eligible stakes. Returns count."""
        await self._ensure_loaded()
        count = 0
        for stake in list(self._stakes.values()):
            if stake.status in ("active", "locked"):
                pending = await self._calculate_pending_rewards(stake)
                if pending >= 0.000001:  # Minimum 1 microtoken
                    await self._distribute_rewards(stake, pending)
                    count += 1

        if count > 0:
            logger.info(f"Distributed rewards to {count} stake positions")
        return count

    async def get_rewards_history(
        self, staker_id: str, limit: int = 50
    ) -> List[RewardDistribution]:
        """Get reward distribution history for a user."""
        await self._ensure_loaded()
        results = [d for d in self._distributions if d.staker_id == staker_id]
        results.sort(key=lambda d: d.timestamp, reverse=True)
        return results[:limit]

    # ── Validators ───────────────────────────────────────────────────────

    async def register_validator(
        self,
        owner_id: str,
        name: str,
        self_stake: float = 0.0,
        commission_rate: float = 0.05,
        description: str = "",
        metadata: Optional[Dict] = None,
    ) -> Validator:
        """Register a new validator node."""
        if commission_rate < 0 or commission_rate > 1:
            raise ValueError("Commission rate must be between 0 and 1")

        await self._ensure_loaded()
        now = datetime.utcnow()

        validator = Validator(
            validator_id=f"val_{uuid.uuid4().hex[:16]}",
            owner_id=owner_id,
            name=name,
            commission_rate=commission_rate,
            self_stake=self_stake,
            total_staked=self_stake,
            status="active",
            created_at=now.isoformat(),
            last_active=now.isoformat(),
            description=description,
            metadata=metadata or {},
        )

        async with self._lock:
            self._validators[validator.validator_id] = validator
        await self._append_ledger("validator", validator.to_dict())
        logger.info(f"Validator {validator.validator_id} registered: {name}")
        return validator

    async def get_validator(self, validator_id: str) -> Optional[Validator]:
        """Get a validator by ID."""
        await self._ensure_loaded()
        return self._validators.get(validator_id)

    async def list_validators(
        self, status: Optional[str] = None
    ) -> List[Validator]:
        """List all validators, optionally filtered by status."""
        await self._ensure_loaded()
        results = list(self._validators.values())
        if status:
            results = [v for v in results if v.status == status]
        results.sort(key=lambda v: v.total_staked, reverse=True)
        return results

    async def jail_validator(self, validator_id: str, reason: str = "") -> bool:
        """Jail a validator (temporarily disable)."""
        validator = await self.get_validator(validator_id)
        if not validator:
            return False
        validator.status = "jailed"
        validator.metadata["jail_reason"] = reason
        validator.metadata["jailed_at"] = datetime.utcnow().isoformat()
        await self._append_ledger("validator", validator.to_dict())
        logger.info(f"Validator {validator_id} jailed: {reason}")
        return True

    async def unjail_validator(self, validator_id: str) -> bool:
        """Unjail a validator."""
        validator = await self.get_validator(validator_id)
        if not validator or validator.status != "jailed":
            return False
        validator.status = "active"
        await self._append_ledger("validator", validator.to_dict())
        logger.info(f"Validator {validator_id} unjailed")
        return True

    # ── Slashing ─────────────────────────────────────────────────────────

    async def slash(
        self,
        stake_id: str,
        slash_percentage: float,
        reason: str = "",
    ) -> Tuple[bool, str]:
        """Slash a stake position (penalty)."""
        if slash_percentage <= 0 or slash_percentage > 1:
            return False, "Slash percentage must be between 0 and 1"

        stake = await self.get_stake(stake_id)
        if not stake:
            return False, "Stake position not found"
        if stake.status == "unstaked":
            return False, "Cannot slash unstaked position"

        slash_amount = round(stake.amount * slash_percentage, 6)
        stake.amount -= slash_amount
        stake.status = "slashed"
        stake.metadata["slashed_amount"] = slash_amount
        stake.metadata["slash_reason"] = reason
        stake.metadata["slashed_at"] = datetime.utcnow().isoformat()

        await self._append_ledger("stake", stake.to_dict())
        logger.warning(f"Stake {stake_id} slashed: {slash_amount} ({slash_percentage*100}%) - {reason}")
        return True, stake_id

    # ── Maintenance ──────────────────────────────────────────────────────

    async def unlock_stakes(self) -> List[str]:
        """Transition 'locked' stakes to 'active' when lock expires."""
        await self._ensure_loaded()
        now = datetime.utcnow().isoformat()
        unlocked = []
        for s in self._stakes.values():
            if s.status == "locked" and s.locked_until and s.locked_until <= now:
                s.status = "active"
                await self._append_ledger("stake", s.to_dict())
                unlocked.append(s.stake_id)
        if unlocked:
            logger.info(f"Unlocked {len(unlocked)} stakes")
        return unlocked

    # ── Stats ────────────────────────────────────────────────────────────

    async def get_stats(self) -> Dict[str, Any]:
        """Get staking system statistics."""
        await self._ensure_loaded()
        active_stakes = sum(1 for s in self._stakes.values() if s.status in ("active", "locked"))
        total_staked = sum(s.amount for s in self._stakes.values() if s.status in ("active", "locked", "unstaking"))
        total_rewards_distributed = sum(d.amount for d in self._distributions)

        apy_stats = {}
        for days, apy in self.DEFAULT_APY_TIERS.items():
            stakes_in_tier = [
                s for s in self._stakes.values()
                if s.lock_days == days and s.status in ("active", "locked")
            ]
            apy_stats[f"{days}d"] = {
                "apy": apy * 100,
                "stakers": len(stakes_in_tier),
                "total_staked": sum(s.amount for s in stakes_in_tier),
            }

        return {
            "total_stake_positions": len(self._stakes),
            "active_stakes": active_stakes,
            "total_value_staked": total_staked,
            "total_rewards_distributed": total_rewards_distributed,
            "total_validators": len(self._validators),
            "active_validators": sum(1 for v in self._validators.values() if v.status == "active"),
            "apy_tiers": apy_stats,
            "min_stake": self.MIN_STAKE,
            "unstake_cooldown_days": self.UNSTAKE_COOLDOWN_DAYS,
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_engine: Optional[StakingEngine] = None


def get_staking_engine() -> StakingEngine:
    """Get or create the singleton staking engine."""
    global _engine
    if _engine is None:
        _engine = StakingEngine()
    return _engine


def reset_staking_engine():
    """Reset the staking engine (for testing)."""
    global _engine
    _engine = None
