#!/usr/bin/env python3
"""Code Analyzer — Static analysis and improvement identification.

Scans source files for patterns, anti-patterns, style violations, dead code,
performance bottlenecks, and security concerns. Produces actionable
analysis reports that can be fed to the PatchGenerator.

Typical usage::

    analyzer = CodeAnalyzer()
    report = analyzer.analyze_file("mesh/p2p_transport.py")
    for issue in report.issues:
        print(f"[{issue.severity}] {issue.message} at {issue.location}")
"""

from __future__ import annotations

import ast
import logging
import os
import re
import time
import tokenize
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Severity levels for code analysis issues."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class IssueCategory(Enum):
    """Categories of code issues."""
    STYLE = auto()
    PERFORMANCE = auto()
    SECURITY = auto()
    DEAD_CODE = auto()
    COMPLEXITY = auto()
    ANTI_PATTERN = auto()
    BEST_PRACTICE = auto()
    TYPE_SAFETY = auto()
    IMPORT = auto()
    DOCUMENTATION = auto()


@dataclass
class CodeIssue:
    """A single issue found during code analysis."""
    file: str
    line: int
    column: int
    severity: IssueSeverity
    category: IssueCategory
    message: str
    suggestion: Optional[str] = None
    symbol: Optional[str] = None


@dataclass
class AnalysisMetrics:
    """Aggregated metrics for an analyzed file."""
    loc: int = 0  # Lines of code (excluding blanks/comments)
    total_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    max_complexity: int = 0
    avg_complexity: float = 0.0
    import_count: int = 0
    todo_count: int = 0
    fixme_count: int = 0
    issue_count: int = 0


@dataclass
class AnalysisReport:
    """Complete analysis result for one or more files."""
    target: str  # File or directory analyzed
    issues: List[CodeIssue] = field(default_factory=list)
    metrics: AnalysisMetrics = field(default_factory=AnalysisMetrics)
    analyzed_at: float = 0.0
    elapsed_seconds: float = 0.0

    def has_critical(self) -> bool:
        return any(i.severity == IssueSeverity.CRITICAL for i in self.issues)

    def has_errors(self) -> bool:
        return any(i.severity == IssueSeverity.ERROR for i in self.issues)

    def by_severity(self, severity: IssueSeverity) -> List[CodeIssue]:
        return [i for i in self.issues if i.severity == severity]

    def by_category(self, category: IssueCategory) -> List[CodeIssue]:
        return [i for i in self.issues if i.category == category]


# ── Security-sensitive patterns ────────────────────────────────────────────
_SENSITIVE_PATTERNS: List[Tuple[str, str, IssueSeverity]] = [
    (r"(?i)(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded credential", IssueSeverity.CRITICAL),
    (r"eval\s*\(", "Use of eval()", IssueSeverity.ERROR),
    (r"exec\s*\(", "Use of exec()", IssueSeverity.ERROR),
    (r"pickle\.loads?\s*\(", "Unsafe deserialization (pickle)", IssueSeverity.ERROR),
    (r"subprocess\.(call|Popen|run)\s*\(.*shell=True", "Shell injection risk", IssueSeverity.CRITICAL),
    (r"os\.system\s*\(", "Use of os.system()", IssueSeverity.ERROR),
    (r"__import__\s*\(", "Dynamic import", IssueSeverity.WARNING),
    (r"marshal\.loads?\s*\(", "Unsafe deserialization (marshal)", IssueSeverity.ERROR),
    (r"sqlite3\.(execute|executemany)\s*\(.*f['\"]", "SQL injection via f-string", IssueSeverity.CRITICAL),
    (r"jinja2\.Template\s*\(", "Potential SSTI (untrusted template)", IssueSeverity.WARNING),
]


class CodeAnalyzer:
    """Scans code for issues and produces analysis reports.

    The analyzer performs:
    - AST-based analysis (cyclomatic complexity, unused imports, etc.)
    - Regex-based pattern matching (security issues, TODOs)
    - Style heuristics (line length, naming conventions)
    - Performance hints (large functions, nested loops)
    """

    def __init__(self, max_line_length: int = 120):
        self.max_line_length = max_line_length
        self._visited: Set[str] = set()

    # ── Public API ──────────────────────────────────────────────────────────

    def analyze_file(self, filepath: str) -> AnalysisReport:
        """Analyze a single Python file and return a report."""
        start = time.monotonic()
        report = AnalysisReport(target=filepath, analyzed_at=time.time())
        path = Path(filepath)

        if not path.exists():
            report.issues.append(CodeIssue(
                file=filepath, line=0, column=0,
                severity=IssueSeverity.ERROR, category=IssueCategory.IMPORT,
                message=f"File not found: {filepath}",
            ))
            return report

        if path.suffix not in (".py",):
            report.issues.append(CodeIssue(
                file=filepath, line=0, column=0,
                severity=IssueSeverity.WARNING, category=IssueCategory.IMPORT,
                message=f"Unsupported file type: {path.suffix}. Only .py files are analyzed.",
            ))
            return report

        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            report.issues.append(CodeIssue(
                file=filepath, line=0, column=0,
                severity=IssueSeverity.ERROR, category=IssueCategory.IMPORT,
                message=f"Cannot read file: {exc}",
            ))
            return report

        # Compute basic metrics
        lines = source.split("\n")
        metrics = self._compute_metrics(source, lines)

        # AST analysis
        try:
            tree = ast.parse(source, filename=filepath)
            self._analyze_ast(tree, filepath, report)
            metrics = self._compute_ast_metrics(tree, metrics)
        except SyntaxError as exc:
            report.issues.append(CodeIssue(
                file=filepath, line=exc.lineno or 0, column=exc.offset or 0,
                severity=IssueSeverity.ERROR, category=IssueCategory.IMPORT,
                message=f"Syntax error: {exc.msg}",
            ))

        # Regex-based pattern analysis
        self._analyze_patterns(source, filepath, report)

        # Line-level checks
        self._check_line_issues(lines, filepath, report)

        report.metrics = metrics
        report.elapsed_seconds = time.monotonic() - start
        return report

    def analyze_directory(self, directory: str, pattern: str = "**/*.py") -> AnalysisReport:
        """Analyze all Python files in a directory."""
        start = time.monotonic()
        report = AnalysisReport(target=directory, analyzed_at=time.time())
        path = Path(directory)

        if not path.is_dir():
            report.issues.append(CodeIssue(
                file=directory, line=0, column=0,
                severity=IssueSeverity.ERROR, category=IssueCategory.IMPORT,
                message=f"Directory not found: {directory}",
            ))
            return report

        files_analyzed = 0
        for py_file in sorted(path.glob(pattern)):
            if py_file.is_file():
                file_report = self.analyze_file(str(py_file))
                report.issues.extend(file_report.issues)
                # Merge metrics
                m = report.metrics
                fm = file_report.metrics
                m.loc += fm.loc
                m.total_lines += fm.total_lines
                m.comment_lines += fm.comment_lines
                m.blank_lines += fm.blank_lines
                m.function_count += fm.function_count
                m.class_count += fm.class_count
                m.max_complexity = max(m.max_complexity, fm.max_complexity)
                m.import_count += fm.import_count
                m.todo_count += fm.todo_count
                m.fixme_count += fm.fixme_count
                m.issue_count += fm.issue_count
                files_analyzed += 1

        if files_analyzed > 0:
            report.metrics.avg_complexity = (
                report.metrics.max_complexity / files_analyzed
            )

        report.elapsed_seconds = time.monotonic() - start
        return report

    def get_summary(self, report: AnalysisReport) -> Dict:
        """Return a human-readable summary dict of an analysis report."""
        return {
            "target": report.target,
            "files_analyzed": 1,
            "total_issues": len(report.issues),
            "critical": len(report.by_severity(IssueSeverity.CRITICAL)),
            "errors": len(report.by_severity(IssueSeverity.ERROR)),
            "warnings": len(report.by_severity(IssueSeverity.WARNING)),
            "info": len(report.by_severity(IssueSeverity.INFO)),
            "categories": {
                cat.name: len(report.by_category(cat))
                for cat in IssueCategory
            },
            "loc": report.metrics.loc,
            "functions": report.metrics.function_count,
            "classes": report.metrics.class_count,
            "max_complexity": report.metrics.max_complexity,
            "todos": report.metrics.todo_count,
            "fixmes": report.metrics.fixme_count,
            "elapsed_seconds": round(report.elapsed_seconds, 3),
        }

    # ── Internal analysis methods ──────────────────────────────────────────

    def _compute_metrics(self, source: str, lines: List[str]) -> AnalysisMetrics:
        """Compute basic line-based metrics."""
        metrics = AnalysisMetrics(total_lines=len(lines))

        in_multiline_comment = False
        for line in lines:
            stripped = line.strip()

            if not stripped:
                metrics.blank_lines += 1
                continue

            if stripped.startswith("#"):
                metrics.comment_lines += 1
                continue

            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_multiline_comment = not in_multiline_comment
                metrics.comment_lines += 1
                continue

            if in_multiline_comment:
                metrics.comment_lines += 1
                if stripped.endswith('"""') or stripped.endswith("'''"):
                    in_multiline_comment = False
                continue

            metrics.loc += 1

            # Count TODOs and FIXMEs
            if "TODO" in stripped or "todo" in stripped.lower():
                metrics.todo_count += 1
            if "FIXME" in stripped or "fixme" in stripped.lower():
                metrics.fixme_count += 1

        return metrics

    def _compute_ast_metrics(self, tree: ast.AST, metrics: AnalysisMetrics) -> AnalysisMetrics:
        """Augment metrics with AST data."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics.function_count += 1
                complexity = self._compute_cyclomatic_complexity(node)
                metrics.max_complexity = max(metrics.max_complexity, complexity)
            elif isinstance(node, ast.ClassDef):
                metrics.class_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics.import_count += 1
        return metrics

    def _compute_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Compute McCabe cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.Assert, ast.Raise)):
                complexity += 1
        return complexity

    def _analyze_ast(self, tree: ast.AST, filepath: str, report: AnalysisReport):
        """AST-based analysis passes."""
        self._check_unused_imports(tree, filepath, report)
        self._check_function_complexity(tree, filepath, report)
        self._check_bare_excepts(tree, filepath, report)
        self._check_mutable_defaults(tree, filepath, report)
        self._check_global_statement(tree, filepath, report)

    def _check_unused_imports(self, tree: ast.AST, filepath: str, report: AnalysisReport):
        """Detect imports that are never used in the file."""
        imports: Dict[str, Tuple[str, int]] = {}
        used_names: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = (alias.name, node.lineno or 0)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports[name] = (f"{node.module}.{alias.name}", node.lineno or 0)

        # Collect all name references
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)

        for name, (full_name, line) in imports.items():
            if name not in used_names:
                report.issues.append(CodeIssue(
                    file=filepath, line=line, column=0,
                    severity=IssueSeverity.WARNING, category=IssueCategory.IMPORT,
                    message=f"Unused import: {full_name}",
                    suggestion=f"Remove 'import {full_name}'",
                    symbol=full_name,
                ))

    def _check_function_complexity(self, tree: ast.AST, filepath: str, report: AnalysisReport,
                                   max_complexity: int = 15):
        """Flag functions with excessive cyclomatic complexity."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._compute_cyclomatic_complexity(node)
                if complexity > max_complexity:
                    report.issues.append(CodeIssue(
                        file=filepath, line=node.lineno or 0, column=0,
                        severity=IssueSeverity.WARNING, category=IssueCategory.COMPLEXITY,
                        message=(f"Function '{node.name}' has cyclomatic complexity "
                                 f"{complexity} (max recommended: {max_complexity})"),
                        suggestion="Consider splitting into smaller functions",
                        symbol=node.name,
                    ))

    def _check_bare_excepts(self, tree: ast.AST, filepath: str, report: AnalysisReport):
        """Flag bare 'except:' clauses."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                report.issues.append(CodeIssue(
                    file=filepath, line=node.lineno or 0, column=0,
                    severity=IssueSeverity.WARNING, category=IssueCategory.BEST_PRACTICE,
                    message="Bare 'except:' clause",
                    suggestion="Use 'except Exception:' instead",
                ))

    def _check_mutable_defaults(self, tree: ast.AST, filepath: str, report: AnalysisReport):
        """Flag mutable default arguments."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        report.issues.append(CodeIssue(
                            file=filepath, line=node.lineno or 0, column=0,
                            severity=IssueSeverity.WARNING, category=IssueCategory.BEST_PRACTICE,
                            message=f"Mutable default argument in '{node.name}'",
                            suggestion="Use 'None' as default and create inside function",
                            symbol=node.name,
                        ))

    def _check_global_statement(self, tree: ast.AST, filepath: str, report: AnalysisReport):
        """Flag 'global' statements as style concern."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                report.issues.append(CodeIssue(
                    file=filepath, line=node.lineno or 0, column=0,
                    severity=IssueSeverity.INFO, category=IssueCategory.STYLE,
                    message=f"Use of 'global' for: {', '.join(node.names)}",
                    suggestion="Consider using class attributes or return values",
                ))

    def _analyze_patterns(self, source: str, filepath: str, report: AnalysisReport):
        """Regex-based pattern matching for security and anti-patterns."""
        for pattern, description, severity in _SENSITIVE_PATTERNS:
            for match in re.finditer(pattern, source):
                line_num = source[:match.start()].count("\n") + 1
                report.issues.append(CodeIssue(
                    file=filepath, line=line_num, column=match.start(),
                    severity=severity, category=IssueCategory.SECURITY,
                    message=description,
                    suggestion=f"Avoid using {description.lower()}; use environment variables or vault",
                ))

    def _check_line_issues(self, lines: List[str], filepath: str, report: AnalysisReport):
        """Per-line checks (line length, trailing whitespace, etc.)."""
        for i, line in enumerate(lines, start=1):
            if len(line) > self.max_line_length:
                report.issues.append(CodeIssue(
                    file=filepath, line=i, column=self.max_line_length,
                    severity=IssueSeverity.INFO, category=IssueCategory.STYLE,
                    message=f"Line too long ({len(line)} > {self.max_line_length} chars)",
                    suggestion="Break into multiple lines",
                ))

            if line.endswith(" \n") or line.endswith("\t\n"):
                report.issues.append(CodeIssue(
                    file=filepath, line=i, column=len(line.rstrip()),
                    severity=IssueSeverity.INFO, category=IssueCategory.STYLE,
                    message="Trailing whitespace detected",
                ))

            if line.strip().startswith("print("):
                report.issues.append(CodeIssue(
                    file=filepath, line=i, column=0,
                    severity=IssueSeverity.INFO, category=IssueCategory.BEST_PRACTICE,
                    message="Leftover print() statement",
                    suggestion="Replace with logger.debug()",
                ))


def get_code_analyzer(max_line_length: int = 120) -> CodeAnalyzer:
    """Factory function to get a CodeAnalyzer instance."""
    return CodeAnalyzer(max_line_length=max_line_length)
