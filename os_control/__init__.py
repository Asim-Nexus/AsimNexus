#!/usr/bin/env python3
"""
AsimNexus OS Control Integration
=================================
Unified OS Control system with capability-gated tools.
"""

import sys
from pathlib import Path

# Ensure os_control can be imported
sys.path.insert(0, str(Path(__file__).parent))

# Export main components
try:
    from .tool_registry import tool_registry, ToolRegistry, ToolRegistration, RiskLevel
    from .capability_matrix import capability_matrix, Capability
    from .os_tool_executor import OSToolExecutor
    from .os_control_bridge import call_tool, call_tool_sync, get_available_tools
    
    # Import tool modules
    from .openclaw_like_tools.file_tools import FileTools
    from .openclaw_like_tools.process_tools import ProcessTools
    from .openclaw_like_tools.system_monitor import SystemMonitor
    from .openclaw_like_tools.clipboard_tools import ClipboardTools
    from .openclaw_like_tools.notification_tools import NotificationTools
    
    TOOLS_LOADED = True
except ImportError as e:
    tool_registry = None
    TOOLS_LOADED = False
    import logging
    logging.warning(f"OS Control partial load: {e}")

__all__ = [
    "tool_registry",
    "ToolRegistry",
    "ToolRegistration",
    "RiskLevel",
    "capability_matrix",
    "Capability",
    "OSToolExecutor",
    "call_tool",
    "call_tool_sync",
    "get_available_tools",
    "FileTools",
    "ProcessTools",
    "SystemMonitor",
    "ClipboardTools",
    "NotificationTools",
    "TOOLS_LOADED",
]