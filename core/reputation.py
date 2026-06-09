#!/usr/bin/env python3
"""
Phase 7: Agent Reputation System
=================================
Tracks trust scores for agents based on reliability, accuracy, security.
Provides decentralized reputation that follows agents across mesh instances.
"""

import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("AsimNexus.Core.Reputation")

class ReputationEvent(Enum):
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    TASK_TIMEOUT = "task_timeout"
    HONEST_VOTE = "honest_vote"
    DISHONEST_VOTE = "dishonest_vote"
    SECURITY_VIOLATION = "security_violation"
    RESOURCE_ABUSE = "resource_abuse"
    PEER_ENDORSEMENT = "peer_endorsement"
    PEER_REPORT = "peer_report"

@dataclass
class ReputationScore:
    """Aggregated reputation for an agent."""
    agent_id: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    timed_out_tasks: int = 0
    honest_votes: int = 0
    dishonest_votes: int = 0
    security_violations: int = 0
    resource_abuses: int = 0
    peer_endorsements: int = 0
    peer_reports: int = 0
    last_updated: float = field(default_factory=time.time)
    
    @property
    def reliability(self) -> float:
        """Task completion reliability score 0.0-1.0."""
        if self.total_tasks == 0:
            return 0.5  # Neutral starting score
        return self.successful_tasks / self.total_tasks
    
    @property
    def honesty(self) -> float:
        """Voting honesty score 0.0-1.0."""
        total_votes = self.honest_votes + self.dishonest_votes
        if total_votes == 0:
            return 0.5
        return self.honest_votes / total_votes
    
    @property
    def trust_score(self) -> float:
        """Composite trust score 0.0-1.0."""
        if self.security_violations > 0:
            return max(0.0, 0.5 - (self.security_violations * 0.2))
        w_reliability = 0.4
        w_honesty = 0.3
        w_endorsements = 0.2
        w_penalty = 0.1
        
        score = (
            w_reliability * self.reliability +
            w_honesty * self.honesty +
            w_endorsements * min(1.0, self.peer_endorsements * 0.1) -
            w_penalty * min(1.0, self.peer_reports * 0.2)
        )
        return max(0.0, min(1.0, score))
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ReputationSystem:
    """Singleton reputation system for the entire agent mesh."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._scores: Dict[str, ReputationScore] = {}
        self._history: List[Dict] = []
        self._peer_testimonies: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)
        logger.info("✅ Agent Reputation System initialized")
    
    def record_event(self, agent_id: str, event: ReputationEvent, metadata: Optional[Dict] = None) -> ReputationScore:
        """Record a reputation event for an agent."""
        if agent_id not in self._scores:
            self._scores[agent_id] = ReputationScore(agent_id=agent_id)
        
        score = self._scores[agent_id]
        score.last_updated = time.time()
        
        if event == ReputationEvent.TASK_SUCCESS:
            score.total_tasks += 1
            score.successful_tasks += 1
        elif event == ReputationEvent.TASK_FAILURE:
            score.total_tasks += 1
            score.failed_tasks += 1
        elif event == ReputationEvent.TASK_TIMEOUT:
            score.total_tasks += 1
            score.timed_out_tasks += 1
        elif event == ReputationEvent.HONEST_VOTE:
            score.honest_votes += 1
        elif event == ReputationEvent.DISHONEST_VOTE:
            score.dishonest_votes += 1
        elif event == ReputationEvent.SECURITY_VIOLATION:
            score.security_violations += 1
        elif event == ReputationEvent.RESOURCE_ABUSE:
            score.resource_abuses += 1
        elif event == ReputationEvent.PEER_ENDORSEMENT:
            score.peer_endorsements += 1
        elif event == ReputationEvent.PEER_REPORT:
            score.peer_reports += 1
        
        self._history.append({
            "agent_id": agent_id,
            "event": event.value,
            "timestamp": time.time(),
            "metadata": metadata or {},
            "new_score": score.trust_score
        })
        
        logger.debug(f"Reputation event for {agent_id}: {event.value} → score={score.trust_score:.3f}")
        return score
    
    def get_score(self, agent_id: str) -> Optional[ReputationScore]:
        return self._scores.get(agent_id)
    
    def get_trust_score(self, agent_id: str) -> float:
        score = self._scores.get(agent_id)
        return score.trust_score if score else 0.5
    
    def add_testimony(self, subject_id: str, witness_id: str, testimony: str, weight: float = 1.0):
        """Add peer testimony about an agent."""
        self._peer_testimonies[subject_id].append((witness_id, testimony, weight))
    
    def get_reliable_agents(self, min_score: float = 0.7) -> List[str]:
        """Get agents with trust score above threshold."""
        return [aid for aid, s in self._scores.items() if s.trust_score >= min_score]
    
    def get_stats(self) -> Dict:
        return {
            "total_agents": len(self._scores),
            "avg_trust": sum(s.trust_score for s in self._scores.values()) / max(1, len(self._scores)),
            "total_events": len(self._history),
            "reliable_agents": len(self.get_reliable_agents()),
        }


def get_reputation_system() -> ReputationSystem:
    """Get the singleton reputation system."""
    return ReputationSystem()
