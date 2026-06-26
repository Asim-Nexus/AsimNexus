#!/usr/bin/env python3
"""
STATUS: NEW — Sandbox Executor
AsimNexus Tool Executor
=========================
Tool Registry को साथ जडान गरेर Sandbox Execution गर्ने।
"""

import logging
from typing import Dict, Any

try:
    from ..os_control.tool_registry import tool_registry
    from .sandbox import ToolGuard
except ImportError:
    tool_registry = None
    ToolGuard = None


logger = logging.getLogger("AsimNexus.Executor")


class SandboxExecutor:
    """
    Tool को Sandbox मा निर्देशन दिने।
    Safety + Dharma Veto + Execution एकतामा।
    """
    
    def __init__(self):
        self.tool_guard = ToolGuard() if ToolGuard else None
        
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        user_id: str = "default",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Tool लाई sandbox मा चलाउने।
        """
        context = context or {}
        
        # Tool registration जाँच
        if not tool_registry:
            return {"success": False, "error": "Tool registry not available"}
            
        tool = tool_registry.get_tool(tool_id)
        if not tool:
            return {"success": False, "error": f"Tool {tool_id} not found"}
            
        # Sandbox execution
        if self.tool_guard:
            result = await self.tool_guard.check_and_execute(
                tool_id, parameters, user_id, context
            )
            
            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "execution_id": result.execution_id,
                "duration_ms": result.duration_ms
            }
            
        return {"success": False, "error": "Sandbox executor not initialized"}


# Global executor
executor = SandboxExecutor()