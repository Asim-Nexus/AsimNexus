"""
AsimNexus Self-Builder
======================
Template-based code generation, import fixing, test generation, and autonomous
code modification engine.

This is the "hands" of the self-awareness system — it lets AsimNexus build itself.

Capabilities:
  - Generate new modules from templates (route, model, test, etc.)
  - Fix missing imports in existing modules
  - Generate test stubs for untested modules
  - Add missing __init__.py exports
  - Register new routes in routes/__init__.py
  - Apply code patches from EvolutionEngine suggestions
  - Rollback applied changes
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import shutil
import tempfile
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import jinja2

from .codebase_scanner import CodebaseScanner, ModuleInfo, ScanResult
from .self_knowledge import SelfKnowledge

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
PATCHES_DIR = os.path.join(os.getcwd(), "data", "self_awareness", "patches")
BACKUP_DIR = os.path.join(os.getcwd(), "data", "self_awareness", "backups")

# Template names
TEMPLATE_ROUTE = "route.py.j2"
TEMPLATE_MODEL = "model.py.j2"
TEMPLATE_SERVICE = "service.py.j2"
TEMPLATE_TEST_UNIT = "test_unit.py.j2"
TEMPLATE_TEST_REAL = "test_real.py.j2"
TEMPLATE_TEST_INTEGRATION = "test_integration.py.j2"
TEMPLATE_API_CLIENT = "api_client.ts.j2"
TEMPLATE_REACT_COMPONENT = "react_component.tsx.j2"
TEMPLATE_INIT = "__init__.py.j2"
TEMPLATE_SCHEMA = "schema.py.j2"


# ──────────────────────────────────────────────
#  Data models
# ──────────────────────────────────────────────


@dataclass
class BuildAction:
    """A single build/modification action."""

    action_id: str
    action_type: str  # "create", "modify", "delete", "patch", "register_route"
    target_file: str
    description: str
    status: str = "pending"  # "pending", "applied", "rolled_back", "failed"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    backup_file: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildResult:
    """Result of a build operation."""

    success: bool
    actions: List[BuildAction] = field(default_factory=list)
    error: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class Template:
    """A code template with variables."""

    name: str
    content: str
    variables: Dict[str, str] = field(default_factory=dict)


# ──────────────────────────────────────────────
#  SelfBuilder
# ──────────────────────────────────────────────


class SelfBuilder:
    """
    Autonomous code builder for AsimNexus.

    Can create, modify, patch, and rollback code changes.
    All modifications are backed up and logged for safety.
    """

    def __init__(self, knowledge: Optional[SelfKnowledge] = None) -> None:
        self.knowledge = knowledge or SelfKnowledge()
        self._lock = threading.Lock()
        self._action_history: List[BuildAction] = []
        self._templates: Dict[str, Template] = {}

        # Ensure directories exist
        os.makedirs(PATCHES_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # Load built-in templates
        self._load_templates()

        # Load action history
        self._load_history()

    # ── Public API ──────────────────────────────

    def generate_route_module(self, module_name: str, routes: List[Dict[str, str]],
                              package: str = "routes") -> BuildResult:
        """
        Generate a new route module file.

        Uses the TEMPLATE_ROUTE Jinja2 template for the static boilerplate
        (docstring, imports, router creation, init function) and generates
        the dynamic route endpoints inline.

        Args:
            module_name: e.g. "health" -> routes/health.py
            routes: List of route dicts with keys: method, path, func_name, summary
            package: Target package (default: "routes")

        Returns:
            BuildResult with the creation action.
        """
        filepath = os.path.join(os.getcwd(), package, f"{module_name}.py")
        if os.path.exists(filepath):
            return BuildResult(success=False, error=f"File already exists: {filepath}")

        # Render the static boilerplate from the Jinja2 template
        header = self._render_template(
            TEMPLATE_ROUTE,
            module_name=module_name,
            base_path=f"/api/{module_name}",
        )

        # Build the dynamic route endpoints
        route_lines: List[str] = []
        for route in routes:
            method = route.get("method", "GET").lower()
            path = route.get("path", "/")
            func_name = route.get("func_name", f"{module_name}_{method}")
            summary = route.get("summary", f"{method.upper()} {path}")

            route_lines.extend([
                f'',
                f'@router.{method}("{path}")',
                f'async def {func_name}():',
                f'    """{summary}"""',
                f'    try:',
                f'        return {{"status": "ok", "endpoint": "{path}"}}',
                f'    except Exception as e:',
                f'        logger.exception("Error in {func_name}")',
                f'        raise HTTPException(status_code=500, detail=str(e))',
            ])

        # Combine: header (up to and including router = APIRouter()) + routes + init function
        # The template generates: docstring, imports, router, list/get endpoints, init function
        # We replace the template's default endpoints with our dynamic routes
        header_parts = header.split("\n\n@router.get")
        boilerplate = header_parts[0]  # Everything before the first @router.get

        content = boilerplate + "\n" + "\n".join(route_lines) + "\n\n\n" + (
            f'def init_{module_name}(app_globals: dict) -> None:\n'
            f'    """Initialize the {module_name} module."""\n'
            f'    logger.info("Initialized {module_name} routes")\n'
        )

        return self._create_file(filepath, content, action_type="create",
                                 description=f"Generated route module: {module_name}.py",
                                 metadata={"routes": routes, "module_name": module_name})

    def generate_test_file(self, source_module: str, test_type: str = "unit") -> BuildResult:
        """
        Generate a test file for a given source module.

        Args:
            source_module: Dotted package path, e.g. "core.security.auth_middleware"
            test_type: "unit" or "real"

        Returns:
            BuildResult with the creation action.
        """
        # Determine test file path
        parts = source_module.split(".")
        if test_type == "unit":
            test_dir = os.path.join(os.getcwd(), "tests", "unit")
            test_name = f"test_{parts[-1]}.py"
        else:
            test_dir = os.path.join(os.getcwd(), "tests", "real")
            test_name = f"test_{parts[-1]}.py"

        filepath = os.path.join(test_dir, test_name)
        if os.path.exists(filepath):
            return BuildResult(success=False, error=f"Test file already exists: {filepath}")

        # Get module info for context
        mod = self.knowledge.get_module(source_module)
        class_names = [c.name for c in mod.classes] if mod else []
        func_names = [f.name for f in mod.functions if not f.is_method] if mod else []

        # Render the header/imports from the unit test template
        try:
            header = self._render_template(
                TEMPLATE_TEST_UNIT,
                source_module=source_module,
                class_names=class_names[:5],
                func_names=func_names[:5],
            )
        except Exception as e:
            return BuildResult(success=False, error=f"Template rendering failed: {e}")

        lines = [header]

        # Generate test class for each class
        for cn in class_names:
            lines.extend([
                f'',
                f'class Test{cn}:',
                f'    """Tests for {cn}."""',
                f'',
                f'    def setup_method(self):',
                f'        """Set up test fixtures."""',
                f'        pass',
                f'',
                f'    @pytest.mark.asyncio',
                f'    async def test_initialization(self):',
                f'        """Test that {cn} initializes correctly."""',
                f'        instance = {cn}()',
                f'        assert instance is not None',
                f'',
            ])

        # Generate test function for each standalone function
        for fn in func_names:
            lines.extend([
                f'',
                f'@pytest.mark.asyncio',
                f'async def test_{fn}():',
                f'    """Test the {fn} function."""',
                f'    # TODO: Implement test',
                f'    pass',
            ])

        content = "\n".join(lines)

        return self._create_file(filepath, content, action_type="create",
                                 description=f"Generated {test_type} test for {source_module}",
                                 metadata={"source_module": source_module, "test_type": test_type})

    def generate_model_module(self, model_name: str,
                               fields: Optional[List[Dict[str, str]]] = None,
                               package: str = "models") -> BuildResult:
        """
        Generate a new Pydantic model module from the model template.

        Args:
            model_name: e.g. "transaction" -> models/transaction.py
            fields: List of dicts with keys "name" and "type", e.g.
                    [{"name": "amount", "type": "float"}, {"name": "category", "type": "str"}]
            package: Target package (default: "models")

        Returns:
            BuildResult with the creation action.
        """
        filepath = os.path.join(os.getcwd(), package, f"{model_name}.py")
        if os.path.exists(filepath):
            return BuildResult(success=False, error=f"File already exists: {filepath}")

        fields = fields or [{"name": "name", "type": "str"}, {"name": "value", "type": "float"}]

        # Render the module content using the TEMPLATE_MODEL Jinja2 template
        try:
            content = self._render_template(
                TEMPLATE_MODEL,
                model_name=model_name,
                fields=[(f["name"], f["type"]) for f in fields],
            )
        except Exception as e:
            return BuildResult(success=False, error=f"Template rendering failed: {e}")

        return self._create_file(filepath, content, action_type="create",
                                 description=f"Generated model module: {model_name}.py",
                                 metadata={"model_name": model_name, "fields": fields})

    def generate_service_module(self, service_name: str,
                                 package: str = "services") -> BuildResult:
        """
        Generate a new service module from the service template.

        Args:
            service_name: e.g. "payment" -> services/payment_service.py
            package: Target package (default: "services")

        Returns:
            BuildResult with the creation action.
        """
        filepath = os.path.join(os.getcwd(), package, f"{service_name}_service.py")
        if os.path.exists(filepath):
            return BuildResult(success=False, error=f"File already exists: {filepath}")

        try:
            content = self._render_template(TEMPLATE_SERVICE, service_name=service_name)
        except Exception as e:
            return BuildResult(success=False, error=f"Template rendering failed: {e}")

        return self._create_file(filepath, content, action_type="create",
                                 description=f"Generated service module: {service_name}_service.py",
                                 metadata={"service_name": service_name})

    def generate_api_client(self, service_name: str,
                             fields: Optional[List[Dict[str, str]]] = None,
                             base_path: str = "/api/v1",
                             package: str = "frontend/src/api") -> BuildResult:
        """
        Generate a TypeScript API client module.

        Args:
            service_name: e.g. "payment" -> frontend/src/api/payment.ts
            fields: List of dicts with keys "name" and "type"
            base_path: API base path, e.g. "/api/v1/payments"
            package: Target package (default: "frontend/src/api")

        Returns:
            BuildResult with the creation action.
        """
        filepath = os.path.join(os.getcwd(), package, f"{service_name}.ts")
        if os.path.exists(filepath):
            return BuildResult(success=False, error=f"File already exists: {filepath}")

        fields = fields or [{"name": "name", "type": "string"}, {"name": "value", "type": "number"}]

        try:
            content = self._render_template(
                TEMPLATE_API_CLIENT,
                service_name=service_name,
                base_path=base_path,
                fields=[(f["name"], f["type"]) for f in fields],
            )
        except Exception as e:
            return BuildResult(success=False, error=f"Template rendering failed: {e}")

        return self._create_file(filepath, content, action_type="create",
                                 description=f"Generated API client: {service_name}.ts",
                                 metadata={"service_name": service_name, "base_path": base_path})

    def generate_react_component(self, component_name: str,
                                  service_name: str,
                                  api_module: str = "api",
                                  package: str = "frontend/src/components") -> BuildResult:
        """
        Generate a React component for a service.

        Args:
            component_name: e.g. "PaymentList" -> frontend/src/components/PaymentList.tsx
            service_name: e.g. "payment" (used for API calls)
            api_module: Import path for the API module (default: "api")
            package: Target package (default: "frontend/src/components")

        Returns:
            BuildResult with the creation action.
        """
        filepath = os.path.join(os.getcwd(), package, f"{component_name}.tsx")
        if os.path.exists(filepath):
            return BuildResult(success=False, error=f"File already exists: {filepath}")

        try:
            content = self._render_template(
                TEMPLATE_REACT_COMPONENT,
                service_name=service_name,
                component_name=component_name,
                api_module=api_module,
            )
        except Exception as e:
            return BuildResult(success=False, error=f"Template rendering failed: {e}")

        return self._create_file(filepath, content, action_type="create",
                                 description=f"Generated React component: {component_name}.tsx",
                                 metadata={"component_name": component_name, "service_name": service_name})

    def fix_missing_imports(self, module_package: str) -> BuildResult:
        """
        Scan a module for missing imports and add them.

        Args:
            module_package: Dotted package path, e.g. "routes.infrastructure"

        Returns:
            BuildResult with the modification actions.
        """
        mod = self.knowledge.get_module(module_package)
        if not mod:
            return BuildResult(success=False, error=f"Module not found: {module_package}")

        filepath = mod.filepath
        if not os.path.exists(filepath):
            return BuildResult(success=False, error=f"File not found: {filepath}")

        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        # Parse the source to find undefined names
        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError as e:
            return BuildResult(success=False, error=f"Syntax error: {e}")

        # Collect all defined names in the module
        defined_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    defined_names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    defined_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.FunctionDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)

        # Find names that are used but not defined
        used_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if not isinstance(node.ctx, ast.Store):
                    used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        undefined = used_names - defined_names - {"True", "False", "None", "_"}

        # Filter to names that look like they come from known modules
        # This is a heuristic — we look for names that match known classes/functions
        known_exports: Dict[str, str] = self._build_known_exports()
        missing_imports: Dict[str, List[str]] = {}
        for name in sorted(undefined):
            if name in known_exports:
                module_path = known_exports[name]
                if module_path not in missing_imports:
                    missing_imports[module_path] = []
                missing_imports[module_path].append(name)

        if not missing_imports:
            return BuildResult(success=True, summary="No missing imports detected")

        # Generate the import block to add
        import_lines = []
        for module_path, names in sorted(missing_imports.items()):
            if module_path.startswith("core.") or module_path.startswith("routes."):
                import_lines.append(f"from {module_path} import {', '.join(sorted(names))}")

        if not import_lines:
            return BuildResult(success=True, summary="No actionable missing imports")

        # Add imports after the last existing import
        new_source = self._add_imports_after_last_import(source, import_lines)

        # Backup and write
        backup_path = self._backup_file(filepath)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_source)
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        action = BuildAction(
            action_id=f"FIXIMPORT-{len(self._action_history) + 1}",
            action_type="modify",
            target_file=filepath,
            description=f"Added {len(missing_imports)} missing import(s) to {module_package}",
            status="applied",
            backup_file=backup_path,
            metadata={"missing_imports": {k: v for k, v in missing_imports.items()}},
        )
        self._record_action(action)

        return BuildResult(
            success=True,
            actions=[action],
            summary=f"Added {len(missing_imports)} missing import(s) to {module_package}",
        )

    def register_route_in_init(self, module_name: str) -> BuildResult:
        """
        Register a new route module in routes/__init__.py.

        Args:
            module_name: e.g. "health" -> routes/health.py

        Returns:
            BuildResult with the modification action.
        """
        init_path = os.path.join(os.getcwd(), "routes", "__init__.py")
        if not os.path.exists(init_path):
            return BuildResult(success=False, error=f"routes/__init__.py not found")

        try:
            with open(init_path, encoding="utf-8") as f:
                source = f.read()
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        # Check if already registered
        if f"from .{module_name} import" in source:
            return BuildResult(success=True, summary=f"{module_name} already registered")

        # Find the last import line and add after it
        import_pattern = re.compile(r"^from \.\w+ import .+$", re.MULTILINE)
        matches = list(import_pattern.finditer(source))
        if not matches:
            return BuildResult(success=False, error="No existing route imports found")

        last_import = matches[-1]
        insert_pos = last_import.end()

        # Determine the router variable name and init function
        router_var = f"{module_name}_router"
        init_func = f"init_{module_name}"

        new_lines = [
            f"from .{module_name} import router as {router_var}, {init_func}",
        ]

        # Also add include_router call if there's a pattern
        include_pattern = re.compile(r"app\.include_router\(.*\)")
        if include_pattern.search(source):
            # Find last include_router and add after it
            include_matches = list(include_pattern.finditer(source))
            last_include = include_matches[-1]
            new_lines.append(
                f"app.include_router({router_var}, prefix=\"/api\")"
            )
            insert_pos = last_include.end()

        new_source = source[:insert_pos] + "\n" + "\n".join(new_lines) + source[insert_pos:]

        backup_path = self._backup_file(init_path)
        try:
            with open(init_path, "w", encoding="utf-8") as f:
                f.write(new_source)
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        action = BuildAction(
            action_id=f"REGISTER-{len(self._action_history) + 1}",
            action_type="register_route",
            target_file=init_path,
            description=f"Registered route module: {module_name}",
            status="applied",
            backup_file=backup_path,
        )
        self._record_action(action)

        return BuildResult(success=True, actions=[action],
                           summary=f"Registered {module_name} in routes/__init__.py")

    # ──────────────────────────────────────────────
    #  Self-Healing Methods
    # ──────────────────────────────────────────────

    def fix_bare_excepts(self, filepath: str) -> BuildResult:
        """
        Find and fix bare 'except:' clauses in a Python file by wrapping them
        with 'except Exception as e:' and adding a logger.exception() call.

        Args:
            filepath: Path to the Python file to fix

        Returns:
            BuildResult with the fix actions.
        """
        if not os.path.exists(filepath):
            return BuildResult(success=False, error=f"File not found: {filepath}")

        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        tree = ast.parse(source)
        bare_except_nodes: List[ast.ExceptHandler] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                bare_except_nodes.append(node)

        if not bare_except_nodes:
            return BuildResult(success=True, summary=f"No bare excepts found in {os.path.basename(filepath)}")

        lines = source.splitlines(keepends=True)
        fixes_applied = 0
        for handler in reversed(bare_except_nodes):
            lineno = handler.lineno
            col_offset = handler.col_offset
            indent = " " * col_offset
            old_line = lines[lineno - 1]
            # Replace bare 'except:' with 'except Exception as e:'
            new_line = old_line.replace("except:", "except Exception as e:", 1)
            if new_line == old_line:
                new_line = old_line.replace("except :", "except Exception as e:", 1)
            if new_line != old_line:
                lines[lineno - 1] = new_line
                # Add logger.exception() inside the except block if body exists
                body_start = lineno  # first line of body
                if body_start < len(lines):
                    body_indent = indent + "    "
                    log_line = f"{body_indent}logger.exception(\"Bare except fixed at line {lineno}\")\n"
                    lines.insert(body_start, log_line)
                fixes_applied += 1

        new_source = "".join(lines)
        backup_path = self._backup_file(filepath)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_source)
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        action = BuildAction(
            action_id=f"FIX-BARE-{len(self._action_history) + 1}",
            action_type="fix_bare_except",
            target_file=filepath,
            status="applied",
            backup_file=backup_path,
            description=f"Fixed {fixes_applied} bare except(s) in {os.path.basename(filepath)}",
            metadata={"fixes": fixes_applied, "lines": [n.lineno for n in bare_except_nodes]},
        )
        self._record_action(action)

        return BuildResult(
            success=True,
            actions=[action],
            summary=f"Fixed {fixes_applied} bare except(s) in {os.path.basename(filepath)}",
        )

    def add_missing_docstrings(self, filepath: str) -> BuildResult:
        """
        Add placeholder docstrings to functions, async functions, and classes
        that are missing them in a Python file.

        Args:
            filepath: Path to the Python file to fix

        Returns:
            BuildResult with the fix actions.
        """
        if not os.path.exists(filepath):
            return BuildResult(success=False, error=f"File not found: {filepath}")

        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        tree = ast.parse(source)
        missing_docstrings: List[Tuple[int, str, str]] = []  # (lineno, kind, name)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Check if the first statement is a docstring
                has_docstring = (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                )
                if not has_docstring:
                    kind = "class" if isinstance(node, ast.ClassDef) else "function"
                    missing_docstrings.append((node.lineno, kind, node.name))

        if not missing_docstrings:
            return BuildResult(
                success=True,
                summary=f"No missing docstrings found in {os.path.basename(filepath)}",
            )

        lines = source.splitlines(keepends=True)
        added = 0
        for lineno, kind, name in reversed(missing_docstrings):
            # Find the line with the def/class declaration
            decl_line = lines[lineno - 1]
            indent = " " * (len(decl_line) - len(decl_line.lstrip()))
            docstring = f'{indent}"""{name} — TODO: add docstring."""\n'
            lines.insert(lineno, docstring)
            added += 1

        new_source = "".join(lines)
        backup_path = self._backup_file(filepath)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_source)
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        action = BuildAction(
            action_id=f"FIX-DOCS-{len(self._action_history) + 1}",
            action_type="add_docstring",
            target_file=filepath,
            status="applied",
            backup_file=backup_path,
            description=f"Added {added} missing docstring(s) in {os.path.basename(filepath)}",
            metadata={"added": added, "items": [{"line": l, "kind": k, "name": n} for l, k, n in missing_docstrings]},
        )
        self._record_action(action)

        return BuildResult(
            success=True,
            actions=[action],
            summary=f"Added {added} missing docstring(s) in {os.path.basename(filepath)}",
        )

    def remove_unused_imports(self, filepath: str) -> BuildResult:
        """
        Detect and remove unused imports from a Python file using AST analysis.

        Args:
            filepath: Path to the Python file to clean

        Returns:
            BuildResult with the fix actions.
        """
        if not os.path.exists(filepath):
            return BuildResult(success=False, error=f"File not found: {filepath}")

        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        tree = ast.parse(source)

        # Collect all imported names and their source locations
        imported_names: Dict[str, List[Tuple[int, int, str]]] = {}  # name -> [(lineno, end_lineno, full_line)]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_names.setdefault(name, []).append(
                        (node.lineno, node.end_lineno or node.lineno, name)
                    )
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_names.setdefault(name, []).append(
                        (node.lineno, node.end_lineno or node.lineno, name)
                    )

        if not imported_names:
            return BuildResult(
                success=True,
                summary=f"No imports found in {os.path.basename(filepath)}",
            )

        # Collect all name references in the module (excluding imports themselves)
        referenced_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                # Skip names that are part of import statements
                parent = getattr(node, 'parent', None)
                if not isinstance(parent, (ast.Import, ast.ImportFrom)):
                    referenced_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                referenced_names.add(node.attr)

        # Build parent references for AST nodes (needed to skip import names)
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore[attr-defined]

        # Re-collect referenced names with parent context
        referenced_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                parent = getattr(node, 'parent', None)
                if not isinstance(parent, (ast.Import, ast.ImportFrom)):
                    referenced_names.add(node.id)

        # Find unused imports
        unused: List[Tuple[int, str]] = []  # (lineno, name)
        for name, locations in imported_names.items():
            base_name = name.split(".")[0]
            if base_name not in referenced_names:
                for lineno, _, _ in locations:
                    unused.append((lineno, name))

        if not unused:
            return BuildResult(
                success=True,
                summary=f"No unused imports found in {os.path.basename(filepath)}",
            )

        # Remove unused import lines (in reverse order to preserve line numbers)
        lines = source.splitlines(keepends=True)
        removed_lines = set()
        for lineno, name in sorted(unused, key=lambda x: -x[0]):
            if lineno - 1 not in removed_lines:
                lines[lineno - 1] = None  # mark for removal
                removed_lines.add(lineno - 1)

        new_lines = [l for l in lines if l is not None]
        new_source = "".join(new_lines)
        backup_path = self._backup_file(filepath)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_source)
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        action = BuildAction(
            action_id=f"FIX-IMPORTS-{len(self._action_history) + 1}",
            action_type="remove_unused_import",
            target_file=filepath,
            status="applied",
            backup_file=backup_path,
            description=f"Removed {len(unused)} unused import(s) from {os.path.basename(filepath)}",
            metadata={"removed": len(unused), "names": [n for _, n in unused]},
        )
        self._record_action(action)

        return BuildResult(
            success=True,
            actions=[action],
            summary=f"Removed {len(unused)} unused import(s) from {os.path.basename(filepath)}",
        )

    def resolve_todos(self, filepath: str) -> BuildResult:
        """
        Scan a file for TODO, FIXME, HACK, XXX, BUG, OPTIMIZE comments and
        create IssueRecord entries in SelfKnowledge for each one.

        Args:
            filepath: Path to the file to scan

        Returns:
            BuildResult with the created issue records.
        """
        if not os.path.exists(filepath):
            return BuildResult(success=False, error=f"File not found: {filepath}")

        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        # Pattern matching for TODO/FIXME/HACK/XXX/BUG/OPTIMIZE
        pattern = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|BUG|OPTIMIZE)\b\s*:?\s*(.*)", re.IGNORECASE)
        lines = source.splitlines()
        found_items: List[Dict[str, Any]] = []

        for i, line in enumerate(lines, start=1):
            m = pattern.search(line)
            if m:
                tag = m.group(1).upper()
                comment_text = m.group(2).strip()
                severity_map = {
                    "BUG": "error",
                    "FIXME": "warning",
                    "HACK": "warning",
                    "TODO": "info",
                    "XXX": "warning",
                    "OPTIMIZE": "info",
                }
                found_items.append({
                    "lineno": i,
                    "tag": tag,
                    "text": comment_text,
                    "severity": severity_map.get(tag, "info"),
                })

        if not found_items:
            return BuildResult(
                success=True,
                summary=f"No TODO/FIXME/HACK items found in {os.path.basename(filepath)}",
            )

        # Create IssueRecord entries via SelfKnowledge
        issues_created = 0
        if self.knowledge is not None:
            from .self_knowledge import IssueRecord
            import uuid
            for item in found_items:
                issue = IssueRecord(
                    issue_id=f"TODO-{uuid.uuid4().hex[:8]}",
                    module=filepath,
                    issue_type=item["tag"].lower(),
                    description=f"{item['tag']}: {item['text']}" if item["text"] else f"{item['tag']} at line {item['lineno']}",
                    lineno=item["lineno"],
                    severity=item["severity"],
                    status="open",
                    metadata={"source": "resolve_todos", "filepath": filepath},
                )
                self.knowledge.add_issue(issue)
                issues_created += 1

        action = BuildAction(
            action_id=f"TODO-{len(self._action_history) + 1}",
            action_type="resolve_todos",
            target_file=filepath,
            status="applied",
            description=f"Found {len(found_items)} TODO/FIXME item(s) in {os.path.basename(filepath)}, created {issues_created} issue(s)",
            metadata={"found": len(found_items), "issues_created": issues_created, "items": found_items},
        )
        self._record_action(action)

        return BuildResult(
            success=True,
            actions=[action],
            summary=f"Found {len(found_items)} TODO/FIXME item(s), created {issues_created} issue record(s) in {os.path.basename(filepath)}",
        )

    def apply_patch(self, filepath: str, search: str, replace: str,
                    description: str = "") -> BuildResult:
        """
        Apply a search/replace patch to a file.

        Args:
            filepath: Path to the file to patch
            search: Exact text to search for
            replace: Text to replace with
            description: Human-readable description of the change

        Returns:
            BuildResult with the modification action.
        """
        if not os.path.exists(filepath):
            return BuildResult(success=False, error=f"File not found: {filepath}")

        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        if search not in source:
            return BuildResult(success=False, error=f"Search text not found in {filepath}")

        new_source = source.replace(search, replace, 1)
        if new_source == source:
            return BuildResult(success=False, error="Replacement produced no change")

        backup_path = self._backup_file(filepath)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_source)
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        action = BuildAction(
            action_id=f"PATCH-{len(self._action_history) + 1}",
            action_type="patch",
            target_file=filepath,
            status="applied",
            backup_file=backup_path,
            description=description or f"Applied patch to {os.path.basename(filepath)}",
            metadata={"search": search[:100], "replace": replace[:100]},
        )
        self._record_action(action)

        return BuildResult(success=True, actions=[action],
                           summary=f"Patched {os.path.basename(filepath)}")

    def rollback(self, action_id: str) -> BuildResult:
        """
        Rollback a previously applied action by restoring the backup.

        Args:
            action_id: The ID of the action to rollback

        Returns:
            BuildResult with the rollback action.
        """
        with self._lock:
            action = None
            for a in self._action_history:
                if a.action_id == action_id:
                    action = a
                    break

        if not action:
            return BuildResult(success=False, error=f"Action not found: {action_id}")
        if action.status != "applied":
            return BuildResult(success=False, error=f"Action {action_id} is not in 'applied' state")
        if not action.backup_file or not os.path.exists(action.backup_file):
            return BuildResult(success=False, error=f"Backup file not found for {action_id}")

        try:
            with open(action.backup_file, encoding="utf-8") as f:
                backup_content = f.read()
            with open(action.target_file, "w", encoding="utf-8") as f:
                f.write(backup_content)
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        action.status = "rolled_back"
        self._save_history()

        return BuildResult(
            success=True,
            actions=[action],
            summary=f"Rolled back {action_id}: {action.description}",
        )

    def get_action_history(self, limit: int = 50) -> List[BuildAction]:
        """Get the action history, most recent first."""
        with self._lock:
            return list(reversed(self._action_history[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Get builder statistics."""
        with self._lock:
            total = len(self._action_history)
            applied = sum(1 for a in self._action_history if a.status == "applied")
            rolled_back = sum(1 for a in self._action_history if a.status == "rolled_back")
            failed = sum(1 for a in self._action_history if a.status == "failed")
            return {
                "total_actions": total,
                "applied": applied,
                "rolled_back": rolled_back,
                "failed": failed,
                "backup_count": len(os.listdir(BACKUP_DIR)) if os.path.isdir(BACKUP_DIR) else 0,
            }

    # ── Internal ───────────────────────────────

    def _create_file(self, filepath: str, content: str, action_type: str,
                     description: str, metadata: Optional[Dict] = None) -> BuildResult:
        """Create a new file with backup safety."""
        if os.path.exists(filepath):
            return BuildResult(success=False, error=f"File already exists: {filepath}")

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except (OSError, PermissionError) as e:
            return BuildResult(success=False, error=str(e))

        action = BuildAction(
            action_id=f"CREATE-{len(self._action_history) + 1}",
            action_type=action_type,
            target_file=filepath,
            description=description,
            status="applied",
            metadata=metadata or {},
        )
        self._record_action(action)

        return BuildResult(success=True, actions=[action],
                           summary=f"Created {os.path.basename(filepath)}")

    def _backup_file(self, filepath: str) -> str:
        """Create a backup of a file before modifying it."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        relpath = os.path.relpath(filepath, os.getcwd())
        safe_name = relpath.replace(os.sep, "_").replace(".", "_")
        backup_name = f"{timestamp}_{safe_name}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        try:
            shutil.copy2(filepath, backup_path)
        except (OSError, PermissionError) as e:
            logger.warning("Failed to create backup of %s: %s", filepath, e)

        return backup_path

    def _record_action(self, action: BuildAction) -> None:
        """Record an action and persist history."""
        with self._lock:
            self._action_history.append(action)
            self._save_history()

    def _build_known_exports(self) -> Dict[str, str]:
        """Build a mapping of exported names to their module paths."""
        exports: Dict[str, str] = {}
        for package, mod in self.knowledge.get_all_modules().items():
            for cls in mod.classes:
                exports[cls.name] = package
            for func in mod.functions:
                exports[func.name] = package
        return exports

    def _add_imports_after_last_import(self, source: str, import_lines: List[str]) -> str:
        """Add import lines after the last existing import in the source."""
        lines = source.splitlines()
        last_import_idx = -1

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_idx = i

        if last_import_idx >= 0:
            # Insert after the last import, with a blank line separator
            indent = ""
            result = lines[:last_import_idx + 1] + [""] + [f"{indent}{l}" for l in import_lines] + lines[last_import_idx + 1:]
        else:
            # No existing imports, add at the top after docstring
            result = lines[:1] + [""] + import_lines + [""] + lines[1:]

        return "\n".join(result)

    # ── Templates ──────────────────────────────

    def _render_template(self, template_name: str, **kwargs: Any) -> str:
        """Render a Jinja2 template with the given variables.

        Args:
            template_name: The template name constant (e.g. TEMPLATE_MODEL)
            **kwargs: Variables to pass to the template

        Returns:
            Rendered string content.

        Raises:
            ValueError: If the template is not found.
        """
        tmpl = self._templates.get(template_name)
        if tmpl is None:
            raise ValueError(f"Template not found: {template_name}")
        env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            undefined=jinja2.StrictUndefined,
        )
        env.filters["title"] = lambda s: s.replace("_", " ").title().replace(" ", "")
        template = env.from_string(tmpl.content)
        return template.render(**kwargs)

    def _load_templates(self) -> None:
        """Load built-in templates."""
        # Built-in templates as defaults
        self._templates = {
            TEMPLATE_ROUTE: Template(
                name=TEMPLATE_ROUTE,
                content="""\"\"\"
{{ module_name | title }} Routes
Auto-generated by AsimNexus SelfBuilder.
\"\"\"

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("{{ base_path }}")
async def list_{{ module_name }}():
    \"\"\"List all {{ module_name }} items.\"\"\"
    try:
        return {"status": "ok", "items": []}
    except Exception as e:
        logger.exception("Error listing {{ module_name }}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("{{ base_path }}/{item_id}")
async def get_{{ module_name }}(item_id: str):
    \"\"\"Get a {{ module_name }} item by ID.\"\"\"
    try:
        return {"status": "ok", "item_id": item_id}
    except Exception as e:
        logger.exception("Error getting {{ module_name }}")
        raise HTTPException(status_code=500, detail=str(e))


def init_{{ module_name }}(app_globals: dict) -> None:
    \"\"\"Initialize the {{ module_name }} module.\"\"\"
    logger.info("Initialized {{ module_name }} routes")
""",
                variables={"module_name": "str", "base_path": "str"},
            ),
            TEMPLATE_MODEL: Template(
                name=TEMPLATE_MODEL,
                content="""\"\"\"
{{ model_name | title }} Model
Auto-generated by AsimNexus SelfBuilder.
\"\"\"

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class {{ model_name | title }}Base(BaseModel):
    \"\"\"Base model for {{ model_name | title }}.\"\"\"
    {% for field_name, field_type in fields %}
    {{ field_name }}: {{ field_type }}
    {% endfor %}


class {{ model_name | title }}Create({{ model_name | title }}Base):
    \"\"\"Create model for {{ model_name | title }}.\"\"\"
    pass


class {{ model_name | title }}Update(BaseModel):
    \"\"\"Update model for {{ model_name | title }}. All fields optional.\"\"\"
    {% for field_name, field_type in fields %}
    {{ field_name }}: Optional[{{ field_type }}] = None
    {% endfor %}


class {{ model_name | title }}Response({{ model_name | title }}Base):
    \"\"\"Response model for {{ model_name | title }}.\"\"\"
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
""",
                variables={"model_name": "str", "fields": "list"},
            ),
            TEMPLATE_SERVICE: Template(
                name=TEMPLATE_SERVICE,
                content="""\"\"\"
{{ service_name | title }} Service
Auto-generated by AsimNexus SelfBuilder.
\"\"\"

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class {{ service_name | title }}Service:
    \"\"\"Business logic service for {{ service_name | title }}.\"\"\"

    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Create a new {{ service_name }} item.\"\"\"
        import secrets
        item_id = secrets.token_hex(8)
        record = {"id": item_id, **data}
        self._items[item_id] = record
        logger.info("Created {{ service_name }}: %s", item_id)
        return record

    async def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        \"\"\"Get a {{ service_name }} item by ID.\"\"\"
        return self._items.get(item_id)

    async def list(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        \"\"\"List {{ service_name }} items with pagination.\"\"\"
        items = list(self._items.values())
        return items[skip:skip + limit]

    async def update(self, item_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        \"\"\"Update a {{ service_name }} item.\"\"\"
        if item_id not in self._items:
            return None
        self._items[item_id].update(data)
        return self._items[item_id]

    async def delete(self, item_id: str) -> bool:
        \"\"\"Delete a {{ service_name }} item.\"\"\"
        return self._items.pop(item_id, None) is not None
""",
                variables={"service_name": "str"},
            ),
            TEMPLATE_TEST_INTEGRATION: Template(
                name=TEMPLATE_TEST_INTEGRATION,
                content="""\"\"\"
Integration tests for {{ module_name }}
Auto-generated by AsimNexus SelfBuilder.
\"\"\"

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_list_{{ module_name }}(app):
    \"\"\"Test listing {{ module_name }} items.\"\"\"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("{{ base_path }}")
    assert response.status_code in (200, 401)
    if response.status_code == 200:
        data = response.json()
        assert "items" in data


@pytest.mark.asyncio
async def test_get_{{ module_name }}_not_found(app):
    \"\"\"Test getting a non-existent {{ module_name }} item.\"\"\"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("{{ base_path }}/nonexistent")
    assert response.status_code in (404, 401)
""",
                variables={"module_name": "str", "base_path": "str"},
            ),
            TEMPLATE_API_CLIENT: Template(
                name=TEMPLATE_API_CLIENT,
                content="""/**
 * {{ service_name | title }} API Client
 * Auto-generated by AsimNexus SelfBuilder.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface {{ service_name | title }}Item {
  id: string;
  {% for field_name, field_type in fields %}
  {{ field_name }}: {{ field_type }};
  {% endfor %}
  created_at: string;
  updated_at?: string;
}

export interface {{ service_name | title }}ListResponse {
  status: string;
  items: {{ service_name | title }}Item[];
}

export interface {{ service_name | title }}CreateRequest {
  {% for field_name, field_type in fields %}
  {{ field_name }}: {{ field_type }};
  {% endfor %}
}

export async function list{{ service_name | title }}(): Promise<{{ service_name | title }}ListResponse> {
  const res = await fetch(`${API_BASE}{{ base_path }}`);
  if (!res.ok) throw new Error(`Failed to list {{ service_name }}: ${res.statusText}`);
  return res.json();
}

export async function get{{ service_name | title }}(id: string): Promise<{{ service_name | title }}Item> {
  const res = await fetch(`${API_BASE}{{ base_path }}/${id}`);
  if (!res.ok) throw new Error(`Failed to get {{ service_name }}: ${res.statusText}`);
  return res.json();
}

export async function create{{ service_name | title }}(data: {{ service_name | title }}CreateRequest): Promise<{{ service_name | title }}Item> {
  const res = await fetch(`${API_BASE}{{ base_path }}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to create {{ service_name }}: ${res.statusText}`);
  return res.json();
}
""",
                variables={"service_name": "str", "base_path": "str", "fields": "list"},
            ),
            TEMPLATE_REACT_COMPONENT: Template(
                name=TEMPLATE_REACT_COMPONENT,
                content="""import React, { useEffect, useState } from 'react';
import { {{ service_name | title }}Item, list{{ service_name | title }} } from '../{{ api_module }}/{{ service_name }}';

interface {{ component_name }}Props {
  title?: string;
}

export const {{ component_name }}: React.FC<{{ component_name }}Props> = ({ title = '{{ service_name | title }}' }) => {
  const [items, setItems] = useState<{{ service_name | title }}Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadItems();
  }, []);

  async function loadItems() {
    try {
      setLoading(true);
      const response = await list{{ service_name | title }}();
      setItems(response.items);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="p-4 text-gray-500">Loading {{ service_name }}...</div>;
  if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">{title}</h2>
      {items.length === 0 ? (
        <p className="text-gray-400">No {{ service_name }} items found.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.id} className="border rounded p-3 hover:bg-gray-50">
              <pre className="text-sm">{JSON.stringify(item, null, 2)}</pre>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default {{ component_name }};
""",
                variables={"service_name": "str", "component_name": "str", "api_module": "str"},
            ),
            TEMPLATE_TEST_UNIT: Template(
                name=TEMPLATE_TEST_UNIT,
                content="""\"\"\"
Tests for {{ source_module }}
{{ "=" * (source_module | length + 10) }}
Auto-generated by AsimNexus SelfBuilder.
\"\"\"

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


from {{ source_module }} import (
{% for class_name in class_names %}
    {{ class_name }},
{% endfor %}
{% for func_name in func_names %}
    {{ func_name }},
{% endfor %}
)
""",
                variables={"source_module": "str", "class_names": "list", "func_names": "list"},
            ),
            TEMPLATE_TEST_REAL: Template(
                name=TEMPLATE_TEST_REAL,
                content="""\"\"\"
Real tests for {{ module_name }}
{{ "=" * (module_name | length + 15) }}
Auto-generated by AsimNexus SelfBuilder.
\"\"\"

from __future__ import annotations

import pytest
import requests


@pytest.mark.real
def test_health_endpoint():
    \"\"\"Test that the health endpoint is reachable.\"\"\"
    response = requests.get("{{ base_url }}/health/live", timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.real
def test_api_root():
    \"\"\"Test that the API root is reachable.\"\"\"
    response = requests.get("{{ base_url }}/", timeout=10)
    assert response.status_code in (200, 404)
""",
                variables={"module_name": "str", "base_url": "str"},
            ),
            TEMPLATE_INIT: Template(
                name=TEMPLATE_INIT,
                content="""\"\"\"
{{ package_name | title }} Package
{{ "=" * (package_name | length + 9) }}
Auto-generated by AsimNexus SelfBuilder.
\"\"\"

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


__all__: list[str] = [
{% for export_name in exports %}
    "{{ export_name }}",
{% endfor %}
]
""",
                variables={"package_name": "str", "exports": "list"},
            ),
            TEMPLATE_SCHEMA: Template(
                name=TEMPLATE_SCHEMA,
                content="""\"\"\"
{{ schema_name | title }} Schema
{{ "=" * (schema_name | length + 8) }}
Auto-generated by AsimNexus SelfBuilder.
\"\"\"

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class {{ schema_name | title }}Schema(BaseModel):
    \"\"\"Schema for {{ schema_name | title }}.\"\"\"
    {% for field_name, field_type in fields %}
    {{ field_name }}: {{ field_type }}
    {% endfor %}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class {{ schema_name | title }}ListResponse(BaseModel):
    \"\"\"List response for {{ schema_name | title }}.\"\"\"
    status: str = "ok"
    items: List[{{ schema_name | title }}Schema] = []
    total: int = 0
""",
                variables={"schema_name": "str", "fields": "list"},
            ),
        }

    # ── Persistence ────────────────────────────

    def _save_history(self) -> None:
        """Persist action history to disk."""
        try:
            filepath = os.path.join(PATCHES_DIR, "action_history.json")
            data = [asdict(a) for a in self._action_history]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except (OSError, PermissionError) as e:
            logger.error("Failed to save action history: %s", e)

    def _load_history(self) -> None:
        """Load action history from disk."""
        filepath = os.path.join(PATCHES_DIR, "action_history.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                self._action_history = [BuildAction(**a) for a in data]
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("Failed to load action history: %s", e)


# ── Convenience ────────────────────────────────

_default_builder: Optional[SelfBuilder] = None


def get_builder() -> SelfBuilder:
    """Get or create the default SelfBuilder singleton."""
    global _default_builder
    if _default_builder is None:
        _default_builder = SelfBuilder()
    return _default_builder
