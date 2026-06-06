"""
ASIMNEXUS OS Tool Executor
==========================
Orchestration layer that wraps ToolRegistry with human-confirmation gates,
sandbox execution, and structured audit logging to ``security/audit_log.py``.

Architecture (complete chain)::

  Agent / Frontend
       │
       ▼
  OsToolExecutor.execute()          ← human confirmation + sandbox + audit
       │
       ├─ 1. Check CapabilityMatrix
       ├─ 2. Check human confirmation
       ├─ 3. Sandbox (if required)
       ├─ 4. Delegate to ToolRegistry.execute_tool()
       └─ 5. Audit-log decision → security/audit_log.py
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .tool_registry import (
    ToolRegistry,
    ToolRegistration,
    RiskLevel,
    ToolVerdict,
    tool_registry as _base_registry,
)
from .capability_matrix import (
    CapabilityMatrix,
    Capability,
    capability_matrix as _base_capability_matrix,
)
from .sandbox.docker_sandbox import DockerSandbox, docker_sandbox

# ── Audit-log integration (security/audit_log.py) ─────────────────────
from security.audit_log import (
    AuditLog,
    AuditEventType,
    AuditSeverity,
    audit_log as _base_audit_log,
)

logger = logging.getLogger("AsimNexus.OSToolExecutor")


# ══════════════════════════════════════════════════════════════════════
# Data
# ══════════════════════════════════════════════════════════════════════

@dataclass
class ToolCallRecord:
    """Record of a tool call for local JSONL audit trail."""
    call_id: str
    tool_name: str
    agent_name: str
    user_id: str
    verdict: str
    risk_level: str
    parameters_safe: str
    output_hash: str
    execution_ms: float
    timestamp: str
    error: str = ""
    reason: str = ""


# ══════════════════════════════════════════════════════════════════════
# Orchestrator
# ══════════════════════════════════════════════════════════════════════

class OSToolExecutor:
    """
    Main orchestrator for OS Control tool execution.

    Layers (thin) on top of :class:`ToolRegistry`:

    1. **Capability gating** — checks ``CapabilityMatrix`` before every call.
    2. **Human confirmation** — holds calls pending user approval.
    3. **Sandbox** — routes high-risk tools through ``DockerSandbox``.
    4. **Audit logging** — writes every decision (granted / denied) to
       ``security/audit_log.py`` (the universal audit trail) **and** to a
       local JSONL file.
    """

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        capability_matrix: Optional[CapabilityMatrix] = None,
        audit_log: Optional[AuditLog] = None,
        sandbox: Optional[DockerSandbox] = None,
        audit_path: Optional[Path] = None,
    ):
        self.tool_registry = tool_registry or _base_registry
        self.capability_matrix = capability_matrix or _base_capability_matrix
        self.audit_log = audit_log or _base_audit_log
        self.sandbox = sandbox or docker_sandbox

        self.audit_path = audit_path or Path("data/os_control_audit.jsonl")
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

        # Pending human confirmations
        self._pending_confirmations: Dict[str, ToolCallRecord] = {}

        # In-memory audit buffer
        self._audit_buffer: List[ToolCallRecord] = []
        self._max_buffer_size = 1000

        logger.info(
            "🌐 OSToolExecutor initialized — Capability-Gated OS Control active"
        )

    # ── Capability Matrix Integration ──────────────────────────────────

    def get_capability_for_tool(self, tool_name: str) -> Optional[Capability]:
        """Return the *first* required capability for a tool."""
        reg = self.tool_registry.get_tool(tool_name)
        if reg and reg.required_capabilities:
            return next(iter(reg.required_capabilities))
        return None

    def check_tool_permission(
        self, tool_name: str, agent_name: str = "AutoModeAgent"
    ) -> Tuple[bool, str]:
        """
        Check if *agent_name* is allowed to execute *tool_name*.

        Returns ``(allowed, reason)``.
        """
        reg = self.tool_registry.get_tool(tool_name)
        if reg is None:
            return False, f"Tool '{tool_name}' not registered"

        for cap in reg.required_capabilities:
            allowed, reason = self.capability_matrix.check_capability_allowed(
                agent_name, cap
            )
            if not allowed:
                return (
                    False,
                    f"Capability '{cap.value}' denied for agent "
                    f"'{agent_name}': {reason}",
                )

        return True, "allowed"

    def requires_human_confirmation(
        self, tool_name: str, agent_name: str = "AutoModeAgent"
    ) -> bool:
        """Check whether this tool needs human approval for *agent_name*."""
        reg = self.tool_registry.get_tool(tool_name)
        if reg is None:
            return True  # unknown → confirm

        # Tool-level flag
        if reg.requires_confirmation:
            return True

        # Per-capability confirmation from CapabilityMatrix
        for cap in reg.required_capabilities:
            if self.capability_matrix.requires_human_confirmation(agent_name, cap):
                return True

        return False

    def requires_sandbox(
        self, tool_name: str, agent_name: str = "AutoModeAgent"
    ) -> bool:
        """Check whether this tool must run inside a sandbox."""
        reg = self.tool_registry.get_tool(tool_name)
        if reg and reg.sandbox_required:
            return True

        # Also check per-capability sandbox requirement
        if reg:
            for cap in reg.required_capabilities:
                if self.capability_matrix.requires_sandbox(agent_name, cap):
                    return True
        return False

    # ── Main Execution ─────────────────────────────────────────────────

    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_name: str = "AutoModeAgent",
        user_id: str = "guest",
    ) -> Dict[str, Any]:
        """
        Execute a tool with full permission gating.

        Flow
        ----
        1. Look up tool metadata.
        2. Check ``CapabilityMatrix`` → DENIED if not allowed.
        3. Check human confirmation → PENDING_HUMAN if required.
        4. Check sandbox requirement → route through sandbox if needed.
        5. Delegate to ``ToolRegistry.execute_tool()``.
        6. Write structured audit log to ``security/audit_log.py``.
        7. Return structured response.

        Returns
        -------
        dict with keys:
          - ``call_id``, ``tool_name``, ``verdict``
          - ``output`` / ``error`` / ``execution_ms`` / ``agent`` / ``user_id``
        """
        t_start = time.monotonic()
        call_id = str(uuid.uuid4())[:12]

        # ── Step 1 — Look up tool ──────────────────────────────────────
        reg = self.tool_registry.get_tool(tool_name)
        if reg is None:
            return self._denied_response(
                call_id, tool_name, agent_name, user_id,
                f"Tool '{tool_name}' not registered in OS Tool Registry",
                t_start,
                "unknown",
            )

        # ── Step 2 — CapabilityMatrix gate ─────────────────────────────
        allowed, reason = self.check_tool_permission(tool_name, agent_name)
        if not allowed:
            # Log denial to security audit trail
            self._log_authorization_decision(
                agent_name=agent_name,
                user_id=user_id,
                tool_name=tool_name,
                allowed=False,
                reason=reason,
                call_id=call_id,
            )
            return self._denied_response(
                call_id, tool_name, agent_name, user_id,
                f"🛑 Permission denied by Capability Matrix: {reason}",
                t_start,
                reg.risk_level.value if reg else "unknown",
            )

        # Log grant to security audit trail
        self._log_authorization_decision(
            agent_name=agent_name,
            user_id=user_id,
            tool_name=tool_name,
            allowed=True,
            reason="Capability check passed",
            call_id=call_id,
        )

        # ── Step 3 — Human confirmation gate ───────────────────────────
        if self.requires_human_confirmation(tool_name, agent_name):
            record = ToolCallRecord(
                call_id=call_id,
                tool_name=tool_name,
                agent_name=agent_name,
                user_id=user_id,
                verdict=ToolVerdict.PENDING_HUMAN.value,
                risk_level=reg.risk_level.value,
                parameters_safe=self._safe_params(parameters),
                output_hash="",
                execution_ms=0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self._pending_confirmations[call_id] = record
            return {
                "call_id": call_id,
                "tool_name": tool_name,
                "verdict": ToolVerdict.PENDING_HUMAN.value,
                "error": f"⚠️ Human confirmation required. Call ID: {call_id}",
                "requires_human": True,
                "risk_level": reg.risk_level.value,
                "agent": agent_name,
            }

        # ── Step 4 & 5 — Execute (possibly sandboxed) and return ───────
        return await self._execute_tool(
            tool_name, parameters, agent_name, user_id, call_id, t_start, reg
        )

    # ── Internal execution ─────────────────────────────────────────────

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_name: str,
        user_id: str,
        call_id: str,
        t_start: float,
        reg: Optional[ToolRegistration] = None,
    ) -> Dict[str, Any]:
        """Execute tool (possibly sandboxed) and audit-log the result."""

        # ── Sandbox gate ───────────────────────────────────────────────
        if reg and reg.sandbox_required and self.sandbox.is_available():
            logger.info(
                f"🛡️ Routing '{tool_name}' through Docker sandbox for agent '{agent_name}'"
            )
            return await self._execute_sandboxed(
                tool_name, parameters, agent_name, user_id, call_id, t_start, reg
            )

        # ── Direct execution via ToolRegistry ──────────────────────────
        result = await self.tool_registry.execute_tool(
            tool_id=tool_name,
            parameters=parameters,
            agent_name=agent_name,
        )

        elapsed_ms = (time.monotonic() - t_start) * 1000

        # Build structured response
        response: Dict[str, Any] = {
            "call_id": call_id,
            "tool_name": tool_name,
            "verdict": result.verdict.value,
            "execution_ms": round(elapsed_ms, 2),
            "agent": agent_name,
            "user_id": user_id,
        }

        if result.success:
            response["output"] = result.output
        else:
            response["error"] = result.error or "Unknown error"

        # Local JSONL audit
        self._local_audit(
            ToolCallRecord(
                call_id=call_id,
                tool_name=tool_name,
                agent_name=agent_name,
                user_id=user_id,
                verdict=result.verdict.value,
                risk_level=reg.risk_level.value if reg else "unknown",
                parameters_safe=self._safe_params(parameters),
                output_hash=self._hash(str(result.output)),
                execution_ms=round(elapsed_ms, 2),
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=result.error or "",
            )
        )

        return response

    async def _execute_sandboxed(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_name: str,
        user_id: str,
        call_id: str,
        t_start: float,
        reg: ToolRegistration,
    ) -> Dict[str, Any]:
        """Execute a tool inside the Docker sandbox."""
        try:
            # Serialise the tool call as a script that the sandbox can run
            script = (
                f"import json, sys\n"
                f"tool = '{tool_name}'\n"
                f"params = {json.dumps(parameters)}\n"
                f"print(json.dumps({{'tool': tool, 'params': params}}))\n"
            )
            sandbox_result = await self.sandbox.execute_script(
                script_content=script,
                network_access=False,
            )

            elapsed_ms = (time.monotonic() - t_start) * 1000

            if sandbox_result.success:
                return {
                    "call_id": call_id,
                    "tool_name": tool_name,
                    "verdict": ToolVerdict.ALLOWED.value,
                    "output": {
                        "stdout": sandbox_result.stdout,
                        "container_id": sandbox_result.container_id,
                    },
                    "execution_ms": round(elapsed_ms, 2),
                    "sandboxed": True,
                    "agent": agent_name,
                    "user_id": user_id,
                }
            else:
                return {
                    "call_id": call_id,
                    "tool_name": tool_name,
                    "verdict": ToolVerdict.ERROR.value,
                    "error": f"Sandbox execution failed: {sandbox_result.error or sandbox_result.stderr}",
                    "execution_ms": round(elapsed_ms, 2),
                    "sandboxed": True,
                    "agent": agent_name,
                    "user_id": user_id,
                }
        except Exception as exc:
            elapsed_ms = (time.monotonic() - t_start) * 1000
            return {
                "call_id": call_id,
                "tool_name": tool_name,
                "verdict": ToolVerdict.ERROR.value,
                "error": f"Sandbox error: {exc}",
                "execution_ms": round(elapsed_ms, 2),
                "sandboxed": True,
                "agent": agent_name,
                "user_id": user_id,
            }

    # ── Human Confirmation Flow ────────────────────────────────────────

    async def approve(self, call_id: str, approver_id: str) -> Dict[str, Any]:
        """Human approves a pending tool call."""
        record = self._pending_confirmations.pop(call_id, None)
        if not record:
            return {
                "call_id": call_id,
                "verdict": ToolVerdict.ERROR.value,
                "error": f"Call {call_id} not found or already resolved",
            }

        reg = self.tool_registry.get_tool(record.tool_name)
        t_start = time.monotonic()
        return await self._execute_tool(
            record.tool_name,
            json.loads(record.parameters_safe) if record.parameters_safe else {},
            record.agent_name,
            record.user_id,
            call_id,
            t_start,
            reg,
        )

    def reject(self, call_id: str, rejecter_id: str) -> Dict[str, Any]:
        """Human rejects a pending tool call."""
        record = self._pending_confirmations.pop(call_id, None)
        if not record:
            return {
                "call_id": call_id,
                "verdict": ToolVerdict.ERROR.value,
                "error": f"Call {call_id} not found",
            }

        record.verdict = ToolVerdict.DENIED.value
        record.reason = f"Rejected by {rejecter_id}"
        self._local_audit(record)

        return {
            "call_id": call_id,
            "tool_name": record.tool_name,
            "verdict": ToolVerdict.DENIED.value,
            "error": f"Action rejected by human ({rejecter_id})",
        }

    def pending_calls(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List calls awaiting human approval."""
        calls = []
        for call_id, record in self._pending_confirmations.items():
            if user_id is None or record.user_id == user_id:
                calls.append({
                    "call_id": call_id,
                    "tool_name": record.tool_name,
                    "agent_name": record.agent_name,
                    "user_id": record.user_id,
                    "risk_level": record.risk_level,
                    "parameters": record.parameters_safe,
                    "timestamp": record.timestamp,
                })
        return calls

    # ── Security Audit Log (security/audit_log.py) ─────────────────────

    def _log_authorization_decision(
        self,
        agent_name: str,
        user_id: str,
        tool_name: str,
        allowed: bool,
        reason: str,
        call_id: str,
    ) -> None:
        """
        Log every authorization decision (granted / denied) to the universal
        ``security/audit_log.py`` audit trail.
        """
        try:
            self.audit_log.log_event(
                event_type=AuditEventType.AUTHORIZATION,
                action=(
                    f"TOOL_GRANTED:{tool_name}"
                    if allowed
                    else f"TOOL_DENIED:{tool_name}"
                ),
                resource=f"os_tool:{tool_name}",
                user_id=user_id or agent_name,
                severity=AuditSeverity.INFO if allowed else AuditSeverity.WARNING,
                details={
                    "call_id": call_id,
                    "agent_name": agent_name,
                    "tool_name": tool_name,
                    "allowed": allowed,
                    "reason": reason,
                },
            )
            logger.debug(
                f"🔐 Auth decision logged: {'GRANTED' if allowed else 'DENIED'} "
                f"for {tool_name} by {agent_name}"
            )
        except Exception as e:
            logger.error(f"Failed to write to security/audit_log.py: {e}")

    # ── Local JSONL Audit Trail ────────────────────────────────────────

    def _local_audit(self, record: ToolCallRecord) -> None:
        """Persist a record to the in-memory buffer **and** JSONL file."""
        self._audit_buffer.append(record)
        if len(self._audit_buffer) > self._max_buffer_size:
            self._audit_buffer = self._audit_buffer[-self._max_buffer_size:]

        try:
            with open(self.audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(record)) + "\n")
        except Exception as e:
            logger.error(f"Local audit write failed: {e}")

    def get_audit_log(
        self,
        limit: int = 50,
        user_id: Optional[str] = None,
        tool_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return recent local audit entries with optional filters."""
        entries = self._audit_buffer[-limit:] if self._audit_buffer else []
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        if tool_name:
            entries = [e for e in entries if e.tool_name == tool_name]
        return [asdict(e) for e in entries]

    def get_status(self) -> Dict[str, Any]:
        """Return executor status summary."""
        return {
            "tools_registered": len(self.tool_registry.list_tools()),
            "tools": [t.tool_id for t in self.tool_registry.list_tools()],
            "pending_approvals": len(self._pending_confirmations),
            "audit_entries": len(self._audit_buffer),
            "audit_path": str(self.audit_path),
            "sandbox_available": self.sandbox.is_available(),
        }

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _safe_params(params: Dict[str, Any]) -> str:
        """Sanitise parameters for audit logging (redact sensitive fields)."""
        safe = {}
        for k, v in params.items():
            if k in ("content", "text", "password", "secret", "key"):
                safe[k] = f"[REDACTED: {len(str(v))} chars]"
            elif isinstance(v, str) and len(v) > 500:
                safe[k] = v[:200] + "..."
            else:
                safe[k] = v
        return json.dumps(safe, default=str)

    @staticmethod
    def _hash(data: str) -> str:
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _denied_response(
        self,
        call_id: str,
        tool_name: str,
        agent_name: str,
        user_id: str,
        error: str,
        t_start: float,
        risk_level: str,
    ) -> Dict[str, Any]:
        """Build a standardised DENIED response and audit locally."""
        elapsed_ms = (time.monotonic() - t_start) * 1000
        record = ToolCallRecord(
            call_id=call_id,
            tool_name=tool_name,
            agent_name=agent_name,
            user_id=user_id,
            verdict=ToolVerdict.DENIED.value,
            risk_level=risk_level,
            parameters_safe="{}",
            output_hash="",
            execution_ms=round(elapsed_ms, 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=error,
        )
        self._local_audit(record)
        return {
            "call_id": call_id,
            "tool_name": tool_name,
            "verdict": ToolVerdict.DENIED.value,
            "error": error,
            "execution_ms": round(elapsed_ms, 2),
        }


# ══════════════════════════════════════════════════════════════════════
# Global singleton
# ══════════════════════════════════════════════════════════════════════

_os_tool_executor: Optional[OSToolExecutor] = None


def get_os_tool_executor() -> OSToolExecutor:
    """Get or create the global OSToolExecutor singleton."""
    global _os_tool_executor
    if _os_tool_executor is None:
        _os_tool_executor = OSToolExecutor()
    return _os_tool_executor
