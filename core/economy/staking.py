"""
AsimNexus — Staking Engine
===========================
Manages staking operations, validators, and reward distributions.
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any


LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "staking_ledger.jsonl"
)

VALIDATOR_LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "staking_validators.jsonl"
)

REWARDS_LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "staking_rewards.jsonl"
)


class StakeStatus(str, Enum):
    LOCKED = "locked"
    ACTIVE = "active"
    UNSTAKING = "unstaking"
    UNSTAKED = "unstaked"
    SLASHED = "slashed"


class ValidatorStatus(str, Enum):
    ACTIVE = "active"
    JAILED = "jailed"
    INACTIVE = "inactive"


# APY tiers based on lock duration
APY_TIERS = {
    7: 0.05,    # 5% for 7 days
    14: 0.08,   # 8% for 14 days
    30: 0.12,   # 12% for 30 days
    60: 0.15,   # 15% for 60 days
    90: 0.20,   # 20% for 90 days
}

MINIMUM_STAKE = 10.0
UNSTAKE_COOLDOWN_HOURS = 0


@dataclass
class StakePosition:
    stake_id: str
    staker_id: str
    token_type: str
    amount: float
    lock_days: int
    status: str = "locked"
    validator_id: Optional[str] = None
    auto_compound: bool = False
    apy_at_stake: float = 0.0
    rewards_earned: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    locked_until: Optional[str] = None
    unstaked_at: Optional[str] = None

    def __post_init__(self):
        if self.locked_until is None:
            self.locked_until = (
                datetime.utcnow() + timedelta(days=self.lock_days)
            ).isoformat()
        if self.apy_at_stake == 0.0:
            self.apy_at_stake = APY_TIERS.get(self.lock_days, 0.05)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stake_id": self.stake_id,
            "staker_id": self.staker_id,
            "token_type": self.token_type,
            "amount": self.amount,
            "lock_days": self.lock_days,
            "status": self.status,
            "validator_id": self.validator_id,
            "auto_compound": self.auto_compound,
            "apy_at_stake": self.apy_at_stake,
            "rewards_earned": self.rewards_earned,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "locked_until": self.locked_until,
            "unstaked_at": self.unstaked_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StakePosition":
        return cls(
            stake_id=data["stake_id"],
            staker_id=data["staker_id"],
            token_type=data["token_type"],
            amount=data["amount"],
            lock_days=data["lock_days"],
            status=data.get("status", "locked"),
            validator_id=data.get("validator_id"),
            auto_compound=data.get("auto_compound", False),
            apy_at_stake=data.get("apy_at_stake", 0.0),
            rewards_earned=data.get("rewards_earned", 0.0),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            locked_until=data.get("locked_until"),
            unstaked_at=data.get("unstaked_at"),
        )


@dataclass
class Validator:
    validator_id: str
    owner_id: str
    name: str
    commission_rate: float = 0.1
    description: str = ""
    status: str = "active"
    total_staked: float = 0.0
    delegator_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validator_id": self.validator_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "commission_rate": self.commission_rate,
            "description": self.description,
            "status": self.status,
            "total_staked": self.total_staked,
            "delegator_count": self.delegator_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Validator":
        return cls(
            validator_id=data["validator_id"],
            owner_id=data["owner_id"],
            name=data["name"],
            commission_rate=data.get("commission_rate", 0.1),
            description=data.get("description", ""),
            status=data.get("status", "active"),
            total_staked=data.get("total_staked", 0.0),
            delegator_count=data.get("delegator_count", 0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


@dataclass
class RewardDistribution:
    distribution_id: str
    stake_id: str
    staker_id: str
    amount: float
    token_type: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "distribution_id": self.distribution_id,
            "stake_id": self.stake_id,
            "staker_id": self.staker_id,
            "amount": self.amount,
            "token_type": self.token_type,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RewardDistribution":
        return cls(
            distribution_id=data["distribution_id"],
            stake_id=data["stake_id"],
            staker_id=data["staker_id"],
            amount=data["amount"],
            token_type=data["token_type"],
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


class StakingEngine:
    """Manages staking operations."""

    LEDGER_PATH = LEDGER_PATH

    def __init__(self):
        self._stakes: Dict[str, StakePosition] = {}
        self._validators: Dict[str, Validator] = {}
        self._rewards: List[RewardDistribution] = []
        self._lock = threading.Lock()
        self._load()

    async def stake(
        self,
        staker_id: str,
        token_type: str,
        amount: float,
        lock_days: int = 30,
        validator_id: Optional[str] = None,
        auto_compound: bool = False,
    ) -> tuple:
        """Stake tokens."""
        if amount < MINIMUM_STAKE:
            return (False, f"Amount below minimum of {MINIMUM_STAKE}")
        if lock_days not in APY_TIERS:
            return (False, "Invalid lock period")

        apy = APY_TIERS.get(lock_days, 0.05)
        stake = StakePosition(
            stake_id=f"stk_{uuid.uuid4().hex[:16]}",
            staker_id=staker_id,
            token_type=token_type,
            amount=amount,
            lock_days=lock_days,
            validator_id=validator_id,
            auto_compound=auto_compound,
            apy_at_stake=apy,
        )
        with self._lock:
            self._stakes[stake.stake_id] = stake
            self._persist(stake)
            # Update validator total staked
            if validator_id and validator_id in self._validators:
                v = self._validators[validator_id]
                v.total_staked += amount
                v.delegator_count += 1
                self._persist_validator(v)
        return (True, stake.stake_id)

    async def get_stake(self, stake_id: str) -> Optional[StakePosition]:
        """Get stake by ID."""
        with self._lock:
            return self._stakes.get(stake_id)

    async def list_stakes(self, staker_id: Optional[str] = None) -> List[StakePosition]:
        """List stakes with optional filter."""
        with self._lock:
            if staker_id:
                return [s for s in self._stakes.values() if s.staker_id == staker_id]
            return list(self._stakes.values())

    async def get_stakes_for_user(
        self, user_id: str, status: Optional[str] = None
    ) -> List[StakePosition]:
        """Get stakes for a user, optionally filtered by status."""
        with self._lock:
            results = [s for s in self._stakes.values() if s.staker_id == user_id]
        if status:
            results = [s for s in results if s.status == status]
        return results

    async def unstake(self, stake_id: str, user_id: str) -> tuple:
        """Initiate unstaking process."""
        with self._lock:
            stake = self._stakes.get(stake_id)
            if not stake:
                return (False, "Stake not found")
            if stake.staker_id != user_id:
                return (False, "Unauthorized")
            if stake.status == "locked":
                # Check if lock period has expired
                if stake.locked_until:
                    try:
                        locked_until = datetime.fromisoformat(stake.locked_until)
                        if datetime.utcnow() < locked_until:
                            return (False, "Stake is still locked")
                    except (ValueError, TypeError):
                        return (False, "Invalid lock date")
            if stake.status not in ("locked", "active"):
                return (False, "Stake not in unstakable state")
            stake.status = "unstaking"
            stake.unstaked_at = datetime.utcnow().isoformat()
            self._persist(stake)
        return (True, "Unstaking initiated")

    async def unlock_stakes(self) -> List[str]:
        """Transition locked stakes to active if lock period has expired."""
        unlocked = []
        now = datetime.utcnow()
        with self._lock:
            for stake_id, stake in self._stakes.items():
                if stake.status == "locked" and stake.locked_until:
                    try:
                        locked_until = datetime.fromisoformat(stake.locked_until)
                        if now >= locked_until:
                            stake.status = "active"
                            self._persist(stake)
                            unlocked.append(stake_id)
                    except (ValueError, TypeError):
                        pass
        return unlocked

    async def claim_unstaked(self, stake_id: str, user_id: str) -> tuple:
        """Claim tokens after unstaking cooldown."""
        with self._lock:
            stake = self._stakes.get(stake_id)
            if not stake:
                return (False, "Stake not found")
            if stake.staker_id != user_id:
                return (False, "Unauthorized")
            if stake.status != "unstaking":
                return (False, "Stake not in unstaking state")
            if stake.unstaked_at:
                try:
                    unstaked_at = datetime.fromisoformat(stake.unstaked_at)
                    cooldown_end = unstaked_at + timedelta(hours=UNSTAKE_COOLDOWN_HOURS)
                    if datetime.utcnow() < cooldown_end:
                        return (False, "Cooldown period not yet passed")
                except (ValueError, TypeError):
                    return (False, "Invalid unstake date")
            stake.status = "unstaked"
            self._persist(stake)
        return (True, "Tokens claimed")

    async def get_total_staked(self, token_type: Optional[str] = None) -> float:
        """Calculate total staked amount, optionally filtered by token type."""
        with self._lock:
            total = 0.0
            for s in self._stakes.values():
                if s.status in ("locked", "active", "unstaking"):
                    if token_type is None or s.token_type == token_type:
                        total += s.amount
        return total

    async def register_validator(
        self,
        owner_id: str,
        name: str,
        self_stake: float = 0.0,
        commission_rate: float = 0.1,
        description: str = "",
    ) -> Validator:
        """Register a validator."""
        validator = Validator(
            validator_id=f"val_{uuid.uuid4().hex[:16]}",
            owner_id=owner_id,
            name=name,
            commission_rate=commission_rate,
            description=description,
            total_staked=self_stake,
        )
        with self._lock:
            self._validators[validator.validator_id] = validator
            self._persist_validator(validator)
        return validator

    async def get_validator(self, validator_id: str) -> Optional[Validator]:
        """Get validator by ID."""
        with self._lock:
            return self._validators.get(validator_id)

    async def list_validators(self) -> List[Validator]:
        """List all validators, sorted by total_staked descending."""
        with self._lock:
            return sorted(
                list(self._validators.values()),
                key=lambda v: v.total_staked,
                reverse=True,
            )

    async def jail_validator(self, validator_id: str, reason: str = "") -> bool:
        """Jail a validator."""
        with self._lock:
            validator = self._validators.get(validator_id)
            if not validator:
                return False
            validator.status = "jailed"
            self._persist_validator(validator)
        return True

    async def unjail_validator(self, validator_id: str) -> bool:
        """Unjail a validator."""
        with self._lock:
            validator = self._validators.get(validator_id)
            if not validator:
                return False
            validator.status = "active"
            self._persist_validator(validator)
        return True

    async def distribute_rewards(
        self, validator_id: Optional[str] = None
    ) -> int:
        """Distribute rewards to stakers."""
        count = 0
        now = datetime.utcnow()
        with self._lock:
            for stake in self._stakes.values():
                if stake.status not in ("locked", "active"):
                    continue
                if validator_id and stake.validator_id != validator_id:
                    continue
                try:
                    created_at = datetime.fromisoformat(stake.created_at)
                    days_staked = (now - created_at).days
                    if days_staked < 1:
                        continue
                    # Calculate reward: amount * APY * (days/365)
                    reward = stake.amount * stake.apy_at_stake * (days_staked / 365.0)
                    if reward > 0:
                        if stake.auto_compound:
                            stake.amount += reward
                        stake.rewards_earned += reward
                        dist = RewardDistribution(
                            distribution_id=f"dist_{uuid.uuid4().hex[:16]}",
                            stake_id=stake.stake_id,
                            staker_id=stake.staker_id,
                            amount=reward,
                            token_type=stake.token_type,
                        )
                        self._rewards.append(dist)
                        self._persist(stake)
                        self._persist_reward(dist)
                        count += 1
                except (ValueError, TypeError):
                    pass
        return count

    async def distribute_all_rewards(self) -> int:
        """Distribute rewards to all stakers."""
        return await self.distribute_rewards()

    async def get_rewards_history(self, staker_id: str) -> List[RewardDistribution]:
        """Get rewards history for a staker."""
        with self._lock:
            return [r for r in self._rewards if r.staker_id == staker_id]

    async def slash(
        self, stake_id: str, percentage: float, reason: str = ""
    ) -> tuple:
        """Slash a stake position."""
        if percentage <= 0 or percentage > 1.0:
            return (False, "Invalid slash percentage (must be between 0 and 1)")
        with self._lock:
            stake = self._stakes.get(stake_id)
            if not stake:
                return (False, "Stake not found")
            slash_amount = stake.amount * percentage
            stake.amount -= slash_amount
            stake.status = "slashed"
            stake.metadata["slash_reason"] = reason
            self._persist(stake)
        return (True, f"Slashed {percentage*100:.0f}%")

    async def get_stats(self) -> Dict[str, Any]:
        """Get staking statistics."""
        with self._lock:
            total_positions = len(self._stakes)
            total_value = sum(
                s.amount for s in self._stakes.values()
                if s.status in ("locked", "active", "unstaking")
            )
            total_validators = len(self._validators)
            total_rewards = sum(
                r.amount for r in self._rewards
            )
            apy_tiers = {}
            for days, apy in APY_TIERS.items():
                apy_tiers[f"{days}d"] = {"apy": apy * 100}  # Return as percentage
            return {
                "total_stake_positions": total_positions,
                "total_value_staked": total_value,
                "total_validators": total_validators,
                "total_rewards_distributed": total_rewards,
                "apy_tiers": apy_tiers,
            }

    async def _ensure_loaded(self) -> None:
        """Ensure data is loaded (for testing)."""
        self._load()

    def _persist(self, stake: StakePosition) -> None:
        try:
            os.makedirs(os.path.dirname(self.LEDGER_PATH), exist_ok=True)
            with open(self.LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(stake.to_dict()) + "\n")
        except Exception:
            pass

    def _persist_validator(self, validator: Validator) -> None:
        try:
            os.makedirs(os.path.dirname(VALIDATOR_LEDGER_PATH), exist_ok=True)
            with open(VALIDATOR_LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(validator.to_dict()) + "\n")
        except Exception:
            pass

    def _persist_reward(self, reward: RewardDistribution) -> None:
        try:
            os.makedirs(os.path.dirname(REWARDS_LEDGER_PATH), exist_ok=True)
            with open(REWARDS_LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(reward.to_dict()) + "\n")
        except Exception:
            pass

    def _load(self) -> None:
        try:
            if os.path.exists(self.LEDGER_PATH):
                with open(self.LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                stake = StakePosition.from_dict(data)
                                self._stakes[stake.stake_id] = stake
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass
        try:
            if os.path.exists(VALIDATOR_LEDGER_PATH):
                with open(VALIDATOR_LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                validator = Validator.from_dict(data)
                                self._validators[validator.validator_id] = validator
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass
        try:
            if os.path.exists(REWARDS_LEDGER_PATH):
                with open(REWARDS_LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                reward = RewardDistribution.from_dict(data)
                                self._rewards.append(reward)
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass


# Singleton support
_staking_engine: Optional[StakingEngine] = None
_staking_engine_lock = threading.Lock()


def get_staking_engine() -> StakingEngine:
    global _staking_engine
    if _staking_engine is None:
        with _staking_engine_lock:
            if _staking_engine is None:
                _staking_engine = StakingEngine()
    return _staking_engine


def reset_staking_engine() -> None:
    global _staking_engine
    _staking_engine = None
