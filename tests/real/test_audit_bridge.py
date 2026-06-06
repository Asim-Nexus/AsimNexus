#!/usr/bin/env python3
"""
ASIMNEXUS Mesh Audit Sync Bridge Tests
======================================
"""

import pytest
from backend.mesh_audit_bridge import sanitize_for_mesh, queue_mesh_audit, flush_mesh_audit, sync_mesh_audit, _mesh_queue


def test_sanitize_for_mesh_strips_sensitive_data():
    raw_event = {
        "event_id": "evt-123",
        "user_id": "FounderAsim",
        "device_id": "FounderDesktopMacPro",
        "session_id": "secret-session-key",
        "message": "User queried private key context",
        "policy": {
            "rule_id": "rule_file_write",
            "decision": "deny",
            "reason": "Explicit block on file /etc/shadow"
        }
    }
    
    sanitized = sanitize_for_mesh(raw_event)
    
    # Confirm message redacted
    assert sanitized["message"] == "[redacted_for_mesh_sync]"
    
    # Confirm sensitive values hashed
    assert sanitized["user_id"] != "FounderAsim"
    assert len(sanitized["user_id"]) == 16  # SHA256 slice
    
    # Confirm policy reason sanitized
    assert sanitized["policy"]["reason"] == "[sanitized]"


def test_mesh_sync_queue_management():
    _mesh_queue.clear()
    
    event = {
        "component": "backend",
        "action": "request",
        "severity": "info",
        "status": "ok",
        "message": "Ping received"
    }
    
    queue_mesh_audit(event)
    assert len(_mesh_queue) == 1
    
    # Verify sync clears queue
    res = sync_mesh_audit()
    assert res["synced_events_count"] == 1
    assert len(_mesh_queue) == 0


def test_flush_mesh_audit():
    _mesh_queue.clear()
    for i in range(5):
        queue_mesh_audit({
            "component": "backend",
            "action": "request",
            "severity": "info",
            "status": "ok",
            "message": f"Ping {i}"
        })
        
    assert len(_mesh_queue) == 5
    flushed = flush_mesh_audit(limit=3)
    assert flushed == 3
    assert len(_mesh_queue) == 2
