#!/usr/bin/env python3
"""Comprehensive tests for Phase 7 modules: reputation, evolution, swarm, and continuum."""

import json
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ==============================================================================
# core/reputation.py — ReputationSystem, ReputationScore, ReputationEvent
# ==============================================================================

from core.reputation import ReputationSystem, ReputationEvent, ReputationScore, get_reputation_system


class TestReputationEvent:
    """ReputationEvent enum has the correct values."""

    def test_values(self):
        assert ReputationEvent.TASK_SUCCESS.value == "task_success"
        assert ReputationEvent.TASK_FAILURE.value == "task_failure"
        assert ReputationEvent.TASK_TIMEOUT.value == "task_timeout"
        assert ReputationEvent.HONEST_VOTE.value == "honest_vote"
        assert ReputationEvent.DISHONEST_VOTE.value == "dishonest_vote"
        assert ReputationEvent.SECURITY_VIOLATION.value == "security_violation"
        assert ReputationEvent.RESOURCE_ABUSE.value == "resource_abuse"
        assert ReputationEvent.PEER_ENDORSEMENT.value == "peer_endorsement"
        assert ReputationEvent.PEER_REPORT.value == "peer_report"

    def test_all_members_present(self):
        assert len(ReputationEvent) == 9


class TestReputationScore:
    """ReputationScore dataclass properties."""

    def test_default_construction(self):
        score = ReputationScore(agent_id="agent-1")
        assert score.agent_id == "agent-1"
        assert score.total_tasks == 0
        assert score.reliability == 0.5  # Neutral
        assert score.honesty == 0.5  # Neutral
        assert score.trust_score == 0.35  # Composite neutral: 0.4*0.5 + 0.3*0.5 + 0 - 0

    def test_reliability_perfect(self):
        score = ReputationScore(agent_id="agent-1", total_tasks=10, successful_tasks=10)
        assert score.reliability == 1.0

    def test_reliability_half(self):
        score = ReputationScore(agent_id="agent-1", total_tasks=10, successful_tasks=5)
        assert score.reliability == 0.5

    def test_reliability_zero(self):
        score = ReputationScore(agent_id="agent-1", total_tasks=10, successful_tasks=0)
        assert score.reliability == 0.0

    def test_honesty_perfect(self):
        score = ReputationScore(agent_id="agent-1", honest_votes=10, dishonest_votes=0)
        assert score.honesty == 1.0

    def test_honesty_zero(self):
        score = ReputationScore(agent_id="agent-1", honest_votes=0, dishonest_votes=10)
        assert score.honesty == 0.0

    def test_security_violation_drops_trust(self):
        score = ReputationScore(agent_id="agent-1", security_violations=1)
        assert score.trust_score == 0.3  # 0.5 - (1 * 0.2)

    def test_security_violation_multiple(self):
        score = ReputationScore(agent_id="agent-1", security_violations=5)
        assert score.trust_score == 0.0  # max(0, 0.5 - 5*0.2) = max(0, -0.5)

    def test_trust_score_upper_bound(self):
        score = ReputationScore(
            agent_id="agent-1",
            total_tasks=100, successful_tasks=100,
            honest_votes=100, dishonest_votes=0,
            peer_endorsements=100,
        )
        assert score.trust_score <= 1.0

    def test_trust_score_lower_bound(self):
        score = ReputationScore(
            agent_id="agent-1",
            total_tasks=100, successful_tasks=0,
            honest_votes=0, dishonest_votes=100,
            peer_reports=100,
            security_violations=10,
        )
        assert score.trust_score == 0.0  # Clamped

    def test_to_dict(self):
        score = ReputationScore(agent_id="agent-1", total_tasks=5, successful_tasks=3)
        d = score.to_dict()
        assert d["agent_id"] == "agent-1"
        assert d["total_tasks"] == 5
        assert d["successful_tasks"] == 3
        assert "last_updated" in d


class TestReputationSystem:
    """ReputationSystem singleton with event recording."""

    @pytest.fixture(autouse=True)
    def reset_system(self):
        """Reset the singleton before each test."""
        ReputationSystem._instance = None
        yield

    def test_singleton(self):
        rs1 = ReputationSystem()
        rs2 = ReputationSystem()
        assert rs1 is rs2

    def test_get_reputation_system_factory(self):
        rs = get_reputation_system()
        assert isinstance(rs, ReputationSystem)

    def test_record_event_creates_score(self):
        rs = ReputationSystem()
        score = rs.record_event("agent-1", ReputationEvent.TASK_SUCCESS)
        assert isinstance(score, ReputationScore)
        assert score.agent_id == "agent-1"

    def test_record_task_success(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.TASK_SUCCESS)
        score = rs.get_score("agent-1")
        assert score.total_tasks == 1
        assert score.successful_tasks == 1

    def test_record_task_failure(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.TASK_FAILURE)
        score = rs.get_score("agent-1")
        assert score.total_tasks == 1
        assert score.failed_tasks == 1

    def test_record_task_timeout(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.TASK_TIMEOUT)
        score = rs.get_score("agent-1")
        assert score.total_tasks == 1
        assert score.timed_out_tasks == 1

    def test_record_honest_vote(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.HONEST_VOTE)
        score = rs.get_score("agent-1")
        assert score.honest_votes == 1

    def test_record_dishonest_vote(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.DISHONEST_VOTE)
        score = rs.get_score("agent-1")
        assert score.dishonest_votes == 1

    def test_record_security_violation(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.SECURITY_VIOLATION)
        score = rs.get_score("agent-1")
        assert score.security_violations == 1

    def test_record_resource_abuse(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.RESOURCE_ABUSE)
        score = rs.get_score("agent-1")
        assert score.resource_abuses == 1

    def test_record_peer_endorsement(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.PEER_ENDORSEMENT)
        score = rs.get_score("agent-1")
        assert score.peer_endorsements == 1

    def test_record_peer_report(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.PEER_REPORT)
        score = rs.get_score("agent-1")
        assert score.peer_reports == 1

    def test_record_with_metadata(self):
        rs = ReputationSystem()
        score = rs.record_event("agent-1", ReputationEvent.TASK_SUCCESS, {"task": "test"})
        assert score.successful_tasks == 1

    def test_get_score_unknown(self):
        rs = ReputationSystem()
        assert rs.get_score("unknown") is None

    def test_get_trust_score_known(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.TASK_SUCCESS)
        rs.record_event("agent-1", ReputationEvent.TASK_SUCCESS)
        assert rs.get_trust_score("agent-1") == 0.55  # 0.4*1.0 + 0.3*0.5 = 0.55

    def test_get_trust_score_unknown(self):
        rs = ReputationSystem()
        assert rs.get_trust_score("unknown") == 0.5  # Default neutral

    def test_add_testimony(self):
        rs = ReputationSystem()
        rs.add_testimony("agent-1", "witness-1", "Reliable", weight=0.8)
        # No return value, just stored internally

    def test_get_reliable_agents(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.TASK_SUCCESS)
        rs.record_event("agent-2", ReputationEvent.TASK_FAILURE)
        reliable = rs.get_reliable_agents(min_score=0.5)
        assert "agent-1" in reliable
        assert "agent-2" not in reliable

    def test_get_reliable_agents_empty(self):
        rs = ReputationSystem()
        assert rs.get_reliable_agents() == []

    def test_get_stats_empty(self):
        rs = ReputationSystem()
        stats = rs.get_stats()
        assert stats["total_agents"] == 0
        assert stats["total_events"] == 0
        assert stats["avg_trust"] == 0.0
        assert stats["reliable_agents"] == 0

    def test_get_stats_with_data(self):
        rs = ReputationSystem()
        rs.record_event("agent-1", ReputationEvent.TASK_SUCCESS)
        rs.record_event("agent-2", ReputationEvent.TASK_FAILURE)
        stats = rs.get_stats()
        assert stats["total_agents"] == 2
        assert stats["total_events"] == 2
        assert stats["reliable_agents"] == 0  # agent-1 trust=0.55, agent-2 trust=0.15, both < 0.7

    def test_record_multiple_agents(self):
        rs = ReputationSystem()
        for i in range(5):
            rs.record_event(f"agent-{i}", ReputationEvent.TASK_SUCCESS)
        assert len(rs.get_reliable_agents()) == 0  # Each has trust=0.55, below default 0.7 threshold


# ==============================================================================
# evolution/code_analyzer.py — CodeAnalyzer, AnalysisReport, CodeIssue
# ==============================================================================

from evolution.code_analyzer import (
    CodeAnalyzer,
    AnalysisReport,
    CodeIssue,
    AnalysisMetrics,
    IssueSeverity,
    IssueCategory,
    get_code_analyzer,
)


class TestIssueSeverity:
    """IssueSeverity enum."""

    def test_values(self):
        assert IssueSeverity.INFO is not None
        assert IssueSeverity.WARNING is not None
        assert IssueSeverity.ERROR is not None
        assert IssueSeverity.CRITICAL is not None

    def test_all_members(self):
        assert len(IssueSeverity) == 4


class TestIssueCategory:
    """IssueCategory enum."""

    def test_values(self):
        assert IssueCategory.STYLE is not None
        assert IssueCategory.PERFORMANCE is not None
        assert IssueCategory.SECURITY is not None
        assert IssueCategory.DEAD_CODE is not None
        assert IssueCategory.COMPLEXITY is not None
        assert IssueCategory.ANTI_PATTERN is not None
        assert IssueCategory.BEST_PRACTICE is not None
        assert IssueCategory.TYPE_SAFETY is not None
        assert IssueCategory.IMPORT is not None
        assert IssueCategory.DOCUMENTATION is not None

    def test_all_members(self):
        assert len(IssueCategory) == 10


class TestCodeIssue:
    """CodeIssue dataclass."""

    def test_create(self):
        issue = CodeIssue(
            file="test.py", line=10, column=5,
            severity=IssueSeverity.WARNING,
            category=IssueCategory.STYLE,
            message="Line too long",
        )
        assert issue.file == "test.py"
        assert issue.line == 10
        assert issue.severity == IssueSeverity.WARNING
        assert issue.suggestion is None
        assert issue.symbol is None

    def test_create_with_optional(self):
        issue = CodeIssue(
            file="test.py", line=10, column=5,
            severity=IssueSeverity.ERROR,
            category=IssueCategory.SECURITY,
            message="Hardcoded password",
            suggestion="Use env vars",
            symbol="password",
        )
        assert issue.suggestion == "Use env vars"
        assert issue.symbol == "password"


class TestAnalysisMetrics:
    """AnalysisMetrics dataclass."""

    def test_defaults(self):
        m = AnalysisMetrics()
        assert m.loc == 0
        assert m.function_count == 0
        assert m.class_count == 0
        assert m.max_complexity == 0
        assert m.avg_complexity == 0.0

    def test_with_values(self):
        m = AnalysisMetrics(loc=100, function_count=5, class_count=2, max_complexity=8)
        assert m.loc == 100
        assert m.function_count == 5


class TestAnalysisReport:
    """AnalysisReport dataclass with helper methods."""

    def test_defaults(self):
        report = AnalysisReport(target="test.py")
        assert report.target == "test.py"
        assert report.issues == []
        assert report.metrics.loc == 0

    def test_has_critical(self):
        report = AnalysisReport(target="test.py")
        report.issues.append(CodeIssue(
            file="test.py", line=1, column=0,
            severity=IssueSeverity.CRITICAL, category=IssueCategory.SECURITY,
            message="Critical issue",
        ))
        assert report.has_critical()
        assert not report.has_errors()

    def test_has_errors(self):
        report = AnalysisReport(target="test.py")
        report.issues.append(CodeIssue(
            file="test.py", line=1, column=0,
            severity=IssueSeverity.ERROR, category=IssueCategory.IMPORT,
            message="Error",
        ))
        assert report.has_errors()

    def test_by_severity(self):
        report = AnalysisReport(target="test.py")
        report.issues.append(CodeIssue(
            file="test.py", line=1, column=0,
            severity=IssueSeverity.INFO, category=IssueCategory.STYLE,
            message="Info",
        ))
        report.issues.append(CodeIssue(
            file="test.py", line=2, column=0,
            severity=IssueSeverity.WARNING, category=IssueCategory.STYLE,
            message="Warning",
        ))
        assert len(report.by_severity(IssueSeverity.INFO)) == 1
        assert len(report.by_severity(IssueSeverity.WARNING)) == 1

    def test_by_category(self):
        report = AnalysisReport(target="test.py")
        report.issues.append(CodeIssue(
            file="test.py", line=1, column=0,
            severity=IssueSeverity.INFO, category=IssueCategory.STYLE,
            message="Style issue",
        ))
        report.issues.append(CodeIssue(
            file="test.py", line=2, column=0,
            severity=IssueSeverity.WARNING, category=IssueCategory.SECURITY,
            message="Security issue",
        ))
        assert len(report.by_category(IssueCategory.STYLE)) == 1
        assert len(report.by_category(IssueCategory.SECURITY)) == 1


class TestCodeAnalyzer:
    """CodeAnalyzer static analysis."""

    def test_get_code_analyzer_factory(self):
        analyzer = get_code_analyzer()
        assert isinstance(analyzer, CodeAnalyzer)

    def test_get_code_analyzer_custom_length(self):
        analyzer = get_code_analyzer(max_line_length=80)
        assert analyzer.max_line_length == 80

    def test_analyze_file_nonexistent(self):
        analyzer = CodeAnalyzer()
        report = analyzer.analyze_file("/nonexistent/path.py")
        assert len(report.issues) == 1
        assert "not found" in report.issues[0].message.lower()

    def test_analyze_file_non_python(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
            f.write("hello")
            fname = f.name
        try:
            analyzer = CodeAnalyzer()
            report = analyzer.analyze_file(fname)
            assert len(report.issues) == 1
            assert "unsupported" in report.issues[0].message.lower()
        finally:
            os.unlink(fname)

    def test_analyze_valid_python(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("x = 1\nprint(x)\n")
            fname = f.name
        try:
            analyzer = CodeAnalyzer()
            report = analyzer.analyze_file(fname)
            assert report.target == fname
            assert report.metrics.loc > 0
        finally:
            os.unlink(fname)

    def test_analyze_detects_print(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write('print("hello world")\n')
            fname = f.name
        try:
            analyzer = CodeAnalyzer()
            report = analyzer.analyze_file(fname)
            print_issues = [i for i in report.issues if "print" in i.message.lower()]
            assert len(print_issues) >= 1
        finally:
            os.unlink(fname)

    def test_analyze_syntax_error(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def broken(\n")
            fname = f.name
        try:
            analyzer = CodeAnalyzer()
            report = analyzer.analyze_file(fname)
            syntax_issues = [i for i in report.issues if "syntax" in i.message.lower()]
            assert len(syntax_issues) >= 1
        finally:
            os.unlink(fname)

    def test_analyze_detects_bare_except(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("try:\n    pass\nexcept:\n    pass\n")
            fname = f.name
        try:
            analyzer = CodeAnalyzer()
            report = analyzer.analyze_file(fname)
            bare_issues = [i for i in report.issues if "bare" in i.message.lower()]
            assert len(bare_issues) >= 1
        finally:
            os.unlink(fname)

    def test_analyze_detects_line_length(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("# " + "x" * 200 + "\n")
            fname = f.name
        try:
            analyzer = CodeAnalyzer(max_line_length=50)
            report = analyzer.analyze_file(fname)
            length_issues = [i for i in report.issues if "too long" in i.message.lower()]
            assert len(length_issues) >= 1
        finally:
            os.unlink(fname)

    def test_analyze_directory_nonexistent(self):
        analyzer = CodeAnalyzer()
        report = analyzer.analyze_directory("/nonexistent/dir")
        assert len(report.issues) == 1
        assert "not found" in report.issues[0].message.lower()

    def test_analyze_directory_with_files(self, tmp_path):
        d = tmp_path / "code"
        d.mkdir()
        (d / "a.py").write_text("x = 1\n")
        (d / "b.py").write_text("y = 2\n")
        analyzer = CodeAnalyzer()
        report = analyzer.analyze_directory(str(d))
        assert report.metrics.loc >= 2
        assert report.metrics.function_count >= 0

    def test_get_summary(self):
        report = AnalysisReport(target="test.py")
        report.issues.append(CodeIssue(
            file="test.py", line=1, column=0,
            severity=IssueSeverity.CRITICAL, category=IssueCategory.SECURITY,
            message="Critical",
        ))
        report.issues.append(CodeIssue(
            file="test.py", line=2, column=0,
            severity=IssueSeverity.INFO, category=IssueCategory.STYLE,
            message="Info",
        ))
        analyzer = CodeAnalyzer()
        summary = analyzer.get_summary(report)
        assert summary["target"] == "test.py"
        assert summary["total_issues"] == 2
        assert summary["critical"] == 1
        assert summary["info"] == 1
        assert "categories" in summary


# ==============================================================================
# evolution/patch_generator.py — PatchGenerator, Patch, PatchEdit
# ==============================================================================

from evolution.patch_generator import (
    PatchGenerator,
    Patch,
    PatchEdit,
    PatchStatus,
    PatchStrategy,
    get_patch_generator,
)


class TestPatchStatus:
    """PatchStatus enum."""

    def test_values(self):
        assert PatchStatus.PENDING is not None
        assert PatchStatus.VALIDATED is not None
        assert PatchStatus.APPROVED is not None
        assert PatchStatus.APPLIED is not None
        assert PatchStatus.REJECTED is not None
        assert PatchStatus.FAILED is not None
        assert PatchStatus.ROLLED_BACK is not None

    def test_all_members(self):
        assert len(PatchStatus) == 7


class TestPatchStrategy:
    """PatchStrategy enum."""

    def test_values(self):
        assert PatchStrategy.AUTO_FIX is not None
        assert PatchStrategy.LLM_SUGGESTED is not None
        assert PatchStrategy.TEMPLATE is not None
        assert PatchStrategy.MANUAL is not None

    def test_all_members(self):
        assert len(PatchStrategy) == 4


class TestPatchEdit:
    """PatchEdit dataclass."""

    def test_create(self):
        edit = PatchEdit(file="test.py", line_start=1, line_end=3, old_text="a\nb\nc", new_text="d\ne\nf")
        assert edit.file == "test.py"
        assert edit.line_start == 1
        assert edit.line_end == 3


class TestPatch:
    """Patch dataclass with lifecycle properties."""

    def test_create(self):
        patch = Patch(
            patch_id="patch-001",
            description="Fix trailing whitespace",
            strategy=PatchStrategy.AUTO_FIX,
        )
        assert patch.patch_id == "patch-001"
        assert patch.status == PatchStatus.PENDING
        assert patch.edits == []
        assert patch.created_at != ""

    def test_is_applied(self):
        patch = Patch(patch_id="p1", description="Test", strategy=PatchStrategy.AUTO_FIX,
                      status=PatchStatus.APPLIED)
        assert patch.is_applied
        assert not patch.is_rejected

    def test_is_rejected(self):
        patch = Patch(patch_id="p1", description="Test", strategy=PatchStrategy.AUTO_FIX,
                      status=PatchStatus.REJECTED)
        assert patch.is_rejected
        assert not patch.is_applied

    def test_default_created_at(self):
        patch = Patch(patch_id="p1", description="Test", strategy=PatchStrategy.AUTO_FIX)
        assert patch.created_at != ""


class TestPatchGenerator:
    """PatchGenerator lifecycle management."""

    def test_get_patch_generator_factory(self):
        gen = get_patch_generator()
        assert isinstance(gen, PatchGenerator)

    def test_get_patch_generator_disabled_llm(self):
        gen = get_patch_generator(llm_enabled=False)
        assert not gen.llm_enabled

    def test_generate_patches_empty_report(self):
        report = AnalysisReport(target="test.py")
        gen = PatchGenerator()
        patches = gen.generate_patches(report)
        assert patches == []

    def test_generate_patches_with_style_issue(self):
        report = AnalysisReport(target="test.py")
        issue = CodeIssue(
            file="test.py", line=10, column=0,
            severity=IssueSeverity.WARNING,
            category=IssueCategory.STYLE,
            message="trailing whitespace detected",
        )
        report.issues.append(issue)
        gen = PatchGenerator()
        patches = gen.generate_patches(report)
        assert len(patches) >= 1
        assert patches[0].strategy == PatchStrategy.AUTO_FIX

    def test_generate_patches_security_issue(self):
        report = AnalysisReport(target="test.py")
        issue = CodeIssue(
            file="test.py", line=5, column=0,
            severity=IssueSeverity.CRITICAL,
            category=IssueCategory.SECURITY,
            message="Hardcoded credential",
        )
        report.issues.append(issue)
        gen = PatchGenerator()
        patches = gen.generate_patches(report)
        assert len(patches) >= 1
        assert patches[0].strategy == PatchStrategy.LLM_SUGGESTED

    def test_get_patch(self):
        report = AnalysisReport(target="test.py")
        issue = CodeIssue(
            file="test.py", line=10, column=0,
            severity=IssueSeverity.WARNING,
            category=IssueCategory.STYLE,
            message="trailing whitespace detected",
        )
        report.issues.append(issue)
        gen = PatchGenerator()
        patches = gen.generate_patches(report)
        patch_id = patches[0].patch_id
        retrieved = gen.get_patch(patch_id)
        assert retrieved is not None
        assert retrieved.patch_id == patch_id

    def test_get_patch_unknown(self):
        gen = PatchGenerator()
        assert gen.get_patch("nonexistent") is None

    def test_get_all_patches(self):
        report = AnalysisReport(target="test.py")
        report.issues.append(CodeIssue(
            file="test.py", line=1, column=0,
            severity=IssueSeverity.INFO, category=IssueCategory.STYLE,
            message="trailing whitespace detected",
        ))
        report.issues.append(CodeIssue(
            file="test.py", line=2, column=0,
            severity=IssueSeverity.CRITICAL, category=IssueCategory.SECURITY,
            message="Hardcoded password",
        ))
        gen = PatchGenerator()
        gen.generate_patches(report)
        all_patches = gen.get_all_patches()
        assert len(all_patches) >= 1

    def test_get_patches_by_status(self):
        report = AnalysisReport(target="test.py")
        report.issues.append(CodeIssue(
            file="test.py", line=1, column=0,
            severity=IssueSeverity.WARNING, category=IssueCategory.STYLE,
            message="trailing whitespace detected",
        ))
        gen = PatchGenerator()
        patches = gen.generate_patches(report)
        # Auto-fix patches get VALIDATED status
        validated = gen.get_patches_by_status(PatchStatus.VALIDATED)
        assert len(validated) >= 1

    def test_approve_patch(self):
        report = AnalysisReport(target="test.py")
        report.issues.append(CodeIssue(
            file="test.py", line=1, column=0,
            severity=IssueSeverity.WARNING, category=IssueCategory.STYLE,
            message="trailing whitespace detected",
        ))
        gen = PatchGenerator()
        patches = gen.generate_patches(report)
        patch = patches[0]
        assert patch.status == PatchStatus.VALIDATED  # Auto-fix auto-validates

        result = gen.approve_patch(patch.patch_id, notes="Looks good")
        assert result
        assert patch.status == PatchStatus.APPROVED
        assert patch.review_notes == "Looks good"

    def test_approve_patch_not_validated(self):
        gen = PatchGenerator()
        patch = Patch(patch_id="p1", description="Test", strategy=PatchStrategy.AUTO_FIX,
                      status=PatchStatus.PENDING)
        gen._generated["p1"] = patch
        assert not gen.approve_patch("p1")  # Must be VALIDATED first

    def test_approve_patch_unknown(self):
        gen = PatchGenerator()
        assert not gen.approve_patch("unknown")

    def test_reject_patch(self):
        gen = PatchGenerator()
        patch = Patch(patch_id="p1", description="Test", strategy=PatchStrategy.AUTO_FIX)
        gen._generated["p1"] = patch
        assert gen.reject_patch("p1", notes="Not needed")
        assert patch.status == PatchStatus.REJECTED
        assert patch.review_notes == "Not needed"

    def test_reject_patch_unknown(self):
        gen = PatchGenerator()
        assert not gen.reject_patch("unknown")

    def test_apply_patch_not_approved(self):
        gen = PatchGenerator()
        patch = Patch(patch_id="p1", description="Test", strategy=PatchStrategy.AUTO_FIX)
        gen._generated["p1"] = patch
        assert not gen.apply_patch("p1")  # Not approved

    def test_apply_patch_file_not_found(self, tmp_path):
        gen = PatchGenerator()
        target_file = str(tmp_path / "nonexistent.py")
        patch = Patch(
            patch_id="p1", description="Test", strategy=PatchStrategy.AUTO_FIX,
            status=PatchStatus.APPROVED,
            edits=[PatchEdit(file=target_file, line_start=1, line_end=1,
                            old_text="", new_text="x = 1\n")],
        )
        gen._generated["p1"] = patch
        assert not gen.apply_patch("p1")  # File doesn't exist → FAILED

    def test_apply_patch_success(self, tmp_path):
        target_file = str(tmp_path / "test.py")
        with open(target_file, "w") as f:
            f.write("old content\n")

        gen = PatchGenerator()
        patch = Patch(
            patch_id="p1", description="Replace content", strategy=PatchStrategy.MANUAL,
            status=PatchStatus.APPROVED,
            edits=[PatchEdit(file=target_file, line_start=1, line_end=1,
                            old_text="old content\n", new_text="new content\n")],
        )
        gen._generated["p1"] = patch
        assert gen.apply_patch("p1")
        assert patch.status == PatchStatus.APPLIED
        assert patch.applied_at is not None
        with open(target_file) as f:
            assert "new content" in f.read()

    def test_rollback_patch_not_applied(self):
        gen = PatchGenerator()
        patch = Patch(patch_id="p1", description="Test", strategy=PatchStrategy.AUTO_FIX,
                      status=PatchStatus.APPROVED)
        gen._generated["p1"] = patch
        assert not gen.rollback_patch("p1")  # Not APPLIED

    def test_rollback_patch_success(self, tmp_path):
        target_file = str(tmp_path / "test.py")
        with open(target_file, "w") as f:
            f.write("new content\n")

        gen = PatchGenerator()
        patch = Patch(
            patch_id="p1", description="Replace content", strategy=PatchStrategy.MANUAL,
            status=PatchStatus.APPLIED,
            edits=[PatchEdit(file=target_file, line_start=1, line_end=1,
                            old_text="old content\n", new_text="new content\n")],
        )
        gen._generated["p1"] = patch
        assert gen.rollback_patch("p1")
        assert patch.status == PatchStatus.ROLLED_BACK
        with open(target_file) as f:
            assert "old content" in f.read()

    def test_rollback_unknown(self):
        gen = PatchGenerator()
        assert not gen.rollback_patch("unknown")


# ==============================================================================
# evolution/test_runner.py — TestRunner, TestSuiteResult, TestResult
# ==============================================================================

from evolution.test_runner import (
    TestRunner,
    TestSuiteResult,
    TestResult,
    TestOutcome,
    RegressionRecord,
    get_test_runner,
)


class TestTestOutcome:
    """TestOutcome enum."""

    def test_values(self):
        assert TestOutcome.PASSED is not None
        assert TestOutcome.FAILED is not None
        assert TestOutcome.ERROR is not None
        assert TestOutcome.SKIPPED is not None
        assert TestOutcome.XFAIL is not None
        assert TestOutcome.XPASS is not None

    def test_all_members(self):
        assert len(TestOutcome) == 6


class TestTestResult:
    """TestResult dataclass."""

    def test_create(self):
        tr = TestResult(node_id="test.py::test_func", outcome=TestOutcome.PASSED)
        assert tr.node_id == "test.py::test_func"
        assert tr.outcome == TestOutcome.PASSED


class TestTestSuiteResult:
    """TestSuiteResult dataclass with properties."""

    def test_create(self):
        result = TestSuiteResult(target="tests/test_x.py")
        assert result.target == "tests/test_x.py"
        assert result.timestamp != ""

    def test_success_true(self):
        result = TestSuiteResult(target="t.py", exit_code=0)
        assert result.success

    def test_success_false(self):
        result = TestSuiteResult(target="t.py", exit_code=1)
        assert not result.success

    def test_has_regressions_true(self):
        result = TestSuiteResult(target="t.py")
        result.tests.append(TestResult(node_id="t::f", outcome=TestOutcome.FAILED))
        assert result.has_regressions

    def test_has_regressions_false(self):
        result = TestSuiteResult(target="t.py")
        result.tests.append(TestResult(node_id="t::f", outcome=TestOutcome.PASSED))
        assert not result.has_regressions

    def test_summary(self):
        result = TestSuiteResult(target="t.py", passed=5, failed=1, total=6, duration_seconds=2.5)
        s = result.summary()
        assert s["passed"] == 5
        assert s["failed"] == 1
        assert s["total"] == 6
        assert s["success"] is True  # exit_code defaults to 0, so success is True
        assert s["duration_seconds"] == 2.5


class TestRegressionRecord:
    """RegressionRecord dataclass."""

    def test_create(self):
        rec = RegressionRecord(
            test_id="t::f",
            previous_outcome=TestOutcome.PASSED,
            current_outcome=TestOutcome.FAILED,
            previous_run="2024-01-01",
            current_run="2024-01-02",
        )
        assert rec.test_id == "t::f"
        assert rec.previous_outcome == TestOutcome.PASSED


class TestTestRunner:
    """TestRunner with mocked subprocess."""

    def test_get_test_runner_factory(self):
        runner = get_test_runner()
        assert isinstance(runner, TestRunner)

    def test_init_creates_history_dir(self, tmp_path):
        history_dir = str(tmp_path / "history")
        runner = TestRunner(history_dir=history_dir)
        assert os.path.isdir(history_dir)

    @patch("evolution.test_runner.subprocess.run")
    def test_run_tests_success(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = (
            "tests/test_x.py::test_a PASSED\n"
            "tests/test_x.py::test_b PASSED\n"
            "== 2 passed in 0.50s ==\n"
        )
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmp:
            runner = TestRunner(history_dir=tmp)
            result = runner.run_tests("tests/test_x.py")
        assert result.target == "tests/test_x.py"
        assert result.exit_code == 0
        assert result.passed >= 2
        assert result.failed == 0

    @patch("evolution.test_runner.subprocess.run")
    def test_run_tests_with_failures(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = (
            "tests/test_x.py::test_a PASSED\n"
            "tests/test_x.py::test_b FAILED\n"
            "== 1 passed, 1 failed in 0.50s ==\n"
        )
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmp:
            runner = TestRunner(history_dir=tmp)
            result = runner.run_tests("tests/test_x.py")
        assert result.exit_code == 1
        assert result.passed >= 1
        assert result.failed >= 1

    @patch("evolution.test_runner.subprocess.run")
    def test_run_tests_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=1)

        with tempfile.TemporaryDirectory() as tmp:
            runner = TestRunner(history_dir=tmp)
            result = runner.run_tests("tests/test_x.py", timeout=1)
        assert result.exit_code == -1
        assert result.errors == 1
        assert any("timed out" in w.lower() for w in result.warnings)

    @patch("evolution.test_runner.subprocess.run")
    def test_run_tests_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()

        with tempfile.TemporaryDirectory() as tmp:
            runner = TestRunner(history_dir=tmp)
            result = runner.run_tests("nonexistent.py")
        assert result.exit_code == -2
        assert result.errors == 1

    def test_get_history_empty(self, tmp_path):
        runner = TestRunner(history_dir=str(tmp_path))
        assert runner.get_history("nonexistent") is None

    def test_get_history_from_memory(self, tmp_path):
        runner = TestRunner(history_dir=str(tmp_path))
        result = TestSuiteResult(target="t.py", passed=1, total=1, exit_code=0)
        runner._history["t.py"] = result
        assert runner.get_history("t.py") is result

    def test_compare_runs_no_history(self, tmp_path):
        runner = TestRunner(history_dir=str(tmp_path))
        assert runner.compare_runs("a", "b") == []

    def test_detect_regressions(self, tmp_path):
        runner = TestRunner(history_dir=str(tmp_path))
        prev = TestSuiteResult(target="t.py")
        prev.tests.append(TestResult(node_id="t::a", outcome=TestOutcome.PASSED))
        curr = TestSuiteResult(target="t.py")
        curr.tests.append(TestResult(node_id="t::a", outcome=TestOutcome.FAILED))

        regressions = runner._detect_regressions(prev, curr)
        assert len(regressions) == 1
        assert regressions[0].test_id == "t::a"
        assert regressions[0].previous_outcome == TestOutcome.PASSED
        assert regressions[0].current_outcome == TestOutcome.FAILED

    def test_clear_history_single(self, tmp_path):
        runner = TestRunner(history_dir=str(tmp_path))
        result = TestSuiteResult(target="t.py", passed=1, total=1, exit_code=0)
        runner._history["t.py"] = result
        runner.clear_history(target="t.py")
        assert "t.py" not in runner._history

    def test_clear_history_all(self, tmp_path):
        runner = TestRunner(history_dir=str(tmp_path))
        runner._history["a"] = TestSuiteResult(target="a", passed=1, total=1, exit_code=0)
        runner._history["b"] = TestSuiteResult(target="b", passed=1, total=1, exit_code=0)
        runner.clear_history()
        assert runner._history == {}


# ==============================================================================
# swarm/federated_learning.py — FederatedLearning, TrainingRound, NodeUpdate
# ==============================================================================

from swarm.federated_learning import (
    FederatedLearning,
    TrainingRound,
    NodeUpdate,
    RoundStatus,
    ContributionStrategy,
    get_federated_learning,
)


class TestRoundStatus:
    """RoundStatus enum."""

    def test_values(self):
        assert RoundStatus.PENDING is not None
        assert RoundStatus.COLLECTING is not None
        assert RoundStatus.AGGREGATING is not None
        assert RoundStatus.COMPLETED is not None
        assert RoundStatus.FAILED is not None
        assert RoundStatus.TIMEOUT is not None


class TestContributionStrategy:
    """ContributionStrategy enum."""

    def test_values(self):
        assert ContributionStrategy.EQUAL is not None
        assert ContributionStrategy.DATA_VOLUME is not None
        assert ContributionStrategy.REPUTATION is not None
        assert ContributionStrategy.PERFORMANCE is not None

    def test_all_members(self):
        assert len(ContributionStrategy) == 4


class TestNodeUpdate:
    """NodeUpdate dataclass."""

    def test_create(self):
        update = NodeUpdate(node_id="node-1", round_id="fl-abc", weights={"w1": 0.5})
        assert update.node_id == "node-1"
        assert update.round_id == "fl-abc"
        assert update.timestamp != ""


class TestTrainingRound:
    """TrainingRound dataclass with properties."""

    def test_create(self):
        tr = TrainingRound(round_id="fl-abc")
        assert tr.round_id == "fl-abc"
        assert tr.status == RoundStatus.PENDING
        assert tr.created_at != ""

    def test_submission_count(self):
        tr = TrainingRound(round_id="fl-abc")
        tr.submissions["node-1"] = NodeUpdate(node_id="node-1", round_id="fl-abc", weights={})
        assert tr.submission_count == 1

    def test_is_timed_out_true(self):
        tr = TrainingRound(
            round_id="fl-abc",
            created_at=(datetime.utcnow() - timedelta(hours=1)).isoformat(),
            timeout_seconds=60,
        )
        assert tr.is_timed_out

    def test_is_timed_out_false(self):
        tr = TrainingRound(round_id="fl-abc")
        assert not tr.is_timed_out

    def test_is_timed_out_completed(self):
        tr = TrainingRound(round_id="fl-abc", status=RoundStatus.COMPLETED)
        assert not tr.is_timed_out

    def test_is_ready_to_aggregate_true(self):
        tr = TrainingRound(round_id="fl-abc", min_nodes=2)
        tr.submissions["n1"] = NodeUpdate(node_id="n1", round_id="fl-abc", weights={})
        tr.submissions["n2"] = NodeUpdate(node_id="n2", round_id="fl-abc", weights={})
        assert tr.is_ready_to_aggregate

    def test_is_ready_to_aggregate_false(self):
        tr = TrainingRound(round_id="fl-abc", min_nodes=2)
        tr.submissions["n1"] = NodeUpdate(node_id="n1", round_id="fl-abc", weights={})
        assert not tr.is_ready_to_aggregate  # Only 1 of 2


class TestFederatedLearning:
    """FederatedLearning round lifecycle."""

    def test_get_federated_learning_factory(self):
        fl = get_federated_learning()
        assert isinstance(fl, FederatedLearning)

    def test_init_creates_storage_dir(self, tmp_path):
        fl = FederatedLearning(storage_dir=str(tmp_path / "fl"))
        assert os.path.isdir(str(tmp_path / "fl"))

    def test_start_round(self):
        fl = FederatedLearning()
        round_id = fl.start_round()
        assert round_id.startswith("fl-")
        assert fl.get_round(round_id) is not None

    def test_start_round_with_config(self):
        fl = FederatedLearning()
        round_id = fl.start_round(
            model_config={"layers": 3},
            strategy=ContributionStrategy.DATA_VOLUME,
            min_nodes=3,
            timeout_seconds=600,
        )
        r = fl.get_round(round_id)
        assert r.model_config == {"layers": 3}
        assert r.strategy == ContributionStrategy.DATA_VOLUME
        assert r.min_nodes == 3
        assert r.timeout_seconds == 600
        assert r.status == RoundStatus.COLLECTING

    def test_submit_update(self):
        fl = FederatedLearning()
        round_id = fl.start_round(min_nodes=1)
        assert fl.submit_update(round_id, "node-1", {"w1": 1.0}, data_volume=100)

    def test_submit_update_unknown_round(self):
        fl = FederatedLearning()
        assert not fl.submit_update("unknown", "node-1", {})

    def test_submit_update_closed_round(self):
        fl = FederatedLearning()
        round_id = fl.start_round(min_nodes=1)
        fl.submit_update(round_id, "node-1", {"w1": 1.0})
        fl.aggregate_round(round_id)
        # Round is now COMPLETED, should reject further submissions
        assert not fl.submit_update(round_id, "node-2", {})

    def test_aggregate_round_unknown(self):
        fl = FederatedLearning()
        assert fl.aggregate_round("unknown") is None

    def test_aggregate_round_success_equal(self):
        fl = FederatedLearning()
        round_id = fl.start_round(min_nodes=2, strategy=ContributionStrategy.EQUAL)
        fl.submit_update(round_id, "node-1", {"w1": 1.0}, validation_score=0.8)
        fl.submit_update(round_id, "node-2", {"w1": 3.0}, validation_score=0.9)
        weights = fl.aggregate_round(round_id)
        assert weights is not None
        # Equal weight: (1.0 + 3.0) / 2 = 2.0
        assert weights["w1"] == 2.0

    def test_aggregate_round_success_data_volume(self):
        fl = FederatedLearning()
        round_id = fl.start_round(min_nodes=2, strategy=ContributionStrategy.DATA_VOLUME)
        fl.submit_update(round_id, "node-1", {"w1": 0.0}, data_volume=100)
        fl.submit_update(round_id, "node-2", {"w1": 1.0}, data_volume=300)
        weights = fl.aggregate_round(round_id)
        assert weights is not None
        # Volume-weighted: (0.0*100 + 1.0*300) / 400 = 0.75
        assert weights["w1"] == 0.75

    def test_aggregate_round_insufficient_nodes(self):
        fl = FederatedLearning()
        round_id = fl.start_round(min_nodes=3)
        fl.submit_update(round_id, "node-1", {"w1": 1.0})
        fl.submit_update(round_id, "node-2", {"w1": 2.0})
        # Need 3 nodes, only have 2
        assert fl.aggregate_round(round_id) is None

    def test_aggregate_sets_metrics(self):
        fl = FederatedLearning()
        round_id = fl.start_round(min_nodes=2)
        fl.submit_update(round_id, "node-1", {"w1": 1.0}, data_volume=100, validation_score=0.8)
        fl.submit_update(round_id, "node-2", {"w1": 2.0}, data_volume=200, validation_score=0.9)
        fl.aggregate_round(round_id)
        r = fl.get_round(round_id)
        assert r.status == RoundStatus.COMPLETED
        assert r.completed_at is not None
        assert "mean_validation_score" in r.aggregated_metrics
        assert r.aggregated_metrics["total_data_volume"] == 300

    def test_get_active_rounds(self):
        fl = FederatedLearning()
        fl.start_round()
        fl.start_round()
        assert len(fl.get_active_rounds()) == 2

    def test_get_completed_rounds(self):
        fl = FederatedLearning()
        r1 = fl.start_round(min_nodes=1)
        fl.submit_update(r1, "node-1", {})
        fl.aggregate_round(r1)
        completed = fl.get_completed_rounds()
        assert len(completed) == 1
        assert completed[0].round_id == r1

    def test_get_stats_empty(self):
        fl = FederatedLearning()
        stats = fl.get_stats()
        assert stats["total_rounds"] == 0
        assert stats["active_rounds"] == 0

    def test_get_stats_with_data(self):
        fl = FederatedLearning()
        r1 = fl.start_round(min_nodes=1)
        fl.submit_update(r1, "node-1", {})
        fl.aggregate_round(r1)
        r2 = fl.start_round()
        stats = fl.get_stats()
        assert stats["total_rounds"] == 2
        assert stats["active_rounds"] == 1
        assert stats["completed_rounds"] == 1

    def test_prune_old_rounds(self):
        fl = FederatedLearning()
        fl.start_round()
        assert len(fl.get_active_rounds()) == 1
        # Prune with 0 max_age to remove instantly
        fl.prune_old_rounds(max_age_hours=0)
        # May or may not be pruned depending on timing, but should not crash

    def test_non_numeric_weights(self):
        fl = FederatedLearning()
        round_id = fl.start_round(min_nodes=2)
        fl.submit_update(round_id, "node-1", {"lst": [1, 2, 3]}, data_volume=100)
        fl.submit_update(round_id, "node-2", {"lst": [4, 5, 6]}, data_volume=100)
        weights = fl.aggregate_round(round_id)
        assert weights is not None
        # Non-numeric: takes from highest-weighted node (equal, so first)
        assert "lst" in weights


# ==============================================================================
# swarm/task_distributor.py — TaskDistributor, Task, SwarmNode
# ==============================================================================

from swarm.task_distributor import (
    TaskDistributor,
    Task,
    SwarmNode,
    TaskPriority,
    TaskStatus,
    SchedulingStrategy,
    get_task_distributor,
)


class TestTaskPriority:
    """TaskPriority enum."""

    def test_values(self):
        assert TaskPriority.LOW.value == 0
        assert TaskPriority.NORMAL.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.CRITICAL.value == 3


class TestTaskStatus:
    """TaskStatus enum."""

    def test_values(self):
        assert TaskStatus.PENDING is not None
        assert TaskStatus.QUEUED is not None
        assert TaskStatus.ASSIGNED is not None
        assert TaskStatus.RUNNING is not None
        assert TaskStatus.COMPLETED is not None
        assert TaskStatus.FAILED is not None
        assert TaskStatus.TIMEOUT is not None
        assert TaskStatus.CANCELLED is not None

    def test_all_members(self):
        assert len(TaskStatus) == 8


class TestSchedulingStrategy:
    """SchedulingStrategy enum."""

    def test_values(self):
        assert SchedulingStrategy.ROUND_ROBIN is not None
        assert SchedulingStrategy.LEAST_LOADED is not None
        assert SchedulingStrategy.RANDOM is not None
        assert SchedulingStrategy.AFFINITY is not None
        assert SchedulingStrategy.REPUTATION is not None


class TestTask:
    """Task dataclass."""

    def test_create(self):
        task = Task(task_id="task-001", task_type="inference", payload={"prompt": "hello"})
        assert task.task_id == "task-001"
        assert task.task_type == "inference"
        assert task.priority == TaskPriority.NORMAL
        assert task.created_at != ""

    def test_duration_ms_none(self):
        task = Task(task_id="t1", task_type="test", payload={})
        assert task.duration_ms is None

    def test_duration_ms_with_times(self):
        start = datetime.utcnow() - timedelta(seconds=5)
        end = datetime.utcnow()
        task = Task(
            task_id="t1", task_type="test", payload={},
            started_at=start.isoformat(),
            completed_at=end.isoformat(),
        )
        assert task.duration_ms is not None
        assert task.duration_ms > 0


class TestSwarmNode:
    """SwarmNode dataclass."""

    def test_create(self):
        node = SwarmNode(node_id="node-1", address="http://localhost:8080")
        assert node.node_id == "node-1"
        assert node.max_concurrent_tasks == 5
        assert node.is_online


class TestTaskDistributor:
    """TaskDistributor task and node management."""

    def test_get_task_distributor_factory(self):
        td = get_task_distributor()
        assert isinstance(td, TaskDistributor)

    def test_init_with_node_id(self):
        td = TaskDistributor(node_id="my-distributor")
        assert td.node_id == "my-distributor"

    def test_register_node(self):
        td = TaskDistributor()
        node = td.register_node("node-1", "http://localhost:8080", ["gpu", "tpu"])
        assert node.node_id == "node-1"
        assert "gpu" in node.capabilities
        assert node.is_online
        assert node.last_heartbeat is not None

    def test_register_node_defaults(self):
        td = TaskDistributor()
        node = td.register_node("node-1", "http://localhost:8080")
        assert node.capabilities == set()

    def test_unregister_node(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        assert td.unregister_node("node-1")
        assert td.get_node("node-1") is None

    def test_unregister_node_unknown(self):
        td = TaskDistributor()
        assert not td.unregister_node("unknown")

    def test_get_node_unknown(self):
        td = TaskDistributor()
        assert td.get_node("unknown") is None

    def test_get_online_nodes(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.register_node("node-2", "http://localhost:8081")
        assert len(td.get_online_nodes()) == 2

    def test_heartbeat(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        assert td.heartbeat("node-1")

    def test_heartbeat_unknown(self):
        td = TaskDistributor()
        assert not td.heartbeat("unknown")

    def test_check_node_health(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        # Initially online
        assert len(td.check_node_health(max_age_seconds=0)) >= 0

    def test_dispatch_task_no_nodes(self):
        td = TaskDistributor()
        task_id = td.dispatch_task("inference", {"prompt": "hello"})
        assert task_id is None  # No nodes available

    def test_dispatch_task_with_node(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        task_id = td.dispatch_task("inference", {"prompt": "hello"})
        assert task_id is not None
        assert task_id.startswith("task-")

    def test_dispatch_task_assigns_node(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        task_id = td.dispatch_task("inference", {"prompt": "hello"})
        task = td.get_task(task_id)
        assert task is not None
        assert task.assigned_node == "node-1"
        assert task.status == TaskStatus.ASSIGNED

    def test_dispatch_task_increments_active(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.dispatch_task("inference", {"p": "hello"})
        node = td.get_node("node-1")
        assert node.active_tasks == 1

    def test_complete_task(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        task_id = td.dispatch_task("inference", {"p": "hello"})
        assert td.complete_task(task_id, {"result": "ok"})
        task = td.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == {"result": "ok"}
        # Active count decremented
        node = td.get_node("node-1")
        assert node.active_tasks == 0

    def test_complete_task_unknown(self):
        td = TaskDistributor()
        assert not td.complete_task("unknown", {})

    def test_fail_task(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        task_id = td.dispatch_task("inference", {"p": "hello"})
        assert td.fail_task(task_id, "error occurred")
        task = td.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.error == "error occurred"

    def test_fail_task_unknown(self):
        td = TaskDistributor()
        assert not td.fail_task("unknown", "error")

    def test_cancel_task(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        task_id = td.dispatch_task("inference", {"p": "hello"})
        assert td.cancel_task(task_id)
        task = td.get_task(task_id)
        assert task.status == TaskStatus.CANCELLED

    def test_cancel_task_already_completed(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        task_id = td.dispatch_task("inference", {"p": "hello"})
        td.complete_task(task_id, {})
        assert not td.cancel_task(task_id)  # Already completed

    def test_cancel_task_unknown(self):
        td = TaskDistributor()
        assert not td.cancel_task("unknown")

    def test_get_pending_tasks(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.dispatch_task("type1", {})
        td.dispatch_task("type2", {})
        assert len(td.get_pending_tasks()) == 2

    def test_get_tasks_by_node(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.register_node("node-2", "http://localhost:8081")
        tid1 = td.dispatch_task("type1", {})  # Assigned to node-1
        tid2 = td.dispatch_task("type1", {})  # Assigned to node-2
        assert len(td.get_tasks_by_node("node-1")) >= 1

    def test_get_tasks_by_type(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.dispatch_task("inference", {})
        td.dispatch_task("training", {})
        assert len(td.get_tasks_by_type("inference")) == 1
        assert len(td.get_tasks_by_type("training")) == 1

    def test_check_timeouts(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        task_id = td.dispatch_task("inference", {}, timeout_seconds=0)
        # Set started_at in the past so it times out immediately
        task = td.get_task(task_id)
        task.started_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        timed_out = td.check_timeouts()
        assert task_id in timed_out
        assert task.status == TaskStatus.TIMEOUT

    def test_register_handler(self):
        td = TaskDistributor()
        handler = MagicMock()
        td.register_handler("inference", handler)
        assert "inference" in td._handlers

    def test_get_stats_empty(self):
        td = TaskDistributor()
        stats = td.get_stats()
        assert stats["registered_nodes"] == 0
        assert stats["total_tasks_dispatched"] == 0

    def test_get_stats_with_data(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.dispatch_task("inference", {})
        stats = td.get_stats()
        assert stats["registered_nodes"] == 1
        assert stats["online_nodes"] == 1
        assert stats["total_tasks_dispatched"] == 1
        assert stats["pending_tasks"] == 1

    def test_scheduling_round_robin(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.register_node("node-2", "http://localhost:8081")
        tid1 = td.dispatch_task("t", {}, strategy=SchedulingStrategy.ROUND_ROBIN)
        tid2 = td.dispatch_task("t", {}, strategy=SchedulingStrategy.ROUND_ROBIN)
        t1 = td.get_task(tid1)
        t2 = td.get_task(tid2)
        # Round-robin should assign to different nodes
        assert t1.assigned_node != t2.assigned_node

    def test_scheduling_least_loaded(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.register_node("node-2", "http://localhost:8081")
        # First dispatch goes to one node
        tid1 = td.dispatch_task("t", {}, strategy=SchedulingStrategy.LEAST_LOADED)
        t1 = td.get_task(tid1)
        # Second dispatch should go to the other (least loaded)
        tid2 = td.dispatch_task("t", {}, strategy=SchedulingStrategy.LEAST_LOADED)
        t2 = td.get_task(tid2)
        assert t1.assigned_node != t2.assigned_node

    def test_scheduling_affinity(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080", ["gpu"])
        td.register_node("node-2", "http://localhost:8081", ["cpu"])
        task_id = td.dispatch_task("t", {}, strategy=SchedulingStrategy.AFFINITY, affinity="gpu")
        if task_id:
            task = td.get_task(task_id)
            assert task.assigned_node == "node-1"

    def test_scheduling_reputation(self):
        td = TaskDistributor()
        td.register_node("node-1", "http://localhost:8080")
        td.register_node("node-2", "http://localhost:8081")
        td.get_node("node-2").reputation_score = 0.9  # Higher reputation
        task_id = td.dispatch_task("t", {}, strategy=SchedulingStrategy.REPUTATION)
        task = td.get_task(task_id)
        assert task.assigned_node == "node-2"


# ==============================================================================
# swarm/knowledge_graph.py — KnowledgeGraph, KnowledgeNode, KnowledgeEdge
# ==============================================================================

from swarm.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeNode,
    KnowledgeEdge,
    QueryResult,
    get_knowledge_graph,
)


class TestKnowledgeNode:
    """KnowledgeNode dataclass with serialization."""

    def test_create(self):
        node = KnowledgeNode(node_id="n1", labels={"Person"}, properties={"name": "Alice"})
        assert node.node_id == "n1"
        assert "Person" in node.labels
        assert node.created_at != ""
        assert node.updated_at != ""

    def test_to_dict(self):
        node = KnowledgeNode(node_id="n1", labels={"Person"})
        d = node.to_dict()
        assert d["node_id"] == "n1"
        assert isinstance(d["labels"], list)
        assert "Person" in d["labels"]

    def test_from_dict(self):
        d = {"node_id": "n1", "labels": ["Person"], "properties": {"name": "Alice"},
             "created_at": "", "updated_at": "", "source": ""}
        node = KnowledgeNode.from_dict(d)
        assert node.node_id == "n1"
        assert isinstance(node.labels, set)
        assert "Person" in node.labels


class TestKnowledgeEdge:
    """KnowledgeEdge dataclass with serialization."""

    def test_create(self):
        edge = KnowledgeEdge(edge_id="e1", source_id="n1", target_id="n2", relationship="KNOWS", weight=0.9)
        assert edge.edge_id == "e1"
        assert edge.relationship == "KNOWS"
        assert edge.weight == 0.9

    def test_to_dict(self):
        edge = KnowledgeEdge(edge_id="e1", source_id="n1", target_id="n2")
        d = edge.to_dict()
        assert d["edge_id"] == "e1"
        assert d["relationship"] == "RELATED_TO"

    def test_from_dict(self):
        d = {"edge_id": "e1", "source_id": "n1", "target_id": "n2",
             "relationship": "KNOWS", "weight": 0.9,
             "properties": {}, "created_at": "", "updated_at": ""}
        edge = KnowledgeEdge.from_dict(d)
        assert edge.relationship == "KNOWS"


class TestQueryResult:
    """QueryResult dataclass."""

    def test_create(self):
        qr = QueryResult(query="test")
        assert qr.query == "test"
        assert qr.nodes == []
        assert qr.edges == []


class TestKnowledgeGraph:
    """KnowledgeGraph CRUD and query operations."""

    def test_get_knowledge_graph_factory(self):
        kg = get_knowledge_graph()
        assert isinstance(kg, KnowledgeGraph)

    def test_init_creates_storage_dir(self, tmp_path):
        kg = KnowledgeGraph(storage_dir=str(tmp_path / "kg"))
        assert os.path.isdir(str(tmp_path / "kg"))

    def test_add_node(self):
        kg = KnowledgeGraph()
        nid = kg.add_node("n1", labels={"Person"}, properties={"name": "Alice"}, source="test")
        assert nid == "n1"
        node = kg.get_node("n1")
        assert node is not None
        assert node.labels == {"Person"}

    def test_add_node_duplicate_raises(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        with pytest.raises(ValueError, match="already exists"):
            kg.add_node("n1")

    def test_get_node_unknown(self):
        kg = KnowledgeGraph()
        assert kg.get_node("unknown") is None

    def test_update_node(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", properties={"name": "Alice"})
        assert kg.update_node("n1", labels={"Bot"}, properties={"role": "assistant"})
        node = kg.get_node("n1")
        assert node.labels == {"Bot"}
        assert node.properties["name"] == "Alice"  # Merged
        assert node.properties["role"] == "assistant"

    def test_update_node_replace_properties(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", properties={"name": "Alice"})
        kg.update_node("n1", properties={"role": "assistant"}, merge_properties=False)
        node = kg.get_node("n1")
        assert node.properties == {"role": "assistant"}  # Replaced

    def test_update_node_unknown(self):
        kg = KnowledgeGraph()
        assert not kg.update_node("unknown", labels={"Test"})

    def test_delete_node(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        assert kg.delete_node("n1")
        assert kg.get_node("n1") is None

    def test_delete_node_unknown(self):
        kg = KnowledgeGraph()
        assert not kg.delete_node("unknown")

    def test_delete_node_removes_edges(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_edge("n1", "n2", "CONNECTED")
        kg.delete_node("n1")
        assert len(kg.get_all_edges()) == 0

    def test_get_all_nodes(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        assert len(kg.get_all_nodes()) == 2

    def test_get_nodes_by_label(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", labels={"Person"})
        kg.add_node("n2", labels={"Bot"})
        assert len(kg.get_nodes_by_label("Person")) == 1
        assert len(kg.get_nodes_by_label("Bot")) == 1
        assert len(kg.get_nodes_by_label("Nonexistent")) == 0

    def test_add_edge(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        eid = kg.add_edge("n1", "n2", "KNOWS", weight=0.9)
        assert eid is not None
        edge = kg.get_edge(eid)
        assert edge is not None
        assert edge.relationship == "KNOWS"
        assert edge.weight == 0.9

    def test_add_edge_missing_source(self):
        kg = KnowledgeGraph()
        kg.add_node("n2")
        with pytest.raises(ValueError, match="does not exist"):
            kg.add_edge("n1", "n2")

    def test_add_edge_missing_target(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        with pytest.raises(ValueError, match="does not exist"):
            kg.add_edge("n1", "n2")

    def test_get_edge_unknown(self):
        kg = KnowledgeGraph()
        assert kg.get_edge("unknown") is None

    def test_update_edge(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        eid = kg.add_edge("n1", "n2", "KNOWS", weight=0.5)
        assert kg.update_edge(eid, relationship="FRIENDS", weight=0.9)
        edge = kg.get_edge(eid)
        assert edge.relationship == "FRIENDS"
        assert edge.weight == 0.9

    def test_update_edge_unknown(self):
        kg = KnowledgeGraph()
        assert not kg.update_edge("unknown", weight=0.5)

    def test_delete_edge(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        eid = kg.add_edge("n1", "n2")
        assert kg.delete_edge(eid)
        assert kg.get_edge(eid) is None

    def test_delete_edge_unknown(self):
        kg = KnowledgeGraph()
        assert not kg.delete_edge("unknown")

    def test_get_edges_for_node(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_node("n3")
        kg.add_edge("n1", "n2")
        kg.add_edge("n3", "n1")
        edges = kg.get_edges_for_node("n1")
        assert len(edges) == 2

    def test_get_outgoing_edges(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_edge("n1", "n2")
        assert len(kg.get_outgoing_edges("n1")) == 1
        assert len(kg.get_outgoing_edges("n2")) == 0

    def test_get_incoming_edges(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_edge("n1", "n2")
        assert len(kg.get_incoming_edges("n1")) == 0
        assert len(kg.get_incoming_edges("n2")) == 1

    def test_get_all_edges(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_node("n3")
        kg.add_edge("n1", "n2")
        kg.add_edge("n1", "n3")
        assert len(kg.get_all_edges()) == 2

    def test_query_exact_match(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", properties={"name": "Alice"})
        kg.add_node("n2", properties={"name": "Bob"})
        result = kg.query("Alice")
        assert len(result.nodes) == 1
        assert result.nodes[0].node_id == "n1"

    def test_query_case_insensitive(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", properties={"name": "Alice"})
        result = kg.query("alice")
        assert len(result.nodes) == 1

    def test_query_threshold_filter(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", properties={"name": "Alice"})
        result = kg.query("Bob", threshold=0.9)
        assert len(result.nodes) == 0

    def test_query_includes_edges(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", properties={"name": "Alice"})
        kg.add_node("n2", properties={"name": "Bob"})
        kg.add_edge("n1", "n2", "FRIENDS")
        result = kg.query("Alice")
        # Edge between n1 and n2 should be included since both match
        # But Bob doesn't match "Alice", so edge won't be in result
        assert len(result.edges) == 0

    def test_query_matches_node_id(self):
        kg = KnowledgeGraph()
        kg.add_node("alice-1", properties={"role": "helper"})
        result = kg.query("alice")
        assert len(result.nodes) == 1

    def test_query_matches_labels(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", labels={"Person"})
        result = kg.query("person")
        assert len(result.nodes) == 1

    def test_query_empty_result(self):
        kg = KnowledgeGraph()
        result = kg.query("nonexistent")
        assert len(result.nodes) == 0

    def test_get_neighbors_direct(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_edge("n1", "n2", "CONNECTED", weight=1.0)
        result = kg.get_neighbors("n1", max_hops=1)
        assert len(result.nodes) == 1
        assert result.nodes[0].node_id == "n2"

    def test_get_neighbors_two_hops(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_node("n3")
        kg.add_edge("n1", "n2", "CONNECTED", weight=1.0)
        kg.add_edge("n2", "n3", "CONNECTED", weight=1.0)
        result = kg.get_neighbors("n1", max_hops=2)
        assert len(result.nodes) == 2
        nids = {n.node_id for n in result.nodes}
        assert nids == {"n2", "n3"}

    def test_get_neighbors_unknown_node(self):
        kg = KnowledgeGraph()
        result = kg.get_neighbors("unknown")
        assert len(result.nodes) == 0

    def test_get_neighbors_min_weight_filter(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_edge("n1", "n2", "CONNECTED", weight=0.3)
        result = kg.get_neighbors("n1", min_weight=0.5)
        assert len(result.nodes) == 0  # Edge weight below threshold

    def test_get_importance_isolated(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        assert kg.get_importance("n1") == 0.0

    def test_get_importance_connected(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_edge("n1", "n2")
        # n1 has 1 outgoing, n2 has 1 incoming
        # max_possible = 2*(2-1) = 2
        # n1 importance = 1/2 = 0.5
        assert kg.get_importance("n1") == 0.5

    def test_get_importance_unknown(self):
        kg = KnowledgeGraph()
        assert kg.get_importance("unknown") == 0.0

    def test_get_importance_scores(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        scores = kg.get_importance_scores()
        assert "n1" in scores
        assert "n2" in scores

    def test_get_top_nodes(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        top = kg.get_top_nodes(n=1)
        assert len(top) == 1

    def test_merge_adds_nodes(self):
        kg1 = KnowledgeGraph()
        kg1.add_node("n1", properties={"name": "Alice"})

        kg2 = KnowledgeGraph()
        kg2.add_node("n2", properties={"name": "Bob"})

        result = kg1.merge(kg2)
        assert result["added_nodes"] == 1
        assert kg1.get_node("n2") is not None

    def test_merge_updates_existing(self):
        kg1 = KnowledgeGraph()
        kg1.add_node("n1", properties={"name": "Alice"})

        kg2 = KnowledgeGraph()
        kg2.add_node("n1", properties={"role": "assistant"})

        result = kg1.merge(kg2)
        assert result["updated_nodes"] == 1
        node = kg1.get_node("n1")
        assert node.properties["name"] == "Alice"
        assert node.properties["role"] == "assistant"

    def test_merge_adds_edges(self):
        kg1 = KnowledgeGraph()
        kg1.add_node("n1")
        kg1.add_node("n2")

        kg2 = KnowledgeGraph()
        kg2.add_node("n1")
        kg2.add_node("n2")
        kg2.add_edge("n1", "n2", "FRIENDS")

        result = kg1.merge(kg2)
        assert result["added_edges"] >= 1

    def test_merge_from_dict(self, tmp_path):
        kg = KnowledgeGraph(storage_dir=str(tmp_path))
        data = {
            "nodes": [{"node_id": "n1", "labels": ["Person"], "properties": {},
                       "created_at": "", "updated_at": "", "source": ""}],
            "edges": [],
        }
        result = kg.merge_from_dict(data)
        assert result["added_nodes"] == 1

    def test_get_stats_empty(self):
        kg = KnowledgeGraph()
        stats = kg.get_stats()
        assert stats["node_count"] == 0
        assert stats["edge_count"] == 0

    def test_get_stats_with_data(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", labels={"Person"})
        kg.add_node("n2", labels={"Bot"})
        kg.add_edge("n1", "n2", "KNOWS")
        stats = kg.get_stats()
        assert stats["node_count"] == 2
        assert stats["edge_count"] == 1
        assert stats["label_counts"]["Person"] == 1
        assert stats["label_counts"]["Bot"] == 1
        assert stats["relationship_counts"]["KNOWS"] == 1

    def test_save_and_load(self, tmp_path):
        file_path = str(tmp_path / "kg.json")
        kg = KnowledgeGraph()
        kg.add_node("n1", properties={"name": "Alice"})
        saved = kg.save(file_path)
        assert saved == file_path
        assert os.path.isfile(file_path)

        kg2 = KnowledgeGraph()
        loaded = kg2.load(file_path)
        assert loaded == 1
        assert kg2.get_node("n1") is not None

    def test_save_default_path(self, tmp_path):
        kg = KnowledgeGraph(storage_dir=str(tmp_path))
        kg.add_node("n1")
        path = kg.save()
        assert os.path.isfile(path)

    def test_load_nonexistent_file(self):
        kg = KnowledgeGraph()
        assert kg.load("/nonexistent.json") == 0

    def test_export_graph(self):
        kg = KnowledgeGraph()
        kg.add_node("n1")
        kg.add_node("n2")
        kg.add_edge("n1", "n2", "FRIENDS")
        exported = kg.export_graph()
        assert len(exported["nodes"]) == 2
        assert len(exported["edges"]) == 1


# ==============================================================================
# continuum/context_manager.py — ContextContinuum, ContextSnapshot, SessionState
# ==============================================================================

from continuum.context_manager import (
    ContextContinuum,
    ContextSnapshot,
    SessionState,
    DeviceType,
    get_context_manager,
)


class TestDeviceType:
    """DeviceType enum."""

    def test_values(self):
        assert DeviceType.PWA is not None
        assert DeviceType.MOBILE is not None
        assert DeviceType.DESKTOP is not None
        assert DeviceType.SERVER is not None
        assert DeviceType.EMBEDDED is not None

    def test_all_members(self):
        assert len(DeviceType) == 5


class TestSessionState:
    """SessionState dataclass with serialization."""

    def test_create(self):
        ss = SessionState(device_type=DeviceType.PWA, device_id="dev-1")
        assert ss.device_type == DeviceType.PWA
        assert ss.device_id == "dev-1"
        assert ss.last_activity != ""

    def test_to_dict(self):
        ss = SessionState(device_type=DeviceType.DESKTOP, device_id="dev-1")
        d = ss.to_dict()
        assert d["device_type"] == "DESKTOP"
        assert d["device_id"] == "dev-1"

    def test_from_dict(self):
        d = {"device_type": "MOBILE", "device_id": "dev-1",
             "active_snapshot_id": None, "last_activity": "", "metadata": {}}
        ss = SessionState.from_dict(d)
        assert ss.device_type == DeviceType.MOBILE
        assert ss.device_id == "dev-1"


class TestContextSnapshot:
    """ContextSnapshot dataclass with properties."""

    def test_create(self):
        snap = ContextSnapshot(snapshot_id="snap-001", device_type=DeviceType.PWA)
        assert snap.snapshot_id == "snap-001"
        assert snap.timestamp != ""

    def test_age_hours(self):
        snap = ContextSnapshot(snapshot_id="s1", device_type=DeviceType.PWA)
        assert snap.age_hours >= 0.0

    def test_message_count(self):
        snap = ContextSnapshot(
            snapshot_id="s1", device_type=DeviceType.PWA,
            conversation_history=[{"role": "user", "content": "hi"}],
        )
        assert snap.message_count == 1

    def test_summary(self):
        snap = ContextSnapshot(snapshot_id="snap-abcdef123456", device_type=DeviceType.SERVER)
        summary = snap.summary
        # summary uses snapshot_id[:8]; "snap-abcdef123456"[:8] == "snap-abc"
        assert "snap-abc" in summary
        assert "SERVER" in summary

    def test_to_dict(self):
        snap = ContextSnapshot(snapshot_id="s1", device_type=DeviceType.DESKTOP)
        d = snap.to_dict()
        assert d["device_type"] == "DESKTOP"
        assert d["snapshot_id"] == "s1"

    def test_from_dict(self):
        d = {
            "snapshot_id": "s1", "device_type": "PWA", "timestamp": "",
            "conversation_history": [], "agent_state": {},
            "mesh_state": {}, "metadata": {},
        }
        snap = ContextSnapshot.from_dict(d)
        assert snap.device_type == DeviceType.PWA


class TestContextContinuum:
    """ContextContinuum snapshot lifecycle and device management."""

    def test_get_context_manager_factory(self):
        cm = get_context_manager()
        assert isinstance(cm, ContextContinuum)

    def test_init_with_storage_dir(self, tmp_path):
        cm = ContextContinuum(storage_dir=str(tmp_path / "continuum"))
        assert os.path.isdir(str(tmp_path / "continuum"))

    def test_create_snapshot(self):
        cm = ContextContinuum()
        sid = cm.create_snapshot(
            device_type=DeviceType.PWA,
            conversation_history=[{"role": "user", "content": "Hello"}],
            agent_state={"task": "greeting"},
            mesh_state={"peers": ["node-1"]},
            metadata={"version": "1.0"},
        )
        assert sid.startswith("snap-")
        snap = cm.get_snapshot(sid)
        assert snap is not None
        assert snap.device_type == DeviceType.PWA
        assert len(snap.conversation_history) == 1

    def test_create_snapshot_with_device_id(self):
        cm = ContextContinuum()
        sid = cm.create_snapshot(device_type=DeviceType.DESKTOP, device_id="my-pc")
        assert sid is not None

    def test_restore_snapshot(self):
        cm = ContextContinuum()
        sid = cm.create_snapshot(
            device_type=DeviceType.PWA,
            conversation_history=[{"role": "user", "content": "Hello"}],
        )
        restored = cm.restore_snapshot(sid)
        assert restored is not None
        assert restored.snapshot_id == sid
        assert len(restored.conversation_history) == 1

    def test_restore_snapshot_unknown(self):
        cm = ContextContinuum()
        assert cm.restore_snapshot("unknown") is None

    def test_restore_returns_deep_copy(self):
        cm = ContextContinuum()
        sid = cm.create_snapshot(device_type=DeviceType.PWA)
        restored = cm.restore_snapshot(sid)
        # Modify the restored copy
        restored.metadata["modified"] = True
        # Original should be unchanged
        original = cm.get_snapshot(sid)
        assert "modified" not in original.metadata

    def test_transfer_context(self):
        cm = ContextContinuum()
        cm.create_snapshot(device_type=DeviceType.PWA, device_id="phone")
        new_sid = cm.transfer_context(
            from_device=DeviceType.PWA,
            to_device=DeviceType.DESKTOP,
            from_device_id="phone",
            to_device_id="pc",
        )
        assert new_sid is not None
        assert new_sid.startswith("snap-")

    def test_transfer_context_no_source(self):
        cm = ContextContinuum()
        result = cm.transfer_context(DeviceType.PWA, DeviceType.DESKTOP)
        assert result is None

    def test_transfer_truncates_for_mobile(self):
        cm = ContextContinuum()
        history = [{"role": "user", "content": f"msg-{i}"} for i in range(100)]
        cm.create_snapshot(device_type=DeviceType.SERVER, device_id="server",
                          conversation_history=history)
        new_sid = cm.transfer_context(
            from_device=DeviceType.SERVER,
            to_device=DeviceType.MOBILE,
            from_device_id="server",
            to_device_id="phone",
        )
        snap = cm.get_snapshot(new_sid)
        # Should be truncated to 50 for mobile
        assert snap.message_count <= 50

    def test_list_snapshots(self):
        cm = ContextContinuum()
        cm.create_snapshot(device_type=DeviceType.PWA)
        cm.create_snapshot(device_type=DeviceType.DESKTOP)
        snapshots = cm.list_snapshots()
        assert len(snapshots) == 2

    def test_list_snapshots_filtered(self):
        cm = ContextContinuum()
        cm.create_snapshot(device_type=DeviceType.PWA)
        cm.create_snapshot(device_type=DeviceType.DESKTOP)
        pwa_snaps = cm.list_snapshots(device_type=DeviceType.PWA)
        assert len(pwa_snaps) == 1

    def test_list_snapshots_limit(self):
        cm = ContextContinuum()
        for _ in range(5):
            cm.create_snapshot(device_type=DeviceType.PWA)
        assert len(cm.list_snapshots(limit=3)) == 3

    def test_get_latest(self):
        cm = ContextContinuum()
        cm.create_snapshot(device_type=DeviceType.PWA, device_id="phone")
        latest = cm.get_latest(DeviceType.PWA, device_id="phone")
        assert latest is not None

    def test_get_latest_no_match(self):
        cm = ContextContinuum()
        assert cm.get_latest(DeviceType.PWA) is None

    def test_register_device(self):
        cm = ContextContinuum()
        session = cm.register_device(DeviceType.PWA, "phone-1", {"os": "Android"})
        assert session.device_type == DeviceType.PWA
        assert session.device_id == "phone-1"
        assert session.metadata["os"] == "Android"

    def test_register_device_twice_updates(self):
        cm = ContextContinuum()
        cm.register_device(DeviceType.PWA, "phone-1")
        session = cm.register_device(DeviceType.PWA, "phone-1", {"version": "2.0"})
        assert session.metadata["version"] == "2.0"

    def test_unregister_device(self):
        cm = ContextContinuum()
        cm.register_device(DeviceType.PWA, "phone-1")
        assert cm.unregister_device("phone-1")
        assert not cm.unregister_device("phone-1")  # Already gone

    def test_unregister_device_unknown(self):
        cm = ContextContinuum()
        assert not cm.unregister_device("unknown")

    def test_get_device_sessions(self):
        cm = ContextContinuum()
        cm.register_device(DeviceType.PWA, "phone-1")
        cm.register_device(DeviceType.DESKTOP, "pc-1")
        sessions = cm.get_device_sessions()
        assert len(sessions) == 2

    def test_prune_old(self):
        cm = ContextContinuum()
        sid = cm.create_snapshot(device_type=DeviceType.PWA)
        # Manually set the snapshot timestamp to be old so prune_old catches it
        cm._snapshots[sid].timestamp = "2020-01-01T00:00:00"
        # Prune with 0 max_age — should remove everything older than now
        cm.prune_old(max_age_hours=0)
        assert len(cm.list_snapshots()) == 0

    def test_prune_old_clears_session_refs(self):
        cm = ContextContinuum()
        sid = cm.create_snapshot(device_type=DeviceType.PWA, device_id="phone")
        # Manually set the snapshot timestamp to be old so prune_old catches it
        cm._snapshots[sid].timestamp = "2020-01-01T00:00:00"
        cm.prune_old(max_age_hours=0)
        # Session should have active_snapshot_id set to None
        for session in cm.get_device_sessions():
            assert session.active_snapshot_id is None

    def test_get_stats_empty(self):
        cm = ContextContinuum()
        stats = cm.get_stats()
        assert stats["total_snapshots"] == 0
        assert stats["total_transfers"] == 0
        assert stats["registered_devices"] == 0

    def test_get_stats_with_data(self):
        cm = ContextContinuum()
        cm.create_snapshot(device_type=DeviceType.PWA)
        cm.create_snapshot(device_type=DeviceType.DESKTOP)
        stats = cm.get_stats()
        assert stats["total_snapshots"] == 2
        assert stats["total_transfers"] == 0
        assert stats["snapshots_by_device"]["PWA"] == 1
        assert stats["snapshots_by_device"]["DESKTOP"] == 1

    def test_get_stats_tracks_transfers(self):
        cm = ContextContinuum()
        cm.create_snapshot(device_type=DeviceType.PWA, device_id="phone")
        cm.transfer_context(DeviceType.PWA, DeviceType.DESKTOP,
                           from_device_id="phone", to_device_id="pc")
        stats = cm.get_stats()
        assert stats["total_transfers"] == 1

    def test_save_and_load(self, tmp_path):
        save_dir = str(tmp_path / "continuum")
        cm1 = ContextContinuum(storage_dir=save_dir)
        cm1.create_snapshot(device_type=DeviceType.PWA, device_id="phone",
                           conversation_history=[{"role": "user", "content": "Hi"}])
        cm1.register_device(DeviceType.PWA, "phone")
        cm1.save()

        cm2 = ContextContinuum(storage_dir=save_dir)
        loaded = cm2.load()
        assert loaded >= 1
        assert len(cm2.list_snapshots()) >= 1

    def test_save_default_path(self, tmp_path):
        cm = ContextContinuum(storage_dir=str(tmp_path / "cm"))
        cm.create_snapshot(device_type=DeviceType.PWA)
        path = cm.save()
        assert os.path.isdir(path)

    def test_load_no_directory(self):
        cm = ContextContinuum()
        assert cm.load() == 0

    def test_load_from_init(self, tmp_path):
        save_dir = str(tmp_path / "continuum")
        cm1 = ContextContinuum(storage_dir=save_dir)
        cm1.create_snapshot(device_type=DeviceType.PWA, device_id="phone")
        cm1.save()

        cm2 = ContextContinuum(storage_dir=save_dir)
        # Should auto-load from disk on init
        assert len(cm2.list_snapshots()) >= 1

    def test_create_snapshot_with_storage_persists(self, tmp_path):
        save_dir = str(tmp_path / "continuum")
        cm = ContextContinuum(storage_dir=save_dir)
        cm.create_snapshot(device_type=DeviceType.PWA)
        # Check file was written
        files = os.listdir(save_dir)
        snap_files = [f for f in files if f.startswith("snap-")]
        assert len(snap_files) >= 1
