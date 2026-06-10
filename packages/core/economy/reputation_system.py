"""
ASIMNEXUS Reputation System with Staking
=========================================
Full REAL implementation with JSONL persistence.
Tracks entity reputation, level progression, staking, slashing.

Features:
- Entity registration with initial NEW level
- Reputation scoring with level progression
- Staking/unstaking reputation as collateral
- Slashing for malicious behavior
- Leaderboard with configurable limits
- JSONL persistence
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger("ReputationSystem")

REPUTATION_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "reputation.jsonl"
REPUTATION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class ReputationLevel(Enum):
    NEW = "new"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


@dataclass
class ReputationScore:
    entity_id: str
    score: float
    level: str
    staked_amount: float
    total_earned: float
    total_lost: float
    last_updated: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReputationScore":
        return cls(**data)


@dataclass
class StakeRecord:
    stake_id: str
    entity_id: str
    amount: float
    staked_at: str
    unstaked_at: Optional[str] = None
    slashed: bool = False
    slashed_amount: float = 0.0
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StakeRecord":
        return cls(**data)


@dataclass
class ReputationEvent:
    event_id: str
    entity_id: str
    event_type: str
    amount: float
    balance_after: float
    reason: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReputationEvent":
        return cls(**data)


class ReputationSystem:
    LEVEL_THRESHOLDS: Dict[ReputationLevel, float] = {
        ReputationLevel.NEW: 0,
        ReputationLevel.BRONZE: 100,
        ReputationLevel.SILVER: 500,
        ReputationLevel.GOLD: 2000,
        ReputationLevel.PLATINUM: 10000,
        ReputationLevel.DIAMOND: 50000,
    }

    def __init__(self):
        self.scores: Dict[str, ReputationScore] = {}
        self.stakes: Dict[str, StakeRecord] = {}
        self.events: List[ReputationEvent] = []
        self._load_from_db()

    def _persist(self, entry_type: str, data: Dict[str, Any]) -> None:
        try:
            record = {"__type__": entry_type, **data}
            with open(REPUTATION_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Persist failed: {e}")

    def _load_from_db(self) -> None:
        path = REPUTATION_DB_PATH
        if not path.exists():
            logger.info("⭐ Reputation System initialized (no existing data)")
            return
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    entry_type = data.pop("__type__", None)
                    if entry_type == "score":
                        s = ReputationScore.from_dict(data)
                        self.scores[s.entity_id] = s
                    elif entry_type == "stake":
                        st = StakeRecord.from_dict(data)
                        self.stakes[st.stake_id] = st
                    elif entry_type == "event":
                        ev = ReputationEvent.from_dict(data)
                        self.events.append(ev)
            logger.info(f"⭐ Loaded {len(self.scores)} entities, {len(self.stakes)} stakes")
        except Exception as e:
            logger.warning(f"Failed to load reputation: {e}")

    def register_entity(self, entity_id: str, initial_score: float = 0.0) -> ReputationScore:
        if entity_id in self.scores:
            return self.scores[entity_id]
        score = ReputationScore(
            entity_id=entity_id,
            score=initial_score,
            level=ReputationLevel.NEW.value,
            staked_amount=0.0,
            total_earned=initial_score,
            total_lost=0.0,
            last_updated=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
        )
        self.scores[entity_id] = score
        self._persist("score", score.to_dict())
        self._add_event(entity_id, "registration", initial_score, initial_score, "Entity registered")
        logger.info(f"✅ Entity registered: {entity_id}")
        return score

    def add_reputation(self, entity_id: str, amount: float, reason: str = "") -> Optional[ReputationScore]:
        if entity_id not in self.scores:
            return None
        if amount <= 0:
            return None
        score = self.scores[entity_id]
        score.score += amount
        score.total_earned += amount
        score.last_updated = datetime.utcnow().isoformat()
        self._update_level(entity_id)
        self._persist("score", score.to_dict())
        self._add_event(entity_id, "add", amount, score.score, reason)
        logger.info(f"⭐ Added {amount} reputation to {entity_id} — now {score.score}")
        return score

    def remove_reputation(self, entity_id: str, amount: float, reason: str = "") -> Optional[ReputationScore]:
        if entity_id not in self.scores:
            return None
        if amount <= 0:
            return None
        score = self.scores[entity_id]
        actual = min(amount, score.score)
        score.score -= actual
        score.total_lost += actual
        score.last_updated = datetime.utcnow().isoformat()
        self._update_level(entity_id)
        self._persist("score", score.to_dict())
        self._add_event(entity_id, "remove", -actual, score.score, reason)
        logger.info(f"⬇️ Removed {actual} reputation from {entity_id} — now {score.score}")
        return score

    def _update_level(self, entity_id: str) -> None:
        if entity_id not in self.scores:
            return
        score = self.scores[entity_id].score
        new_level = ReputationLevel.NEW.value
        for level, threshold in sorted(
            self.LEVEL_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        ):
            if score >= threshold:
                new_level = level.value
                break
        self.scores[entity_id].level = new_level

    def stake(self, entity_id: str, amount: float, reason: str = "") -> Optional[StakeRecord]:
        if entity_id not in self.scores:
            return None
        if amount <= 0:
            return None
        score = self.scores[entity_id]
        if score.score < amount:
            return None
        score.score -= amount
        score.staked_amount += amount
        score.last_updated = datetime.utcnow().isoformat()
        stake = StakeRecord(
            stake_id=f"stake_{uuid.uuid4().hex[:12]}",
            entity_id=entity_id,
            amount=amount,
            staked_at=datetime.utcnow().isoformat(),
            reason=reason,
        )
        self.stakes[stake.stake_id] = stake
        self._persist("score", score.to_dict())
        self._persist("stake", stake.to_dict())
        self._add_event(entity_id, "stake", -amount, score.score, f"Staked {amount}: {reason}")
        logger.info(f"🔒 Staked {amount} reputation for {entity_id}")
        return stake

    def unstake(self, stake_id: str) -> Optional[StakeRecord]:
        if stake_id not in self.stakes:
            return None
        stake = self.stakes[stake_id]
        if stake.unstaked_at is not None:
            return None
        if stake.entity_id not in self.scores:
            return None
        score = self.scores[stake.entity_id]
        score.score += stake.amount
        score.staked_amount -= stake.amount
        score.last_updated = datetime.utcnow().isoformat()
        stake.unstaked_at = datetime.utcnow().isoformat()
        self._persist("score", score.to_dict())
        self._persist("stake", stake.to_dict())
        self._add_event(stake.entity_id, "unstake", stake.amount, score.score,
                        f"Unstaked {stake.amount}")
        logger.info(f"🔓 Unstaked {stake.amount} reputation for {stake.entity_id}")
        return stake

    def slash(self, stake_id: str, penalty_pct: float = 1.0, reason: str = "") -> Optional[StakeRecord]:
        if stake_id not in self.stakes:
            return None
        stake = self.stakes[stake_id]
        if stake.unstaked_at is not None:
            return None
        if stake.entity_id not in self.scores:
            return None
        slash_amount = round(stake.amount * min(penalty_pct, 1.0), 2)
        stake.amount -= slash_amount
        stake.slashed = True
        stake.slashed_amount += slash_amount
        self.scores[stake.entity_id].staked_amount -= slash_amount
        self.scores[stake.entity_id].total_lost += slash_amount
        self.scores[stake.entity_id].last_updated = datetime.utcnow().isoformat()
        self._persist("score", self.scores[stake.entity_id].to_dict())
        self._persist("stake", stake.to_dict())
        self._add_event(stake.entity_id, "slash", -slash_amount,
                        self.scores[stake.entity_id].score, f"Slashed {slash_amount}: {reason}")
        logger.warning(f"⚔️ Slashed {slash_amount} from {stake.entity_id}: {reason}")
        return stake

    def _add_event(self, entity_id: str, event_type: str, amount: float,
                   balance_after: float, reason: str = "") -> None:
        ev = ReputationEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            entity_id=entity_id,
            event_type=event_type,
            amount=amount,
            balance_after=balance_after,
            reason=reason,
            timestamp=datetime.utcnow().isoformat(),
        )
        self.events.append(ev)
        self._persist("event", ev.to_dict())

    def get_reputation(self, entity_id: str) -> Optional[Dict[str, Any]]:
        s = self.scores.get(entity_id)
        if not s:
            return None
        return s.to_dict()

    def get_entity_events(self, entity_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        result = [e.to_dict() for e in self.events if e.entity_id == entity_id]
        result.sort(key=lambda x: x["timestamp"], reverse=True)
        return result[:limit]

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_scores = sorted(
            self.scores.values(),
            key=lambda x: x.score,
            reverse=True,
        )
        return [s.to_dict() for s in sorted_scores[:limit]]

    def get_system_stats(self) -> Dict[str, Any]:
        level_counts = {}
        for s in self.scores.values():
            level_counts[s.level] = level_counts.get(s.level, 0) + 1
        total_staked = sum(s.staked_amount for s in self.scores.values())
        total_earned_all = sum(s.total_earned for s in self.scores.values())
        active_stakes = sum(1 for s in self.stakes.values() if s.unstaked_at is None)
        total_slashed = sum(s.slashed_amount for s in self.stakes.values())
        return {
            "total_entities": len(self.scores),
            "level_distribution": level_counts,
            "total_staked": total_staked,
            "active_stakes": active_stakes,
            "total_stakes": len(self.stakes),
            "total_slashed": total_slashed,
            "total_earned_all": total_earned_all,
            "total_events": len(self.events),
            "average_score": round(sum(s.score for s in self.scores.values()) / max(len(self.scores), 1), 2),
        }


_reputation_system: Optional[ReputationSystem] = None


def get_reputation_system() -> ReputationSystem:
    global _reputation_system
    if _reputation_system is None:
        _reputation_system = ReputationSystem()
    return _reputation_system


def reset_reputation_system() -> None:
    global _reputation_system
    _reputation_system = None
