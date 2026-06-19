#!/usr/bin/env python3
"""
AsimNexus Unified Tools Barrel
==============================
All tools consolidated in one place for frontend/backend access.
"""

from typing import Dict, Any, List

# Web Tools
try:
    from core.tools.web_tools import (
        web_search,
        web_fetch,
        web_scrape,
        TOOL_DEFINITION_WEB_SEARCH,
        TOOL_DEFINITION_WEB_FETCH,
        TOOL_DEFINITION_WEB_SCRAPE,
    )
except ImportError:
    def web_search(query, num_results=5): return {"success": False, "error": "web_tools not available"}
    def web_fetch(url, timeout=15): return {"success": False, "error": "web_tools not available"}
    def web_scrape(url, selector, attribute=""): return {"success": False, "error": "web_tools not available"}
    TOOL_DEFINITION_WEB_SEARCH = TOOL_DEFINITION_WEB_FETCH = TOOL_DEFINITION_WEB_SCRAPE = {}

# Memory Tools
try:
    from core.tools.memory_tools import (
        TOOL_DEFINITION_MEMORY_STORE,
        TOOL_DEFINITION_MEMORY_RECALL,
        TOOL_DEFINITION_MEMORY_SEARCH,
    )
except ImportError:
    TOOL_DEFINITION_MEMORY_STORE = TOOL_DEFINITION_MEMORY_RECALL = TOOL_DEFINITION_MEMORY_SEARCH = {}

# Mesh Tools
try:
    from core.tools.mesh_tools import (
        TOOL_DEFINITION_MESH_JOIN,
        TOOL_DEFINITION_MESH_SYNC,
        TOOL_DEFINITION_MESH_STATUS,
    )
except ImportError:
    TOOL_DEFINITION_MESH_JOIN = TOOL_DEFINITION_MESH_SYNC = TOOL_DEFINITION_MESH_STATUS = {}

# File Tools
try:
    from core.tools.file_tools import (
        TOOL_DEFINITION_FILE_READ,
        TOOL_DEFINITION_FILE_WRITE,
        TOOL_DEFINITION_FILE_DELETE,
    )
except ImportError:
    TOOL_DEFINITION_FILE_READ = TOOL_DEFINITION_FILE_WRITE = TOOL_DEFINITION_FILE_DELETE = {}

# Bash Tools
try:
    from core.tools.bash_tools import (
        TOOL_DEFINITION_EXECUTE_BASH,
        TOOL_DEFINITION_EXECUTE_PYTHON,
    )
except ImportError:
    TOOL_DEFINITION_EXECUTE_BASH = TOOL_DEFINITION_EXECUTE_PYTHON = {}

# Code Tools
try:
    from core.tools.code_tools import (
        TOOL_DEFINITION_CODE_REVIEW,
        TOOL_DEFINITION_CODE_GENERATE,
    )
except ImportError:
    TOOL_DEFINITION_CODE_REVIEW = TOOL_DEFINITION_CODE_GENERATE = {}

# All tool definitions for API endpoint
ALL_TOOL_DEFINITIONS = [
    TOOL_DEFINITION_WEB_SEARCH,
    TOOL_DEFINITION_WEB_FETCH,
    TOOL_DEFINITION_WEB_SCRAPE,
    TOOL_DEFINITION_MEMORY_STORE,
    TOOL_DEFINITION_MEMORY_RECALL,
    TOOL_DEFINITION_MEMORY_SEARCH,
    TOOL_DEFINITION_MESH_JOIN,
    TOOL_DEFINITION_MESH_SYNC,
    TOOL_DEFINITION_MESH_STATUS,
    TOOL_DEFINITION_FILE_READ,
    TOOL_DEFINITION_FILE_WRITE,
    TOOL_DEFINITION_FILE_DELETE,
    TOOL_DEFINITION_EXECUTE_BASH,
    TOOL_DEFINITION_EXECUTE_PYTHON,
    TOOL_DEFINITION_CODE_REVIEW,
    TOOL_DEFINITION_CODE_GENERATE,
]

def get_all_tools():
    """Return all tool definitions for frontend compatibility."""
    return {"tools": ALL_TOOL_DEFINITIONS, "count": len(ALL_TOOL_DEFINITIONS)}