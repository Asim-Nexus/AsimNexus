#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade File System Tools for Agent System

Tool functions for file operations: read, write, edit, search, list, and upload.
Each function has a TOOL_DEFINITION dict for OpenAI-compatible function calling,
proper error handling, and structured JSON-serializable return values.

Security: These are SENSITIVE-level tools (file write/edit operations).
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import logging
import os
import re
import shutil
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.Tools.File")

# ─── Constants ─────────────────────────────────────────────────────────────────

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB read limit
_MAX_SEARCH_SIZE = 50 * 1024 * 1024  # 50 MB search limit
_WORKSPACE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..")
)


# ─── Helper ────────────────────────────────────────────────────────────────────

def _safe_result(success: bool, data: Any = None,
                 error: Optional[str] = None, **extra) -> Dict:
    """Build a standardized result dict."""
    result = {"success": success, "error": error}
    if data is not None:
        result["data"] = data
    result.update(extra)
    return result


def _resolve_path(path: str) -> str:
    """Resolve a path relative to workspace root and validate it."""
    abs_path = os.path.abspath(path)

    # Security: prevent path traversal
    if ".." in path.split(os.sep):
        # Resolve to check actual traversal
        if not abs_path.startswith(_WORKSPACE_ROOT):
            raise PermissionError(f"Path traversal detected: {path} resolves outside workspace")

    return abs_path


def _is_within_workspace(abs_path: str) -> bool:
    """Check if an absolute path is within the workspace."""
    return abs_path.startswith(_WORKSPACE_ROOT) or os.path.commonpath([_WORKSPACE_ROOT, abs_path]) == _WORKSPACE_ROOT


# ─── TOOL: file_read ───────────────────────────────────────────────────────────

TOOL_DEFINITION_FILE_READ = {
    "name": "file_read",
    "description": "Read the full contents of a file. Returns text content and metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read."
            }
        },
        "required": ["path"]
    }
}


def file_read(path: str) -> Dict[str, Any]:
    """Read the full contents of a file.

    Args:
        path: File path to read.

    Returns:
        Dict with keys: success, content, path, size, line_count
    """
    logger.info(f"File read: {path}")

    try:
        abs_path = _resolve_path(path)

        if not os.path.exists(abs_path):
            return _safe_result(False, error=f"File not found: {abs_path}")
        if not os.path.isfile(abs_path):
            return _safe_result(False, error=f"Not a file: {abs_path}")

        file_size = os.path.getsize(abs_path)
        if file_size > _MAX_FILE_SIZE:
            return _safe_result(
                False,
                error=f"File too large: {file_size} bytes (max: {_MAX_FILE_SIZE} bytes)"
            )

        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        return _safe_result(
            success=True,
            data={
                "content": content,
                "path": abs_path,
                "size": file_size,
                "line_count": line_count,
                "lines": content.splitlines(keepends=True) if line_count < 2000 else None,  # Only inline for small files
            }
        )

    except PermissionError as e:
        return _safe_result(False, error=f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Failed to read file '{path}': {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: file_write ──────────────────────────────────────────────────────────

TOOL_DEFINITION_FILE_WRITE = {
    "name": "file_write",
    "description": "Write content to a file. Creates parent directories if they don't exist.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to write the file to."
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file."
            },
            "create_dirs": {
                "type": "boolean",
                "description": "Create parent directories if they don't exist (default: true).",
                "default": True
            }
        },
        "required": ["path", "content"]
    }
}


def file_write(path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
    """Write content to a file.

    Args:
        path: File path to write.
        content: Content to write.
        create_dirs: Create parent directories if missing.

    Returns:
        Dict with keys: success, path, size, action
    """
    logger.info(f"File write: {path} ({len(content)} chars)")

    try:
        abs_path = _resolve_path(path)

        # Create parent directories
        if create_dirs:
            parent_dir = os.path.dirname(abs_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                logger.info(f"Created parent directory: {parent_dir}")

        # Compute checksum before write
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        file_size = os.path.getsize(abs_path)

        logger.info(f"File written: {abs_path} ({file_size} bytes)")
        return _safe_result(
            success=True,
            data={
                "path": abs_path,
                "size": file_size,
                "checksum": checksum,
                "action": "written",
            }
        )

    except PermissionError as e:
        return _safe_result(False, error=f"Permission denied: {e}")
    except OSError as e:
        return _safe_result(False, error=f"OS error: {e}")
    except Exception as e:
        logger.error(f"Failed to write file '{path}': {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: file_edit ───────────────────────────────────────────────────────────

TOOL_DEFINITION_FILE_EDIT = {
    "name": "file_edit",
    "description": "Edit a file by replacing lines in a specific range. Line numbers are 1-based.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit."
            },
            "line_start": {
                "type": "integer",
                "description": "Starting line number (1-based, inclusive)."
            },
            "line_end": {
                "type": "integer",
                "description": "Ending line number (1-based, inclusive). Set to -1 to replace from line_start to end of file."
            },
            "new_text": {
                "type": "string",
                "description": "New text to replace the specified line range with."
            }
        },
        "required": ["path", "line_start", "line_end", "new_text"]
    }
}


def file_edit(path: str, line_start: int, line_end: int, new_text: str) -> Dict[str, Any]:
    """Edit a file by replacing a range of lines.

    Line numbers are 1-based. Replaces lines [line_start, line_end] inclusive.
    If line_end is -1, replaces from line_start to end of file.

    Args:
        path: File path.
        line_start: Start line (1-based, inclusive).
        line_end: End line (1-based, inclusive). -1 means end of file.
        new_text: Replacement text.

    Returns:
        Dict with keys: success, path, lines_replaced, original_range
    """
    logger.info(f"File edit: {path} lines {line_start}-{line_end}")

    try:
        abs_path = _resolve_path(path)

        if not os.path.exists(abs_path):
            return _safe_result(False, error=f"File not found: {abs_path}")

        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)

        # Validate line numbers
        if line_start < 1:
            return _safe_result(False, error=f"line_start must be >= 1, got {line_start}")

        if line_end == -1:
            line_end = total_lines

        if line_start > line_end:
            return _safe_result(False, error=f"line_start ({line_start}) must be <= line_end ({line_end})")
        if line_start > total_lines:
            return _safe_result(False, error=f"line_start ({line_start}) exceeds file length ({total_lines} lines)")

        # Adjust for 0-based indexing
        idx_start = line_start - 1
        idx_end = min(line_end, total_lines)

        original_lines = lines[idx_start:idx_end]
        original_text = "".join(original_lines)

        # Build new content
        new_lines = lines[:idx_start] + [new_text] + lines[idx_end:]

        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        logger.info(f"File edited: {abs_path} (replaced {len(original_lines)} lines)")
        return _safe_result(
            success=True,
            data={
                "path": abs_path,
                "lines_replaced": len(original_lines),
                "original_range": {"start": line_start, "end": min(line_end, total_lines)},
            }
        )

    except PermissionError as e:
        return _safe_result(False, error=f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Failed to edit file '{path}': {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: file_search ─────────────────────────────────────────────────────────

TOOL_DEFINITION_FILE_SEARCH = {
    "name": "file_search",
    "description": "Search for a pattern (regex or literal) across files in a directory.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to search in."
            },
            "pattern": {
                "type": "string",
                "description": "Regex or literal pattern to search for."
            },
            "file_pattern": {
                "type": "string",
                "description": "Optional glob pattern to filter files (e.g., '*.py', '*.md').",
                "default": "*"
            },
            "use_regex": {
                "type": "boolean",
                "description": "If true, treat pattern as regex. If false, literal string search.",
                "default": True
            }
        },
        "required": ["path", "pattern"]
    }
}


def file_search(path: str, pattern: str, file_pattern: str = "*",
                use_regex: bool = True) -> Dict[str, Any]:
    """Search for a pattern across files in a directory.

    Args:
        path: Directory to search.
        pattern: Search pattern (regex or literal).
        file_pattern: Glob pattern to filter files.
        use_regex: If True, pattern is regex; else literal.

    Returns:
        Dict with keys: success, results (list of {file, line, content, line_number}), total_matches
    """
    logger.info(f"File search: '{path}' for '{pattern}' (glob={file_pattern}, regex={use_regex})")

    try:
        abs_path = _resolve_path(path)

        if not os.path.exists(abs_path):
            return _safe_result(False, error=f"Directory not found: {abs_path}")
        if not os.path.isdir(abs_path):
            return _safe_result(False, error=f"Not a directory: {abs_path}")

        # Compile regex
        try:
            if use_regex:
                regex = re.compile(pattern, re.IGNORECASE)
            else:
                regex = re.compile(re.escape(pattern), re.IGNORECASE)
        except re.error as e:
            return _safe_result(False, error=f"Invalid regex pattern: {e}")

        results = []
        file_count = 0
        total_size = 0

        for root, dirs, filenames in os.walk(abs_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for filename in filenames:
                # Skip hidden files and binary extensions
                if filename.startswith("."):
                    continue

                # Apply file pattern filter
                if file_pattern != "*" and not fnmatch.fnmatch(filename, file_pattern):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, abs_path)

                # Check total size limit
                try:
                    fsize = os.path.getsize(filepath)
                    total_size += fsize
                    if total_size > _MAX_SEARCH_SIZE:
                        logger.warning(f"Search size limit reached, stopping at {filepath}")
                        break
                except OSError:
                    continue

                # Skip binary files by checking extension
                ext = os.path.splitext(filename)[1].lower()
                binary_exts = {".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib",
                               ".bin", ".dat", ".db", ".sqlite", ".png", ".jpg",
                               ".jpeg", ".gif", ".bmp", ".ico", ".pdf", ".zip",
                               ".tar", ".gz", ".bz2", ".7z", ".rar", ".o", ".a",
                               ".lib", ".obj", ".pdb", ".ttf", ".otf", ".woff",
                               ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".wav",
                               ".flac", ".ogg"}
                if ext in binary_exts:
                    continue

                try:
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        for line_num, line_content in enumerate(f, 1):
                            match = regex.search(line_content)
                            if match:
                                results.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "content": line_content.rstrip("\n\r"),
                                    "match": match.group() if use_regex else pattern,
                                })
                except (OSError, UnicodeDecodeError):
                    pass

                file_count += 1

            if total_size > _MAX_SEARCH_SIZE:
                break

        # Limit results to prevent overflow
        if len(results) > 1000:
            results = results[:1000]
            logger.info(f"Search results truncated to 1000 matches")

        logger.info(f"Search complete: {len(results)} matches in {file_count} files")
        return _safe_result(
            success=True,
            data={
                "results": results,
                "total_matches": len(results),
                "files_searched": file_count,
                "directory": abs_path,
            }
        )

    except Exception as e:
        logger.error(f"Failed to search '{path}': {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: file_list ───────────────────────────────────────────────────────────

TOOL_DEFINITION_FILE_LIST = {
    "name": "file_list",
    "description": "List files and directories at a path. Can list recursively.",
    "parameters": {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Directory path to list."
            },
            "recursive": {
                "type": "boolean",
                "description": "If true, list files recursively (default: false).",
                "default": False
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum recursion depth when recursive=true (default: 10).",
                "default": 10
            }
        },
        "required": ["directory"]
    }
}


def file_list(directory: str, recursive: bool = False,
              max_depth: int = 10) -> Dict[str, Any]:
    """List files and directories at a path.

    Args:
        directory: Directory path to list.
        recursive: List recursively.
        max_depth: Maximum recursion depth.

    Returns:
        Dict with keys: success, files, directories, path
    """
    logger.info(f"File list: {directory} (recursive={recursive}, depth={max_depth})")

    try:
        abs_path = _resolve_path(directory)

        if not os.path.exists(abs_path):
            return _safe_result(False, error=f"Directory not found: {abs_path}")
        if not os.path.isdir(abs_path):
            return _safe_result(False, error=f"Not a directory: {abs_path}")

        files = []
        directories = []

        if recursive:
            base_depth = abs_path.count(os.sep)
            for root, dirs, filenames in os.walk(abs_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                current_depth = root.count(os.sep) - base_depth
                if current_depth >= max_depth:
                    dirs.clear()  # Don't go deeper

                rel_root = os.path.relpath(root, abs_path)
                if rel_root == ".":
                    rel_root = ""

                for d in sorted(dirs):
                    directories.append(os.path.join(rel_root, d) if rel_root else d)
                for f in sorted(filenames):
                    if f.startswith("."):
                        continue
                    files.append(os.path.join(rel_root, f) if rel_root else f)
        else:
            for entry in sorted(os.listdir(abs_path)):
                if entry.startswith("."):
                    continue
                entry_path = os.path.join(abs_path, entry)
                if os.path.isdir(entry_path):
                    directories.append(entry)
                else:
                    files.append(entry)

        return _safe_result(
            success=True,
            data={
                "path": abs_path,
                "files": files,
                "directories": directories,
                "total_files": len(files),
                "total_directories": len(directories),
            }
        )

    except PermissionError as e:
        return _safe_result(False, error=f"Permission denied: {e}")
    except Exception as e:
        logger.error(f"Failed to list directory '{directory}': {e}")
        return _safe_result(False, error=str(e))


# ─── TOOL: file_upload ─────────────────────────────────────────────────────────

TOOL_DEFINITION_FILE_UPLOAD = {
    "name": "file_upload",
    "description": "Copy/upload a file from source to destination path.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Source file path to copy."
            },
            "destination": {
                "type": "string",
                "description": "Destination path to copy to."
            },
            "overwrite": {
                "type": "boolean",
                "description": "Overwrite destination if it exists (default: false).",
                "default": False
            }
        },
        "required": ["path", "destination"]
    }
}


def file_upload(path: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
    """Copy a file from source to destination.

    Args:
        path: Source file path.
        destination: Destination file path.
        overwrite: If True, overwrite existing destination.

    Returns:
        Dict with keys: success, source, destination, size
    """
    logger.info(f"File upload: {path} -> {destination}")

    try:
        src_path = _resolve_path(path)

        if not os.path.exists(src_path):
            return _safe_result(False, error=f"Source file not found: {src_path}")
        if not os.path.isfile(src_path):
            return _safe_result(False, error=f"Source is not a file: {src_path}")

        # Resolve destination
        dst_path = os.path.abspath(destination)

        # Check overwrite
        if os.path.exists(dst_path) and not overwrite:
            return _safe_result(
                False,
                error=f"Destination exists: {dst_path}. Set overwrite=True to overwrite."
            )

        # Create parent directories
        dst_parent = os.path.dirname(dst_path)
        if dst_parent and not os.path.exists(dst_parent):
            os.makedirs(dst_parent, exist_ok=True)

        # Copy file
        shutil.copy2(src_path, dst_path)
        file_size = os.path.getsize(dst_path)

        logger.info(f"File copied: {src_path} -> {dst_path} ({file_size} bytes)")
        return _safe_result(
            success=True,
            data={
                "source": src_path,
                "destination": dst_path,
                "size": file_size,
            }
        )

    except PermissionError as e:
        return _safe_result(False, error=f"Permission denied: {e}")
    except shutil.SameFileError:
        return _safe_result(False, error="Source and destination are the same file")
    except Exception as e:
        logger.error(f"Failed to copy file '{path}' -> '{destination}': {e}")
        return _safe_result(False, error=str(e))
