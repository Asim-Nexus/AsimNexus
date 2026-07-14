"""
Dreaming Engine Routes
======================
REST API for the Dreaming Engine — background memory consolidation, dream cycles,
lesson extraction, pattern analysis, and automated bug triage.

Reference:
  - core/dreaming/dreaming_engine.py — Core DreamingEngine implementation
  - core/dreaming/bug_triage.py — Bug triage engine
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Dreaming")

router = APIRouter(tags=["Dreaming"])

# Module-level globals (set via init_dreaming)
orchestrator = None


def init_dreaming(app_globals: dict) -> None:
    """Initialize dreaming module with shared app state."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Dream Cycles ────────────────────────────────────────────────────────────


@router.post("/api/dreaming/cycle/trigger")
async def dreaming_trigger_cycle():
    """Manually trigger a dream cycle for memory consolidation.

    Returns:
      - cycle: The completed DreamCycle with lessons and patterns
    """
    try:
        from core.dreaming import DreamingEngine

        engine = DreamingEngine()
        await engine.start()

        return ok(data={
            "status": "dream_cycle_triggered",
            "message": "Dream cycle started. Check /api/dreaming/status for results.",
        })
    except Exception as e:
        logger.exception("Failed to trigger dream cycle")
        return error(str(e))


@router.get("/api/dreaming/cycles")
async def dreaming_cycles(
    limit: int = Query(10, description="Max cycles to return"),
):
    """Get recent dream cycles.

    Query params:
      - limit (int, optional): Max cycles (default: 10)

    Returns:
      - cycles: List of recent DreamCycle objects
    """
    try:
        from core.dreaming import DreamingEngine

        engine = DreamingEngine()
        status = engine.status()

        return ok(data={
            "cycles": status.get("cycles", []),
            "total_cycles": status.get("total_cycles", 0),
        })
    except Exception as e:
        logger.exception("Failed to get dream cycles")
        return error(str(e))


# ─── Lessons ─────────────────────────────────────────────────────────────────


@router.get("/api/dreaming/lessons")
async def dreaming_lessons(
    limit: int = Query(20, description="Max lessons to return"),
):
    """Get extracted lessons from dream cycles.

    Query params:
      - limit (int, optional): Max lessons (default: 20)

    Returns:
      - lessons: List of Lesson objects
    """
    try:
        from core.dreaming.dreaming_engine import _get_dream_lessons

        lessons = _get_dream_lessons(limit=limit)

        return ok(data={
            "lessons": lessons,
            "count": len(lessons),
        })
    except Exception as e:
        logger.exception("Failed to get lessons")
        return error(str(e))


# ─── Patterns ────────────────────────────────────────────────────────────────


@router.get("/api/dreaming/patterns")
async def dreaming_patterns():
    """Get detected patterns from dream analysis.

    Returns:
      - patterns: Dict of pattern categories with confidence scores
    """
    try:
        from core.dreaming import DreamingEngine

        engine = DreamingEngine()
        patterns = engine.get_patterns()

        return ok(data={
            "patterns": patterns,
        })
    except Exception as e:
        logger.exception("Failed to get patterns")
        return error(str(e))


# ─── Briefing ────────────────────────────────────────────────────────────────


@router.get("/api/dreaming/briefing")
async def dreaming_briefing():
    """Get the latest dream briefing.

    Returns:
      - briefing: Generated briefing text from recent lessons
    """
    try:
        from core.dreaming.dreaming_engine import (
            DreamCycle,
            _get_dream_lessons,
            generate_briefing,
        )

        lessons_data = _get_dream_lessons(limit=10)
        lessons = []
        for ld in lessons_data:
            from core.dreaming import Lesson

            lessons.append(Lesson(
                topic=ld.get("topic", ld.get("topic", "unknown")),
                summary=ld.get("summary", ld.get("insight", "")),
                source_messages=ld.get("source_messages", []),
                confidence=ld.get("confidence", 0.0),
                created_at=ld.get("created_at", ld.get("timestamp", "")),
            ))

        cycle = DreamCycle(
            cycle_id="briefing",
            started_at="",
            ended_at=None,
            messages_processed=0,
            lessons_extracted=len(lessons),
            memories_pruned=0,
            briefing="",
            status="completed",
        )
        briefing = generate_briefing(lessons, cycle)

        return ok(data={
            "briefing": briefing,
            "lessons_count": len(lessons),
        })
    except Exception as e:
        logger.exception("Failed to get briefing")
        return error(str(e))


# ─── Nightly Evolution ───────────────────────────────────────────────────────


@router.post("/api/dreaming/nightly-evolution")
async def dreaming_nightly_evolution(
    reflections: Optional[List[Dict[str, Any]]] = Body(None, description="Optional reflections to process"),
):
    """Trigger nightly evolution with optional reflections.

    Request body:
      - reflections (list, optional): List of reflection dicts to process

    Returns:
      - dreams: List of generated Dream objects
    """
    try:
        from core.dreaming import DreamingEngine

        engine = DreamingEngine()
        dreams = await engine.nightly_evolution(reflections=reflections)

        return ok(data={
            "dreams": [d.to_dict() if hasattr(d, "to_dict") else d for d in dreams],
            "count": len(dreams),
        })
    except Exception as e:
        logger.exception("Failed to run nightly evolution")
        return error(str(e))


# ─── Status ──────────────────────────────────────────────────────────────────


@router.get("/api/dreaming/status")
async def dreaming_status():
    """Get the current status of the dreaming engine.

    Returns:
      - status: DreamingEngine status with cycle info and metrics
    """
    try:
        from core.dreaming import DreamingEngine

        engine = DreamingEngine()
        status = engine.status()

        return ok(data=status)
    except Exception as e:
        logger.exception("Failed to get dreaming status")
        return error(str(e))


# ─── Bug Triage ──────────────────────────────────────────────────────────────


@router.get("/api/dreaming/bug-triage/stats")
async def dreaming_bug_triage_stats():
    """Get bug triage statistics.

    Returns:
      - stats: Bug triage statistics
    """
    try:
        from core.dreaming import get_bug_triage

        triage = get_bug_triage()
        stats = triage.get_stats()

        return ok(data=stats.to_dict() if hasattr(stats, "to_dict") else stats)
    except Exception as e:
        logger.exception("Failed to get bug triage stats")
        return error(str(e))


@router.get("/api/dreaming/bug-triage/reports")
async def dreaming_bug_reports(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, description="Max reports to return"),
):
    """Get bug reports from triage.

    Query params:
      - severity (str, optional): Filter by severity (critical/high/medium/low)
      - status (str, optional): Filter by status (open/in_progress/resolved/closed)
      - limit (int, optional): Max reports (default: 20)

    Returns:
      - reports: List of BugReport objects
    """
    try:
        from core.dreaming import get_bug_triage

        triage = get_bug_triage()
        # BugTriageEngine stores reports internally; get via stats
        stats = triage.get_stats()

        return ok(data={
            "reports": stats.get("recent_reports", []) if hasattr(stats, "get") else [],
            "total_reports": stats.get("total_reports", 0) if hasattr(stats, "get") else 0,
        })
    except Exception as e:
        logger.exception("Failed to get bug reports")
        return error(str(e))
