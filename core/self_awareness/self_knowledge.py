"""
AsimNexus Self-Knowledge
========================
Persistent knowledge base that stores and queries structured information about
the AsimNexus codebase — module registry, dependency graph, route index,
issue tracker, and evolution history.

This is the "brain" of the self-awareness system — it remembers what AsimNexus knows.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .codebase_scanner import (
    CodebaseScanner,
    ModuleInfo,
    PackageInfo,
    RouteInfo,
    ScanResult,
    scan_codebase,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────

DEFAULT_STORAGE_DIR = os.path.join(os.getcwd(), "data", "self_awareness")
SCAN_CACHE_FILE = "scan_cache.json"
KNOWLEDGE_FILE = "knowledge.json"
ISSUES_FILE = "issues.jsonl"


# ──────────────────────────────────────────────
#  Data models
# ──────────────────────────────────────────────


@dataclass
class KnowledgeEntry:
    """A single piece of knowledge about the codebase."""

    key: str
    value: Any
    source: str  # e.g. "scan", "manual", "evolution", "inference"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IssueRecord:
    """A recorded issue (bug, warning, improvement opportunity)."""

    issue_id: str
    module: str
    issue_type: str  # "bug", "warning", "improvement", "todo", "bare_except"
    description: str
    lineno: int = 0
    severity: str = "info"  # "info", "warning", "error", "critical"
    status: str = "open"  # "open", "acknowledged", "fixed", "wontfix"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeSummary:
    """Summary statistics about the codebase knowledge."""

    total_modules: int = 0
    total_packages: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_routes: int = 0
    total_lines: int = 0
    total_issues: int = 0
    open_issues: int = 0
    last_scan: Optional[str] = None
    last_updated: Optional[str] = None


# ──────────────────────────────────────────────
#  SelfKnowledge
# ──────────────────────────────────────────────


class SelfKnowledge:
    """
    Persistent knowledge base for AsimNexus self-awareness.

    Stores:
      - Module registry (all scanned modules with metadata)
      - Dependency graph (who imports whom)
      - Route index (all API routes)
      - Issue tracker (bugs, warnings, improvement opportunities)
      - Evolution history (past changes and their impact)

    Thread-safe for concurrent access.
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        self._lock = threading.RLock()

        # In-memory stores
        self._modules: Dict[str, ModuleInfo] = {}
        self._packages: Dict[str, PackageInfo] = {}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._route_index: Dict[str, List[RouteInfo]] = defaultdict(list)
        self._knowledge: Dict[str, KnowledgeEntry] = {}
        self._issues: List[IssueRecord] = []
        self._last_scan: Optional[str] = None
        self._last_updated: Optional[str] = None

        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)

        # Load persisted state
        self._load()

    # ── Public API ──────────────────────────────

    def refresh(self, scanner: Optional[CodebaseScanner] = None) -> ScanResult:
        """
        Run a fresh scan and update all knowledge stores.

        Args:
            scanner: Optional pre-configured scanner. If None, uses default.

        Returns:
            The ScanResult from the scan.
        """
        logger.info("Refreshing self-knowledge from codebase scan...")
        result = (scanner or CodebaseScanner()).scan()

        with self._lock:
            # Update module registry
            self._modules = dict(result.modules)
            self._packages = dict(result.packages)

            # Update dependency graph
            self._dependency_graph = defaultdict(set, result.dependency_graph)
            self._reverse_dependency_graph = defaultdict(set, result.reverse_dependency_graph)

            # Update route index
            self._route_index = defaultdict(list, result.route_index)

            # Record scan timestamp
            now = datetime.now(timezone.utc).isoformat()
            self._last_scan = now
            self._last_updated = now

            # Auto-detect issues from scan patterns
            self._detect_issues_from_scan(result)

            # Persist
            self._save()

        logger.info(
            "Knowledge refreshed: %d modules, %d packages, %d routes, %d issues",
            len(self._modules),
            len(self._packages),
            sum(len(v) for v in self._route_index.values()),
            len(self._issues),
        )
        return result

    def get_module(self, package: str) -> Optional[ModuleInfo]:
        """Get module info by dotted package path."""
        with self._lock:
            return self._modules.get(package)

    def get_all_modules(self) -> Dict[str, ModuleInfo]:
        """Get all registered modules."""
        with self._lock:
            return dict(self._modules)

    def get_package(self, package: str) -> Optional[PackageInfo]:
        """Get package info by dotted path."""
        with self._lock:
            return self._packages.get(package)

    def get_all_packages(self) -> Dict[str, PackageInfo]:
        """Get all registered packages."""
        with self._lock:
            return dict(self._packages)

    def get_dependencies(self, package: str) -> Set[str]:
        """Get modules that a given module depends on."""
        with self._lock:
            return set(self._dependency_graph.get(package, set()))

    def get_dependents(self, package: str) -> Set[str]:
        """Get modules that depend on a given module."""
        with self._lock:
            return set(self._reverse_dependency_graph.get(package, set()))

    def get_routes(self, method: Optional[str] = None, path_pattern: Optional[str] = None) -> Dict[str, List[RouteInfo]]:
        """Get all routes, optionally filtered by method and/or path pattern."""
        import re
        with self._lock:
            if method and path_pattern:
                regex = re.compile(path_pattern)
                return {
                    k: [r for r in v if regex.search(r.path)]
                    for k, v in self._route_index.items()
                    if k.startswith(method.upper())
                }
            elif method:
                return {k: v for k, v in self._route_index.items() if k.startswith(method.upper())}
            elif path_pattern:
                regex = re.compile(path_pattern)
                return {k: [r for r in v if regex.search(r.path)] for k, v in self._route_index.items()}
            return dict(self._route_index)

    def get_all_routes_flat(self) -> List[RouteInfo]:
        """Get all routes as a flat list."""
        with self._lock:
            result = []
            for routes in self._route_index.values():
                result.extend(routes)
            return result

    def get_route_count(self) -> int:
        """Get total number of registered routes."""
        with self._lock:
            return sum(len(v) for v in self._route_index.values())

    # ── Knowledge store ────────────────────────

    def store_knowledge(self, key: str, value: Any, source: str = "manual", metadata: Optional[Dict] = None) -> None:
        """Store an arbitrary piece of knowledge."""
        with self._lock:
            self._knowledge[key] = KnowledgeEntry(
                key=key,
                value=value,
                source=source,
                metadata=metadata or {},
            )
            self._last_updated = datetime.now(timezone.utc).isoformat()
            self._save()

    def get_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve a piece of knowledge by key."""
        with self._lock:
            entry = self._knowledge.get(key)
            return entry.value if entry else None

    def get_all_knowledge(self) -> Dict[str, KnowledgeEntry]:
        """Get all stored knowledge entries."""
        with self._lock:
            return dict(self._knowledge)

    def search_knowledge(self, query: str) -> List[KnowledgeEntry]:
        """Search knowledge entries by key or value (simple substring match)."""
        query_lower = query.lower()
        with self._lock:
            return [
                entry for entry in self._knowledge.values()
                if query_lower in entry.key.lower() or query_lower in str(entry.value).lower()
            ]

    # ── Issue tracking ─────────────────────────

    def add_issue(self, issue: IssueRecord) -> None:
        """Add an issue record."""
        with self._lock:
            self._issues.append(issue)
            self._last_updated = datetime.now(timezone.utc).isoformat()
            self._save_issues()

    def add_issues(self, issues: List[IssueRecord]) -> None:
        """Add multiple issue records."""
        with self._lock:
            self._issues.extend(issues)
            self._last_updated = datetime.now(timezone.utc).isoformat()
            self._save_issues()

    def get_issues(self, module: Optional[str] = None, status: Optional[str] = None,
                   issue_type: Optional[str] = None) -> List[IssueRecord]:
        """Get issues, optionally filtered."""
        with self._lock:
            results = list(self._issues)
            if module:
                results = [i for i in results if i.module == module]
            if status:
                results = [i for i in results if i.status == status]
            if issue_type:
                results = [i for i in results if i.issue_type == issue_type]
            return results

    def get_open_issues(self) -> List[IssueRecord]:
        """Get all open issues."""
        return self.get_issues(status="open")

    def acknowledge_issue(self, issue_id: str) -> bool:
        """Mark an issue as acknowledged."""
        return self._update_issue_status(issue_id, "acknowledged")

    def resolve_issue(self, issue_id: str) -> bool:
        """Mark an issue as fixed."""
        return self._update_issue_status(issue_id, "fixed")

    def close_issue(self, issue_id: str, status: str = "wontfix") -> bool:
        """Close an issue without fixing."""
        return self._update_issue_status(issue_id, status)

    def get_issue_count(self, status: Optional[str] = None) -> int:
        """Get count of issues, optionally by status."""
        with self._lock:
            if status:
                return sum(1 for i in self._issues if i.status == status)
            return len(self._issues)

    # ── Summary ────────────────────────────────

    def get_summary(self) -> KnowledgeSummary:
        """Get a summary of the current knowledge state."""
        with self._lock:
            return KnowledgeSummary(
                total_modules=len(self._modules),
                total_packages=len(self._packages),
                total_classes=sum(len(m.classes) for m in self._modules.values()),
                total_functions=sum(len(m.functions) for m in self._modules.values()),
                total_routes=self.get_route_count(),
                total_lines=sum(m.lineno_count for m in self._modules.values()),
                total_issues=len(self._issues),
                open_issues=sum(1 for i in self._issues if i.status == "open"),
                last_scan=self._last_scan,
                last_updated=self._last_updated,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire knowledge base to a dictionary."""
        with self._lock:
            return {
                "modules": {p: self._module_to_dict(m) for p, m in self._modules.items()},
                "packages": {p: asdict(pkg) for p, pkg in self._packages.items()},
                "dependency_graph": {k: list(v) for k, v in self._dependency_graph.items()},
                "reverse_dependency_graph": {k: list(v) for k, v in self._reverse_dependency_graph.items()},
                "route_index": {
                    k: [
                        asdict(r) if hasattr(r, '__dataclass_fields__') else r
                        for r in v
                    ]
                    for k, v in self._route_index.items()
                },
                "knowledge": {k: asdict(v) for k, v in self._knowledge.items()},
                "issues": [asdict(i) for i in self._issues],
                "last_scan": self._last_scan,
                "last_updated": self._last_updated,
            }

    # ── Internal ───────────────────────────────

    def _detect_issues_from_scan(self, result: ScanResult) -> None:
        """Auto-detect issues from scan patterns."""
        new_issues: List[IssueRecord] = []
        issue_counter = len(self._issues) + 1

        # Bare excepts
        for package, lines in result.bare_excepts.items():
            for lineno in lines:
                new_issues.append(IssueRecord(
                    issue_id=f"BE-{issue_counter}",
                    module=package,
                    issue_type="bare_except",
                    description=f"Bare except clause at line {lineno}",
                    lineno=lineno,
                    severity="warning",
                ))
                issue_counter += 1

        # TODOs
        for package, lines in result.todos.items():
            for lineno in lines:
                new_issues.append(IssueRecord(
                    issue_id=f"TODO-{issue_counter}",
                    module=package,
                    issue_type="todo",
                    description=f"TODO at line {lineno}",
                    lineno=lineno,
                    severity="info",
                ))
                issue_counter += 1

        # FIXMEs
        for package, lines in result.fixmes.items():
            for lineno in lines:
                new_issues.append(IssueRecord(
                    issue_id=f"FIXME-{issue_counter}",
                    module=package,
                    issue_type="bug",
                    description=f"FIXME at line {lineno}",
                    lineno=lineno,
                    severity="warning",
                ))
                issue_counter += 1

        # HACKs
        for package, lines in result.hacks.items():
            for lineno in lines:
                new_issues.append(IssueRecord(
                    issue_id=f"HACK-{issue_counter}",
                    module=package,
                    issue_type="improvement",
                    description=f"HACK at line {lineno}",
                    lineno=lineno,
                    severity="info",
                ))
                issue_counter += 1

        # Modules with parse errors
        for package, mod in result.modules.items():
            if mod.errors:
                for err in mod.errors:
                    new_issues.append(IssueRecord(
                        issue_id=f"ERR-{issue_counter}",
                        module=package,
                        issue_type="bug",
                        description=f"Parse error: {err}",
                        severity="error",
                    ))
                    issue_counter += 1

        # Modules without test files
        for package, mod in result.modules.items():
            if "test" in package.lower():
                continue
            if not mod.has_test_file and not package.endswith(".__init__"):
                new_issues.append(IssueRecord(
                    issue_id=f"NOTEST-{issue_counter}",
                    module=package,
                    issue_type="improvement",
                    description=f"No test file found for {package}",
                    severity="info",
                ))
                issue_counter += 1

        self._issues.extend(new_issues)

    def _update_issue_status(self, issue_id: str, new_status: str) -> bool:
        """Update the status of an issue by ID."""
        with self._lock:
            for issue in self._issues:
                if issue.issue_id == issue_id:
                    issue.status = new_status
                    self._last_updated = datetime.now(timezone.utc).isoformat()
                    self._save_issues()
                    return True
            return False

    @staticmethod
    def _module_to_dict(mod: ModuleInfo) -> Dict[str, Any]:
        """Serialize a ModuleInfo to a dict (avoiding circular refs)."""
        return {
            "filepath": mod.filepath,
            "package": mod.package,
            "docstring": mod.docstring,
            "lineno_count": mod.lineno_count,
            "classes": [asdict(c) for c in mod.classes],
            "functions": [asdict(f) for f in mod.functions],
            "imports": [asdict(i) for i in mod.imports],
            "routes": [asdict(r) for r in mod.routes],
            "errors": mod.errors,
            "has_test_file": mod.has_test_file,
            "test_filepath": mod.test_filepath,
        }

    # ── Persistence ────────────────────────────

    def _save(self) -> None:
        """Persist all knowledge to disk."""
        try:
            data = self.to_dict()
            filepath = os.path.join(self.storage_dir, KNOWLEDGE_FILE)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, PermissionError) as e:
            logger.error("Failed to persist knowledge: %s", e)

    def _save_issues(self) -> None:
        """Append issues to the JSONL issues file."""
        try:
            filepath = os.path.join(self.storage_dir, ISSUES_FILE)
            with open(filepath, "a", encoding="utf-8") as f:
                for issue in self._issues[-10:]:  # Save last 10 as JSONL
                    f.write(json.dumps(asdict(issue), default=str) + "\n")
        except (OSError, PermissionError) as e:
            logger.error("Failed to persist issues: %s", e)

    def _load(self) -> None:
        """Load persisted knowledge from disk."""
        # Load knowledge file
        filepath = os.path.join(self.storage_dir, KNOWLEDGE_FILE)
        if os.path.exists(filepath):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                self._modules = {
                    p: self._dict_to_module(m) for p, m in data.get("modules", {}).items()
                }
                self._packages = {
                    p: PackageInfo(**pkg) for p, pkg in data.get("packages", {}).items()
                }
                self._dependency_graph = defaultdict(
                    set, {k: set(v) for k, v in data.get("dependency_graph", {}).items()}
                )
                self._reverse_dependency_graph = defaultdict(
                    set, {k: set(v) for k, v in data.get("reverse_dependency_graph", {}).items()}
                )
                self._route_index = defaultdict(list, data.get("route_index", {}))
                self._knowledge = {
                    k: KnowledgeEntry(**v) for k, v in data.get("knowledge", {}).items()
                }
                self._last_scan = data.get("last_scan")
                self._last_updated = data.get("last_updated")
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("Failed to load knowledge file (will start fresh): %s", e)

        # Load issues from JSONL
        issues_file = os.path.join(self.storage_dir, ISSUES_FILE)
        if os.path.exists(issues_file):
            try:
                with open(issues_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                self._issues.append(IssueRecord(**json.loads(line)))
                            except (json.JSONDecodeError, KeyError):
                                pass
            except (OSError, PermissionError) as e:
                logger.warning("Failed to load issues file: %s", e)

    @staticmethod
    def _dict_to_module(data: Dict[str, Any]) -> ModuleInfo:
        """Deserialize a dict back to ModuleInfo."""
        from .codebase_scanner import ClassInfo, FunctionInfo, ImportInfo, RouteInfo
        mod = ModuleInfo(
            filepath=data.get("filepath", ""),
            package=data.get("package", ""),
            docstring=data.get("docstring"),
            lineno_count=data.get("lineno_count", 0),
            classes=[ClassInfo(**c) for c in data.get("classes", [])],
            functions=[FunctionInfo(**f) for f in data.get("functions", [])],
            imports=[ImportInfo(**i) for i in data.get("imports", [])],
            routes=[RouteInfo(**r) for r in data.get("routes", [])],
            errors=data.get("errors", []),
            has_test_file=data.get("has_test_file", False),
            test_filepath=data.get("test_filepath"),
        )
        return mod


# ── Convenience ────────────────────────────────

_default_knowledge: Optional[SelfKnowledge] = None


def get_knowledge() -> SelfKnowledge:
    """Get or create the default SelfKnowledge singleton."""
    global _default_knowledge
    if _default_knowledge is None:
        _default_knowledge = SelfKnowledge()
    return _default_knowledge


def refresh_knowledge() -> ScanResult:
    """Convenience: refresh knowledge from a fresh scan."""
    return get_knowledge().refresh()
