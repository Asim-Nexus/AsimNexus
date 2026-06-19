#!/usr/bin/env python3
"""
AsimNexus Unified Tools System
=============================
Central integration point for ALL tools: OS Control + Core Tools
- OS Control: 80+ tools (file.*, process.*, system.*, hw.*, clipboard.*)
- Core Tools: web_*, memory_*, mesh_*, bash_*, code_*
"""

from typing import Dict, Any, List

# OS Control Tools (from os_control/tool_registry.py)
try:
    from os_control.tool_registry import tool_registry, ToolRegistry, RiskLevel
    OS_TOOLS_AVAILABLE = True
except ImportError:
    OS_TOOLS_AVAILABLE = False
    tool_registry = None

# Core Tools
try:
    from core.tools.web_tools import (
        TOOL_DEFINITION_WEB_SEARCH, TOOL_DEFINITION_WEB_FETCH, TOOL_DEFINITION_WEB_SCRAPE,
    )
except ImportError:
    TOOL_DEFINITION_WEB_SEARCH = TOOL_DEFINITION_WEB_FETCH = TOOL_DEFINITION_WEB_SCRAPE = {}

try:
    from core.tools.memory_tools import (
        TOOL_DEFINITION_MEMORY_STORE, TOOL_DEFINITION_MEMORY_RECALL, TOOL_DEFINITION_MEMORY_SEARCH,
    )
except ImportError:
    TOOL_DEFINITION_MEMORY_STORE = TOOL_DEFINITION_MEMORY_RECALL = TOOL_DEFINITION_MEMORY_SEARCH = {}

try:
    from core.tools.mesh_tools import (
        TOOL_DEFINITION_MESH_JOIN, TOOL_DEFINITION_MESH_SYNC, TOOL_DEFINITION_MESH_STATUS,
    )
except ImportError:
    TOOL_DEFINITION_MESH_JOIN = TOOL_DEFINITION_MESH_SYNC = TOOL_DEFINITION_MESH_STATUS = {}

try:
    from core.tools.bash_tools import (
        TOOL_DEFINITION_EXECUTE_BASH, TOOL_DEFINITION_EXECUTE_PYTHON,
    )
except ImportError:
    TOOL_DEFINITION_EXECUTE_BASH = TOOL_DEFINITION_EXECUTE_PYTHON = {}

try:
    from core.tools.code_tools import (
        TOOL_DEFINITION_CODE_REVIEW, TOOL_DEFINITION_CODE_GENERATE,
    )
except ImportError:
    TOOL_DEFINITION_CODE_REVIEW = TOOL_DEFINITION_CODE_GENERATE = {}

def get_all_tools():
    """
    Return ALL registered tools for frontend compatibility.
    Combines OS Control tools + Core tools.
    """
    all_tools = []
    
    # Add OS Control tools (if available)
    if OS_TOOLS_AVAILABLE and tool_registry:
        for reg in tool_registry.list_tools():
            all_tools.append({
                "name": reg.tool_id,
                "description": reg.description,
                "risk_level": reg.risk_level.value,
                "requires_confirmation": reg.requires_confirmation,
            })
    else:
        # Fallback core tools
        all_tools.extend([
            TOOL_DEFINITION_WEB_SEARCH,
            TOOL_DEFINITION_WEB_FETCH,
            TOOL_DEFINITION_WEB_SCRAPE,
            TOOL_DEFINITION_MEMORY_STORE,
            TOOL_DEFINITION_MEMORY_RECALL,
            TOOL_DEFINITION_MEMORY_SEARCH,
            TOOL_DEFINITION_MESH_JOIN,
            TOOL_DEFINITION_MESH_SYNC,
            TOOL_DEFINITION_MESH_STATUS,
        ])
    
    return {"tools": all_tools, "count": len(all_tools)}

def list_tool_ids():
    """Return list of all tool IDs."""
    if OS_TOOLS_AVAILABLE and tool_registry:
        return [reg.tool_id for reg in tool_registry.list_tools()]
    return ["web.search", "web.fetch", "web.scrape", "mesh.join", "mesh.sync"]

__all__ = ["get_all_tools", "list_tool_ids", "tool_registry", "OS_TOOLS_AVAILABLE"]