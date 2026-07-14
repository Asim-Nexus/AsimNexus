"""
AsimNexus Self-Awareness System
================================
Enables AsimNexus to understand its own codebase, architecture, components,
and build/modify itself autonomously.

Components:
  - CodebaseScanner: AST-based scanner that builds a knowledge graph of all modules
  - SelfKnowledge: Persistent knowledge base of module registry, dependencies, issues
  - SelfBuilder: Template-based code generation, import fixing, test generation
  - EvolutionBridge: Connects EvolutionEngine/DreamingEngine/MirrorModule to SelfBuilder
  - GapAnalyzer: Identifies gaps, inconsistencies, and improvement opportunities
  - AutoBuilder: Autonomous self-building loop with test-verify-rollback
"""

from __future__ import annotations

import logging
from typing import Optional

from .codebase_scanner import CodebaseScanner
from .self_knowledge import SelfKnowledge
from .self_builder import SelfBuilder
from .evolution_bridge import EvolutionBridge, get_bridge
from .gap_analyzer import GapAnalyzer, GapAnalysisResult, Gap
from .auto_builder import AutoBuilder, BuildCycle, get_auto_builder, reset_auto_builder

logger = logging.getLogger(__name__)

# Module-level singletons
_scanner: Optional[CodebaseScanner] = None
_knowledge: Optional[SelfKnowledge] = None
_builder: Optional[SelfBuilder] = None
_analyzer: Optional[GapAnalyzer] = None


def get_scanner() -> CodebaseScanner:
    """Get or create the singleton CodebaseScanner."""
    global _scanner
    if _scanner is None:
        _scanner = CodebaseScanner()
    return _scanner


def get_knowledge() -> SelfKnowledge:
    """Get or create the singleton SelfKnowledge."""
    global _knowledge
    if _knowledge is None:
        _knowledge = SelfKnowledge()
    return _knowledge


def get_builder() -> SelfBuilder:
    """Get or create the singleton SelfBuilder."""
    global _builder
    if _builder is None:
        _builder = SelfBuilder()
    return _builder


def get_gap_analyzer() -> GapAnalyzer:
    """Get or create the singleton GapAnalyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = GapAnalyzer(scanner=get_scanner(), knowledge=get_knowledge())
    return _analyzer


def reset_all() -> None:
    """Reset all singletons (for testing)."""
    global _scanner, _knowledge, _builder, _analyzer
    _scanner = None
    _knowledge = None
    _builder = None
    _analyzer = None
    reset_auto_builder()



# Re-export from root-level module: ai_improvements.py
from core.ai_improvements import (
    MultiModalProcessor,
    NepaliFineTuner,
    get_multimodal_processor,
    get_nepali_fine_tuner,
)


__all__ = [
    "CodebaseScanner",
    "SelfKnowledge",
    "SelfBuilder",
    "EvolutionBridge",
    "GapAnalyzer",
    "GapAnalysisResult",
    "Gap",
    "AutoBuilder",
    "BuildCycle",
    "get_scanner",
    "get_knowledge",
    "get_builder",
    "get_gap_analyzer",
    "get_bridge",
    "get_auto_builder",
    "reset_auto_builder",
    "reset_all",
]
