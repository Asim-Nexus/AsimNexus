"""
Dreaming Engine — Mirror Module Shim
======================================
Backward-compatible re-export from the consolidated core dreaming engine.

The canonical implementation now lives at:
    core/dreaming/dreaming_engine.py

All types and classes are re-exported here so existing imports from
``core.mirror.dreaming_engine`` continue to work without modification.
"""

from __future__ import annotations

from core.dreaming.dreaming_engine import (
    DreamingEngine,
    Dream,
    DreamType,
    DreamCycle,
    Lesson,
)

__all__ = [
    "DreamingEngine",
    "Dream",
    "DreamType",
    "DreamCycle",
    "Lesson",
]
