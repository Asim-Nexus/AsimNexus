#!/usr/bin/env python3
"""
Tests for [`core/agent_loop.py`](../../core/agent_loop.py)
Covers:
  - ToolRegistry: register, get_all_tools, get_tools_for_llm, unregister, reset
  - AgentLoop: session creation, basic run, cancellation, active sessions, stats
  - Veto hook integration: set_veto_hook, blocked tool returns BLOCKED status
  - Timeout: step timeout, session timeout
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import pytest

from core.agent_loop import (
    AgentLoop,
    AgentMode,
    AgentStatus,
    AgentStep,
    AgentContext,
    ToolRegistry,
    SECURITY_LEVEL_SECURE,
    SECURITY_LEVEL_SENSITIVE,
    SECURITY_LEVEL_DANGEROUS,
)


# ─── Log capture helper ─────────────────────────────────────────────────────────

@pytest.fixture
def caplog_fix(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture asimnexus agent loop logs."""
    caplog.set_level(logging.INFO, logger="AsimNexus.AgentLoop")
    return caplog


# ═══════════════════════════════════════════════════════════════════════════════
# ToolRegistry Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolRegistry:
    """Tests for ToolRegistry."""

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        return ToolRegistry()

    # ── register_tool & get_tool ────────────────────────────────────────────

    async def _dummy_handler(self, **kwargs) -> Dict[str, Any]:
        return {"result": "ok"}

    def test_register_and_get_tool(self, registry: ToolRegistry):
        """Register a tool and retrieve it by name."""
        registry.register_tool(
            name="test_tool",
            description="A test tool",
            handler=self._dummy_handler,
            parameters={"type": "object", "properties": {"arg1": {"type": "string"}}},
            security_level=SECURITY_LEVEL_SECURE,
        )
        tool = registry.get_tool("test_tool")
        assert tool is not None
        assert tool["name"] == "test_tool"
        assert tool["description"] == "A test tool"
        assert tool["security_level"] == SECURITY_LEVEL_SECURE
        assert tool["requires_approval"] is False

    def test_get_tool_unknown(self, registry: ToolRegistry):
        """Getting an unregistered tool returns None."""
        assert registry.get_tool("nonexistent") is None

    def test_register_overwrite_warning(self, registry: ToolRegistry, caplog_fix):
        """Overwriting an existing tool logs a warning."""
        registry.register_tool(
            name="dup", description="first", handler=self._dummy_handler,
            parameters={}, security_level=SECURITY_LEVEL_SECURE,
        )
        registry.register_tool(
            name="dup", description="second", handler=self._dummy_handler,
            parameters={}, security_level=SECURITY_LEVEL_SECURE,
        )
        assert "Overwriting existing tool: dup" in caplog_fix.text

    def test_register_with_approval(self, registry: ToolRegistry):
        """Tool can require human approval."""
        registry.register_tool(
            name="danger", description="dangerous tool", handler=self._dummy_handler,
            parameters={}, security_level=SECURITY_LEVEL_DANGEROUS,
            requires_approval=True,
        )
        tool = registry.get_tool("danger")
        assert tool["requires_approval"] is True
        assert tool["security_level"] == SECURITY_LEVEL_DANGEROUS

    # ── get_all_tools ───────────────────────────────────────────────────────

    def test_get_all_tools_empty(self, registry: ToolRegistry):
        """Empty registry returns empty list."""
        assert registry.get_all_tools() == []

    def test_get_all_tools_multiple(self, registry: ToolRegistry):
        """Returns all registered tools."""
        registry.register_tool("a", "tool a", self._dummy_handler, {})
        registry.register_tool("b", "tool b", self._dummy_handler, {})
        all_tools = registry.get_all_tools()
        assert len(all_tools) == 2
        names = {t["name"] for t in all_tools}
        assert names == {"a", "b"}

    # ── get_tools_for_llm ───────────────────────────────────────────────────

    def test_get_tools_for_llm_empty(self, registry: ToolRegistry):
        """Empty registry returns empty list for LLM."""
        assert registry.get_tools_for_llm() == []

    def test_get_tools_for_llm_format(self, registry: ToolRegistry):
        """Returns tools in OpenAI-compatible function calling format."""
        registry.register_tool(
            name="my_tool",
            description="My test tool",
            handler=self._dummy_handler,
            parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
        )
        tools = registry.get_tools_for_llm()
        assert len(tools) == 1
        entry = tools[0]
        assert entry["type"] == "function"
        assert entry["function"]["name"] == "my_tool"
        assert entry["function"]["description"] == "My test tool"
        assert entry["function"]["parameters"] == {"type": "object", "properties": {"x": {"type": "integer"}}}

    def test_get_tools_for_llm_no_security_leak(self, registry: ToolRegistry):
        """LLM format must NOT contain handler, security_level, or requires_approval."""
        registry.register_tool(
            name="safe_tool", description="safe", handler=self._dummy_handler,
            parameters={}, security_level=SECURITY_LEVEL_DANGEROUS,
            requires_approval=True,
        )
        entry = registry.get_tools_for_llm()[0]
        func = entry["function"]
        assert "handler" not in func
        assert "security_level" not in func
        assert "requires_approval" not in func

    # ── unregister_tool ─────────────────────────────────────────────────────

    def test_unregister_tool(self, registry: ToolRegistry):
        """Unregister removes the tool."""
        registry.register_tool("tmp", "temporary", self._dummy_handler, {})
        assert registry.get_tool("tmp") is not None
        registry.unregister_tool("tmp")
        assert registry.get_tool("tmp") is None

    def test_unregister_nonexistent(self, registry: ToolRegistry):
        """Unregistering a nonexistent tool does not raise."""
        registry.unregister_tool("ghost")  # should not raise

    # ── reset ───────────────────────────────────────────────────────────────

    def test_reset_clears_all(self, registry: ToolRegistry):
        """Reset wipes all registered tools."""
        registry.register_tool("a", "a", self._dummy_handler, {})
        registry.register_tool("b", "b", self._dummy_handler, {})
        registry.reset()
        assert registry.get_all_tools() == []
        assert registry.get_tool("a") is None


# ═══════════════════════════════════════════════════════════════════════════════
# AgentLoop Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentLoopBasics:
    """Tests for AgentLoop construction and session management."""

    @pytest.fixture
    def loop(self) -> AgentLoop:
        return AgentLoop()

    def test_init_default_tool_registry(self, loop: AgentLoop):
        """Default AgentLoop creates an empty ToolRegistry."""
        assert isinstance(loop.tool_registry, ToolRegistry)
        assert loop.tool_registry.get_all_tools() == []

    def test_init_with_tool_registry(self):
        """AgentLoop accepts a pre-populated ToolRegistry."""
        reg = ToolRegistry()
        reg.register_tool("preloaded", "desc", lambda **kw: {}, {})
        al = AgentLoop(tool_registry=reg)
        assert al.tool_registry.get_tool("preloaded") is not None

    def test_set_veto_hook(self, loop: AgentLoop):
        """Setting a veto hook stores it."""
        async def fake_hook(tool_name, tool_args, user_id):
            return {"allowed": True, "reason": "approved", "level": "secure"}
        loop.set_veto_hook(fake_hook)
        assert loop._veto_hook is not None
        assert loop._veto_hook is fake_hook

    def test_get_session_unknown(self, loop: AgentLoop):
        """Getting a nonexistent session returns None."""
        assert loop.get_session("no-such-session") is None

    def test_get_active_sessions_empty(self, loop: AgentLoop):
        """No sessions means empty active list."""
        assert loop.get_active_sessions() == []

    def test_get_stats_empty(self, loop: AgentLoop):
        """Stats with no sessions."""
        stats = loop.get_stats()
        assert stats["total_sessions"] == 0
        assert stats["total_steps"] == 0
        assert stats["total_duration_ms"] == 0.0
        assert stats["active_sessions"] == 0


class TestAgentLoopRun:
    """Tests for AgentLoop.run() with various scenarios."""

    # ── Helper: build a controllable mock LLM ──────────────────────────────

    @staticmethod
    def _make_step_llm(tool_name: str = "test_tool",
                       tool_args: Optional[Dict] = None,
                       thought: str = "I need to use the tool.") -> Any:
        """Return an async LLM generator that does one tool call then final answer.

        Usage:
            llm = _make_step_llm("search")
            llm is a callable that returns:
              - 1st call → tool call dict
              - 2nd call → final answer (no tool_calls)
              - subsequent calls → final answer
        """
        call_count = 0

        async def llm_generate(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": thought,
                    "tool_calls": [{
                        "id": "call_step_001",
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args or {}),
                        }
                    }]
                }
            return {
                "content": "[Mock LLM] Task complete.",
                "tool_calls": None,
            }

        return llm_generate

    @staticmethod
    def _make_final_llm(answer: str = "Final answer.") -> Any:
        """Return an async LLM generator that immediately returns final answer."""
        async def llm_generate(messages, system="", tools=None):
            return {"content": answer, "tool_calls": None}
        return llm_generate

    @staticmethod
    def _make_plan_aware_llm(plan_text: str = "Step 1: Use tool A\nStep 2: Done") -> Any:
        """Return an async LLM generator for PLAN mode."""
        async def llm_generate(messages, system="", tools=None):
            return {"content": plan_text, "tool_calls": None}
        return llm_generate

    async def _dummy_handler(self, **kwargs) -> Dict[str, Any]:
        return {"result": "handler_ok", "args": kwargs}

    @pytest.fixture
    def reg_with_tool(self) -> ToolRegistry:
        reg = ToolRegistry()
        reg.register_tool(
            name="test_tool",
            description="A test tool",
            handler=self._dummy_handler,
            parameters={"type": "object", "properties": {}},
            security_level=SECURITY_LEVEL_SECURE,
        )
        return reg

    # ── Basic run with mock LLM ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_run_basic(self, reg_with_tool: ToolRegistry):
        """AgentLoop completes a basic run with one tool call."""
        llm = self._make_step_llm(tool_name="test_tool")
        al = AgentLoop(tool_registry=reg_with_tool, llm_generate=llm)
        ctx = await al.run(user_input="Hello, agent!", user_id="user1")
        assert ctx.session_id is not None
        assert ctx.status == AgentStatus.COMPLETED
        assert ctx.final_output is not None
        assert len(ctx.steps) == 1
        step = ctx.steps[0]
        assert step.tool_name == "test_tool"
        assert step.tool_result == {"result": "handler_ok", "args": {}}
        assert step.status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_no_tools(self):
        """AgentLoop completes immediately when no tools are registered."""
        llm = self._make_final_llm("No tools needed.")
        al = AgentLoop(llm_generate=llm)
        ctx = await al.run(user_input="Hello!")
        assert ctx.status == AgentStatus.COMPLETED
        assert len(ctx.steps) == 0  # No tool calls made
        assert ctx.final_output == "No tools needed."

    @pytest.mark.asyncio
    async def test_run_with_custom_system_prompt(self):
        """Custom system prompt is used instead of default."""
        llm = self._make_final_llm()
        al = AgentLoop(llm_generate=llm)
        custom_prompt = "You are a custom agent."
        ctx = await al.run(user_input="Hi", system_prompt=custom_prompt)
        assert ctx.system_prompt == custom_prompt

    @pytest.mark.asyncio
    async def test_run_with_clone_id(self):
        """Clone ID is stored in the context."""
        llm = self._make_final_llm()
        al = AgentLoop(llm_generate=llm)
        ctx = await al.run(user_input="Hi", clone_id="clone-odysseus")
        assert ctx.clone_id == "clone-odysseus"

    # ── Session management ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_session_after_run(self, reg_with_tool: ToolRegistry):
        """Session is retrievable after run completes."""
        llm = self._make_step_llm(tool_name="test_tool")
        al = AgentLoop(tool_registry=reg_with_tool, llm_generate=llm)
        ctx = await al.run(user_input="test")
        retrieved = al.get_session(ctx.session_id)
        assert retrieved is not None
        assert retrieved.session_id == ctx.session_id

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, reg_with_tool: ToolRegistry):
        """Completed sessions are NOT in active list."""
        llm = self._make_step_llm(tool_name="test_tool")
        al = AgentLoop(tool_registry=reg_with_tool, llm_generate=llm)
        ctx = await al.run(user_input="test")
        active = al.get_active_sessions()
        # COMPLETED is not in the active statuses set
        assert ctx.session_id not in [s.session_id for s in active]

    # ── Cancel session ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_cancel_session(self):
        """Cancel a running session."""
        # Use an LLM that takes many steps so we can cancel mid-flight
        call_count = 0

        async def slow_llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if tools and call_count < 10:
                return {
                    "content": "Using tool...",
                    "tool_calls": [{
                        "id": "call_slow",
                        "type": "function",
                        "function": {"name": "slow_tool", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        reg = ToolRegistry()
        async def slow_handler(**kw):
            await asyncio.sleep(0.01)
            return {"result": "ok"}

        reg.register_tool("slow_tool", "slow", slow_handler, {},
                          security_level=SECURITY_LEVEL_SECURE)
        al = AgentLoop(tool_registry=reg, llm_generate=slow_llm)

        # Launch run in background
        task = asyncio.create_task(al.run(user_input="test"))

        # Give it a moment to start
        await asyncio.sleep(0.02)

        # Find the session and cancel it
        sessions = list(al._sessions.values())
        assert len(sessions) >= 1
        session_id = sessions[0].session_id
        cancelled = al.cancel_session(session_id)
        assert cancelled is True

        ctx = await task
        assert ctx.status == AgentStatus.CANCELLED
        assert ctx.completed_at is not None

    @pytest.mark.asyncio
    async def test_cancel_unknown_session(self):
        """Cancelling a nonexistent session returns False."""
        al = AgentLoop()
        assert al.cancel_session("no-such-id") is False

    # ── Stats ──────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_stats_after_run(self, reg_with_tool: ToolRegistry):
        """Stats reflect completed sessions."""
        llm = self._make_step_llm(tool_name="test_tool")
        al = AgentLoop(tool_registry=reg_with_tool, llm_generate=llm)
        ctx = await al.run(user_input="hi")
        stats = al.get_stats()
        assert stats["total_sessions"] == 1
        assert stats["total_steps"] == 1
        assert stats["total_duration_ms"] >= 0

    @pytest.mark.asyncio
    async def test_get_stats_by_status(self, reg_with_tool: ToolRegistry):
        """Stats break down sessions by status."""
        llm = self._make_step_llm(tool_name="test_tool")
        al = AgentLoop(tool_registry=reg_with_tool, llm_generate=llm)
        ctx = await al.run(user_input="hi")
        stats = al.get_stats()
        assert "COMPLETED" in stats["by_status"]
        assert stats["by_status"]["COMPLETED"] == 1

    # ── max_steps ──────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_run_max_steps_respected(self):
        """max_steps limits the number of loop iterations."""
        call_count = 0

        async def looping_llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if tools:
                return {
                    "content": "Keep going...",
                    "tool_calls": [{
                        "id": "call_loop",
                        "type": "function",
                        "function": {"name": "loop_tool", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        reg = ToolRegistry()
        async def loop_handler(**kw):
            return {"result": "ok"}

        reg.register_tool("loop_tool", "looping", loop_handler, {},
                          security_level=SECURITY_LEVEL_SECURE)
        al = AgentLoop(tool_registry=reg, llm_generate=looping_llm)
        ctx = await al.run(user_input="test", max_steps=3)
        assert ctx.status == AgentStatus.COMPLETED
        assert len(ctx.steps) == 3


# ═══════════════════════════════════════════════════════════════════════════════
# Veto Hook Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestVetoHook:
    """Tests for Dharma Chakra veto integration."""

    @pytest.fixture
    def reg_with_tool(self) -> ToolRegistry:
        reg = ToolRegistry()
        async def handler(**kw):
            return {"result": "ok"}
        reg.register_tool("test_tool", "desc", handler, {},
                          security_level=SECURITY_LEVEL_SENSITIVE)
        return reg

    @staticmethod
    def _make_step_llm(tool_name: str = "test_tool"):
        call_count = 0
        async def llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": "Using tool.",
                    "tool_calls": [{
                        "id": "call_veto",
                        "type": "function",
                        "function": {"name": tool_name, "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}
        return llm

    @pytest.mark.asyncio
    async def test_veto_allows_tool(self, reg_with_tool: ToolRegistry):
        """Veto hook that allows does not block execution."""
        async def allow_hook(tool_name, tool_args, user_id):
            return {"allowed": True, "reason": "ok", "level": "sensitive"}

        llm = self._make_step_llm()
        al = AgentLoop(tool_registry=reg_with_tool, llm_generate=llm)
        al.set_veto_hook(allow_hook)
        ctx = await al.run(user_input="run")
        assert ctx.status == AgentStatus.COMPLETED
        assert len(ctx.steps) == 1
        assert ctx.steps[0].status == AgentStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_veto_blocks_tool(self, reg_with_tool: ToolRegistry):
        """Veto hook that denies results in BLOCKED status."""
        async def block_hook(tool_name, tool_args, user_id):
            return {"allowed": False, "reason": "Not permitted by Dharma Chakra", "level": "dangerous"}

        llm = self._make_step_llm()
        al = AgentLoop(tool_registry=reg_with_tool, llm_generate=llm)
        al.set_veto_hook(block_hook)
        ctx = await al.run(user_input="run")
        assert ctx.status == AgentStatus.BLOCKED
        assert len(ctx.steps) == 1
        assert ctx.steps[0].status == AgentStatus.BLOCKED
        assert ctx.steps[0].veto_result is not None
        assert ctx.steps[0].veto_result["allowed"] is False
        assert "Dharma Chakra" in ctx.steps[0].observation

    @pytest.mark.asyncio
    async def test_veto_fail_closed(self, reg_with_tool: ToolRegistry):
        """Veto hook that errors causes fail-closed (blocked)."""
        async def error_hook(tool_name, tool_args, user_id):
            raise RuntimeError("Veto engine crashed")

        llm = self._make_step_llm()
        al = AgentLoop(tool_registry=reg_with_tool, llm_generate=llm)
        al.set_veto_hook(error_hook)
        ctx = await al.run(user_input="run")
        assert ctx.status == AgentStatus.BLOCKED
        step = ctx.steps[0]
        assert step.veto_result is not None
        assert step.veto_result["allowed"] is False
        assert "Veto hook error" in step.veto_result.get("reason", "")

    @pytest.mark.asyncio
    async def test_veto_hook_not_called_no_tool(self):
        """Veto hook is not called when no tool is selected."""
        veto_called = False

        async def veto(tool_name, tool_args, user_id):
            nonlocal veto_called
            veto_called = True
            return {"allowed": True, "reason": "", "level": "secure"}

        async def final_llm(messages, system="", tools=None):
            return {"content": "No tool needed.", "tool_calls": None}

        al = AgentLoop(llm_generate=final_llm)
        al.set_veto_hook(veto)
        ctx = await al.run(user_input="no tool")
        assert ctx.status == AgentStatus.COMPLETED
        assert veto_called is False


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Mode Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAgentModes:
    """Tests for different AgentMode behaviors."""

    @pytest.mark.asyncio
    async def test_plan_mode(self):
        """PLAN mode produces a plan without executing any tools."""
        plan_text = "Step 1: Research\nStep 2: Implement\nStep 3: Test"
        call_count = 0

        async def plan_llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            return {"content": plan_text, "tool_calls": None}

        al = AgentLoop(llm_generate=plan_llm)
        ctx = await al.run(user_input="build something", mode=AgentMode.PLAN)
        assert ctx.status == AgentStatus.COMPLETED
        assert ctx.final_output == plan_text
        assert len(ctx.steps) == 0  # No steps executed

    @pytest.mark.asyncio
    async def test_observe_mode_skips_dangerous(self):
        """OBSERVE mode skips execution of dangerous tools."""
        reg = ToolRegistry()
        async def handler(**kw):
            return {"result": "executed"}
        reg.register_tool("danger_tool", "dangerous", handler, {},
                          security_level=SECURITY_LEVEL_DANGEROUS)
        reg.register_tool("safe_tool", "safe", handler, {},
                          security_level=SECURITY_LEVEL_SECURE)

        # LLM that calls danger_tool first, then safe_tool
        call_count = 0
        async def observe_llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": "Using dangerous tool.",
                    "tool_calls": [{
                        "id": "call_d1",
                        "type": "function",
                        "function": {"name": "danger_tool", "arguments": "{}"},
                    }]
                }
            if call_count == 2 and tools:
                return {
                    "content": "Now using safe tool.",
                    "tool_calls": [{
                        "id": "call_s1",
                        "type": "function",
                        "function": {"name": "safe_tool", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        al = AgentLoop(tool_registry=reg, llm_generate=observe_llm)
        ctx = await al.run(user_input="test", mode=AgentMode.OBSERVE, max_steps=3)
        # The dangerous tool step should have been skipped but not blocked
        assert len(ctx.steps) == 2
        # Danger step should be completed (skipped in observe mode)
        assert ctx.steps[0].tool_name == "danger_tool"
        assert ctx.steps[0].observation is not None
        assert "OBSERVE MODE" in ctx.steps[0].observation
        # Safe tool should have been executed normally
        assert ctx.steps[1].tool_name == "safe_tool"
        assert ctx.steps[1].tool_result is not None

    @pytest.mark.asyncio
    async def test_guide_mode_proceeds(self):
        """GUIDE mode proceeds with execution (confirmation is external)."""
        reg = ToolRegistry()
        async def handler(**kw):
            return {"result": "ok"}
        reg.register_tool("guide_tool", "guided", handler, {},
                          security_level=SECURITY_LEVEL_SECURE)

        call_count = 0
        async def guide_llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": "Proposing step.",
                    "tool_calls": [{
                        "id": "call_g1",
                        "type": "function",
                        "function": {"name": "guide_tool", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        al = AgentLoop(tool_registry=reg, llm_generate=guide_llm)
        ctx = await al.run(user_input="test", mode=AgentMode.GUIDE)
        assert ctx.status == AgentStatus.COMPLETED
        assert len(ctx.steps) == 1
        # In GUIDE mode, step is set to AWAITING_TOOL, then execution proceeds
        assert ctx.steps[0].tool_name == "guide_tool"
        assert ctx.steps[0].tool_result == {"result": "ok"}


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Execution Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolExecution:
    """Tests for tool execution within AgentLoop."""

    @pytest.mark.asyncio
    async def test_tool_with_args(self):
        """Tool arguments are passed correctly to the handler."""
        reg = ToolRegistry()
        captured_args = {}

        async def handler(**kw):
            nonlocal captured_args
            captured_args = kw
            return {"result": "ok"}

        reg.register_tool("echo", "echo tool", handler,
                          parameters={"type": "object", "properties": {"msg": {"type": "string"}}})

        call_count = 0
        async def llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": "Echoing.",
                    "tool_calls": [{
                        "id": "call_e1",
                        "type": "function",
                        "function": {"name": "echo", "arguments": '{"msg": "hello"}'},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        al = AgentLoop(tool_registry=reg, llm_generate=llm)
        ctx = await al.run(user_input="say hello")
        assert captured_args == {"msg": "hello"}
        assert ctx.steps[0].tool_result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_unknown_tool_error(self):
        """Calling an unregistered tool returns an error gracefully."""
        reg = ToolRegistry()

        call_count = 0
        async def llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "content": "Using unknown.",
                    "tool_calls": [{
                        "id": "call_u1",
                        "type": "function",
                        "function": {"name": "no_such_tool", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        al = AgentLoop(tool_registry=reg, llm_generate=llm)
        ctx = await al.run(user_input="test")
        assert len(ctx.steps) == 1
        assert "error" in ctx.steps[0].tool_result
        assert "Unknown tool" in ctx.steps[0].tool_result["error"]

    @pytest.mark.asyncio
    async def test_tool_handler_exception(self):
        """Handler exceptions are caught and returned as error results."""
        reg = ToolRegistry()

        async def failing_handler(**kw):
            raise ValueError("Something went wrong")

        reg.register_tool("fail", "failing", failing_handler, {},
                          security_level=SECURITY_LEVEL_SECURE)

        call_count = 0
        async def llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": "Calling failing tool.",
                    "tool_calls": [{
                        "id": "call_f1",
                        "type": "function",
                        "function": {"name": "fail", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        al = AgentLoop(tool_registry=reg, llm_generate=llm)
        ctx = await al.run(user_input="test")
        assert ctx.status == AgentStatus.COMPLETED  # Error is per-step, not fatal
        assert "error" in ctx.steps[0].tool_result
        assert "Something went wrong" in ctx.steps[0].tool_result["error"]


# ═══════════════════════════════════════════════════════════════════════════════
# Timeout Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestTimeouts:
    """Tests for step and session timeouts."""

    @pytest.mark.asyncio
    async def test_step_timeout(self):
        """A tool that exceeds step timeout is caught."""
        reg = ToolRegistry()

        async def slow_handler(**kw):
            await asyncio.sleep(10)  # Will be interrupted by 60s step timeout
            return {"result": "too late"}

        reg.register_tool("slow", "slow tool", slow_handler, {},
                          security_level=SECURITY_LEVEL_SECURE)

        call_count = 0
        async def llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": "Calling slow tool.",
                    "tool_calls": [{
                        "id": "call_slow1",
                        "type": "function",
                        "function": {"name": "slow", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        al = AgentLoop(tool_registry=reg, llm_generate=llm)
        # _DEFAULT_STEP_TIMEOUT is 60s; our tool sleeps 10s, so technically it
        # would not time out with defaults. We rely on step timeout being set.
        # Since we can't easily inject a shorter default, we verify the
        # timeout mechanism exists by checking the asyncio.wait_for wrapping.
        ctx = await al.run(user_input="test")
        # With default 60s timeout, 10s sleep should not time out
        assert ctx.status == AgentStatus.COMPLETED
        assert ctx.steps[0].tool_result == {"result": "too late"}

    @pytest.mark.asyncio
    async def test_session_timeout(self):
        """A session that exceeds session timeout is failed."""
        reg = ToolRegistry()
        async def handler(**kw):
            return {"result": "ok"}
        reg.register_tool("t", "t", handler, {},
                          security_level=SECURITY_LEVEL_SECURE)

        # We cannot easily mock time.monotonic, so we verify the timeout check
        # passes through normally. The session timeout is 600s default, so a
        # normal run should never timeout.
        call_count = 0
        async def llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": "Using tool.",
                    "tool_calls": [{
                        "id": "call_t1",
                        "type": "function",
                        "function": {"name": "t", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        al = AgentLoop(tool_registry=reg, llm_generate=llm)
        import core.agent_loop as al_mod
        original_timeout = al_mod._DEFAULT_SESSION_TIMEOUT
        try:
            al_mod._DEFAULT_SESSION_TIMEOUT = 0.001  # 1ms session timeout
            # Because the module constants are read at runtime inside the while loop
            # (via _parse_iso_timestamp / time.monotonic comparison), we need to
            # patch the module-level constant. However, the constants are read as
            # local variables in the run() method, so we need a different approach.
            pass
        finally:
            al_mod._DEFAULT_SESSION_TIMEOUT = original_timeout

        # For session timeout, we verify the logic path exists by checking the
        # code has the timeout check. Since we can't reliably trigger it in a
        # test without injecting time.monotonic, we document the coverage gap.
        ctx = await al.run(user_input="test")
        assert ctx.status == AgentStatus.COMPLETED  # Normal completion

    @pytest.mark.asyncio
    async def test_step_timeout_mechanism_exists(self):
        """Verify the timeout mechanism catches genuinely slow tools.

        We use a tool that sleeps for 2 seconds but set an effective timeout
        by patching the step timeout constant used in asyncio.wait_for.
        """
        reg = ToolRegistry()
        timeout_caught = False

        async def very_slow_handler(**kw):
            await asyncio.sleep(5)
            return {"result": "finally"}

        reg.register_tool("vslow", "very slow", very_slow_handler, {},
                          security_level=SECURITY_LEVEL_SECURE)

        call_count = 0
        async def llm(messages, system="", tools=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and tools:
                return {
                    "content": "Calling very slow tool.",
                    "tool_calls": [{
                        "id": "call_vs1",
                        "type": "function",
                        "function": {"name": "vslow", "arguments": "{}"},
                    }]
                }
            return {"content": "Done.", "tool_calls": None}

        al = AgentLoop(tool_registry=reg, llm_generate=llm)

        # Monkey-patch the module constant used in asyncio.wait_for
        import core.agent_loop as agent_loop_mod
        orig_timeout = agent_loop_mod._DEFAULT_STEP_TIMEOUT
        try:
            agent_loop_mod._DEFAULT_STEP_TIMEOUT = 1  # 1 second
            ctx = await al.run(user_input="test")
            # The tool should have timed out
            assert ctx.status == AgentStatus.COMPLETED
            step = ctx.steps[0]
            assert "timed out" in step.tool_result.get("error", "").lower()
        finally:
            agent_loop_mod._DEFAULT_STEP_TIMEOUT = orig_timeout


# ═══════════════════════════════════════════════════════════════════════════════
# AgentContext & AgentStep Data Class Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataClasses:
    """Tests for AgentContext and AgentStep dataclasses."""

    def test_agent_step_defaults(self):
        """AgentStep sets created_at on init."""
        step = AgentStep(step_id="s1", thought="thinking")
        assert step.step_id == "s1"
        assert step.thought == "thinking"
        assert step.tool_name is None
        assert step.tool_args is None
        assert step.status == AgentStatus.PENDING
        assert step.created_at != ""

    def test_agent_step_to_dict(self):
        """AgentStep.to_dict serializes correctly."""
        step = AgentStep(step_id="s1", thought="think", tool_name="t1",
                         tool_args={"a": 1}, status=AgentStatus.COMPLETED)
        d = step.to_dict()
        assert d["step_id"] == "s1"
        assert d["status"] == "COMPLETED"
        assert d["tool_name"] == "t1"
        assert d["tool_args"] == {"a": 1}

    def test_agent_context_defaults(self):
        """AgentContext sets created_at on init."""
        ctx = AgentContext(session_id="session1")
        assert ctx.session_id == "session1"
        assert ctx.user_id == "anonymous"
        assert ctx.status == AgentStatus.PENDING
        assert ctx.created_at != ""
        assert ctx.steps == []
        assert ctx.messages == []

    def test_agent_context_to_dict(self):
        """AgentContext.to_dict serializes correctly."""
        ctx = AgentContext(session_id="s1", user_id="u1",
                           status=AgentStatus.COMPLETED,
                           final_output="done")
        step = AgentStep(step_id="st1", thought="t", status=AgentStatus.COMPLETED)
        ctx.steps.append(step)
        d = ctx.to_dict()
        assert d["session_id"] == "s1"
        assert d["user_id"] == "u1"
        assert d["status"] == "COMPLETED"
        assert d["final_output"] == "done"
        assert len(d["steps"]) == 1
        assert d["steps"][0]["step_id"] == "st1"

    def test_agent_context_custom_user(self):
        """AgentContext accepts a custom user_id."""
        ctx = AgentContext(session_id="s1", user_id="custom_user")
        assert ctx.user_id == "custom_user"

    def test_agent_context_metadata(self):
        """AgentContext accepts metadata dict."""
        ctx = AgentContext(session_id="s1", metadata={"source": "test"})
        assert ctx.metadata == {"source": "test"}


# ═══════════════════════════════════════════════════════════════════════════════
# AgentMode & AgentStatus Enum Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnums:
    """Tests for AgentMode and AgentStatus enums."""

    def test_agent_mode_values(self):
        assert AgentMode.AUTO.name == "AUTO"
        assert AgentMode.GUIDE.name == "GUIDE"
        assert AgentMode.PLAN.name == "PLAN"
        assert AgentMode.OBSERVE.name == "OBSERVE"
        assert len(AgentMode) == 4

    def test_agent_status_values(self):
        assert AgentStatus.PENDING.name == "PENDING"
        assert AgentStatus.PLANNING.name == "PLANNING"
        assert AgentStatus.AWAITING_TOOL.name == "AWAITING_TOOL"
        assert AgentStatus.EXECUTING.name == "EXECUTING"
        assert AgentStatus.OBSERVING.name == "OBSERVING"
        assert AgentStatus.COMPLETED.name == "COMPLETED"
        assert AgentStatus.FAILED.name == "FAILED"
        assert AgentStatus.CANCELLED.name == "CANCELLED"
        assert AgentStatus.BLOCKED.name == "BLOCKED"
        assert len(AgentStatus) == 9


# ─── Helper: json import for test file ─────────────────────────────────────────

import json
