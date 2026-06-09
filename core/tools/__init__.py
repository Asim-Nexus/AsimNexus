#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Agent Tools Package

Comprehensive tool library for AsimNexus agent system, inspired by
Odysseus's 50+ tool architecture. Each module provides tools organized
by domain, with OpenAI-compatible function calling schemas.

Modules:
    bash_tools:    Shell command execution, Python sandbox, file I/O
    web_tools:     Web search, URL fetching, CSS scraping
    memory_tools:  Vector memory search, store, recall
    file_tools:    File system operations (read, write, edit, search, list, upload)
    code_tools:    Code analysis, review, formatting, explanation
    mesh_tools:    Mesh network peer discovery, messaging, broadcast

Usage:
    from core.tools import get_default_tool_registry
    registry = get_default_tool_registry()
    # registry is a ToolRegistry with all tools registered
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from core.agent_loop import ToolRegistry, SECURITY_LEVEL_SECURE, SECURITY_LEVEL_SENSITIVE, SECURITY_LEVEL_DANGEROUS

logger = logging.getLogger("AsimNexus.Tools")

# ─── Import all tool modules ───────────────────────────────────────────────────

from core.tools import bash_tools
from core.tools import web_tools
from core.tools import memory_tools
from core.tools import file_tools
from core.tools import code_tools
from core.tools import mesh_tools

# ─── Exported symbols ─────────────────────────────────────────────────────────

__all__ = [
    "bash_tools",
    "web_tools",
    "memory_tools",
    "file_tools",
    "code_tools",
    "mesh_tools",
    "get_default_tool_registry",
    "reset_tool_registry",
]

# ─── Module-level singleton ───────────────────────────────────────────────────

_default_registry: Optional[ToolRegistry] = None


def get_default_tool_registry() -> ToolRegistry:
    """Create and return a ToolRegistry with ALL tools registered.

    Each tool is registered with:
    - OpenAI-compatible parameter schema (from TOOL_DEFINITION constants)
    - Appropriate security level (secure/sensitive/dangerous)
    - requires_approval flag for sensitive and dangerous tools

    Returns:
        ToolRegistry instance with all tools registered.
    """
    global _default_registry
    if _default_registry is not None:
        return _default_registry

    registry = ToolRegistry()

    # ── Bash Tools ──────────────────────────────────────────────────────────
    # Security: DANGEROUS — can execute arbitrary commands

    registry.register_tool(
        name="execute_bash",
        description=bash_tools.TOOL_DEFINITION_EXECUTE_BASH["description"],
        handler=bash_tools.execute_bash,
        parameters=bash_tools.TOOL_DEFINITION_EXECUTE_BASH["parameters"],
        security_level=SECURITY_LEVEL_DANGEROUS,
        requires_approval=True,
    )

    registry.register_tool(
        name="execute_python",
        description=bash_tools.TOOL_DEFINITION_EXECUTE_PYTHON["description"],
        handler=bash_tools.execute_python,
        parameters=bash_tools.TOOL_DEFINITION_EXECUTE_PYTHON["parameters"],
        security_level=SECURITY_LEVEL_DANGEROUS,
        requires_approval=True,
    )

    registry.register_tool(
        name="read_file",
        description=bash_tools.TOOL_DEFINITION_READ_FILE["description"],
        handler=bash_tools.read_file,
        parameters=bash_tools.TOOL_DEFINITION_READ_FILE["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="write_file",
        description=bash_tools.TOOL_DEFINITION_WRITE_FILE["description"],
        handler=bash_tools.write_file,
        parameters=bash_tools.TOOL_DEFINITION_WRITE_FILE["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=True,
    )

    registry.register_tool(
        name="edit_file",
        description=bash_tools.TOOL_DEFINITION_EDIT_FILE["description"],
        handler=bash_tools.edit_file,
        parameters=bash_tools.TOOL_DEFINITION_EDIT_FILE["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=True,
    )

    registry.register_tool(
        name="list_files",
        description=bash_tools.TOOL_DEFINITION_LIST_FILES["description"],
        handler=bash_tools.list_files,
        parameters=bash_tools.TOOL_DEFINITION_LIST_FILES["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    # ── Web Tools ───────────────────────────────────────────────────────────
    # Security: SECURE — read-only web operations

    registry.register_tool(
        name="web_search",
        description=web_tools.TOOL_DEFINITION_WEB_SEARCH["description"],
        handler=web_tools.web_search,
        parameters=web_tools.TOOL_DEFINITION_WEB_SEARCH["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="web_fetch",
        description=web_tools.TOOL_DEFINITION_WEB_FETCH["description"],
        handler=web_tools.web_fetch,
        parameters=web_tools.TOOL_DEFINITION_WEB_FETCH["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="web_scrape",
        description=web_tools.TOOL_DEFINITION_WEB_SCRAPE["description"],
        handler=web_tools.web_scrape,
        parameters=web_tools.TOOL_DEFINITION_WEB_SCRAPE["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    # ── Memory Tools ────────────────────────────────────────────────────────
    # Security: SENSITIVE — read/write user memory data

    registry.register_tool(
        name="memory_search",
        description=memory_tools.TOOL_DEFINITION_MEMORY_SEARCH["description"],
        handler=memory_tools.memory_search,
        parameters=memory_tools.TOOL_DEFINITION_MEMORY_SEARCH["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=False,
    )

    registry.register_tool(
        name="memory_store",
        description=memory_tools.TOOL_DEFINITION_MEMORY_STORE["description"],
        handler=memory_tools.memory_store,
        parameters=memory_tools.TOOL_DEFINITION_MEMORY_STORE["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=True,
    )

    registry.register_tool(
        name="memory_recall",
        description=memory_tools.TOOL_DEFINITION_MEMORY_RECALL["description"],
        handler=memory_tools.memory_recall,
        parameters=memory_tools.TOOL_DEFINITION_MEMORY_RECALL["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=False,
    )

    # ── File Tools ──────────────────────────────────────────────────────────
    # Security: SENSITIVE — file system operations

    registry.register_tool(
        name="file_read",
        description=file_tools.TOOL_DEFINITION_FILE_READ["description"],
        handler=file_tools.file_read,
        parameters=file_tools.TOOL_DEFINITION_FILE_READ["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="file_write",
        description=file_tools.TOOL_DEFINITION_FILE_WRITE["description"],
        handler=file_tools.file_write,
        parameters=file_tools.TOOL_DEFINITION_FILE_WRITE["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=True,
    )

    registry.register_tool(
        name="file_edit",
        description=file_tools.TOOL_DEFINITION_FILE_EDIT["description"],
        handler=file_tools.file_edit,
        parameters=file_tools.TOOL_DEFINITION_FILE_EDIT["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=True,
    )

    registry.register_tool(
        name="file_search",
        description=file_tools.TOOL_DEFINITION_FILE_SEARCH["description"],
        handler=file_tools.file_search,
        parameters=file_tools.TOOL_DEFINITION_FILE_SEARCH["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="file_list",
        description=file_tools.TOOL_DEFINITION_FILE_LIST["description"],
        handler=file_tools.file_list,
        parameters=file_tools.TOOL_DEFINITION_FILE_LIST["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="file_upload",
        description=file_tools.TOOL_DEFINITION_FILE_UPLOAD["description"],
        handler=file_tools.file_upload,
        parameters=file_tools.TOOL_DEFINITION_FILE_UPLOAD["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=True,
    )

    # ── Code Tools ──────────────────────────────────────────────────────────
    # Security: SECURE — read-only code operations

    registry.register_tool(
        name="code_analyze",
        description=code_tools.TOOL_DEFINITION_CODE_ANALYZE["description"],
        handler=code_tools.code_analyze,
        parameters=code_tools.TOOL_DEFINITION_CODE_ANALYZE["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="code_review",
        description=code_tools.TOOL_DEFINITION_CODE_REVIEW["description"],
        handler=code_tools.code_review,
        parameters=code_tools.TOOL_DEFINITION_CODE_REVIEW["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="code_format",
        description=code_tools.TOOL_DEFINITION_CODE_FORMAT["description"],
        handler=code_tools.code_format,
        parameters=code_tools.TOOL_DEFINITION_CODE_FORMAT["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="code_explain",
        description=code_tools.TOOL_DEFINITION_CODE_EXPLAIN["description"],
        handler=code_tools.code_explain,
        parameters=code_tools.TOOL_DEFINITION_CODE_EXPLAIN["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    # ── Mesh Tools ──────────────────────────────────────────────────────────
    # Security: SECURE (discover, status) / SENSITIVE (send, broadcast)

    registry.register_tool(
        name="mesh_discover",
        description=mesh_tools.TOOL_DEFINITION_MESH_DISCOVER["description"],
        handler=mesh_tools.mesh_discover,
        parameters=mesh_tools.TOOL_DEFINITION_MESH_DISCOVER["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="mesh_send",
        description=mesh_tools.TOOL_DEFINITION_MESH_SEND["description"],
        handler=mesh_tools.mesh_send,
        parameters=mesh_tools.TOOL_DEFINITION_MESH_SEND["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=True,
    )

    registry.register_tool(
        name="mesh_status",
        description=mesh_tools.TOOL_DEFINITION_MESH_STATUS["description"],
        handler=mesh_tools.mesh_status,
        parameters=mesh_tools.TOOL_DEFINITION_MESH_STATUS["parameters"],
        security_level=SECURITY_LEVEL_SECURE,
        requires_approval=False,
    )

    registry.register_tool(
        name="mesh_broadcast",
        description=mesh_tools.TOOL_DEFINITION_MESH_BROADCAST["description"],
        handler=mesh_tools.mesh_broadcast,
        parameters=mesh_tools.TOOL_DEFINITION_MESH_BROADCAST["parameters"],
        security_level=SECURITY_LEVEL_SENSITIVE,
        requires_approval=True,
    )

    # ── Summary ─────────────────────────────────────────────────────────────

    all_tools = registry.get_all_tools()
    tool_names = [t["name"] for t in all_tools]
    by_security = {
        SECURITY_LEVEL_SECURE: sum(1 for t in all_tools if t["security_level"] == SECURITY_LEVEL_SECURE),
        SECURITY_LEVEL_SENSITIVE: sum(1 for t in all_tools if t["security_level"] == SECURITY_LEVEL_SENSITIVE),
        SECURITY_LEVEL_DANGEROUS: sum(1 for t in all_tools if t["security_level"] == SECURITY_LEVEL_DANGEROUS),
    }
    by_approval = {
        "requires_approval": sum(1 for t in all_tools if t["requires_approval"]),
        "auto": sum(1 for t in all_tools if not t["requires_approval"]),
    }

    logger.info(
        f"Tool registry initialized: {len(all_tools)} tools registered "
        f"(secure={by_security[SECURITY_LEVEL_SECURE]}, "
        f"sensitive={by_security[SECURITY_LEVEL_SENSITIVE]}, "
        f"dangerous={by_security[SECURITY_LEVEL_DANGEROUS]}, "
        f"approval={by_approval['requires_approval']})"
    )
    logger.debug(f"Registered tools: {', '.join(sorted(tool_names))}")

    _default_registry = registry
    return registry


def reset_tool_registry():
    """Reset the default tool registry singleton.

    Useful for testing to get a clean registry.
    """
    global _default_registry
    if _default_registry is not None:
        _default_registry.reset()
    _default_registry = None
    logger.info("Tool registry reset for testing")
