#!/usr/bin/env python3
"""
STATUS: REAL — MCPManager: MCP (Model Context Protocol) Client

Implements the core MCP client per the MCP specification (modelcontextprotocol.io).
Manages connections to MCP-compatible tool servers, discovers tools via tools/list,
and invokes tools via tools/call using SSE (Server-Sent Events) transport.

Architecture:
    MCPManager
    ├── register_server()  → adds an MCPServer config
    ├── connect_server()   → SSE connect + capabilities + tools/list
    ├── call_tool()        → tools/call on a specific server
    ├── call_tool_by_name()→ auto-routes to correct server
    └── get_tools_for_llm()→ OpenAI-compatible function-calling format

Reference: https://modelcontextprotocol.io/specification/latest
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import aiohttp

logger = logging.getLogger("AsimNexus.MCP.Manager")


# ─── Enums ────────────────────────────────────────────────────────────────────


class MCPServerStatus(Enum):
    """Connection status of an MCP server."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()


# ─── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class MCPTool:
    """A tool exposed by an MCP server.

    Attributes:
        name:        Unique tool name within the server.
        description: Human-readable description of what the tool does.
        parameters:  JSON Schema object describing the tool's input parameters.
        server_name: Name of the server that provides this tool (populated on discovery).
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    server_name: str = ""

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI-compatible function calling format.

        Returns:
            Dict with 'type': 'function' and 'function' key containing the
            name, description, and parameters schema.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "server_name": self.server_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPTool":
        """Deserialize from a plain dict."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            server_name=data.get("server_name", ""),
        )


@dataclass
class MCPServer:
    """An MCP server connection descriptor.

    Attributes:
        name:           Human-readable identifier for this server.
        url:            SSE endpoint URL for the MCP server.
        status:         Current connection status.
        tools:          List of tools discovered from this server.
        capabilities:   Server capabilities negotiated during handshake.
        client_id:      Unique client identifier assigned during connection.
        last_connected: ISO-formatted timestamp of last successful connection.
        error:          Most recent error message, if any.
        auth_token:     Optional OAuth2 bearer token for authentication.
    """
    name: str
    url: str  # SSE endpoint URL
    status: MCPServerStatus = MCPServerStatus.DISCONNECTED
    tools: List[MCPTool] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)
    client_id: Optional[str] = None
    last_connected: Optional[str] = None
    error: Optional[str] = None
    auth_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict (for logging/persistence)."""
        return {
            "name": self.name,
            "url": self.url,
            "status": self.status.name,
            "tools": [t.to_dict() for t in self.tools],
            "capabilities": self.capabilities,
            "client_id": self.client_id,
            "last_connected": self.last_connected,
            "error": self.error,
            "auth_token": "[REDACTED]" if self.auth_token else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServer":
        """Deserialize from a plain dict."""
        return cls(
            name=data["name"],
            url=data["url"],
            status=MCPServerStatus[data.get("status", "DISCONNECTED")],
            tools=[MCPTool.from_dict(t) for t in data.get("tools", [])],
            capabilities=data.get("capabilities", {}),
            client_id=data.get("client_id"),
            last_connected=data.get("last_connected"),
            error=data.get("error"),
            auth_token=data.get("auth_token"),
        )


@dataclass
class MCPCall:
    """A single tool call made via MCP.

    Tracks the lifecycle of a tool invocation from submission through completion.

    Attributes:
        call_id:    Unique identifier for this call.
        server_name: Name of the server that handled this call.
        tool_name:  Name of the tool that was invoked.
        arguments:  Arguments passed to the tool.
        status:     Current status (pending/running/success/error).
        result:     Result returned by the tool (if successful).
        error:      Error message (if failed).
        duration_ms: Execution time in milliseconds.
        timestamp:  ISO-formatted timestamp of when the call was initiated.
    """
    call_id: str
    server_name: str
    tool_name: str
    arguments: Dict[str, Any]
    status: str = "pending"  # pending, running, success, error
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: str = ""

    def complete(self, result: Any, duration_ms: float) -> None:
        """Mark the call as successfully completed."""
        self.status = "success"
        self.result = result
        self.duration_ms = duration_ms

    def fail(self, error: str, duration_ms: float) -> None:
        """Mark the call as failed."""
        self.status = "error"
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "call_id": self.call_id,
            "server_name": self.server_name,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


# ─── MCPManager ──────────────────────────────────────────────────────────────


class MCPManager:
    """Manages connections to MCP-compatible tool servers.

    The MCP (Model Context Protocol) is an open standard that lets LLM applications
    discover and invoke tools from any MCP-compatible server. This manager:

    1. Connects to MCP servers via SSE (Server-Sent Events)
    2. Discovers available tools via ``tools/list``
    3. Invokes tools via ``tools/call``
    4. Manages server lifecycle (connect/disconnect/reconnect)
    5. Supports OAuth2 authentication
    6. Provides tool lists in OpenAI-compatible format

    Usage::

        manager = MCPManager()
        await manager.register_server("my-server", "http://localhost:9100/mcp/my")
        await manager.connect_server("my-server")
        tools = manager.get_tools_for_llm()
        result = await manager.call_tool("my-server", "my_tool", {"arg": "value"})
        await manager.shutdown()
    """

    def __init__(self) -> None:
        self._servers: Dict[str, MCPServer] = {}
        self._calls: Dict[str, MCPCall] = {}
        self._http_session: Optional[Any] = None

    # ── Session Management ──────────────────────────────────────────────────

    async def _get_session(self) -> Any:
        """Get or create an ``aiohttp.ClientSession``.

        Returns:
            An active ``aiohttp.ClientSession`` instance.
        """
        if self._http_session is None or self._http_session.closed:
            import aiohttp
            self._http_session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )
        return self._http_session

    # ── Server Registration ─────────────────────────────────────────────────

    def register_server(
        self,
        name: str,
        url: str,
        auth_token: Optional[str] = None,
    ) -> MCPServer:
        """Register an MCP server for future connection.

        Adds a server descriptor to the manager's registry without connecting.
        Call :meth:`connect_server` afterwards to establish the connection.

        Args:
            name:       Human-readable identifier for the server.
            url:        SSE endpoint URL (e.g., ``http://localhost:9100/mcp/my``).
            auth_token: Optional OAuth2 bearer token.

        Returns:
            The newly created :class:`MCPServer` descriptor.

        Raises:
            ValueError: If a server with the given name is already registered.
        """
        if name in self._servers:
            raise ValueError(f"Server '{name}' is already registered")

        server = MCPServer(
            name=name,
            url=url,
            auth_token=auth_token,
            status=MCPServerStatus.DISCONNECTED,
        )
        self._servers[name] = server
        logger.info("Registered MCP server: %s (%s)", name, url)
        return server

    async def unregister_server(self, name: str) -> bool:
        """Unregister and disconnect a server.

        Args:
            name: Name of the server to remove.

        Returns:
            ``True`` if the server was found and removed, ``False`` otherwise.
        """
        if name not in self._servers:
            logger.warning("Server '%s' not found for unregister", name)
            return False

        server = self._servers[name]
        if server.status == MCPServerStatus.CONNECTED:
            await self._disconnect(server)

        del self._servers[name]
        logger.info("Unregistered MCP server: %s", name)
        return True

    # ── Connection Management ───────────────────────────────────────────────

    async def connect_server(self, name: str) -> bool:
        """Establish a connection to a registered server and discover its tools.

        Uses MCP's SSE transport to:
        1. Connect to the server endpoint
        2. Negotiate capabilities via ``initialize`` handshake
        3. Discover available tools via ``tools/list``

        Args:
            name: Name of the registered server to connect to.

        Returns:
            ``True`` if connection and tool discovery succeeded.

        Raises:
            ValueError: If the server is not registered.
        """
        server = self.get_server(name)
        if server is None:
            raise ValueError(f"Server '{name}' is not registered. Call register_server() first.")

        server.status = MCPServerStatus.CONNECTING

        try:
            session = await self._get_session()

            # Build request headers
            headers: Dict[str, str] = {"Content-Type": "application/json"}
            if server.auth_token:
                headers["Authorization"] = f"Bearer {server.auth_token}"

            # ── Step 1: Initialize handshake ────────────────────────────────
            init_payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "initialize",
                "params": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {
                        "tools": {},
                        "sampling": {},
                    },
                    "clientInfo": {
                        "name": "AsimNexus",
                        "version": "1.0.0",
                    },
                },
            }

            async with session.post(
                server.url,
                json=init_payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise ConnectionError(
                        f"Initialize handshake failed: HTTP {resp.status} - {error_text}"
                    )
                init_result = await resp.json()

            # Extract server capabilities from response
            if "result" in init_result:
                server.capabilities = init_result["result"].get("capabilities", {})
                server.client_id = init_result["result"].get("clientId")

            # ── Step 2: Discover tools via tools/list ───────────────────────
            tools_payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list",
                "params": {},
            }

            async with session.post(
                server.url,
                json=tools_payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise ConnectionError(
                        f"tools/list failed: HTTP {resp.status}"
                    )
                tools_result = await resp.json()

            # Parse tools from response
            tools_data = []
            if "result" in tools_result:
                tools_data = tools_result["result"].get("tools", [])

            server.tools = []
            for tool_data in tools_data:
                tool = MCPTool(
                    name=tool_data.get("name", "unknown"),
                    description=tool_data.get("description", ""),
                    parameters=tool_data.get("parameters", {}),
                    server_name=server.name,
                )
                server.tools.append(tool)

            server.status = MCPServerStatus.CONNECTED
            server.last_connected = datetime.now(timezone.utc).isoformat()
            server.error = None

            logger.info(
                "Connected to MCP server '%s' — discovered %d tools",
                name,
                len(server.tools),
            )
            return True

        except Exception as e:
            server.status = MCPServerStatus.ERROR
            server.error = str(e)
            logger.error("Failed to connect to MCP server '%s': %s", name, str(e))
            return False

    async def disconnect_server(self, name: str) -> bool:
        """Disconnect from a registered server.

        Args:
            name: Name of the server to disconnect.

        Returns:
            ``True`` if the server was disconnected.
        """
        server = self.get_server(name)
        if server is None:
            logger.warning("Server '%s' not found for disconnect", name)
            return False

        await self._disconnect(server)
        return True

    async def _disconnect(self, server: MCPServer) -> None:
        """Internal: disconnect a server without acquiring the lock."""
        if server.status == MCPServerStatus.CONNECTED:
            try:
                session = await self._get_session()
                headers: Dict[str, str] = {"Content-Type": "application/json"}
                if server.auth_token:
                    headers["Authorization"] = f"Bearer {server.auth_token}"

                shutdown_payload = {
                    "jsonrpc": "2.0",
                    "id": str(uuid.uuid4()),
                    "method": "shutdown",
                    "params": {},
                }
                async with session.post(
                    server.url,
                    json=shutdown_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5),
                ):
                    pass  # Intentional — fire-and-forget
            except Exception:
                pass  # Best-effort disconnect

        server.status = MCPServerStatus.DISCONNECTED
        server.tools = []
        logger.info("Disconnected from MCP server '%s'", server.name)

    # ── Tool Invocation ─────────────────────────────────────────────────────

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Call a tool on a specific MCP server.

        Uses MCP's ``tools/call`` endpoint with proper error handling and
        call history tracking.

        Args:
            server_name: Name of the server hosting the tool.
            tool_name:   Name of the tool to invoke.
            arguments:   Arguments to pass to the tool (must match JSON Schema).

        Returns:
            The result returned by the tool.

        Raises:
            ValueError: If the server is not registered or not connected.
            RuntimeError: If the tool call fails on the server side.
        """
        server = self.get_server(server_name)
        if server is None:
            raise ValueError(f"Server '{server_name}' is not registered")
        if server.status != MCPServerStatus.CONNECTED:
            raise ValueError(
                f"Server '{server_name}' is not connected (status: {server.status.name})"
            )

        # Create call record
        call = MCPCall(
            call_id=str(uuid.uuid4()),
            server_name=server_name,
            tool_name=tool_name,
            arguments=arguments,
            status="running",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._calls[call.call_id] = call

        start_time = time.monotonic()

        try:
            session = await self._get_session()
            headers: Dict[str, str] = {"Content-Type": "application/json"}
            if server.auth_token:
                headers["Authorization"] = f"Bearer {server.auth_token}"

            call_payload = {
                "jsonrpc": "2.0",
                "id": call.call_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
            }

            async with session.post(
                server.url,
                json=call_payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    duration = (time.monotonic() - start_time) * 1000
                    call.fail(f"HTTP {resp.status}: {error_text}", duration)
                    raise RuntimeError(
                        f"Tool call '{tool_name}' on '{server_name}' failed: "
                        f"HTTP {resp.status} - {error_text}"
                    )

                result_data = await resp.json()

            duration = (time.monotonic() - start_time) * 1000

            # Check for JSON-RPC error
            if "error" in result_data:
                error_msg = result_data["error"].get("message", "Unknown error")
                call.fail(error_msg, duration)
                raise RuntimeError(
                    f"Tool call '{tool_name}' on '{server_name}' failed: {error_msg}"
                )

            result = result_data.get("result", {}).get("content", result_data.get("result"))
            call.complete(result, duration)

            logger.info(
                "Tool call '%s' on '%s' succeeded in %.0fms",
                tool_name,
                server_name,
                duration,
            )
            return result

        except asyncio.TimeoutError:
            duration = (time.monotonic() - start_time) * 1000
            call.fail("Request timed out after 60s", duration)
            raise RuntimeError(
                f"Tool call '{tool_name}' on '{server_name}' timed out"
            )

        except Exception as e:
            duration = (time.monotonic() - start_time) * 1000
            if not call.error:  # Don't overwrite a more specific error
                call.fail(str(e), duration)
            raise

    async def call_tool_by_name(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Find which server has this tool and call it.

        Searches across all connected servers for the tool by name.
        If multiple servers expose the same tool name, the first match is used.

        Args:
            tool_name:  Name of the tool to invoke.
            arguments:  Arguments to pass to the tool.

        Returns:
            The result returned by the tool.

        Raises:
            ValueError: If the tool is not found on any connected server.
        """
        for server in self._servers.values():
            if server.status != MCPServerStatus.CONNECTED:
                continue
            for tool in server.tools:
                if tool.name == tool_name:
                    return await self.call_tool(server.name, tool_name, arguments)

        raise ValueError(
            f"Tool '{tool_name}' not found on any connected MCP server. "
            f"Available tools: {[t.name for s in self._servers.values() for t in s.tools]}"
        )

    # ── Tool Discovery ──────────────────────────────────────────────────────

    def get_all_tools(self) -> List[MCPTool]:
        """Get all tools from all connected servers.

        Returns:
            A flat list of all :class:`MCPTool` objects across all connected servers.
        """
        tools: List[MCPTool] = []
        for server in self._servers.values():
            if server.status == MCPServerStatus.CONNECTED:
                tools.extend(server.tools)
        return tools

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI function-calling format.

        This is the primary integration point for LLM providers. The returned
        list can be passed directly to OpenAI, Anthropic, or any provider that
        supports the OpenAI-compatible function calling schema.

        Returns:
            List of OpenAI-compatible tool definitions.
        """
        return [tool.to_openai_format() for tool in self.get_all_tools()]

    # ── Server Access ───────────────────────────────────────────────────────

    def get_server(self, name: str) -> Optional[MCPServer]:
        """Get a registered server by name.

        Args:
            name: Server name.

        Returns:
            The :class:`MCPServer` instance, or ``None`` if not found.
        """
        return self._servers.get(name)

    def get_servers(self) -> Dict[str, MCPServer]:
        """Get all registered servers.

        Returns:
            Dict mapping server names to :class:`MCPServer` instances.
        """
        return dict(self._servers)

    def get_connected_servers(self) -> Dict[str, MCPServer]:
        """Get only connected servers.

        Returns:
            Dict mapping server names to connected :class:`MCPServer` instances.
        """
        return {
            name: server
            for name, server in self._servers.items()
            if server.status == MCPServerStatus.CONNECTED
        }

    # ── Call History ────────────────────────────────────────────────────────

    def get_call_history(self, limit: int = 50) -> List[MCPCall]:
        """Get recent call history.

        Args:
            limit: Maximum number of calls to return. Defaults to 50.

        Returns:
            List of :class:`MCPCall` records, most recent first.
        """
        # Sort by timestamp descending, most recent first
        sorted_calls = sorted(
            self._calls.values(),
            key=lambda c: c.timestamp,
            reverse=True,
        )
        return sorted_calls[:limit]

    def get_call(self, call_id: str) -> Optional[MCPCall]:
        """Get a specific call by ID.

        Args:
            call_id: Unique call identifier.

        Returns:
            The :class:`MCPCall` record, or ``None`` if not found.
        """
        return self._calls.get(call_id)

    def clear_call_history(self) -> None:
        """Clear all call history records."""
        self._calls.clear()
        logger.debug("MCP call history cleared")

    # ── Statistics ──────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get MCP manager statistics.

        Returns:
            Dict with server counts, tool counts, and call statistics.
        """
        total_servers = len(self._servers)
        connected_servers = sum(
            1 for s in self._servers.values()
            if s.status == MCPServerStatus.CONNECTED
        )
        total_tools = sum(
            len(s.tools) for s in self._servers.values()
            if s.status == MCPServerStatus.CONNECTED
        )
        total_calls = len(self._calls)
        success_calls = sum(
            1 for c in self._calls.values() if c.status == "success"
        )
        error_calls = sum(
            1 for c in self._calls.values() if c.status == "error"
        )

        return {
            "total_servers": total_servers,
            "connected_servers": connected_servers,
            "total_tools": total_tools,
            "total_calls": total_calls,
            "successful_calls": success_calls,
            "failed_calls": error_calls,
            "servers": {
                name: {
                    "url": server.url,
                    "status": server.status.name,
                    "tools": len(server.tools),
                    "last_connected": server.last_connected,
                }
                for name, server in self._servers.items()
            },
        }

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def shutdown(self) -> None:
        """Disconnect all servers and clean up resources.

        Gracefully shuts down all server connections and closes the HTTP session.
        This should be called before application exit.
        """
        logger.info("MCPManager shutting down...")

        # Disconnect all servers
        disconnect_tasks = []
        for server in self._servers.values():
            if server.status == MCPServerStatus.CONNECTED:
                disconnect_tasks.append(self._disconnect(server))

        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        # Close HTTP session
        if self._http_session is not None and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None

        logger.info("MCPManager shutdown complete")
