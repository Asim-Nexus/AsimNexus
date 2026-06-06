#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade observability, telemetry, and trust posture tracking
ASIMNEXUS Observability Subsystem
=================================
Collects normalized telemetry event envelopes, writes to data/telemetry.jsonl,
evaluates dynamic security postures, and tracks execution lineages.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.telemetry_schema import validate_event, normalize_event
from core.trust_posture import assess_posture, posture_reason

logger = logging.getLogger("ASIMObservability")

TELEMETRY_LOG_PATH = Path("data/telemetry.jsonl")
TELEMETRY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


class ObservabilityCollector:
    """Manages active telemetry, in-memory event queues, and computes trust posture."""

    def __init__(self):
        self.events_buffer: List[Dict[str, Any]] = []
        self.policy_score = 1.0  # Perfect score to start
        self.device_trust = "trusted"
        self.session_start = datetime.utcnow()
        self.mode = "personal"

    def _append_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Validate, buffer, and persist event to telemetry.jsonl."""
        validated = validate_event(event)
        self.events_buffer.append(validated)
        
        # Cap memory buffer
        if len(self.events_buffer) > 1000:
            self.events_buffer = self.events_buffer[-1000:]

        try:
            with open(TELEMETRY_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(validated) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to telemetry log: {e}")
            
        return validated

    def record_request(self, *, request_id: str, path: str, method: str, status_code: int, latency_ms: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Record standard backend HTTP request event."""
        event = {
            "request_id": request_id,
            "trace_id": context.get("trace_id"),
            "span_id": context.get("span_id"),
            "user_id": context.get("user_id"),
            "device_id": context.get("device_id"),
            "session_id": context.get("session_id"),
            "component": "backend",
            "action": "request",
            "severity": "info" if status_code < 400 else "warning" if status_code < 500 else "error",
            "status": "ok" if status_code < 400 else "failed",
            "latency_ms": latency_ms,
            "privacy_level": context.get("privacy_level", "public"),
            "mode": context.get("mode", "personal"),
            "message": f"HTTP {method} {path} returned status {status_code}"
        }
        return self._append_event(event)

    def record_decision(self, *, action: str, decision: str, reason: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Record security policy gating allow/deny decision."""
        # Adjust policy score dynamically for denials
        if decision == "deny":
            self.policy_score = max(0.0, self.policy_score - 0.15)
        elif decision == "blocked":
            self.policy_score = max(0.0, self.policy_score - 0.25)

        event = {
            "request_id": context.get("request_id"),
            "trace_id": context.get("trace_id"),
            "user_id": context.get("user_id"),
            "component": "policy",
            "action": "decision",
            "severity": "info" if decision == "allow" else "warning" if decision == "review" else "critical",
            "status": "ok" if decision == "allow" else "blocked",
            "policy": {
                "rule_id": action,
                "decision": decision,
                "reason": reason
            },
            "privacy_level": context.get("privacy_level", "public"),
            "mode": context.get("mode", "personal"),
            "message": f"Policy decision: {decision} on action {action}. Reason: {reason}"
        }
        return self._append_event(event)

    def record_tool_call(self, *, tool_name: str, model: Optional[str], route: str, latency_ms: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Record tool invocation, parameters, and model routers."""
        event = {
            "request_id": context.get("request_id"),
            "trace_id": context.get("trace_id"),
            "user_id": context.get("user_id"),
            "component": "core",
            "action": "tool_call",
            "severity": "info",
            "status": "ok" if route != "blocked" else "blocked",
            "latency_ms": latency_ms,
            "tool": {
                "name": tool_name,
                "selected_model": model,
                "route": route
            },
            "privacy_level": context.get("privacy_level", "public"),
            "mode": context.get("mode", "personal"),
            "message": f"Executed tool {tool_name} via route {route} using model {model}"
        }
        return self._append_event(event)

    def record_error(self, *, error_type: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Record errors, exceptions, or failures."""
        event = {
            "request_id": context.get("request_id"),
            "trace_id": context.get("trace_id"),
            "user_id": context.get("user_id"),
            "component": context.get("component") or "backend",
            "action": "error",
            "severity": "error",
            "status": "failed",
            "message": f"Error [{error_type}]: {message}"
        }
        return self._append_event(event)

    def get_telemetry(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return buffered telemetry logs."""
        return self.events_buffer[-limit:]

    def get_posture(self) -> Dict[str, Any]:
        """Evaluate trust posture dynamically."""
        session_age = int((datetime.utcnow() - self.session_start).total_seconds())
        posture = assess_posture(
            device_trust=self.device_trust,
            session_age_sec=session_age,
            mode=self.mode,
            privacy_level="public",
            policy_score=self.policy_score
        )
        posture["reason"] = posture_reason(posture)
        return posture


# Singleton instance matching test & route demands
_collector_instance = ObservabilityCollector()


def get_collector() -> ObservabilityCollector:
    """Return default collector singleton."""
    return _collector_instance


# Keep ASIMObservability class legacy support
class ASIMObservability:
    """ASIMObservability legacy wrapper redirecting calls to new ObservabilityCollector."""

    def __init__(self):
        self.collector = _collector_instance

    def log(self, level: Any, message: str, component: str, metadata: Optional[Dict[str, Any]] = None):
        sev_map = {"debug": "debug", "info": "info", "warning": "warning", "error": "error", "critical": "critical"}
        severity = getattr(level, "value", str(level)).lower()
        severity = sev_map.get(severity, "info")
        
        self.collector._append_event({
            "component": component,
            "severity": severity,
            "message": message,
            "metadata": metadata or {}
        })

    def get_trust_posture(self) -> Dict[str, Any]:
        p = self.collector.get_posture()
        return {
            "trust_score": p["score"],
            "posture": p["level"].upper(),
            "system_health": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


def get_observability() -> ASIMObservability:
    return ASIMObservability()
