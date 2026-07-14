"""
Evolution Engine Routes
=======================
REST API for the Evolution Engine — autonomous code evolution suggestions,
events, statistics, and evolution history tracking.

Reference:
  - core/evolution/evolution_engine.py — Core EvolutionEngine implementation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Evolution")

router = APIRouter(tags=["Evolution"])

# Module-level globals (set via init_evolution)
orchestrator = None


def init_evolution(app_globals: dict) -> None:
    """Initialize evolution module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Suggestions ─────────────────────────────────────────────────────────────


@router.get("/api/evolution/suggestions")
async def evolution_suggestions(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Max suggestions to return"),
):
    """Get evolution suggestions.

    Query params:
      - category (str, optional): Filter by category (performance/security/feature/refactor/docs/test)
      - status (str, optional): Filter by status (pending/approved/rejected/implemented)
      - limit (int, optional): Max suggestions (default: 50)

    Returns:
      - suggestions: List of EvolutionSuggestion objects
    """
    try:
        from core.evolution import get_evolution_engine

        engine = get_evolution_engine()
        suggestions = engine.get_suggestions(category=category, status=status)

        result = suggestions[:limit] if isinstance(suggestions, list) else suggestions
        return ok(data={
            "suggestions": [s.to_dict() if hasattr(s, "to_dict") else s for s in result],
            "count": len(result),
        })
    except Exception as e:
        logger.exception("Failed to get evolution suggestions")
        return error(str(e))


@router.get("/api/evolution/suggestions/pending-review")
async def evolution_pending_review(
    limit: int = Query(20, description="Max suggestions to return"),
):
    """Get evolution suggestions pending human review.

    Query params:
      - limit (int, optional): Max suggestions (default: 20)

    Returns:
      - suggestions: List of EvolutionSuggestion objects pending review
    """
    try:
        from core.evolution import get_evolution_engine

        engine = get_evolution_engine()
        suggestions = engine.get_pending_review()

        result = suggestions[:limit] if isinstance(suggestions, list) else suggestions
        return ok(data={
            "suggestions": [s.to_dict() if hasattr(s, "to_dict") else s for s in result],
            "count": len(result),
        })
    except Exception as e:
        logger.exception("Failed to get pending review suggestions")
        return error(str(e))


@router.get("/api/evolution/suggestions/{suggestion_id}")
async def evolution_get_suggestion(suggestion_id: str):
    """Get a specific evolution suggestion by ID.

    Path params:
      - suggestion_id (str, required): The suggestion ID

    Returns:
      - suggestion: The EvolutionSuggestion object
    """
    try:
        from core.evolution import get_evolution_engine

        engine = get_evolution_engine()
        suggestion = engine.get_suggestion(suggestion_id)

        if suggestion is None:
            return error("Suggestion not found")

        return ok(data=suggestion.to_dict() if hasattr(suggestion, "to_dict") else suggestion)
    except Exception as e:
        logger.exception("Failed to get suggestion")
        return error(str(e))


@router.post("/api/evolution/suggestions/{suggestion_id}/approve")
async def evolution_approve_suggestion(suggestion_id: str):
    """Approve an evolution suggestion for implementation.

    Path params:
      - suggestion_id (str, required): The suggestion ID

    Returns:
      - suggestion: The updated EvolutionSuggestion
    """
    try:
        from core.evolution import get_evolution_engine, SuggestionStatus

        engine = get_evolution_engine()
        suggestion = engine.get_suggestion(suggestion_id)

        if suggestion is None:
            return error("Suggestion not found")

        # Update status to approved
        if hasattr(suggestion, "status"):
            suggestion.status = SuggestionStatus.APPROVED

        return ok(data={
            "suggestion_id": suggestion_id,
            "status": "approved",
            "message": "Suggestion approved for implementation",
        })
    except Exception as e:
        logger.exception("Failed to approve suggestion")
        return error(str(e))


@router.post("/api/evolution/suggestions/{suggestion_id}/reject")
async def evolution_reject_suggestion(
    suggestion_id: str,
    reason: str = Body("", embed=True),
):
    """Reject an evolution suggestion.

    Path params:
      - suggestion_id (str, required): The suggestion ID

    Request body:
      - reason (str, optional): Reason for rejection

    Returns:
      - suggestion: The updated EvolutionSuggestion
    """
    try:
        from core.evolution import get_evolution_engine, SuggestionStatus

        engine = get_evolution_engine()
        suggestion = engine.get_suggestion(suggestion_id)

        if suggestion is None:
            return error("Suggestion not found")

        if hasattr(suggestion, "status"):
            suggestion.status = SuggestionStatus.REJECTED

        return ok(data={
            "suggestion_id": suggestion_id,
            "status": "rejected",
            "reason": reason,
        })
    except Exception as e:
        logger.exception("Failed to reject suggestion")
        return error(str(e))


# ─── Events ──────────────────────────────────────────────────────────────────


@router.get("/api/evolution/events")
async def evolution_events(
    limit: int = Query(50, description="Max events to return"),
):
    """Get evolution events.

    Query params:
      - limit (int, optional): Max events (default: 50)

    Returns:
      - events: List of EvolutionEvent objects
    """
    try:
        from core.evolution import get_evolution_engine

        engine = get_evolution_engine()
        events = engine.get_events()

        result = events[:limit] if isinstance(events, list) else events
        return ok(data={
            "events": [e.to_dict() if hasattr(e, "to_dict") else e for e in result],
            "count": len(result),
        })
    except Exception as e:
        logger.exception("Failed to get evolution events")
        return error(str(e))


# ─── Statistics ──────────────────────────────────────────────────────────────


@router.get("/api/evolution/stats")
async def evolution_stats():
    """Get evolution engine statistics.

    Returns:
      - stats: Evolution statistics with counts and metrics
    """
    try:
        from core.evolution import get_evolution_engine

        engine = get_evolution_engine()
        stats = engine.get_stats()

        return ok(data=stats.to_dict() if hasattr(stats, "to_dict") else stats)
    except Exception as e:
        logger.exception("Failed to get evolution stats")
        return error(str(e))


# ─── History ─────────────────────────────────────────────────────────────────


@router.get("/api/evolution/history")
async def evolution_history(
    limit: int = Query(50, description="Max history entries to return"),
):
    """Get evolution history.

    Query params:
      - limit (int, optional): Max history entries (default: 50)

    Returns:
      - history: Evolution history entries
    """
    try:
        from core.evolution import get_evolution_engine

        engine = get_evolution_engine()
        history = engine.get_evolution_history()

        result = history[:limit] if isinstance(history, list) else history
        return ok(data={
            "history": [h.to_dict() if hasattr(h, "to_dict") else h for h in result],
            "count": len(result),
        })
    except Exception as e:
        logger.exception("Failed to get evolution history")
        return error(str(e))
