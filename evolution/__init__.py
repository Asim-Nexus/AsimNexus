#!/usr/bin/env python3
"""Self-Evolving Code Engine (Phase 8).

Enables AsimNexus to autonomously analyze, patch, test, and deploy its own code
within constitutional bounds. This package provides the foundational modules for
code analysis, automated patch generation, self-testing, constitutional guard
integration, and auto-deployment.

Modules:
    code_analyzer: Static analysis and improvement identification
    patch_generator: AI-driven patch creation from analysis results
    test_runner: Automated test execution and regression detection
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = [
    "CodeAnalyzer",
    "PatchGenerator",
    "TestRunner",
    "get_code_analyzer",
    "get_patch_generator",
    "get_test_runner",
]

# Global singletons
_code_analyzer: Optional["CodeAnalyzer"] = None
_patch_generator: Optional["PatchGenerator"] = None
_test_runner: Optional["TestRunner"] = None


def get_code_analyzer() -> "CodeAnalyzer":
    """Get or create the singleton CodeAnalyzer instance."""
    global _code_analyzer
    if _code_analyzer is None:
        from evolution.code_analyzer import CodeAnalyzer
        _code_analyzer = CodeAnalyzer()
    return _code_analyzer


def get_patch_generator() -> "PatchGenerator":
    """Get or create the singleton PatchGenerator instance."""
    global _patch_generator
    if _patch_generator is None:
        from evolution.patch_generator import PatchGenerator
        _patch_generator = PatchGenerator()
    return _patch_generator


def get_test_runner() -> "TestRunner":
    """Get or create the singleton TestRunner instance."""
    global _test_runner
    if _test_runner is None:
        from evolution.test_runner import TestRunner
        _test_runner = TestRunner()
    return _test_runner


def reset_all():
    """Reset all singleton instances (for testing)."""
    global _code_analyzer, _patch_generator, _test_runner
    _code_analyzer = None
    _patch_generator = None
    _test_runner = None
