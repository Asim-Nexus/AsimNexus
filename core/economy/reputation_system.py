
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Reputation System with Staking
=========================================
Reputation system with staking mechanism
Includes: Reputation scoring, staking, slashing, rewards
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid
import os

logger = logging.getLogger("ReputationSystem")


class ReputationLevel(Enum):
    """Reputation levels"""
    NEW = "new"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


@dataclass
class ReputationScore:
    """Reputation score for an entity"""
    entity_id: str
    score: float
    level: ReputationLevel
    staked_amount: float
    total_earned: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Stake:
    """Stake record"""
    stake_id: str
    entity_id: str
    amount: float
    staked_at: datetime = field(default_factory=datetime.utcnow)
    unstaked_at: Optional[datetime] = None
    slashed: bool = False


class ReputationSystem:
    """Reputation system with staking"""
    
    def __init__(self):
        self.scores: Dict[str, ReputationScore] = {}
        self.stakes: Dict[str, Stake] = {}
        self.level_thresholds = {
            ReputationLevel.NEW: 0,
            ReputationLevel.BRONZE: 100,
            ReputationLevel.SILVER: 500,
            ReputationLevel.GOLD: 2000,
            ReputationLevel.PLATINUM: 10000,
            ReputationLevel.DIAMOND: 50000
        }
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize reputation system"""
        logger.info("⭐ Initializing Reputation System with Staking...")
        logger.info("📊 Setting up reputation scoring")
        logger.info("💰 Setting up staking mechanism")
        logger.info("⚔️  Setting up slashing")
        logger.info("✅ Reputation System initialized")
    
    def register_entity(self, entity_id: str) -> ReputationScore:
        """Register a new entity"""
        score = ReputationScore(
            entity_id=entity_id,
            score=0.0,
            level=ReputationLevel.NEW,
            staked_amount=0.0
        )
        self.scores[entity_id] = score
        logger.info(f"✅ Registered entity: {entity_id}")
        return score
    
    def add_reputation(self, entity_id: str, amount: float) -> bool:
        """Add reputation to entity"""
        if entity_id not in self.scores:
            return False
        
        self.scores[entity_id].score += amount
        self.scores[entity_id].total_earned += amount
        self._update_level(entity_id)
        
        logger.info(f"✅ Added {amount} reputation to {entity_id}")
        return True
    
    def remove_reputation(self, entity_id: str, amount: float) -> bool:
        """Remove reputation from entity"""
        if entity_id not in self.scores:
            return False
        
        self.scores[entity_id].score = max(0, self.scores[entity_id].score - amount)
        self._update_level(entity_id)
        
        logger.info(f"✅ Removed {amount} reputation from {entity_id}")
        return True
    
    def _update_level(self, entity_id: str) -> None:
        """Update reputation level based on score"""
        if entity_id not in self.scores:
            return
        
        score = self.scores[entity_id].score
        
        for level, threshold in reversed(list(self.level_thresholds.items())):
            if score >= threshold:
                self.scores[entity_id].level = level
                break
    
    def stake_reputation(self, entity_id: str, amount: float) -> bool:
        """Stake reputation"""
        if entity_id not in self.scores or self.scores[entity_id].score < amount:
            return False
        
        self.scores[entity_id].score -= amount
        self.scores[entity_id].staked_amount += amount
        
        stake = Stake(
            stake_id=f"stake_{uuid.uuid4().hex[:8]}",
            entity_id=entity_id,
            amount=amount
        )
        self.stakes[stake.stake_id] = stake
        
        logger.info(f"✅ Staked {amount} reputation for {entity_id}")
        return True
    
    def unstake_reputation(self, stake_id: str) -> bool:
        """Unstake reputation"""
        if stake_id not in self.stakes:
            return False
        
        stake = self.stakes[stake_id]
        entity_id = stake.entity_id
        
        if entity_id in self.scores:
            self.scores[entity_id].score += stake.amount
            self.scores[entity_id].staked_amount -= stake.amount
        
        stake.unstaked_at = datetime.utcnow()
        
        logger.info(f"✅ Unstaked {stake.amount} reputation for {entity_id}")
        return True
    
    def slash_stake(self, stake_id: str, penalty: float) -> bool:
        """Slash staked reputation as penalty"""
        if stake_id not in self.stakes:
            return False
        
        stake = self.stakes[stake_id]
        entity_id = stake.entity_id
        
        if entity_id in self.scores:
            slash_amount = min(stake.amount, penalty)
            self.scores[entity_id].staked_amount -= slash_amount
            self.scores[entity_id].score = max(0, self.scores[entity_id].score - slash_amount)
            stake.amount -= slash_amount
            stake.slashed = True
        
        logger.info(f"⚔️  Slashed {slash_amount} reputation from {entity_id}")
        return True
    
    def get_reputation(self, entity_id: str) -> Optional[ReputationScore]:
        """Get reputation score for entity"""
        return self.scores.get(entity_id)
    
    def get_leaderboard(self, limit: int = 10) -> List[ReputationScore]:
        """Get top entities by reputation"""
        sorted_scores = sorted(
            self.scores.values(),
            key=lambda x: x.score,
            reverse=True
        )
        return sorted_scores[:limit]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        level_counts = {}
        for score in self.scores.values():
            level_counts[score.level.value] = level_counts.get(score.level.value, 0) + 1
        
        total_staked = sum(s.staked_amount for s in self.scores.values())
        
        return {
            "total_entities": len(self.scores),
            "level_distribution": level_counts,
            "total_staked": total_staked,
            "total_stakes": len(self.stakes),
            "active_stakes": sum(1 for s in self.stakes.values() if s.unstaked_at is None)
        }


# Global instance
_reputation_system: Optional[ReputationSystem] = None


def get_reputation_system() -> ReputationSystem:
    """Get singleton instance"""
    global _reputation_system
    if _reputation_system is None:
        _reputation_system = ReputationSystem()
    return _reputation_system
