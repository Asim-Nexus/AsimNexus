#!/usr/bin/env python3
"""
STATUS: REAL — Full Digital Twin with Log Analysis & Self-Evolution
ASIMNEXUS Mirror Module
========================
Digital Twin for every user with full self-evolution capabilities.
- LoRA/QLoRA Auto Fine-Tuning
- Dreaming Engine for pattern discovery
- Log analysis from StructuredLogger
- Integration with Data Lake for OLAP analytics
- Code improvement via evolution engine

Reference: Digital Twin Architecture (Graeme Wright),
           Tesla Over-the-Air Update Pattern,
           Continuous Self-Evolution Systems

Features:
  - Conscious/Subconscious state management
  - LoRA Auto Fine-Tuning from reflection data
  - Dreaming Engine for nightly pattern evolution
  - Log analysis for anomaly detection
  - Data Lake integration for OLAP analytics
  - Code improvement suggestions via evolution engine
  - 3-Confirmation Integration for safety
"""

import time
import json
import logging
import asyncio
import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Awaitable
from pathlib import Path

logger = logging.getLogger("AsimNexus.Mirror.Module")

# Try optional imports (graceful fallback)
try:
    from .consciousness import ConsciousnessLayer, Thought, ThoughtType
except ImportError:
    ConsciousnessLayer = None

try:
    from .lora_engine import MirrorLoRA
except ImportError:
    MirrorLoRA = None

try:
    from .dreaming_engine import DreamingEngine, Dream, DreamType
except ImportError:
    DreamingEngine = None

# Try Data Lake integration
try:
    from core.analytics.data_lake import get_data_lake, SnapshotType
    DATA_LAKE_AVAILABLE = True
except ImportError:
    DATA_LAKE_AVAILABLE = False

# Try Structured Logger integration
try:
    from core.structured_logger import get_logger, StructuredLogger
    STRUCTURED_LOGGER_AVAILABLE = True
except ImportError:
    STRUCTURED_LOGGER_AVAILABLE = False

MIRROR_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "mirror"
MIRROR_DB_PATH.mkdir(parents=True, exist_ok=True)


@dataclass
class MirrorReflection:
    """A single reflection on an action."""
    action: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    intent: str = ""
    outcome: str = ""
    contradictions: List[str] = field(default_factory=list)
    balance_impact: float = 0.0
    mirror_response: str = ""
    reflection_hash: str = ""

    def __post_init__(self):
        if not self.reflection_hash:
            content = f"{self.intent}:{self.outcome}:{self.timestamp}"
            self.reflection_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "timestamp": self.timestamp,
            "intent": self.intent,
            "outcome": self.outcome,
            "contradictions": self.contradictions,
            "balance_impact": self.balance_impact,
            "mirror_response": self.mirror_response,
            "reflection_hash": self.reflection_hash,
        }


@dataclass
class EvolutionSuggestion:
    """A suggestion for self-evolution from the Mirror Module."""
    suggestion_id: str
    suggestion_type: str  # code_improvement, behavior_adjustment, fine_tune, dream_insight
    description: str
    source: str  # nightly_dream, log_analysis, data_lake, contradiction_pattern
    confidence: float = 0.0
    created_at: float = field(default_factory=time.time)
    applied: bool = False
    applied_at: Optional[float] = None
    impact_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MirrorModule:
    """
    Digital Twin for each user.
    
    Full self-evolution capabilities:
    - Conscious/Subconscious state management
    - LoRA Auto Fine-Tuning from reflection data
    - Dreaming Engine for nightly pattern evolution
    - Log analysis for anomaly detection
    - Data Lake integration for OLAP analytics
    - Code improvement suggestions via evolution engine
    - 3-Confirmation Integration for safety
    """
    
    def __init__(self, user_id: str, user_type: str = "citizen"):
        self.user_id = user_id
        self.user_type = user_type
        
        # Optional sub-modules
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
        
        # Core state
        self.reflections: List[MirrorReflection] = []
        self.evolution_suggestions: List[EvolutionSuggestion] = []
        self.daily_summary: Dict[str, Any] = {}
        
        # Log analysis state
        self._log_buffer: List[Dict[str, Any]] = []
        self._last_log_analysis: float = 0.0
        
        # Data Lake integration
        self._data_lake = None
        if DATA_LAKE_AVAILABLE:
            try:
                self._data_lake = get_data_lake()
            except Exception:
                pass
        
        # Structured Logger
        self._logger = None
        if STRUCTURED_LOGGER_AVAILABLE:
            try:
                self._logger = get_logger(f"Mirror.{user_id}")
            except Exception:
                pass
        
        # Load persisted state
        self._load_state()
        
        logger.info(f"🪞 Mirror Module initialized for {user_id} ({user_type})")
    
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
            mirror_response=mirror_response,
        )
        
        self.reflections.append(reflection)
        self._persist_reflection(reflection)
        
        # Update consciousness
        if self.consciousness:
            self.consciousness.update_principles(action)
            thought = Thought(
                thought_type=ThoughtType.REFLECTION,
                content=f"Reflected: {intent}",
                metadata={"related_action": intent}
            )
            self.consciousness.add_thought(thought)
        
        # Log to structured logger
        if self._logger:
            self._logger.info(
                f"Reflection: {intent[:50]}",
                extra={
                    "reflection_hash": reflection.reflection_hash,
                    "contradictions": len(contradictions),
                    "balance_impact": balance_impact,
                },
            )
        
        # Take Data Lake snapshot if available
        if self._data_lake:
            try:
                self._data_lake.record_aggregation(
                    metric_name=f"mirror.{self.user_id}.reflections",
                    value=1.0,
                )
                if contradictions:
                    self._data_lake.record_aggregation(
                        metric_name=f"mirror.{self.user_id}.contradictions",
                        value=len(contradictions),
                    )
            except Exception:
                pass
        
        return reflection
    
    def _detect_contradictions(self, action: Dict[str, Any]) -> List[str]:
        """Detect contradictions between intent and outcome."""
        contradictions = []
        intent = action.get("intent", "").lower()
        outcome = action.get("outcome", "").lower()
        
        if "helpful" in intent and "harmful" in outcome:
            contradictions.append("Stated helpful but outcome was harmful")
            
        if "honest" in intent and "deceptive" in outcome:
            contradictions.append("Stated honest but outcome was deceptive")
        
        if "secure" in intent and "breach" in outcome:
            contradictions.append("Stated secure but outcome was a breach")
        
        if "private" in intent and "exposed" in outcome:
            contradictions.append("Stated private but data was exposed")
        
        # Check for intent-outcome mismatch
        if intent and outcome and intent != outcome:
            # Check if outcome contradicts intent
            negative_outcomes = ["failed", "error", "rejected", "violation", "breach"]
            positive_intents = ["create", "help", "support", "enable", "approve"]
            
            if any(n in outcome for n in negative_outcomes) and any(p in intent for p in positive_intents):
                contradictions.append(f"Positive intent '{intent}' had negative outcome '{outcome}'")
        
        return contradictions
    
    def _calculate_balance_impact(self, action: Dict[str, Any], contradictions: List[str]) -> float:
        """Calculate the balance impact of an action."""
        impact = 0.0
        
        if contradictions:
            impact += len(contradictions) * 0.3
            
        intent = action.get("intent", "").lower()
        if any(word in intent for word in ["helpful", "kind", "support"]):
            impact -= 0.1
            
        outcome = action.get("outcome", "").lower()
        if any(word in outcome for word in ["failed", "error", "rejected"]):
            impact += 0.2
            
        return round(impact, 2)
    
    def _generate_mirror_response(self, intent: str, contradictions: List[str], balance_impact: float) -> str:
        """Generate a mirror response based on analysis."""
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
    
    async def nightly_dream(self) -> List[EvolutionSuggestion]:
        """
        Run Dreaming Engine nightly for pattern discovery and evolution.
        
        Analyzes all reflections from the day and generates evolution suggestions.
        """
        suggestions = []
        
        # Run dreaming engine if available
        if self.dreaming_engine:
            reflections_dict = [
                {"intent": r.intent, "outcome": r.outcome, "timestamp": r.timestamp}
                for r in self.reflections
            ]
            dreams = await self.dreaming_engine.nightly_evolution(reflections_dict)
            
            for dream in dreams:
                suggestion = EvolutionSuggestion(
                    suggestion_id=f"dream_{int(time.time())}_{len(suggestions)}",
                    suggestion_type="dream_insight",
                    description=str(dream) if not isinstance(dream, str) else dream,
                    source="nightly_dream",
                    confidence=0.7,
                    metadata={"dream_data": dream if isinstance(dream, dict) else {"content": str(dream)}},
                )
                suggestions.append(suggestion)
        
        # Analyze contradiction patterns
        contradiction_patterns = self._analyze_contradiction_patterns()
        for pattern in contradiction_patterns:
            suggestion = EvolutionSuggestion(
                suggestion_id=f"pattern_{int(time.time())}_{len(suggestions)}",
                suggestion_type="behavior_adjustment",
                description=pattern["description"],
                source="contradiction_pattern",
                confidence=pattern.get("confidence", 0.5),
                metadata=pattern,
            )
            suggestions.append(suggestion)
        
        # Generate code improvement suggestions from log analysis
        log_suggestions = self._analyze_logs_for_improvements()
        suggestions.extend(log_suggestions)
        
        # Store suggestions
        self.evolution_suggestions.extend(suggestions)
        self._persist_suggestions(suggestions)
        
        # Take Data Lake snapshot
        if self._data_lake:
            try:
                self._data_lake.take_snapshot(
                    snapshot_type=SnapshotType.MIRROR_STATE,
                    data={
                        "user_id": self.user_id,
                        "reflections_count": len(self.reflections),
                        "suggestions_count": len(suggestions),
                        "contradiction_rate": self._get_contradiction_rate(),
                    },
                    metadata={"source": "nightly_dream"},
                )
            except Exception:
                pass
        
        logger.info(f"🌙 Nightly dream complete: {len(suggestions)} suggestions for {self.user_id}")
        return suggestions
    
    def _analyze_contradiction_patterns(self) -> List[Dict[str, Any]]:
        """Analyze reflection history for recurring contradiction patterns."""
        patterns = []
        
        if len(self.reflections) < 3:
            return patterns
        
        # Count contradictions by type
        contradiction_counts: Dict[str, int] = {}
        for ref in self.reflections:
            for c in ref.contradictions:
                contradiction_counts[c] = contradiction_counts.get(c, 0) + 1
        
        # Find patterns that occur frequently
        for contradiction, count in contradiction_counts.items():
            if count >= 3:
                patterns.append({
                    "description": f"Recurring contradiction ({count}x): {contradiction}",
                    "confidence": min(0.9, 0.3 + (count * 0.1)),
                    "count": count,
                    "pattern_type": "recurring_contradiction",
                })
        
        # Check for time-based patterns
        recent = self.reflections[-10:]
        recent_contradictions = sum(len(r.contradictions) for r in recent)
        if len(recent) >= 5 and recent_contradictions / len(recent) > 0.5:
            patterns.append({
                "description": f"High contradiction rate in recent actions: {recent_contradictions}/{len(recent)}",
                "confidence": 0.6,
                "count": recent_contradictions,
                "pattern_type": "high_contradiction_rate",
            })
        
        return patterns
    
    def _analyze_logs_for_improvements(self) -> List[EvolutionSuggestion]:
        """Analyze logs for code improvement suggestions."""
        suggestions = []
        
        if not self._log_buffer:
            return suggestions
        
        # Count error patterns
        error_counts: Dict[str, int] = {}
        for log_entry in self._log_buffer:
            level = log_entry.get("level", "").upper()
            if level in ("ERROR", "CRITICAL"):
                msg = log_entry.get("message", "")
                # Group similar errors
                error_key = msg[:50] if len(msg) > 50 else msg
                error_counts[error_key] = error_counts.get(error_key, 0) + 1
        
        for error_msg, count in error_counts.items():
            if count >= 2:
                suggestions.append(EvolutionSuggestion(
                    suggestion_id=f"log_{int(time.time())}_{len(suggestions)}",
                    suggestion_type="code_improvement",
                    description=f"Recurring error ({count}x): {error_msg}",
                    source="log_analysis",
                    confidence=min(0.8, 0.3 + (count * 0.1)),
                    metadata={"error_count": count, "error_sample": error_msg},
                ))
        
        return suggestions
    
    def ingest_log(self, log_entry: Dict[str, Any]) -> None:
        """Ingest a log entry for analysis."""
        self._log_buffer.append(log_entry)
        
        # Trim buffer to last 1000 entries
        if len(self._log_buffer) > 1000:
            self._log_buffer = self._log_buffer[-1000:]
    
    async def auto_fine_tune(self) -> Dict[str, Any]:
        """
        Run LoRA Auto Fine-Tuning.
        
        Uses reflection data to fine-tune the model for better alignment.
        """
        if self.lora_engine:
            reflections_dict = [
                {"intent": r.intent, "outcome": r.outcome}
                for r in self.reflections
            ]
            
            if not reflections_dict:
                return {"status": "skipped", "reason": "No reflection data available"}
            
            result = await self.lora_engine.fine_tune(reflections_dict)
            
            # Record fine-tune event in Data Lake
            if self._data_lake:
                try:
                    self._data_lake.record_aggregation(
                        metric_name=f"mirror.{self.user_id}.fine_tune",
                        value=1.0,
                        metadata={"reflections_used": len(reflections_dict)},
                    )
                except Exception:
                    pass
            
            logger.info(f"🔧 Auto fine-tune complete for {self.user_id}")
            return result
        
        return {"status": "skipped", "reason": "LoRA engine not available"}
    
    def get_evolution_suggestions(
        self,
        suggestion_type: Optional[str] = None,
        only_unapplied: bool = True,
    ) -> List[EvolutionSuggestion]:
        """Get evolution suggestions with optional filtering."""
        results = list(self.evolution_suggestions)
        
        if suggestion_type:
            results = [s for s in results if s.suggestion_type == suggestion_type]
        if only_unapplied:
            results = [s for s in results if not s.applied]
        
        results.sort(key=lambda s: s.confidence, reverse=True)
        return results
    
    def apply_suggestion(self, suggestion_id: str) -> bool:
        """Mark an evolution suggestion as applied."""
        for suggestion in self.evolution_suggestions:
            if suggestion.suggestion_id == suggestion_id and not suggestion.applied:
                suggestion.applied = True
                suggestion.applied_at = time.time()
                self._persist_suggestions([suggestion])
                logger.info(f"✅ Suggestion {suggestion_id} applied")
                return True
        return False
    
    def get_daily_report(self) -> Dict[str, Any]:
        """Generate daily report with full analytics."""
        today = datetime.now().date()
        today_reflections = [
            r for r in self.reflections 
            if datetime.fromtimestamp(r.timestamp).date() == today
        ]
        
        total_contradictions = sum(len(r.contradictions) for r in today_reflections)
        avg_balance = sum(r.balance_impact for r in today_reflections) / len(today_reflections) if today_reflections else 0
        
        # Count suggestions by type
        suggestions_by_type = {}
        for s in self.evolution_suggestions:
            suggestions_by_type[s.suggestion_type] = suggestions_by_type.get(s.suggestion_type, 0) + 1
        
        report = {
            "date": str(today),
            "user_id": self.user_id,
            "user_type": self.user_type,
            "total_actions": len(today_reflections),
            "total_contradictions": total_contradictions,
            "avg_balance_impact": round(avg_balance, 2),
            "contradiction_rate": round(total_contradictions / len(today_reflections), 2) if today_reflections else 0,
            "total_suggestions": len(self.evolution_suggestions),
            "applied_suggestions": sum(1 for s in self.evolution_suggestions if s.applied),
            "suggestions_by_type": suggestions_by_type,
            "principles": self.consciousness.get_state() if self.consciousness else {},
            "reflections": [r.mirror_response for r in today_reflections[-10:]],
            "top_suggestions": [
                {"id": s.suggestion_id, "type": s.suggestion_type, "description": s.description, "confidence": s.confidence}
                for s in sorted(self.evolution_suggestions, key=lambda x: x.confidence, reverse=True)[:5]
            ],
        }
        
        self.daily_summary = report
        return report
    
    def requires_human_review(self, threshold: float = 0.7) -> bool:
        """Check if the latest reflection requires human review."""
        if not self.reflections:
            return False
        latest = self.reflections[-1]
        return latest.balance_impact > threshold
    
    def _get_contradiction_rate(self) -> float:
        """Calculate the overall contradiction rate."""
        if not self.reflections:
            return 0.0
        total = sum(len(r.contradictions) for r in self.reflections)
        return round(total / len(self.reflections), 2)
    
    def _persist_reflection(self, reflection: MirrorReflection) -> None:
        """Persist a reflection to disk."""
        try:
            filepath = MIRROR_DB_PATH / f"{self.user_id}_reflections.jsonl"
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(reflection.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist reflection: {e}")
    
    def _persist_suggestions(self, suggestions: List[EvolutionSuggestion]) -> None:
        """Persist evolution suggestions to disk."""
        try:
            filepath = MIRROR_DB_PATH / f"{self.user_id}_suggestions.jsonl"
            with open(filepath, "a", encoding="utf-8") as f:
                for s in suggestions:
                    f.write(json.dumps({
                        "suggestion_id": s.suggestion_id,
                        "suggestion_type": s.suggestion_type,
                        "description": s.description,
                        "source": s.source,
                        "confidence": s.confidence,
                        "created_at": s.created_at,
                        "applied": s.applied,
                        "applied_at": s.applied_at,
                    }) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist suggestions: {e}")
    
    def _load_state(self) -> None:
        """Load persisted state from disk."""
        # Load reflections
        try:
            filepath = MIRROR_DB_PATH / f"{self.user_id}_reflections.jsonl"
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                reflection = MirrorReflection(
                                    action=data.get("action", {}),
                                    timestamp=data.get("timestamp", time.time()),
                                    intent=data.get("intent", ""),
                                    outcome=data.get("outcome", ""),
                                    contradictions=data.get("contradictions", []),
                                    balance_impact=data.get("balance_impact", 0.0),
                                    mirror_response=data.get("mirror_response", ""),
                                )
                                self.reflections.append(reflection)
                            except (json.JSONDecodeError, KeyError):
                                continue
        except Exception as e:
            logger.warning(f"Failed to load reflections: {e}")
        
        # Load suggestions
        try:
            filepath = MIRROR_DB_PATH / f"{self.user_id}_suggestions.jsonl"
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                suggestion = EvolutionSuggestion(
                                    suggestion_id=data["suggestion_id"],
                                    suggestion_type=data.get("suggestion_type", "unknown"),
                                    description=data.get("description", ""),
                                    source=data.get("source", "unknown"),
                                    confidence=data.get("confidence", 0.0),
                                    created_at=data.get("created_at", time.time()),
                                    applied=data.get("applied", False),
                                    applied_at=data.get("applied_at"),
                                )
                                self.evolution_suggestions.append(suggestion)
                            except (json.JSONDecodeError, KeyError):
                                continue
        except Exception as e:
            logger.warning(f"Failed to load suggestions: {e}")
        
        logger.info(f"Loaded {len(self.reflections)} reflections, {len(self.evolution_suggestions)} suggestions")


_mirror_instances: Dict[str, MirrorModule] = {}
_mirror_instances_lock = threading.Lock()


def get_mirror(user_id: str, user_type: str = "citizen") -> MirrorModule:
    """Get user's Mirror Module Instance."""
    if user_id not in _mirror_instances:
        with _mirror_instances_lock:
            if user_id not in _mirror_instances:
                _mirror_instances[user_id] = MirrorModule(user_id, user_type)
    return _mirror_instances[user_id]


def reset_mirror(user_id: Optional[str] = None) -> None:
    """Reset mirror instance(s) for testing."""
    global _mirror_instances
    with _mirror_instances_lock:
        if user_id:
            _mirror_instances.pop(user_id, None)
        else:
            _mirror_instances.clear()
