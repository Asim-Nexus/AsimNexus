#!/usr/bin/env python3
"""
Tests for [`core/tools/veto_integration.py`](../../core/tools/veto_integration.py)
and [`core/tools/audit_integration.py`](../../core/tools/audit_integration.py).

Covers:
  - TOOL_SECURITY_MAP: mappings, counts by level
  - VetoIntegration: check_tool (secure/sensitive/dangerous/unknown), fail-open,
    fail-closed, veto_engine integration, constitution integration,
    get_security_level, set_veto_engine, set_constitution, set_fail_open
  - create_default_veto_hook: factory wiring
  - ToolAuditEntry: creation, to_dict, __post_init__
  - ToolAuditor: record, get_recent, get_by_user, get_by_tool,
    get_vetoed_calls, get_failed_calls, get_stats, clear
  - get_tool_auditor, reset_tool_auditor: singleton factory
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.tools.veto_integration import (
    TOOL_SECURITY_MAP,
    VetoIntegration,
    create_default_veto_hook,
)
from core.tools.audit_integration import (
    ToolAuditEntry,
    ToolAuditor,
    get_tool_auditor,
    reset_tool_auditor,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL_SECURITY_MAP Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolSecurityMap:
    """Tests for the TOOL_SECURITY_MAP constant."""

    def test_map_has_expected_tools(self):
        """All expected tools are mapped."""
        assert "execute_bash" in TOOL_SECURITY_MAP
        assert "execute_python" in TOOL_SECURITY_MAP
        assert "file_write" in TOOL_SECURITY_MAP
        assert "file_edit" in TOOL_SECURITY_MAP
        assert "file_upload" in TOOL_SECURITY_MAP
        assert "mesh_broadcast" in TOOL_SECURITY_MAP

    def test_total_mapped(self):
        """Total tools mapped: 6 dangerous + 6 sensitive + 12 secure = 24."""
        assert len(TOOL_SECURITY_MAP) == 24

    def test_secure_tools(self):
        """Secure tools are all informational."""
        secure_tools = {k for k, v in TOOL_SECURITY_MAP.items() if v == "secure"}
        expected_secure = {
            "read_file", "file_read", "file_list", "file_search",
            "web_scrape", "memory_recall", "code_analyze",
            "code_format", "code_explain", "mesh_discover", "mesh_status",
            "list_files",
        }
        assert secure_tools == expected_secure, f"Got {secure_tools}"
        assert len(secure_tools) == 12

    def test_sensitive_tools(self):
        """Sensitive tools require veto check."""
        sensitive_tools = {k for k, v in TOOL_SECURITY_MAP.items() if v == "sensitive"}
        expected_sensitive = {
            "memory_store", "memory_search", "web_search",
            "web_fetch", "code_review", "mesh_send",
        }
        assert sensitive_tools == expected_sensitive
        assert len(sensitive_tools) == 6

    def test_dangerous_tools(self):
        """Dangerous tools require veto + confirmation."""
        dangerous_tools = {k for k, v in TOOL_SECURITY_MAP.items() if v == "dangerous"}
        expected_dangerous = {
            "execute_bash", "execute_python", "file_write",
            "file_edit", "file_upload", "mesh_broadcast",
        }
        assert dangerous_tools == expected_dangerous
        assert len(dangerous_tools) == 6

    def test_unknown_tool_defaults_to_sensitive(self):
        """Unknown tools should default to 'sensitive'."""
        vi = VetoIntegration()
        level = vi.get_security_level("some_unknown_tool")
        assert level == "sensitive"


# ═══════════════════════════════════════════════════════════════════════════════
# VetoIntegration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestVetoIntegration:
    """Tests for VetoIntegration class."""

    @pytest.fixture
    def veto(self) -> VetoIntegration:
        return VetoIntegration()

    # ── check_tool — Secure tools ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_check_secure_allowed(self, veto: VetoIntegration):
        """Secure tools are always allowed (no veto check)."""
        result = await veto.check_tool("read_file", {"path": "/tmp/test"})
        assert result["allowed"] is True
        assert result["level"] == "secure"

    @pytest.mark.asyncio
    async def test_check_secure_list_files(self, veto: VetoIntegration):
        """list_files is secure and always allowed."""
        result = await veto.check_tool("list_files", {"directory": "/tmp"})
        assert result["allowed"] is True
        assert result["level"] == "secure"

    # ── check_tool — Sensitive tools (no engine = fail-open) ──────────────

    @pytest.mark.asyncio
    async def test_check_sensitive_no_engine_fail_open(self, veto: VetoIntegration):
        """Sensitive tool with no engine and fail_open=True is allowed."""
        result = await veto.check_tool("memory_store", {"key": "x", "value": "y"})
        assert result["allowed"] is True
        assert result["level"] == "sensitive"

    @pytest.mark.asyncio
    async def test_check_sensitive_no_engine_fail_closed(self):
        """Sensitive tool with no engine and fail_open=False is blocked."""
        veto = VetoIntegration()
        veto.set_fail_open(False)
        result = await veto.check_tool("memory_store", {"key": "x"})
        assert result["allowed"] is False
        assert "unavailable" in result["reason"].lower()

    # ── check_tool — Sensitive with veto engine ───────────────────────────

    @pytest.mark.asyncio
    async def test_check_sensitive_with_engine_allowed(self):
        """Sensitive tool with engine that allows is allowed."""
        mock_engine = MagicMock()
        mock_engine.check.return_value = MagicMock(allowed=True)

        veto = VetoIntegration(veto_engine=mock_engine)
        result = await veto.check_tool("memory_store", {"key": "x"})
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_sensitive_with_engine_blocked(self):
        """Sensitive tool with engine that blocks is blocked."""
        mock_result = MagicMock()
        mock_result.allowed = False
        mock_result.reason = "Not authorized"
        mock_result.level.name = "BLOCK"

        mock_engine = MagicMock()
        mock_engine.check.return_value = mock_result

        veto = VetoIntegration(veto_engine=mock_engine)
        result = await veto.check_tool("memory_store", {"key": "x"})
        assert result["allowed"] is False
        assert "Not authorized" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_sensitive_engine_crashes_fail_open(self):
        """Engine crash with fail_open=True allows the tool."""
        mock_engine = MagicMock()
        mock_engine.check.side_effect = RuntimeError("Engine down")

        veto = VetoIntegration(veto_engine=mock_engine)
        result = await veto.check_tool("web_search", {"query": "test"})
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_sensitive_engine_crashes_fail_closed(self):
        """Engine crash with fail_open=False blocks the tool."""
        mock_engine = MagicMock()
        mock_engine.check.side_effect = RuntimeError("Engine down")

        veto = VetoIntegration(veto_engine=mock_engine)
        veto.set_fail_open(False)
        result = await veto.check_tool("web_search", {"query": "test"})
        assert result["allowed"] is False
        assert "Engine down" in result["reason"]

    # ── check_tool — Dangerous tools ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_check_dangerous_both_pass(self):
        """Dangerous tool passes when both engine and constitution allow."""
        mock_engine = MagicMock()
        mock_engine.check.return_value = MagicMock(allowed=True)

        mock_constitution = MagicMock()
        mock_constitution.check_decision.return_value = MagicMock()
        mock_constitution.check_decision.return_value.verdict.name = "ALLOW"

        veto = VetoIntegration(veto_engine=mock_engine, constitution=mock_constitution)
        result = await veto.check_tool("execute_bash", {"command": "ls"})
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_dangerous_veto_blocks(self):
        """Dangerous tool blocked by veto engine (constitution not reached)."""
        mock_engine = MagicMock()
        mock_engine.check.return_value = MagicMock(allowed=False, reason="Veto denied",
                                                   level=MagicMock(name="BLOCK"))

        veto = VetoIntegration(veto_engine=mock_engine)
        veto.set_fail_open(False)  # Ensure engine result is honored
        result = await veto.check_tool("execute_bash", {"command": "rm -rf /"})
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_check_dangerous_constitution_blocks(self):
        """Dangerous tool blocked by constitution even if veto allows."""
        mock_engine = MagicMock()
        mock_engine.check.return_value = MagicMock(allowed=True)

        mock_constitution = MagicMock()
        mock_constitution.check_decision.return_value = MagicMock()
        mock_constitution.check_decision.return_value.verdict.name = "BLOCK"
        mock_constitution.check_decision.return_value.message = "Constitution says no"

        veto = VetoIntegration(veto_engine=mock_engine, constitution=mock_constitution)
        result = await veto.check_tool("execute_bash", {"command": "ls"})
        assert result["allowed"] is False
        assert "Constitution" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_dangerous_no_constitution(self):
        """Dangerous tool without constitution falls through to veto result."""
        mock_engine = MagicMock()
        mock_engine.check.return_value = MagicMock(allowed=True)

        veto = VetoIntegration(veto_engine=mock_engine, constitution=None)
        result = await veto.check_tool("execute_bash", {"command": "ls"})
        assert result["allowed"] is True

    # ── check_tool — Unknown tools ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_check_unknown_tool_default_sensitive(self, veto: VetoIntegration):
        """Unknown tool defaults to sensitive (fail-open = allowed)."""
        result = await veto.check_tool("unknown_tool_xyz", {})
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_unknown_tool_fail_closed(self):
        """Unknown tool with fail-closed and no engine is blocked."""
        veto = VetoIntegration()
        veto.set_fail_open(False)
        result = await veto.check_tool("mystery_tool", {})
        assert result["allowed"] is False

    # ── get_security_level ────────────────────────────────────────────────

    def test_get_security_level_dangerous(self, veto: VetoIntegration):
        assert veto.get_security_level("execute_bash") == "dangerous"
        assert veto.get_security_level("file_write") == "dangerous"

    def test_get_security_level_sensitive(self, veto: VetoIntegration):
        assert veto.get_security_level("memory_store") == "sensitive"
        assert veto.get_security_level("web_search") == "sensitive"

    def test_get_security_level_secure(self, veto: VetoIntegration):
        assert veto.get_security_level("read_file") == "secure"
        assert veto.get_security_level("file_read") == "secure"

    def test_get_security_level_unknown_default(self, veto: VetoIntegration):
        assert veto.get_security_level("nonexistent_tool") == "sensitive"

    # ── set_veto_engine / set_constitution / set_fail_open ────────────────

    def test_set_veto_engine(self, veto: VetoIntegration):
        """set_veto_engine stores the engine."""
        mock_engine = MagicMock()
        veto.set_veto_engine(mock_engine)
        assert veto._veto_engine is mock_engine

    def test_set_constitution(self, veto: VetoIntegration):
        """set_constitution stores the constitution."""
        mock_constitution = MagicMock()
        veto.set_constitution(mock_constitution)
        assert veto._constitution is mock_constitution

    def test_set_fail_open(self, veto: VetoIntegration):
        """set_fail_open toggles the flag."""
        assert veto._fail_open is True
        veto.set_fail_open(False)
        assert veto._fail_open is False
        veto.set_fail_open(True)
        assert veto._fail_open is True

    # ── _build_veto_message ───────────────────────────────────────────────

    def test_build_veto_message_basic(self, veto: VetoIntegration):
        """_build_veto_message formats tool name and args."""
        msg = veto._build_veto_message("execute_bash", {"command": "ls -la"})
        assert "Execute tool 'execute_bash'" in msg
        assert "command=ls -la" in msg

    def test_build_veto_message_skips_bytes(self, veto: VetoIntegration):
        """_build_veto_message skips binary arguments."""
        msg = veto._build_veto_message("write_file", {
            "path": "/tmp/test",
            "content": b"binary data",
        })
        assert "content=" not in msg  # bytes should be skipped
        assert "path=/tmp/test" in msg


# ═══════════════════════════════════════════════════════════════════════════════
# create_default_veto_hook Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateDefaultVetoHook:
    """Tests for create_default_veto_hook factory."""

    @pytest.mark.asyncio
    async def test_creates_callable(self):
        """Factory returns a callable."""
        hook = await create_default_veto_hook()
        assert callable(hook)

    @pytest.mark.asyncio
    async def test_returns_async_callable(self):
        """Returned callable is async and returns veto result dict."""
        hook = await create_default_veto_hook()
        result = await hook(tool_name="read_file", tool_args={}, user_id="test")
        assert isinstance(result, dict)
        assert "allowed" in result

    @pytest.mark.asyncio
    async def test_accepts_explicit_engine(self):
        """Factory accepts an explicit veto engine."""
        mock_engine = MagicMock()
        mock_engine.check.return_value = MagicMock(allowed=True)
        hook = await create_default_veto_hook(veto_engine=mock_engine)
        result = await hook(tool_name="memory_store", tool_args={}, user_id="test")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_accepts_explicit_constitution(self):
        """Factory accepts an explicit constitution."""
        mock_constitution = MagicMock()
        mock_constitution.check_decision.return_value = MagicMock()
        mock_constitution.check_decision.return_value.verdict.name = "ALLOW"

        mock_engine = MagicMock()
        mock_engine.check.return_value = MagicMock(allowed=True)

        hook = await create_default_veto_hook(
            veto_engine=mock_engine, constitution=mock_constitution
        )
        result = await hook(tool_name="execute_bash", tool_args={}, user_id="test")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_fail_open_configurable(self):
        """Factory accepts fail_open parameter."""
        # Prevent auto-wiring of veto engine and constitution so the test
        # exercises the "no engine + fail_closed" path.
        with patch("core.dharma_chakra.veto_engine.get_veto_engine",
                   side_effect=Exception("mocked — no engine")):
            with patch("security.power_balance_constitution.get_power_balance",
                       side_effect=Exception("mocked — no constitution")):
                hook = await create_default_veto_hook(fail_open=False)
        result = await hook(tool_name="web_search", tool_args={}, user_id="test")
        # With no engine and fail_closed, sensitive tools should be blocked
        assert result["allowed"] is False



# ═══════════════════════════════════════════════════════════════════════════════
# ToolAuditEntry Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolAuditEntry:
    """Tests for ToolAuditEntry dataclass."""

    def test_minimal_creation(self):
        """Create entry with minimal required fields."""
        entry = ToolAuditEntry(
            tool_name="execute_bash",
            arguments={"command": "ls"},
            result_summary="Success",
        )
        assert entry.tool_name == "execute_bash"
        assert entry.arguments == {"command": "ls"}
        assert entry.result_summary == "Success"
        assert entry.user_id == "anonymous"
        assert entry.success is True
        assert entry.timestamp != ""  # Auto-generated
        assert entry.timestamp.endswith("Z")

    def test_full_creation(self):
        """Create entry with all fields."""
        entry = ToolAuditEntry(
            tool_name="file_write",
            arguments={"path": "/tmp/test"},
            result_summary="Written 42 bytes",
            veto_result={"allowed": True, "level": "sensitive"},
            user_id="user_001",
            clone_id="clone_alpha",
            session_id="session_abc",
            duration_ms=150.0,
            success=True,
            error=None,
            timestamp="2025-01-01T00:00:00Z",
        )
        assert entry.user_id == "user_001"
        assert entry.clone_id == "clone_alpha"
        assert entry.session_id == "session_abc"
        assert entry.duration_ms == 150.0

    def test_to_dict(self):
        """to_dict returns JSON-compatible dict."""
        entry = ToolAuditEntry(
            tool_name="test_tool",
            arguments={"key": "value"},
            result_summary="done",
            user_id="u1",
            timestamp="2025-01-01T00:00:00Z",
        )
        d = entry.to_dict()
        assert d["tool_name"] == "test_tool"
        assert d["arguments"] == {"key": "value"}
        assert d["result_summary"] == "done"
        assert d["user_id"] == "u1"
        assert d["success"] is True

    def test_safe_serialize_complex(self):
        """_safe_serialize handles nested structures."""
        complex_obj = {
            "string": "hello",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
            "bytes_obj": b"binary",
        }
        result = ToolAuditEntry._safe_serialize(complex_obj)
        assert result["string"] == "hello"
        assert result["int"] == 42
        assert result["none"] is None
        assert result["bytes_obj"] == "b'binary'"


# ═══════════════════════════════════════════════════════════════════════════════
# ToolAuditor Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolAuditor:
    """Tests for ToolAuditor class."""

    @pytest.fixture
    def auditor(self) -> ToolAuditor:
        """Fresh ToolAuditor with small max_entries for testing."""
        return ToolAuditor(max_entries=100)

    def make_entry(self, tool_name: str = "test_tool", user_id: str = "user1",
                   success: bool = True, veto_result: Optional[Dict] = None,
                   duration_ms: float = 10.0) -> ToolAuditEntry:
        return ToolAuditEntry(
            tool_name=tool_name,
            arguments={},
            result_summary="ok",
            user_id=user_id,
            success=success,
            veto_result=veto_result,
            duration_ms=duration_ms,
        )

    # ── record ────────────────────────────────────────────────────────────

    def test_record_entry(self, auditor: ToolAuditor):
        """Record a single entry."""
        entry = self.make_entry()
        auditor.record(entry)
        recent = auditor.get_recent(limit=10)
        assert len(recent) == 1
        assert recent[0].tool_name == "test_tool"

    def test_record_multiple(self, auditor: ToolAuditor):
        """Record multiple entries."""
        for i in range(5):
            auditor.record(self.make_entry(tool_name=f"tool_{i}"))
        assert len(auditor.get_recent(limit=10)) == 5

    def test_ring_buffer_enforced(self):
        """max_entries ring buffer is enforced."""
        auditor = ToolAuditor(max_entries=10)
        for i in range(15):
            auditor.record(self.make_entry(tool_name=f"t{i}"))
        recent = auditor.get_recent(limit=20)
        assert len(recent) == 10  # Only last 10 kept

    # ── get_recent ────────────────────────────────────────────────────────

    def test_get_recent_empty(self, auditor: ToolAuditor):
        """No entries returns empty list."""
        assert auditor.get_recent() == []

    def test_get_recent_limited(self, auditor: ToolAuditor):
        """get_recent respects limit."""
        for i in range(20):
            auditor.record(self.make_entry(tool_name=f"t{i}"))
        recent = auditor.get_recent(limit=5)
        assert len(recent) == 5

    def test_get_recent_newest_first(self, auditor: ToolAuditor):
        """get_recent returns newest entries first."""
        auditor.record(self.make_entry(tool_name="first"))
        auditor.record(self.make_entry(tool_name="second"))
        recent = auditor.get_recent(limit=10)
        assert recent[0].tool_name == "second"
        assert recent[1].tool_name == "first"

    # ── get_by_user ───────────────────────────────────────────────────────

    def test_get_by_user(self, auditor: ToolAuditor):
        """Filter entries by user."""
        auditor.record(self.make_entry(user_id="alice"))
        auditor.record(self.make_entry(user_id="bob"))
        auditor.record(self.make_entry(user_id="alice"))
        alice_entries = auditor.get_by_user("alice")
        assert len(alice_entries) == 2
        bob_entries = auditor.get_by_user("bob")
        assert len(bob_entries) == 1

    def test_get_by_user_empty(self, auditor: ToolAuditor):
        """No entries for a user returns empty list."""
        assert auditor.get_by_user("nonexistent") == []

    # ── get_by_tool ───────────────────────────────────────────────────────

    def test_get_by_tool(self, auditor: ToolAuditor):
        """Filter entries by tool name."""
        auditor.record(self.make_entry(tool_name="bash"))
        auditor.record(self.make_entry(tool_name="python"))
        auditor.record(self.make_entry(tool_name="bash"))
        bash_entries = auditor.get_by_tool("bash")
        assert len(bash_entries) == 2
        python_entries = auditor.get_by_tool("python")
        assert len(python_entries) == 1

    def test_get_by_tool_empty(self, auditor: ToolAuditor):
        """No entries for a tool returns empty list."""
        assert auditor.get_by_tool("ghost_tool") == []

    # ── get_vetoed_calls ──────────────────────────────────────────────────

    def test_get_vetoed_calls(self, auditor: ToolAuditor):
        """Filter entries that were vetoed."""
        auditor.record(self.make_entry(veto_result={"allowed": True}))
        auditor.record(self.make_entry(veto_result={"allowed": False, "reason": "blocked"}))
        auditor.record(self.make_entry(veto_result=None))
        vetoed = auditor.get_vetoed_calls()
        assert len(vetoed) == 1
        assert vetoed[0].veto_result["allowed"] is False

    def test_get_vetoed_calls_empty(self, auditor: ToolAuditor):
        """No vetoed calls returns empty list."""
        auditor.record(self.make_entry(veto_result={"allowed": True}))
        assert auditor.get_vetoed_calls() == []

    # ── get_failed_calls ──────────────────────────────────────────────────

    def test_get_failed_calls(self, auditor: ToolAuditor):
        """Filter entries that failed."""
        auditor.record(self.make_entry(success=True))
        auditor.record(self.make_entry(success=False))
        auditor.record(self.make_entry(success=False))
        failed = auditor.get_failed_calls()
        assert len(failed) == 2

    def test_get_failed_calls_empty(self, auditor: ToolAuditor):
        """No failed calls returns empty list."""
        auditor.record(self.make_entry(success=True))
        assert auditor.get_failed_calls() == []

    # ── get_stats ─────────────────────────────────────────────────────────

    def test_get_stats_empty(self, auditor: ToolAuditor):
        """Stats with no entries."""
        stats = auditor.get_stats()
        assert stats["total_calls"] == 0
        assert stats["total_users"] == 0
        assert stats["total_tools"] == 0
        assert stats["vetoed"] == 0
        assert stats["failed"] == 0
        assert stats["most_used_tool"] is None
        assert stats["most_active_user"] is None

    def test_get_stats_with_data(self, auditor: ToolAuditor):
        """Stats reflect recorded entries."""
        auditor.record(self.make_entry(tool_name="bash", user_id="alice", duration_ms=100))
        auditor.record(self.make_entry(tool_name="bash", user_id="alice",
                                        duration_ms=50, success=False))
        auditor.record(self.make_entry(tool_name="python", user_id="bob", duration_ms=200))
        auditor.record(self.make_entry(tool_name="python", user_id="alice",
                                        veto_result={"allowed": False}))

        stats = auditor.get_stats()
        assert stats["total_calls"] == 4
        assert stats["total_users"] == 2
        assert stats["total_tools"] == 2
        assert stats["vetoed"] == 1
        assert stats["failed"] == 1
        assert stats["most_used_tool"] == "bash"  # bash appears twice
        assert stats["most_active_user"] == "alice"  # alice appears 3 times
        assert stats["avg_duration_ms"] > 0
        assert stats["veto_rate"] == 0.25
        assert stats["failure_rate"] == 0.25

    # ── clear ─────────────────────────────────────────────────────────────

    def test_clear(self, auditor: ToolAuditor):
        """Clearing removes all entries."""
        auditor.record(self.make_entry())
        auditor.record(self.make_entry())
        auditor.clear()
        assert auditor.get_recent() == []
        stats = auditor.get_stats()
        assert stats["total_calls"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Factory Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolAuditorSingleton:
    """Tests for get_tool_auditor and reset_tool_auditor."""

    @pytest.fixture(autouse=True)
    def clean_singleton(self):
        """Reset singleton before and after each test."""
        reset_tool_auditor()
        yield
        reset_tool_auditor()

    def test_get_tool_auditor_returns_singleton(self):
        """get_tool_auditor returns the same instance."""
        a1 = get_tool_auditor()
        a2 = get_tool_auditor()
        assert a1 is a2

    def test_reset_tool_auditor_creates_new(self):
        """reset_tool_auditor replaces the singleton."""
        a1 = get_tool_auditor()
        a1.record(ToolAuditEntry(tool_name="t1", arguments={}, result_summary="ok"))
        reset_tool_auditor()
        a2 = get_tool_auditor()
        assert a1 is not a2
        assert a2.get_stats()["total_calls"] == 0

    def test_singleton_shares_state(self):
        """Multiple calls to get_tool_auditor share state."""
        a1 = get_tool_auditor()
        a1.record(ToolAuditEntry(tool_name="shared", arguments={}, result_summary="ok"))
        a2 = get_tool_auditor()
        assert a2.get_stats()["total_calls"] == 1
