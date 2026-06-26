#!/usr/bin/env python3
"""
STATUS: NEW — Mirror Module Main
AsimNexus Mirror Module
======================
Digital Twin for every user.
LoRA/QLoRA Auto Fine-Tuning, Dreaming Engine included.
"""

import time
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from .consciousness import ConsciousnessLayer, Thought, ThoughtType
    from .lora_engine import MirrorLoRA
    from .dreaming_engine import DreamingEngine, Dream, DreamType
except ImportError:
    ConsciousnessLayer = None
    MirrorLoRA = None
    DreamingEngine = None


@dataclass
class MirrorReflection:
    action: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    intent: str = ""
    outcome: str = ""
    contradictions: List[str] = field(default_factory=list)
    balance_impact: float = 0.0
    mirror_response: str = ""


class MirrorModule:
    """
    Digital Twin for each user.
    - Conscious/Subconscious state management
    - LoRA Auto Fine-Tuning
    - Dreaming Engine evolution
    - 3-Confirmation Integration
    """
    
    def __init__(self, user_id: str, user_type: str = "citizen"):
        self.user_id = user_id
        self.user_type = user_type
        
        if ConsciousnessLayer:
            self.consciousness = ConsciousnessLayer(user_id)
        else:
            self.consciousness = None
            
        if MirrorLoRA:
            self.lora_engine = MirrorLoRA(user_id)
        else:
            self.lora_engine = None
            
        if DreamingEngine:
            self.dreaming_engine = DreamingEngine(user_id)
        else:
            self.dreaming_engine = None
            
        self.reflections: List[MirrorReflection] = []
        self.daily_summary: Dict[str, Any] = {}
        
    async def reflect(self, action: Dict[str, Any]) -> MirrorReflection:
        """Reflect each action without bias - only truth."""
        intent = action.get("intent", action.get("message", ""))
        outcome = action.get("outcome", "")
        
        contradictions = self._detect_contradictions(action)
        balance_impact = self._calculate_balance_impact(action, contradictions)
        mirror_response = self._generate_mirror_response(intent, contradictions, balance_impact)
        
        reflection = MirrorReflection(
            action=action,
            intent=intent,
            outcome=outcome,
            contradictions=contradictions,
            balance_impact=balance_impact,
            mirror_response=mirror_response
        )
        
        self.reflections.append(reflection)
        
        if self.consciousness:
            self.consciousness.update_principles(action)
            thought = Thought(
                thought_type=ThoughtType.REFLECTION,
                content=f"Reflected: {intent}",
                related_action=intent
            )
            self.consciousness.add_thought(thought)
        
        return reflection
        
    def _detect_contradictions(self, action: Dict[str, Any]) -> List[str]:
        contradictions = []
        intent = action.get("intent", "").lower()
        outcome = action.get("outcome", "").lower()
        
        if "helpful" in intent and "harmful" in outcome:
            contradictions.append("Stated helpful but outcome was harmful")
            
        if "honest" in intent and "deceptive" in outcome:
            contradictions.append("Stated honest but outcome was deceptive")
            
        return contradictions
        
    def _calculate_balance_impact(self, action: Dict[str, Any], contradictions: List[str]) -> float:
        impact = 0.0
        
        if contradictions:
            impact += len(contradictions) * 0.3
            
        intent = action.get("intent", "").lower()
        if any(word in intent for word in ["helpful", "kind", "support"]):
            impact -= 0.1
            
        return round(impact, 2)
        
    def _generate_mirror_response(self, intent: str, contradictions: List[str], balance_impact: float) -> str:
        if not contradictions:
            return "🌌 **Asim**\n\n✅ Action aligned with intent. No contradictions detected."
            
        response = "🌌 **Asim**\n\n⚠️ **Contradictions Detected**:\n"
        for c in contradictions:
            response += f"- {c}\n"
            
        if balance_impact > 0.7:
            response += f"\n🔴 Balance impact: {balance_impact} (High - needs attention)\n"
            response += "Would you like to change this?"
        else:
            response += f"\n🟡 Balance impact: {balance_impact} (Moderate)"
            
        return response
        
    async def nightly_dream(self) -> List[Any]:
        """Run Dreaming Engine nightly."""
        if self.dreaming_engine:
            reflections_dict = [
                {"intent": r.intent, "outcome": r.outcome, "timestamp": r.timestamp}
                for r in self.reflections
            ]
            return await self.dreaming_engine.nightly_evolution(reflections_dict)
        return []
        
    async def auto_fine_tune(self) -> Dict[str, Any]:
        """Run LoRA Auto Fine-Tuning."""
        if self.lora_engine:
            reflections_dict = [
                {"intent": r.intent, "outcome": r.outcome}
                for r in self.reflections
            ]
            return await self.lora_engine.fine_tune(reflections_dict)
        return {"status": "skipped", "reason": "LoRA engine not available"}
        
    def get_daily_report(self) -> Dict[str, Any]:
        """Generate daily report."""
        today = datetime.now().date()
        today_reflections = [
            r for r in self.reflections 
            if datetime.fromtimestamp(r.timestamp).date() == today
        ]
        
        total_contradictions = sum(len(r.contradictions) for r in today_reflections)
        avg_balance = sum(r.balance_impact for r in today_reflections) / len(today_reflections) if today_reflections else 0
        
        return {
            "date": str(today),
            "total_actions": len(today_reflections),
            "total_contradictions": total_contradictions,
            "avg_balance_impact": round(avg_balance, 2),
            "principles": self.consciousness.get_state() if self.consciousness else {},
            "reflections": [r.mirror_response for r in today_reflections[-10:]]
        }
        
    def requires_human_review(self, threshold: float = 0.7) -> bool:
        if not self.reflections:
            return False
        latest = self.reflections[-1]
        return latest.balance_impact > threshold


_mirror_instances: Dict[str, MirrorModule] = {}


def get_mirror(user_id: str, user_type: str = "citizen") -> MirrorModule:
    """Get user's Mirror Module Instance."""
    if user_id not in _mirror_instances:
        _mirror_instances[user_id] = MirrorModule(user_id, user_type)
    return _mirror_instances[user_id]