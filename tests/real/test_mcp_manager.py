#!/usr/bin/env python3
"""
Tests for [`core/mcp/`](../../core/mcp/) — MCP protocol integration.

Covers:
  - MCPManager: register_server, unregister_server, get_server, get_servers,
    get_connected_servers, get_all_tools, get_tools_for_llm, get_stats, shutdown
  - MCPTool: to_openai_format, to_dict, from_dict
  - MCPServer: to_dict, from_dict
  - MCPCall: complete, fail, to_dict
  - MCPServerStatus enum
  - BUILTIN_SERVERS, register_builtin_servers, get_builtin_server_names
  - MCPServerAdapter: register_tool, unregister_tool, get_tool, list_tools,
    handle_tools_list, handle_tools_call
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.mcp.mcp_manager import (
    MCPManager,
    MCPTool,
    MCPServer,
    MCPCall,
    MCPServerStatus,
)
from core.mcp.builtin_servers import (
    BUILTIN_SERVERS,
    register_builtin_servers,
    get_builtin_server_names,
    get_builtin_server_config,
    is_builtin_server,
)
from core.mcp.server_adapter import MCPServerAdapter


# ═══════════════════════════════════════════════════════════════════════════════
# MCPServerStatus Enum Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMCPServerStatus:
    """Tests for MCPServerStatus enum."""

    def test_values(self):
        assert MCPServerStatus.DISCONNECTED.name == "DISCONNECTED"
        assert MCPServerStatus.CONNECTING.name == "CONNECTING"
        assert MCPServerStatus.CONNECTED.name == "CONNECTED"
        assert MCPServerStatus.ERROR.name == "ERROR"
        assert len(MCPServerStatus) == 4


# ═══════════════════════════════════════════════════════════════════════════════
# MCPTool Data Class Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMCPTool:
    """Tests for MCPTool dataclass."""

    def test_basic_creation(self):
        tool = MCPTool(name="test_tool", description="A test tool",
                       parameters={"type": "object", "properties": {}})
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.server_name == ""

    def test_with_server_name(self):
        tool = MCPTool(name="t1", description="d1",
                       parameters={}, server_name="my-server")
        assert tool.server_name == "my-server"

    def test_to_openai_format(self):
        tool = MCPTool(name="my_tool", description="My desc",
                       parameters={"type": "object", "properties": {"x": {"type": "string"}}})
        fmt = tool.to_openai_format()
        assert fmt["type"] == "function"
        assert fmt["function"]["name"] == "my_tool"
        assert fmt["function"]["description"] == "My desc"
        assert fmt["function"]["parameters"] == {"type": "object", "properties": {"x": {"type": "string"}}}

    def test_to_dict(self):
        tool = MCPTool(name="my_tool", description="desc",
                       parameters={}, server_name="srv1")
        d = tool.to_dict()
        assert d["name"] == "my_tool"
        assert d["server_name"] == "srv1"

    def test_from_dict(self):
        data = {"name": "restored", "description": "restored desc",
                "parameters": {"type": "object"}, "server_name": "srv2"}
        tool = MCPTool.from_dict(data)
        assert tool.name == "restored"
        assert tool.server_name == "srv2"
        assert tool.parameters == {"type": "object"}


# ═══════════════════════════════════════════════════════════════════════════════
# MCPServer Data Class Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMCPServer:
    """Tests for MCPServer dataclass."""

    def test_minimal_creation(self):
        server = MCPServer(name="my-server", url="http://localhost:9100/mcp/test")
        assert server.name == "my-server"
        assert server.url == "http://localhost:9100/mcp/test"
        assert server.status == MCPServerStatus.DISCONNECTED
        assert server.tools == []
        assert server.capabilities == {}

    def test_with_tools(self):
        tool = MCPTool(name="t1", description="d1", parameters={})
        server = MCPServer(name="s1", url="http://localhost:9100/mcp/s1",
                           tools=[tool], status=MCPServerStatus.CONNECTED)
        assert len(server.tools) == 1
        assert server.tools[0].name == "t1"
        assert server.status == MCPServerStatus.CONNECTED

    def test_to_dict_redacts_token(self):
        server = MCPServer(name="s1", url="http://localhost:9100/mcp/s1",
                           auth_token="secret123")
        d = server.to_dict()
        assert d["auth_token"] == "[REDACTED]"

    def test_to_dict_no_token(self):
        server = MCPServer(name="s1", url="http://localhost:9100/mcp/s1")
        d = server.to_dict()
        assert d["auth_token"] is None

    def test_from_dict(self):
        data = {
            "name": "s1",
            "url": "http://localhost:9100/mcp/s1",
            "status": "CONNECTED",
            "tools": [{"name": "t1", "description": "d1", "parameters": {}, "server_name": ""}],
            "capabilities": {},
            "client_id": None,
            "last_connected": None,
            "error": None,
            "auth_token": None,
        }
        server = MCPServer.from_dict(data)
        assert server.name == "s1"
        assert server.status == MCPServerStatus.CONNECTED
        assert len(server.tools) == 1
        assert server.tools[0].name == "t1"

    def test_round_trip_serialization(self):
        tool = MCPTool(name="x", description="y", parameters={"z": 1}, server_name="s1")
        original = MCPServer(name="s1", url="http://localhost:9100/mcp/s1",
                             tools=[tool], status=MCPServerStatus.CONNECTED,
                             client_id="client-001", last_connected="2025-01-01T00:00:00")
        d = original.to_dict()
        restored = MCPServer.from_dict(d)
        assert restored.name == original.name
        assert restored.status == original.status
        assert restored.client_id == original.client_id


# ═══════════════════════════════════════════════════════════════════════════════
# MCPCall Data Class Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMCPCall:
    """Tests for MCPCall dataclass."""

    def test_basic_creation(self):
        call = MCPCall(call_id="call-001", server_name="s1",
                       tool_name="t1", arguments={"x": 1})
        assert call.call_id == "call-001"
        assert call.status == "pending"
        assert call.result is None
        assert call.error is None

    def test_complete(self):
        call = MCPCall(call_id="c1", server_name="s1",
                       tool_name="t1", arguments={})
        call.complete(result={"ok": True}, duration_ms=42.5)
        assert call.status == "success"
        assert call.result == {"ok": True}
        assert call.duration_ms == 42.5

    def test_fail(self):
        call = MCPCall(call_id="c1", server_name="s1",
                       tool_name="t1", arguments={})
        call.fail(error="Something broke", duration_ms=10.0)
        assert call.status == "error"
        assert call.error == "Something broke"
        assert call.duration_ms == 10.0

    def test_to_dict(self):
        call = MCPCall(call_id="c1", server_name="s1",
                       tool_name="t1", arguments={"a": 1},
                       status="running", timestamp="2025-01-01T00:00:00")
        d = call.to_dict()
        assert d["call_id"] == "c1"
        assert d["status"] == "running"
        assert d["arguments"] == {"a": 1}
        assert d["timestamp"] == "2025-01-01T00:00:00"


# ═══════════════════════════════════════════════════════════════════════════════
# MCPManager Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMCPManager:
    """Tests for MCPManager class (without network connections)."""

    @pytest.fixture
    def manager(self) -> MCPManager:
        return MCPManager()

    # ── register_server ────────────────────────────────────────────────────

    def test_register_server(self, manager: MCPManager):
        """Register a server successfully."""
        server = manager.register_server(
            name="test-server",
            url="http://localhost:9100/mcp/test",
        )
        assert isinstance(server, MCPServer)
        assert server.name == "test-server"
        assert server.url == "http://localhost:9100/mcp/test"
        assert server.status == MCPServerStatus.DISCONNECTED

    def test_register_server_with_auth(self, manager: MCPManager):
        """Register a server with auth token."""
        server = manager.register_server(
            name="auth-server",
            url="http://localhost:9100/mcp/auth",
            auth_token="bearer-token-xyz",
        )
        assert server.auth_token == "bearer-token-xyz"

    def test_register_duplicate_server(self, manager: MCPManager):
        """Registering a duplicate server name raises ValueError."""
        manager.register_server(name="dup", url="http://localhost:9100/mcp/dup")
        with pytest.raises(ValueError, match="already registered"):
            manager.register_server(name="dup", url="http://localhost:9100/mcp/dup2")

    def test_register_multiple_servers(self, manager: MCPManager):
        """Multiple servers can be registered."""
        manager.register_server("s1", "http://localhost:9100/mcp/s1")
        manager.register_server("s2", "http://localhost:9100/mcp/s2")
        assert len(manager.get_servers()) == 2

    # ── unregister_server ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_unregister_server(self, manager: MCPManager):
        """Unregister an existing server."""
        manager.register_server("to-go", "http://localhost:9100/mcp/to-go")
        result = await manager.unregister_server("to-go")
        assert result is True
        assert manager.get_server("to-go") is None

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self, manager: MCPManager):
        """Unregistering a nonexistent server returns False."""
        result = await manager.unregister_server("no-such-server")
        assert result is False

    # ── get_server / get_servers ───────────────────────────────────────────

    def test_get_server(self, manager: MCPManager):
        """Get a registered server by name."""
        manager.register_server("my-srv", "http://localhost:9100/mcp/my")
        srv = manager.get_server("my-srv")
        assert srv is not None
        assert srv.name == "my-srv"

    def test_get_server_nonexistent(self, manager: MCPManager):
        """Getting a nonexistent server returns None."""
        assert manager.get_server("ghost") is None

    def test_get_servers_empty(self, manager: MCPManager):
        """No registered servers."""
        assert manager.get_servers() == {}

    def test_get_servers_returns_copy(self, manager: MCPManager):
        """get_servers returns a copy (dict modification safe)."""
        manager.register_server("s1", "http://localhost:9100/mcp/s1")
        servers = manager.get_servers()
        # Adding to the copy should not affect the original dict
        from core.mcp.mcp_manager import MCPServer
        servers["s2"] = MCPServer(name="fake", url="http://fake")
        assert "s2" not in manager.get_servers()

    # ── get_connected_servers ──────────────────────────────────────────────

    def test_get_connected_servers_empty(self, manager: MCPManager):
        """No connected servers when none are registered."""
        assert manager.get_connected_servers() == {}

    def test_get_connected_servers(self, manager: MCPManager):
        """Only connected servers are returned."""
        manager.register_server("s1", "http://localhost:9100/mcp/s1")
        from core.mcp.mcp_manager import MCPServerStatus
        srv = manager.get_server("s1")
        # Manually set status to CONNECTED (simulates successful connection)
        srv.status = MCPServerStatus.CONNECTED
        manager.register_server("s2", "http://localhost:9100/mcp/s2")
        connected = manager.get_connected_servers()
        assert "s1" in connected
        assert "s2" not in connected

    # ── get_all_tools / get_tools_for_llm ──────────────────────────────────

    def test_get_all_tools_empty(self, manager: MCPManager):
        """No tools when no connected servers."""
        assert manager.get_all_tools() == []

    def test_get_all_tools_from_connected(self, manager: MCPManager):
        """Tools from connected servers are returned."""
        tool = MCPTool(name="t1", description="d1", parameters={}, server_name="s1")
        manager.register_server("s1", "http://localhost:9100/mcp/s1")
        srv = manager.get_server("s1")
        srv.status = MCPServerStatus.CONNECTED
        srv.tools.append(tool)
        all_tools = manager.get_all_tools()
        assert len(all_tools) == 1
        assert all_tools[0].name == "t1"

    def test_get_all_tools_disconnected_excluded(self, manager: MCPManager):
        """Tools from disconnected servers are excluded."""
        manager.register_server("s1", "http://localhost:9100/mcp/s1")
        srv = manager.get_server("s1")
        srv.tools.append(MCPTool(name="ghost_tool", description="", parameters={}))
        # s1 is DISCONNECTED, so its tools should not appear
        assert manager.get_all_tools() == []

    def test_get_tools_for_llm_empty(self, manager: MCPManager):
        """No LLM tools when no connected servers."""
        assert manager.get_tools_for_llm() == []

    def test_get_tools_for_llm_format(self, manager: MCPManager):
        """LLM tools are in OpenAI format."""
        tool = MCPTool(name="search", description="Search tool",
                       parameters={"type": "object"}, server_name="s1")
        manager.register_server("s1", "http://localhost:9100/mcp/s1")
        srv = manager.get_server("s1")
        srv.status = MCPServerStatus.CONNECTED
        srv.tools.append(tool)
        llm_tools = manager.get_tools_for_llm()
        assert len(llm_tools) == 1
        assert llm_tools[0]["type"] == "function"
        assert llm_tools[0]["function"]["name"] == "search"

    # ── get_stats ──────────────────────────────────────────────────────────

    def test_get_stats_empty(self, manager: MCPManager):
        """Stats with no servers."""
        stats = manager.get_stats()
        assert stats["total_servers"] == 0
        assert stats["connected_servers"] == 0
        assert stats["total_tools"] == 0
        assert stats["total_calls"] == 0

    def test_get_stats_with_data(self, manager: MCPManager):
        """Stats reflect registered servers and calls."""
        manager.register_server("s1", "http://localhost:9100/mcp/s1")
        srv = manager.get_server("s1")
        srv.status = MCPServerStatus.CONNECTED
        srv.tools.append(MCPTool(name="t1", description="", parameters={}))

        call = MCPCall(call_id="c1", server_name="s1", tool_name="t1", arguments={})
        call.complete(result={}, duration_ms=10)
        manager._calls["c1"] = call

        stats = manager.get_stats()
        assert stats["total_servers"] == 1
        assert stats["connected_servers"] == 1
        assert stats["total_tools"] == 1
        assert stats["total_calls"] == 1
        assert stats["successful_calls"] == 1
        assert stats["failed_calls"] == 0

    # ── get_call_history / get_call / clear_call_history ───────────────────

    def test_get_call_history_empty(self, manager: MCPManager):
        """No call history when no calls made."""
        assert manager.get_call_history() == []

    def test_get_call_history_ordered(self, manager: MCPManager):
        """Call history is ordered most recent first."""
        c1 = MCPCall(call_id="c1", server_name="s1", tool_name="t1", arguments={},
                     timestamp="2025-01-01T00:00:00")
        c2 = MCPCall(call_id="c2", server_name="s1", tool_name="t2", arguments={},
                     timestamp="2025-01-01T00:01:00")
        manager._calls["c1"] = c1
        manager._calls["c2"] = c2
        history = manager.get_call_history()
        assert history[0].call_id == "c2"  # Most recent first
        assert history[1].call_id == "c1"

    def test_get_call(self, manager: MCPManager):
        """Get a specific call by ID."""
        call = MCPCall(call_id="find-me", server_name="s1", tool_name="t1", arguments={})
        manager._calls["find-me"] = call
        assert manager.get_call("find-me") is call
        assert manager.get_call("no-such") is None

    def test_clear_call_history(self, manager: MCPManager):
        """Clearing call history removes all calls."""
        manager._calls["c1"] = MCPCall(call_id="c1", server_name="s1", tool_name="t1", arguments={})
        manager.clear_call_history()
        assert manager._calls == {}

    # ── shutdown ───────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_shutdown_empty(self, manager: MCPManager):
        """Shutdown with no servers succeeds."""
        await manager.shutdown()  # Should not raise

    @pytest.mark.asyncio
    async def test_shutdown_with_disconnected_servers(self, manager: MCPManager):
        """Shutdown with disconnected servers succeeds."""
        manager.register_server("s1", "http://localhost:9100/mcp/s1")
        manager.register_server("s2", "http://localhost:9100/mcp/s2")
        await manager.shutdown()  # Should not raise

    @pytest.mark.asyncio
    async def test_shutdown_closes_session(self, manager: MCPManager):
        """Shutdown closes HTTP session if open."""
        mock_session = AsyncMock()
        mock_session.closed = False
        manager._http_session = mock_session
        await manager.shutdown()
        mock_session.close.assert_called_once()
        assert manager._http_session is None

    @patch("aiohttp.ClientSession")
    @pytest.mark.asyncio
    async def test_get_session_creates(self, mock_client_session, manager: MCPManager):
        """_get_session creates a new aiohttp session if none exists."""
        mock_session = MagicMock()
        mock_session.closed = False
        mock_client_session.return_value = mock_session
        session = await manager._get_session()
        assert session is mock_session
        mock_client_session.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# BUILTIN_SERVERS Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuiltinServers:
    """Tests for core/mcp/builtin_servers.py."""

    def test_builtin_servers_defined(self):
        """BUILTIN_SERVERS has the expected 5 servers."""
        assert len(BUILTIN_SERVERS) == 5

    def test_builtin_servers_keys(self):
        """All expected server names are present."""
        expected = {"asim-memory", "asim-mesh", "asim-files", "asim-dharma", "asim-clones"}
        assert set(BUILTIN_SERVERS.keys()) == expected

    def test_builtin_servers_structure(self):
        """Each builtin server has url, description, builtin, enabled keys."""
        for name, config in BUILTIN_SERVERS.items():
            assert "url" in config, f"{name} missing url"
            assert "description" in config, f"{name} missing description"
            assert config.get("builtin") is True, f"{name} not marked builtin"
            assert config.get("enabled") is True, f"{name} not enabled"

    def test_builtin_server_urls(self):
        """All builtin server URLs are under localhost:9100/mcp/."""
        for name, config in BUILTIN_SERVERS.items():
            url = str(config["url"])
            assert url.startswith("http://localhost:9100/mcp/"), f"{name} has unexpected URL: {url}"

    def test_get_builtin_server_names(self):
        """get_builtin_server_names returns all 5 names."""
        names = get_builtin_server_names()
        assert len(names) == 5
        assert "asim-memory" in names
        assert "asim-clones" in names

    def test_get_builtin_server_config_found(self):
        """get_builtin_server_config returns config for valid name."""
        config = get_builtin_server_config("asim-mesh")
        assert config is not None
        assert config["url"] == "http://localhost:9100/mcp/mesh"

    def test_get_builtin_server_config_not_found(self):
        """get_builtin_server_config returns None for unknown name."""
        assert get_builtin_server_config("no-such-server") is None

    def test_is_builtin_server_true(self):
        """is_builtin_server returns True for known servers."""
        assert is_builtin_server("asim-memory") is True
        assert is_builtin_server("asim-dharma") is True

    def test_is_builtin_server_false(self):
        """is_builtin_server returns False for unknown servers."""
        assert is_builtin_server("custom-server") is False

    def test_register_builtin_servers(self):
        """register_builtin_servers registers all 5 servers on a manager."""
        manager = MCPManager()
        register_builtin_servers(manager)
        servers = manager.get_servers()
        assert len(servers) == 5
        assert "asim-memory" in servers
        assert "asim-clones" in servers

    def test_register_builtin_servers_idempotent(self):
        """register_builtin_servers handles already-registered servers."""
        manager = MCPManager()
        manager.register_server("asim-memory", "http://localhost:9100/mcp/memory")
        register_builtin_servers(manager)  # Should log and skip, not raise
        assert len(manager.get_servers()) == 5


# ═══════════════════════════════════════════════════════════════════════════════
# MCPServerAdapter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMCPServerAdapter:
    """Tests for MCPServerAdapter (without starting HTTP server)."""

    @pytest.fixture
    def adapter(self) -> MCPServerAdapter:
        return MCPServerAdapter(name="test-adapter",
                                listen_url="http://localhost:9200/mcp/test")

    def test_initial_state(self, adapter: MCPServerAdapter):
        """Adapter starts with no tools and not started."""
        assert adapter.name == "test-adapter"
        assert adapter.listen_url == "http://localhost:9200/mcp/test"
        assert adapter.list_tools() == []
        assert adapter.is_running is False

    # ── register_tool ──────────────────────────────────────────────────────

    def test_register_tool(self, adapter: MCPServerAdapter):
        """Register a tool on the adapter."""
        def my_handler(**kw):
            return {"result": "ok"}
        adapter.register_tool(name="my_tool", handler=my_handler,
                              description="My tool description",
                              parameters={"type": "object"})
        tool = adapter.get_tool("my_tool")
        assert tool is not None
        assert tool["name"] == "my_tool"
        assert tool["handler"] is my_handler

    def test_register_multiple_tools(self, adapter: MCPServerAdapter):
        """Multiple tools can be registered."""
        adapter.register_tool("a", lambda: None, "desc A", {})
        adapter.register_tool("b", lambda: None, "desc B", {})
        assert len(adapter.list_tools()) == 2

    # ── unregister_tool ────────────────────────────────────────────────────

    def test_unregister_tool(self, adapter: MCPServerAdapter):
        """Unregister a tool."""
        adapter.register_tool("tmp", lambda: None, "tmp", {})
        assert adapter.unregister_tool("tmp") is True
        assert adapter.get_tool("tmp") is None

    def test_unregister_nonexistent(self, adapter: MCPServerAdapter):
        """Unregistering a nonexistent tool returns False."""
        assert adapter.unregister_tool("ghost") is False

    # ── get_tool ───────────────────────────────────────────────────────────

    def test_get_tool_returns_copy_or_ref(self, adapter: MCPServerAdapter):
        """Getting a registered tool returns its definition."""
        adapter.register_tool("my_tool", lambda: None, "desc", {})
        tool = adapter.get_tool("my_tool")
        assert tool["name"] == "my_tool"
        assert tool["description"] == "desc"

    # ── list_tools ─────────────────────────────────────────────────────────

    def test_list_tools_format(self, adapter: MCPServerAdapter):
        """list_tools returns tools without handler function."""
        adapter.register_tool("safe_tool", lambda: None, "safe desc",
                              {"type": "object"})
        listed = adapter.list_tools()
        assert len(listed) == 1
        assert listed[0]["name"] == "safe_tool"
        assert "handler" not in listed[0]  # Handler must be excluded

    # ── handle_tools_list ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, adapter: MCPServerAdapter):
        """handle_tools_list returns MCP-format tool list."""
        adapter.register_tool("t1", lambda: None, "desc1", {"type": "object"})
        result = await adapter.handle_tools_list({})
        assert "result" in result
        assert "tools" in result["result"]
        tools = result["result"]["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "t1"

    @pytest.mark.asyncio
    async def test_handle_tools_list_empty(self, adapter: MCPServerAdapter):
        """handle_tools_list with no tools returns empty list."""
        result = await adapter.handle_tools_list({})
        assert result["result"]["tools"] == []

    # ── handle_tools_call ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_handle_tools_call_sync_handler(self, adapter: MCPServerAdapter):
        """handle_tools_call invokes a synchronous handler."""
        def sync_handler(**kw):
            return {"echo": kw.get("msg", "")}

        adapter.register_tool("echo", sync_handler, "Echo tool",
                              {"type": "object", "properties": {"msg": {"type": "string"}}})
        request = {
            "params": {
                "name": "echo",
                "arguments": {"msg": "hello"},
            }
        }
        result = await adapter.handle_tools_call(request)
        assert "result" in result
        assert result["result"]["content"] == {"echo": "hello"}

    @pytest.mark.asyncio
    async def test_handle_tools_call_async_handler(self, adapter: MCPServerAdapter):
        """handle_tools_call invokes an async handler."""
        async def async_handler(**kw):
            return {"result": "async_ok"}

        adapter.register_tool("async_tool", async_handler, "Async tool", {})
        request = {
            "params": {
                "name": "async_tool",
                "arguments": {},
            }
        }
        result = await adapter.handle_tools_call(request)
        assert result["result"]["content"] == {"result": "async_ok"}

    @pytest.mark.asyncio
    async def test_handle_tools_call_unknown_tool(self, adapter: MCPServerAdapter):
        """handle_tools_call with unknown tool returns error."""
        request = {
            "params": {
                "name": "no_such_tool",
                "arguments": {},
            }
        }
        result = await adapter.handle_tools_call(request)
        assert "error" in result
        assert "Tool not found" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_tools_call_handler_error(self, adapter: MCPServerAdapter):
        """Handler exceptions are caught and returned as errors."""
        def broken_handler(**kw):
            raise ValueError("Handler crashed")

        adapter.register_tool("broken", broken_handler, "Broken tool", {})
        request = {
            "params": {
                "name": "broken",
                "arguments": {},
            }
        }
        result = await adapter.handle_tools_call(request)
        assert "error" in result
        assert "Handler crashed" in result["error"]["message"]

    # ── handle_initialize / handle_shutdown ────────────────────────────────

    @pytest.mark.asyncio
    async def test_handle_initialize(self, adapter: MCPServerAdapter):
        """handle_initialize returns protocol info."""
        result = await adapter.handle_initialize({"params": {}})
        assert "result" in result
        assert "protocolVersion" in result["result"]
        assert "capabilities" in result["result"]
        assert "serverInfo" in result["result"]

    @pytest.mark.asyncio
    async def test_handle_shutdown(self, adapter: MCPServerAdapter):
        """handle_shutdown returns success."""
        result = await adapter.handle_shutdown({})
        assert result == {"jsonrpc": "2.0", "id": 1, "result": None}

    # ── start / stop (unit-level, no actual HTTP) ──────────────────────────

    def test_is_running_initially_false(self, adapter: MCPServerAdapter):
        """Adapter is not running initially."""
        assert adapter.is_running is False

    @pytest.mark.asyncio
    async def test_get_stats(self, adapter: MCPServerAdapter):
        """get_stats returns adapter info."""
        adapter.register_tool("t1", lambda: None, "desc", {})
        stats = adapter.get_stats()
        assert stats["name"] == "test-adapter"
        assert stats["listen_url"] == "http://localhost:9200/mcp/test"
        assert stats["tools_registered"] == 1
        assert stats["running"] is False
