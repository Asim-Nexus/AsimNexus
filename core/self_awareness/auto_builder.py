"""
core/self_awareness/auto_builder.py
AsimNexus — AutoBuilder (Self-Building Loop)

The autonomous self-building engine that:
  1. Analyzes gaps via GapAnalyzer
  2. Prioritizes and schedules build actions
  3. Executes builds via SelfBuilder (optionally in parallel)
  4. Runs tests to verify changes (optionally targeted to changed modules)
  5. Rolls back on failure
  6. Records results in SelfKnowledge

This completes the self-building loop:
  Scan → Analyze → Plan → Build → Test → Verify → (Rollback|Commit) → Learn
"""

import asyncio
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .codebase_scanner import CodebaseScanner
from .self_knowledge import SelfKnowledge, IssueRecord
from .self_builder import SelfBuilder, BuildResult
from .gap_analyzer import GapAnalyzer, GapAnalysisResult, Gap

logger = logging.getLogger("AsimNexus.SelfAwareness.AutoBuilder")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Try to load config for AutoBuilder settings
try:
    from asim_config import get_config
    _CONFIG = get_config()
    _AUTO_BUILDER_ENABLED = getattr(_CONFIG, "auto_builder_enabled", True)
    _AUTO_BUILDER_INTERVAL = getattr(_CONFIG, "auto_builder_interval", 7200)
    _AUTO_BUILDER_MAX_ACTIONS = getattr(_CONFIG, "auto_builder_max_actions", 5)
    _AUTO_BUILDER_PARALLEL = getattr(_CONFIG, "auto_builder_parallel", True)
    _AUTO_BUILDER_TEST_TARGETED = getattr(_CONFIG, "auto_builder_test_targeted", True)
except Exception:
    _AUTO_BUILDER_ENABLED = True
    _AUTO_BUILDER_INTERVAL = 7200
    _AUTO_BUILDER_MAX_ACTIONS = 5
    _AUTO_BUILDER_PARALLEL = True
    _AUTO_BUILDER_TEST_TARGETED = True


# ── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class BuildCycle:
    """A single build cycle in the self-building loop."""

    cycle_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "running"       # "running", "completed", "failed", "rolled_back", "healed", "deployed"
    gaps_found: int = 0
    actions_planned: int = 0
    actions_succeeded: int = 0
    actions_failed: int = 0
    actions_rolled_back: int = 0
    tests_before: int = 0
    tests_after: int = 0
    tests_passed_before: int = 0
    tests_passed_after: int = 0
    duration_seconds: float = 0.0
    details: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    # Deployment fields
    deployed: bool = False
    deploy_target: str = ""
    deploy_url: str = ""
    smoke_tests_passed: int = 0
    smoke_tests_total: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "gaps_found": self.gaps_found,
            "actions_planned": self.actions_planned,
            "actions_succeeded": self.actions_succeeded,
            "actions_failed": self.actions_failed,
            "actions_rolled_back": self.actions_rolled_back,
            "tests_before": self.tests_before,
            "tests_after": self.tests_after,
            "tests_passed_before": self.tests_passed_before,
            "tests_passed_after": self.tests_passed_after,
            "duration_seconds": self.duration_seconds,
            "details": self.details,
            "error": self.error,
            "deployed": self.deployed,
            "deploy_target": self.deploy_target,
            "deploy_url": self.deploy_url,
            "smoke_tests_passed": self.smoke_tests_passed,
            "smoke_tests_total": self.smoke_tests_total,
        }


# ── AutoBuilder ───────────────────────────────────────────────────────────

class AutoBuilder:
    """Autonomous self-building engine with test-verify-rollback loop.

    The AutoBuilder orchestrates the complete self-building cycle:
      1. Scan the codebase
      2. Analyze gaps
      3. Plan build actions (prioritized)
      4. Run baseline tests
      5. Execute build actions (with backup, optionally parallel)
      6. Run post-build tests (optionally targeted to changed modules)
      7. Rollback if tests regress (with self-healing)
      8. Auto-deploy to staging if tests pass (optional)
      9. Run smoke tests against deployed server
      10. Record results
    """

    def __init__(
        self,
        scanner: Optional[CodebaseScanner] = None,
        knowledge: Optional[SelfKnowledge] = None,
        builder: Optional[SelfBuilder] = None,
        analyzer: Optional[GapAnalyzer] = None,
        test_command: str = "python -m pytest tests/real/test_self_awareness.py -x -q",
        max_actions_per_cycle: int = _AUTO_BUILDER_MAX_ACTIONS,
        auto_rollback: bool = True,
        parallel_execution: bool = _AUTO_BUILDER_PARALLEL,
        test_targeted: bool = _AUTO_BUILDER_TEST_TARGETED,
        auto_deploy: bool = False,
        deploy_command: str = "",
        smoke_test_command: str = "python -m pytest tests/smoke/ -q --tb=short",
        deploy_url: str = "http://127.0.0.1:8000",
    ):
        self._scanner = scanner
        self._knowledge = knowledge
        self._builder = builder
        self._analyzer = analyzer or GapAnalyzer(scanner, knowledge)
        self._test_command = test_command
        self._max_actions_per_cycle = max_actions_per_cycle
        self._auto_rollback = auto_rollback
        self._parallel_execution = parallel_execution
        self._test_targeted = test_targeted
        self._auto_deploy = auto_deploy
        self._deploy_command = deploy_command
        self._smoke_test_command = smoke_test_command
        self._deploy_url = deploy_url
        self._cycle_history: List[BuildCycle] = []
        self._git_available = self._check_git()
        self._changed_files: Set[str] = set()  # Track files modified in current cycle

    # ── Public API ───────────────────────────────────────────────────────

    async def run_cycle(self) -> BuildCycle:
        """Execute one complete self-building cycle.

        Supports:
          - Parallel execution of independent build actions
          - Targeted test runs for changed modules
          - Git-based file backup before modifications
          - Automatic rollback on test regression
          - Self-healing: analyzes failures and retries with alternatives
          - Auto-deploy: deploys to staging if tests pass (optional)
          - Smoke tests: runs smoke tests against deployed server
          - EvolutionBridge integration: processes Mirror reflections & Dream lessons
          - Direct DreamingEngine integration: triggers dream cycles & feeds lessons

        Returns:
            BuildCycle with full results.
        """
        cycle_id = f"cycle_{int(time.time())}_{os.urandom(4).hex()}"
        cycle = BuildCycle(
            cycle_id=cycle_id,
            started_at=datetime.utcnow().isoformat() + "Z",
        )
        start_time = time.time()
        self._changed_files.clear()

        try:
            # Ensure singletons
            self._ensure_dependencies()

            # Step 1: Scan the codebase
            logger.info("[Cycle %s] Step 1: Scanning codebase...", cycle_id)
            scan_result = self._scanner.scan()
            logger.info("  -> %d modules, %d routes scanned",
                        len(scan_result.modules), scan_result.total_routes)

            # Step 1b: Trigger DreamingEngine cycle for fresh lessons/patterns
            dream_actions: List[Dict[str, Any]] = []
            try:
                from core.dreaming.dreaming_engine import dreaming_engine
                # Trigger a dream cycle to consolidate recent messages
                logger.info("[Cycle %s] Step 1b: Triggering DreamingEngine cycle...", cycle_id)
                briefing = await dreaming_engine.trigger_now()
                cycle.details.append({
                    "step": "dreaming_engine",
                    "briefing": briefing[:200] if briefing else "No briefing",
                })
                # Fetch fresh lessons directly
                fresh_lessons = dreaming_engine.get_recent_lessons(limit=10)
                if fresh_lessons:
                    logger.info("  -> %d fresh lessons from DreamingEngine", len(fresh_lessons))
                    for lesson in fresh_lessons:
                        topics = []
                        if isinstance(lesson, dict):
                            topic = lesson.get("topic", "") or lesson.get("summary", "")
                            if topic:
                                topics.append(topic)
                            # Also check for keywords/topics list
                            kw = lesson.get("topics") or lesson.get("keywords") or []
                            if isinstance(kw, list):
                                topics.extend(kw)
                        # Convert each lesson topic to a build action
                        for t in topics[:2]:
                            dream_actions.append({
                                "action_type": "generate_test",
                                "module": t.replace(" ", "_").replace("/", "_"),
                                "filepath": "",
                                "description": f"[Dream] Lesson: {t[:80]}",
                            })
                # Also get patterns as potential refactoring hints
                patterns = dreaming_engine.get_patterns()
                if patterns:
                    for pattern_name, confidence in patterns.items():
                        if confidence > 0.5 and pattern_name not in ("unknown", ""):
                            dream_actions.append({
                                "action_type": "resolve_todos",
                                "module": pattern_name.replace(" ", "_").replace("/", "_"),
                                "filepath": "",
                                "description": f"[Dream] Pattern (conf={confidence:.2f}): {pattern_name[:80]}",
                            })
                if dream_actions:
                    logger.info("  -> %d dream-derived build actions", len(dream_actions))
            except Exception as exc:
                logger.debug("DreamingEngine trigger skipped: %s", exc)

            # Step 1c: Check MirrorModule for contradiction patterns
            mirror_actions: List[Dict[str, Any]] = []
            try:
                from core.mirror.mirror_module import get_mirror
                # Use "system" user for the self-awareness mirror instance
                mirror = get_mirror("system", user_type="ai")
                # Get daily report for contradiction rate
                report = mirror.get_daily_report()
                contradiction_rate = report.get("contradiction_rate", 0)
                total_contradictions = report.get("total_contradictions", 0)
                if contradiction_rate > 0.3 or total_contradictions > 5:
                    logger.info(
                        "[Cycle %s] Step 1c: MirrorModule contradiction rate=%.2f, total=%d",
                        cycle_id, contradiction_rate, total_contradictions,
                    )
                    mirror_actions.append({
                        "action_type": "resolve_todos",
                        "module": "mirror",
                        "filepath": "",
                        "description": f"[Mirror] High contradiction rate ({contradiction_rate:.2f}, total={total_contradictions})",
                    })
                # Check for recurring contradiction patterns
                try:
                    patterns = mirror._analyze_contradiction_patterns()
                    for pattern in patterns:
                        if pattern.get("count", 0) >= 3 and pattern.get("confidence", 0) >= 0.5:
                            mirror_actions.append({
                                "action_type": "generate_test",
                                "module": "mirror",
                                "filepath": "",
                                "description": f"[Mirror] Pattern: {pattern.get('description', '')[:100]}",
                            })
                except Exception:
                    pass
                # Check for unapplied evolution suggestions with high confidence
                for sug in mirror.evolution_suggestions:
                    if not sug.applied and getattr(sug, 'confidence', 0) > 0.7:
                        mirror_actions.append({
                            "action_type": "resolve_todos",
                            "module": sug.suggestion_type or "mirror",
                            "filepath": "",
                            "description": f"[Mirror] Suggestion (conf={sug.confidence:.2f}): {sug.description[:100]}",
                        })
                if mirror_actions:
                    logger.info("  -> %d mirror-derived build actions", len(mirror_actions))
            except Exception as exc:
                logger.debug("MirrorModule check skipped: %s", exc)

            # Step 2: Analyze gaps
            logger.info("[Cycle %s] Step 2: Analyzing gaps...", cycle_id)
            gap_result = self._analyzer.analyze(self._scanner, self._knowledge)
            cycle.gaps_found = len(gap_result.gaps)
            logger.info("  -> %d gaps found", cycle.gaps_found)

            # Step 2b: Check EvolutionBridge for pending actions (Mirror/Dream)
            bridge_actions: List[Dict[str, Any]] = []
            try:
                from core.self_awareness.evolution_bridge import get_bridge
                bridge = get_bridge()
                pending = bridge.get_actions(limit=20)
                for ba in pending:
                    if ba.source_type in ("mirror_reflection", "dream_lesson"):
                        # Convert bridge action to a build action
                        meta = ba.metadata or {}
                        if ba.source_type == "mirror_reflection":
                            if meta.get("contradiction_count", 0) > 0:
                                bridge_actions.append({
                                    "action_type": "resolve_todos",
                                    "module": "mirror",
                                    "filepath": "",
                                    "description": f"[Bridge] Mirror contradiction: {ba.source_title}",
                                })
                        elif ba.source_type == "dream_lesson":
                            topics = meta.get("topics", [])
                            if topics:
                                for topic in topics[:2]:  # Max 2 per lesson
                                    bridge_actions.append({
                                        "action_type": "generate_test",
                                        "module": topic.replace(" ", "_"),
                                        "filepath": "",
                                        "description": f"[Bridge] Dream lesson topic: {topic}",
                                    })
                if bridge_actions:
                    logger.info("  -> %d bridge actions from EvolutionBridge", len(bridge_actions))
            except Exception as exc:
                logger.debug("EvolutionBridge check skipped: %s", exc)

            # Step 3: Plan build actions (gap analysis + bridge + dream + mirror)
            logger.info("[Cycle %s] Step 3: Planning build actions...", cycle_id)
            gap_actions = self._analyzer.suggest_build_actions(
                gap_result, max_actions=self._max_actions_per_cycle,
            )
            # Merge: mirror actions (highest) → dream actions → bridge actions → gap actions
            build_actions = mirror_actions + dream_actions + bridge_actions + gap_actions
            # Limit to max actions
            build_actions = build_actions[:self._max_actions_per_cycle]
            cycle.actions_planned = len(build_actions)
            logger.info("  -> %d actions planned (%d gaps, %d bridge, %d dream, %d mirror)",
                        cycle.actions_planned, len(gap_actions), len(bridge_actions),
                        len(dream_actions), len(mirror_actions))

            if not build_actions:
                logger.info("[Cycle %s] No actions to take. Cycle complete.", cycle_id)
                cycle.status = "completed"
                cycle.completed_at = datetime.utcnow().isoformat() + "Z"
                cycle.duration_seconds = round(time.time() - start_time, 3)
                self._cycle_history.append(cycle)
                self._record_cycle(cycle)
                return cycle

            # Step 4: Run baseline tests
            logger.info("[Cycle %s] Step 4: Running baseline tests...", cycle_id)
            before = self._run_tests()
            cycle.tests_before = before.get("total", 0)
            cycle.tests_passed_before = before.get("passed", 0)
            logger.info("  -> %d/%d tests passed (baseline)",
                        cycle.tests_passed_before, cycle.tests_before)

            # Step 5: Execute build actions (optionally in parallel)
            logger.info("[Cycle %s] Step 5: Executing %d build actions%s...",
                        cycle_id, len(build_actions),
                        " (parallel)" if self._parallel_execution else "")

            if self._parallel_execution and len(build_actions) > 1:
                # Parallel execution: run independent actions concurrently
                tasks = [
                    self._execute_build_action(action, cycle)
                    for action in build_actions
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        cycle.details.append({
                            "action_type": build_actions[i].get("action_type", "unknown"),
                            "module": build_actions[i].get("module", "unknown"),
                            "filepath": build_actions[i].get("filepath", ""),
                            "description": build_actions[i].get("description", ""),
                            "status": "failed",
                            "error": f"{type(result).__name__}: {result}",
                        })
                        cycle.actions_failed += 1
                    else:
                        cycle.details.append(result)
            else:
                # Sequential execution
                for action in build_actions:
                    result = await self._execute_build_action(action, cycle)
                    cycle.details.append(result)

            # Step 6: Run post-build tests
            logger.info("[Cycle %s] Step 6: Running post-build tests...", cycle_id)
            if self._test_targeted and self._changed_files:
                # Run targeted tests for changed modules
                after = self._run_targeted_tests()
            else:
                after = self._run_tests()

            cycle.tests_after = after.get("total", 0)
            cycle.tests_passed_after = after.get("passed", 0)
            logger.info("  -> %d/%d tests passed (post-build)",
                        cycle.tests_passed_after, cycle.tests_after)

            # Step 7: Verify and self-heal if needed
            if self._auto_rollback and self._should_rollback(before, after):
                logger.warning("[Cycle %s] Tests regressed! Attempting self-heal...", cycle_id)
                # First rollback to restore clean state
                await self._rollback_cycle(cycle)
                cycle.status = "rolled_back"

                # Self-heal: analyze failed actions and retry with alternatives
                healed_actions = await self._self_heal(cycle, build_actions)
                if healed_actions:
                    logger.info("[Cycle %s] Self-heal produced %d alternative actions. Re-executing...",
                                cycle_id, len(healed_actions))
                    # Re-run baseline tests after rollback
                    before_retry = self._run_tests()
                    # Execute healed actions
                    for action in healed_actions:
                        result = await self._execute_build_action(action, cycle)
                        cycle.details.append(result)
                    # Re-test
                    after_retry = self._run_tests()
                    if not self._should_rollback(before_retry, after_retry):
                        cycle.status = "healed"
                        logger.info("[Cycle %s] Self-heal successful! Tests passed.", cycle_id)
                    else:
                        # Final rollback of healed actions
                        logger.warning("[Cycle %s] Self-heal failed. Rolling back healed actions.", cycle_id)
                        await self._rollback_cycle(cycle)
                else:
                    logger.warning("[Cycle %s] No alternative actions for self-heal.", cycle_id)
            else:
                cycle.status = "completed"
                logger.info("[Cycle %s] All actions verified. Cycle complete.", cycle_id)

            # Step 8: Auto-deploy to staging if tests passed and auto_deploy is enabled
            if cycle.status in ("completed", "healed") and self._auto_deploy:
                logger.info("[Cycle %s] Step 8: Deploying to staging...", cycle_id)
                deploy_success = await self._deploy_to_staging(cycle)
                if deploy_success:
                    cycle.status = "deployed"
                    logger.info("[Cycle %s] Deployment successful! Running smoke tests...", cycle_id)
                    # Step 9: Run smoke tests against deployed server
                    smoke_ok, passed, total = await self._run_smoke_tests(cycle)
                    cycle.smoke_tests_passed = passed
                    cycle.smoke_tests_total = total
                    if smoke_ok:
                        logger.info("[Cycle %s] Smoke tests passed: %d/%d", cycle_id, passed, total)
                    else:
                        logger.warning("[Cycle %s] Smoke tests failed: %d/%d", cycle_id, passed, total)
                else:
                    logger.warning("[Cycle %s] Deployment failed.", cycle_id)

        except Exception as exc:
            logger.exception("[Cycle %s] Cycle failed: %s", cycle_id, exc)
            cycle.status = "failed"
            cycle.error = f"{type(exc).__name__}: {exc}"

        finally:
            cycle.completed_at = datetime.utcnow().isoformat() + "Z"
            cycle.duration_seconds = round(time.time() - start_time, 3)
            self._cycle_history.append(cycle)
            self._record_cycle(cycle)

        return cycle

    def get_cycle_history(self, limit: int = 10) -> List[BuildCycle]:
        """Return recent build cycles."""
        return self._cycle_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get AutoBuilder statistics."""
        total = len(self._cycle_history)
        completed = sum(1 for c in self._cycle_history if c.status == "completed")
        failed = sum(1 for c in self._cycle_history if c.status == "failed")
        rolled_back = sum(1 for c in self._cycle_history if c.status == "rolled_back")
        total_actions = sum(c.actions_planned for c in self._cycle_history)
        total_succeeded = sum(c.actions_succeeded for c in self._cycle_history)

        return {
            "total_cycles": total,
            "completed": completed,
            "failed": failed,
            "rolled_back": rolled_back,
            "total_actions_planned": total_actions,
            "total_actions_succeeded": total_succeeded,
            "last_cycle": self._cycle_history[-1].to_dict() if self._cycle_history else None,
        }

    # ── Internals ────────────────────────────────────────────────────────

    def _check_git(self) -> bool:
        """Check if git is available in the project root."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(_PROJECT_ROOT),
            )
            return result.returncode == 0
        except Exception:
            return False

    def _ensure_dependencies(self) -> None:
        """Ensure all dependencies are initialized."""
        if self._scanner is None:
            from . import get_scanner
            self._scanner = get_scanner()
        if self._knowledge is None:
            from . import get_knowledge
            self._knowledge = get_knowledge()
        if self._builder is None:
            from . import get_builder
            self._builder = get_builder()
        if self._analyzer is None:
            self._analyzer = GapAnalyzer(self._scanner, self._knowledge)

    async def _execute_build_action(self, action: Dict[str, Any],
                                     cycle: BuildCycle) -> Dict[str, Any]:
        """Execute a single build action and return its result.

        Supports action types:
          - generate_test       : Generate test file for a module
          - create_init         : Create __init__.py for a package
          - add_docstring       : Add missing docstrings to a file
          - fix_bare_except     : Fix bare except: clauses
          - remove_unused_imports : Remove unused imports from a file
          - resolve_todos       : Create IssueRecords for TODO/FIXME/HACK items
          - generate_route      : Generate a new route module
          - generate_model      : Generate a new Pydantic model module
          - generate_service    : Generate a new service module
          - generate_component  : Generate a new React component
        """
        action_type = action.get("action_type", "unknown")
        module = action.get("module", "unknown")
        filepath = action.get("filepath", "")
        description = action.get("description", "")

        logger.info("  -> Executing: %s on %s", action_type, module)

        result: Dict[str, Any] = {
            "action_type": action_type,
            "module": module,
            "filepath": filepath,
            "description": description,
            "status": "pending",
            "error": None,
        }

        try:
            # Backup file before modification (if git not available)
            if filepath and action_type in ("add_docstring", "fix_bare_except",
                                             "remove_unused_imports", "resolve_todos"):
                self._backup_file(filepath)

            if action_type == "generate_test":
                build_result = self._builder.generate_test_file(module)
                result["status"] = "succeeded" if build_result.success else "failed"
                result["error"] = build_result.error
                if build_result.success:
                    cycle.actions_succeeded += 1
                    # Track generated test file for targeted testing
                    test_path = f"tests/test_{module.replace('.', '/')}.py"
                    self._changed_files.add(test_path)
                else:
                    cycle.actions_failed += 1

            elif action_type == "create_init":
                pkg_dir = Path(filepath).parent if filepath else _PROJECT_ROOT / module.replace(".", "/")
                init_path = pkg_dir / "__init__.py"
                if not init_path.exists():
                    init_path.write_text(
                        f'# {module}\n"""\n{module} package.\n"""\n\n'
                        f'__all__: list = []\n',
                        encoding="utf-8",
                    )
                    result["status"] = "succeeded"
                    cycle.actions_succeeded += 1
                    self._changed_files.add(str(init_path))
                else:
                    result["status"] = "skipped"
                    result["error"] = "Already exists"

            elif action_type == "add_docstring":
                if filepath:
                    build_result = self._builder.add_missing_docstrings(filepath)
                    result["status"] = "succeeded" if build_result.success else "failed"
                    result["error"] = build_result.error
                    if build_result.success:
                        cycle.actions_succeeded += 1
                        self._changed_files.add(filepath)
                    else:
                        cycle.actions_failed += 1
                else:
                    result["status"] = "skipped"
                    result["error"] = "No filepath provided"

            elif action_type == "fix_bare_except":
                if filepath:
                    build_result = self._builder.fix_bare_excepts(filepath)
                    result["status"] = "succeeded" if build_result.success else "failed"
                    result["error"] = build_result.error
                    if build_result.success:
                        cycle.actions_succeeded += 1
                        self._changed_files.add(filepath)
                    else:
                        cycle.actions_failed += 1
                else:
                    result["status"] = "skipped"
                    result["error"] = "No filepath provided"

            elif action_type == "remove_unused_imports":
                if filepath:
                    build_result = self._builder.remove_unused_imports(filepath)
                    result["status"] = "succeeded" if build_result.success else "failed"
                    result["error"] = build_result.error
                    if build_result.success:
                        cycle.actions_succeeded += 1
                        self._changed_files.add(filepath)
                    else:
                        cycle.actions_failed += 1
                else:
                    result["status"] = "skipped"
                    result["error"] = "No filepath provided"

            elif action_type == "resolve_todos":
                if filepath:
                    build_result = self._builder.resolve_todos(filepath)
                    result["status"] = "succeeded" if build_result.success else "failed"
                    result["error"] = build_result.error
                    if build_result.success:
                        cycle.actions_succeeded += 1
                        self._changed_files.add(filepath)
                    else:
                        cycle.actions_failed += 1
                else:
                    result["status"] = "skipped"
                    result["error"] = "No filepath provided"

            elif action_type == "generate_route":
                routes = action.get("routes", [{"method": "GET", "path": "/", "func_name": "root", "summary": "Root endpoint"}])
                build_result = self._builder.generate_route_module(module, routes)
                result["status"] = "succeeded" if build_result.success else "failed"
                result["error"] = build_result.error
                if build_result.success:
                    cycle.actions_succeeded += 1
                    route_path = f"routes/{module}.py"
                    self._changed_files.add(route_path)
                    # Auto-generate test for the new route module
                    self._auto_generate_test(module, cycle)
                else:
                    cycle.actions_failed += 1

            elif action_type == "generate_model":
                fields = action.get("fields", None)
                build_result = self._builder.generate_model_module(module, fields)
                result["status"] = "succeeded" if build_result.success else "failed"
                result["error"] = build_result.error
                if build_result.success:
                    cycle.actions_succeeded += 1
                    model_path = f"models/{module}.py"
                    self._changed_files.add(model_path)
                    # Auto-generate test for the new model module
                    self._auto_generate_test(module, cycle)
                else:
                    cycle.actions_failed += 1

            elif action_type == "generate_service":
                build_result = self._builder.generate_service_module(module)
                result["status"] = "succeeded" if build_result.success else "failed"
                result["error"] = build_result.error
                if build_result.success:
                    cycle.actions_succeeded += 1
                    svc_path = f"services/{module}_service.py"
                    self._changed_files.add(svc_path)
                    # Auto-generate test for the new service module
                    self._auto_generate_test(module, cycle)
                else:
                    cycle.actions_failed += 1

            elif action_type == "generate_component":
                component_name = action.get("component_name", module.title().replace("_", "") + "List")
                service_name = action.get("service_name", module)
                api_module = action.get("api_module", "api")
                build_result = self._builder.generate_react_component(component_name, service_name, api_module)
                result["status"] = "succeeded" if build_result.success else "failed"
                result["error"] = build_result.error
                if build_result.success:
                    cycle.actions_succeeded += 1
                    comp_path = f"frontend/src/components/{component_name}.tsx"
                    self._changed_files.add(comp_path)
                else:
                    cycle.actions_failed += 1

            else:
                result["status"] = "skipped"
                result["error"] = f"Unknown action type: {action_type}"

        except Exception as exc:
            logger.error("  -> Action failed: %s", exc)
            result["status"] = "failed"
            result["error"] = f"{type(exc).__name__}: {exc}"
            cycle.actions_failed += 1

        return result

    def _backup_file(self, filepath: str) -> Optional[str]:
        """Create a backup of a file before modification.

        Uses git stash-like approach if git is available,
        otherwise copies to a .backups directory.
        Returns the backup path or None on failure.
        """
        try:
            src = Path(filepath)
            if not src.exists():
                return None

            backup_dir = src.parent / ".backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{src.name}.{timestamp}.bak"
            shutil.copy2(str(src), str(backup_path))
            logger.debug("  -> Backed up %s to %s", filepath, backup_path)
            return str(backup_path)
        except Exception as exc:
            logger.warning("  -> Backup failed for %s: %s", filepath, exc)
            return None

    def _run_tests(self) -> Dict[str, int]:
        """Run the test suite and return results.

        Returns:
            Dict with 'total' and 'passed' counts.
        """
        try:
            result = subprocess.run(
                self._test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                cwd=str(_PROJECT_ROOT),
            )

            output = result.stdout + result.stderr

            # Parse pytest output for summary
            total = 0
            passed = 0
            for line in output.split("\n"):
                if "passed" in line and "failed" in line:
                    # e.g., "3 passed, 0 failed in 0.45s"
                    m = re.search(r'(\d+)\s+passed', line)
                    if m:
                        passed = int(m.group(1))
                    m = re.search(r'(\d+)\s+failed', line)
                    if m:
                        total = passed + int(m.group(1))
                    else:
                        total = passed
                    break

            return {"total": total, "passed": passed}

        except subprocess.TimeoutExpired:
            logger.warning("Tests timed out after 120s")
            return {"total": 0, "passed": 0}
        except Exception as exc:
            logger.warning("Test run failed: %s", exc)
            return {"total": 0, "passed": 0}

    def _run_targeted_tests(self) -> Dict[str, int]:
        """Run tests only for modules that were changed in this cycle.

        Falls back to full test suite if no specific test files can be
        determined for the changed modules.
        """
        if not self._changed_files:
            return self._run_tests()

        # Map changed files to potential test files
        test_targets: List[str] = []
        for changed in self._changed_files:
            p = Path(changed)
            # Skip non-Python files (e.g. .tsx, .ts) — no Python tests for them
            if p.suffix not in (".py",):
                continue
            # If the changed file is itself a test file, run it
            if "test_" in p.name or p.name.startswith("test_"):
                test_targets.append(str(p))
            else:
                # Look for corresponding test file
                stem = p.stem
                test_candidates = [
                    _PROJECT_ROOT / "tests" / "real" / f"test_{stem}.py",
                    _PROJECT_ROOT / "tests" / "unit" / f"test_{stem}.py",
                    _PROJECT_ROOT / "tests" / "integration" / f"test_{stem}.py",
                ]
                for tc in test_candidates:
                    if tc.exists():
                        test_targets.append(str(tc))
                        break

        if not test_targets:
            logger.info("  -> No targeted tests found, running full suite")
            return self._run_tests()

        # Build targeted test command
        targets_str = " ".join(test_targets)
        targeted_cmd = f"python -m pytest {targets_str} -x -q"
        logger.info("  -> Running targeted tests: %s", targeted_cmd)

        try:
            result = subprocess.run(
                targeted_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(_PROJECT_ROOT),
            )

            output = result.stdout + result.stderr
            total = 0
            passed = 0
            for line in output.split("\n"):
                if "passed" in line and "failed" in line:
                    m = re.search(r'(\d+)\s+passed', line)
                    if m:
                        passed = int(m.group(1))
                    m = re.search(r'(\d+)\s+failed', line)
                    if m:
                        total = passed + int(m.group(1))
                    else:
                        total = passed
                    break

            return {"total": total, "passed": passed}

        except subprocess.TimeoutExpired:
            logger.warning("Targeted tests timed out after 120s")
            return {"total": 0, "passed": 0}
        except Exception as exc:
            logger.warning("Targeted test run failed: %s", exc)
            return {"total": 0, "passed": 0}

    def _should_rollback(self, before: Dict[str, int],
                          after: Dict[str, int]) -> bool:
        """Determine if we should rollback based on test results.

        Rollback if:
          - Post-build tests have fewer passes than baseline
          - Post-build tests have 0 passes (complete failure)
        """
        before_passed = before.get("passed", 0)
        after_passed = after.get("passed", 0)

        if after_passed < before_passed:
            logger.warning(
                "Test regression detected: %d passed (before) vs %d passed (after)",
                before_passed, after_passed,
            )
            return True

        if after_passed == 0 and before_passed > 0:
            logger.warning("Complete test failure after build actions")
            return True

        return False

    async def _rollback_cycle(self, cycle: BuildCycle) -> None:
        """Rollback all actions in this cycle using SelfBuilder.rollback()."""
        for detail in cycle.details:
            if detail.get("status") != "succeeded":
                continue

            action_type = detail.get("action_type", "")
            filepath = detail.get("filepath", "")

            # For file-based actions, try to restore from backup
            if filepath and self._builder:
                try:
                    # Find the most recent backup
                    backup_dir = Path(filepath).parent / ".backups"
                    if backup_dir.exists():
                        backups = sorted(backup_dir.glob(f"{Path(filepath).name}.*.bak"))
                        if backups:
                            shutil.copy2(backups[-1], filepath)
                            logger.info("  -> Rolled back %s from backup", filepath)
                            cycle.actions_rolled_back += 1
                except Exception as exc:
                    logger.warning("  -> Rollback failed for %s: %s", filepath, exc)

    async def _self_heal(self, cycle: BuildCycle,
                          original_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze failed actions and produce alternative approaches.

        Examines which actions failed or caused regression, then generates
        alternative actions with different parameters or approaches.

        Returns:
            List of alternative build actions to retry.
        """
        healed: List[Dict[str, Any]] = []
        failed_details = [d for d in cycle.details if d.get("status") == "failed"]

        if not failed_details:
            # All actions succeeded but tests regressed — try gentler alternatives
            logger.info("  -> All actions succeeded but tests regressed. Trying gentler alternatives.")
            for action in original_actions:
                action_type = action.get("action_type", "")
                module = action.get("module", "")
                if action_type == "fix_bare_except":
                    # Skip bare except fixes — they're risky
                    logger.info("  -> Skipping fix_bare_except for %s (too risky)", module)
                    continue
                elif action_type == "remove_unused_imports":
                    # Skip import removal — might break things
                    logger.info("  -> Skipping remove_unused_imports for %s (too risky)", module)
                    continue
                elif action_type == "add_docstring":
                    # Docstrings are safe — keep them
                    healed.append(action)
                elif action_type == "resolve_todos":
                    # TODOs are safe — keep them
                    healed.append(action)
                elif action_type == "generate_test":
                    # Test generation is safe — keep it
                    healed.append(action)
                elif action_type == "create_init":
                    # __init__.py creation is safe — keep it
                    healed.append(action)
                # Skip generate_route, generate_model, generate_service, generate_component
                # — these create new files that might conflict
            return healed

        # Analyze each failed action
        for detail in failed_details:
            action_type = detail.get("action_type", "")
            module = detail.get("module", "")
            error = detail.get("error", "")

            logger.info("  -> Healing failed action: %s on %s (error: %s)",
                        action_type, module, error)

            if action_type == "generate_test":
                # Test generation failed — try with different module path
                alt_action = {
                    "action_type": "generate_test",
                    "module": module,
                    "filepath": "",
                    "description": f"Retry: generate test for {module}",
                }
                healed.append(alt_action)

            elif action_type == "generate_route":
                # Route generation failed — try with simpler routes
                alt_action = {
                    "action_type": "generate_route",
                    "module": module,
                    "routes": [{"method": "GET", "path": "/", "func_name": "root",
                                "summary": f"Root endpoint for {module}"}],
                    "description": f"Retry: generate route for {module} (simplified)",
                }
                healed.append(alt_action)

            elif action_type == "generate_model":
                # Model generation failed — try with default fields
                alt_action = {
                    "action_type": "generate_model",
                    "module": module,
                    "fields": None,  # Use defaults
                    "description": f"Retry: generate model for {module} (default fields)",
                }
                healed.append(alt_action)

            elif action_type == "generate_service":
                # Service generation failed — try with different name
                alt_action = {
                    "action_type": "generate_service",
                    "module": module,
                    "description": f"Retry: generate service for {module}",
                }
                healed.append(alt_action)

            elif action_type == "generate_component":
                # Component generation failed — try with default params
                alt_action = {
                    "action_type": "generate_component",
                    "module": module,
                    "component_name": module.title().replace("_", "") + "List",
                    "service_name": module,
                    "api_module": "api",
                    "description": f"Retry: generate component for {module} (default params)",
                }
                healed.append(alt_action)

            elif action_type in ("fix_bare_except", "remove_unused_imports",
                                  "add_docstring", "resolve_todos"):
                # These operate on filepath — skip if filepath is missing
                filepath = detail.get("filepath", "")
                if filepath:
                    healed.append({
                        "action_type": action_type,
                        "module": module,
                        "filepath": filepath,
                        "description": f"Retry: {action_type} on {filepath}",
                    })

        return healed

    def _auto_generate_test(self, module: str, cycle: BuildCycle) -> None:
        """Auto-generate a test file for a newly generated module.

        Called after successful code generation actions to ensure
        new modules have corresponding test coverage.

        Args:
            module: The module name (e.g. "routes.payment" or "payment")
            cycle: The current build cycle to record results in.
        """
        try:
            # Strip package prefix if present
            simple_name = module.split(".")[-1] if "." in module else module
            logger.info("  -> Auto-generating test for %s...", simple_name)
            build_result = self._builder.generate_test_file(simple_name, test_type="unit")
            if build_result.success:
                logger.info("  -> Test generated for %s", simple_name)
                test_path = f"tests/unit/test_{simple_name}.py"
                self._changed_files.add(test_path)
            else:
                logger.info("  -> Test generation for %s skipped: %s",
                            simple_name, build_result.error)
        except Exception as exc:
            logger.warning("  -> Auto-test generation failed for %s: %s", module, exc)

    async def _deploy_to_staging(self, cycle: BuildCycle) -> bool:
        """Deploy the current build to staging environment.

        Uses the configured deploy command (e.g. docker-compose up,
        git push, or custom script). If no deploy command is configured,
        attempts a default git-based deployment.

        Args:
            cycle: The current build cycle to record deployment info in.

        Returns:
            True if deployment succeeded, False otherwise.
        """
        try:
            if self._deploy_command:
                # Use custom deploy command
                logger.info("  -> Running deploy command: %s", self._deploy_command)
                result = subprocess.run(
                    self._deploy_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout for deployment
                    cwd=str(_PROJECT_ROOT),
                )
                if result.returncode != 0:
                    logger.error("  -> Deploy command failed (rc=%d): %s",
                                 result.returncode, result.stderr[:500])
                    return False
                logger.info("  -> Deploy command succeeded")
                cycle.deploy_target = self._deploy_command.split(" ")[0]
                cycle.deploy_url = self._deploy_url
                cycle.deployed = True
                return True

            # Default: git-based deployment
            if not self._git_available:
                logger.warning("  -> Git not available, cannot deploy")
                return False

            logger.info("  -> Deploying via git...")
            # Stage all changes
            result = subprocess.run(
                ["git", "add", "-A"],
                capture_output=True, text=True, timeout=30,
                cwd=str(_PROJECT_ROOT),
            )
            if result.returncode != 0:
                logger.warning("  -> Git add failed: %s", result.stderr[:200])
                return False

            # Commit with cycle info
            commit_msg = f"Auto-build cycle {cycle.cycle_id}: {cycle.actions_succeeded} actions, {cycle.tests_passed_after}/{cycle.tests_after} tests"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg, "--allow-empty"],
                capture_output=True, text=True, timeout=30,
                cwd=str(_PROJECT_ROOT),
            )
            if result.returncode != 0:
                logger.warning("  -> Git commit failed: %s", result.stderr[:200])
                return False

            # Push to remote
            result = subprocess.run(
                ["git", "push"],
                capture_output=True, text=True, timeout=60,
                cwd=str(_PROJECT_ROOT),
            )
            if result.returncode != 0:
                logger.warning("  -> Git push failed: %s", result.stderr[:200])
                return False

            logger.info("  -> Git push succeeded")
            cycle.deploy_target = "git"
            cycle.deploy_url = self._deploy_url
            cycle.deployed = True
            return True

        except subprocess.TimeoutExpired:
            logger.error("  -> Deploy timed out after 300s")
            return False
        except Exception as exc:
            logger.error("  -> Deploy failed: %s", exc)
            return False

    async def _run_smoke_tests(self, cycle: BuildCycle) -> Tuple[bool, int, int]:
        """Run smoke tests against the deployed server.

        Executes the configured smoke test command and parses results.
        Smoke tests verify that the deployed server is responding correctly
        to basic API requests.

        Args:
            cycle: The current build cycle for context.

        Returns:
            Tuple of (all_passed, passed_count, total_count).
        """
        try:
            logger.info("  -> Running smoke tests against %s...", self._deploy_url)
            result = subprocess.run(
                self._smoke_test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout for smoke tests
                cwd=str(_PROJECT_ROOT),
            )

            output = result.stdout + result.stderr
            logger.info("  -> Smoke test output:\n%s", output[:1000])

            # Parse pytest output for summary
            total = 0
            passed = 0
            for line in output.split("\n"):
                if "passed" in line and "failed" in line:
                    m = re.search(r'(\d+)\s+passed', line)
                    if m:
                        passed = int(m.group(1))
                    m = re.search(r'(\d+)\s+failed', line)
                    if m:
                        total = passed + int(m.group(1))
                    else:
                        total = passed
                    break

            all_passed = (result.returncode == 0) and (total > 0) and (passed == total)
            return all_passed, passed, total

        except subprocess.TimeoutExpired:
            logger.warning("  -> Smoke tests timed out after 120s")
            return False, 0, 0
        except Exception as exc:
            logger.warning("  -> Smoke tests failed: %s", exc)
            return False, 0, 0

    def _record_cycle(self, cycle: BuildCycle) -> None:
        """Record the build cycle in SelfKnowledge."""
        if not self._knowledge:
            return
        try:
            self._knowledge.store_knowledge(
                key=f"build_cycle:{cycle.cycle_id}",
                value=cycle.to_dict(),
                source="auto_builder",
                metadata={"cycle_id": cycle.cycle_id, "status": cycle.status},
            )
        except Exception as exc:
            logger.warning("Failed to record cycle: %s", exc)


# ── Singleton ─────────────────────────────────────────────────────────────

_auto_builder: Optional[AutoBuilder] = None


def get_auto_builder() -> AutoBuilder:
    """Get or create the singleton AutoBuilder."""
    global _auto_builder
    if _auto_builder is None:
        _auto_builder = AutoBuilder()
    return _auto_builder


def reset_auto_builder() -> None:
    """Reset the singleton (for testing)."""
    global _auto_builder
    _auto_builder = None
