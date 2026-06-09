#!/usr/bin/env python3
"""
STATUS: NEW — Phase 1d Odysseus Integration
Audit Integration — Records all agent tool executions for audit trail.

Stores tool calls, results, and veto decisions in memory and optionally
persists to the audit_bus system (core/audit_bus.py).

Features:
- In-memory ring buffer with configurable max entries
- Query by user, tool, or veto status
- Aggregate statistics (pass/block rates, most-used tools, etc.)
- Optional persistence via core/audit_bus.emit_audit()
- Singleton factory for application-wide auditor
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolAuditEntry:
    """A single tool execution audit record.

    Captures everything needed for post-hoc review and compliance analysis:
    who ran which tool, with what arguments, what the veto said, how long it
    took, and whether it succeeded.
    """

    tool_name: str
    arguments: Dict[str, Any]
    result_summary: str
    veto_result: Optional[Dict] = None
    user_id: str = "anonymous"
    clone_id: Optional[str] = None
    session_id: Optional[str] = None
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "tool_name": self.tool_name,
            "arguments": self._safe_serialize(self.arguments),
            "result_summary": self.result_summary,
            "veto_result": self.veto_result,
            "user_id": self.user_id,
            "clone_id": self.clone_id,
            "session_id": self.session_id,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def _safe_serialize(obj: Any) -> Any:
        """Recursively sanitize arguments for JSON serialization."""
        if isinstance(obj, dict):
            return {k: ToolAuditEntry._safe_serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [ToolAuditEntry._safe_serialize(v) for v in obj]
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if obj is None:
            return None
        # Fallback: convert to string
        return str(obj)


class ToolAuditor:
    """Records and queries tool execution history for audit purposes.

    Uses an in-memory ring buffer (``max_entries``) to bound memory usage.
    For long-term persistence, entries are also forwarded to the audit_bus
    system when available.
    """

    def __init__(self, max_entries: int = 1000):
        self._entries: List[ToolAuditEntry] = []
        self._max_entries = max_entries
        self._lock = threading.RLock()
        self._audit_bus_available = False

        # Try to connect to audit_bus for optional persistence
        try:
            from core.audit_bus import emit_audit as _emit
            self._emit_audit = _emit
            self._audit_bus_available = True
        except ImportError:
            self._emit_audit = None
            logger.info(
                "core.audit_bus not available — audit records are in-memory only. "
                "Install core.audit_bus for persistent audit trail."
            )
        except Exception as e:
            self._emit_audit = None
            logger.warning("Failed to connect audit_bus: %s", e)

        logger.info(
            "ToolAuditor initialized (max_entries=%d, audit_bus=%s)",
            max_entries,
            self._audit_bus_available,
        )

    # ── Recording ──────────────────────────────────────────────────────────────

    def record(self, entry: ToolAuditEntry):
        """Record a tool execution.

        Appends to the in-memory ring buffer and, if available, forwards to the
        audit_bus system for durable persistence.

        Args:
            entry: The ToolAuditEntry to record.
        """
        with self._lock:
            # Enforce max entries (ring buffer)
            if len(self._entries) >= self._max_entries:
                self._entries.pop(0)
            self._entries.append(entry)

        # Optionally persist to audit_bus
        if self._emit_audit is not None:
            try:
                self._emit_audit({
                    "event_type": "tool_execution",
                    "component": "ToolAuditor",
                    "data": entry.to_dict(),
                    "severity": "info" if entry.success else "error",
                    "status": "ok" if entry.success else "failed",
                })
            except Exception as e:
                logger.warning("Failed to emit audit to audit_bus: %s", e)

    # ── Queries ────────────────────────────────────────────────────────────────

    def get_recent(self, limit: int = 50) -> List[ToolAuditEntry]:
        """Get the most recent audit entries.

        Args:
            limit: Maximum number of entries to return (default 50).

        Returns:
            List of ToolAuditEntry, newest first.
        """
        with self._lock:
            return list(reversed(self._entries[-limit:]))

    def get_by_user(self, user_id: str, limit: int = 50) -> List[ToolAuditEntry]:
        """Get audit entries for a specific user.

        Args:
            user_id: The user identifier to filter by.
            limit: Maximum number of entries to return.

        Returns:
            List of matching ToolAuditEntry, newest first.
        """
        with self._lock:
            matches = [e for e in self._entries if e.user_id == user_id]
            return list(reversed(matches[-limit:]))

    def get_by_tool(self, tool_name: str, limit: int = 50) -> List[ToolAuditEntry]:
        """Get audit entries for a specific tool.

        Args:
            tool_name: The tool name to filter by (e.g., "execute_bash").
            limit: Maximum number of entries to return.

        Returns:
            List of matching ToolAuditEntry, newest first.
        """
        with self._lock:
            matches = [e for e in self._entries if e.tool_name == tool_name]
            return list(reversed(matches[-limit:]))

    def get_vetoed_calls(self, limit: int = 50) -> List[ToolAuditEntry]:
        """Get all tool calls that were vetoed (blocked by Dharma Chakra).

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of matching ToolAuditEntry, newest first.
        """
        with self._lock:
            matches = [
                e for e in self._entries
                if e.veto_result and not e.veto_result.get("allowed", True)
            ]
            return list(reversed(matches[-limit:]))

    def get_failed_calls(self, limit: int = 50) -> List[ToolAuditEntry]:
        """Get all tool calls that resulted in an error.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of matching ToolAuditEntry, newest first.
        """
        with self._lock:
            matches = [e for e in self._entries if not e.success]
            return list(reversed(matches[-limit:]))

    # ── Statistics ─────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Get comprehensive audit statistics.

        Returns:
            Dict with keys:
                - total_calls: Total tool executions recorded.
                - total_users: Number of unique users.
                - total_tools: Number of unique tools used.
                - by_tool: Per-tool breakdown dict.
                - by_user: Per-user breakdown dict.
                - vetoed: Number of calls blocked by veto.
                - veto_rate: Fraction of calls that were vetoed (0.0-1.0).
                - failed: Number of calls that failed.
                - failure_rate: Fraction of calls that failed (0.0-1.0).
                - avg_duration_ms: Average execution duration in ms.
                - most_used_tool: Name of the most frequently used tool.
                - most_active_user: User with the most tool calls.
        """
        with self._lock:
            total = len(self._entries)
            if total == 0:
                return {
                    "total_calls": 0,
                    "total_users": 0,
                    "total_tools": 0,
                    "by_tool": {},
                    "by_user": {},
                    "vetoed": 0,
                    "veto_rate": 0.0,
                    "failed": 0,
                    "failure_rate": 0.0,
                    "avg_duration_ms": 0.0,
                    "most_used_tool": None,
                    "most_active_user": None,
                }

            # Per-tool counts
            tool_counts: Dict[str, int] = {}
            # Per-user counts
            user_counts: Dict[str, int] = {}
            # Veto and failure counters
            vetoed_count = 0
            failed_count = 0
            total_duration = 0.0

            for entry in self._entries:
                tool_counts[entry.tool_name] = tool_counts.get(entry.tool_name, 0) + 1
                user_counts[entry.user_id] = user_counts.get(entry.user_id, 0) + 1

                if entry.veto_result and not entry.veto_result.get("allowed", True):
                    vetoed_count += 1
                if not entry.success:
                    failed_count += 1
                total_duration += entry.duration_ms

            # Most used tool
            most_used_tool = max(tool_counts, key=tool_counts.get) if tool_counts else None
            # Most active user
            most_active_user = max(user_counts, key=user_counts.get) if user_counts else None

            return {
                "total_calls": total,
                "total_users": len(user_counts),
                "total_tools": len(tool_counts),
                "by_tool": dict(sorted(tool_counts.items(), key=lambda x: -x[1])),
                "by_user": dict(sorted(user_counts.items(), key=lambda x: -x[1])),
                "vetoed": vetoed_count,
                "veto_rate": round(vetoed_count / max(total, 1), 4),
                "failed": failed_count,
                "failure_rate": round(failed_count / max(total, 1), 4),
                "avg_duration_ms": round(total_duration / max(total, 1), 2),
                "most_used_tool": most_used_tool,
                "most_active_user": most_active_user,
            }

    def clear(self):
        """Clear all audit entries (useful for testing)."""
        with self._lock:
            self._entries.clear()
            logger.info("ToolAuditor cleared all entries")


# ─── Singleton Factory ──────────────────────────────────────────────────────────

_auditor_instance: Optional[ToolAuditor] = None
_auditor_lock = threading.Lock()


def get_tool_auditor() -> ToolAuditor:
    """Factory function returning a singleton ToolAuditor.

    The singleton is lazily initialized on first call and shares state across
    the entire application.  For testing, call ``reset_tool_auditor()`` to get
    a clean instance.
    """
    global _auditor_instance
    if _auditor_instance is None:
        with _auditor_lock:
            if _auditor_instance is None:
                _auditor_instance = ToolAuditor()
                logger.debug("ToolAuditor singleton created")
    return _auditor_instance


def reset_tool_auditor() -> None:
    """Reset the ToolAuditor singleton (for testing).

    Clears all entries in the current auditor and replaces it with a fresh
    instance.
    """
    global _auditor_instance
    with _auditor_lock:
        if _auditor_instance is not None:
            _auditor_instance.clear()
        _auditor_instance = None
    logger.info("ToolAuditor singleton reset")


# ─── Module Exports ─────────────────────────────────────────────────────────────

__all__ = [
    "ToolAuditEntry",
    "ToolAuditor",
    "get_tool_auditor",
    "reset_tool_auditor",
]
