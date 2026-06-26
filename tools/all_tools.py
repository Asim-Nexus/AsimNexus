#!/usr/bin/env python3
"""
AsimNexus Unified Tools System
==============================
Central integration point for ALL tools: OS Control + Core Tools
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "DigitalNepal-backend"))

from typing import Dict, Any, List

# OS Control Tools (from os_control/tool_registry.py)
try:
    from os_control.tool_registry import tool_registry, ToolRegistry, RiskLevel
    OS_TOOLS_AVAILABLE = True
except ImportError:
    OS_TOOLS_AVAILABLE = False
    tool_registry = None

def get_all_tools():
    """Return ALL registered tools for frontend compatibility."""
    all_tools = []
    
    if OS_TOOLS_AVAILABLE and tool_registry:
        for reg in tool_registry.list_tools():
            all_tools.append({
                "name": reg.tool_id,
                "description": reg.description,
                "risk_level": reg.risk_level.value,
                "requires_confirmation": reg.requires_confirmation,
            })
    else:
        all_tools.extend([
            {"name": "web.search", "description": "Web search"},
            {"name": "web.fetch", "description": "Web fetch"},
            {"name": "mesh.join", "description": "Join mesh"},
            {"name": "mesh.sync", "description": "Mesh sync"},
        ])
    
    return {"tools": all_tools, "count": len(all_tools)}

def list_tool_ids():
    """Return list of all tool IDs."""
    if OS_TOOLS_AVAILABLE and tool_registry:
        return [reg.tool_id for reg in tool_registry.list_tools()]
    return ["web.search", "web.fetch", "mesh.join", "mesh.sync"]

__all__ = ["get_all_tools", "list_tool_ids", "tool_registry", "OS_TOOLS_AVAILABLE"]