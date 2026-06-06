#!/usr/bin/env python3
"""
REAL Integration Tests — OS Control Full Pipeline
=================================================
Validates the end-to-end flow:
  call_tool() → ToolRegistry → CapabilityMatrix → Sandbox → Execution → Audit

These tests use the **real** singleton instances, not mocks.
"""

import pytest
import pytest_asyncio
from os_control.os_control_bridge import call_tool, get_available_tools
from os_control.tool_registry import (
    tool_registry, ToolVerdict, ToolRegistration, RiskLevel,
)
from os_control.capability_matrix import Capability
from os_control.os_tool_executor import get_os_tool_executor


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def fresh_executor():
    """Ensure a clean singleton for each test.

    Clears the **executor's** registry (not just the global ``tool_registry``)
    because :func:`call_tool` routes through ``OSToolExecutor`` which holds
    its own ``_base_registry`` instance.
    """
    executor = get_os_tool_executor()
    executor._pending_confirmations.clear()
    executor._audit_buffer.clear()

    # Re-register openclaw tools on the executor's internal registry
    reg = executor.tool_registry
    reg._registrations.clear()
    reg._register_openclaw_tools()

    # Also re-register on the global tool_registry so direct-access tests
    # (e.g. TestCapabilityGate) work consistently.
    tool_registry._registrations.clear()
    tool_registry._register_openclaw_tools()

    return executor


# =============================================================================
# Helpers — register temporary tools
# =============================================================================

def _register_test_tool(
    tool_id: str = "test.danger.shutdown",
    caps: set = frozenset({Capability.SYSTEM_SHUTDOWN}),
    risk: RiskLevel = RiskLevel.CRITICAL,
    handler=None,
    requires_confirmation: bool = False,
    sandbox_required: bool = False,
    agent_name: str = "AutoModeAgent",
):
    """Register a temporary test tool on **both** registries so it works
    regardless of whether the test goes through ``call_tool()`` (executor)
    or ``tool_registry.execute_tool()``."""
    from os_control.os_tool_executor import get_os_tool_executor

    if handler is None:
        async def dummy_handler(**kw):
            return {"done": True}
        handler = dummy_handler

    tr = ToolRegistration(
        tool_id=tool_id,
        description=f"Test tool: {tool_id}",
        risk_level=risk,
        required_capabilities=set(caps),
        handler=handler,
        requires_confirmation=requires_confirmation,
        sandbox_required=sandbox_required,
    )

    # Register on both registries
    tool_registry.register_tool(tr)
    executor = get_os_tool_executor()
    executor.tool_registry.register_tool(tr)
    return tr


# =============================================================================
# Full Pipeline: call_tool() → Registry → CapabilityGate → Execution → Audit
# =============================================================================

class TestFullPipeline:
    """End-to-end tests exercising the complete OS Control pipeline."""

    @pytest.mark.asyncio
    async def test_call_tool_allow_low_risk(self):
        """A low-risk tool should be allowed for AutoModeAgent."""
        result = await call_tool("system.info", {}, agent_id="AutoModeAgent")
        assert result["success"] is True
        assert result["permission_denied"] is False
        assert result["verdict"] == ToolVerdict.ALLOWED.value
        assert result["audit_id"] != "error"

    @pytest.mark.asyncio
    async def test_call_tool_deny_high_risk_for_restricted_agent(self):
        """A tool requiring SYSTEM_SHUTDOWN should be denied for AutoModeAgent."""
        _register_test_tool(
            tool_id="test.shutdown.denied",
            caps={Capability.SYSTEM_SHUTDOWN},
            risk=RiskLevel.CRITICAL,
        )
        result = await call_tool(
            "test.shutdown.denied", {"reason": "test"},
            agent_id="AutoModeAgent",
        )
        assert result["success"] is False
        assert result["permission_denied"] is True
        assert result["verdict"] == ToolVerdict.DENIED.value
        assert "Permission denied" in (result.get("error") or "")

    @pytest.mark.asyncio
    async def test_call_tool_allow_all_for_asim_core(self):
        """ASIMCore has ALL capabilities — should allow SYSTEM_SHUTDOWN."""
        _register_test_tool(
            tool_id="test.shutdown.allowed",
            caps={Capability.SYSTEM_SHUTDOWN},
            risk=RiskLevel.CRITICAL,
        )
        result = await call_tool(
            "test.shutdown.allowed", {"reason": "test"},
            agent_id="ASIMCore",
        )
        # ASIMCore has SYSTEM_SHUTDOWN, but CRITICAL risk may pend for human
        assert result["verdict"] in (
            ToolVerdict.ALLOWED.value,
            ToolVerdict.PENDING_HUMAN.value,
        )

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self):
        """An unregistered tool returns 'denied' (not 'error') because the
        executor treats unknown tools as a permission denial."""
        result = await call_tool("does.not.exist", {}, agent_id="AutoModeAgent")
        assert result["success"] is False
        assert result["verdict"] == ToolVerdict.DENIED.value
        assert "not registered" in (result.get("error") or "").lower()

    @pytest.mark.asyncio
    async def test_call_tool_audit_record_created(self):
        """After execution, the audit trail should contain the record."""
        executor = get_os_tool_executor()
        before = len(executor.get_audit_log(limit=1000))

        await call_tool("system.info", {}, agent_id="AutoModeAgent")

        after = len(executor.get_audit_log(limit=1000))
        assert after >= before + 1, "Audit record should have been created"


# =============================================================================
# Capability Gating (ToolRegistry.execute_tool → CapabilityMatrix)
# =============================================================================

class TestCapabilityGate:
    """Verify that capability gating works end-to-end through the registry."""

    @pytest.mark.asyncio
    async def test_safe_tool_allowed(self):
        """Tool with SYSTEM_INFO capability should pass for AutoModeAgent."""
        result = await tool_registry.execute_tool(
            "system.info", {},
            agent_name="AutoModeAgent",
        )
        assert result.verdict == ToolVerdict.ALLOWED
        assert result.success is True

    @pytest.mark.asyncio
    async def test_dangerous_tool_denied(self):
        """Tool requiring SYSTEM_SHUTDOWN should be denied for AutoModeAgent."""
        _register_test_tool(
            tool_id="test.danger.denied",
            caps={Capability.SYSTEM_SHUTDOWN},
        )

        result = await tool_registry.execute_tool(
            "test.danger.denied", {},
            agent_name="AutoModeAgent",
        )
        assert result.verdict == ToolVerdict.DENIED
        assert result.success is False
        assert "Permission denied" in (result.error or "")

    @pytest.mark.asyncio
    async def test_dangerous_tool_allowed_for_asim_core(self):
        """ASIMCore should be able to execute SYSTEM_SHUTDOWN tools."""
        _register_test_tool(
            tool_id="test.danger.allowed",
            caps={Capability.SYSTEM_SHUTDOWN},
        )

        result = await tool_registry.execute_tool(
            "test.danger.allowed", {},
            agent_name="ASIMCore",
        )
        # ASIMCore has ALL capabilities, so it should be ALLOWED
        assert result.verdict == ToolVerdict.ALLOWED
        assert result.success is True

    @pytest.mark.asyncio
    async def test_multiple_capabilities_all_required(self):
        """Tool requiring multiple capabilities needs ALL of them."""
        _register_test_tool(
            tool_id="test.multi.cap",
            caps={Capability.FILE_READ_ONLY, Capability.SYSTEM_INFO},
            risk=RiskLevel.MEDIUM,
        )

        # AutoModeAgent has both FILE_READ_ONLY and SYSTEM_INFO
        result = await tool_registry.execute_tool(
            "test.multi.cap", {},
            agent_name="AutoModeAgent",
        )
        assert result.verdict == ToolVerdict.ALLOWED


# =============================================================================
# Human Confirmation Gate (OSToolExecutor → Human Approval)
# =============================================================================

class TestHumanConfirmationGate:
    """Verify the human confirmation flow for high-risk tools."""

    @pytest.mark.asyncio
    async def test_high_risk_tool_pends_for_human(self):
        """A CRITICAL risk tool that requires confirmation should pend."""
        executor = get_os_tool_executor()
        _register_test_tool(
            tool_id="test.needs.approval",
            caps={Capability.SYSTEM_INFO},        # AutoModeAgent has this
            risk=RiskLevel.HIGH,
            requires_confirmation=True,
        )

        result = await executor.execute(
            tool_name="test.needs.approval",
            parameters={},
            agent_name="AutoModeAgent",
            user_id="test_user",
        )
        assert result["verdict"] == ToolVerdict.PENDING_HUMAN.value

    @pytest.mark.asyncio
    async def test_approve_flow(self):
        """Human can approve a pending call and it executes."""
        executor = get_os_tool_executor()

        async def delayed_handler(**kw):
            return {"approved": True}

        _register_test_tool(
            tool_id="test.approve.me",
            caps={Capability.SYSTEM_INFO},
            risk=RiskLevel.HIGH,
            handler=delayed_handler,
            requires_confirmation=True,
        )

        # Execute — should pend
        result = await executor.execute(
            tool_name="test.approve.me",
            parameters={},
            agent_name="AutoModeAgent",
            user_id="test_user",
        )
        assert result["verdict"] == ToolVerdict.PENDING_HUMAN.value

        call_id = result["call_id"]
        assert call_id != "unknown"

        # Approve — returns the execution result directly
        approval = await executor.approve(call_id, approver_id="human_operator")
        # approve() delegates to _execute_tool(), so the response is a
        # standard execution result dict with tool_name / verdict / output
        assert approval.get("output", {}).get("approved") is True


# =============================================================================
# Available Tools Listing
# =============================================================================

class TestAvailableTools:
    """Verify get_available_tools returns correct metadata."""

    def test_available_tools_includes_openclaw_tools(self):
        """Should list all 20 openclaw-like tools plus any registered tools."""
        tools = get_available_tools()
        assert len(tools) >= 20

        tool_ids = {t["tool_id"] for t in tools}
        # Core tools that should exist
        assert "file.list" in tool_ids
        assert "file.read" in tool_ids
        assert "process.list" in tool_ids
        assert "system.info" in tool_ids
        assert "clipboard.read" in tool_ids
        assert "notification.send" in tool_ids

    def test_available_tools_have_required_fields(self):
        """Every tool entry must have all metadata fields."""
        tools = get_available_tools()
        for t in tools:
            assert "tool_id" in t
            assert "description" in t
            assert "risk_level" in t
            assert "required_capabilities" in t
            assert "requires_confirmation" in t
            assert isinstance(t["risk_level"], str)
            assert isinstance(t["required_capabilities"], list)
            assert isinstance(t["requires_confirmation"], bool)


# =============================================================================
# Audit Trail Verification
# =============================================================================

class TestAuditTrail:
    """Verify that audit logging works end-to-end."""

    @pytest.mark.asyncio
    async def test_audit_trail_after_execution(self):
        """After a tool executes, the audit buffer should contain the record."""
        executor = get_os_tool_executor()
        await call_tool("system.info", {}, agent_id="AutoModeAgent")

        log = executor.get_audit_log(limit=10)
        assert len(log) >= 1
        entry = log[-1]
        # ToolCallRecord uses tool_name, not tool_id
        assert entry["tool_name"] == "system.info"
        assert entry["verdict"] == ToolVerdict.ALLOWED.value
        assert "timestamp" in entry

    @pytest.mark.asyncio
    async def test_audit_trail_for_denied(self):
        """Denied tools should also appear in the audit trail."""
        executor = get_os_tool_executor()
        _register_test_tool(
            tool_id="test.deny.audit",
            caps={Capability.SYSTEM_SHUTDOWN},
            risk=RiskLevel.CRITICAL,
        )
        await call_tool(
            "test.deny.audit", {"reason": "test"},
            agent_id="AutoModeAgent",
        )

        log = executor.get_audit_log(limit=10)
        denied_entries = [e for e in log if e.get("tool_name") == "test.deny.audit"]
        assert len(denied_entries) >= 1
        assert denied_entries[-1]["verdict"] == ToolVerdict.DENIED.value

    def test_audit_log_empty_initially(self):
        """Fresh executor should have no audit entries (after clearing)."""
        executor = get_os_tool_executor()
        executor._audit_buffer.clear()
        log = executor.get_audit_log(limit=10)
        assert len(log) == 0


# =============================================================================
# OSToolExecutor Status
# =============================================================================

class TestExecutorStatus:
    """Verify executor status reporting."""

    def test_status_contains_key_fields(self):
        executor = get_os_tool_executor()
        status = executor.get_status()
        assert "tools_registered" in status
        assert "pending_approvals" in status
        assert "audit_entries" in status
        assert status["tools_registered"] >= 20
