#!/usr/bin/env python3
"""
STATUS: REAL — Thread-safe append-only system auditing subsystem
ASIMNEXUS Audit Bus
===================
Appends security events, actions, and overrides to data/audit_bus.jsonl.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.telemetry_schema import validate_event

AUDIT_BUS_PATH = Path("data/audit_bus.jsonl")
AUDIT_BUS_PATH.parent.mkdir(parents=True, exist_ok=True)


def emit_audit(event: Dict[str, Any]) -> None:
    """Appends validation-enforced event envelope to audit_bus.jsonl."""
    try:
        validated = validate_event(event)
        with open(AUDIT_BUS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(validated) + "\n")
    except Exception as e:
        # Fallback print if file write fails to prevent loss of critical audit logs
        print(f"[AUDIT BUS ERROR] Failed to log audit: {e}. Event: {event}")


def fetch_audit(limit: int = 100, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve audit history records. Optionally paginate using event_id as cursor."""
    if not AUDIT_BUS_PATH.exists():
        return []

    records = []
    try:
        with open(AUDIT_BUS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    records.append(json.loads(line_str))
    except Exception as e:
        print(f"[AUDIT BUS ERROR] Failed to read audit log: {e}")
        return []

    if cursor:
        # Find index of cursor event
        idx = next((i for i, r in enumerate(records) if r.get("event_id") == cursor), None)
        if idx is not None:
            records = records[idx + 1:]

    return records[-limit:]


def audit_summary() -> Dict[str, Any]:
    """Provide count metrics of logged operations grouped by component, status, and severity."""
    summary = {
        "total_records": 0,
        "by_severity": {"debug": 0, "info": 0, "warning": 0, "error": 0, "critical": 0},
        "by_status": {"ok": 0, "blocked": 0, "failed": 0, "degraded": 0},
        "by_component": {}
    }
    
    if not AUDIT_BUS_PATH.exists():
        return summary

    try:
        with open(AUDIT_BUS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                record = json.loads(line_str)
                summary["total_records"] += 1
                
                sev = record.get("severity", "info")
                summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1
                
                status = record.get("status", "ok")
                summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
                
                comp = record.get("component", "unknown")
                summary["by_component"][comp] = summary["by_component"].get(comp, 0) + 1
    except Exception as e:
        print(f"[AUDIT BUS ERROR] Failed to calculate audit summary: {e}")

    return summary
