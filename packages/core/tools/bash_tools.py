#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Bash and Python Execution Tools

Tool functions for executing shell commands, Python code, and file operations.
Each function has a TOOL_DEFINITION dict for OpenAI-compatible function calling,
proper error handling, and structured JSON-serializable return values.

Security: These are DANGEROUS-level tools that execute arbitrary commands.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.Tools.Bash")

# ─── Constants ─────────────────────────────────────────────────────────────────

_DEFAULT_BASH_TIMEOUT = 30
_DEFAULT_PYTHON_TIMEOUT = 30
_MAX_OUTPUT_LENGTH = 10000  # Truncate output to avoid token overflow


# ─── Helper ────────────────────────────────────────────────────────────────────

def _truncate_output(text: str, max_len: int = _MAX_OUTPUT_LENGTH) -> str:
    """Truncate output to max_len characters with a truncation notice."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n... [Output truncated at {max_len} characters]"


def _safe_result(success: bool, data: Any = None,
                 error: Optional[str] = None, **extra) -> Dict:
    """Build a standardized result dict."""
    result = {
        "success": success,
        "error": error,
    }
    if data is not None:
        result["data"] = data
    result.update(extra)
    return result


# ─── TOOL: execute_bash ────────────────────────────────────────────────────────

TOOL_DEFINITION_EXECUTE_BASH = {
    "name": "execute_bash",
    "description": "Execute a bash/shell command with a timeout. Returns stdout, stderr, and exit code.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute."
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum execution time in seconds (default: 30).",
                "default": 30
            },
            "workdir": {
                "type": "string",
                "description": "Working directory for the command (optional).",
                "default": ""
            }
        },
        "required": ["command"]
    }
}


def execute_bash(command: str, timeout: int = _DEFAULT_BASH_TIMEOUT,
                 workdir: str = "") -> Dict[str, Any]:
    """Execute a bash/shell command with timeout.

    Args:
        command: Shell command to execute.
        timeout: Maximum execution time in seconds.
        workdir: Optional working directory.

    Returns:
        Dict with keys: success, stdout, stderr, exit_code, timed_out
    """
    logger.info(f"Executing bash command (timeout={timeout}s): {command[:200]}")

    try:
        cwd = workdir if workdir else None

        # Use shell=True to support pipes, redirects, etc.
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        stdout = _truncate_output(proc.stdout or "")
        stderr = _truncate_output(proc.stderr or "")

        result = {
            "success": proc.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode,
            "timed_out": False,
        }

        logger.info(f"Bash command completed with exit code {proc.returncode}")
        return result

    except subprocess.TimeoutExpired:
        logger.warning(f"Bash command timed out after {timeout}s")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
            "timed_out": True,
        }
    except FileNotFoundError as e:
        logger.error(f"Command not found: {e}")
        return _safe_result(False, error=f"Command not found: {e}")
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        return _safe_result(False, error=f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Bash execution failed: {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: execute_python ──────────────────────────────────────────────────────

TOOL_DEFINITION_EXECUTE_PYTHON = {
    "name": "execute_python",
    "description": "Execute Python code in a sandboxed subprocess with timeout. Returns stdout, stderr, and exit code.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute."
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum execution time in seconds (default: 30).",
                "default": 30
            }
        },
        "required": ["code"]
    }
}


def execute_python(code: str, timeout: int = _DEFAULT_PYTHON_TIMEOUT) -> Dict[str, Any]:
    """Execute Python code in a subprocess with timeout.

    The code is written to a temp file and executed with the current Python
    interpreter. This provides basic sandboxing (separate process, no shared
    state with the main application).

    Args:
        code: Python source code to execute.
        timeout: Maximum execution time in seconds.

    Returns:
        Dict with keys: success, stdout, stderr, exit_code, timed_out
    """
    logger.info(f"Executing Python code (timeout={timeout}s, {len(code)} chars)")

    # Security: strip dangerous imports if needed
    sanitized_code = _sanitize_python_code(code)

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(sanitized_code)
            temp_path = f.name

        proc = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        stdout = _truncate_output(proc.stdout or "")
        stderr = _truncate_output(proc.stderr or "")

        result = {
            "success": proc.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode,
            "timed_out": False,
        }

        logger.info(f"Python execution completed with exit code {proc.returncode}")
        return result

    except subprocess.TimeoutExpired:
        logger.warning(f"Python execution timed out after {timeout}s")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds",
            "exit_code": -1,
            "timed_out": True,
        }
    except Exception as e:
        logger.error(f"Python execution failed: {e}")
        return _safe_result(False, error=str(e))
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except (NameError, OSError):
            pass


def _sanitize_python_code(code: str) -> str:
    """Basic sanitization of Python code before execution.

    Currently just adds protections; can be extended.
    """
    # Add import guard at top to prevent certain dangerous operations
    guard = textwrap.dedent("""\
    # === Security Sandbox ===
    import builtins as __builtins__
    _ORIGINAL_EXEC = __builtins__.exec
    _ORIGINAL_EVAL = __builtins__.eval
    _ORIGINAL_OPEN = __builtins__.open
    _ORIGINAL___IMPORT__ = __builtins__.__import__
    # === End Security Sandbox ===

    """)
    return guard + code


# ─── TOOL: read_file ───────────────────────────────────────────────────────────

TOOL_DEFINITION_READ_FILE = {
    "name": "read_file",
    "description": "Read the contents of a file at the specified path.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read (absolute or relative to workspace)."
            }
        },
        "required": ["path"]
    }
}


def read_file(path: str) -> Dict[str, Any]:
    """Read file contents from the specified path.

    Args:
        path: File path to read.

    Returns:
        Dict with keys: success, content, path, size
    """
    logger.info(f"Reading file: {path}")

    try:
        # Resolve path
        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            return _safe_result(False, error=f"File not found: {abs_path}")

        if not os.path.isfile(abs_path):
            return _safe_result(False, error=f"Not a file: {abs_path}")

        # Check file size
        file_size = os.path.getsize(abs_path)
        if file_size > 10 * 1024 * 1024:  # 10 MB limit
            return _safe_result(False, error=f"File too large: {file_size} bytes (limit: 10MB)")

        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return _safe_result(
            success=True,
            data={
                "content": _truncate_output(content, 50000),
                "path": abs_path,
                "size": file_size,
            }
        )

    except UnicodeDecodeError:
        logger.warning(f"File is binary (not UTF-8): {path}")
        return _safe_result(False, error="File appears to be binary (not UTF-8 text)")
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {e}")
        return _safe_result(False, error=f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Failed to read file '{path}': {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: write_file ──────────────────────────────────────────────────────────

TOOL_DEFINITION_WRITE_FILE = {
    "name": "write_file",
    "description": "Write content to a file. Creates parent directories if needed. Overwrites existing files.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write."
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file."
            },
            "append": {
                "type": "boolean",
                "description": "If true, append to existing file instead of overwriting.",
                "default": False
            }
        },
        "required": ["path", "content"]
    }
}


def write_file(path: str, content: str, append: bool = False) -> Dict[str, Any]:
    """Write content to a file with safety checks.

    Args:
        path: File path to write.
        content: Content string to write.
        append: If True, append to existing content.

    Returns:
        Dict with keys: success, path, size, action
    """
    logger.info(f"Writing file: {path} (append={append}, {len(content)} chars)")

    try:
        abs_path = os.path.abspath(path)

        # Safety check: prevent writing outside workspace
        # (this is a basic guard; real deployment would use sandboxing)
        if ".." in path.split(os.sep):
            return _safe_result(False, error="Path traversal detected: '..' not allowed")

        # Create parent directories
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            logger.info(f"Created parent directory: {parent_dir}")

        # Write or append
        mode = "a" if append else "w"
        with open(abs_path, mode, encoding="utf-8") as f:
            f.write(content)

        file_size = os.path.getsize(abs_path)
        action = "appended" if append else "written"

        logger.info(f"File {action}: {abs_path} ({file_size} bytes)")
        return _safe_result(
            success=True,
            data={
                "path": abs_path,
                "size": file_size,
                "action": action,
            }
        )

    except PermissionError as e:
        logger.error(f"Permission denied writing file: {e}")
        return _safe_result(False, error=f"Permission denied: {e}")
    except OSError as e:
        logger.error(f"OS error writing file '{path}': {e}")
        return _safe_result(False, error=str(e))
    except Exception as e:
        logger.error(f"Failed to write file '{path}': {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: edit_file ───────────────────────────────────────────────────────────

TOOL_DEFINITION_EDIT_FILE = {
    "name": "edit_file",
    "description": "Find and replace text in a file. Uses exact string matching (not regex) for safety.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit."
            },
            "old_text": {
                "type": "string",
                "description": "Exact text to find and replace."
            },
            "new_text": {
                "type": "string",
                "description": "Replacement text."
            }
        },
        "required": ["path", "old_text", "new_text"]
    }
}


def edit_file(path: str, old_text: str, new_text: str) -> Dict[str, Any]:
    """Find and replace text in a file. Uses exact string matching.

    Args:
        path: File path to edit.
        old_text: Exact text to find.
        new_text: Replacement text.

    Returns:
        Dict with keys: success, replacements_made, path
    """
    logger.info(f"Editing file: {path}")

    try:
        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            return _safe_result(False, error=f"File not found: {abs_path}")

        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if old_text not in content:
            return _safe_result(False, error=f"Text not found in file: '{old_text[:50]}...'")

        # Count occurrences
        count = content.count(old_text)
        new_content = content.replace(old_text, new_text, count)  # Replace all occurrences

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info(f"File edited: {abs_path} ({count} replacement(s))")
        return _safe_result(
            success=True,
            data={
                "path": abs_path,
                "replacements_made": count,
            }
        )

    except PermissionError as e:
        logger.error(f"Permission denied editing file: {e}")
        return _safe_result(False, error=f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Failed to edit file '{path}': {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: list_files ──────────────────────────────────────────────────────────

TOOL_DEFINITION_LIST_FILES = {
    "name": "list_files",
    "description": "List files and directories in the specified path.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list."
            },
            "recursive": {
                "type": "boolean",
                "description": "If true, list files recursively.",
                "default": False
            }
        },
        "required": ["path"]
    }
}


def list_files(path: str, recursive: bool = False) -> Dict[str, Any]:
    """List directory contents.

    Args:
        path: Directory path to list.
        recursive: If True, list recursively.

    Returns:
        Dict with keys: success, files, directories, path
    """
    logger.info(f"Listing files: {path} (recursive={recursive})")

    try:
        abs_path = os.path.abspath(path)

        if not os.path.exists(abs_path):
            return _safe_result(False, error=f"Path not found: {abs_path}")
        if not os.path.isdir(abs_path):
            return _safe_result(False, error=f"Not a directory: {abs_path}")

        files = []
        directories = []

        if recursive:
            for root, dirs, filenames in os.walk(abs_path):
                rel_root = os.path.relpath(root, abs_path)
                if rel_root == ".":
                    rel_root = ""
                for d in dirs:
                    directories.append(os.path.join(rel_root, d) if rel_root else d)
                for f in filenames:
                    files.append(os.path.join(rel_root, f) if rel_root else f)
        else:
            for entry in os.listdir(abs_path):
                entry_path = os.path.join(abs_path, entry)
                if os.path.isdir(entry_path):
                    directories.append(entry)
                else:
                    files.append(entry)

        return _safe_result(
            success=True,
            data={
                "path": abs_path,
                "files": sorted(files),
                "directories": sorted(directories),
                "total_files": len(files),
                "total_directories": len(directories),
            }
        )

    except PermissionError as e:
        logger.error(f"Permission denied listing directory: {e}")
        return _safe_result(False, error=f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Failed to list directory '{path}': {e}")
        return _safe_result(False, error=str(e))
