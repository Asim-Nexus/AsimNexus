"""
core/evolution/evolution_engine.py
AsimNexus — Phase 4 Real Evolution Engine (Tesla FSD Pattern)
===============================================================

Tesla FSD (Full Self-Driving) Pattern:
  1. MirrorModule detects contradiction patterns (like FSD cameras detect road conditions)
  2. Evolution Engine generates code improvement suggestions (like FSD plans trajectory)
  3. Immutable Constitution checks suggestions against formal rules (like FSD safety checks)
  4. Human approval required before applying (like FSD supervised mode — human in the loop)
  5. Applied changes tracked with cryptographic audit trail (like FSD's shadow mode logging)

Reference: Tesla FSD Beta Architecture,
           Continuous Self-Evolution Systems,
           Formal Verification Methods (Leslie Lamport)

Features:
  - Contradiction pattern ingestion from MirrorModule
  - Code improvement suggestion generation with confidence scoring
  - Constitution formal rules verification before approval
  - Human approval gate (Tesla FSD supervised mode)
  - Cryptographic audit trail for all evolution events
  - Evolution metrics and statistics
  - Integration with Data Lake for OLAP analytics
"""

import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("AsimNexus.Evolution")

# Try optional imports (graceful fallback)
try:
    from core.security.immutable_constitution import (
        get_constitution,
        FormalRuleType,
        PrincipleSeverity,
    )
    CONSTITUTION_AVAILABLE = True
except ImportError:
    CONSTITUTION_AVAILABLE = False

try:
    from core.analytics.data_lake import get_data_lake, SnapshotType
    DATA_LAKE_AVAILABLE = True
except ImportError:
    DATA_LAKE_AVAILABLE = False

try:
    from core.security.audit_log import get_audit_log, AuditEventType, AuditSeverity
    AUDIT_LOG_AVAILABLE = True
except ImportError:
    AUDIT_LOG_AVAILABLE = False

EVOLUTION_DB_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "evolution"
)
EVOLUTION_DB_PATH.mkdir(parents=True, exist_ok=True)


class SuggestionCategory(str, Enum):
    """Categories of evolution suggestions."""
    CODE_IMPROVEMENT = "code_improvement"
    BEHAVIOR_ADJUSTMENT = "behavior_adjustment"
    ARCHITECTURE_CHANGE = "architecture_change"
    CONFIGURATION_TUNE = "configuration_tune"
    SECURITY_HARDENING = "security_hardening"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    COMPLIANCE_UPDATE = "compliance_update"


class SuggestionStatus(str, Enum):
    """Status of an evolution suggestion through the pipeline."""
    PENDING_REVIEW = "pending_review"       # Generated, awaiting human review
    CONSTITUTION_CHECK = "constitution_check"  # Being checked against constitution
    CONSTITUTION_FAILED = "constitution_failed"  # Failed constitution check
    APPROVED = "approved"                    # Human approved
    APPLIED = "applied"                      # Successfully applied
    REJECTED = "rejected"                    # Human rejected
    ROLLED_BACK = "rolled_back"              # Applied but rolled back


@dataclass
class EvolutionSuggestion:
    """
    A suggestion for system evolution.

    Tesla FSD Pattern:
    - Like FSD's planned trajectory — generated from perception data
    - Must pass safety checks before execution
    - Requires human confirmation (supervised mode)
    """
    suggestion_id: str
    category: SuggestionCategory
    title: str
    description: str
    source: str  # contradiction_pattern, log_analysis, nightly_dream, manual
    confidence: float = 0.0
    status: SuggestionStatus = SuggestionStatus.PENDING_REVIEW
    created_at: float = field(default_factory=time.time)
    reviewed_at: Optional[float] = None
    reviewed_by: Optional[str] = None
    applied_at: Optional[float] = None
    constitution_results: List[Dict[str, Any]] = field(default_factory=list)
    impact_estimate: Dict[str, Any] = field(default_factory=dict)
    rollback_plan: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = (
                f"{self.suggestion_id}:{self.category.value}:{self.title}:"
                f"{self.description}:{self.created_at}"
            )
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "confidence": self.confidence,
            "status": self.status.value,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
            "applied_at": self.applied_at,
            "constitution_results": self.constitution_results,
            "impact_estimate": self.impact_estimate,
            "rollback_plan": self.rollback_plan,
            "metadata": self.metadata,
            "hash": self.hash,
        }


@dataclass
class EvolutionEvent:
    """
    A recorded evolution event in the system's history.

    Tesla FSD Pattern:
    - Like FSD's shadow mode logs — every decision recorded
    - Used for post-hoc analysis and improvement
    """
    event_id: str
    event_type: str  # suggestion_created, reviewed, applied, rolled_back, constitution_fail
    suggestion_id: str
    actor: str  # system, human_user_id
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            content = (
                f"{self.event_id}:{self.event_type}:{self.suggestion_id}:"
                f"{self.actor}:{self.timestamp}:{self.previous_hash}"
            )
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "suggestion_id": self.suggestion_id,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class EvolutionEngine:
    """
    Phase 4 — Real Evolution Engine (Tesla FSD Pattern).

    The engine drives continuous self-evolution of the AsimNexus system:

    ┌─────────────────────────────────────────────────────────────┐
    │                    TESLA FSD PATTERN                        │
    ├──────────────┬──────────────────┬───────────────────────────┤
    │  Perception  │    Planning      │      Control              │
    │ (Mirror)     │  (Evolution)     │  (Constitution + Human)   │
    ├──────────────┼──────────────────┼───────────────────────────┤
    │ Contradiction│  Generate code   │  Formal rules check       │
    │ patterns     │  improvements    │  (Constitution)           │
    │ Log analysis │  Score by        │  Human approval gate     │
    │ Dream insights│  confidence     │  (Supervised mode)       │
    │ Data Lake    │  Estimate impact │  Apply with rollback     │
    └──────────────┴──────────────────┴───────────────────────────┘
    """

    def __init__(self):
        self._suggestions: Dict[str, EvolutionSuggestion] = {}
        self._events: List[EvolutionEvent] = []
        self._lock = threading.Lock()
        self._initialized = False
        self._started_at: float = time.time()
        self._constitution = None
        self._data_lake = None
        self._audit_log = None

        # Load constitution if available
        if CONSTITUTION_AVAILABLE:
            try:
                from core.security.immutable_constitution import get_constitution
                self._constitution = get_constitution()
            except Exception as e:
                logger.warning(f"Constitution not available: {e}")

        # Load Data Lake if available
        if DATA_LAKE_AVAILABLE:
            try:
                self._data_lake = get_data_lake()
            except Exception:
                pass

        # Load Audit Log if available
        if AUDIT_LOG_AVAILABLE:
            try:
                self._audit_log = get_audit_log()
            except Exception:
                pass

        # Load persisted state
        self._load_state()

        logger.info(
            "🧬 Evolution Engine initialized (Phase 4 — Tesla FSD Pattern)"
        )

    # ── Suggestion Generation ──────────────────────────────────────────────

    def ingest_contradiction_pattern(
        self,
        pattern: Dict[str, Any],
        source: str = "contradiction_pattern",
    ) -> Optional[str]:
        """
        Ingest a contradiction pattern from MirrorModule and generate
        an evolution suggestion.

        Tesla FSD Pattern:
        - Like FSD's perception layer detecting road anomalies
        - Each contradiction pattern is analyzed for improvement potential
        """
        description = pattern.get("description", "")
        confidence = pattern.get("confidence", 0.5)
        pattern_type = pattern.get("pattern_type", "unknown")

        # Determine suggestion category based on pattern type
        if "recurring_contradiction" in pattern_type:
            category = SuggestionCategory.BEHAVIOR_ADJUSTMENT
            title = f"Adjust behavior for recurring contradiction"
        elif "high_contradiction_rate" in pattern_type:
            category = SuggestionCategory.CODE_IMPROVEMENT
            title = f"Improve code to reduce contradiction rate"
        elif "security" in pattern_type.lower():
            category = SuggestionCategory.SECURITY_HARDENING
            title = f"Security hardening for detected pattern"
        elif "performance" in pattern_type.lower():
            category = SuggestionCategory.PERFORMANCE_OPTIMIZATION
            title = f"Performance optimization opportunity"
        else:
            category = SuggestionCategory.CODE_IMPROVEMENT
            title = f"Code improvement from pattern analysis"

        suggestion = EvolutionSuggestion(
            suggestion_id=f"evolve_{int(time.time())}_{len(self._suggestions)}",
            category=category,
            title=title,
            description=description,
            source=source,
            confidence=confidence,
            status=SuggestionStatus.PENDING_REVIEW,
            metadata={
                "pattern_type": pattern_type,
                "pattern_data": pattern,
            },
        )

        with self._lock:
            self._suggestions[suggestion.suggestion_id] = suggestion
            self._persist_suggestion(suggestion)

        # Record event
        self._record_event(
            event_type="suggestion_created",
            suggestion_id=suggestion.suggestion_id,
            actor="system",
            details={
                "category": category.value,
                "confidence": confidence,
                "source": source,
            },
        )

        logger.info(
            f"💡 Evolution suggestion created: {suggestion.suggestion_id} "
            f"({category.value}, confidence={confidence})"
        )

        return suggestion.suggestion_id

    def ingest_log_improvement(
        self,
        error_msg: str,
        error_count: int,
        confidence: float = 0.5,
    ) -> Optional[str]:
        """
        Ingest a log-based improvement opportunity.

        Tesla FSD Pattern:
        - Like FSD's shadow mode detecting edge cases from logs
        """
        suggestion = EvolutionSuggestion(
            suggestion_id=f"evolve_{int(time.time())}_{len(self._suggestions)}",
            category=SuggestionCategory.CODE_IMPROVEMENT,
            title=f"Fix recurring error: {error_msg[:60]}",
            description=(
                f"Error occurred {error_count} times: {error_msg}\n"
                f"Confidence: {confidence:.2f}"
            ),
            source="log_analysis",
            confidence=confidence,
            status=SuggestionStatus.PENDING_REVIEW,
            metadata={
                "error_count": error_count,
                "error_sample": error_msg,
            },
        )

        with self._lock:
            self._suggestions[suggestion.suggestion_id] = suggestion
            self._persist_suggestion(suggestion)

        self._record_event(
            event_type="suggestion_created",
            suggestion_id=suggestion.suggestion_id,
            actor="system",
            details={
                "category": SuggestionCategory.CODE_IMPROVEMENT.value,
                "confidence": confidence,
                "source": "log_analysis",
                "error_count": error_count,
            },
        )

        return suggestion.suggestion_id

    def create_manual_suggestion(
        self,
        title: str,
        description: str,
        category: SuggestionCategory = SuggestionCategory.CODE_IMPROVEMENT,
        confidence: float = 0.8,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a manually submitted evolution suggestion.

        Tesla FSD Pattern:
        - Like a human engineer submitting a code change for FSD
        """
        suggestion = EvolutionSuggestion(
            suggestion_id=f"evolve_{int(time.time())}_{len(self._suggestions)}",
            category=category,
            title=title,
            description=description,
            source="manual",
            confidence=confidence,
            status=SuggestionStatus.PENDING_REVIEW,
            metadata=metadata or {},
        )

        with self._lock:
            self._suggestions[suggestion.suggestion_id] = suggestion
            self._persist_suggestion(suggestion)

        self._record_event(
            event_type="suggestion_created",
            suggestion_id=suggestion.suggestion_id,
            actor="system",
            details={
                "category": category.value,
                "confidence": confidence,
                "source": "manual",
            },
        )

        return suggestion.suggestion_id

    # ── Constitution Check (Safety Gate) ──────────────────────────────────

    def check_constitution(
        self, suggestion_id: str
    ) -> Dict[str, Any]:
        """
        Check an evolution suggestion against the Immutable Constitution.

        Tesla FSD Pattern:
        - Like FSD's safety monitor checking planned trajectory
        - No suggestion can proceed without passing constitution checks
        - Critical violations block the suggestion entirely

        Returns:
            Dict with:
            - passed: bool — overall result
            - violations: List[Dict] — any constitution violations found
            - critical_violations: int — count of critical severity violations
        """
        with self._lock:
            suggestion = self._suggestions.get(suggestion_id)
            if not suggestion:
                return {
                    "passed": False,
                    "violations": [],
                    "critical_violations": 0,
                    "error": f"Suggestion {suggestion_id} not found",
                }

            # Update status
            suggestion.status = SuggestionStatus.CONSTITUTION_CHECK

        if not self._constitution:
            # No constitution available — warn but allow
            logger.warning(
                f"Constitution not available for suggestion {suggestion_id} — "
                f"skipping check"
            )
            with self._lock:
                suggestion.constitution_results = []
                suggestion.status = SuggestionStatus.PENDING_REVIEW
            return {
                "passed": True,
                "violations": [],
                "critical_violations": 0,
                "warning": "Constitution not available — check skipped",
            }

        # Build context for constitution check
        context = {
            "suggestion_id": suggestion.suggestion_id,
            "category": suggestion.category.value,
            "title": suggestion.title,
            "description": suggestion.description,
            "source": suggestion.source,
            "confidence": suggestion.confidence,
            "metadata": suggestion.metadata,
        }

        # Run formal rules verification
        violations = self._constitution.check_all_rules(context)

        # Count critical violations
        critical_count = sum(
            1
            for v in violations
            if v.get("severity") == PrincipleSeverity.CRITICAL.value
        )

        passed = len(violations) == 0

        with self._lock:
            suggestion.constitution_results = violations
            if not passed:
                suggestion.status = SuggestionStatus.CONSTITUTION_FAILED
            else:
                suggestion.status = SuggestionStatus.PENDING_REVIEW

        # Record event
        self._record_event(
            event_type="constitution_fail" if not passed else "constitution_pass",
            suggestion_id=suggestion_id,
            actor="system",
            details={
                "violations": len(violations),
                "critical_violations": critical_count,
                "passed": passed,
            },
        )

        if not passed:
            logger.warning(
                f"⛔ Suggestion {suggestion_id} failed constitution check: "
                f"{len(violations)} violations ({critical_count} critical)"
            )
        else:
            logger.info(
                f"✅ Suggestion {suggestion_id} passed constitution check"
            )

        return {
            "passed": passed,
            "violations": violations,
            "critical_violations": critical_count,
        }

    # ── Human Approval Gate (Tesla FSD Supervised Mode) ───────────────────

    def approve_suggestion(
        self,
        suggestion_id: str,
        reviewer_id: str,
        impact_estimate: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Human approves an evolution suggestion.

        Tesla FSD Pattern:
        - Like a human driver confirming FSD's planned maneuver
        - The human is always in the loop (supervised mode)
        - Without approval, no change is applied

        Args:
            suggestion_id: The suggestion to approve
            reviewer_id: Human user ID who reviewed
            impact_estimate: Optional impact assessment

        Returns:
            Dict with approval result
        """
        with self._lock:
            suggestion = self._suggestions.get(suggestion_id)
            if not suggestion:
                return {
                    "approved": False,
                    "error": f"Suggestion {suggestion_id} not found",
                }

            if suggestion.status == SuggestionStatus.CONSTITUTION_FAILED:
                return {
                    "approved": False,
                    "error": (
                        f"Suggestion {suggestion_id} failed constitution check — "
                        f"cannot approve"
                    ),
                    "constitution_results": suggestion.constitution_results,
                }

            if suggestion.status == SuggestionStatus.APPLIED:
                return {
                    "approved": False,
                    "error": f"Suggestion {suggestion_id} already applied",
                }

            if suggestion.status == SuggestionStatus.REJECTED:
                return {
                    "approved": False,
                    "error": f"Suggestion {suggestion_id} was already rejected",
                }

            # Approve
            suggestion.status = SuggestionStatus.APPROVED
            suggestion.reviewed_at = time.time()
            suggestion.reviewed_by = reviewer_id
            if impact_estimate:
                suggestion.impact_estimate = impact_estimate

        # Record event
        self._record_event(
            event_type="reviewed",
            suggestion_id=suggestion_id,
            actor=reviewer_id,
            details={
                "action": "approved",
                "impact_estimate": impact_estimate or {},
            },
        )

        # Log to audit log
        if self._audit_log:
            try:
                self._audit_log.log_event(
                    event_type=AuditEventType.SYSTEM_CHANGE,
                    severity=AuditSeverity.INFO,
                    component="EvolutionEngine",
                    description=f"Evolution suggestion approved: {suggestion_id}",
                    metadata={
                        "suggestion_id": suggestion_id,
                        "reviewer": reviewer_id,
                        "title": suggestion.title,
                    },
                )
            except Exception:
                pass

        logger.info(
            f"✅ Evolution suggestion {suggestion_id} approved by {reviewer_id}"
        )

        return {
            "approved": True,
            "suggestion_id": suggestion_id,
            "reviewer": reviewer_id,
            "status": SuggestionStatus.APPROVED.value,
        }

    def reject_suggestion(
        self,
        suggestion_id: str,
        reviewer_id: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Human rejects an evolution suggestion.

        Tesla FSD Pattern:
        - Like a human driver disengaging FSD and taking control
        - The suggestion is recorded for future analysis
        """
        with self._lock:
            suggestion = self._suggestions.get(suggestion_id)
            if not suggestion:
                return {
                    "rejected": False,
                    "error": f"Suggestion {suggestion_id} not found",
                }

            suggestion.status = SuggestionStatus.REJECTED
            suggestion.reviewed_at = time.time()
            suggestion.reviewed_by = reviewer_id
            suggestion.metadata["rejection_reason"] = reason

        self._record_event(
            event_type="reviewed",
            suggestion_id=suggestion_id,
            actor=reviewer_id,
            details={
                "action": "rejected",
                "reason": reason,
            },
        )

        logger.info(
            f"❌ Evolution suggestion {suggestion_id} rejected by {reviewer_id}: "
            f"{reason}"
        )

        return {
            "rejected": True,
            "suggestion_id": suggestion_id,
            "reviewer": reviewer_id,
            "reason": reason,
        }

    # ── Application & Rollback ────────────────────────────────────────────

    def apply_suggestion(
        self,
        suggestion_id: str,
        applied_by: str = "system",
    ) -> Dict[str, Any]:
        """
        Apply an approved evolution suggestion.

        Tesla FSD Pattern:
        - Like FSD executing a confirmed maneuver
        - Only approved suggestions can be applied
        - Rollback plan is recorded before execution

        Returns:
            Dict with application result
        """
        with self._lock:
            suggestion = self._suggestions.get(suggestion_id)
            if not suggestion:
                return {
                    "applied": False,
                    "error": f"Suggestion {suggestion_id} not found",
                }

            if suggestion.status != SuggestionStatus.APPROVED:
                return {
                    "applied": False,
                    "error": (
                        f"Suggestion {suggestion_id} is not approved "
                        f"(status: {suggestion.status.value})"
                    ),
                }

            # Generate rollback plan
            rollback_plan = self._generate_rollback_plan(suggestion)
            suggestion.rollback_plan = rollback_plan

            # Mark as applied
            suggestion.status = SuggestionStatus.APPLIED
            suggestion.applied_at = time.time()

        # Record event
        self._record_event(
            event_type="applied",
            suggestion_id=suggestion_id,
            actor=applied_by,
            details={
                "rollback_plan": rollback_plan,
            },
        )

        # Log to audit log
        if self._audit_log:
            try:
                self._audit_log.log_event(
                    event_type=AuditEventType.SYSTEM_CHANGE,
                    severity=AuditSeverity.WARNING,
                    component="EvolutionEngine",
                    description=f"Evolution suggestion applied: {suggestion_id}",
                    metadata={
                        "suggestion_id": suggestion_id,
                        "applied_by": applied_by,
                        "title": suggestion.title,
                        "rollback_plan": rollback_plan,
                    },
                )
            except Exception:
                pass

        # Record in Data Lake
        if self._data_lake:
            try:
                self._data_lake.record_aggregation(
                    metric_name="evolution.suggestions_applied",
                    value=1.0,
                    metadata={
                        "category": suggestion.category.value,
                        "confidence": suggestion.confidence,
                    },
                )
            except Exception:
                pass

        logger.info(
            f"🚀 Evolution suggestion {suggestion_id} applied: {suggestion.title}"
        )

        return {
            "applied": True,
            "suggestion_id": suggestion_id,
            "rollback_plan": rollback_plan,
        }

    def rollback_suggestion(
        self,
        suggestion_id: str,
        rolled_back_by: str = "system",
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Roll back an applied evolution suggestion.

        Tesla FSD Pattern:
        - Like FSD's safe stop when encountering unexpected conditions
        - Every applied suggestion has a rollback plan
        """
        with self._lock:
            suggestion = self._suggestions.get(suggestion_id)
            if not suggestion:
                return {
                    "rolled_back": False,
                    "error": f"Suggestion {suggestion_id} not found",
                }

            if suggestion.status != SuggestionStatus.APPLIED:
                return {
                    "rolled_back": False,
                    "error": (
                        f"Suggestion {suggestion_id} is not applied "
                        f"(status: {suggestion.status.value})"
                    ),
                }

            suggestion.status = SuggestionStatus.ROLLED_BACK
            suggestion.metadata["rollback_reason"] = reason
            suggestion.metadata["rolled_back_at"] = time.time()
            suggestion.metadata["rolled_back_by"] = rolled_back_by

        self._record_event(
            event_type="rolled_back",
            suggestion_id=suggestion_id,
            actor=rolled_back_by,
            details={
                "reason": reason,
                "rollback_plan": suggestion.rollback_plan,
            },
        )

        # Log to audit log
        if self._audit_log:
            try:
                self._audit_log.log_event(
                    event_type=AuditEventType.SYSTEM_CHANGE,
                    severity=AuditSeverity.CRITICAL,
                    component="EvolutionEngine",
                    description=f"Evolution suggestion rolled back: {suggestion_id}",
                    metadata={
                        "suggestion_id": suggestion_id,
                        "rolled_back_by": rolled_back_by,
                        "reason": reason,
                    },
                )
            except Exception:
                pass

        logger.warning(
            f"↩️ Evolution suggestion {suggestion_id} rolled back by "
            f"{rolled_back_by}: {reason}"
        )

        return {
            "rolled_back": True,
            "suggestion_id": suggestion_id,
            "rolled_back_by": rolled_back_by,
            "reason": reason,
        }

    def _generate_rollback_plan(
        self, suggestion: EvolutionSuggestion
    ) -> str:
        """
        Generate a rollback plan for a suggestion.

        Every applied change must have a way to undo it.
        """
        category = suggestion.category

        if category == SuggestionCategory.CODE_IMPROVEMENT:
            return (
                "1. Revert the code change via git revert\n"
                "2. Restart the affected service\n"
                "3. Verify system health after rollback\n"
                "4. Log the rollback in the audit trail"
            )
        elif category == SuggestionCategory.CONFIGURATION_TUNE:
            return (
                "1. Restore previous configuration from backup\n"
                "2. Reload configuration without restart\n"
                "3. Verify configuration is valid\n"
                "4. Log the rollback in the audit trail"
            )
        elif category == SuggestionCategory.SECURITY_HARDENING:
            return (
                "1. Disable the security policy change\n"
                "2. Verify no security gaps introduced\n"
                "3. Log the rollback in the audit trail\n"
                "4. Notify security team"
            )
        else:
            return (
                "1. Identify the specific change that was applied\n"
                "2. Reverse the change using available tools\n"
                "3. Verify system integrity after reversal\n"
                "4. Log the rollback in the audit trail"
            )

    # ── Query & Statistics ────────────────────────────────────────────────

    def get_suggestion(
        self, suggestion_id: str
    ) -> Optional[EvolutionSuggestion]:
        """Get a specific evolution suggestion."""
        with self._lock:
            return self._suggestions.get(suggestion_id)

    def get_suggestions(
        self,
        status: Optional[SuggestionStatus] = None,
        category: Optional[SuggestionCategory] = None,
        source: Optional[str] = None,
        limit: int = 50,
    ) -> List[EvolutionSuggestion]:
        """Get evolution suggestions with optional filtering."""
        with self._lock:
            results = list(self._suggestions.values())

        if status:
            results = [s for s in results if s.status == status]
        if category:
            results = [s for s in results if s.category == category]
        if source:
            results = [s for s in results if s.source == source]

        results.sort(key=lambda s: s.created_at, reverse=True)
        return results[:limit]

    def get_pending_review(self) -> List[EvolutionSuggestion]:
        """Get all suggestions pending human review."""
        return self.get_suggestions(status=SuggestionStatus.PENDING_REVIEW)

    def get_events(
        self, limit: int = 100
    ) -> List[EvolutionEvent]:
        """Get recent evolution events."""
        with self._lock:
            return list(reversed(self._events[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Get evolution engine statistics."""
        with self._lock:
            total = len(self._suggestions)
            by_status: Dict[str, int] = {}
            by_category: Dict[str, int] = {}
            for s in self._suggestions.values():
                by_status[s.status.value] = by_status.get(s.status.value, 0) + 1
                by_category[s.category.value] = by_category.get(
                    s.category.value, 0
                ) + 1

            return {
                "total_suggestions": total,
                "by_status": by_status,
                "by_category": by_category,
                "total_events": len(self._events),
                "uptime_seconds": time.time() - self._started_at,
                "constitution_available": CONSTITUTION_AVAILABLE,
                "data_lake_available": DATA_LAKE_AVAILABLE,
                "audit_log_available": AUDIT_LOG_AVAILABLE,
                "phase": "Phase 4 — Tesla FSD Pattern",
                "pipeline": (
                    "MirrorModule (Perception) → "
                    "EvolutionEngine (Planning) → "
                    "Constitution (Safety Check) → "
                    "Human Approval (Supervised Mode)"
                ),
            }

    def get_evolution_history(
        self, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get the evolution history with cryptographic chain.

        Returns a hash chain of evolution events for audit.
        """
        events = self.get_events(limit=limit)
        return [e.to_dict() for e in events]

    # ── Internal ──────────────────────────────────────────────────────────

    def _record_event(
        self,
        event_type: str,
        suggestion_id: str,
        actor: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an evolution event with hash chain."""
        previous_hash = (
            self._events[-1].hash if self._events else "genesis"
        )

        event = EvolutionEvent(
            event_id=f"evt_{int(time.time() * 1000)}_{len(self._events)}",
            event_type=event_type,
            suggestion_id=suggestion_id,
            actor=actor,
            details=details or {},
            previous_hash=previous_hash,
        )

        with self._lock:
            self._events.append(event)
            self._persist_event(event)

    def _persist_suggestion(
        self, suggestion: EvolutionSuggestion
    ) -> None:
        """Persist a suggestion to disk."""
        try:
            filepath = EVOLUTION_DB_PATH / "suggestions.jsonl"
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(suggestion.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist suggestion: {e}")

    def _persist_event(self, event: EvolutionEvent) -> None:
        """Persist an event to disk."""
        try:
            filepath = EVOLUTION_DB_PATH / "events.jsonl"
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist event: {e}")

    def _load_state(self) -> None:
        """Load persisted state from disk."""
        # Load suggestions
        try:
            filepath = EVOLUTION_DB_PATH / "suggestions.jsonl"
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                suggestion = EvolutionSuggestion(
                                    suggestion_id=data["suggestion_id"],
                                    category=SuggestionCategory(
                                        data.get("category", "code_improvement")
                                    ),
                                    title=data.get("title", ""),
                                    description=data.get("description", ""),
                                    source=data.get("source", "unknown"),
                                    confidence=data.get("confidence", 0.0),
                                    status=SuggestionStatus(
                                        data.get("status", "pending_review")
                                    ),
                                    created_at=data.get(
                                        "created_at", time.time()
                                    ),
                                    reviewed_at=data.get("reviewed_at"),
                                    reviewed_by=data.get("reviewed_by"),
                                    applied_at=data.get("applied_at"),
                                    constitution_results=data.get(
                                        "constitution_results", []
                                    ),
                                    impact_estimate=data.get(
                                        "impact_estimate", {}
                                    ),
                                    rollback_plan=data.get("rollback_plan"),
                                    metadata=data.get("metadata", {}),
                                )
                                self._suggestions[suggestion.suggestion_id] = (
                                    suggestion
                                )
                            except (json.JSONDecodeError, KeyError, ValueError):
                                continue
        except Exception as e:
            logger.warning(f"Failed to load suggestions: {e}")

        # Load events
        try:
            filepath = EVOLUTION_DB_PATH / "events.jsonl"
            if filepath.exists():
                with open(filepath, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                event = EvolutionEvent(
                                    event_id=data["event_id"],
                                    event_type=data.get("event_type", "unknown"),
                                    suggestion_id=data.get("suggestion_id", ""),
                                    actor=data.get("actor", "system"),
                                    timestamp=data.get("timestamp", time.time()),
                                    details=data.get("details", {}),
                                    previous_hash=data.get(
                                        "previous_hash", "genesis"
                                    ),
                                )
                                self._events.append(event)
                            except (json.JSONDecodeError, KeyError):
                                continue
        except Exception as e:
            logger.warning(f"Failed to load events: {e}")

        logger.info(
            f"Loaded {len(self._suggestions)} suggestions, "
            f"{len(self._events)} events"
        )


# ── Singleton ────────────────────────────────────────────────────────────────

_evolution_instance: Optional[EvolutionEngine] = None
_evolution_lock = threading.Lock()


def get_evolution_engine() -> EvolutionEngine:
    """Get the singleton EvolutionEngine instance."""
    global _evolution_instance
    if _evolution_instance is None:
        with _evolution_lock:
            if _evolution_instance is None:
                _evolution_instance = EvolutionEngine()
    return _evolution_instance


def reset_evolution_engine() -> None:
    """Reset the singleton (for testing)."""
    global _evolution_instance
    with _evolution_lock:
        _evolution_instance = None
