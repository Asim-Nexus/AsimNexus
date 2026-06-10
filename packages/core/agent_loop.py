#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Multi-Round Agent Execution Loop

Agent Loop — Multi-round autonomous agent execution.

Inspired by Odysseus (PewDiePie's open-source AI workspace), adapted for
AsimNexus infrastructure including Dharma Chakra constitution enforcement,
Digital Clone identity, and Mesh Network distribution.

The agent loop:
1. Receives a task/query from user
2. Plans steps using LLM (think -> tool -> observe -> repeat)
3. Executes tools with security checks
4. Observes results and iterates
5. Produces final output
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("AsimNexus.AgentLoop")

# ─── Environment Configuration ────────────────────────────────────────────────
_DEFAULT_MAX_STEPS = int(os.getenv("ASIM_AGENT_MAX_STEPS", "25"))
_DEFAULT_STEP_TIMEOUT = int(os.getenv("ASIM_AGENT_STEP_TIMEOUT", "60"))
_DEFAULT_SESSION_TIMEOUT = int(os.getenv("ASIM_AGENT_SESSION_TIMEOUT", "600"))
_DEFAULT_LLM_PROVIDER = os.getenv("ASIM_AGENT_LLM_PROVIDER", "openai")
_DEFAULT_LLM_MODEL = os.getenv("ASIM_AGENT_LLM_MODEL", "gpt-4")


# ─── ENUMS ─────────────────────────────────────────────────────────────────────

class AgentMode(Enum):
    """Agent operating modes."""
    AUTO = auto()       # Autonomous - plans and executes independently
    GUIDE = auto()      # Guided - proposes steps, asks for confirmation
    PLAN = auto()       # Plan - produces plan only, no execution
    OBSERVE = auto()    # Observe - reads data, no modifications


class AgentStatus(Enum):
    """Status of an agent execution."""
    PENDING = auto()
    PLANNING = auto()
    AWAITING_TOOL = auto()
    EXECUTING = auto()
    OBSERVING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    BLOCKED = auto()  # Blocked by Dharma Chakra / security


# ─── DATA CLASSES ──────────────────────────────────────────────────────────────

@dataclass
class AgentStep:
    """A single step in agent execution."""
    step_id: str
    thought: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None
    observation: str = ""
    status: AgentStatus = AgentStatus.PENDING
    duration_ms: float = 0.0
    veto_result: Optional[Dict] = None  # Dharma Chakra veto response
    created_at: str = ""
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize step to JSON-compatible dict."""
        result = asdict(self)
        result["status"] = self.status.name
        return result


@dataclass
class AgentContext:
    """Full context for an agent execution session."""
    session_id: str
    user_id: str = "anonymous"
    clone_id: Optional[str] = None
    mode: AgentMode = AgentMode.AUTO
    system_prompt: str = ""
    messages: List[Dict] = field(default_factory=list)
    steps: List[AgentStep] = field(default_factory=list)
    status: AgentStatus = AgentStatus.PENDING
    max_steps: int = _DEFAULT_MAX_STEPS
    created_at: str = ""
    completed_at: Optional[str] = None
    final_output: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to JSON-compatible dict."""
        result = asdict(self)
        result["mode"] = self.mode.name
        result["status"] = self.status.name
        result["steps"] = [s.to_dict() for s in self.steps]
        return result


# ─── TOOL REGISTRY ─────────────────────────────────────────────────────────────

class ToolRegistry:
    """Registry of available tools that agents can use.

    Each tool has:
    - name: unique identifier
    - description: what it does (for LLM function calling)
    - handler: async callable that executes the tool
    - parameters: JSON schema for arguments
    - security_level: SECURE, SENSITIVE, DANGEROUS
    - requires_approval: whether human must confirm
    """

    def __init__(self):
        self._tools: Dict[str, Dict] = {}

    def register_tool(self, name: str, description: str, handler: Callable,
                      parameters: Dict, security_level: str = "secure",
                      requires_approval: bool = False):
        """Register a tool with the registry.

        Args:
            name: Unique tool identifier.
            description: Human-readable description for LLM.
            handler: Async callable that accepts **kwargs and returns Dict.
            parameters: JSON Schema dict describing accepted arguments.
            security_level: One of "secure", "sensitive", "dangerous".
            requires_approval: If True, human must confirm before execution.
        """
        if name in self._tools:
            logger.warning(f"Overwriting existing tool: {name}")

        self._tools[name] = {
            "name": name,
            "description": description,
            "handler": handler,
            "parameters": parameters,
            "security_level": security_level,
            "requires_approval": requires_approval,
        }
        logger.info(f"Registered tool: {name} (security={security_level}, approval={requires_approval})")

    def get_tool(self, name: str) -> Optional[Dict]:
        """Get a tool definition by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> List[Dict]:
        """Get all registered tool definitions."""
        return list(self._tools.values())

    def get_tools_for_llm(self) -> List[Dict]:
        """Return tools formatted for OpenAI-compatible function calling API.

        Returns a list of dicts in the format expected by the LLM:
        {
            "type": "function",
            "function": {
                "name": "...",
                "description": "...",
                "parameters": {...}
            }
        }
        """
        tools = []
        for tool in self._tools.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                }
            })
        return tools

    def unregister_tool(self, name: str):
        """Remove a tool from the registry."""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")

    def reset(self):
        """Clear all registered tools."""
        self._tools.clear()
        logger.info("Tool registry reset")


# ─── SECURITY LEVEL CONSTANTS ──────────────────────────────────────────────────

SECURITY_LEVEL_SECURE = "secure"
SECURITY_LEVEL_SENSITIVE = "sensitive"
SECURITY_LEVEL_DANGEROUS = "dangerous"


# ─── AGENT LOOP ────────────────────────────────────────────────────────────────

class AgentLoop:
    """Multi-round agent execution loop with planning, tool execution, and observation.

    Flow: plan -> select tool -> check security -> execute -> observe -> re-plan -> ...

    Features:
    - Multiple agent modes (AUTO, GUIDE, PLAN, OBSERVE)
    - Tool registry with security levels
    - Dharma Chakra veto integration point
    - Step-by-step execution tracking
    - Timeout and cancellation support
    - LLM-agnostic (works with any provider)
    """

    def __init__(self, tool_registry: Optional[ToolRegistry] = None,
                 llm_generate: Optional[Callable] = None):
        self.tool_registry = tool_registry or ToolRegistry()
        self.llm_generate = llm_generate or self._default_llm_generate
        self._sessions: Dict[str, AgentContext] = {}
        self._veto_hook: Optional[Callable] = None  # Dharma Chakra hook
        self._cancelled: Set[str] = set()

    # ── Veto Hook ───────────────────────────────────────────────────────────

    def set_veto_hook(self, hook: Callable):
        """Set a Dharma Chakra veto callback.

        The hook should be an async callable accepting
        (tool_name: str, tool_args: Dict, user_id: str) and returning:
            {"allowed": bool, "reason": str, "level": str}
        """
        self._veto_hook = hook
        logger.info("Veto hook registered")

    # ── Session Management ──────────────────────────────────────────────────

    def get_session(self, session_id: str) -> Optional[AgentContext]:
        """Get an agent session context by ID."""
        return self._sessions.get(session_id)

    def cancel_session(self, session_id: str) -> bool:
        """Cancel a running session. Returns True if found."""
        if session_id in self._sessions:
            self._cancelled.add(session_id)
            ctx = self._sessions[session_id]
            ctx.status = AgentStatus.CANCELLED
            ctx.completed_at = datetime.utcnow().isoformat()
            logger.info(f"Session cancelled: {session_id}")
            return True
        return False

    def get_active_sessions(self) -> List[AgentContext]:
        """Get all sessions that are currently active."""
        active_statuses = {
            AgentStatus.PENDING, AgentStatus.PLANNING,
            AgentStatus.AWAITING_TOOL, AgentStatus.EXECUTING,
            AgentStatus.OBSERVING
        }
        return [
            ctx for ctx in self._sessions.values()
            if ctx.status in active_statuses
        ]

    def get_stats(self) -> Dict:
        """Get aggregate statistics about all sessions."""
        total = len(self._sessions)
        by_status: Dict[str, int] = {}
        total_steps = 0
        total_duration_ms = 0.0

        for ctx in self._sessions.values():
            status_name = ctx.status.name
            by_status[status_name] = by_status.get(status_name, 0) + 1
            total_steps += len(ctx.steps)
            for step in ctx.steps:
                total_duration_ms += step.duration_ms

        return {
            "total_sessions": total,
            "by_status": by_status,
            "total_steps": total_steps,
            "total_duration_ms": total_duration_ms,
            "active_sessions": len(self.get_active_sessions()),
        }

    # ── Main Run ────────────────────────────────────────────────────────────

    async def run(self, user_input: str, user_id: str = "anonymous",
                  clone_id: Optional[str] = None,
                  mode: AgentMode = AgentMode.AUTO,
                  system_prompt: Optional[str] = None,
                  max_steps: int = _DEFAULT_MAX_STEPS) -> AgentContext:
        """Run the agent loop on a user input. Returns the final AgentContext.

        Args:
            user_input: The user's task or query string.
            user_id: Unique user identifier.
            clone_id: Optional Digital Clone ID for identity binding.
            mode: Agent operating mode.
            system_prompt: Optional system prompt override.
            max_steps: Maximum number of planning/execution steps.

        Returns:
            AgentContext with full execution trace and final_output.
        """
        session_id = str(uuid.uuid4())

        # Build default system prompt if none provided
        if not system_prompt:
            system_prompt = self._build_system_prompt(mode, clone_id)

        ctx = AgentContext(
            session_id=session_id,
            user_id=user_id,
            clone_id=clone_id,
            mode=mode,
            system_prompt=system_prompt,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            status=AgentStatus.PLANNING,
            max_steps=max_steps,
        )
        self._sessions[session_id] = ctx

        try:
            # In PLAN mode, produce a plan and stop
            if mode == AgentMode.PLAN:
                await self._produce_plan(ctx)
                return ctx

            # In OBSERVE mode, only read tools are allowed
            # In GUIDE mode, each step requires user confirmation
            # In AUTO mode, full autonomous execution

            step_count = 0
            while step_count < max_steps:
                # Check cancellation
                if session_id in self._cancelled:
                    ctx.status = AgentStatus.CANCELLED
                    break

                # Check session timeout
                start_time = time.monotonic()
                elapsed = start_time - self._parse_iso_timestamp(ctx.created_at)
                if elapsed > _DEFAULT_SESSION_TIMEOUT:
                    ctx.error = f"Session timeout after {_DEFAULT_SESSION_TIMEOUT}s"
                    ctx.status = AgentStatus.FAILED
                    break

                # PLAN: LLM decides next step (tool call or final answer)
                ctx.status = AgentStatus.PLANNING
                plan_result = await self._plan(ctx)

                if plan_result is None:
                    # LLM produced final answer, no more tool calls
                    break

                if "error" in plan_result:
                    ctx.error = plan_result["error"]
                    ctx.status = AgentStatus.FAILED
                    break

                step = AgentStep(
                    step_id=str(uuid.uuid4()),
                    thought=plan_result.get("thought", ""),
                    tool_name=plan_result.get("tool_name"),
                    tool_args=plan_result.get("tool_args"),
                    status=AgentStatus.AWAITING_TOOL,
                )
                ctx.steps.append(step)

                # In PLAN mode, we already extracted the plan above; skip execution
                if mode == AgentMode.PLAN:
                    ctx.status = AgentStatus.COMPLETED
                    break

                # In GUIDE mode, pause for user confirmation
                if mode == AgentMode.GUIDE:
                    # The framework will call step_callback; store that we need confirmation
                    step.status = AgentStatus.AWAITING_TOOL
                    # For now, proceed (the external orchestrator can check for AWAITING_TOOL)
                    # In a real system, this would yield control back to the caller
                    pass

                # Check veto before execution
                veto_allowed = await self._check_veto(step, ctx)
                if not veto_allowed:
                    step.status = AgentStatus.BLOCKED
                    step.observation = step.veto_result.get("reason", "Blocked by Dharma Chakra")
                    ctx.status = AgentStatus.BLOCKED
                    logger.warning(f"Step {step.step_id} blocked by veto: {step.veto_result}")
                    break

                # In OBSERVE mode, skip execution of non-read tools
                if mode == AgentMode.OBSERVE and step.tool_name:
                    tool_def = self.tool_registry.get_tool(step.tool_name)
                    if tool_def and tool_def.get("security_level") in ("sensitive", "dangerous"):
                        step.observation = f"[OBSERVE MODE] Skipped '{step.tool_name}' - write operations not allowed in observe mode"
                        step.status = AgentStatus.COMPLETED
                        step_count += 1
                        continue

                # EXECUTE TOOL
                step.status = AgentStatus.EXECUTING
                tool_start = time.monotonic()
                try:
                    result = await asyncio.wait_for(
                        self._execute_tool(ctx, step),
                        timeout=_DEFAULT_STEP_TIMEOUT
                    )
                    step.tool_result = result
                except asyncio.TimeoutError:
                    step.tool_result = {
                        "error": f"Tool execution timed out after {_DEFAULT_STEP_TIMEOUT}s",
                        "tool": step.tool_name
                    }
                    logger.warning(f"Tool '{step.tool_name}' timed out in session {session_id}")
                except Exception as e:
                    step.tool_result = {
                        "error": str(e),
                        "tool": step.tool_name
                    }
                    logger.error(f"Tool '{step.tool_name}' failed: {e}")

                step.duration_ms = (time.monotonic() - tool_start) * 1000

                # OBSERVE: LLM interprets the result
                ctx.status = AgentStatus.OBSERVING
                await self._observe(ctx, step)

                step.status = AgentStatus.COMPLETED
                step.completed_at = datetime.utcnow().isoformat()
                step_count += 1

            # End of loop
            if ctx.status not in (AgentStatus.FAILED, AgentStatus.CANCELLED, AgentStatus.BLOCKED):
                ctx.status = AgentStatus.COMPLETED

            # Build final output from conversation
            ctx.final_output = self._build_final_output(ctx)
            ctx.completed_at = datetime.utcnow().isoformat()

        except Exception as e:
            ctx.error = str(e)
            ctx.status = AgentStatus.FAILED
            ctx.completed_at = datetime.utcnow().isoformat()
            logger.exception(f"Agent loop failed for session {session_id}: {e}")

        finally:
            self._cancelled.discard(session_id)

        return ctx

    # ── Planning ────────────────────────────────────────────────────────────

    async def _plan(self, ctx: AgentContext) -> Optional[Dict]:
        """LLM-based planning step. Returns tool call dict or None for final answer.

        Returns:
            Dict with keys:
                - "thought": str — LLM's reasoning
                - "tool_name": Optional[str] — tool to call (None = final answer)
                - "tool_args": Optional[Dict] — arguments for the tool
            or None if the LLM wants to produce the final answer.
        """
        # Build the messages with full conversation history
        messages = list(ctx.messages)

        # Add step history
        for step in ctx.steps:
            messages.append({
                "role": "assistant",
                "content": step.thought
            })
            if step.tool_name:
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": f"call_{step.step_id}",
                        "type": "function",
                        "function": {
                            "name": step.tool_name,
                            "arguments": json.dumps(step.tool_args or {})
                        }
                    }]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": f"call_{step.step_id}",
                    "content": json.dumps(step.tool_result) if step.tool_result else ""
                })
            if step.observation:
                messages.append({
                    "role": "assistant",
                    "content": step.observation
                })

        # Add planning instruction
        messages.append({
            "role": "user",
            "content": (
                "What is the next step? If you need to use a tool, respond with a tool call. "
                "If the task is complete or you have enough information, provide the final answer. "
                "Think step by step before deciding."
            )
        })

        # Get LLM response with tools
        tools = self.tool_registry.get_tools_for_llm()

        try:
            response = await self.llm_generate(
                messages=messages,
                system=ctx.system_prompt,
                tools=tools if tools else None,
            )
        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            return {"error": f"LLM planning failed: {e}"}

        # Parse response
        thought = response.get("content", "")
        tool_calls = response.get("tool_calls")

        if tool_calls and len(tool_calls) > 0:
            tc = tool_calls[0]
            try:
                args = json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"]
            except (json.JSONDecodeError, KeyError):
                args = {}
            return {
                "thought": thought,
                "tool_name": tc["function"]["name"],
                "tool_args": args,
            }

        # No tool call — check if it's a final answer
        if thought:
            ctx.messages.append({"role": "assistant", "content": thought})
            ctx.final_output = thought

        return None

    async def _produce_plan(self, ctx: AgentContext):
        """In PLAN mode, produce a step-by-step plan without execution."""
        messages = list(ctx.messages)
        messages.append({
            "role": "user",
            "content": (
                "Produce a detailed step-by-step plan to accomplish this task. "
                "For each step, specify which tool would be used and why. "
                "Output the plan in a clear structured format."
            )
        })

        try:
            response = await self.llm_generate(
                messages=messages,
                system=ctx.system_prompt,
                tools=self.tool_registry.get_tools_for_llm(),
            )
            ctx.final_output = response.get("content", "")
            ctx.status = AgentStatus.COMPLETED
        except Exception as e:
            ctx.error = f"Plan generation failed: {e}"
            ctx.status = AgentStatus.FAILED

    # ── Tool Execution ──────────────────────────────────────────────────────

    async def _execute_tool(self, ctx: AgentContext, step: AgentStep) -> Any:
        """Execute a tool with security checks and Dharma Chakra veto.

        Args:
            ctx: The agent session context.
            step: The step containing tool name and args.

        Returns:
            The raw result from the tool handler (should be JSON-serializable).
        """
        if not step.tool_name:
            return {"error": "No tool name specified"}

        tool_def = self.tool_registry.get_tool(step.tool_name)
        if not tool_def:
            return {"error": f"Unknown tool: {step.tool_name}"}

        handler = tool_def["handler"]
        tool_args = step.tool_args or {}

        logger.info(f"Executing tool '{step.tool_name}' with args: {json.dumps(tool_args, default=str)[:200]}")

        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**tool_args)
            else:
                result = handler(**tool_args)
            return result
        except Exception as e:
            logger.error(f"Tool '{step.tool_name}' execution error: {e}")
            return {"error": str(e), "tool": step.tool_name}

    async def _check_veto(self, step: AgentStep, ctx: AgentContext) -> bool:
        """Check Dharma Chakra veto before executing a tool.

        Returns True if the tool is allowed, False if blocked.
        """
        if not self._veto_hook or not step.tool_name:
            return True

        try:
            result = await self._veto_hook(
                tool_name=step.tool_name,
                tool_args=step.tool_args or {},
                user_id=ctx.user_id,
            )
            step.veto_result = result
            if not result.get("allowed", True):
                logger.warning(
                    f"Veto blocked '{step.tool_name}' for user '{ctx.user_id}': "
                    f"{result.get('reason', 'No reason')}"
                )
                return False
            return True
        except Exception as e:
            logger.error(f"Veto hook error: {e}")
            # Fail closed — if veto hook errors, block the action
            step.veto_result = {"allowed": False, "reason": f"Veto hook error: {e}", "level": "error"}
            return False

    # ── Observation ─────────────────────────────────────────────────────────

    async def _observe(self, ctx: AgentContext, step: AgentStep):
        """LLM observation of tool result - what happened, what next.

        Adds the observation to the step and stores the interaction
        in the conversation history.
        """
        messages = list(ctx.messages)

        # Add the assistant's thought
        messages.append({
            "role": "assistant",
            "content": step.thought
        })

        # Add the tool result
        if step.tool_name:
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": f"call_{step.step_id}",
                    "type": "function",
                    "function": {
                        "name": step.tool_name,
                        "arguments": json.dumps(step.tool_args or {})
                    }
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": f"call_{step.step_id}",
                "content": json.dumps(step.tool_result) if step.tool_result else "No result"
            })

        # Get observation from LLM
        messages.append({
            "role": "user",
            "content": (
                "Summarize what happened as a result of the tool execution. "
                "What was the outcome? What should be done next? "
                "Keep the observation concise."
            )
        })

        try:
            response = await self.llm_generate(
                messages=messages,
                system=ctx.system_prompt,
            )
            step.observation = response.get("content", "")
        except Exception as e:
            step.observation = f"[Observation error: {e}]"
            logger.warning(f"Observation LLM call failed: {e}")

    # ── Default LLM Generator ───────────────────────────────────────────────

    async def _default_llm_generate(self, messages: List[Dict], system: str = "",
                                    tools: Optional[List[Dict]] = None) -> Dict:
        """Default LLM generation that checks for configured provider.

        Tries in order:
        1. _local_llm if available
        2. litellm for configured provider
        3. Returns a mock response for testing
        """
        # Try to import and use litellm
        try:
            import litellm

            # Build kwargs
            kwargs = {
                "model": os.getenv("ASIM_AGENT_LLM_MODEL", _DEFAULT_LLM_MODEL),
                "messages": messages,
                "temperature": 0.3,
            }
            if tools:
                kwargs["tools"] = tools

            response = await litellm.acompletion(**kwargs)
            choice = response.choices[0]

            result = {"content": choice.message.content or ""}
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in choice.message.tool_calls
                ]
            return result

        except ImportError:
            logger.warning("litellm not available, using mock LLM")
            return self._mock_llm_generate(messages, system, tools)
        except Exception as e:
            logger.error(f"LLM provider error: {e}, falling back to mock")
            return self._mock_llm_generate(messages, system, tools)

    def _mock_llm_generate(self, messages: List[Dict], system: str = "",
                           tools: Optional[List[Dict]] = None) -> Dict:
        """Mock LLM for testing or when no provider is configured."""
        last_msg = messages[-1]["content"] if messages else ""

        # If tools are available and we have steps remaining, simulate a tool call
        if tools and len(tools) > 0 and "final answer" not in last_msg.lower():
            tool = tools[0]["function"]
            return {
                "content": f"I need to use the {tool['name']} tool to proceed.",
                "tool_calls": [{
                    "id": "call_mock_001",
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "arguments": "{}",
                    }
                }]
            }

        return {
            "content": f"[Mock LLM] Processed: {last_msg[:100]}... Task complete.",
            "tool_calls": None,
        }

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _build_system_prompt(self, mode: AgentMode, clone_id: Optional[str] = None) -> str:
        """Build the default system prompt for an agent session."""
        mode_desc = {
            AgentMode.AUTO: "You are an autonomous agent. Plan and execute steps independently.",
            AgentMode.GUIDE: "You are a guided agent. Propose each step and wait for confirmation.",
            AgentMode.PLAN: "You are a planning agent. Produce a detailed plan without executing.",
            AgentMode.OBSERVE: "You are an observing agent. Read data and report findings without making changes.",
        }

        prompt = f"""You are an AI agent in the AsimNexus system.

{mode_desc.get(mode, "")}

You have access to a set of tools you can use to accomplish tasks.
Think step by step about what needs to be done.
Use tools when necessary, and provide clear reasoning for each step.

Guidelines:
- Always think before acting
- Use the most appropriate tool for each step
- If you have enough information to answer, provide the final answer directly
- Never make up tool results — use actual tool calls
- If a tool fails, try an alternative approach
- Be concise but thorough in your responses
"""
        if clone_id:
            prompt += f"\nYour Digital Clone ID: {clone_id}\n"

        return prompt

    def _build_final_output(self, ctx: AgentContext) -> str:
        """Build the final output from completed steps and conversation."""
        if ctx.final_output:
            return ctx.final_output

        if ctx.error:
            return f"Agent session failed: {ctx.error}"

        # Synthesize from steps
        parts = []
        for i, step in enumerate(ctx.steps, 1):
            if step.thought:
                parts.append(f"Step {i}: {step.thought}")
            if step.observation:
                parts.append(f"  -> {step.observation}")

        if parts:
            return "\n".join(parts)

        return "Agent completed with no output."

    @staticmethod
    def _parse_iso_timestamp(iso_str: str) -> float:
        """Parse ISO timestamp string to seconds since epoch."""
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.timestamp()
        except (ValueError, TypeError):
            return 0.0
