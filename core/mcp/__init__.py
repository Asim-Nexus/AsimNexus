#!/usr/bin/env python3
"""
STATUS: REAL — MCP (Model Context Protocol) Manager Package

MCP is the industry-standard protocol for LLM tool integration (modelcontextprotocol.io).
This package provides a full MCP client that can discover, connect to, and invoke tools
from any MCP-compatible server.

Modules:
    mcp_manager:     Core MCPManager — connects to servers, discovers tools, invokes calls
    builtin_servers: Built-in MCP server definitions for AsimNexus subsystems
    server_adapter:  Adapter to expose existing Python functionality as an MCP server

Usage:
    from core.mcp import get_mcp_manager
    manager = get_mcp_manager()
    await manager.register_server("my-server", "http://localhost:9100/mcp/my")
    await manager.connect_server("my-server")
    tools = manager.get_tools_for_llm()
    result = await manager.call_tool("my-server", "my_tool", {"arg": "value"})
"""

from __future__ import annotations

import logging
from typing import Optional

from core.mcp.mcp_manager import (
    MCPManager,
    MCPServer,
    MCPServerStatus,
    MCPTool,
    MCPCall,
)

logger = logging.getLogger("AsimNexus.MCP")

# ─── Module-level singleton ───────────────────────────────────────────────────

_manager_instance: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """Get or create the singleton MCPManager instance.

    Returns the global MCPManager singleton, creating it on first call.
    All built-in servers are registered automatically when the manager
    is first created.

    Returns:
        MCPManager singleton instance.
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MCPManager()
        # Register built-in servers on first initialization
        from core.mcp.builtin_servers import register_builtin_servers
        register_builtin_servers(_manager_instance)
        logger.info("MCPManager initialized with built-in servers")
    return _manager_instance


def reset_mcp_manager() -> None:
    """Reset the MCPManager singleton (primarily for testing).

    Clears the global instance and shuts down any active connections.
    Call this between test cases to get a fresh manager.
    """
    global _manager_instance
    if _manager_instance is not None:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_manager_instance.shutdown())
            else:
                loop.run_until_complete(_manager_instance.shutdown())
        except RuntimeError:
            pass  # No event loop available; cleanup will happen on next init
        _manager_instance = None
        logger.debug("MCPManager singleton reset")


__all__ = [
    "MCPManager",
    "MCPServer",
    "MCPServerStatus",
    "MCPTool",
    "MCPCall",
    "get_mcp_manager",
    "reset_mcp_manager",
]
