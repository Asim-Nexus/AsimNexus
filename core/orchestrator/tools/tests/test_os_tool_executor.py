"""
Real pytest tests for OSToolExecutor — the capability-gated OS Control orchestrator
Tests the actual implementation which delegates to ToolRegistry.execute_tool().
"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import asdict
from pathlib import Path


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_registry():
    """Create a mock ToolRegistry with predefined tools"""
    from asim_tools.registry.tool_registry import ToolRegistry, ToolRegistration, RiskLevel
    from asim_tools.registry.capability_matrix import Capability
    
    registry = ToolRegistry()
    # Clear any pre-registered tools
    registry._registrations.clear()
    
    # Register tools that mirror the actual openclaw tool set
    registry.register_tool(ToolRegistration(
        tool_id="file.list", description="List files",
        risk_level=RiskLevel.LOW,
        required_capabilities={Capability.FILE_READ_ONLY},
        handler=lambda path=".", show_hidden=False: {"success": True, "files": []},
        allowed_args=["path", "show_hidden"],
    ))
    registry.register_tool(ToolRegistration(
        tool_id="file.read", description="Read file",
        risk_level=RiskLevel.LOW,
        required_capabilities={Capability.FILE_READ_ONLY},
        handler=lambda path=".", max_lines=1000: {"success": True, "content": ""},
        allowed_args=["path", "max_lines"],
    ))
    registry.register_tool(ToolRegistration(
        tool_id="file.write", description="Write file",
        risk_level=RiskLevel.MEDIUM,
        required_capabilities={Capability.FILE_WRITE_SAFE},
        requires_confirmation=True,
        undo_supported=True,
        handler=lambda path="", content="", backup=True: {"success": True},
        allowed_args=["path", "content", "backup"],
    ))
    registry.register_tool(ToolRegistration(
        tool_id="file.delete", description="Delete file",
        risk_level=RiskLevel.HIGH,
        required_capabilities={Capability.FILE_DELETE_SAFE},
        sandbox_required=True,
        requires_confirmation=True,
        handler=lambda path="", confirm=False: {"success": True},
        allowed_args=["path", "confirm"],
    ))
    registry.register_tool(ToolRegistration(
        tool_id="process.list", description="List processes",
        risk_level=RiskLevel.LOW,
        required_capabilities={Capability.PROCESS_INSPECT},
        handler=lambda filter_name="": {"success": True, "processes": []},
        allowed_args=["filter_name"],
    ))
    registry.register_tool(ToolRegistration(
        tool_id="system.cpu", description="Get CPU metrics",
        risk_level=RiskLevel.LOW,
        required_capabilities={Capability.SYSTEM_INFO},
        handler=lambda: {"percent": 0.0},
    ))
    registry.register_tool(ToolRegistration(
        tool_id="clipboard.read", description="Read clipboard",
        risk_level=RiskLevel.MEDIUM,
        required_capabilities={Capability.CLIPBOARD_ACCESS},
        requires_confirmation=True,
        handler=lambda user_id="", consent_if_needed=True: {"text": ""},
        allowed_args=["user_id", "consent_if_needed"],
    ))
    registry.register_tool(ToolRegistration(
        tool_id="notification.send", description="Send notification",
        risk_level=RiskLevel.LOW,
        required_capabilities={Capability.NOTIFICATION_SEND},
        handler=lambda title="", message="", urgency="normal", timeout_seconds=5: {"success": True},
        allowed_args=["title", "message", "urgency", "timeout_seconds"],
    ))
    return registry


@pytest.fixture
def mock_capability_matrix():
    """Create a mock CapabilityMatrix that allows most things"""
    from asim_tools.registry.capability_matrix import CapabilityMatrix
    matrix = MagicMock(spec=CapabilityMatrix)
    matrix.check_capability_allowed.return_value = (True, "Capability allowed")
    matrix.requires_human_confirmation.return_value = False
    matrix.requires_sandbox.return_value = False
    matrix.get_agent_risk_level.return_value = "low"
    return matrix


@pytest.fixture
def executor(mock_registry, mock_capability_matrix, tmp_path):
    """Create an OSToolExecutor with mocked dependencies"""
    from asim_tools.registry.os_tool_executor import OSToolExecutor
    audit_path = tmp_path / "audit.jsonl"
    ex = OSToolExecutor(
        tool_registry=mock_registry,
        capability_matrix=mock_capability_matrix,
        audit_path=audit_path,
    )
    return ex


# ── Test ToolVerdict Enum ──────────────────────────────────────────────────

class TestToolVerdict:
    """Tests for the ToolVerdict enum"""

    def test_enum_values(self):
        from asim_tools.registry.tool_registry import ToolVerdict
        assert ToolVerdict.ALLOWED.value == "allowed"
        assert ToolVerdict.DENIED.value == "denied"
        assert ToolVerdict.PENDING_HUMAN.value == "pending_human"
        assert ToolVerdict.ERROR.value == "error"

    def test_enum_members(self):
        from asim_tools.registry.tool_registry import ToolVerdict
        assert len(ToolVerdict) == 4


# ── Test ToolCallRecord Dataclass ──────────────────────────────────────────

class TestToolCallRecord:
    """Tests for the ToolCallRecord dataclass"""

    def test_create_record(self):
        from asim_tools.registry.os_tool_executor import ToolCallRecord
        record = ToolCallRecord(
            call_id="abc123",
            tool_name="file.list",
            agent_name="AutoModeAgent",
            user_id="test_user",
            verdict="allowed",
            risk_level="low",
            parameters_safe='{"path": "."}',
            output_hash="abc123def456",
            execution_ms=12.34,
            timestamp="2025-01-01T00:00:00+00:00",
        )
        assert record.call_id == "abc123"
        assert record.tool_name == "file.list"
        assert record.verdict == "allowed"
        assert record.error == ""

    def test_create_record_with_error(self):
        from asim_tools.registry.os_tool_executor import ToolCallRecord
        record = ToolCallRecord(
            call_id="xyz789",
            tool_name="file.write",
            agent_name="AutoModeAgent",
            user_id="guest",
            verdict="error",
            risk_level="medium",
            parameters_safe="{}",
            output_hash="",
            execution_ms=0,
            timestamp="2025-01-01T00:00:00+00:00",
            error="Permission denied",
            reason="No capability",
        )
        assert record.error == "Permission denied"
        assert record.reason == "No capability"


# ── Test OSToolExecutor Init ───────────────────────────────────────────────

class TestOSToolExecutorInit:
    """Tests for OSToolExecutor initialization"""

    def test_init_with_defaults(self):
        """Init with no args should use global singletons"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        assert ex.tool_registry is not None
        assert ex.capability_matrix is not None

    def test_init_with_custom_deps(self, mock_registry, mock_capability_matrix, tmp_path):
        """Init with custom deps should use those"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        audit_path = tmp_path / "test_audit.jsonl"
        ex = OSToolExecutor(
            tool_registry=mock_registry,
            capability_matrix=mock_capability_matrix,
            audit_path=audit_path,
        )
        assert ex.tool_registry is mock_registry
        assert ex.capability_matrix is mock_capability_matrix
        assert ex.audit_path == audit_path
        assert audit_path.parent.exists()

    def test_init_creates_audit_dir(self, tmp_path):
        """Init should create parent dir for audit path"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        deep_path = tmp_path / "deep" / "nested" / "audit.jsonl"
        ex = OSToolExecutor(audit_path=deep_path)
        assert deep_path.parent.exists()

    def test_init_registers_openclaw_tools(self):
        """Init should register all 20 openclaw tools"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        tools = ex.tool_registry.list_tools()
        tool_names = {t.tool_id for t in tools}
        expected = {
            "file.list", "file.read", "file.write", "file.copy", "file.move",
            "file.delete", "file.info",
            "process.list", "process.start", "process.close",
            "system.cpu", "system.memory", "system.disk", "system.network",
            "system.battery", "system.info", "system.all",
            "clipboard.read", "clipboard.write",
            "notification.send",
        }
        assert expected.issubset(tool_names)
        assert len(tool_names) >= 20


# ── Test Capability Mapping ────────────────────────────────────────────────

class TestOSToolExecutorCapabilityMapping:
    """Tests for get_capability_for_tool"""

    def test_get_capability_for_known_tool(self):
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        from asim_tools.registry.capability_matrix import Capability
        ex = OSToolExecutor()
        cap = ex.get_capability_for_tool("file.list")
        assert cap == Capability.FILE_READ_ONLY

    def test_get_capability_for_unknown_tool(self):
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        cap = OSToolExecutor().get_capability_for_tool("nonexistent")
        assert cap is None


# ── Test Permission Checks ─────────────────────────────────────────────────

class TestOSToolExecutorPermission:
    """Tests for check_tool_permission"""

    def test_check_permission_allowed(self, executor):
        """Known tool with allowed capability should pass"""
        allowed, reason = executor.check_tool_permission("file.list", "AutoModeAgent")
        assert allowed is True
        assert reason == "allowed"

    def test_check_permission_not_registered(self, executor):
        """Unknown tool should be denied"""
        allowed, reason = executor.check_tool_permission("nonexistent", "AutoModeAgent")
        assert allowed is False
        assert "not registered" in reason.lower()

    def test_check_permission_denied_by_matrix(self, executor, mock_capability_matrix):
        """Tool that capability matrix denies should be denied"""
        mock_capability_matrix.check_capability_allowed.return_value = (False, "Not allowed for this agent")

        allowed, reason = executor.check_tool_permission("file.list", "RestrictedAgent")
        assert allowed is False
        assert "denied" in reason.lower()


# ── Test Human Confirmation ────────────────────────────────────────────────

class TestOSToolExecutorHumanConfirmation:
    """Tests for requires_human_confirmation"""

    def test_requires_confirmation_from_metadata(self):
        """Tool with requires_confirmation=True should require human"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        # file.write requires confirmation per metadata
        assert ex.requires_human_confirmation("file.write") is True

    def test_not_requires_confirmation(self):
        """Tool with requires_confirmation=False should not require human"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        # file.list does not require confirmation per metadata
        assert ex.requires_human_confirmation("file.list") is False

    def test_unknown_tool_requires_confirmation(self):
        """Unknown tool should default to requiring confirmation"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        assert ex.requires_human_confirmation("nonexistent") is True


# ── Test Sandbox Requirement ───────────────────────────────────────────────

class TestOSToolExecutorSandbox:
    """Tests for requires_sandbox"""

    def test_sandbox_not_required_for_low_risk(self):
        """Low risk tool should not require sandbox"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        assert ex.requires_sandbox("file.list") is False

    def test_sandbox_required_for_high_risk(self):
        """High risk tool with sandbox_required=True should require sandbox"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        # file.delete has sandbox_required=True
        assert ex.requires_sandbox("file.delete") is True

    def test_sandbox_not_required_for_unknown_tool(self):
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        assert ex.requires_sandbox("nonexistent") is False


# ── Test Execute Flow ──────────────────────────────────────────────────────

class TestOSToolExecutorExecute:
    """Tests for the main execute method"""

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, executor):
        """Execute an unregistered tool should error"""
        result = await executor.execute("nonexistent", {})
        assert result["verdict"] == "denied"
        assert "not registered" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_permission_denied(self, executor, mock_capability_matrix):
        """Execute a tool without permission should be denied"""
        mock_capability_matrix.check_capability_allowed.return_value = (False, "Not allowed")

        result = await executor.execute("file.list", {}, agent_name="RestrictedAgent")
        assert result["verdict"] == "denied"
        assert "permission denied" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_pending_human(self, executor, mock_capability_matrix):
        """Execute a tool that requires human confirmation should pend"""
        mock_capability_matrix.requires_human_confirmation.return_value = True

        result = await executor.execute("file.list", {"path": "."})
        assert result["verdict"] == "pending_human"
        assert result.get("requires_human") is True
        assert "call_id" in result

    @pytest.mark.asyncio
    async def test_execute_success(self, executor):
        """Execute a tool with all checks passing should succeed"""
        result = await executor.execute("file.list", {"path": "."})
        assert result["verdict"] == "allowed"
        assert "output" in result
        assert "execution_ms" in result
        assert result["execution_ms"] >= 0

    @pytest.mark.asyncio
    async def test_execute_handler_error(self, mock_registry, executor):
        """Execute a handler that raises should result in error"""
        # Replace handler with a failing one
        def failing_handler(**kw):
            raise RuntimeError("Something went wrong")
        mock_registry._registrations["file.list"].handler = failing_handler

        result = await executor.execute("file.list", {"path": "."})
        assert result["verdict"] == "error"
        assert "Something went wrong" in result["error"]


# ── Test Approve / Reject Flow ─────────────────────────────────────────────

class TestOSToolExecutorApproveReject:
    """Tests for human confirmation approve/reject"""

    @pytest.mark.asyncio
    async def test_approve_pending_call(self, executor, mock_capability_matrix):
        """Approving a pending call should execute the tool"""
        mock_capability_matrix.requires_human_confirmation.return_value = True

        # First, execute to create a pending call
        pending = await executor.execute("file.list", {"path": "."})
        call_id = pending["call_id"]

        # Then approve it
        result = await executor.approve(call_id, "human1")
        assert result["verdict"] == "allowed"

    @pytest.mark.asyncio
    async def test_approve_nonexistent_call(self, executor):
        """Approving a nonexistent call should error"""
        result = await executor.approve("nonexistent", "human1")
        assert result["verdict"] == "error"
        assert "not found" in result["error"].lower()

    def test_reject_pending_call(self, executor):
        """Rejecting a pending call should deny it"""
        from asim_tools.registry.os_tool_executor import ToolCallRecord

        record = ToolCallRecord(
            call_id="test_call_1",
            tool_name="file.write",
            agent_name="AutoModeAgent",
            user_id="guest",
            verdict="pending_human",
            risk_level="medium",
            parameters_safe=json.dumps({"path": "/tmp/test.txt"}),
            output_hash="",
            execution_ms=0,
            timestamp="2025-01-01T00:00:00+00:00",
        )
        executor._pending_confirmations["test_call_1"] = record

        result = executor.reject("test_call_1", "human1")
        assert result["verdict"] == "denied"
        assert "rejected by human" in result["error"].lower()
        assert "test_call_1" not in executor._pending_confirmations

    def test_reject_nonexistent_call(self, executor):
        """Rejecting a nonexistent call should error"""
        result = executor.reject("nonexistent", "human1")
        assert result["verdict"] == "error"
        assert "not found" in result["error"].lower()

    def test_pending_calls_list(self, executor):
        """List pending calls"""
        assert executor.pending_calls() == []

    def test_pending_calls_with_user_filter(self, executor):
        """Filter pending calls by user"""
        from asim_tools.registry.os_tool_executor import ToolCallRecord
        executor._pending_confirmations["call1"] = ToolCallRecord(
            call_id="call1", tool_name="file.write", agent_name="agent1",
            user_id="user1", verdict="pending_human", risk_level="medium",
            parameters_safe="{}", output_hash="", execution_ms=0,
            timestamp="2025-01-01T00:00:00+00:00",
        )
        executor._pending_confirmations["call2"] = ToolCallRecord(
            call_id="call2", tool_name="file.delete", agent_name="agent2",
            user_id="user2", verdict="pending_human", risk_level="high",
            parameters_safe="{}", output_hash="", execution_ms=0,
            timestamp="2025-01-01T00:00:00+00:00",
        )

        user1_calls = executor.pending_calls(user_id="user1")
        assert len(user1_calls) == 1
        assert user1_calls[0]["call_id"] == "call1"

        all_calls = executor.pending_calls()
        assert len(all_calls) == 2


# ── Test Audit Log ─────────────────────────────────────────────────────────

class TestOSToolExecutorAudit:
    """Tests for audit logging"""

    def test_audit_records_to_buffer(self, executor):
        """_local_audit should add record to in-memory buffer"""
        from asim_tools.registry.os_tool_executor import ToolCallRecord
        record = ToolCallRecord(
            call_id="audit_1", tool_name="file.list", agent_name="agent",
            user_id="user", verdict="allowed", risk_level="low",
            parameters_safe="{}", output_hash="abc", execution_ms=5.0,
            timestamp="2025-01-01T00:00:00+00:00",
        )
        executor._local_audit(record)
        assert len(executor._audit_buffer) == 1
        assert executor._audit_buffer[0].call_id == "audit_1"

    def test_audit_writes_to_file(self, executor, tmp_path):
        """_local_audit should write record to JSONL file"""
        from asim_tools.registry.os_tool_executor import ToolCallRecord
        audit_path = tmp_path / "audit_test.jsonl"
        executor.audit_path = audit_path
        record = ToolCallRecord(
            call_id="audit_file", tool_name="file.list", agent_name="agent",
            user_id="user", verdict="allowed", risk_level="low",
            parameters_safe="{}", output_hash="abc", execution_ms=5.0,
            timestamp="2025-01-01T00:00:00+00:00",
        )
        executor._local_audit(record)
        assert audit_path.exists()
        content = audit_path.read_text(encoding="utf-8")
        assert "audit_file" in content
        assert "file.list" in content

    def test_audit_buffer_max_size(self, executor):
        """Audit buffer should respect max size"""
        from asim_tools.registry.os_tool_executor import ToolCallRecord
        executor._max_buffer_size = 5
        for i in range(10):
            record = ToolCallRecord(
                call_id=f"buf_{i}", tool_name="file.list", agent_name="agent",
                user_id="user", verdict="allowed", risk_level="low",
                parameters_safe="{}", output_hash="abc", execution_ms=5.0,
                timestamp="2025-01-01T00:00:00+00:00",
            )
            executor._local_audit(record)
        assert len(executor._audit_buffer) == 5
        assert executor._audit_buffer[0].call_id == "buf_5"
        assert executor._audit_buffer[-1].call_id == "buf_9"

    def test_get_audit_log(self, executor):
        """get_audit_log should return recent entries"""
        from asim_tools.registry.os_tool_executor import ToolCallRecord
        for i in range(5):
            executor._audit_buffer.append(ToolCallRecord(
                call_id=f"log_{i}", tool_name="file.list", agent_name="agent",
                user_id=f"user_{i % 2}", verdict="allowed", risk_level="low",
                parameters_safe="{}", output_hash="abc", execution_ms=5.0,
                timestamp="2025-01-01T00:00:00+00:00",
            ))

        all_logs = executor.get_audit_log(limit=10)
        assert len(all_logs) == 5

        user0_logs = executor.get_audit_log(limit=10, user_id="user_0")
        assert len(user0_logs) == 3  # user_0 has indices 0, 2, 4

        user1_logs = executor.get_audit_log(limit=10, user_id="user_1")
        assert len(user1_logs) == 2  # user_1 has indices 1, 3

    def test_get_audit_log_empty(self, executor):
        """get_audit_log should return empty list when no entries"""
        logs = executor.get_audit_log()
        assert logs == []


# ── Test Status ────────────────────────────────────────────────────────────

class TestOSToolExecutorStatus:
    """Tests for get_status"""

    def test_get_status(self):
        """get_status should return summary info"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        ex = OSToolExecutor()
        status = ex.get_status()
        assert "tools_registered" in status
        assert status["tools_registered"] >= 20
        assert "tools" in status
        assert "pending_approvals" in status
        assert "audit_entries" in status
        assert "audit_path" in status


# ── Test Safe Params ───────────────────────────────────────────────────────

class TestOSToolExecutorSafeParams:
    """Tests for _safe_params helper"""

    def test_safe_params_redacts_content(self):
        """_safe_params should redact 'content' and 'text' params"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        safe = OSToolExecutor._safe_params({"content": "secret data", "path": "/tmp/file.txt"})
        parsed = json.loads(safe)
        assert "REDACTED" in parsed["content"]
        assert parsed["path"] == "/tmp/file.txt"

    def test_safe_params_redacts_text(self):
        """_safe_params should redact 'text' parameter"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        safe = OSToolExecutor._safe_params({"text": "clipboard secret", "user_id": "guest"})
        parsed = json.loads(safe)
        assert "REDACTED" in parsed["text"]

    def test_safe_params_truncates_long_strings(self):
        """_safe_params should truncate strings over 500 chars"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        long_str = "x" * 1000
        safe = OSToolExecutor._safe_params({"path": long_str})
        parsed = json.loads(safe)
        assert len(parsed["path"]) < 500
        assert parsed["path"].endswith("...")

    def test_safe_params_preserves_short_values(self):
        """_safe_params should preserve short non-sensitive values"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        safe = OSToolExecutor._safe_params({"path": "/tmp/file.txt", "show_hidden": False})
        parsed = json.loads(safe)
        assert parsed["path"] == "/tmp/file.txt"
        assert parsed["show_hidden"] is False


# ── Test Hash Helper ───────────────────────────────────────────────────────

class TestOSToolExecutorHash:
    """Tests for _hash helper"""

    def test_hash_returns_hex_string(self):
        """_hash should return a hex string"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        result = OSToolExecutor._hash("test data")
        assert isinstance(result, str)
        assert len(result) == 16  # first 16 chars of SHA256
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_is_deterministic(self):
        """_hash should be deterministic for same input"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        assert OSToolExecutor._hash("data") == OSToolExecutor._hash("data")

    def test_hash_differs_for_different_input(self):
        """_hash should differ for different input"""
        from asim_tools.registry.os_tool_executor import OSToolExecutor
        assert OSToolExecutor._hash("data1") != OSToolExecutor._hash("data2")


# ── Test Global Singleton ──────────────────────────────────────────────────

class TestGetOSToolExecutor:
    """Tests for the get_os_tool_executor singleton"""

    def test_get_os_tool_executor_returns_instance(self):
        """get_os_tool_executor should return an OSToolExecutor"""
        from asim_tools.registry.os_tool_executor import get_os_tool_executor, OSToolExecutor
        ex = get_os_tool_executor()
        assert isinstance(ex, OSToolExecutor)

    def test_get_os_tool_executor_singleton(self):
        """get_os_tool_executor should return the same instance"""
        from asim_tools.registry.os_tool_executor import get_os_tool_executor
        ex1 = get_os_tool_executor()
        ex2 = get_os_tool_executor()
        assert ex1 is ex2
