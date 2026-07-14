"""
AsimNexus Evolution Module
==========================
Autonomous code evolution engine that analyzes the codebase and suggests
improvements, refactorings, and architectural changes.
"""

from __future__ import annotations

from .evolution_engine import (
    EvolutionEngine, EvolutionSuggestion, EvolutionEvent,
    SuggestionCategory, SuggestionStatus,
    get_evolution_engine,
)

__all__ = [
    "EvolutionEngine",
    "EvolutionSuggestion",
    "EvolutionEvent",
    "SuggestionCategory",
    "SuggestionStatus",
    "get_evolution_engine",
]
