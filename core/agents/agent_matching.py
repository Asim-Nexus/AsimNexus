
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Agent Matching System
===============================
Matches Human Digital Twins with contracts/jobs
Based on skills, availability, and trust score
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ASIM_AGENT_MATCH")

class MatchStatus(Enum):
    """Matching status"""
    PENDING = "pending"
    MATCHED = "matched"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class MatchResult:
    """Result of agent matching"""
    match_id: str
    twin_id: str
    contract_id: str
    score: float  # 0-1 matching score
    status: MatchStatus
    matched_at: datetime
    expires_at: datetime
    reasoning: List[str]

class AgentMatcher:
    """
    Agent Matching Engine
    
    Matches digital twins with contracts based on:
    - Skills compatibility
    - Historical performance
    - Current workload
    - Trust score
    - ΔT fairness (anti-concentration)
    """
    
    def __init__(self):
        self.matches: Dict[str, MatchResult] = {}
        self.pending_offers: Dict[str, List[MatchResult]] = {}  # twin_id -> offers
        
        # Scoring weights
        self.weights = {
            'skills': 0.35,
            'performance': 0.25,
            'availability': 0.20,
            'trust': 0.15,
            'fairness': 0.05  # ΔT anti-concentration
        }
        
        logger.info("🎯 Agent Matching system initialized")
    
    async def find_matches(self, contract_id: str, required_skills: List[str],
                          max_results: int = 5) -> List[MatchResult]:
        """Find matching agents for a contract"""
        
        # Get available twins
        try:
            from core.agent.digital_twin import get_human_digital_twin
            hdt = get_human_digital_twin()
        except Exception:
            logger.error("Digital Twin system not available")
            return []
        
        # Get all active twins
        all_twins = [
            twin for twin in hdt.twins.values()
            if twin.state.value in ['active', 'executing']
        ]
        
        if not all_twins:
            logger.warning("No active twins available for matching")
            return []
        
        # Score each twin
        scored_matches: List[Tuple[float, MatchResult]] = []
        
        for twin in all_twins:
            score, reasoning = await self._calculate_match_score(
                twin, required_skills, contract_id
            )
            
            if score > 0.3:  # Minimum threshold
                match = MatchResult(
                    match_id=f"match_{contract_id}_{twin.twin_id}_{datetime.now().timestamp()}",
                    twin_id=twin.twin_id,
                    contract_id=contract_id,
                    score=score,
                    status=MatchStatus.PENDING,
                    matched_at=datetime.now(),
                    expires_at=datetime.now().replace(hour=23, minute=59, second=59),
                    reasoning=reasoning
                )
                scored_matches.append((score, match))
        
        # Sort by score and return top matches
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        
        # Store matches
        results = []
        for score, match in scored_matches[:max_results]:
            self.matches[match.match_id] = match
            
            # Add to twin's pending offers
            if match.twin_id not in self.pending_offers:
                self.pending_offers[match.twin_id] = []
            self.pending_offers[match.twin_id].append(match)
            
            results.append(match)
        
        logger.info(f"Found {len(results)} matches for contract {contract_id[:16]}")
        return results
    
    async def _calculate_match_score(self, twin, required_skills: List[str],
                                    contract_id: str) -> Tuple[float, List[str]]:
        """Calculate match score for a twin"""
        
        scores = {}
        reasoning = []
        
        # 1. Skills match
        twin_skills = set(twin.behavior_patterns.keys())
        required = set(required_skills)
        
        if required:
            skill_overlap = len(twin_skills & required) / len(required)
            scores['skills'] = skill_overlap
            reasoning.append(f"Skills overlap: {skill_overlap:.0%}")
        else:
            scores['skills'] = 0.5
            reasoning.append("No specific skills required")
        
        # 2. Historical performance
        if twin.total_actions > 0:
            # Calculate success rate from behavior patterns
            success_rates = [
                p['success_rate'] for p in twin.behavior_patterns.values()
                if 'success_rate' in p
            ]
            if success_rates:
                avg_success = sum(success_rates) / len(success_rates)
                scores['performance'] = avg_success
                reasoning.append(f"Historical success rate: {avg_success:.0%}")
            else:
                scores['performance'] = 0.5
                reasoning.append("No performance history yet")
        else:
            scores['performance'] = 0.3  # New twin
            reasoning.append("New twin (limited history)")
        
        # 3. Availability
        active_contracts = len(twin.active_contracts)
        if active_contracts == 0:
            scores['availability'] = 1.0
            reasoning.append("Fully available")
        elif active_contracts < 3:
            scores['availability'] = 0.7
            reasoning.append(f"Moderate workload ({active_contracts} contracts)")
        else:
            scores['availability'] = 0.3
            reasoning.append(f"Heavy workload ({active_contracts} contracts)")
        
        # 4. Trust score
        # Based on completed contracts and actions
        trust_base = min(twin.completed_contracts / 10, 1.0)  # Max at 10 contracts
        trust_bonus = min(twin.total_actions / 100, 0.3)  # Max bonus at 100 actions
        scores['trust'] = trust_base + trust_bonus
        reasoning.append(f"Trust score: {scores['trust']:.2f}")
        
        # 5. ΔT fairness (anti-concentration)
        # Check if this twin already has too many matches
        recent_matches = sum(
            1 for m in self.matches.values()
            if m.twin_id == twin.twin_id and m.status == MatchStatus.ACCEPTED
        )
        
        if recent_matches < 2:
            scores['fairness'] = 1.0
            reasoning.append("Fairness: Low recent activity")
        elif recent_matches < 5:
            scores['fairness'] = 0.7
            reasoning.append("Fairness: Moderate activity")
        else:
            scores['fairness'] = 0.3
            reasoning.append("Fairness: High activity (anti-concentration)")
        
        # Calculate weighted total
        total_score = sum(
            scores.get(key, 0) * weight
            for key, weight in self.weights.items()
        )
        
        return total_score, reasoning
    
    def accept_match(self, match_id: str, twin_id: str) -> bool:
        """Twin accepts a match"""
        if match_id not in self.matches:
            return False
        
        match = self.matches[match_id]
        
        # Verify ownership
        if match.twin_id != twin_id:
            return False
        
        # Check expiration
        if datetime.now() > match.expires_at:
            match.status = MatchStatus.EXPIRED
            return False
        
        # Accept
        match.status = MatchStatus.ACCEPTED
        
        # Remove from pending
        if twin_id in self.pending_offers:
            self.pending_offers[twin_id] = [
                m for m in self.pending_offers[twin_id]
                if m.match_id != match_id
            ]
        
        logger.info(f"✅ Match accepted: {match_id[:16]} by {twin_id[:16]}")
        return True
    
    def reject_match(self, match_id: str, twin_id: str, reason: str = None) -> bool:
        """Twin rejects a match"""
        if match_id not in self.matches:
            return False
        
        match = self.matches[match_id]
        
        if match.twin_id != twin_id:
            return False
        
        match.status = MatchStatus.REJECTED
        
        # Remove from pending
        if twin_id in self.pending_offers:
            self.pending_offers[twin_id] = [
                m for m in self.pending_offers[twin_id]
                if m.match_id != match_id
            ]
        
        logger.info(f"❌ Match rejected: {match_id[:16]} by {twin_id[:16]} ({reason})")
        return True
    
    def get_pending_matches(self, twin_id: str) -> List[MatchResult]:
        """Get pending matches for a twin"""
        # Clean expired matches first
        now = datetime.now()
        for match in self.matches.values():
            if match.status == MatchStatus.PENDING and now > match.expires_at:
                match.status = MatchStatus.EXPIRED
        
        return [
            match for match in self.pending_offers.get(twin_id, [])
            if match.status == MatchStatus.PENDING
        ]
    
    def get_match(self, match_id: str) -> Optional[MatchResult]:
        """Get match by ID"""
        return self.matches.get(match_id)
    
    def get_matching_stats(self) -> Dict[str, Any]:
        """Get matching system statistics"""
        status_counts = {}
        for match in self.matches.values():
            s = match.status.value
            status_counts[s] = status_counts.get(s, 0) + 1
        
        return {
            'total_matches': len(self.matches),
            'by_status': status_counts,
            'twins_with_offers': len(self.pending_offers),
            'average_score': sum(m.score for m in self.matches.values()) / len(self.matches) if self.matches else 0,
            'weights': self.weights
        }

_matcher = None

def get_agent_matcher() -> AgentMatcher:
    """Get agent matcher singleton"""
    global _matcher
    if _matcher is None:
        _matcher = AgentMatcher()
    return _matcher

if __name__ == "__main__":
    import asyncio
    import sys
    
    async def main():
        matcher = get_agent_matcher()
        
        if len(sys.argv) > 1 and sys.argv[1] == "match":
            # Create test data first
            from core.agent.digital_twin import get_human_digital_twin, TwinCapability
            hdt = get_human_digital_twin()
            
            # Create a twin
            twin = hdt.create_twin("user_test", "Test Twin", [
                TwinCapability.RESEARCH,
                TwinCapability.NEGOTIATE,
                TwinCapability.SCHEDULE
            ])
            
            # Add some learning data
            hdt.learn_from_action(twin.twin_id, "research", {'topic': 'AI'}, 'success')
            hdt.learn_from_action(twin.twin_id, "negotiate", {'parties': 2}, 'success')
            
            # Find matches
            matches = await matcher.find_matches(
                "contract_test_001",
                ["research", "negotiate"],
                max_results=3
            )
            
            print(f"Found {len(matches)} matches:")
            for m in matches:
                print(f"  - Twin: {m.twin_id[:16]}... Score: {m.score:.2f}")
                print(f"    Reasoning: {m.reasoning}")
        
        elif len(sys.argv) > 1 and sys.argv[1] == "stats":
            import json
            print(json.dumps(matcher.get_matching_stats(), indent=2))
        
        else:
            print("Usage: python agent_matching.py [match|stats]")
    
    asyncio.run(main())
