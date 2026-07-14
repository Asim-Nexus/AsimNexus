"""
AsimNexus Codebase Scanner
==========================
AST-based scanner that walks the entire project tree, parses every Python file,
and builds a structured knowledge graph of modules, classes, functions, routes,
dependencies, and patterns.

This is the "eyes" of the self-awareness system — it tells AsimNexus what it is.
"""

from __future__ import annotations

import ast
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Data models
# ──────────────────────────────────────────────


@dataclass
class FunctionInfo:
    """Metadata about a function or method."""

    name: str
    lineno: int
    end_lineno: int
    is_async: bool
    is_method: bool
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    args: List[str] = field(default_factory=list)
    return_annotation: Optional[str] = None


@dataclass
class ClassInfo:
    """Metadata about a class."""

    name: str
    lineno: int
    end_lineno: int
    bases: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """A single import statement."""

    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    lineno: int = 0


@dataclass
class RouteInfo:
    """A FastAPI route handler."""

    path: str
    method: str  # GET, POST, PUT, DELETE, etc.
    func_name: str
    lineno: int
    summary: Optional[str] = None


@dataclass
class ModuleInfo:
    """Full metadata for a single Python module."""

    filepath: str
    package: str  # dotted module path, e.g. "core.security.auth_middleware"
    docstring: Optional[str] = None
    lineno_count: int = 0
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    routes: List[RouteInfo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    has_test_file: bool = False
    test_filepath: Optional[str] = None


@dataclass
class PackageInfo:
    """Metadata about a package (directory with __init__.py)."""

    path: str
    package: str
    submodules: List[str] = field(default_factory=list)
    subpackages: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class ScanResult:
    """Result of a full codebase scan."""

    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    packages: Dict[str, PackageInfo] = field(default_factory=dict)
    total_files: int = 0
    total_lines: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_routes: int = 0
    errors: List[str] = field(default_factory=list)

    # Dependency graph
    dependency_graph: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse_dependency_graph: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    # Route index
    route_index: Dict[str, List[RouteInfo]] = field(default_factory=lambda: defaultdict(list))

    # Pattern registry
    bare_excepts: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
    todos: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
    fixmes: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))
    hacks: Dict[str, List[int]] = field(default_factory=lambda: defaultdict(list))


# ──────────────────────────────────────────────
#  AST Visitors
# ──────────────────────────────────────────────


class _ModuleVisitor(ast.NodeVisitor):
    """Walks a single module's AST and extracts metadata."""

    def __init__(self, source: str, filepath: str) -> None:
        self.source = source
        self.filepath = filepath
        self.lines = source.splitlines()
        self.info = ModuleInfo(filepath=filepath, package="")
        self.info.lineno_count = len(self.lines)
        self._current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(self._format_attr(b))
            elif isinstance(b, ast.Subscript):
                bases.append(self._format_node(b))
        decorators = [self._format_decorator(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node)
        cls = ClassInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            bases=bases,
            decorators=decorators,
            docstring=docstring,
        )
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class
        self.info.classes.append(cls)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._add_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._add_function(node, is_async=True)

    def _add_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        decorators = [self._format_decorator(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node)
        args = [a.arg for a in node.args.args]
        return_ann = None
        if node.returns:
            return_ann = self._format_node(node.returns)
        func = FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=node.end_lineno or node.lineno,
            is_async=is_async,
            is_method=self._current_class is not None,
            decorators=decorators,
            docstring=docstring,
            args=args,
            return_annotation=return_ann,
        )
        if self._current_class:
            # Find the class and add method
            for cls in self.info.classes:
                if cls.name == self._current_class:
                    cls.methods.append(func)
                    break
        else:
            self.info.functions.append(func)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.info.imports.append(
                ImportInfo(
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    alias=alias.asname,
                    lineno=node.lineno,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        names = [a.name for a in node.names]
        self.info.imports.append(
            ImportInfo(
                module=module,
                names=names,
                lineno=node.lineno,
            )
        )

    def _format_decorator(self, d: ast.expr) -> str:
        if isinstance(d, ast.Name):
            return d.id
        elif isinstance(d, ast.Attribute):
            return self._format_attr(d)
        elif isinstance(d, ast.Call):
            if isinstance(d.func, ast.Name):
                return f"{d.func.id}(...)"
            elif isinstance(d.func, ast.Attribute):
                return f"{self._format_attr(d.func)}(...)"
        return ast.dump(d)

    def _format_attr(self, node: ast.Attribute) -> str:
        parts = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _format_node(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._format_attr(node)
        elif isinstance(node, ast.Subscript):
            value = self._format_node(node.value)
            if isinstance(node.slice, ast.Name):
                return f"{value}[{node.slice.id}]"
            return f"{value}[...]"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        return ast.dump(node)


class _RouteDetector(ast.NodeVisitor):
    """Detects FastAPI route decorators and extracts route info."""

    ROUTE_METHODS = {"get", "post", "put", "delete", "patch", "options", "head", "trace", "websocket"}

    def __init__(self, source: str, filepath: str) -> None:
        self.source = source
        self.filepath = filepath
        self.lines = source.splitlines()
        self.routes: List[RouteInfo] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_routes(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_routes(node)

    def _check_routes(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            route = self._parse_route_decorator(decorator, node)
            if route:
                self.routes.append(route)

    def _parse_route_decorator(self, decorator: ast.expr, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Optional[RouteInfo]:
        """Parse a decorator like @router.get('/path') or @app.post('/path')."""
        if not isinstance(decorator, ast.Call):
            return None
        if not isinstance(decorator.func, ast.Attribute):
            return None

        method = decorator.func.attr.lower()
        if method not in self.ROUTE_METHODS:
            return None

        # Extract path from first positional arg
        path = ""
        if decorator.args:
            if isinstance(decorator.args[0], ast.Constant):
                path = decorator.args[0].value
            elif isinstance(decorator.args[0], ast.Str):  # Python 3.7 compat
                path = decorator.args[0].s

        # Extract summary from docstring
        summary = ast.get_docstring(node)

        return RouteInfo(
            path=path,
            method=method.upper(),
            func_name=node.name,
            lineno=node.lineno,
            summary=summary,
        )


class _PatternDetector:
    """Detects code patterns like bare excepts, TODOs, FIXMEs, HACKs."""

    TODO_RE = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|BUG|OPTIMIZE)\b", re.IGNORECASE)
    BARE_EXCEPT_RE = re.compile(r"^\s*except\s*:")

    @classmethod
    def scan(cls, source: str, filepath: str) -> Dict[str, List[int]]:
        result: Dict[str, List[int]] = {"todos": [], "fixmes": [], "hacks": [], "bare_excepts": []}
        lines = source.splitlines()
        for i, line in enumerate(lines, start=1):
            m = cls.TODO_RE.search(line)
            if m:
                tag = m.group(1).lower()
                if tag == "todo":
                    result["todos"].append(i)
                elif tag == "fixme":
                    result["fixmes"].append(i)
                elif tag == "hack":
                    result["hacks"].append(i)
            if cls.BARE_EXCEPT_RE.match(line):
                result["bare_excepts"].append(i)
        return result


# ──────────────────────────────────────────────
#  Scanner
# ──────────────────────────────────────────────


class CodebaseScanner:
    """
    Scans the entire AsimNexus codebase and builds a structured knowledge graph.

    Usage:
        scanner = CodebaseScanner()
        result = scanner.scan()  # Full scan
        # or
        result = scanner.scan(["core", "routes"])  # Scan specific dirs
    """

    # Directories to always skip
    SKIP_DIRS = {
        "__pycache__",
        ".git",
        ".github",
        ".kilo",
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "dist",
        "build",
        ".next",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "backups",
        "worktree_sandbox",
    }

    # File extensions to scan
    SCAN_EXTENSIONS = {".py"}

    def __init__(self, root_dir: Optional[str] = None) -> None:
        self.root_dir = root_dir or os.getcwd()
        self._result: Optional[ScanResult] = None

    # ── Public API ──────────────────────────────

    def scan(self, subdirs: Optional[List[str]] = None) -> ScanResult:
        """
        Run a full scan of the codebase.

        Args:
            subdirs: If provided, only scan these subdirectories relative to root.
                     If None, scan the entire root directory.
        """
        logger.info("Starting codebase scan (root=%s, subdirs=%s)", self.root_dir, subdirs)
        result = ScanResult()

        if subdirs:
            scan_paths = [os.path.join(self.root_dir, d) for d in subdirs]
        else:
            scan_paths = [self.root_dir]

        for scan_path in scan_paths:
            if not os.path.isdir(scan_path):
                logger.warning("Scan path does not exist: %s", scan_path)
                continue
            self._scan_directory(scan_path, result)

        # Build dependency graph
        self._build_dependency_graph(result)

        # Build route index
        self._build_route_index(result)

        # Match test files
        self._match_test_files(result)

        logger.info(
            "Scan complete: %d files, %d lines, %d classes, %d functions, %d routes",
            result.total_files,
            result.total_lines,
            result.total_classes,
            result.total_functions,
            result.total_routes,
        )
        self._result = result
        return result

    def get_result(self) -> Optional[ScanResult]:
        """Return the last scan result, or None if no scan has been run."""
        return self._result

    def get_module(self, package: str) -> Optional[ModuleInfo]:
        """Get module info by dotted package path."""
        if self._result is None:
            return None
        return self._result.modules.get(package)

    def find_modules_by_pattern(self, pattern: str) -> List[ModuleInfo]:
        """Find modules whose package path matches a regex pattern."""
        if self._result is None:
            return []
        regex = re.compile(pattern)
        return [m for m in self._result.modules.values() if regex.search(m.package)]

    def get_modules_with_routes(self) -> List[ModuleInfo]:
        """Get all modules that define FastAPI routes."""
        if self._result is None:
            return []
        return [m for m in self._result.modules.values() if m.routes]

    def get_modules_with_errors(self) -> List[ModuleInfo]:
        """Get all modules that had parse errors."""
        if self._result is None:
            return []
        return [m for m in self._result.modules.values() if m.errors]

    def get_dependency_chain(self, package: str, reverse: bool = False) -> Set[str]:
        """Get all modules that a given module depends on (or is depended by)."""
        if self._result is None:
            return set()
        graph = self._result.reverse_dependency_graph if reverse else self._result.dependency_graph
        return graph.get(package, set())

    def get_orphaned_modules(self) -> List[str]:
        """Find modules that nothing imports (potential dead code)."""
        if self._result is None:
            return []
        imported = set()
        for deps in self._result.dependency_graph.values():
            imported.update(deps)
        all_modules = set(self._result.modules.keys())
        # Remove __init__ files from orphan check
        orphans = all_modules - imported
        return sorted(o for o in orphans if not o.endswith(".__init__"))

    # ── Internal ───────────────────────────────

    def _scan_directory(self, dirpath: str, result: ScanResult) -> None:
        """Recursively scan a directory for Python files."""
        for root, dirs, files in os.walk(dirpath):
            # Skip unwanted directories (modify dirs in-place to prevent os.walk from descending)
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS and not d.startswith(".")]

            for file in files:
                if not any(file.endswith(ext) for ext in self.SCAN_EXTENSIONS):
                    continue
                filepath = os.path.join(root, file)
                self._scan_file(filepath, result)

    def _scan_file(self, filepath: str, result: ScanResult) -> None:
        """Parse a single Python file and extract metadata."""
        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                source = f.read()
        except (OSError, PermissionError) as e:
            result.errors.append(f"Cannot read {filepath}: {e}")
            return

        # Compute dotted package path
        relpath = os.path.relpath(filepath, self.root_dir)
        package = relpath.replace(os.sep, ".").replace("/", ".").replace("\\", ".")
        if package.endswith(".py"):
            package = package[:-3]
        # Handle __init__.py -> treat as the package itself
        if package.endswith(".__init__"):
            package = package[:-9]  # remove .__init__

        # Parse AST
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError as e:
            result.errors.append(f"Syntax error in {filepath}: {e}")
            mod = ModuleInfo(filepath=filepath, package=package, lineno_count=len(source.splitlines()))
            mod.errors.append(str(e))
            result.modules[package] = mod
            result.total_files += 1
            result.total_lines += mod.lineno_count
            return

        # Extract module docstring
        docstring = ast.get_docstring(tree)

        # Extract classes, functions, imports
        visitor = _ModuleVisitor(source, filepath)
        visitor.visit(tree)
        mod = visitor.info
        mod.package = package
        mod.docstring = docstring

        # Detect routes
        route_detector = _RouteDetector(source, filepath)
        route_detector.visit(tree)
        mod.routes = route_detector.routes

        # Detect patterns
        patterns = _PatternDetector.scan(source, filepath)
        for tag, lines in patterns.items():
            target = getattr(result, tag, None)
            if target is not None:
                target[package].extend(lines)

        # Store
        result.modules[package] = mod
        result.total_files += 1
        result.total_lines += mod.lineno_count
        result.total_classes += len(mod.classes)
        result.total_functions += len(mod.functions)
        result.total_routes += len(mod.routes)

    def _build_dependency_graph(self, result: ScanResult) -> None:
        """Build forward and reverse dependency graphs from import info."""
        for package, mod in result.modules.items():
            for imp in mod.imports:
                # Only track internal dependencies (start with known prefixes)
                dep = imp.module
                if dep.startswith("core.") or dep.startswith("routes.") or dep.startswith("mesh.") or \
                   dep.startswith("agents.") or dep.startswith("connectors.") or dep.startswith("governance.") or \
                   dep.startswith("knowledge.") or dep.startswith("security.") or dep.startswith("os_control.") or \
                   dep.startswith("database.") or dep.startswith("infrastructure.") or dep.startswith("compliance.") or \
                   dep.startswith("tests.") or dep.startswith("scripts.") or dep.startswith("monitoring.") or \
                   dep.startswith("risk_management.") or dep.startswith("ui.") or dep.startswith("models.") or \
                   dep.startswith("config.") or dep.startswith("asim_tools."):
                    result.dependency_graph[package].add(dep)
                    result.reverse_dependency_graph[dep].add(package)

    def _build_route_index(self, result: ScanResult) -> None:
        """Build an index of routes keyed by HTTP method."""
        for package, mod in result.modules.items():
            for route in mod.routes:
                key = f"{route.method} {route.path}"
                result.route_index[key].append(route)

    def _match_test_files(self, result: ScanResult) -> None:
        """Match source modules to their test files."""
        # Find all test modules
        test_modules = {p: m for p, m in result.modules.items() if "test" in p.lower()}

        for package, mod in result.modules.items():
            if "test" in package.lower():
                continue
            # Look for matching test file
            # e.g. core/security/auth_middleware.py -> tests/unit/test_auth_middleware.py
            # or tests/real/test_auth_middleware.py
            base_name = package.split(".")[-1]
            for test_pkg, test_mod in test_modules.items():
                if base_name in test_pkg:
                    mod.has_test_file = True
                    mod.test_filepath = test_mod.filepath
                    break


# ── Convenience ────────────────────────────────

_default_scanner: Optional[CodebaseScanner] = None


def get_scanner() -> CodebaseScanner:
    """Get or create the default CodebaseScanner singleton."""
    global _default_scanner
    if _default_scanner is None:
        _default_scanner = CodebaseScanner()
    return _default_scanner


def scan_codebase(subdirs: Optional[List[str]] = None) -> ScanResult:
    """Convenience: scan and return result."""
    return get_scanner().scan(subdirs)
