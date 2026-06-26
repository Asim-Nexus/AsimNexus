"""
ASIMNEXUS Tool Registry
=======================
Central registry for all OS control tools. Stores metadata (risk level,
required capabilities, sandbox requirements) and handler references for
every tool. Provides execute_tool() as the single entry point for
capability-gated tool execution.

Architecture:
  call_tool(tool_id) â†’ ToolRegistry.execute_tool()
    â†’ look up ToolRegistration (metadata + handler)
    â†’ check required capabilities against CapabilityMatrix
    â†’ if denied â†’ PermissionDenied result
    â†’ if allowed â†’ route to tool implementation handler
    â†’ audit-log the execution

Registered tool families (all 5 from openclaw_like_tools/):
  - file.*      (FileTools)
  - process.*   (ProcessTools)
  - system.*    (SystemMonitor)
  - clipboard.* (ClipboardTools)
  - notification.* (NotificationTools)
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from .capability_matrix import Capability, capability_matrix

logger = logging.getLogger("AsimNexus.ToolRegistry")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Enums & Data
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class RiskLevel(Enum):
    """Risk classification for each tool"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolVerdict(str, Enum):
    """Outcome of a tool execution attempt"""
    ALLOWED = "allowed"
    DENIED = "denied"
    ERROR = "error"
    PENDING_HUMAN = "pending_human"


@dataclass
class ToolRegistration:
    """
    Complete registration record for a single tool.

    Fields
    ------
    tool_id : str
        Unique identifier, e.g. ``"clipboard.read"``, ``"file.write"``
    description : str
        Human-readable description of what the tool does
    risk_level : RiskLevel
        LOW / MEDIUM / HIGH / CRITICAL
    required_capabilities : set[Capability]
        Every capability the requesting agent MUST possess
    sandbox_required : bool
        Whether execution MUST happen inside a sandbox (Docker / low-priv)
    handler : Callable | None
        Reference to the async or sync function that implements the tool
    agent_owner : str
        Which agent "owns" this tool (typically ``"system"``)
    requires_confirmation : bool
        Whether human confirmation gate is needed before execution
    undo_supported : bool
        Whether the tool supports an undo operation
    allowed_args : list[str]
        Parameter names that the tool accepts
    """
    tool_id: str
    description: str
    risk_level: RiskLevel
    required_capabilities: Set[Capability]
    sandbox_required: bool = False
    handler: Optional[Callable] = None
    agent_owner: str = "system"
    requires_confirmation: bool = False
    undo_supported: bool = False
    allowed_args: List[str] = field(default_factory=list)


@dataclass
class ToolExecutionResult:
    """
    Structured result returned by ``execute_tool()``.

    Fields
    ------
    success : bool
        True if the tool ran and returned normally
    verdict : ToolVerdict
        ALLOWED | DENIED | ERROR | PENDING_HUMAN
    output : Any
        Return value from the tool implementation (if allowed)
    error : str | None
        Error / denial reason message
    call_id : str
        Unique audit identifier for this call
    execution_ms : float
        Wall-clock time of execution in milliseconds
    required_capabilities : list[str]
        The capability strings that were checked
    """
    success: bool
    verdict: ToolVerdict
    output: Any = None
    error: Optional[str] = None
    call_id: str = ""
    execution_ms: float = 0.0
    required_capabilities: List[str] = field(default_factory=list)


# â”€â”€ Fallback helpers for MicroKernel tools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _get_gpu_status_fallback() -> dict:
    """Get GPU status using psutil (no dedicated GPU method in MicroKernel)."""
    try:
        import psutil
        gpus = []
        # Try nvidia-smi first
        import subprocess
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 4:
                        gpus.append({
                            "name": parts[0],
                            "memory_total_mb": parts[1],
                            "memory_used_mb": parts[2],
                            "utilization_percent": parts[3],
                        })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return {
            "category": "gpu",
            "name": gpus[0]["name"] if gpus else "No GPU detected",
            "status": "ok" if gpus else "unavailable",
            "metrics": {"gpus": gpus} if gpus else {},
            "details": "nvidia-smi not available" if not gpus else "",
        }
    except ImportError:
        return {"category": "gpu", "name": "Unknown", "status": "unknown", "metrics": {}, "details": "psutil not available"}


def _get_battery_status_fallback() -> dict:
    """Get battery status using psutil."""
    try:
        import psutil
        if not hasattr(psutil, "sensors_battery"):
            return {"category": "battery", "name": "Battery", "status": "unavailable", "metrics": {}, "details": "sensors_battery not available"}
        batt = psutil.sensors_battery()
        if batt is None:
            return {"category": "battery", "name": "Battery", "status": "unavailable", "metrics": {}, "details": "No battery detected"}
        return {
            "category": "battery",
            "name": "Battery",
            "status": "ok",
            "metrics": {
                "percent": batt.percent,
                "charging": batt.power_plugged,
                "remaining_sec": batt.secsleft if batt.secsleft != -1 else None,
            },
        }
    except ImportError:
        return {"category": "battery", "name": "Battery", "status": "unknown", "metrics": {}, "details": "psutil not available"}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Registry
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class ToolRegistry:
    """
    Central tool registry for ASIMNEXUS.

    Responsibilities
    ----------------
    * Store rich metadata for every tool (risk, capabilities, sandbox).
    * Map tool IDs to handler callables.
    * Provide ``execute_tool()`` that gates on capabilities and routes to
      the correct implementation.
    * Maintain an in-memory audit buffer of recent executions.
    """

    def __init__(self):
        self._registrations: Dict[str, ToolRegistration] = {}
        self._audit_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = 1000
        self.logger = logging.getLogger("AsimNexus.ToolRegistry")
        self._register_openclaw_tools()

    # â”€â”€ Registration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def register_tool(self, reg: ToolRegistration) -> None:
        """Register (or re-register) a single tool."""
        self._registrations[reg.tool_id] = reg
        caps = ", ".join(c.value for c in reg.required_capabilities)
        self.logger.info(
            f"ðŸ“¦ Tool registered: {reg.tool_id} "
            f"[risk={reg.risk_level.value}, caps={{{caps}}}]"
        )

    def get_tool(self, tool_id: str) -> Optional[ToolRegistration]:
        """Retrieve a tool's full registration record by ID."""
        return self._registrations.get(tool_id)

    def list_tools(self) -> List[ToolRegistration]:
        """Return every registered tool."""
        return list(self._registrations.values())

    def get_required_capabilities(self, tool_id: str) -> Set[Capability]:
        """Return the set of capabilities required to execute *tool_id*."""
        reg = self.get_tool(tool_id)
        return reg.required_capabilities if reg else set()

    # â”€â”€ Execution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        agent_name: str = "AutoModeAgent",
    ) -> ToolExecutionResult:
        """
        Execute a tool through the registry with capability gating.

        Flow
        ----
        1. Look up the tool's ``ToolRegistration``.
        2. For each required capability, call
           ``CapabilityMatrix.check_capability_allowed()``.
        3. If **any** capability is denied â†’ return ``DENIED`` result.
        4. If all allowed â†’ invoke the registered handler with *parameters*.
        5. Audit-log the execution (both denied and allowed).
        """
        t_start = time.monotonic()
        call_id = str(uuid.uuid4())[:12]

        # â”€â”€ Step 1 â€” Look up registration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        reg = self.get_tool(tool_id)
        if reg is None:
            return ToolExecutionResult(
                success=False,
                verdict=ToolVerdict.ERROR,
                error=f"Tool '{tool_id}' is not registered",
                call_id=call_id,
            )

        # â”€â”€ Step 2 â€” Capability check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        denied_caps: List[str] = []
        for cap in reg.required_capabilities:
            allowed, reason = capability_matrix.check_capability_allowed(
                agent_name, cap
            )
            if not allowed:
                denied_caps.append(f"{cap.value}: {reason}")

        if denied_caps:
            result = ToolExecutionResult(
                success=False,
                verdict=ToolVerdict.DENIED,
                error=(
                    f"Permission denied for agent '{agent_name}' on "
                    f"tool '{tool_id}': {'; '.join(denied_caps)}"
                ),
                call_id=call_id,
                required_capabilities=[c.value for c in reg.required_capabilities],
            )
            self._audit_log(result, reg, parameters, agent_name)
            return result

        # â”€â”€ Step 3 â€” Invoke handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        handler = reg.handler
        if handler is None:
            result = ToolExecutionResult(
                success=False,
                verdict=ToolVerdict.ERROR,
                error=f"Tool '{tool_id}' has no handler registered",
                call_id=call_id,
                required_capabilities=[c.value for c in reg.required_capabilities],
            )
            self._audit_log(result, reg, parameters, agent_name)
            return result

        try:
            if asyncio.iscoroutinefunction(handler):
                output = await handler(**parameters)
            else:
                output = handler(**parameters)

            elapsed_ms = (time.monotonic() - t_start) * 1000
            result = ToolExecutionResult(
                success=True,
                verdict=ToolVerdict.ALLOWED,
                output=output,
                call_id=call_id,
                execution_ms=round(elapsed_ms, 2),
                required_capabilities=[c.value for c in reg.required_capabilities],
            )
            self._audit_log(result, reg, parameters, agent_name)
            return result

        except Exception as exc:
            elapsed_ms = (time.monotonic() - t_start) * 1000
            self.logger.error(f"âŒ Tool execution error [{tool_id}]: {exc}")
            result = ToolExecutionResult(
                success=False,
                verdict=ToolVerdict.ERROR,
                error=f"Execution error: {exc}",
                call_id=call_id,
                execution_ms=round(elapsed_ms, 2),
                required_capabilities=[c.value for c in reg.required_capabilities],
            )
            self._audit_log(result, reg, parameters, agent_name)
            return result

    # â”€â”€ Audit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _audit_log(
        self,
        result: ToolExecutionResult,
        reg: ToolRegistration,
        parameters: Dict[str, Any],
        agent_name: str,
    ) -> None:
        """Persist an execution record to the in-memory audit buffer."""
        entry = {
            "call_id": result.call_id,
            "tool_id": reg.tool_id,
            "agent_name": agent_name,
            "verdict": result.verdict.value,
            "risk_level": reg.risk_level.value,
            "required_capabilities": [c.value for c in reg.required_capabilities],
            "parameters_safe": self._safe_params(parameters),
            "output_hash": (
                hashlib.sha256(str(result.output).encode()).hexdigest()[:16]
                if result.output is not None
                else ""
            ),
            "execution_ms": result.execution_ms,
            "error": result.error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._audit_buffer.append(entry)
        if len(self._audit_buffer) > self._max_buffer_size:
            self._audit_buffer = self._audit_buffer[-self._max_buffer_size:]

    # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _safe_params(params: Dict[str, Any]) -> str:
        """Sanitize sensitive parameters for audit logging."""
        safe = {}
        for k, v in params.items():
            if k in ("content", "text", "password", "secret", "key"):
                safe[k] = f"[REDACTED: {len(str(v))} chars]"
            elif isinstance(v, str) and len(v) > 500:
                safe[k] = v[:200] + "..."
            else:
                safe[k] = v
        return json.dumps(safe, default=str)

    def get_audit_log(
        self, limit: int = 50, tool_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return recent audit entries, optionally filtered by tool_id."""
        entries = self._audit_buffer[-limit:] if self._audit_buffer else []
        if tool_id:
            entries = [e for e in entries if e["tool_id"] == tool_id]
        return entries

    # â”€â”€ Built-in tool registration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _register_openclaw_tools(self) -> None:
        """
        Import and register every tool from ``openclaw_like_tools/``
        and the MicroKernelInterface hardware control layer.

        Each registration captures:
        * Tool ID (e.g. ``clipboard.read``)
        * Risk level from ``RiskLevel``
        * Required capabilities from ``Capability``
        * Sandbox requirement
        * Handler reference to the concrete implementation
        """
        # Lazy imports to keep startup lean and avoid circular deps
        from .openclaw_like_tools.file_tools import FileTools
        from .openclaw_like_tools.process_tools import ProcessTools
        from .openclaw_like_tools.system_monitor import get_system_monitor
        from .openclaw_like_tools.clipboard_tools import get_clipboard_tools
        from .openclaw_like_tools.notification_tools import get_notification_tools
        from .microkernel import MicroKernelInterface

        ft = FileTools()
        pt = ProcessTools()
        sm = get_system_monitor()
        ct = get_clipboard_tools()
        nt = get_notification_tools()
        mki = MicroKernelInterface()

        # â”€â”€ File tools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self.register_tool(ToolRegistration(
            tool_id="file.list",
            description="List directory contents with safety filtering",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.FILE_READ_ONLY},
            sandbox_required=False,
            handler=ft.list_directory,
            allowed_args=["path", "show_hidden"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="file.read",
            description="Read file content safely (max 1000 lines, 10 MB, allowed extensions)",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.FILE_READ_ONLY},
            sandbox_required=False,
            handler=ft.read_file,
            allowed_args=["path", "max_lines"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="file.write",
            description="Write content to file safely with backup support",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.FILE_WRITE_SAFE},
            sandbox_required=False,
            requires_confirmation=True,
            undo_supported=True,
            handler=ft.write_file_safe,
            allowed_args=["path", "content", "backup"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="file.copy",
            description="Copy a file safely to a destination path",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.FILE_WRITE_SAFE},
            sandbox_required=False,
            handler=ft.copy_file,
            allowed_args=["src", "dst"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="file.move",
            description="Move (rename) a file safely",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.FILE_WRITE_SAFE},
            sandbox_required=False,
            undo_supported=True,
            handler=ft.move_file,
            allowed_args=["src", "dst"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="file.delete",
            description="Delete a file safely (requires explicit confirmation)",
            risk_level=RiskLevel.HIGH,
            required_capabilities={Capability.FILE_DELETE_SAFE},
            sandbox_required=True,
            requires_confirmation=True,
            handler=ft.delete_file_safe,
            allowed_args=["path", "confirm"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="file.info",
            description="Get file/directory metadata (size, type, permissions)",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.FILE_SYSTEM_INFO},
            sandbox_required=False,
            handler=ft.get_file_info,
            allowed_args=["path"],
        ))

        # â”€â”€ Process tools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self.register_tool(ToolRegistration(
            tool_id="process.list",
            description="List running processes with optional name filter",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.PROCESS_INSPECT},
            sandbox_required=False,
            handler=pt.list_processes,
            allowed_args=["filter_name"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="process.start",
            description="Start an application or script safely",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.PROCESS_MANAGE_LIMITED},
            sandbox_required=False,
            requires_confirmation=True,
            undo_supported=True,
            handler=pt.start_application,
            allowed_args=["app_path", "arguments"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="process.close",
            description="Close a running application safely",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.PROCESS_MANAGE_LIMITED},
            sandbox_required=False,
            requires_confirmation=True,
            handler=pt.close_application,
            allowed_args=["app_name", "force"],
        ))

        # â”€â”€ System monitor tools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self.register_tool(ToolRegistration(
            tool_id="system.cpu",
            description="Get CPU metrics: percent, count, frequency, per-core",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=sm.get_cpu,
        ))
        self.register_tool(ToolRegistration(
            tool_id="system.memory",
            description="Get memory metrics: virtual and swap usage",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=sm.get_memory,
        ))
        self.register_tool(ToolRegistration(
            tool_id="system.disk",
            description="Get disk metrics: partitions, usage, IO",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=sm.get_disk,
        ))
        self.register_tool(ToolRegistration(
            tool_id="system.network",
            description="Get network metrics: interfaces, IO, connections",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=sm.get_network,
        ))
        self.register_tool(ToolRegistration(
            tool_id="system.battery",
            description="Get battery status (percent, plugged, remaining)",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=sm.get_battery,
        ))
        self.register_tool(ToolRegistration(
            tool_id="system.info",
            description="Get comprehensive read-only system information",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=sm.get_system_info,
        ))
        self.register_tool(ToolRegistration(
            tool_id="system.all",
            description="Get all system metrics in one consolidated snapshot",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO, Capability.RESOURCE_MONITOR},
            sandbox_required=False,
            handler=sm.get_all_metrics,
        ))

        # â”€â”€ Clipboard tools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self.register_tool(ToolRegistration(
            tool_id="clipboard.read",
            description="Read clipboard content (requires user consent)",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.CLIPBOARD_ACCESS},
            sandbox_required=False,
            requires_confirmation=True,
            handler=ct.read_clipboard,
            allowed_args=["user_id", "consent_if_needed"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="clipboard.write",
            description="Write text to clipboard (requires user consent)",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.CLIPBOARD_ACCESS},
            sandbox_required=False,
            requires_confirmation=True,
            undo_supported=True,
            handler=ct.write_clipboard,
            allowed_args=["text", "user_id"],
        ))

        # â”€â”€ Notification tools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self.register_tool(ToolRegistration(
            tool_id="notification.send",
            description="Send a system notification to the user",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.NOTIFICATION_SEND},
            sandbox_required=False,
            handler=nt.send_notification,
            allowed_args=["title", "message", "urgency", "timeout_seconds"],
        ))

        # â”€â”€ MicroKernel hardware tools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Read-only hardware status (INFO risk)
        self.register_tool(ToolRegistration(
            tool_id="hw.status",
            description="Get comprehensive hardware status across all components (CPU, memory, disk, network)",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki.get_system_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.cpu",
            description="Get CPU status: usage, core count, frequency",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_cpu_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.memory",
            description="Get memory status: total, available, used, percent",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_memory_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.disk",
            description="Get disk status: partitions, usage per mount point",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_disk_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.network",
            description="Get network status: interfaces, IP addresses, IO counters",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_network_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.gpu",
            description="Get GPU status: name, memory (MB), driver version, temperature",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_gpu_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.npu",
            description="Get NPU / AI accelerator status: name, vendor, driver",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_npu_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.motherboard",
            description="Get motherboard / baseboard information: manufacturer, model, serial, version",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_motherboard_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.chipset",
            description="Get chipset information: name, manufacturer, driver version",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_chipset_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.ram",
            description="Get RAM module information: bank, capacity, speed, type, manufacturer for each module",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_ram_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.rom",
            description="Get ROM / BIOS / firmware information: vendor, version, date",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_rom_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.storage_controller",
            description="Get storage controller information: SATA/NVMe/SCSI controllers, driver versions",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_storage_controller_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.usb",
            description="Get USB device information: count of connected USB devices",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_usb_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.display",
            description="Get display/monitor information: name, type, resolution",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_display_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.audio",
            description="Get audio device information: name, manufacturer, status",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_audio_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.sensor",
            description="Get hardware sensor information: temperatures, fans, voltages",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_sensor_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.thermal",
            description="Get thermal/cooling status: fan speeds, cooling devices",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_thermal_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.bios",
            description="Get BIOS / UEFI firmware status: vendor, version, release date",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki._get_bios_status,
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.battery",
            description="Get battery status via psutil (percent, charging, remaining time)",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=lambda: _get_battery_status_fallback(),
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.all",
            description="Get ALL hardware status in one consolidated snapshot (CPU, GPU, NPU, motherboard, chipset, RAM, ROM, storage, USB, display, audio, sensors, thermal, BIOS, battery)",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO, Capability.RESOURCE_MONITOR},
            sandbox_required=False,
            handler=mki.get_all_hardware_status,
        ))

        # Power management (CONTROL/POWER risk â€” requires confirmation)
        self.register_tool(ToolRegistration(
            tool_id="hw.power.shutdown",
            description="Shutdown the system (requires human confirmation)",
            risk_level=RiskLevel.HIGH,
            required_capabilities={Capability.SYSTEM_SHUTDOWN},
            sandbox_required=False,
            requires_confirmation=True,
            handler=lambda force=False: mki.execute_operation("shutdown", "system", {"force": force}),
            allowed_args=["force"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.power.restart",
            description="Restart the system (requires human confirmation)",
            risk_level=RiskLevel.HIGH,
            required_capabilities={Capability.SYSTEM_REBOOT},
            sandbox_required=False,
            requires_confirmation=True,
            handler=lambda force=False: mki.execute_operation("restart", "system", {"force": force}),
            allowed_args=["force"],
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.power.sleep",
            description="Put the system to sleep",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            requires_confirmation=True,
            handler=lambda: mki.execute_operation("sleep", "system"),
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.power.hibernate",
            description="Hibernate the system (requires human confirmation)",
            risk_level=RiskLevel.HIGH,
            required_capabilities={Capability.SYSTEM_SHUTDOWN},
            sandbox_required=False,
            requires_confirmation=True,
            handler=lambda: mki.execute_operation("hibernate", "system"),
        ))
        self.register_tool(ToolRegistration(
            tool_id="hw.power.scheme",
            description="Set power scheme: balanced, power_saver, high_performance",
            risk_level=RiskLevel.MEDIUM,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            requires_confirmation=True,
            handler=lambda scheme="balanced": mki._set_power_scheme(scheme),
            allowed_args=["scheme"],
        ))

        # Driver management (DRIVER risk â€” requires confirmation)
        self.register_tool(ToolRegistration(
            tool_id="hw.drivers.list",
            description="List installed drivers (Windows only)",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki.list_drivers,
        ))

        # MicroKernel stats
        self.register_tool(ToolRegistration(
            tool_id="hw.stats",
            description="Get MicroKernel interface statistics (operation counts, risk breakdown)",
            risk_level=RiskLevel.LOW,
            required_capabilities={Capability.SYSTEM_INFO},
            sandbox_required=False,
            handler=mki.get_stats,
        ))

        self.logger.info(
            f"âœ… ToolRegistry initialised â€” "
            f"{len(self._registrations)} openclaw + microkernel tools registered"
        )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# Global singleton
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

tool_registry = ToolRegistry()
