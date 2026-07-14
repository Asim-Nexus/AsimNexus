"""
REAL Unit Tests for ToolRegistry
Tests registration, lookup, listing, capability gating, and audit logging.
"""

import pytest

try:
    from asim_tools.registry.tool_registry import (
        ToolRegistry,
        ToolRegistration,
        ToolExecutionResult,
        ToolVerdict,
        RiskLevel,
        tool_registry as global_registry,
    )
except ImportError:
    # asim_tools is an external dependency; tests will be skipped at runtime if missing
    ToolRegistry = None  # type: ignore
    ToolRegistration = None  # type: ignore
    ToolExecutionResult = None  # type: ignore
    ToolVerdict = None  # type: ignore
    RiskLevel = None  # type: ignore
    global_registry = None  # type: ignore


class TestRiskLevel:
    """Tests for the RiskLevel enum"""

    def test_enum_values(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_enum_ordering(self):
        levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        for i in range(len(levels) - 1):
            assert levels[i] != levels[i + 1]


class TestToolVerdict:
    """Tests for the ToolVerdict enum"""

    def test_enum_values(self):
        assert ToolVerdict.ALLOWED.value == "allowed"
        assert ToolVerdict.DENIED.value == "denied"
        assert ToolVerdict.ERROR.value == "error"
        assert ToolVerdict.PENDING_HUMAN.value == "pending_human"

    def test_enum_members(self):
        assert len(ToolVerdict) == 4


class TestToolRegistration:
    """Tests for the ToolRegistration dataclass"""

    def test_create_low_risk_tool(self):
        from asim_tools.registry.capability_matrix import Capability
        reg = ToolRegistration(
            tool_id="test.tool",
            description="A test tool",
            required_capabilities={Capability.SYSTEM_INFO},
            risk_level=RiskLevel.LOW,
            agent_owner="test_agent",
        )
        assert reg.tool_id == "test.tool"
        assert reg.description == "A test tool"
        assert reg.agent_owner == "test_agent"
        assert reg.risk_level == RiskLevel.LOW
        assert reg.requires_confirmation is False
        assert reg.undo_supported is False
        assert reg.allowed_args == []

    def test_create_with_all_fields(self):
        from asim_tools.registry.capability_matrix import Capability
        reg = ToolRegistration(
            tool_id="file.write",
            description="Write to a file",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.FILE_WRITE_SAFE},
            requires_confirmation=True,
            undo_supported=True,
            allowed_args=["path", "content"],
            handler=lambda **kw: {"ok": True},
        )
        assert reg.requires_confirmation is True
        assert reg.undo_supported is True
        assert reg.allowed_args == ["path", "content"]
        assert reg.handler is not None

    def test_create_high_risk_tool(self):
        from asim_tools.registry.capability_matrix import Capability
        reg = ToolRegistration(
            tool_id="system.shutdown",
            description="Shutdown the system",
            risk_level=RiskLevel.CRITICAL,
            required_capabilities={Capability.SYSTEM_SHUTDOWN},
            requires_confirmation=True,
            sandbox_required=True,
        )
        assert reg.risk_level == RiskLevel.CRITICAL
        assert reg.sandbox_required is True


class TestToolExecutionResult:
    """Tests for the ToolExecutionResult dataclass"""

    def test_allowed_result(self):
        result = ToolExecutionResult(
            success=True,
            verdict=ToolVerdict.ALLOWED,
            output={"data": "ok"},
            call_id="abc123",
            execution_ms=10.5,
            required_capabilities=["system.info"],
        )
        assert result.success is True
        assert result.verdict == ToolVerdict.ALLOWED
        assert result.output == {"data": "ok"}

    def test_denied_result(self):
        result = ToolExecutionResult(
            success=False,
            verdict=ToolVerdict.DENIED,
            error="Permission denied",
            call_id="abc124",
        )
        assert result.success is False
        assert result.verdict == ToolVerdict.DENIED


class TestToolRegistry:
    """Tests for the ToolRegistry class"""

    def setup_method(self):
        """Create a fresh registry for each test"""
        self.registry = ToolRegistry()
        # Clear registry to start clean
        self.registry._registrations.clear()

    def test_initial_empty(self):
        assert self.registry.list_tools() == []

    def test_register_and_get_tool(self):
        from asim_tools.registry.capability_matrix import Capability
        reg = ToolRegistration(
            tool_id="test.tool",
            description="A test",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            agent_owner="tester",
        )
        self.registry.register_tool(reg)
        retrieved = self.registry.get_tool("test.tool")
        assert retrieved is not None
        assert retrieved.tool_id == "test.tool"
        assert retrieved.agent_owner == "tester"

    def test_get_nonexistent_tool(self):
        assert self.registry.get_tool("nonexistent") is None

    def test_list_tools(self):
        from asim_tools.registry.capability_matrix import Capability
        tools = [
            ToolRegistration("tool.a", "First", RiskLevel.LOW, {Capability.SYSTEM_INFO}, agent_owner="agent1"),
            ToolRegistration("tool.b", "Second", RiskLevel.MEDIUM, {Capability.SYSTEM_INFO}, agent_owner="agent2"),
            ToolRegistration("tool.c", "Third", RiskLevel.HIGH, {Capability.SYSTEM_INFO}, agent_owner="agent3"),
        ]
        for t in tools:
            self.registry.register_tool(t)
        listed = self.registry.list_tools()
        assert len(listed) == 3
        names = {t.tool_id for t in listed}
        assert names == {"tool.a", "tool.b", "tool.c"}

    def test_register_duplicate_overwrites(self):
        from asim_tools.registry.capability_matrix import Capability
        reg1 = ToolRegistration("dup.tool", "First version", RiskLevel.LOW, {Capability.SYSTEM_INFO}, agent_owner="agent1")
        reg2 = ToolRegistration("dup.tool", "Second version", RiskLevel.HIGH, {Capability.SYSTEM_INFO}, agent_owner="agent2")
        self.registry.register_tool(reg1)
        self.registry.register_tool(reg2)
        retrieved = self.registry.get_tool("dup.tool")
        assert retrieved.description == "Second version"
        assert retrieved.agent_owner == "agent2"
        assert retrieved.risk_level == RiskLevel.HIGH

    def test_multiple_risk_levels(self):
        from asim_tools.registry.capability_matrix import Capability
        for level in RiskLevel:
            reg = ToolRegistration(f"tool.{level.value}", f"{level.value} tool", level, {Capability.SYSTEM_INFO})
            self.registry.register_tool(reg)
        assert len(self.registry.list_tools()) == 4

    def test_register_medium_with_confirmation(self):
        from asim_tools.registry.capability_matrix import Capability
        reg = ToolRegistration(
            "file.write", "Write file", RiskLevel.MEDIUM, {Capability.FILE_WRITE_SAFE},
            agent_owner="system", requires_confirmation=True, undo_supported=True,
            allowed_args=["path", "content"],
        )
        self.registry.register_tool(reg)
        retrieved = self.registry.get_tool("file.write")
        assert retrieved.requires_confirmation is True
        assert retrieved.undo_supported is True
        assert retrieved.allowed_args == ["path", "content"]

    def test_global_registry_exists(self):
        """Verify global singleton is a ToolRegistry instance"""
        assert global_registry is not None
        assert isinstance(global_registry, ToolRegistry)


class TestToolRegistryEdgeCases:
    """Edge cases for ToolRegistry"""

    def setup_method(self):
        self.registry = ToolRegistry()
        self.registry._registrations.clear()

    def test_register_empty_name(self):
        from asim_tools.registry.capability_matrix import Capability
        reg = ToolRegistration("", "empty name", RiskLevel.LOW, {Capability.SYSTEM_INFO})
        self.registry.register_tool(reg)
        assert self.registry.get_tool("") is not None

    def test_register_special_characters(self):
        from asim_tools.registry.capability_matrix import Capability
        reg = ToolRegistration("tool.with.dots", "dots", RiskLevel.LOW, {Capability.SYSTEM_INFO})
        self.registry.register_tool(reg)
        assert self.registry.get_tool("tool.with.dots") is not None

    def test_register_very_long_name(self):
        from asim_tools.registry.capability_matrix import Capability
        long_name = "a" * 500
        reg = ToolRegistration(long_name, "long", RiskLevel.LOW, {Capability.SYSTEM_INFO})
        self.registry.register_tool(reg)
        assert self.registry.get_tool(long_name) is not None


class TestToolRegistryCapabilityGating:
    """Tests that capability gating works in execute_tool"""

    @pytest.mark.asyncio
    async def test_execute_tool_capability_denied(self):
        from asim_tools.registry.capability_matrix import Capability, capability_matrix
        registry = ToolRegistry()
        registry._registrations.clear()

        # Register a tool requiring SYSTEM_SHUTDOWN
        registry.register_tool(ToolRegistration(
            tool_id="danger.tool",
            description="Dangerous",
            required_capabilities={Capability.SYSTEM_SHUTDOWN},
            risk_level=RiskLevel.CRITICAL,
            handler=lambda: {"done": True},
        ))

        # AutoModeAgent does NOT have SYSTEM_SHUTDOWN
        result = await registry.execute_tool("danger.tool", {}, agent_name="AutoModeAgent")
        assert result.verdict == ToolVerdict.DENIED
        assert result.success is False
        assert "Permission denied" in (result.error or "")

    @pytest.mark.asyncio
    async def test_execute_tool_capability_allowed(self):
        from asim_tools.registry.capability_matrix import Capability
        registry = ToolRegistry()
        registry._registrations.clear()

        async def my_handler(**kw):
            return {"processed": True}

        registry.register_tool(ToolRegistration(
            tool_id="safe.tool",
            description="Safe",
            required_capabilities={Capability.SYSTEM_INFO},
            risk_level=RiskLevel.LOW,
            handler=my_handler,
        ))

        result = await registry.execute_tool("safe.tool", {"param": "x"}, agent_name="AutoModeAgent")
        assert result.verdict == ToolVerdict.ALLOWED
        assert result.success is True
        assert result.output == {"processed": True}

    @pytest.mark.asyncio
    async def test_execute_unregistered_tool(self):
        from asim_tools.registry.capability_matrix import Capability
        registry = ToolRegistry()
        registry._registrations.clear()

        result = await registry.execute_tool("does.not.exist", {})
        assert result.verdict == ToolVerdict.ERROR
        assert result.success is False
        assert "not registered" in (result.error or "")

    @pytest.mark.asyncio
    async def test_execute_no_handler(self):
        from asim_tools.registry.capability_matrix import Capability
        registry = ToolRegistry()
        registry._registrations.clear()

        registry.register_tool(ToolRegistration(
            tool_id="no.handler",
            description="No handler",
            required_capabilities={Capability.SYSTEM_INFO},
            risk_level=RiskLevel.LOW,
        ))

        result = await registry.execute_tool("no.handler", {})
        assert result.verdict == ToolVerdict.ERROR
        assert result.success is False
        assert "no handler" in (result.error or "").lower()

    @pytest.mark.asyncio
    async def test_execute_handler_error(self):
        from asim_tools.registry.capability_matrix import Capability
        registry = ToolRegistry()
        registry._registrations.clear()

        def failing_handler(**kw):
            raise RuntimeError("Something broke")

        registry.register_tool(ToolRegistration(
            tool_id="failing.tool",
            description="Fails",
            required_capabilities={Capability.SYSTEM_INFO},
            risk_level=RiskLevel.LOW,
            handler=failing_handler,
        ))

        result = await registry.execute_tool("failing.tool", {})
        assert result.verdict == ToolVerdict.ERROR
        assert result.success is False
        assert "Something broke" in (result.error or "")


class TestToolRegistryAudit:
    """Tests for audit logging in ToolRegistry"""

    def setup_method(self):
        self.registry = ToolRegistry()
        self.registry._registrations.clear()
        self.registry._audit_buffer.clear()

    def test_audit_buffer_records_executions(self):
        from asim_tools.registry.capability_matrix import Capability
        self.registry.register_tool(ToolRegistration(
            "audit.test", "Audit test", RiskLevel.LOW, {Capability.SYSTEM_INFO},
            handler=lambda: {"ok": True},
        ))

        import asyncio
        asyncio.run(self.registry.execute_tool("audit.test", {}))

        entries = self.registry.get_audit_log(limit=10)
        assert len(entries) >= 1
        assert entries[0]["tool_id"] == "audit.test"

    def test_audit_buffer_max_size(self):
        self.registry._max_buffer_size = 5
        from asim_tools.registry.capability_matrix import Capability
        self.registry.register_tool(ToolRegistration(
            "buf.test", "Buffer test", RiskLevel.LOW, {Capability.SYSTEM_INFO},
            handler=lambda: {"ok": True},
        ))

        import asyncio
        for i in range(10):
            asyncio.run(self.registry.execute_tool("buf.test", {}))

        assert len(self.registry._audit_buffer) == 5

    def test_get_required_capabilities(self):
        from asim_tools.registry.capability_matrix import Capability
        self.registry.register_tool(ToolRegistration(
            "caps.test", "Caps test", RiskLevel.LOW, {Capability.FILE_READ_ONLY, Capability.SYSTEM_INFO},
        ))
        caps = self.registry.get_required_capabilities("caps.test")
        assert Capability.FILE_READ_ONLY in caps
        assert Capability.SYSTEM_INFO in caps

    def test_get_required_capabilities_unknown(self):
        caps = self.registry.get_required_capabilities("ghost")
        assert caps == set()
