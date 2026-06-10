#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Code Analysis Tools for Agent System

Tool functions for code analysis, review, formatting, and explanation.
Integrates with AsimNexus evolution module for deep code understanding.

Each function has a TOOL_DEFINITION dict for OpenAI-compatible function calling,
proper error handling, and structured JSON-serializable return values.

Security: These are SECURE-level tools (read-only code operations).
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.Tools.Code")

# ─── Constants ─────────────────────────────────────────────────────────────────

_MAX_CODE_LENGTH = 50000
_LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescriptreact",
    ".jsx": "javascriptreact",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".md": "markdown",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".vue": "vue",
    ".svelte": "svelte",
}


# ─── Helper ────────────────────────────────────────────────────────────────────

def _safe_result(success: bool, data: Any = None,
                 error: Optional[str] = None, **extra) -> Dict:
    """Build a standardized result dict."""
    result = {"success": success, "error": error}
    if data is not None:
        result["data"] = data
    result.update(extra)
    return result


def _detect_language(path_or_ext: str) -> str:
    """Detect programming language from file path or extension."""
    _, ext = os.path.splitext(path_or_ext)
    return _LANGUAGE_EXTENSIONS.get(ext.lower(), "unknown")


def _truncate(text: str, max_len: int = _MAX_CODE_LENGTH) -> str:
    """Truncate text to max_len."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n... [Truncated at {max_len} chars]"


# ─── TOOL: code_analyze ────────────────────────────────────────────────────────

TOOL_DEFINITION_CODE_ANALYZE = {
    "name": "code_analyze",
    "description": "Analyze a source code file and return structured information including imports, classes, functions, and complexity metrics.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the source code file to analyze."
            }
        },
        "required": ["path"]
    }
}


def code_analyze(path: str) -> Dict[str, Any]:
    """Analyze a source code file.

    Extracts:
    - Imports statements
    - Class definitions
    - Function/method definitions
    - Line counts
    - Basic complexity metrics (for Python)

    Args:
        path: Path to source code file.

    Returns:
        Dict with keys: success, language, imports, classes, functions, metrics
    """
    logger.info(f"Code analyze: {path}")

    try:
        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            return _safe_result(False, error=f"File not found: {abs_path}")
        if not os.path.isfile(abs_path):
            return _safe_result(False, error=f"Not a file: {abs_path}")

        file_size = os.path.getsize(abs_path)
        if file_size > _MAX_CODE_LENGTH:
            return _safe_result(False, error=f"File too large: {file_size} bytes")

        language = _detect_language(abs_path)

        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()

        lines = source.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith(("#", "//", "/*", "*", "--")))

        result = {
            "language": language,
            "path": abs_path,
            "metrics": {
                "total_lines": total_lines,
                "code_lines": total_lines - blank_lines - comment_lines,
                "blank_lines": blank_lines,
                "comment_lines": comment_lines,
            },
        }

        # Python-specific deep analysis
        if language == "python":
            try:
                tree = ast.parse(source)

                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append({"name": alias.name, "alias": alias.asname})
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            imports.append({
                                "module": module,
                                "name": alias.name,
                                "alias": alias.asname,
                            })

                classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        methods = [
                            {
                                "name": n.name,
                                "lines": n.end_lineno - n.lineno + 1 if hasattr(n, 'end_lineno') else 0,
                                "decorators": [d.id if isinstance(d, ast.Name) else "" for d in n.decorator_list],
                            }
                            for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        ]
                        classes.append({
                            "name": node.name,
                            "bases": [b.id if isinstance(b, ast.Name) else str(b.id) for b in node.bases if isinstance(b, ast.Name)],
                            "lines": (node.end_lineno or 0) - (node.lineno or 0) + 1,
                            "methods": methods,
                            "method_count": len(methods),
                        })

                functions = []
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        functions.append({
                            "name": node.name,
                            "lines": (node.end_lineno or 0) - (node.lineno or 0) + 1,
                            "decorators": [d.id if isinstance(d, ast.Name) else "" for d in node.decorator_list],
                        })

                result["imports"] = imports
                result["classes"] = classes
                result["functions"] = functions
                result["metrics"]["class_count"] = len(classes)
                result["metrics"]["function_count"] = len(functions)
                result["metrics"]["import_count"] = len(imports)

                # Complexity estimate
                total_branches = sum(
                    1 for node in ast.walk(tree)
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                         ast.Try, ast.Assert, ast.BoolOp))
                )
                result["metrics"]["complexity_score"] = total_branches + 1

            except SyntaxError as e:
                result["parse_error"] = f"AST parse error: {e}"
                logger.warning(f"AST parse error for {abs_path}: {e}")

        else:
            # For non-Python: basic regex-based analysis
            imports = _extract_imports_generic(source, language)
            result["imports"] = imports
            result["metrics"]["import_count"] = len(imports)

        logger.info(f"Analysis complete: {abs_path} ({language}, {total_lines} lines)")
        return _safe_result(success=True, data=result)

    except Exception as e:
        logger.error(f"Failed to analyze '{path}': {e}")
        return _safe_result(False, error=str(e))


def _extract_imports_generic(source: str, language: str) -> List[Dict]:
    """Extract import statements from non-Python code using regex."""
    imports = []
    patterns = {
        "javascript": [
            r'import\s+(?:\{[^}]*\}|[^;]+?)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
        ],
        "typescript": [
            r'import\s+(?:\{[^}]*\}|[^;]+?)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+type\s+(?:\{[^}]*\}|[^;]+?)\s+from\s+[\'"]([^\'"]+)[\'"]',
        ],
        "java": [
            r'import\s+(?:static\s+)?([\w.]+);',
        ],
        "go": [
            r'import\s+"([^"]+)"',
            r'import\s+\(([^)]+)\)',
        ],
        "rust": [
            r'use\s+([\w:]+);',
            r'use\s+([\w:]+)\s+as\s+\w+;',
        ],
    }

    lang_patterns = patterns.get(language, [])
    for pattern in lang_patterns:
        for match in re.finditer(pattern, source):
            imports.append({"source": match.group(1), "pattern": match.group(0)[:80]})

    return imports


# ─── TOOL: code_review ─────────────────────────────────────────────────────────

TOOL_DEFINITION_CODE_REVIEW = {
    "name": "code_review",
    "description": "Review a code diff or code snippet for potential issues, bugs, style violations, and security concerns.",
    "parameters": {
        "type": "object",
        "properties": {
            "diff": {
                "type": "string",
                "description": "The code diff (unified format) or code snippet to review."
            },
            "language": {
                "type": "string",
                "description": "Programming language of the code (e.g., 'python', 'javascript'). If not specified, will auto-detect.",
                "default": ""
            }
        },
        "required": ["diff"]
    }
}


def code_review(diff: str, language: str = "") -> Dict[str, Any]:
    """Review a code diff or snippet for potential issues.

    Performs static analysis checks:
    - Python: PEP8 style, common bugs, security issues
    - General: syntax errors, dangerous patterns

    Args:
        diff: Code diff or snippet to review.
        language: Programming language (auto-detect if empty).

    Returns:
        Dict with keys: success, issues (list of {severity, type, line, message}), summary
    """
    logger.info(f"Code review ({len(diff)} chars, language={language or 'auto'}")

    if not diff.strip():
        return _safe_result(False, error="No code provided to review")

    # Detect language from content if not provided
    if not language:
        language = _detect_language_from_content(diff)

    issues = []

    # Python-specific checks
    if language == "python":
        issues.extend(_review_python(diff))
    elif language in ("javascript", "typescript"):
        issues.extend(_review_javascript(diff, language))
    else:
        # Generic code review
        issues.extend(_review_generic(diff))

    # Security checks (language-agnostic)
    issues.extend(_review_security(diff))

    # Severity counts
    errors = sum(1 for i in issues if i["severity"] == "error")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    info = sum(1 for i in issues if i["severity"] == "info")

    return _safe_result(
        success=True,
        data={
            "issues": issues,
            "summary": {
                "total": len(issues),
                "errors": errors,
                "warnings": warnings,
                "info": info,
                "language": language,
            }
        }
    )


def _detect_language_from_content(code: str) -> str:
    """Detect programming language from code content."""
    # Shebang detection
    first_line = code.splitlines()[0] if code.splitlines() else ""
    shebang_map = {
        "python": "python",
        "node": "javascript",
        "deno": "javascript",
        "bash": "bash",
        "sh": "bash",
        "ruby": "ruby",
        "perl": "perl",
        "php": "php",
        "go": "go",
        "rust": "rust",
    }
    if first_line.startswith("#!"):
        for key, lang in shebang_map.items():
            if key in first_line.lower():
                return lang

    # Keyword-based detection
    keywords = {
        "python": {"def ", "import ", "class ", "print(", "if __name__", "elif ", "except "},
        "javascript": {"function ", "const ", "let ", "var ", "=>", "console.log", "document."},
        "typescript": {": string", ": number", ": boolean", "interface ", "type ", "as string"},
        "java": {"public class", "private ", "protected ", "System.out", "void main"},
        "go": {"func ", "package main", "import (", "defer ", "go func"},
        "rust": {"fn ", "let mut ", "impl ", "struct ", "enum ", "match ", "println!"},
    }

    code_lower = code.lower()
    scores = {}
    for lang, kws in keywords.items():
        scores[lang] = sum(1 for kw in kws if kw.lower() in code_lower)

    if scores and max(scores.values()) > 0:
        return max(scores, key=scores.get)

    return "unknown"


def _review_python(code: str) -> List[Dict]:
    """Run Python-specific code review checks."""
    issues = []

    # Try AST parse for syntax errors
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append({
            "severity": "error",
            "type": "syntax",
            "line": e.lineno or 0,
            "message": f"Syntax error: {e.msg}",
        })
        return issues  # Can't do further analysis on invalid syntax

    # Check for common issues
    lines = code.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Bare except
        if re.match(r'^except\s*:', stripped):
            issues.append({
                "severity": "warning",
                "type": "style",
                "line": i,
                "message": "Bare except clause. Specify exception type(s).",
            })

        # Long lines (PEP8)
        if len(line.rstrip()) > 100 and not line.strip().startswith("#"):
            issues.append({
                "severity": "info",
                "type": "pep8",
                "line": i,
                "message": f"Line too long ({len(line.rstrip())} > 100 chars)",
            })

        # Use of eval/exec
        if re.search(r'\b(eval|exec)\s*\(', stripped):
            issues.append({
                "severity": "error",
                "type": "security",
                "line": i,
                "message": "Use of eval()/exec() is dangerous. Avoid dynamic code execution.",
            })

        # Print in production code
        if re.match(r'^print\s*\(', stripped):
            issues.append({
                "severity": "info",
                "type": "debug",
                "line": i,
                "message": "print() statement found. Use logging instead in production.",
            })

        # Mutable default arguments
        if re.search(r'def\s+\w+\s*\([^)]*=\s*(\[|\{|set\()', stripped):
            issues.append({
                "severity": "warning",
                "type": "bug",
                "line": i,
                "message": "Mutable default argument. Use None instead.",
            })

    # Check for TODO/FIXME
    todo_pattern = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        match = todo_pattern.search(line)
        if match:
            issues.append({
                "severity": "info",
                "type": "todo",
                "line": i,
                "message": f"Found: {match.group()}",
            })

    return issues


def _review_javascript(code: str, language: str) -> List[Dict]:
    """Run JavaScript/TypeScript-specific code review checks."""
    issues = []
    lines = code.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Console.log
        if re.search(r'console\.(log|debug|warn|error)\s*\(', stripped):
            issues.append({
                "severity": "info",
                "type": "debug",
                "line": i,
                "message": "console.* statement found. Remove in production.",
            })

        # Var (should use let/const)
        if re.match(r'var\s+', stripped):
            issues.append({
                "severity": "warning",
                "type": "style",
                "line": i,
                "message": "'var' used. Prefer 'const' or 'let'.",
            })

        # == vs ===
        if re.search(r'[^=!]==[^=]', stripped) and "!==" not in stripped:
            issues.append({
                "severity": "warning",
                "type": "style",
                "line": i,
                "message": "Use '===' instead of '==' for strict equality.",
            })

    return issues


def _review_generic(code: str) -> List[Dict]:
    """Run generic code review checks."""
    issues = []
    lines = code.splitlines()
    todo_pattern = re.compile(r'\b(TODO|FIXME|HACK)\b', re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        match = todo_pattern.search(stripped)
        if match:
            issues.append({
                "severity": "info",
                "type": "todo",
                "line": i,
                "message": f"Found: {match.group()}",
            })

    return issues


def _review_security(code: str) -> List[Dict]:
    """Run security-focused code review checks."""
    issues = []
    lines = code.splitlines()

    dangerous_patterns = [
        (r'\b(subprocess|os\.system|os\.popen|pty\.spawn)\b', "Dangerous subprocess call", "error"),
        (r'\b(sqlite3\.execute|\.execute\(.*["\'].*SELECT|\.execute\(.*["\'].*INSERT)', "Possible SQL injection", "warning"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password", "error"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key", "error"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret", "error"),
        (r'token\s*=\s*["\'][^"\']{10,}["\']', "Possible hardcoded token", "warning"),
        (r'\b(pickle\.loads?|yaml\.load(?!.*SafeLoader)|marshal\.load)\b', "Unsafe deserialization", "error"),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, message, severity in dangerous_patterns:
            if re.search(pattern, line):
                issues.append({
                    "severity": severity,
                    "type": "security",
                    "line": i,
                    "message": message,
                })

    return issues


# ─── TOOL: code_format ─────────────────────────────────────────────────────────

TOOL_DEFINITION_CODE_FORMAT = {
    "name": "code_format",
    "description": "Format code according to language standards. Supports Python (autopep8/black), JavaScript/TypeScript (prettier), and others.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Source code to format."
            },
            "language": {
                "type": "string",
                "description": "Programming language (e.g., 'python', 'javascript')."
            }
        },
        "required": ["code", "language"]
    }
}


def code_format(code: str, language: str) -> Dict[str, Any]:
    """Format code according to language standards.

    Uses:
    - Python: autopep8 or black
    - JS/TS: prettier (if available) or basic indentation
    - Others: basic indentation normalization

    Args:
        code: Source code to format.
        language: Programming language.

    Returns:
        Dict with keys: success, formatted, formatter_used
    """
    logger.info(f"Code format ({len(code)} chars, {language})")

    if not code.strip():
        return _safe_result(False, error="No code provided to format")

    try:
        formatted_code = None
        formatter_used = "none"

        if language == "python":
            # Try black first, then autopep8
            try:
                import black
                formatted_code = black.format_str(code, mode=black.Mode())
                formatter_used = "black"
            except ImportError:
                try:
                    import autopep8
                    formatted_code = autopep8.fix_code(code)
                    formatter_used = "autopep8"
                except ImportError:
                    pass

        elif language in ("javascript", "typescript", "javascriptreact", "typescriptreact",
                          "css", "scss", "json", "html", "markdown", "yaml"):
            try:
                import subprocess
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=f".{language}", delete=False, encoding="utf-8"
                ) as f:
                    f.write(code)
                    temp_path = f.name

                result = subprocess.run(
                    ["npx", "prettier", "--write", "--parser", _prettier_parser(language), temp_path],
                    capture_output=True, text=True, timeout=15,
                )

                if result.returncode == 0:
                    with open(temp_path, "r", encoding="utf-8") as f:
                        formatted_code = f.read()
                    formatter_used = "prettier"

                os.unlink(temp_path)
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                pass

        # Fallback: basic indentation normalization
        if formatted_code is None:
            formatted_code = _basic_format(code)
            formatter_used = "basic"

        return _safe_result(
            success=True,
            data={
                "formatted": formatted_code,
                "formatter_used": formatter_used,
                "original_length": len(code),
                "formatted_length": len(formatted_code),
            }
        )

    except Exception as e:
        logger.error(f"Failed to format code: {e}")
        return _safe_result(False, error=str(e))


def _prettier_parser(language: str) -> str:
    """Map language to prettier parser name."""
    parser_map = {
        "javascript": "babel",
        "javascriptreact": "babel",
        "typescript": "typescript",
        "typescriptreact": "typescript",
        "css": "css",
        "scss": "scss",
        "json": "json",
        "html": "html",
        "markdown": "markdown",
        "yaml": "yaml",
    }
    return parser_map.get(language, "babel")


def _basic_format(code: str) -> str:
    """Basic code formatting: normalize indentation and trailing whitespace."""
    lines = code.splitlines()
    formatted = []
    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()
        formatted.append(line)

    # Ensure single trailing newline
    while formatted and formatted[-1] == "":
        formatted.pop()
    formatted.append("")

    return "\n".join(formatted)


# ─── TOOL: code_explain ────────────────────────────────────────────────────────

TOOL_DEFINITION_CODE_EXPLAIN = {
    "name": "code_explain",
    "description": "Explain what a piece of code does. Returns a structured explanation with purpose, logic, and key details.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Source code to explain."
            },
            "language": {
                "type": "string",
                "description": "Programming language (e.g., 'python', 'javascript'). If not specified, auto-detected.",
                "default": ""
            }
        },
        "required": ["code"]
    }
}


def code_explain(code: str, language: str = "") -> Dict[str, Any]:
    """Explain what a piece of code does.

    Performs structural analysis to produce:
    - Overall purpose
    - Key components (classes, functions)
    - Logic flow
    - Notable patterns

    Args:
        code: Source code to explain.
        language: Programming language (auto-detect if empty).

    Returns:
        Dict with keys: success, explanation (structured text), components
    """
    logger.info(f"Code explain ({len(code)} chars, language={language or 'auto'}")

    if not code.strip():
        return _safe_result(False, error="No code provided to explain")

    if not language:
        language = _detect_language_from_content(code)

    try:
        components = []
        explanation_parts = []

        if language == "python":
            try:
                tree = ast.parse(code)

                # Module docstring
                docstring = ast.get_docstring(tree)
                if docstring:
                    explanation_parts.append(f"Purpose: {docstring.split(chr(10))[0]}")

                # Classes
                classes = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        cls_doc = ast.get_docstring(node)
                        methods = [
                            n.name for n in node.body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        ]
                        classes.append({
                            "type": "class",
                            "name": node.name,
                            "doc": cls_doc or "",
                            "methods": methods,
                            "line": node.lineno,
                        })
                        components.append({
                            "type": "class",
                            "name": node.name,
                            "line": node.lineno,
                            "doc": (cls_doc or "")[:200],
                        })

                if classes:
                    explanation_parts.append(f"Defines {len(classes)} class(es): {', '.join(c['name'] for c in classes)}")

                # Functions
                functions = []
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fn_doc = ast.get_docstring(node)
                        functions.append({
                            "name": node.name,
                            "doc": fn_doc or "",
                            "line": node.lineno,
                        })
                        components.append({
                            "type": "function",
                            "name": node.name,
                            "line": node.lineno,
                            "doc": (fn_doc or "")[:200],
                        })

                if functions:
                    explanation_parts.append(f"Defines {len(functions)} function(s): {', '.join(f['name'] for f in functions)}")

                # Imports
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)

                if imports:
                    explanation_parts.append(f"Imports from {len(imports)} module(s)")

            except SyntaxError:
                explanation_parts.append("(Code contains syntax errors - analysis limited)")

        # Generic structural analysis
        lines = code.splitlines()
        total_lines = len(lines)

        explanation_parts.append(f"\nCode structure: {total_lines} lines of {language} code")

        if not components:
            # Fallback component detection via regex
            # Function definitions
            for i, line in enumerate(lines, 1):
                fn_match = re.search(
                    r'(?:def|function|func|fn|async def)\s+(\w+)\s*\(',
                    line
                )
                if fn_match:
                    components.append({
                        "type": "function",
                        "name": fn_match.group(1),
                        "line": i,
                    })

                cls_match = re.search(
                    r'(?:class|interface|struct|trait)\s+(\w+)',
                    line
                )
                if cls_match:
                    components.append({
                        "type": "class" if "class" in line else "type",
                        "name": cls_match.group(1),
                        "line": i,
                    })

        return _safe_result(
            success=True,
            data={
                "explanation": "\n".join(explanation_parts),
                "components": components,
                "language": language,
                "line_count": total_lines,
            }
        )

    except Exception as e:
        logger.error(f"Failed to explain code: {e}")
        return _safe_result(False, error=str(e))
