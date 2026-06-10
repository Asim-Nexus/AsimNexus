#!/usr/bin/env python3
"""
STATUS: REAL — Built-in MCP Server Definitions for AsimNexus

Defines the set of built-in MCP servers that ship with AsimNexus. These are
lightweight HTTP servers that wrap existing AsimNexus subsystems into MCP-compatible
endpoints, allowing any MCP-compatible client (including other AI agents) to
discover and invoke their tools.

Each built-in server runs on a dedicated path under the AsimNexus MCP gateway
(default: ``http://localhost:9100/mcp/<name>``).

Built-in servers:
    asim-memory:   Vector + keyword search, store, recall (core/vectormemory.py)
    asim-mesh:     Mesh network — discover peers, send messages, broadcast
    asim-files:    File system — read, write, edit, search files
    asim-dharma:   Dharma Chakra — veto check, cultural compliance, ethical guard
    asim-clones:   Digital Clone system — identity, life journey, agent routing
"""

from __future__ import annotations

from typing import Dict, List, Optional

from core.mcp.mcp_manager import MCPManager

# ─── Built-in Server Definitions ─────────────────────────────────────────────

BUILTIN_SERVERS: Dict[str, Dict[str, object]] = {
    "asim-memory": {
        "url": "http://localhost:9100/mcp/memory",
        "description": "AsimNexus memory system (vector + keyword search, store, recall)",
        "builtin": True,
        "enabled": True,
    },
    "asim-mesh": {
        "url": "http://localhost:9100/mcp/mesh",
        "description": "AsimNexus mesh network (discover peers, send messages, broadcast)",
        "builtin": True,
        "enabled": True,
    },
    "asim-files": {
        "url": "http://localhost:9100/mcp/files",
        "description": "AsimNexus file system (read, write, edit, search files)",
        "builtin": True,
        "enabled": True,
    },
    "asim-dharma": {
        "url": "http://localhost:9100/mcp/dharma",
        "description": "AsimNexus Dharma Chakra (veto check, cultural compliance, ethical guard)",
        "builtin": True,
        "enabled": True,
    },
    "asim-clones": {
        "url": "http://localhost:9100/mcp/clones",
        "description": "AsimNexus Digital Clone system (identity, life journey, agent routing)",
        "builtin": True,
        "enabled": True,
    },
}


# ─── Public API ──────────────────────────────────────────────────────────────


def register_builtin_servers(manager: MCPManager) -> None:
    """Register all built-in MCP servers with the given manager.

    Iterates over :data:`BUILTIN_SERVERS` and registers each enabled server
    with the provided :class:`~core.mcp.mcp_manager.MCPManager` instance.
    Servers are registered in ``DISCONNECTED`` state; call
    :meth:`~core.mcp.mcp_manager.MCPManager.connect_server` to establish
    connections.

    Args:
        manager: An :class:`~core.mcp.mcp_manager.MCPManager` instance.
    """
    import logging
    logger = logging.getLogger("AsimNexus.MCP.BuiltinServers")

    for name, config in BUILTIN_SERVERS.items():
        if not config.get("enabled", True):
            logger.debug("Skipping disabled built-in server: %s", name)
            continue

        url = str(config["url"])
        try:
            manager.register_server(name=name, url=url)
            logger.info("Registered built-in MCP server: %s (%s)", name, url)
        except ValueError:
            # Server already registered — log and continue
            logger.debug("Built-in server '%s' already registered, skipping", name)
        except Exception as e:
            logger.error("Failed to register built-in server '%s': %s", name, str(e))


def get_builtin_server_names() -> List[str]:
    """Get the list of built-in MCP server names.

    Returns:
        List of built-in server names (e.g., ``["asim-memory", "asim-mesh", ...]``).
    """
    return list(BUILTIN_SERVERS.keys())


def get_builtin_server_config(name: str) -> Optional[Dict[str, object]]:
    """Get the configuration for a specific built-in server.

    Args:
        name: Server name (e.g., ``"asim-memory"``).

    Returns:
        The server config dict, or ``None`` if not found.
    """
    return BUILTIN_SERVERS.get(name)


def is_builtin_server(name: str) -> bool:
    """Check if a server name corresponds to a built-in server.

    Args:
        name: Server name to check.

    Returns:
        ``True`` if the name matches a built-in server definition.
    """
    return name in BUILTIN_SERVERS
