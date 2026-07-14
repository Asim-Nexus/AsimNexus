"""
core/self_awareness/gap_analyzer.py
AsimNexus — Gap Analyzer

Analyzes the codebase to identify gaps, inconsistencies, and improvement
opportunities. This is the "brain" of the self-building loop that decides
WHAT needs to be built or fixed next.

Capabilities:
  - Detect modules without tests (test coverage gaps)
  - Detect modules without route registration (orphaned modules)
  - Detect missing __init__.py exports
  - Detect inconsistent naming conventions
  - Detect duplicate functionality
  - Prioritize gaps by impact and effort
  - Generate actionable build suggestions
"""

import ast
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .codebase_scanner import CodebaseScanner, ScanResult, ModuleInfo
from .self_knowledge import SelfKnowledge, IssueRecord

logger = logging.getLogger("AsimNexus.SelfAwareness.GapAnalyzer")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class Gap:
    """A single gap or improvement opportunity identified in the codebase."""

    gap_id: str
    category: str          # "test_coverage", "orphaned_module", "missing_exports",
                           # "naming_inconsistency", "duplicate_functionality",
                           # "missing_docstrings", "bare_except", "todo_resolved"
    module: str            # Affected module package path
    description: str       # Human-readable description
    severity: str          # "critical", "high", "medium", "low", "info"
    effort: str            # "small", "medium", "large"
    impact: str            # "high", "medium", "low"
    suggestion: str        # What to do about it
    auto_fixable: bool     # Can SelfBuilder fix this automatically?
    filepath: Optional[str] = None
    line_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "category": self.category,
            "module": self.module,
            "description": self.description,
            "severity": self.severity,
            "effort": self.effort,
            "impact": self.impact,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
            "priority_score": self.priority_score,
            "filepath": self.filepath,
            "line_number": self.line_number,
            "metadata": self.metadata,
        }

    @property
    def priority_score(self) -> float:
        """Compute a numeric priority score (higher = more urgent)."""
        severity_map = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        impact_map = {"high": 3, "medium": 2, "low": 1}
        effort_map = {"small": 3, "medium": 2, "large": 1}
        s = severity_map.get(self.severity, 1)
        i = impact_map.get(self.impact, 1)
        e = effort_map.get(self.effort, 1)
        return s * i * e


@dataclass
class GapAnalysisResult:
    """Result of a full gap analysis run."""

    gaps: List[Gap] = field(default_factory=list)
    total_modules_scanned: int = 0
    total_routes: int = 0
    total_issues: int = 0
    scan_duration_ms: float = 0.0

    def top_gaps(self, n: int = 10) -> List[Gap]:
        """Return the top N gaps sorted by priority score."""
        sorted_gaps = sorted(self.gaps, key=lambda g: g.priority_score, reverse=True)
        return sorted_gaps[:n]

    def by_category(self) -> Dict[str, List[Gap]]:
        """Group gaps by category."""
        result: Dict[str, List[Gap]] = {}
        for g in self.gaps:
            result.setdefault(g.category, []).append(g)
        return result

    def auto_fixable_gaps(self) -> List[Gap]:
        """Return gaps that can be automatically fixed."""
        return [g for g in self.gaps if g.auto_fixable]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_gaps": len(self.gaps),
            "total_modules_scanned": self.total_modules_scanned,
            "total_routes": self.total_routes,
            "total_issues": self.total_issues,
            "scan_duration_ms": self.scan_duration_ms,
            "gaps": [g.to_dict() for g in self.gaps],
            "by_category": {
                cat: [g.to_dict() for g in gaps]
                for cat, gaps in self.by_category().items()
            },
        }


# ── Gap Analyzer ──────────────────────────────────────────────────────────

class GapAnalyzer:
    """Analyzes the codebase for gaps and improvement opportunities."""

    def __init__(self, scanner: Optional[CodebaseScanner] = None,
                 knowledge: Optional[SelfKnowledge] = None):
        self._scanner = scanner
        self._knowledge = knowledge

    # ── Public API ───────────────────────────────────────────────────────

    def analyze(self, scanner: Optional[CodebaseScanner] = None,
                knowledge: Optional[SelfKnowledge] = None) -> GapAnalysisResult:
        """Run a full gap analysis on the codebase.

        Args:
            scanner: CodebaseScanner instance (uses singleton if not provided)
            knowledge: SelfKnowledge instance (uses singleton if not provided)

        Returns:
            GapAnalysisResult with all identified gaps.
        """
        import time
        start = time.perf_counter()

        s = scanner or self._scanner
        k = knowledge or self._knowledge

        # Ensure we have a scan result
        if s is None:
            from . import get_scanner
            s = get_scanner()
        if k is None:
            from . import get_knowledge
            k = get_knowledge()

        # Run scan if not already done
        result = s.scan()

        gaps: List[Gap] = []

        # Run all gap detectors
        gaps.extend(self._detect_test_coverage_gaps(s, result))
        gaps.extend(self._detect_orphaned_modules(s, result))
        gaps.extend(self._detect_missing_exports(s, result))
        gaps.extend(self._detect_missing_init_exports(s, result))
        gaps.extend(self._detect_missing_api_routes(s, result))
        gaps.extend(self._detect_missing_frontend_components(s, result))
        gaps.extend(self._detect_naming_inconsistencies(s, result))
        gaps.extend(self._detect_duplicate_functionality(s, result))
        gaps.extend(self._detect_missing_docstrings(s, result))
        gaps.extend(self._detect_bare_excepts(s, result))
        gaps.extend(self._detect_todos(s, result))
        gaps.extend(self._detect_knowledge_issues(k))

        elapsed = (time.perf_counter() - start) * 1000

        return GapAnalysisResult(
            gaps=gaps,
            total_modules_scanned=len(result.modules),
            total_routes=result.total_routes,
            total_issues=len(result.errors),
            scan_duration_ms=round(elapsed, 2),
        )

    def suggest_build_actions(self, result: GapAnalysisResult,
                              max_actions: int = 5) -> List[Dict[str, Any]]:
        """Convert top gaps into actionable build suggestions for SelfBuilder.

        Args:
            result: GapAnalysisResult from analyze()
            max_actions: Maximum number of build actions to suggest

        Returns:
            List of build action dicts that can be fed to SelfBuilder.
        """
        suggestions = []
        for gap in result.top_gaps(max_actions):
            action = self._gap_to_build_action(gap)
            if action:
                suggestions.append(action)
        return suggestions

    # ── Gap Detectors ────────────────────────────────────────────────────

    def _detect_test_coverage_gaps(self, scanner: CodebaseScanner,
                                   result: ScanResult) -> List[Gap]:
        """Find modules that don't have corresponding test files."""
        gaps = []
        test_dir = _PROJECT_ROOT / "tests"
        if not test_dir.exists():
            return gaps

        test_files = set()
        for root, _dirs, files in os.walk(str(test_dir)):
            for f in files:
                if f.endswith(".py") and f.startswith("test_"):
                    test_files.add(f)

        for mod_name, mod_info in result.modules.items():
            # Skip __init__.py and non-core modules
            if mod_name.endswith(".__init__") or mod_name.startswith("_"):
                continue
            # Derive expected test filename
            base_name = mod_name.replace(".", "/")
            expected_test = f"test_{Path(base_name).name}.py"
            if expected_test not in test_files:
                gaps.append(Gap(
                    gap_id=f"test_{mod_name}",
                    category="test_coverage",
                    module=mod_name,
                    description=f"Module '{mod_name}' has no corresponding test file",
                    severity="medium",
                    effort="medium",
                    impact="high",
                    suggestion=f"Create tests/{expected_test} with unit tests for {mod_name}",
                    auto_fixable=True,
                    filepath=mod_info.filepath,
                    metadata={"expected_test_file": f"tests/{expected_test}"},
                ))
        return gaps

    def _detect_orphaned_modules(self, scanner: CodebaseScanner,
                                  result: ScanResult) -> List[Gap]:
        """Find modules that are not imported anywhere (orphaned)."""
        gaps = []
        orphaned = scanner.get_orphaned_modules()
        for mod_name in orphaned:
            mod_info = result.modules.get(mod_name)
            gaps.append(Gap(
                gap_id=f"orphan_{mod_name}",
                category="orphaned_module",
                module=mod_name,
                description=f"Module '{mod_name}' is orphaned (not imported by any other module)",
                severity="medium",
                effort="small",
                impact="medium",
                suggestion=f"Check if '{mod_name}' is still needed; add imports or remove",
                auto_fixable=False,
                filepath=mod_info.filepath if mod_info else None,
            ))
        return gaps

    def _detect_missing_exports(self, scanner: CodebaseScanner,
                                 result: ScanResult) -> List[Gap]:
        """Find packages missing __init__.py or with incomplete __all__ exports."""
        gaps = []
        packages_seen: Set[str] = set()

        for mod_name, mod_info in result.modules.items():
            pkg = ".".join(mod_name.split(".")[:-1]) if "." in mod_name else ""
            if not pkg or pkg in packages_seen:
                continue
            packages_seen.add(pkg)

            # Check if __init__.py exists for this package
            init_path = _PROJECT_ROOT / pkg.replace(".", "/") / "__init__.py"
            if not init_path.exists():
                gaps.append(Gap(
                    gap_id=f"missing_init_{pkg}",
                    category="missing_exports",
                    module=pkg,
                    description=f"Package '{pkg}' is missing __init__.py",
                    severity="high",
                    effort="small",
                    impact="high",
                    suggestion=f"Create {pkg}/__init__.py with proper exports",
                    auto_fixable=True,
                    filepath=str(init_path),
                ))
                continue

            # Check if __all__ is defined
            try:
                source = init_path.read_text(encoding="utf-8")
                tree = ast.parse(source)
                has_all = any(
                    isinstance(node, ast.Assign)
                    for node in ast.walk(tree)
                    if hasattr(node, "targets")
                    and any(
                        isinstance(t, ast.Name) and t.id == "__all__"
                        for t in node.targets
                    )
                )
                if not has_all:
                    # Only flag if there are public names to export
                    public_names = [
                        node.name for node in tree.body
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                        and not node.name.startswith("_")
                    ]
                    if public_names:
                        gaps.append(Gap(
                            gap_id=f"missing_all_{pkg}",
                            category="missing_exports",
                            module=pkg,
                            description=f"Package '{pkg}' has public names but no __all__ in __init__.py",
                            severity="low",
                            effort="small",
                            impact="medium",
                            suggestion=f"Add __all__ = {public_names} to {pkg}/__init__.py",
                            auto_fixable=True,
                            filepath=str(init_path),
                            metadata={"public_names": public_names},
                        ))
            except SyntaxError:
                pass

        return gaps

    def _detect_naming_inconsistencies(self, scanner: CodebaseScanner,
                                        result: ScanResult) -> List[Gap]:
        """Detect inconsistent naming conventions across the codebase."""
        gaps = []
        # Check for mixed snake_case and camelCase in function names
        snake_case = re.compile(r'^[a-z][a-z0-9_]*$')
        camel_case = re.compile(r'^[a-z][a-zA-Z0-9]*$')

        for mod_name, mod_info in result.modules.items():
            if not mod_info.filepath:
                continue
            try:
                source = Path(mod_info.filepath).read_text(encoding="utf-8")
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        name = node.name
                        if name.startswith("_"):
                            continue
                        # Check if it's a test function
                        if name.startswith("test_"):
                            continue
                        # Flag if it looks like camelCase in a snake_case codebase
                        if camel_case.match(name) and not snake_case.match(name):
                            gaps.append(Gap(
                                gap_id=f"naming_{mod_name}_{name}",
                                category="naming_inconsistency",
                                module=mod_name,
                                description=f"Function '{name}' in {mod_name} uses camelCase (expected snake_case)",
                                severity="low",
                                effort="medium",
                                impact="low",
                                suggestion=f"Rename '{name}' to snake_case",
                                auto_fixable=False,
                                filepath=mod_info.filepath,
                                line_number=node.lineno,
                            ))
            except (SyntaxError, UnicodeDecodeError):
                continue

        return gaps

    def _detect_duplicate_functionality(self, scanner: CodebaseScanner,
                                         result: ScanResult) -> List[Gap]:
        """Detect potential duplicate functionality across modules."""
        gaps = []
        # Simple heuristic: look for modules with very similar names
        all_names = list(result.modules.keys())
        for i, name_a in enumerate(all_names):
            for name_b in all_names[i + 1:]:
                # Check for modules that differ only by suffix
                base_a = name_a.rsplit(".", 1)[-1] if "." in name_a else name_a
                base_b = name_b.rsplit(".", 1)[-1] if "." in name_b else name_b
                if base_a == base_b and name_a != name_b:
                    gaps.append(Gap(
                        gap_id=f"duplicate_{base_a}",
                        category="duplicate_functionality",
                        module=name_a,
                        description=f"Potential duplicate: '{name_a}' and '{name_b}' have the same base name",
                        severity="medium",
                        effort="large",
                        impact="medium",
                        suggestion=f"Consolidate '{name_a}' and '{name_b}' into a single module",
                        auto_fixable=False,
                        metadata={"duplicate_of": name_b},
                    ))
        return gaps

    def _detect_missing_docstrings(self, scanner: CodebaseScanner,
                                    result: ScanResult) -> List[Gap]:
        """Detect modules/functions/classes missing docstrings."""
        gaps = []
        for mod_name, mod_info in result.modules.items():
            if not mod_info.filepath:
                continue
            try:
                source = Path(mod_info.filepath).read_text(encoding="utf-8")
                tree = ast.parse(source)

                # Check module-level docstring
                if not ast.get_docstring(tree):
                    gaps.append(Gap(
                        gap_id=f"docstring_module_{mod_name}",
                        category="missing_docstrings",
                        module=mod_name,
                        description=f"Module '{mod_name}' is missing a module-level docstring",
                        severity="low",
                        effort="small",
                        impact="medium",
                        suggestion=f"Add a module-level docstring to {mod_info.filepath}",
                        auto_fixable=True,
                        filepath=mod_info.filepath,
                    ))

                # Check public functions and classes
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith("_"):
                            continue
                        if not ast.get_docstring(node):
                            gaps.append(Gap(
                                gap_id=f"docstring_func_{mod_name}_{node.name}",
                                category="missing_docstrings",
                                module=mod_name,
                                description=f"Function '{node.name}' in {mod_name} is missing a docstring",
                                severity="low",
                                effort="small",
                                impact="medium",
                                suggestion=f"Add a docstring to '{node.name}' in {mod_info.filepath}",
                                auto_fixable=True,
                                filepath=mod_info.filepath,
                                line_number=node.lineno,
                            ))
                    elif isinstance(node, ast.ClassDef):
                        if not ast.get_docstring(node):
                            gaps.append(Gap(
                                gap_id=f"docstring_class_{mod_name}_{node.name}",
                                category="missing_docstrings",
                                module=mod_name,
                                description=f"Class '{node.name}' in {mod_name} is missing a docstring",
                                severity="low",
                                effort="small",
                                impact="medium",
                                suggestion=f"Add a docstring to '{node.name}' in {mod_info.filepath}",
                                auto_fixable=True,
                                filepath=mod_info.filepath,
                                line_number=node.lineno,
                            ))
            except (SyntaxError, UnicodeDecodeError):
                continue

        return gaps

    def _detect_bare_excepts(self, scanner: CodebaseScanner,
                              result: ScanResult) -> List[Gap]:
        """Detect bare 'except:' clauses that should be specific."""
        gaps = []
        for mod_name, mod_info in result.modules.items():
            if not mod_info.filepath:
                continue
            try:
                source = Path(mod_info.filepath).read_text(encoding="utf-8")
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        if node.type is None:
                            gaps.append(Gap(
                                gap_id=f"bare_except_{mod_name}_{node.lineno}",
                                category="bare_except",
                                module=mod_name,
                                description=f"Bare 'except:' at line {node.lineno} in {mod_name}",
                                severity="high",
                                effort="small",
                                impact="high",
                                suggestion=f"Replace bare 'except:' with specific exception type at {mod_info.filepath}:{node.lineno}",
                                auto_fixable=True,
                                filepath=mod_info.filepath,
                                line_number=node.lineno,
                            ))
            except (SyntaxError, UnicodeDecodeError):
                continue

        return gaps

    def _detect_todos(self, scanner: CodebaseScanner,
                       result: ScanResult) -> List[Gap]:
        """Detect TODO/FIXME/HACK comments in the codebase."""
        gaps = []
        todo_pattern = re.compile(r'(TODO|FIXME|HACK|XXX|BUG|OPTIMIZE)\s*[:-]?\s*(.*)', re.IGNORECASE)

        for mod_name, mod_info in result.modules.items():
            if not mod_info.filepath:
                continue
            try:
                source = Path(mod_info.filepath).read_text(encoding="utf-8")
                for i, line in enumerate(source.split("\n"), 1):
                    match = todo_pattern.search(line)
                    if match:
                        tag = match.group(1).upper()
                        comment = match.group(2).strip()
                        gaps.append(Gap(
                            gap_id=f"todo_{mod_name}_{i}",
                            category="todo_resolved",
                            module=mod_name,
                            description=f"{tag}: {comment[:100]}",
                            severity="info",
                            effort="medium",
                            impact="low",
                            suggestion=f"Resolve {tag} at {mod_info.filepath}:{i}: {comment}",
                            auto_fixable=False,
                            filepath=mod_info.filepath,
                            line_number=i,
                            metadata={"tag": tag, "comment": comment},
                        ))
            except (UnicodeDecodeError, OSError):
                continue

        return gaps

    def _detect_knowledge_issues(self, knowledge: SelfKnowledge) -> List[Gap]:
        """Detect issues already recorded in SelfKnowledge."""
        gaps = []
        issues = knowledge.get_issues(status="open")
        for issue in issues:
            gaps.append(Gap(
                gap_id=f"knowledge_issue_{issue.issue_id}",
                category="knowledge_issue",
                module=getattr(issue, "module", "unknown") or "unknown",
                description=getattr(issue, "description", str(issue)),
                severity=getattr(issue, "severity", "info"),
                effort="medium",
                impact="medium",
                suggestion=getattr(issue, "suggestion", "Review and resolve this issue"),
                auto_fixable=getattr(issue, "auto_fixable", False),
                filepath=getattr(issue, "filepath", getattr(issue, "module", None)),
                line_number=getattr(issue, "line_number", getattr(issue, "lineno", 0)),
                metadata={"issue_id": getattr(issue, "issue_id", "unknown"), "issue_type": getattr(issue, "issue_type", "unknown")},
            ))
        return gaps

    def _detect_missing_init_exports(self, scanner: CodebaseScanner,
                                      result: ScanResult) -> List[Gap]:
        """Detect subpackages whose __init__.py doesn't export all public classes/functions.

        This goes beyond the basic _detect_missing_exports check by verifying
        that every public class/function defined in a subpackage's modules is
        actually re-exported from the package's __init__.py.
        """
        gaps = []
        # Map of package -> set of public names that should be exported
        package_public_names: Dict[str, Set[str]] = {}

        for mod_name, mod_info in result.modules.items():
            if not mod_info.filepath:
                continue
            # Skip __init__ modules themselves
            if mod_name.endswith(".__init__"):
                continue
            # Determine the package this module belongs to
            pkg = ".".join(mod_name.split(".")[:-1]) if "." in mod_name else ""
            if not pkg:
                continue

            try:
                source = Path(mod_info.filepath).read_text(encoding="utf-8")
                tree = ast.parse(source)
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not node.name.startswith("_"):
                            package_public_names.setdefault(pkg, set()).add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        if not node.name.startswith("_"):
                            package_public_names.setdefault(pkg, set()).add(node.name)
            except (SyntaxError, UnicodeDecodeError):
                continue

        # Now check each package's __init__.py for re-exports
        for pkg, expected_names in package_public_names.items():
            init_path = _PROJECT_ROOT / pkg.replace(".", "/") / "__init__.py"
            if not init_path.exists():
                continue

            try:
                source = init_path.read_text(encoding="utf-8")
                tree = ast.parse(source)

                # Collect all names actually exported from __init__.py
                exported: Set[str] = set()
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if not node.name.startswith("_"):
                            exported.add(node.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.names:
                            for alias in node.names:
                                if alias.name != "*":
                                    exported.add(alias.asname or alias.name)
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "__all__":
                                if isinstance(node.value, (ast.List, ast.Tuple)):
                                    for elt in node.value.elts:
                                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                            exported.add(elt.value)

                # Find missing exports
                missing = expected_names - exported
                if missing:
                    gaps.append(Gap(
                        gap_id=f"missing_export_{pkg}",
                        category="missing_exports",
                        module=pkg,
                        description=f"Package '{pkg}' is missing exports for: {', '.join(sorted(missing))}",
                        severity="medium",
                        effort="small",
                        impact="high",
                        suggestion=f"Add re-exports for {', '.join(sorted(missing))} in {pkg}/__init__.py",
                        auto_fixable=True,
                        filepath=str(init_path),
                        metadata={"missing_exports": sorted(missing)},
                    ))
            except (SyntaxError, UnicodeDecodeError):
                continue

        return gaps

    def _detect_missing_api_routes(self, scanner: CodebaseScanner,
                                    result: ScanResult) -> List[Gap]:
        """Detect core subsystems that have no corresponding REST API routes.

        Checks if major subsystems (mirror, dreaming, evolution, universe, etc.)
        have route modules registered in routes/__init__.py.
        """
        # Known subsystems that should have API routes
        SUBSYSTEM_ROUTES = {
            "mirror": "routes/mirror.py",
            "dreaming": "routes/dreaming.py",
            "evolution": "routes/evolution.py",
            "universe": "routes/universe.py",
            "self_awareness": "routes/self_awareness.py",
            "soul_key": "routes/soul_key.py",
            "mcp": "routes/mcp.py",
            "mesh": "routes/mesh.py",
            "security": "routes/security.py",
            "identity": "routes/identity.py",
            "governance": "routes/governance.py",
            "government": "routes/government.py",
            "nepal": "routes/nepal.py",
            "finance": "routes/finance.py",
            "consensus": "routes/consensus.py",
            "depin": "routes/depin.py",
            "healing": "routes/healing.py",
            "infrastructure": "routes/infrastructure.py",
            "deploy": "routes/deploy.py",
            "clones": "routes/clones.py",
            "offline": "routes/offline.py",
            "override": "routes/override.py",
            "blockchain_identity": "routes/blockchain_identity.py",
            "jobs": "routes/jobs.py",
            "pwa": "routes/pwa.py",
            "release": "routes/release.py",
            "stakeholder": "routes/stakeholder.py",
            "arvr": "routes/arvr.py",
            "bugs": "routes/bugs.py",
            "push": "routes/push.py",
            "registry": "routes/registry.py",
            "observability": "routes/observability.py",
            "learning": "routes/learning.py",
            "enterprise": "routes/enterprise.py",
            "sovereignty": "routes/sovereignty.py",
            "universal": "routes/universal.py",
            "memory": "routes/memory.py",
            "analytics": "routes/analytics.py",
            "os_control": "routes/os_control.py",
            "router": "routes/router.py",
            "health": "routes/health.py",
            "rbe": "routes/rbe.py",
            "chat": "routes/chat.py",
            "auth": "routes/auth.py",
            "marketplace": "routes/marketplace.py",
        }

        gaps = []
        routes_dir = _PROJECT_ROOT / "routes"
        if not routes_dir.exists():
            return gaps

        existing_route_files = set()
        for f in routes_dir.iterdir():
            if f.suffix == ".py" and f.name != "__init__.py":
                existing_route_files.add(f.name)

        # Check which subsystems are missing route files
        for subsystem, expected_path in SUBSYSTEM_ROUTES.items():
            expected_file = Path(expected_path).name
            if expected_file not in existing_route_files:
                # Check if the core module exists
                core_module = _PROJECT_ROOT / "core" / subsystem
                if core_module.exists() and core_module.is_dir():
                    gaps.append(Gap(
                        gap_id=f"missing_route_{subsystem}",
                        category="missing_api_routes",
                        module=f"core.{subsystem}",
                        description=f"Subsystem 'core.{subsystem}' has no REST API route module",
                        severity="high",
                        effort="medium",
                        impact="high",
                        suggestion=f"Create routes/{expected_file} with API endpoints for core.{subsystem}",
                        auto_fixable=True,
                        filepath=str(routes_dir / expected_file),
                        metadata={"subsystem": subsystem, "expected_route_file": expected_file},
                    ))

        return gaps

    def _detect_missing_frontend_components(self, scanner: CodebaseScanner,
                                             result: ScanResult) -> List[Gap]:
        """Detect backend subsystems that have no corresponding frontend component.

        Checks if major backend subsystems have a matching React component
        in the frontend/src/components directory.
        """
        # Map of backend subsystem -> expected frontend component directory
        SUBSYSTEM_FRONTEND = {
            "mirror": "mirror",
            "self_awareness": "self-awareness",
            "soul_key": "soul-key",
            "mcp": "marketplace",  # MCP panel is in marketplace
            "mesh": "mesh",
            "identity": "identity",
            "governance": "governance",
            "government": "governance",  # Government dashboard is in governance
            "nepal": "nepal",
            "finance": "marketplace",  # Economy dashboard is in marketplace
            "consensus": "consensus",
            "depin": "mesh",  # DePIN is mesh-related
            "healing": "memory",  # Healing is memory-related
            "infrastructure": "mesh",  # Infrastructure is mesh-related
            "deploy": "os",  # Deployment is OS-related
            "clones": "clones",
            "offline": "mesh",  # Offline is mesh-related
            "blockchain_identity": "identity",
            "jobs": "agent",  # Jobs are agent-related
            "arvr": "arvr",
            "enterprise": "enterprise",
            "sovereignty": "os",  # Sovereignty is OS-related
            "universal": "chat",  # Universal chat
            "memory": "memory",
            "analytics": "marketplace",  # Analytics is marketplace-related
            "os_control": "os",
            "chat": "chat",
            "auth": "layout",  # Auth page is in layout
            "marketplace": "marketplace",
            "life_journey": "life",
            "agent": "agent",
            "odysseus": "odysseus",
            "teams": "teams",
        }

        gaps = []
        frontend_components_dir = _PROJECT_ROOT / "frontend" / "src" / "components"
        if not frontend_components_dir.exists():
            return gaps

        existing_component_dirs = set()
        for d in frontend_components_dir.iterdir():
            if d.is_dir():
                existing_component_dirs.add(d.name)

        for subsystem, expected_dir in SUBSYSTEM_FRONTEND.items():
            if expected_dir not in existing_component_dirs:
                # Check if the core module exists
                core_module = _PROJECT_ROOT / "core" / subsystem
                if core_module.exists() and core_module.is_dir():
                    gaps.append(Gap(
                        gap_id=f"missing_frontend_{subsystem}",
                        category="missing_frontend_components",
                        module=f"core.{subsystem}",
                        description=f"Subsystem 'core.{subsystem}' has no frontend component directory 'frontend/src/components/{expected_dir}'",
                        severity="medium",
                        effort="large",
                        impact="medium",
                        suggestion=f"Create frontend/src/components/{expected_dir} with React components for core.{subsystem}",
                        auto_fixable=True,
                        filepath=str(frontend_components_dir / expected_dir),
                        metadata={"subsystem": subsystem, "expected_component_dir": expected_dir},
                    ))

        return gaps

    # ── Helpers ──────────────────────────────────────────────────────────

    def _gap_to_build_action(self, gap: Gap) -> Optional[Dict[str, Any]]:
        """Convert a Gap into a build action dict for SelfBuilder."""
        if gap.category == "test_coverage":
            return {
                "action_type": "generate_test",
                "module": gap.module,
                "filepath": gap.filepath,
                "description": gap.suggestion,
            }
        elif gap.category == "missing_exports" and gap.auto_fixable:
            return {
                "action_type": "create_init",
                "module": gap.module,
                "filepath": gap.filepath,
                "description": gap.suggestion,
            }
        elif gap.category == "missing_docstrings" and gap.auto_fixable:
            return {
                "action_type": "add_docstring",
                "module": gap.module,
                "filepath": gap.filepath,
                "line_number": gap.line_number,
                "description": gap.suggestion,
            }
        elif gap.category == "bare_except" and gap.auto_fixable:
            return {
                "action_type": "fix_bare_except",
                "module": gap.module,
                "filepath": gap.filepath,
                "line_number": gap.line_number,
                "description": gap.suggestion,
            }
        return None
