#!/usr/bin/env python3
"""
STATUS: REAL — MCPServerAdapter: Expose Python Modules as MCP-Compatible Servers

Wraps any Python module, class, or function collection as an MCP-compatible
HTTP server. Allows registering any AsimNexus subsystem (e.g., ``core/reputation.py``,
``mesh/multi_mesh_router.py``) as an MCP server that other AI agents can discover
and use via the MCP protocol.

Usage::

    from core.mcp.server_adapter import MCPServerAdapter

    adapter = MCPServerAdapter("my-server", "http://localhost:9200/mcp/my")

    def my_handler(arg1: str, arg2: int) -> dict:
        return {"result": arg1 * arg2}

    adapter.register_tool(
        name="my_func",
        handler=my_handler,
        description="Multiplies a string by an integer count",
        parameters={
            "type": "object",
            "properties": {
                "arg1": {"type": "string", "description": "The string to repeat"},
                "arg2": {"type": "integer", "description": "Number of repetitions"},
            },
            "required": ["arg1", "arg2"],
        },
    )

    await adapter.start()  # Starts HTTP server with MCP endpoints
    # ... later ...
    await adapter.stop()
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Awaitable

logger = logging.getLogger("AsimNexus.MCP.ServerAdapter")

# Type alias for tool handlers — can be sync or async
ToolHandler = Callable[..., Any]


# ─── MCPServerAdapter ────────────────────────────────────────────────────────


class MCPServerAdapter:
    """Wraps any Python module/class as an MCP-compatible server.

    Allows registering any AsimNexus module (e.g., ``core/reputation.py``,
    ``mesh/multi_mesh_router.py``) as an MCP server that other AI agents can
    discover and use.

    The adapter starts a lightweight HTTP server (using ``aiohttp``) that exposes
    two MCP endpoints:

    - ``POST /`` — JSON-RPC handler dispatching ``tools/list`` and ``tools/call``
      (and optionally ``initialize`` / ``shutdown``).

    Args:
        name:       Human-readable name for this server (e.g., ``"my-server"``).
        listen_url: The URL this server listens on (e.g.,
                    ``"http://localhost:9200/mcp/my"``).
    """

    def __init__(self, name: str, listen_url: str) -> None:
        self.name = name
        self.listen_url = listen_url
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._server: Optional[Any] = None  # aiohttp.TCPSite or app runner
        self._app: Optional[Any] = None      # aiohttp.web.Application
        self._runner: Optional[Any] = None    # aiohttp.web.AppRunner
        self._started = False

    # ── Tool Registration ───────────────────────────────────────────────────

    def register_tool(
        self,
        name: str,
        handler: ToolHandler,
        description: str,
        parameters: Dict[str, Any],
    ) -> None:
        """Register a function as an MCP-compatible tool.

        The handler can be either a synchronous function or an async coroutine.
        It will be invoked when a client sends a ``tools/call`` request with
        the matching tool name.

        Args:
            name:        Unique tool name within this server.
            handler:     Callable (sync or async) that implements the tool logic.
            description: Human-readable description of what the tool does.
            parameters:  JSON Schema object describing the tool's parameters.
        """
        tool_def = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }
        self._tools[name] = tool_def
        logger.debug("Registered tool '%s' on adapter '%s'", name, self.name)

    def unregister_tool(self, name: str) -> bool:
        """Remove a previously registered tool.

        Args:
            name: Name of the tool to remove.

        Returns:
            ``True`` if the tool was found and removed, ``False`` otherwise.
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug("Unregistered tool '%s' from adapter '%s'", name, self.name)
            return True
        return False

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a registered tool definition by name.

        Args:
            name: Tool name.

        Returns:
            The tool definition dict, or ``None`` if not found.
        """
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools in MCP format.

        Returns:
            List of tool definitions (without the handler function) suitable
            for returning from a ``tools/list`` request.
        """
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            }
            for t in self._tools.values()
        ]

    # ── MCP Endpoint Handlers ───────────────────────────────────────────────

    async def handle_tools_list(self, request: Any) -> Dict[str, Any]:
        """Handle an MCP ``tools/list`` JSON-RPC request.

        Args:
            request: The JSON-RPC request dict.

        Returns:
            JSON-RPC response dict with the list of available tools.
        """
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "result": {
                "tools": self.list_tools(),
            },
        }

    async def handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP ``tools/call`` JSON-RPC request.

        Looks up the tool by name, invokes its handler with the provided
        arguments (supporting both sync and async handlers), and returns the
        result wrapped in an MCP response.

        Args:
            request: The JSON-RPC request dict containing ``params.name``
                     and ``params.arguments``.

        Returns:
            JSON-RPC response dict with the tool's result content.

        Raises:
            KeyError: If the requested tool is not registered.
        """
        req_id = request.get("id", 1)
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in self._tools:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}",
                    "data": {
                        "available_tools": list(self._tools.keys()),
                    },
                },
            }

        tool_def = self._tools[tool_name]
        handler = tool_def["handler"]

        try:
            # Invoke the handler (supports both sync and async)
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": result,
                },
            }

        except Exception as e:
            logger.error(
                "Tool '%s' handler failed: %s", tool_name, str(e),
                exc_info=True,
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32000,
                    "message": f"Tool execution error: {str(e)}",
                },
            }

    async def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP ``initialize`` JSON-RPC request.

        Negotiates protocol version and server capabilities with the client.

        Args:
            request: The JSON-RPC request dict.

        Returns:
            JSON-RPC response dict with server capabilities.
        """
        req_id = request.get("id", 1)
        params = request.get("params", {})
        client_info = params.get("clientInfo", {})
        client_name = client_info.get("name", "unknown")
        client_version = client_info.get("version", "0.0.0")

        logger.info(
            "MCP initialize from '%s' v%s",
            client_name,
            client_version,
        )

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": {},
                    "sampling": {},
                },
                "serverInfo": {
                    "name": self.name,
                    "version": "1.0.0",
                },
            },
        }

    async def handle_shutdown(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP ``shutdown`` JSON-RPC request.

        Args:
            request: The JSON-RPC request dict.

        Returns:
            JSON-RPC response confirming shutdown.
        """
        logger.info("MCP shutdown requested for adapter '%s'", self.name)
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "result": None,
        }

    # ── HTTP Server ─────────────────────────────────────────────────────────

    async def _handle_rpc(self, request: Any) -> Any:
        """Main HTTP handler — routes JSON-RPC requests to MCP methods.

        Parses the incoming JSON-RPC request, dispatches to the appropriate
        handler based on the ``method`` field, and returns the JSON-RPC response.

        Supported methods:
            - ``initialize`` — Protocol handshake
            - ``tools/list`` — List available tools
            - ``tools/call`` — Invoke a tool
            - ``shutdown`` — Graceful shutdown
        """
        try:
            body = await request.json()
        except (json.JSONDecodeError, Exception):
            return await self._json_response(
                request,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error: invalid JSON",
                    },
                },
            )

        method = body.get("method", "")

        if method == "initialize":
            result = await self.handle_initialize(body)
        elif method == "tools/list":
            result = await self.handle_tools_list(body)
        elif method == "tools/call":
            result = await self.handle_tools_call(body)
        elif method == "shutdown":
            result = await self.handle_shutdown(body)
        else:
            result = {
                "jsonrpc": "2.0",
                "id": body.get("id", 1),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            }

        return await self._json_response(request, result)

    async def _json_response(self, request: Any, data: Dict[str, Any]) -> Any:
        """Build an aiohttp JSON response with CORS headers."""
        from aiohttp import web
        return web.json_response(
            data,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        )

    async def _handle_options(self, request: Any) -> Any:
        """Handle CORS preflight OPTIONS requests."""
        from aiohttp import web
        return web.Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "3600",
            },
        )

    async def _health_check(self, request: Any) -> Any:
        """Simple health check endpoint."""
        from aiohttp import web
        return web.json_response({
            "status": "ok",
            "server": self.name,
            "tools_count": len(self._tools),
            "uptime": datetime.now(timezone.utc).isoformat(),
        })

    async def start(self) -> None:
        """Start the MCP HTTP server.

        Launches an ``aiohttp`` web application with the following endpoints:

        - ``POST /`` — Main JSON-RPC endpoint for MCP protocol
        - ``OPTIONS /`` — CORS preflight handler
        - ``GET /health`` — Health check endpoint

        The server listens on the URL provided during construction.

        Raises:
            RuntimeError: If the server is already running.
        """
        if self._started:
            raise RuntimeError(f"MCPServerAdapter '{self.name}' is already running")

        from aiohttp import web

        app = web.Application()
        app.router.add_post("/", self._handle_rpc)
        app.router.add_options("/", self._handle_options)
        app.router.add_get("/health", self._health_check)

        self._app = app

        # Parse listen URL to extract host and port
        from urllib.parse import urlparse
        parsed = urlparse(self.listen_url)
        host = parsed.hostname or "0.0.0.0"
        port = parsed.port or 9200

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, host, port)
        await site.start()

        self._started = True
        logger.info(
            "MCPServerAdapter '%s' started on %s:%d",
            self.name,
            host,
            port,
        )

    async def stop(self) -> None:
        """Stop the MCP HTTP server gracefully.

        Cleans up all server resources. Safe to call even if the server
        hasn't been started.
        """
        if not self._started:
            return

        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None

        self._app = None
        self._started = False
        logger.info("MCPServerAdapter '%s' stopped", self.name)

    @property
    def is_running(self) -> bool:
        """Check if the server is currently running.

        Returns:
            ``True`` if the server is active.
        """
        return self._started

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics.

        Returns:
            Dict with server name, status, and registered tool count.
        """
        return {
            "name": self.name,
            "listen_url": self.listen_url,
            "running": self._started,
            "tools_registered": len(self._tools),
            "tool_names": list(self._tools.keys()),
        }
