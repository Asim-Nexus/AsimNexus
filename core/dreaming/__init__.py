"""
AsimNexus Dreaming Module
=========================
Background memory consolidation — runs while the user is idle or sleeping.
Inspired by biological memory consolidation during REM sleep.
- Replays recent conversations and extracts lessons
- Detects repeated patterns / knowledge gaps
- Writes new summaries into vector memory
- Prunes old, low-relevance memories
- Generates "tomorrow's readiness" briefing
"""

from __future__ import annotations

from .dreaming_engine import DreamingEngine, Dream, DreamType, DreamCycle, Lesson
from .bug_triage import (
    BugTriageEngine, BugReport, BugSeverity, BugStatus,
    PipelineDecision, TriageStats, RegressionImpactSimulator,
    AIDraftGenerator, get_bug_triage,
)

__all__ = [
    "DreamingEngine",
    "Dream",
    "DreamType",
    "DreamCycle",
    "Lesson",
    "BugTriageEngine",
    "BugReport",
    "BugSeverity",
    "BugStatus",
    "PipelineDecision",
    "TriageStats",
    "RegressionImpactSimulator",
    "AIDraftGenerator",
    "get_bug_triage",
]
