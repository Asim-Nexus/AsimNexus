#!/usr/bin/env python3
"""Patch Generator — AI-driven patch creation from code analysis results.

Consumes AnalysisReport from CodeAnalyzer and produces Patch objects
with concrete code changes. Supports multiple patch strategies:

- Auto-fix: Direct replacements for trivial issues (whitespace, line length)
- LLM-assisted: Uses local/cloud LLM to suggest fixes for complex issues
- Template-based: Applies known refactoring patterns

Typical usage::

    analyzer = CodeAnalyzer()
    report = analyzer.analyze_file("mesh/p2p_transport.py")
    generator = PatchGenerator()
    patches = generator.generate_patches(report)
    for patch in patches:
        print(f"{patch.patch_id}: {patch.description}")
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

from evolution.code_analyzer import (
    AnalysisReport,
    CodeIssue,
    IssueCategory,
    IssueSeverity,
)

logger = logging.getLogger(__name__)


class PatchStatus(Enum):
    """Lifecycle status of a generated patch."""
    PENDING = auto()
    VALIDATED = auto()
    APPROVED = auto()
    APPLIED = auto()
    REJECTED = auto()
    FAILED = auto()
    ROLLED_BACK = auto()


class PatchStrategy(Enum):
    """Strategy used to generate the patch."""
    AUTO_FIX = auto()       # Direct, deterministic fix
    LLM_SUGGESTED = auto()  # Fix suggested by LLM
    TEMPLATE = auto()       # Known refactoring template
    MANUAL = auto()         # Human-written patch


@dataclass
class PatchEdit:
    """A single edit operation within a patch."""
    file: str
    line_start: int
    line_end: int
    old_text: str
    new_text: str


@dataclass
class Patch:
    """A proposed code change with metadata."""
    patch_id: str
    description: str
    strategy: PatchStrategy
    status: PatchStatus = PatchStatus.PENDING
    edits: List[PatchEdit] = field(default_factory=list)
    source_issue: Optional[CodeIssue] = None
    risk_score: float = 0.0  # 0.0 = safe, 1.0 = risky
    created_at: str = ""
    applied_at: Optional[str] = None
    author: str = "auto-evolution"
    review_notes: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    @property
    def is_applied(self) -> bool:
        return self.status == PatchStatus.APPLIED

    @property
    def is_rejected(self) -> bool:
        return self.status == PatchStatus.REJECTED


class PatchGenerator:
    """Generates code patches from analysis reports.

    The generator evaluates each issue in a report and determines
    the best strategy to produce a fix. Simple issues are auto-fixed;
    complex issues are flagged for LLM assistance.
    """

    def __init__(self, llm_enabled: bool = True):
        self.llm_enabled = llm_enabled
        self._generated: Dict[str, Patch] = {}

    # ── Public API ──────────────────────────────────────────────────────────

    def generate_patches(self, report: AnalysisReport) -> List[Patch]:
        """Generate patches for all actionable issues in a report."""
        patches: List[Patch] = []

        for issue in report.issues:
            strategy = self._determine_strategy(issue)
            patch = self._create_patch(issue, strategy, report.target)
            if patch:
                patches.append(patch)
                self._generated[patch.patch_id] = patch

        return patches

    def generate_for_issue(self, issue: CodeIssue, source_file: str) -> Optional[Patch]:
        """Generate a patch for a single issue."""
        strategy = self._determine_strategy(issue)
        return self._create_patch(issue, strategy, source_file)

    def get_patch(self, patch_id: str) -> Optional[Patch]:
        """Retrieve a previously generated patch by ID."""
        return self._generated.get(patch_id)

    def get_all_patches(self) -> List[Patch]:
        """Get all generated patches."""
        return list(self._generated.values())

    def get_patches_by_status(self, status: PatchStatus) -> List[Patch]:
        """Filter patches by status."""
        return [p for p in self._generated.values() if p.status == status]

    def approve_patch(self, patch_id: str, notes: str = "") -> bool:
        """Mark a patch as approved for application."""
        patch = self._generated.get(patch_id)
        if not patch or patch.status != PatchStatus.VALIDATED:
            return False
        patch.status = PatchStatus.APPROVED
        patch.review_notes = notes
        return True

    def reject_patch(self, patch_id: str, notes: str = "") -> bool:
        """Mark a patch as rejected."""
        patch = self._generated.get(patch_id)
        if not patch:
            return False
        patch.status = PatchStatus.REJECTED
        patch.review_notes = notes
        return True

    def apply_patch(self, patch_id: str) -> bool:
        """Apply a patch to the filesystem."""
        patch = self._generated.get(patch_id)
        if not patch or patch.status != PatchStatus.APPROVED:
            logger.warning("Patch %s not approved; cannot apply", patch_id)
            return False

        try:
            for edit in patch.edits:
                self._apply_edit(edit)
            patch.status = PatchStatus.APPLIED
            patch.applied_at = datetime.utcnow().isoformat()
            logger.info("Patch %s applied successfully (%d edits)", patch_id, len(patch.edits))
            return True
        except Exception as exc:
            logger.error("Failed to apply patch %s: %s", patch_id, exc)
            patch.status = PatchStatus.FAILED
            return False

    def rollback_patch(self, patch_id: str) -> bool:
        """Rollback a previously applied patch."""
        patch = self._generated.get(patch_id)
        if not patch or patch.status != PatchStatus.APPLIED:
            return False

        try:
            # Reverse edits in reverse order
            for edit in reversed(patch.edits):
                self._rollback_edit(edit)
            patch.status = PatchStatus.ROLLED_BACK
            logger.info("Patch %s rolled back successfully", patch_id)
            return True
        except Exception as exc:
            logger.error("Failed to rollback patch %s: %s", patch_id, exc)
            return False

    # ── Internal methods ────────────────────────────────────────────────────

    def _determine_strategy(self, issue: CodeIssue) -> PatchStrategy:
        """Determine the best strategy for fixing an issue."""
        # Trivial issues: auto-fix
        if issue.category in (IssueCategory.STYLE,) and issue.severity in (
            IssueSeverity.INFO, IssueSeverity.WARNING
        ):
            return PatchStrategy.AUTO_FIX

        # Security issues need human review
        if issue.category == IssueCategory.SECURITY:
            return PatchStrategy.LLM_SUGGESTED

        # Complexity / anti-pattern: LLM or template
        if issue.category in (IssueCategory.COMPLEXITY, IssueCategory.ANTI_PATTERN):
            return PatchStrategy.LLM_SUGGESTED if self.llm_enabled else PatchStrategy.TEMPLATE

        # Best practice: template
        if issue.category == IssueCategory.BEST_PRACTICE:
            return PatchStrategy.TEMPLATE

        # Default: LLM if available
        return PatchStrategy.LLM_SUGGESTED if self.llm_enabled else PatchStrategy.AUTO_FIX

    def _create_patch(self, issue: CodeIssue, strategy: PatchStrategy,
                      target: str) -> Optional[Patch]:
        """Create a Patch object for a single issue."""
        # Only generate for actionable severities
        if issue.severity == IssueSeverity.INFO and strategy == PatchStrategy.AUTO_FIX:
            # Skip trivial auto-fix for info-level style issues unless critical
            if issue.category == IssueCategory.STYLE and "trailing whitespace" not in issue.message:
                return None

        patch_id = f"patch-{uuid.uuid4().hex[:12]}"
        description = f"[{strategy.name}] {issue.message}"

        # Build edits based on strategy
        edits: List[PatchEdit] = []

        if strategy == PatchStrategy.AUTO_FIX:
            edit = self._build_auto_fix(issue)
            if edit:
                edits.append(edit)

        risk_score = self._compute_risk(strategy, issue)

        patch = Patch(
            patch_id=patch_id,
            description=description,
            strategy=strategy,
            edits=edits,
            source_issue=issue,
            risk_score=risk_score,
        )

        # Auto-validate auto-fixes
        if strategy == PatchStrategy.AUTO_FIX and edits:
            patch.status = PatchStatus.VALIDATED

        return patch

    def _build_auto_fix(self, issue: CodeIssue) -> Optional[PatchEdit]:
        """Build a PatchEdit for trivially fixable issues."""
        # Trailing whitespace
        if "trailing whitespace" in issue.message:
            return PatchEdit(
                file=issue.file,
                line_start=issue.line,
                line_end=issue.line,
                old_text="",
                new_text="",  # Will strip whitespace on application
            )

        return None

    def _compute_risk(self, strategy: PatchStrategy, issue: CodeIssue) -> float:
        """Compute a risk score for a patch (0.0 = safe, 1.0 = risky)."""
        base = 0.0

        if strategy == PatchStrategy.AUTO_FIX:
            base = 0.1
        elif strategy == PatchStrategy.TEMPLATE:
            base = 0.3
        elif strategy == PatchStrategy.LLM_SUGGESTED:
            base = 0.6

        if issue.severity == IssueSeverity.CRITICAL:
            base += 0.2
        elif issue.severity == IssueSeverity.ERROR:
            base += 0.1

        if issue.category == IssueCategory.SECURITY:
            base += 0.2

        return min(base, 1.0)

    def _apply_edit(self, edit: PatchEdit):
        """Apply a single edit to a file."""
        if not os.path.exists(edit.file):
            raise FileNotFoundError(f"File not found: {edit.file}")

        with open(edit.file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if edit.old_text == "" and "trailing" in edit.__dict__.get("__repr__", ""):
            # Simple trailing whitespace removal
            if 1 <= edit.line_start <= len(lines):
                lines[edit.line_start - 1] = lines[edit.line_start - 1].rstrip() + "\n"
        else:
            # Text replacement
            old_lines = edit.old_text.split("\n")
            new_lines = edit.new_text.split("\n")
            if 1 <= edit.line_start <= len(lines):
                lines[edit.line_start - 1:edit.line_end] = [
                    l + "\n" for l in new_lines
                ]

        with open(edit.file, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def _rollback_edit(self, edit: PatchEdit):
        """Reverse a single edit."""
        if not os.path.exists(edit.file):
            raise FileNotFoundError(f"File not found: {edit.file}")

        with open(edit.file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Replace new text with old text
        new_lines = edit.new_text.split("\n")
        old_lines = edit.old_text.split("\n")
        if 1 <= edit.line_start <= len(lines):
            lines[edit.line_start - 1:edit.line_start + len(new_lines) - 1] = [
                l + "\n" for l in old_lines
            ]

        with open(edit.file, "w", encoding="utf-8") as f:
            f.writelines(lines)


def get_patch_generator(llm_enabled: bool = True) -> PatchGenerator:
    """Factory function to get a PatchGenerator instance."""
    return PatchGenerator(llm_enabled=llm_enabled)
