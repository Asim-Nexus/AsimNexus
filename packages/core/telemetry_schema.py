#!/usr/bin/env python3
"""
STATUS: REAL — Telemetry schema and validation layer
ASIMNEXUS Telemetry Schema Layer
================================
Enforces the 21-field event envelope schema on all metrics, logs, and traces.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any

VALID_COMPONENTS = {"backend", "core", "mesh", "clone", "policy", "learning"}
VALID_ACTIONS = {"request", "decision", "tool_call", "approval", "deny", "sync", "error"}
VALID_SEVERITIES = {"debug", "info", "warning", "error", "critical"}
VALID_STATUSES = {"ok", "blocked", "failed", "degraded"}
VALID_POSTURES = {"trusted", "high", "medium", "low", "untrusted"}
VALID_PRIVACY_LEVELS = {"public", "shared", "private", "highly_sensitive"}
VALID_MODES = {"personal", "family", "company", "community", "government"}


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure every event envelope conforms to the structure with default values."""
    normalized = {
        "event_id": event.get("event_id") or str(uuid.uuid4()),
        "timestamp": event.get("timestamp") or datetime.utcnow().isoformat() + "Z",
        "trace_id": event.get("trace_id") or str(uuid.uuid4()),
        "span_id": event.get("span_id") or str(uuid.uuid4()),
        "request_id": event.get("request_id") or str(uuid.uuid4()),
        "user_id": event.get("user_id"),
        "device_id": event.get("device_id"),
        "session_id": event.get("session_id"),
        "component": event.get("component") or "backend",
        "action": event.get("action") or "request",
        "severity": event.get("severity") or "info",
        "status": event.get("status") or "ok",
        "latency_ms": float(event.get("latency_ms") or 0.0),
        "resource": event.get("resource") or {
            "cpu_pct": 0.0,
            "memory_mb": 0.0,
            "disk_mb": 0.0,
            "network_kbps": 0.0
        },
        "trust_posture": event.get("trust_posture") or "medium",
        "privacy_level": event.get("privacy_level") or "public",
        "mode": event.get("mode") or "personal",
        "policy": event.get("policy") or {
            "rule_id": None,
            "decision": None,
            "reason": None
        },
        "tool": event.get("tool") or {
            "name": None,
            "selected_model": None,
            "route": None
        },
        "audit_ref": event.get("audit_ref"),
        "mesh_ref": event.get("mesh_ref"),
        "message": event.get("message") or ""
    }
    return normalized


def validate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Validate normalized telemetry event fields against strict constraints. Throws ValueError if invalid."""
    normalized = normalize_event(event)
    
    # Value constraints validation
    if normalized["component"] not in VALID_COMPONENTS:
        raise ValueError(f"Invalid component: {normalized['component']}")
    if normalized["action"] not in VALID_ACTIONS:
        raise ValueError(f"Invalid action: {normalized['action']}")
    if normalized["severity"] not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity: {normalized['severity']}")
    if normalized["status"] not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {normalized['status']}")
    if normalized["trust_posture"] not in VALID_POSTURES:
        raise ValueError(f"Invalid trust_posture: {normalized['trust_posture']}")
    if normalized["privacy_level"] not in VALID_PRIVACY_LEVELS:
        raise ValueError(f"Invalid privacy_level: {normalized['privacy_level']}")
    if normalized["mode"] not in VALID_MODES:
        raise ValueError(f"Invalid mode: {normalized['mode']}")

    return normalized


def event_to_json(event: Dict[str, Any]) -> str:
    """Enforce strict schema validation and dump event to single-line JSON string."""
    return json.dumps(validate_event(event))
