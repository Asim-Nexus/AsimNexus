"""Tool Registry — direct re-export of the full AsimNexus tool registry.

This module provides backward compatibility for code that imports from
``os_control.tool_registry`` (e.g., ``app.py``, tests) while exposing the
full 40+ tool catalog from ``asim_tools/registry/tool_registry.py``.

The ``ToolRegistry`` class here wraps the singleton from
``asim_tools.registry.tool_registry`` and provides both:
- The original dict-based API (``list_tools()`` returns dict, ``get_stats()``)
- Direct access to the underlying ``ToolRegistration`` objects via
  ``list_registrations()``

Architecture::

    os_control.tool_registry.ToolRegistry
        └─ delegates to → asim_tools.registry.tool_registry.tool_registry
                             └─ 40+ tools: file.*, process.*, system.*,
                                clipboard.*, notification.*, hw.*
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus")


class ToolRegistry:
    """Compatibility wrapper around the full AsimNexus ToolRegistry.

    Provides the original simple API (``list_tools()`` returns dict,
    ``get_stats()`` returns dict) while delegating to the full
    ``asim_tools.registry.tool_registry.ToolRegistry`` for the actual
    tool metadata and execution.

    Also exposes the full ``ToolRegistration`` objects via
    ``list_registrations()`` for consumers that need rich metadata.
    """

    def __init__(self):
        self._asim_registry = None
        self._fallback_tools: Dict[str, Dict[str, Any]] = {}
        self._register_fallback_tools()

    def _register_fallback_tools(self):
        """Register minimal fallback tools in case asim_tools is unavailable."""
        self._fallback_tools["web_search"] = {
            "desc": "Search the web",
            "category": "web",
            "risk": "low",
        }
        self._fallback_tools["rag_query"] = {
            "desc": "Query RAG knowledge base",
            "category": "knowledge",
            "risk": "low",
        }
        self._fallback_tools["hw.status"] = {
            "desc": "Get comprehensive hardware status across all components (CPU, memory, disk, network)",
            "category": "hardware",
            "risk": "low",
        }

    def _get_asim_registry(self):
        """Lazy-import and return the full tool registry from core/orchestrator/tools/."""
        if self._asim_registry is None:
            try:
                from core.orchestrator.tools.registry.tool_registry import (
                    tool_registry as asim_registry,
                )
                self._asim_registry = asim_registry
            except ImportError:
                logger.debug(
                    "core.orchestrator.tools.registry.tool_registry not available; using fallback"
                )
        return self._asim_registry

    def register_tool(self, name: str, config: Dict[str, Any]):
        """Register a tool in the fallback dict (backward compatibility)."""
        self._fallback_tools[name] = config

    def list_tools(self) -> Dict[str, Any]:
        """Return all registered tools as a dict.

        Merges tools from the full asim_tools registry (if available)
        with the fallback tools. Each tool entry includes:
        - desc: Human-readable description
        - risk: Risk level string
        - category: Tool category
        - sandbox_required: Whether sandbox execution is needed
        - requires_confirmation: Whether human confirmation is needed
        """
        result = dict(self._fallback_tools)
        asim_reg = self._get_asim_registry()
        if asim_reg is not None:
            try:
                for reg in asim_reg.list_tools():
                    tid = reg.tool_id
                    result[tid] = {
                        "desc": reg.description,
                        "risk": reg.risk_level.value if hasattr(reg.risk_level, "value") else str(reg.risk_level),
                        "category": tid.split(".")[0] if "." in tid else "system",
                        "sandbox_required": reg.sandbox_required,
                        "requires_confirmation": reg.requires_confirmation,
                        "allowed_args": reg.allowed_args,
                        "required_capabilities": [c.value for c in reg.required_capabilities],
                    }
            except Exception:
                logger.debug("Error listing asim_tools; using fallback only")
        return result

    def list_registrations(self) -> List[Any]:
        """Return the full list of ``ToolRegistration`` objects.

        Returns an empty list if the asim_tools registry is unavailable.
        """
        asim_reg = self._get_asim_registry()
        if asim_reg is not None:
            try:
                return asim_reg.list_tools()
            except Exception:
                logger.debug("Error listing asim_tools registrations")
        return []

    def get_tool(self, tool_id: str) -> Optional[Any]:
        """Get a single ``ToolRegistration`` by tool_id.

        Returns ``None`` if the tool is not found or registry unavailable.
        """
        asim_reg = self._get_asim_registry()
        if asim_reg is not None:
            try:
                return asim_reg.get_tool(tool_id)
            except Exception:
                pass
        return self._fallback_tools.get(tool_id)

    def get_stats(self) -> Dict[str, Any]:
        """Return microkernel statistics about the registry."""
        tools = self.list_tools()
        return {
            "total_tools": len(tools),
            "tool_names": list(tools.keys()),
            "categories": list(
                {c.get("category", "uncategorized") for c in tools.values() if isinstance(c, dict)}
            ),
        }

    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        agent_name: str = "AutoModeAgent",
    ) -> Dict[str, Any]:
        """Execute a tool through the registry with capability gating.

        Delegates to ``asim_tools.registry.tool_registry.ToolRegistry.execute_tool()``
        which checks the CapabilityMatrix before execution.

        Returns a dict with keys: success, verdict, output, error, call_id, execution_ms.
        """
        asim_reg = self._get_asim_registry()
        if asim_reg is not None:
            try:
                result = await asim_reg.execute_tool(
                    tool_id=tool_id,
                    parameters=parameters,
                    agent_name=agent_name,
                )
                return {
                    "success": result.success,
                    "verdict": result.verdict.value if hasattr(result.verdict, "value") else str(result.verdict),
                    "output": result.output,
                    "error": result.error,
                    "call_id": result.call_id,
                    "execution_ms": result.execution_ms,
                    "required_capabilities": result.required_capabilities,
                }
            except Exception as e:
                logger.error(f"execute_tool error [{tool_id}]: {e}")
                return {
                    "success": False,
                    "verdict": "error",
                    "output": None,
                    "error": str(e),
                    "call_id": "",
                    "execution_ms": 0,
                    "required_capabilities": [],
                }
        return {
            "success": False,
            "verdict": "error",
            "output": None,
            "error": "Tool registry not available",
            "call_id": "",
            "execution_ms": 0,
            "required_capabilities": [],
        }


# Module-level singleton for backward compatibility
tool_registry = ToolRegistry()
