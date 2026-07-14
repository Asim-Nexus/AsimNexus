"""
Evolution Bridge
================
Connects the EvolutionEngine and MirrorModule to the SelfBuilder and SelfKnowledge
systems, enabling autonomous code evolution based on detected patterns.

This bridge allows:
  - EvolutionEngine suggestions to be applied via SelfBuilder patches
  - MirrorModule reflections to feed into SelfKnowledge issues
  - Dreaming Engine lessons to be stored as knowledge entries
  - Autonomous patch generation from contradiction patterns
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from .self_knowledge import SelfKnowledge, IssueRecord, get_knowledge
from .self_builder import SelfBuilder, BuildResult, get_builder

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────

EVOLUTION_STORAGE_DIR = os.path.join(os.getcwd(), "data", "self_awareness", "evolution")
BRIDGE_STATE_FILE = "bridge_state.json"


# ──────────────────────────────────────────────
#  Data models
# ──────────────────────────────────────────────


@dataclass
class BridgeAction:
    """A recorded bridge action linking evolution to self-building."""

    action_id: str
    source_type: str  # "evolution_suggestion", "mirror_reflection", "dream_lesson", "contradiction_pattern"
    source_id: str
    source_title: str
    builder_action_id: Optional[str] = None
    status: str = "pending"  # "pending", "executed", "failed", "skipped"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────
#  EvolutionBridge
# ──────────────────────────────────────────────


class EvolutionBridge:
    """
    Bridges the gap between evolution detection and code modification.

    Listens to EvolutionEngine suggestions and MirrorModule reflections,
    converts them into SelfBuilder actions, and tracks the results.
    """

    def __init__(self, knowledge: Optional[SelfKnowledge] = None,
                 builder: Optional[SelfBuilder] = None) -> None:
        self.knowledge = knowledge or get_knowledge()
        self.builder = builder or get_builder()
        self._lock = threading.Lock()
        self._actions: List[BridgeAction] = []

        os.makedirs(EVOLUTION_STORAGE_DIR, exist_ok=True)
        self._load_state()

    # ── Public API ──────────────────────────────

    def process_evolution_suggestion(self, suggestion: Dict[str, Any]) -> BridgeAction:
        """
        Process an EvolutionEngine suggestion and attempt to apply it.

        Args:
            suggestion: EvolutionSuggestion.to_dict() output

        Returns:
            BridgeAction with the result.
        """
        suggestion_id = suggestion.get("suggestion_id", "unknown")
        title = suggestion.get("title", "")
        description = suggestion.get("description", "")
        category = suggestion.get("category", "unknown")
        metadata = suggestion.get("metadata", {})

        # Determine what kind of action to take based on category
        action_id = f"EVO-{len(self._actions) + 1}"

        if category == "code_improvement":
            # Try to apply as a code patch
            result = self._apply_code_improvement(suggestion)
        elif category == "architecture_change":
            # Record as knowledge for later review
            self.knowledge.store_knowledge(
                f"evolution:architecture:{suggestion_id}",
                suggestion,
                source="evolution_engine",
                metadata={"suggestion_id": suggestion_id},
            )
            result = BuildResult(success=True, summary="Recorded as knowledge for review")
        elif category == "config_change":
            # Record as knowledge
            self.knowledge.store_knowledge(
                f"evolution:config:{suggestion_id}",
                suggestion,
                source="evolution_engine",
            )
            result = BuildResult(success=True, summary="Config suggestion recorded")
        else:
            # Default: store as issue in knowledge base
            issue = IssueRecord(
                issue_id=f"EVO-{suggestion_id}",
                module=metadata.get("target_module", "unknown"),
                issue_type="improvement",
                description=f"[Evolution] {title}: {description}",
                severity="info",
                status="open",
                metadata={"suggestion_id": suggestion_id, "category": category},
            )
            self.knowledge.add_issue(issue)
            result = BuildResult(success=True, summary=f"Issue created: {issue.issue_id}")

        action = BridgeAction(
            action_id=action_id,
            source_type="evolution_suggestion",
            source_id=suggestion_id,
            source_title=title,
            builder_action_id=result.actions[0].action_id if result.actions else None,
            status="executed" if result.success else "failed",
            error=result.error,
            metadata={"category": category, "result_summary": result.summary},
        )
        self._record_action(action)
        return action

    def process_mirror_reflection(self, reflection: Dict[str, Any]) -> BridgeAction:
        """
        Process a MirrorModule reflection and store as knowledge.

        Args:
            reflection: MirrorReflection.to_dict() output

        Returns:
            BridgeAction with the result.
        """
        reflection_id = reflection.get("reflection_id", "unknown")
        intent = reflection.get("intent", "")
        contradictions = reflection.get("contradictions", [])
        balance_impact = reflection.get("balance_impact", 0.0)

        action_id = f"MIR-{len(self._actions) + 1}"

        # Store reflection in knowledge base
        self.knowledge.store_knowledge(
            f"mirror:reflection:{reflection_id}",
            reflection,
            source="mirror_module",
            metadata={"reflection_id": reflection_id, "balance_impact": balance_impact},
        )

        # If there are contradictions, create issues
        if contradictions:
            for i, contradiction in enumerate(contradictions):
                issue = IssueRecord(
                    issue_id=f"MIR-CON-{reflection_id}-{i}",
                    module="unknown",
                    issue_type="improvement",
                    description=f"[Mirror] Contradiction detected: {contradiction}",
                    severity="warning" if abs(balance_impact) > 0.5 else "info",
                    status="open",
                    metadata={"reflection_id": reflection_id, "contradiction": contradiction},
                )
                self.knowledge.add_issue(issue)

        action = BridgeAction(
            action_id=action_id,
            source_type="mirror_reflection",
            source_id=reflection_id,
            source_title=f"Reflection: {intent[:50]}",
            status="executed",
            metadata={
                "contradiction_count": len(contradictions),
                "balance_impact": balance_impact,
            },
        )
        self._record_action(action)
        return action

    def process_dream_lesson(self, lesson: Dict[str, Any]) -> BridgeAction:
        """
        Process a Dreaming Engine lesson and store as knowledge.

        Args:
            lesson: Lesson dict from dreaming_engine

        Returns:
            BridgeAction with the result.
        """
        lesson_id = lesson.get("lesson_id", f"dream_{len(self._actions) + 1}")
        summary = lesson.get("summary", "")
        topics = lesson.get("topics", [])

        action_id = f"DREAM-{len(self._actions) + 1}"

        # Store lesson in knowledge base
        self.knowledge.store_knowledge(
            f"dream:lesson:{lesson_id}",
            lesson,
            source="dreaming_engine",
            metadata={"topics": topics},
        )

        action = BridgeAction(
            action_id=action_id,
            source_type="dream_lesson",
            source_id=lesson_id,
            source_title=f"Dream Lesson: {summary[:50]}",
            status="executed",
            metadata={"topics": topics},
        )
        self._record_action(action)
        return action

    def get_actions(self, limit: int = 50) -> List[BridgeAction]:
        """Get recent bridge actions."""
        with self._lock:
            return list(reversed(self._actions[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        with self._lock:
            total = len(self._actions)
            by_source: Dict[str, int] = {}
            by_status: Dict[str, int] = {}
            for a in self._actions:
                by_source[a.source_type] = by_source.get(a.source_type, 0) + 1
                by_status[a.status] = by_status.get(a.status, 0) + 1
            return {
                "total_actions": total,
                "by_source": by_source,
                "by_status": by_status,
            }

    # ── Internal ───────────────────────────────

    def _apply_code_improvement(self, suggestion: Dict[str, Any]) -> BuildResult:
        """Try to apply a code improvement suggestion as a patch."""
        metadata = suggestion.get("metadata", {})
        target_file = metadata.get("target_file", "")
        search_text = metadata.get("search_text", "")
        replace_text = metadata.get("replace_text", "")

        if target_file and search_text and replace_text:
            return self.builder.apply_patch(
                filepath=target_file,
                search=search_text,
                replace=replace_text,
                description=f"[Evolution] {suggestion.get('title', '')}",
            )
        elif target_file:
            # No specific patch, just record as issue
            issue = IssueRecord(
                issue_id=f"EVO-PATCH-{suggestion.get('suggestion_id', 'unknown')}",
                module=target_file,
                issue_type="improvement",
                description=f"[Evolution] {suggestion.get('title', '')}: {suggestion.get('description', '')}",
                severity="info",
                status="open",
                metadata={"suggestion_id": suggestion.get("suggestion_id")},
            )
            self.knowledge.add_issue(issue)
            return BuildResult(success=True, summary=f"Issue created for {target_file}")

        return BuildResult(success=False, error="No actionable patch data in suggestion")

    def _record_action(self, action: BridgeAction) -> None:
        """Record a bridge action and persist."""
        with self._lock:
            self._actions.append(action)
            self._save_state()

    def _save_state(self) -> None:
        """Persist bridge state to disk."""
        try:
            filepath = os.path.join(EVOLUTION_STORAGE_DIR, BRIDGE_STATE_FILE)
            data = [asdict(a) for a in self._actions]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, PermissionError) as e:
            logger.error("Failed to save bridge state: %s", e)

    def _load_state(self) -> None:
        """Load bridge state from disk."""
        filepath = os.path.join(EVOLUTION_STORAGE_DIR, BRIDGE_STATE_FILE)
        if os.path.exists(filepath):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                self._actions = [BridgeAction(**a) for a in data]
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("Failed to load bridge state: %s", e)


# ── Convenience ────────────────────────────────

_default_bridge: Optional[EvolutionBridge] = None


def get_bridge() -> EvolutionBridge:
    """Get or create the default EvolutionBridge singleton."""
    global _default_bridge
    if _default_bridge is None:
        _default_bridge = EvolutionBridge()
    return _default_bridge


def process_suggestion(suggestion: Dict[str, Any]) -> BridgeAction:
    """Convenience: process a single evolution suggestion."""
    return get_bridge().process_evolution_suggestion(suggestion)


def process_reflection(reflection: Dict[str, Any]) -> BridgeAction:
    """Convenience: process a single mirror reflection."""
    return get_bridge().process_mirror_reflection(reflection)
