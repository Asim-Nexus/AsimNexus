#!/usr/bin/env python3
"""Test Runner — Automated test execution and regression detection.

Orchestrates test execution across the AsimNexus codebase, captures
results, detects regressions, and provides pass/fail summaries.
Integrates with the PatchGenerator to validate patches before and
after application.

Supports:
- Running specific test files or directories
- pytest integration with warning-as-errors flags
- Historical result tracking for regression detection
- Parallel test execution (via pytest-xdist if available)
- Timeout control per test suite

Typical usage::

    runner = TestRunner()
    result = runner.run_tests("tests/real/test_launch_spine.py")
    print(f"Passed: {result.passed}/{result.total}")
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TestOutcome(Enum):
    """Possible outcomes for a single test."""
    PASSED = auto()
    FAILED = auto()
    ERROR = auto()
    SKIPPED = auto()
    XFAIL = auto()
    XPASS = auto()


@dataclass
class TestResult:
    """Result of a single test case."""
    node_id: str
    outcome: TestOutcome
    duration_ms: float = 0.0
    message: str = ""
    file: str = ""
    line: int = 0


@dataclass
class TestSuiteResult:
    """Aggregated results from running a test suite."""
    target: str
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    total: int = 0
    duration_seconds: float = 0.0
    tests: List[TestResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    exit_code: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    @property
    def has_regressions(self) -> bool:
        return len([t for t in self.tests if t.outcome in (
            TestOutcome.FAILED, TestOutcome.ERROR
        )]) > 0

    def summary(self) -> Dict:
        """Return a compact summary dict."""
        return {
            "target": self.target,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "total": self.total,
            "duration_seconds": round(self.duration_seconds, 2),
            "success": self.success,
            "warnings_count": len(self.warnings),
        }


@dataclass
class RegressionRecord:
    """Tracks a regression between two test runs."""
    test_id: str
    previous_outcome: TestOutcome
    current_outcome: TestOutcome
    previous_run: str
    current_run: str


class TestRunner:
    """Orchestrates test execution with regression tracking.

    The runner wraps pytest, captures structured results, and maintains
    a history of test runs for regression detection.
    """

    def __init__(self, history_dir: Optional[str] = None):
        self.history_dir = history_dir or os.path.join(
            os.path.dirname(__file__), "..", "test-results", "evolution"
        )
        os.makedirs(self.history_dir, exist_ok=True)
        self._history: Dict[str, TestSuiteResult] = {}

    # ── Public API ──────────────────────────────────────────────────────────

    def run_tests(
        self,
        target: str,
        extra_args: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        warning_as_errors: bool = True,
        xdist: bool = False,
    ) -> TestSuiteResult:
        """Run pytest on a target and return structured results.

        Args:
            target: Test file or directory path.
            extra_args: Additional pytest arguments.
            timeout: Maximum runtime in seconds (0 = no limit).
            warning_as_errors: Convert warnings to errors with -W flags.
            xdist: Enable parallel execution via pytest-xdist.

        Returns:
            A TestSuiteResult with full details.
        """
        start = time.monotonic()

        cmd = [sys.executable, "-m", "pytest", target, "-v"]
        if extra_args:
            cmd.extend(extra_args)
        if warning_as_errors:
            cmd.extend([
                "-W", "error::RuntimeWarning",
                "-W", "error::DeprecationWarning",
            ])
        if xdist:
            cmd.extend(["-n", "auto"])

        logger.info("Running: %s", " ".join(cmd))

        result = TestSuiteResult(target=target)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or 300,
                cwd=self._get_project_root(),
            )
            result.exit_code = proc.returncode
            self._parse_pytest_output(proc.stdout + proc.stderr, result)

        except subprocess.TimeoutExpired:
            result.exit_code = -1
            result.errors = 1
            result.warnings.append("Test execution timed out")
            logger.error("Test execution timed out for: %s", target)

        except FileNotFoundError:
            result.exit_code = -2
            result.errors = 1
            result.warnings.append(f"pytest not found for target: {target}")
            logger.error("pytest not found for: %s", target)

        except Exception as exc:
            result.exit_code = -3
            result.errors = 1
            result.warnings.append(f"Unexpected error: {exc}")
            logger.exception("Unexpected error running tests: %s", exc)

        result.duration_seconds = time.monotonic() - start

        # Store in history
        self._history[target] = result
        self._save_history(target, result)

        return result

    def run_with_patch_validation(
        self,
        target: str,
        patch_id: str,
        patch_generator: Any = None,
    ) -> Dict:
        """Run tests before and after applying a patch to check for regressions.

        Args:
            target: Test target to run.
            patch_id: ID of the patch to validate.
            patch_generator: PatchGenerator instance (or any object with
                get_patch, apply_patch, rollback_patch methods).

        Returns:
            Dict with 'pre', 'post', and 'regressions' keys.
        """
        result: Dict = {}

        # Pre-patch run
        logger.info("Pre-patch test run for patch %s", patch_id)
        pre_result = self.run_tests(target)
        result["pre"] = pre_result.summary()

        if not pre_result.success:
            logger.warning("Pre-patch tests already failing for %s", patch_id)
            result["pre_failing"] = True
            return result

        # Apply patch
        if patch_generator:
            applied = patch_generator.apply_patch(patch_id)
            result["patch_applied"] = applied

            if applied:
                # Post-patch run
                logger.info("Post-patch test run for patch %s", patch_id)
                post_result = self.run_tests(target)
                result["post"] = post_result.summary()

                # Detect regressions
                regressions = self._detect_regressions(pre_result, post_result)
                result["regressions"] = [
                    asdict(r) for r in regressions
                ]

                # Rollback if regressions found
                if regressions:
                    logger.warning("Regressions detected for patch %s, rolling back", patch_id)
                    patch_generator.rollback_patch(patch_id)
                    result["rolled_back"] = True
            else:
                result["post"] = None
                result["regressions"] = []

        return result

    def get_history(self, target: str) -> Optional[TestSuiteResult]:
        """Get the most recent test result for a target."""
        if target in self._history:
            return self._history[target]

        # Try loading from disk
        return self._load_history(target)

    def compare_runs(self, target_a: str, target_b: str) -> List[RegressionRecord]:
        """Compare two historical runs and return regressions."""
        result_a = self.get_history(target_a)
        result_b = self.get_history(target_b)

        if not result_a or not result_b:
            return []

        return self._detect_regressions(result_a, result_b)

    def clear_history(self, target: Optional[str] = None):
        """Clear test history for a target (or all if None)."""
        if target:
            self._history.pop(target, None)
            history_path = self._history_path(target)
            if os.path.exists(history_path):
                os.remove(history_path)
        else:
            self._history.clear()
            for f in os.listdir(self.history_dir):
                if f.endswith(".json"):
                    os.remove(os.path.join(self.history_dir, f))

    # ── Internal methods ────────────────────────────────────────────────────

    def _parse_pytest_output(self, output: str, result: TestSuiteResult):
        """Parse pytest stdout/stderr into structured TestResult objects."""
        lines = output.split("\n")

        # Track summary line at the end
        for line in lines:
            # Parse test lines like: tests/test_x.py::test_func PASSED
            if "::" in line and ("PASSED" in line or "FAILED" in line or
                                  "ERROR" in line or "SKIPPED" in line):
                self._parse_test_line(line, result)

            # Collect warnings
            if "Warning" in line or "warning" in line:
                result.warnings.append(line.strip())

        # Parse final summary
        for line in lines:
            line_s = line.strip()
            if line_s.startswith("==") and "passed" in line_s and "failed" in line_s:
                self._parse_summary(line_s, result)
                break

        # Fallback: count from parsed tests
        if result.total == 0 and result.tests:
            for t in result.tests:
                result.total += 1
                if t.outcome == TestOutcome.PASSED:
                    result.passed += 1
                elif t.outcome == TestOutcome.FAILED:
                    result.failed += 1
                elif t.outcome == TestOutcome.ERROR:
                    result.errors += 1
                elif t.outcome == TestOutcome.SKIPPED:
                    result.skipped += 1

    def _parse_test_line(self, line: str, result: TestSuiteResult):
        """Parse a single pytest output line."""
        # Format: path::test_name OUTCOME [duration]
        parts = line.split()
        if len(parts) < 2:
            return

        node_id = parts[0]
        outcome_str = parts[1].strip()

        outcome_map = {
            "PASSED": TestOutcome.PASSED,
            "FAILED": TestOutcome.FAILED,
            "ERROR": TestOutcome.ERROR,
            "SKIPPED": TestOutcome.SKIPPED,
            "xfail": TestOutcome.XFAIL,
            "XPASS": TestOutcome.XPASS,
        }

        outcome = outcome_map.get(outcome_str, TestOutcome.PASSED if outcome_str == "PASSED" else TestOutcome.FAILED)

        # Extract file and line from node_id (format: path::test_name)
        file_part = node_id.split("::")[0] if "::" in node_id else node_id

        test_result = TestResult(
            node_id=node_id,
            outcome=outcome,
            file=file_part,
            line=0,
        )
        result.tests.append(test_result)

    def _parse_summary(self, line: str, result: TestSuiteResult):
        """Parse the final pytest summary line."""
        import re

        # Match patterns like "10 passed, 1 failed, 2 skipped in 2.16s"
        passed_m = re.search(r"(\d+)\s+passed", line)
        failed_m = re.search(r"(\d+)\s+failed", line)
        errors_m = re.search(r"(\d+)\s+error", line)
        skipped_m = re.search(r"(\d+)\s+skipped", line)
        duration_m = re.search(r"in\s+([\d.]+)s", line)

        if passed_m:
            result.passed = max(result.passed, int(passed_m.group(1)))
        if failed_m:
            result.failed = max(result.failed, int(failed_m.group(1)))
        if errors_m:
            result.errors = max(result.errors, int(errors_m.group(1)))
        if skipped_m:
            result.skipped = max(result.skipped, int(skipped_m.group(1)))

        # Total = sum
        result.total = result.passed + result.failed + result.errors + result.skipped

        if duration_m:
            result.duration_seconds = max(result.duration_seconds, float(duration_m.group(1)))

    def _detect_regressions(self, previous: TestSuiteResult,
                            current: TestSuiteResult) -> List[RegressionRecord]:
        """Compare two runs and find regressions."""
        regressions: List[RegressionRecord] = []

        prev_map = {t.node_id: t for t in previous.tests}
        curr_map = {t.node_id: t for t in current.tests}

        for node_id, curr_test in curr_map.items():
            prev_test = prev_map.get(node_id)

            if prev_test and prev_test.outcome == TestOutcome.PASSED:
                if curr_test.outcome in (TestOutcome.FAILED, TestOutcome.ERROR):
                    regressions.append(RegressionRecord(
                        test_id=node_id,
                        previous_outcome=prev_test.outcome,
                        current_outcome=curr_test.outcome,
                        previous_run=previous.timestamp,
                        current_run=current.timestamp,
                    ))

        return regressions

    def _history_path(self, target: str) -> str:
        """Get the filesystem path for storing history of a target."""
        safe_name = target.replace("/", "_").replace("\\", "_").replace(".", "_")
        return os.path.join(self.history_dir, f"{safe_name}.json")

    def _save_history(self, target: str, result: TestSuiteResult):
        """Persist a test result to disk."""
        path = self._history_path(target)
        try:
            data = {
                "target": result.target,
                "passed": result.passed,
                "failed": result.failed,
                "errors": result.errors,
                "skipped": result.skipped,
                "total": result.total,
                "duration_seconds": result.duration_seconds,
                "exit_code": result.exit_code,
                "timestamp": result.timestamp,
                "tests": [
                    {"node_id": t.node_id, "outcome": t.outcome.name,
                     "duration_ms": t.duration_ms, "file": t.file, "line": t.line}
                    for t in result.tests
                ],
            }
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            logger.warning("Failed to save test history: %s", exc)

    def _load_history(self, target: str) -> Optional[TestSuiteResult]:
        """Load a historical test result from disk."""
        path = self._history_path(target)
        if not os.path.exists(path):
            return None

        try:
            with open(path) as f:
                data = json.load(f)

            result = TestSuiteResult(
                target=data["target"],
                passed=data["passed"],
                failed=data["failed"],
                errors=data.get("errors", 0),
                skipped=data["skipped"],
                total=data["total"],
                duration_seconds=data["duration_seconds"],
                exit_code=data["exit_code"],
                timestamp=data["timestamp"],
                tests=[
                    TestResult(
                        node_id=t["node_id"],
                        outcome=TestOutcome[t["outcome"]],
                        duration_ms=t.get("duration_ms", 0),
                        file=t.get("file", ""),
                        line=t.get("line", 0),
                    )
                    for t in data.get("tests", [])
                ],
            )
            self._history[target] = result
            return result
        except Exception as exc:
            logger.warning("Failed to load test history: %s", exc)
            return None

    def _get_project_root(self) -> str:
        """Get the project root directory (where setup.py/pyproject.toml is)."""
        # Assume this file is at evolution/test_runner.py
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_test_runner(history_dir: Optional[str] = None) -> TestRunner:
    """Factory function to get a TestRunner instance."""
    return TestRunner(history_dir=history_dir)
